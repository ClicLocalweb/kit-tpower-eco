# Cuadros de prueba de bomba, valvula y joystick (armado y despiece)
# uso: python3 closeups.py <outdir> <samples> <scale> <shots...>
import sys, time, bpy
from mathutils import Vector
sys.path.insert(0, '/home/claude/kit')
import kit_build as K, render_lib as RL
sc, rig, M = K.build()
print("piezas:", len(K.PARTS))
RL.studio(sc)
out = sys.argv[1]; samples = int(sys.argv[2]); scale = float(sys.argv[3])
RL.cycles(sc, int(1920 * scale), int(1080 * scale), samples)
cam = RL.camera(sc, (-1500, -2300, 750), (0, 0, -80), lens=62)

def bbox(prefix):
    bpy.context.view_layer.update()
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(prefix):
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return lo, hi

SH = {  # nombre: (E, cam, objetivo, lente, fstop o None)
    'val0': (0, (-250, -760, 640), (245, -10, 352), 62, None),
    'val1': (1, (-420, -2300, 1560), (275, 0, 870), 62, None),
    'joy0': (0, (1150, -560, 230), (725, -30, 0), 85, None),
    'joy1': (1, (2550, -500, 380), (1200, -55, 25), 50, 0.016),
    'bom0': (0, (430, -900, -240), (-5, -10, -440), 70, None),
    'bom1': (1, (-620, -1750, -330), (-10, -520, -716), 58, None),
    'joy1s': (1, (2250, -730, 420), (1200, -78, 20), 50, None),
    'hero': (0, (-1900, -3000, 850), (40, 0, -60), 62, None),
    'exp':  (1, (-3050, -6100, 1900), (60, 0, -20), 62, None),
}
for s in sys.argv[4:]:
    if s == 'bbox':
        for E in (0, 1):
            K.set_explode(E)
            for p in ('Valvula_', 'Neumatica_Mando', 'Bomba_'):
                lo, hi = bbox(p)
                print(E, p, [round(v) for v in lo], [round(v) for v in hi])
        continue
    if s == 'save':
        K.set_explode(0); K.export_parts_csv(out + '/piezas.csv'); bpy.ops.wm.save_as_mainfile(filepath=out + '/kit_hidraulico.blend'); continue
    E, loc, tgt, lens, fs = SH[s]
    t = time.time()
    for o in bpy.data.objects:
        if o.type in ('MESH', 'FONT', 'CURVE'):
            o.hide_render = (s == 'joy1s' and not o.name.startswith('Neumatica_Mando'))
    K.set_explode(E); cam.location = loc; RL.look_at(cam, tgt); cam.data.lens = lens; cam.data.dof.use_dof = bool(fs)
    if fs:
        cam.data.dof.focus_distance = (Vector(loc) - Vector(tgt)).length; cam.data.dof.aperture_fstop = fs
    RL.render(sc, f"{out}/{s}.png"); print(s, "render s:", round(time.time() - t, 1))
