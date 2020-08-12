
import bpy
import gpu
import bgl
import numpy as np
from random import random
import gpu_extras.batch as gpu_extras_batch
import bmesh

vertex_shader = """
uniform mat4 perspective_matrix;
uniform mat4 matrix_world;
uniform float outline_size;
in vec3 position;
in vec3 vertex_normal;

void main()
{
    vec3 vertex = (matrix_world * vec4(position, 1)).xyz + vertex_normal * 0.1 * outline_size;
    gl_Position = perspective_matrix * vec4(vertex, 1);
}
"""

pixel_shader = """
uniform vec4 color;

void main()
{
    gl_FragColor = color;
}
"""

def get_mesh(object):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    mesh_to_render = bpy.data.meshes.new("AAAAAAAAAAAAAAAA")
    mesh_to_render.create_normals_split()
    
    bm.from_object(object, depsgraph, cage=False, face_normals=False)
    bm.to_mesh(mesh_to_render)
    bm.free()
    
    return mesh_to_render

def draw_mesh(scene):
    draw_handlers = scene.custom_shaders_draw_handlers
    for draw_handler in draw_handlers:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(draw_handler, "WINDOW")
        except (AttributeError, ValueError) as e:
            pass
        draw_handlers.remove(draw_handler)
    
    if bpy.context.active_object.type != "MESH" or not scene.use_outline_shaders:
        return

    mesh = get_mesh(bpy.context.active_object)
    mesh.calc_loop_triangles()

    vertices = np.empty((len(mesh.vertices), 3), 'f')
    normals = np.empty((len(mesh.vertices), 3), 'f')
    indices = np.empty((len(mesh.loop_triangles), 3), 'i')

    mesh.vertices.foreach_get(
        "co", np.reshape(vertices, len(mesh.vertices) * 3))
    mesh.vertices.foreach_get(
        "normal", np.reshape(normals, len(mesh.vertices) * 3))
    mesh.loop_triangles.foreach_get(
        "vertices", np.reshape(indices, len(mesh.loop_triangles) * 3))

    shader = gpu.types.GPUShader(vertex_shader, pixel_shader)
    fmt = gpu.types.GPUVertFormat()
    fmt.attr_add(id="position", comp_type="F32", len=3, fetch_mode="FLOAT")
    fmt.attr_add(id="vertex_normal", comp_type="F32", len=3, fetch_mode="FLOAT")
    vbo = gpu.types.GPUVertBuf(len=len(mesh.vertices), format=fmt)
    vbo.attr_fill(id="position", data=vertices)
    vbo.attr_fill(id="vertex_normal", data=normals)
    ibo = gpu.types.GPUIndexBuf(type="TRIS", seq=indices)
    batch = gpu.types.GPUBatch(type="TRIS", buf=vbo, elem=ibo)

    def draw():
        shader.bind()
        shader.uniform_float("outline_size", scene.custom_outline_size)
        shader.uniform_float("color", (0, 0, 0, 1))
        shader.uniform_float("perspective_matrix", bpy.context.region_data.perspective_matrix)
        shader.uniform_float("matrix_world", bpy.context.active_object.matrix_world)
        bgl.glEnable(bgl.GL_CULL_FACE)
        bgl.glCullFace(bgl.GL_FRONT)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        batch.draw(shader)
        bgl.glDisable(bgl.GL_CULL_FACE)
        bgl.glCullFace(bgl.GL_BACK)
        bgl.glDisable(bgl.GL_DEPTH_TEST)
    
    draw_handlers.append(bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW'))
    
    bpy.data.meshes.remove(mesh)

class OBJECT_PT_outline_rendering(bpy.types.Panel):
    bl_label = "Outline Rendering"
    bl_idname = "OBJECT_PT_outline_rendering"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Shaders"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "use_outline_shaders")
        layout.prop(scene, "custom_outline_size")

def register():
    bpy.utils.register_class(OBJECT_PT_outline_rendering)
    bpy.types.Scene.custom_shaders_draw_handlers = []
    bpy.types.Scene.use_outline_shaders = bpy.props.BoolProperty(name = "Use outline shaders")
    bpy.types.Scene.custom_outline_size = bpy.props.FloatProperty(name = "Outline thickness")

def unregister():
    bpy.utils.unregister_class(OBJECT_PT_outline_rendering)
    del bpy.types.Scene.use_custom_shaders

if __name__ == "__main__":
    register()
    
    # can't be removed later, cause python.
    bpy.app.handlers.depsgraph_update_post.append(draw_mesh)
    bpy.app.handlers.frame_change_post.append(draw_mesh)
