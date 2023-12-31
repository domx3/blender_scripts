bl_info = {
    "name": "Bake Object Materials",
    "description": "Bake all of objects materials to image texture.",
    "author": "Domx3",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "View3D",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Baking"
}

import bpy

def post_bake(material, image_texture, metallic_originals, reset_metallic):
    principled_shader = material.node_tree.nodes.get("Principled BSDF")
    if principled_shader is not None:
        material.node_tree.links.new(principled_shader.inputs["Base Color"], image_texture.outputs["Color"])
    if(reset_metallic and material.name in metallic_originals.keys()):
        principled_shader.inputs['Metallic'].default_value = metallic_originals[material.name]

def pre_bake(material, image_texture, metallic_originals, reset_metallic):    
    nodes = material.node_tree.nodes
    principled_shader = nodes.get("Principled BSDF")
    metallic_value = principled_shader.inputs['Metallic'].default_value
    if principled_shader is not None:        
        if(reset_metallic and metallic_value > 0):
            metallic_originals[material.name] = metallic_value
            principled_shader.inputs['Metallic'].default_value = 0            
        for link in material.node_tree.links:
            if (link.to_node == principled_shader and link.to_socket.name == "Base Color" and 
            link.from_node.name == image_texture.name):
                material.node_tree.links.remove(link)
        if('base_color' in nodes.keys()):
            material.node_tree.links.new(principled_shader.inputs["Base Color"], 
                nodes['base_color'].outputs["Color"])        

def get_bake_image(material_name, width, height):
    image_name = f"{material_name}_tex"
    image = bpy.data.images.get(image_name)
    if(image and (image.size[0] != width or image.size[1] != height)):
        image.scale(width, height)
    if image is None:
        image = bpy.data.images.new(name=image_name, width=width, height=height, alpha=False)
    return image

def get_bake_texture(material, obj_name, img):
    tex_name = f"{obj_name}_tex"
    if(tex_name in material.node_tree.nodes.keys()):
        return material.node_tree.nodes[tex_name]
    else:
        img_tex = material.node_tree.nodes.new("ShaderNodeTexImage")
        img_tex.name = tex_name
        img_tex.image = img
        return img_tex
    
def bake(context):
    bpy.context.scene.render.engine = 'CYCLES'
    metallic_originals = {}
    reset_metallic = context.scene.my_props.reset_metallic
    bake_type = context.scene.my_props.my_enum
    img_res = context.scene.my_props.img_res
    obj = context.active_object
    bake_image = get_bake_image(obj.name, img_res, img_res)
    for slot_index, material_slot in enumerate(obj.material_slots):
        obj.active_material_index = slot_index
        active_material = obj.active_material    
        bake_texture = get_bake_texture(active_material, obj.name, bake_image)
        pre_bake(active_material, bake_texture, metallic_originals, reset_metallic)
    bpy.ops.object.bake(type=bake_type)
    for slot_index, material_slot in enumerate(obj.material_slots):
        obj.active_material_index = slot_index
        active_material = obj.active_material
        bake_texture = get_bake_texture(active_material, obj.name, bake_image)
        post_bake(active_material, bake_texture, metallic_originals, reset_metallic)    
    bake_image.filepath_raw = f"//{bake_image.name}.jpg"
    bake_image.save()
    print("Baking completed for all material slots.")


class BakeObjectMaterials(bpy.types.Operator):
    """Bake object's materials into image texture"""
    bl_idname = "object.bake_object_materials"
    bl_label = "Bake Object Materials"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        bake(context)
        return {'FINISHED'}

class BAKE_PT_panel(bpy.types.Panel):
    """Baking object materials panel"""
    bl_label = "Bake panel"
    bl_idname = "BAKE_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bake"

    def draw(self, context):
        layout = self.layout
        my_props = context.scene.my_props
        layout.label(text="Properties")
        row = layout.row()
        row.prop(my_props, "reset_metallic")
        row = layout.row()
        row.prop(my_props, "img_res")
        row = layout.row()    
        layout.label(text="Set bake type")           
        layout.prop(my_props, "my_enum", text="")
        layout.label(text="")        
        layout.operator("object.bake_object_materials", text="Bake Materials")

class My_props(bpy.types.PropertyGroup):
    reset_metallic: bpy.props.BoolProperty(
        name='Reset Metallic',
        default=True,
        description="Set metallic to 0 during bake",
    )
    img_res: bpy.props.IntProperty(
        name='Image Resolution',
        default=1024,
        description="Set bake image resolution in px",
    )
    my_enum: bpy.props.EnumProperty(
        name="Bake type",
        items=[
            ('COMBINED', "Combined", "Bake color, shadow, emmit"),
            ('DIFFUSE', "Diffuse", "Bake color only"),
            ('SHADOW', "Shadow", "Bake shadow only"),
        ],
        default='COMBINED',
    )

classes = (
    My_props,
    BAKE_PT_panel,
    BakeObjectMaterials,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.my_props = bpy.props.PointerProperty(type=My_props)

def unregister():
    del bpy.types.Scene.my_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
