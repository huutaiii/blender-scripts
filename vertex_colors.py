# <pep8 compliant>

import bpy
from mathutils import *
from math import *

CHANNEL_INDICES = {
    'R': 0,
    'G': 1,
    'B': 2,
    'A': 3
}

def vertex_colors_from_group(object, vertex_color, vertex_group, color_channel, blend_mode):
    data = object.data
    for poly in data.polygons:
        for loop_id in poly.loop_indices:
            vertex = data.loops[loop_id].vertex_index
            color = vertex_color.data[loop_id].color
            weight = 0
            try:
                weight = vertex_group.weight(vertex)
            except RuntimeError:
                pass
            if blend_mode == "REPLACE":
                color[color_channel] = weight
            elif blend_mode == "MULTIPLY":
                color[color_channel] *= weight
            data.vertex_colors.active.data[loop_id].color = color

def fill_vertex_colors(object, vertex_color, fill_color, channels, blend_mode):
    data = object.data
    for poly in data.polygons:
        for loop_id in poly.loop_indices:
            color = vertex_color.data[loop_id].color
            if blend_mode == "REPLACE":
                for i in range(0, 3):
                    color[i] = fill_color[i] if channels[i] else color[i]
            elif blend_mode == "MULTIPLY":
                for i in range(0, 3):
                    color[i] *= fill_color[i] if channels[i] else color[i]
            data.vertex_colors.active.data[loop_id].color = color

class OBJECT_OT_write_vertex_colors(bpy.types.Operator):
    bl_idname = "object.write_vertex_colors"
    bl_label = "Copy weights to vertex colors"
    bl_options = {"REGISTER", "UNDO"}
    
    src_group = bpy.props.StringProperty(name = "Vertex group")
    dst_colors = bpy.props.StringProperty(name = "Vertex colors")
    
    channel: bpy.props.EnumProperty(
        items = [
            ("R", "Red", ""),
            ("G", "Green", ""),
            ("B", "Blue", ""),
            ("A", "Alpha", "")
        ],
        name = "Color channel")
    blend: bpy.props.EnumProperty(
        items = [
            ("REPLACE", "Replace", "", 0),
            ("MULTIPLY", "Multiply", "", 1)
        ],
        name = "Blend mode")
        
    def invoke(self, context, event):
        self.src_group = context.active_object.vertex_groups.active.name
        self.dst_colors = context.active_object.data.vertex_colors.active.name
        self.channel = "R"
        self.blend = "REPLACE"
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop_search(self, "src_group", context.active_object, "vertex_groups")
        layout.prop_search(self, "dst_colors", context.active_object.data, "vertex_colors")
        layout.prop(self, "channel", expand = True)
        layout.prop(self, "blend")
    
    def execute(self, context):
        object = bpy.context.active_object
        vertex_colors_from_group(
            object,
            object.data.vertex_colors[self.dst_colors],
            object.vertex_groups[self.src_group],
            CHANNEL_INDICES[self.channel], self.blend
        )
        return {"FINISHED"}

class OBJECT_OT_fill_vertex_colors(bpy.types.Operator):
    bl_idname = "object.fill_vertex_colors"
    bl_label = "Fill vertex colors"
    bl_options = {"REGISTER", "UNDO"}
    
    fill_color: bpy.props.FloatVectorProperty(
        name = "Color",
        subtype = "COLOR",
        size = 4,
        min = 0,
        max = 1)
    
    channels: bpy.props.BoolVectorProperty(name = "Channels", size = 4, subtype="COLOR")
    
    blend: bpy.props.EnumProperty(
        items = [
            ("REPLACE", "Replace", "", 0),
            ("MULTIPLY", "Multiply", "", 1)
        ],
        name = "Blend mode")
    
    def invoke(self, context, event):
        self.fill_color = (1, 1, 1, 1)
        self.channels = (True, True, True, True)
        self.blend = "REPLACE"
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "fill_color")
        layout.prop(self, "channels", expand = True)
        layout.prop(self, "blend")
    
    def execute(self, context):
        object = bpy.context.active_object
        fill_vertex_colors(
            object,
            object.data.vertex_colors.active,
            self.fill_color,
            self.channels,
            self.blend,
        )
        return {"FINISHED"}

class OBJECT_PT_vertex_colors(bpy.types.Panel):
    bl_label = "Vertex Colors"
    bl_idname = "OBJECT_PT_vertex_colors"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vertex Data"
    
    @classmethod
    def poll(self, context):
        return context.active_object.type == "MESH"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.operator("object.write_vertex_colors")
        layout.operator("object.fill_vertex_colors")

classes = [
    OBJECT_OT_fill_vertex_colors,
    OBJECT_OT_write_vertex_colors,
    OBJECT_PT_vertex_colors,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.register_class(cls)

if __name__ == "__main__":
    register()
