"""Estudio oscuro, camaras y render (Cycles)."""
import bpy, math
from math import radians
from mathutils import Vector
ORANGE = (1.0, 0.33, 0.02)

def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def area(name, loc, target, size, power, color=(1, 1, 1), size_y=None, spread=None):
    L = bpy.data.lights.new(name, 'AREA')
    L.energy = power * 1.3e5          # la escena esta en mm
    L.color = color
    L.shape = 'RECTANGLE'; L.size = size; L.size_y = size_y or size
    if spread: L.spread = spread
    ob = bpy.data.objects.new(name, L); ob.location = loc
    bpy.context.scene.collection.objects.link(ob); look_at(ob, target)
    return ob

def studio(sc):
    w = bpy.data.worlds.new("Estudio_oscuro"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.0015, 0.0015, 0.0018, 1)
    c = (0, 0, 0)
    area("Luz_Cenital", (0, -500, 4600), c, 4200, 7000, size_y=1500)
    area("Luz_Tira_Izq", (-2600, -1400, 500), c, 400, 1500, size_y=2600)
    area("Luz_Tira_Der", (2400, -1800, 300), c, 300, 900, size_y=2400)
    area("Luz_Frontal_Suave", (300, -3200, 900), c, 2400, 500, size_y=1200)
    area("Luz_Contra_Naranja", (1700, 2300, 700), c, 1200, 1500, color=ORANGE, size_y=1800)
    area("Luz_Contra_Naranja_2", (-2100, 1900, -500), c, 900, 450, color=ORANGE, size_y=1600)
    area("Luz_Piso_Naranja", (0, 300, -2300), c, 2400, 70, color=ORANGE)

def camera(sc, loc, target, lens=70, name="Camara"):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.sensor_width = 36
    cd.clip_start = 10; cd.clip_end = 100000
    ob = bpy.data.objects.new(name, cd); ob.location = loc
    sc.collection.objects.link(ob); look_at(ob, target); sc.camera = ob
    return ob

def cycles(sc, w=1920, h=1080, samples=96, threads=0):
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'CPU'; cy.samples = samples
    cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02
    cy.use_denoising = True
    try: cy.denoiser = 'OPENIMAGEDENOISE'
    except Exception: pass
    cy.max_bounces = 6; cy.diffuse_bounces = 2; cy.glossy_bounces = 4; cy.transmission_bounces = 2
    cy.caustics_reflective = False; cy.caustics_refractive = False
    cy.sample_clamp_indirect = 6
    sc.render.resolution_x = w; sc.render.resolution_y = h; sc.render.resolution_percentage = 100
    sc.render.use_persistent_data = False
    if threads: sc.render.threads_mode = 'FIXED'; sc.render.threads = threads
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception as e: print("look:", e)
    sc.render.image_settings.file_format = 'PNG'

def render(sc, path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

def clay_override(sc, on=True):
    m = bpy.data.materials.get("Arcilla")
    if not m:
        m = bpy.data.materials.new("Arcilla"); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.55, 0.55, 0.55, 1); b.inputs["Roughness"].default_value = 0.6
    bpy.context.view_layer.material_override = m if on else None
