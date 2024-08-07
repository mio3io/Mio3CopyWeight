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
        obj = context.active_object
        return obj and obj.mode == "EDIT" and obj.type == "MESH"

    def execute(self, context):
        active_obj = context.active_object
        target_obj = next((obj for obj in context.selected_objects if obj != active_obj), None)
        active_mesh = active_obj.data

        active_bm = bmesh.from_edit_mesh(active_mesh)
        active_bm.verts.ensure_lookup_table()
        active_vert = active_bm.select_history.active
        if not active_vert:
            bmesh.update_edit_mesh(active_mesh)
            self.report({"ERROR"}, "The active object has no selected vertices")
            return {"CANCELLED"}

        active_index = active_vert.index

        if active_mesh.total_vert_sel > 1:
            bpy.ops.object.vertex_weight_copy()

        if target_obj:
            bpy.ops.object.mode_set(mode="OBJECT")
            selected_verts = [v for v in target_obj.data.vertices if v.select]
            vertex_groups = self.get_vgroups(active_obj, active_mesh.vertices[active_index])
            self.copy_weight(vertex_groups, selected_verts, target_obj)
            target_obj.data.update()
            bpy.ops.object.mode_set(mode="EDIT")

            if target_obj.use_mesh_mirror_x:
                if selected_verts:
                    bpy.context.view_layer.objects.active = target_obj
                    for g in selected_verts[0].groups:
                        vg = target_obj.vertex_groups[g.group]
                        if not vg.lock_weight:
                            bpy.ops.object.vertex_weight_paste(weight_group=g.group)
                    bpy.context.view_layer.objects.active = active_obj

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
