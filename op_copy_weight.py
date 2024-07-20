import bpy
import bmesh
from bpy.types import Operator

class MIO3_OT_copy_weight(Operator):
    bl_idname = "object.mio3_vertex_weight_copy"
    bl_label = "Copy weights"
    bl_description = "Copy weights"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.mode == "EDIT"

    def execute(self, context):
        if len(context.selected_objects) < 2:
            self.report({"ERROR"}, "Please select two or more objects")
            return {"CANCELLED"}

        active_obj = context.active_object
        target_obj = [obj for obj in context.selected_objects if obj != active_obj][0]

        bpy.ops.object.mode_set(mode="OBJECT")

        active_mesh = active_obj.data
        active_bm = bmesh.new()
        active_bm.from_mesh(active_mesh)
        active_bm.verts.ensure_lookup_table()
        active_vert = active_bm.select_history.active
        if not active_vert:
            active_bm.to_mesh(active_mesh)
            active_mesh.update()
            active_bm.free()
            bpy.ops.object.mode_set(mode="EDIT")
            self.report({"ERROR"}, "The active object has no selected vertices")
            return {"CANCELLED"}

        active_index = active_vert.index

        selected_verts = [v for v in target_obj.data.vertices if v.select]
        if not selected_verts:
            active_bm.to_mesh(active_mesh)
            active_mesh.update()
            active_bm.free()
            bpy.ops.object.mode_set(mode="EDIT")
            self.report({"ERROR"}, "The target object has no selected vertices")
            return {"CANCELLED"}

        vertex_groups = self.get_vgroups(active_obj, active_mesh.vertices[active_index])
        self.copy_weight(vertex_groups, selected_verts, target_obj)
        target_obj.data.update()

        bpy.ops.object.mode_set(mode="EDIT")

        bpy.context.view_layer.objects.active = target_obj
        for g in selected_verts[0].groups:
            vg = target_obj.vertex_groups[g.group]
            if not vg.lock_weight:
                bpy.ops.object.vertex_weight_paste(weight_group=g.group)
        bpy.context.view_layer.objects.active = active_obj

        if active_mesh.count_selected_items()[0] > 1:
            bpy.ops.object.vertex_weight_copy()

        if active_obj.vertex_groups.active:
            target_group_name = active_obj.vertex_groups.active.name
            if target_group_name in target_obj.vertex_groups:
                vg_index = target_obj.vertex_groups[target_group_name].index
                target_obj.vertex_groups.active_index = vg_index

        return {"FINISHED"}

    def get_vgroups(self, obj, vert):
        vertex_groups = []
        for g in vert.groups:
            vertex_groups.append((obj.vertex_groups[g.group], g.weight))
        return vertex_groups

    def copy_weight(self, vertex_groups, verts, obj):
        indexes = [v.index for v in verts]
        for vg in obj.vertex_groups:
            if not vg.lock_weight:
                vg.remove(indexes)

        for group, weight in vertex_groups:
            if group.name not in obj.vertex_groups:
                new_group = obj.vertex_groups.new(name=group.name)
            else:
                new_group = obj.vertex_groups[group.name]

            if not new_group.lock_weight:
                for v in verts:
                    new_group.add([v.index], weight, "REPLACE")


classes = [
    MIO3_OT_copy_weight,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
