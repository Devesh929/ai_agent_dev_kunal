# Blender 3.x
import bpy
import math
from mathutils import Vector, Matrix

# -----------------------
# helpers & housekeeping
# -----------------------
def reset_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for datablock in (bpy.data.meshes, bpy.data.materials, bpy.data.curves):
        for b in list(datablock):
            if not b.users:
                datablock.remove(b)

def make_collection(name="Helicopter"):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col

def add_emission_mat(name="WireYellow", color=(1.0, 0.9, 0.1, 1.0), strength=3.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emi = nodes.new("ShaderNodeEmission")
    emi.inputs["Color"].default_value = color
    emi.inputs["Strength"].default_value = strength
    links.new(emi.outputs["Emission"], out.inputs["Surface"])
    return mat

def add_wireframe_modifier(obj, thickness=0.02):
    mod = obj.modifiers.new(name="Wireframe", type="WIREFRAME")
    mod.thickness = thickness
    mod.use_boundary = True
    mod.use_replace = True

def cube_like(name, size=(1,1,1), location=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=location)
    o = bpy.context.active_object
    o.name = name
    o.scale = Vector(size)/2.0
    return o

def cylinder(name, radius=1, depth=2, location=(0,0,0), rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation)
    o = bpy.context.active_object
    o.name = name
    return o

def sphere(name, radius=1, location=(0,0,0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=48, ring_count=24)
    o = bpy.context.active_object
    o.name = name
    return o

def set_parent(child, parent):
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()

# -----------------------
# build helicopter parts
# -----------------------
reset_scene()
col = make_collection()
mat_wire = add_emission_mat()

# World & render look
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.use_bloom = True
bpy.data.worlds["World"].use_nodes = True
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.02, 0.03, 1.0)
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 0.8

# Root empty to keep things tidy
root = bpy.data.objects.new("HELI_ROOT", None)
col.objects.link(root)

# Fuselage (stretched sphere)
fuselage = sphere("Fuselage", radius=1.0, location=(0,0,0.9))
fuselage.scale = (2.2, 0.95, 1.0)   # length, width, height
col.objects.link(fuselage)
add_wireframe_modifier(fuselage, 0.015)
fuselage.data.materials.append(mat_wire)
set_parent(fuselage, root)

# Nose bubble
cockpit = sphere("Cockpit", radius=0.8, location=(1.6, 0, 0.9))
cockpit.scale = (0.9, 0.95, 0.9)
col.objects.link(cockpit)
add_wireframe_modifier(cockpit, 0.015)
cockpit.data.materials.append(mat_wire)
set_parent(cockpit, root)

# Tail boom
tail = cylinder("TailBoom", radius=0.12, depth=4.2, location=(-3.0/2, 0, 1.0), rotation=(0, math.radians(90), 0))
tail.location.x = -1.3
col.objects.link(tail)
add_wireframe_modifier(tail, 0.012)
tail.data.materials.append(mat_wire)
set_parent(tail, root)

# Tail fin & tail rotor mast
fin = cube_like("TailFin", size=(0.08, 0.65, 1.0), location=(-3.3, 0, 1.2))
col.objects.link(fin)
add_wireframe_modifier(fin, 0.01)
fin.data.materials.append(mat_wire)
set_parent(fin, root)

tail_mast = cylinder("TailRotorMast", radius=0.05, depth=0.5,
                     location=(-3.3, 0.35, 1.2), rotation=(math.radians(90), 0, 0))
col.objects.link(tail_mast)
add_wireframe_modifier(tail_mast, 0.01)
tail_mast.data.materials.append(mat_wire)
set_parent(tail_mast, root)

# Tail rotor (2 blades)
hub_t = cylinder("TailHub", radius=0.05, depth=0.12, location=(-3.3, 0.35, 1.2), rotation=(math.radians(90), 0, 0))
col.objects.link(hub_t)
add_wireframe_modifier(hub_t, 0.012)
hub_t.data.materials.append(mat_wire)
set_parent(hub_t, root)

for i in range(2):
    blade = cube_like(f"TailBlade_{i+1}", size=(0.06, 0.9, 0.12), location=(-3.3, 0.80, 1.2))
    blade.rotation_euler = (0, 0, math.radians(90*i))
    col.objects.link(blade)
    add_wireframe_modifier(blade, 0.01)
    blade.data.materials.append(mat_wire)
    set_parent(blade, hub_t)

# Main rotor mast & hub
mast = cylinder("MainMast", radius=0.08, depth=0.8, location=(0,0,2.0), rotation=(math.radians(90), 0, 0))
col.objects.link(mast)
add_wireframe_modifier(mast, 0.012)
mast.data.materials.append(mat_wire)
set_parent(mast, root)

hub = cylinder("MainHub", radius=0.15, depth=0.2, location=(0,0,2.4), rotation=(0,0,0))
col.objects.link(hub)
add_wireframe_modifier(hub, 0.012)
hub.data.materials.append(mat_wire)
set_parent(hub, mast)

# Main rotor blades (4)
blade_length = 4.8
blade_width  = 0.28
blade_thick  = 0.06
for i in range(4):
    angle = math.radians(i * 90)
    blade = cube_like(f"MainBlade_{i+1}", size=(blade_length, blade_width, blade_thick), location=(0,0,2.4))
    # move blade so hub connects at root
    blade.location += Vector((blade_length/4, 0, 0))
    blade.rotation_euler = (math.radians(4), 0, angle)
    col.objects.link(blade)
    add_wireframe_modifier(blade, 0.01)
    blade.data.materials.append(mat_wire)
    set_parent(blade, hub)

# Landing skids (two rails + four struts)
rail_dist_y = 0.8
rail_z = 0.15
rail_len = 3.3
rail_r = 0.06

for sgn in (-1, 1):
    rail = cylinder(f"Skid_{'L' if sgn<0 else 'R'}", radius=rail_r, depth=rail_len,
                    location=(0, sgn*rail_dist_y, rail_z), rotation=(0, math.radians(90), 0))
    col.objects.link(rail)
    add_wireframe_modifier(rail, 0.01)
    rail.data.materials.append(mat_wire)
    set_parent(rail, root)

# struts
def strut(x, y, z_top, z_bot, name):
    h = abs(z_top - z_bot)
    c = cylinder(name, radius=0.05, depth=h, location=(x, y, (z_top+z_bot)/2),
                 rotation=(math.radians(20 if y>0 else -20), 0, 0))
    col.objects.link(c)
    add_wireframe_modifier(c, 0.01)
    c.data.materials.append(mat_wire)
    set_parent(c, root)

for x in (-1.2, 1.2):
    for y in (-rail_dist_y, rail_dist_y):
        strut(x, y, 0.7, rail_z, f"Strut_{'F' if x<0 else 'B'}_{'L' if y<0 else 'R'}")

# Small engine / intake hint on top
engine = sphere("EnginePod", radius=0.5, location=(0.2, 0, 1.6))
engine.scale = (1.2, 0.7, 0.7)
col.objects.link(engine)
add_wireframe_modifier(engine, 0.012)
engine.data.materials.append(mat_wire)
set_parent(engine, root)

# Give all objects the material if they somehow missed it
for o in col.objects:
    if getattr(o.data, "materials", None) and not o.data.materials:
        o.data.materials.append(mat_wire)

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
col.objects.link(cam)
scene.camera = cam
cam.location = (7.0, -7.5, 4.0)
# point at origin
direction = Vector((0,0,1.2)) - cam.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot_quat.to_euler()

# Light (not strictly needed for emission, but useful)
bpy.ops.object.light_add(type='AREA', location=(3, -3, 6))
light = bpy.context.active_object
light.data.energy = 200

# Nice viewport: show as wire + glowing lines
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'RENDERED'
                space.shading.use_scene_lights = True
                space.shading.use_scene_world = True
