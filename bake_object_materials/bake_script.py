import bpy

# set metallic to 0 for bake and then 
# return it to its original value
metallic_originals = {}
reset_metallic = True

# DO after bake:
# link bake image into principled shader color
# retrun metallic to original state
#
def post_bake(material, image_texture):

    principled_shader = material.node_tree.nodes.get("Principled BSDF")

    # link baked image to principled shader color
    if principled_shader is not None:
        material.node_tree.links.new(principled_shader.inputs["Base Color"], image_texture.outputs["Color"])

    # set metallic to its original value
    if(reset_metallic and material.name in metallic_originals.keys()):
        #print(material.name)
        principled_shader.inputs['Metallic'].default_value = metallic_originals[material.name]

# DO before bake:
# unlink bake image texture from principal shader color
# link node with base_color to principled color
# set metallic to 0
#
def pre_bake(material, image_texture):
    
    nodes = material.node_tree.nodes
    principled_shader = nodes.get("Principled BSDF")
    metallic_value = principled_shader.inputs['Metallic'].default_value
    
    if principled_shader is not None:
        
        # set metallic to 0
        if(reset_metallic and metallic_value > 0):
            metallic_originals[material.name] = metallic_value
            principled_shader.inputs['Metallic'].default_value = 0
            
        # unlink bake image texture from principled shader color
        for link in material.node_tree.links:
            if (link.to_node == principled_shader and link.to_socket.name == "Base Color" and 
            link.from_node.name == image_texture.name):
                material.node_tree.links.remove(link)
                
        # link original color node to principled shader 
        if('base_color' in nodes.keys()):
            material.node_tree.links.new(principled_shader.inputs["Base Color"], 
                nodes['base_color'].outputs["Color"])        


def get_bake_image(material_name, width, height):
    image_name = f"{material_name}_tex"
    image = bpy.data.images.get(image_name)
    if(image.size[0] != width or image.size[1] != height):
        image.scale(width, height)
    if image is None:
        image = bpy.data.images.new(name=image_name, width=width, height=height, alpha=False)

    return image


def get_bake_texture(material, obj_name, img):
    tex_name = f"{obj_name}_tex"
    
    # already exists
    if(tex_name in material.node_tree.nodes.keys()):
        return material.node_tree.nodes[tex_name]

    # create new image texture
    else:
        img_tex = material.node_tree.nodes.new("ShaderNodeTexImage")
        img_tex.name = tex_name
        img_tex.image = img
        return img_tex
    

def bake():
 
    obj = bpy.context.active_object
    bake_image = get_bake_image(obj.name, 1024, 1024)

    # prepare materials in slots for baking
    for slot_index, material_slot in enumerate(obj.material_slots):
        # set the active material slot
        obj.active_material_index = slot_index
        active_material = obj.active_material    
    
        bake_texture = get_bake_texture(active_material, obj.name, bake_image)
    
        pre_bake(active_material, bake_texture)

    
    # BAKE
    bpy.ops.object.bake(type='COMBINED')
    
    # reset materials in slots
    for slot_index, material_slot in enumerate(obj.material_slots):
        # set the active material slot
        obj.active_material_index = slot_index
        active_material = obj.active_material

        bake_texture = get_bake_texture(active_material, obj.name, bake_image)
        post_bake(active_material, bake_texture)    

    
    # save the baked image to a file
    bake_image.filepath_raw = f"//{bake_image.name}.jpg"
    bake_image.save()




    print("Baking completed for all material slots.")




bake()