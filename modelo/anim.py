"""Animacion de 12 s (288 cuadros, 24 fps): abre en capas girando 360, flota 1 s, cierra con clic.
uso: python3 anim.py <salida> <muestras> <escala> [desde hasta paso] ; 'bake' guarda el .blend animado."""
import sys, os, math, time, bpy
sys.path.insert(0, '/home/claude/kit')
import kit_build as K, render_lib as RL
from mathutils import Vector
FPS, N = 24, 288
T_OPEN0, T_OPEN1, T_HOLD1, T_CLOSE1 = 0.5, 6.0, 7.0, 10.6     # segundos
CLICK_F = int(T_CLOSE1 * FPS)

def E_of(t):
    if t <= T_OPEN0: return 0.0
    if t < T_OPEN1: return (t - T_OPEN0) / (T_OPEN1 - T_OPEN0)
    if t <= T_HOLD1: return 1.0
    if t < T_CLOSE1:
        u = (t - T_HOLD1) / (T_CLOSE1 - T_HOLD1)
        return 1.0 - u ** 1.6          # acelera hacia el cierre: llega con golpe
    return 0.0

def _q(u):
    u = max(0.0, min(1.0, u)); return u * u * u * (u * (6 * u - 15) + 10)

def theta(f):
    """360 grados completos durante la apertura; deriva leve mientras flota; vuelve al frente al cerrar."""
    t = f / FPS
    if t <= T_OPEN1: return 2 * math.pi * _q((t - 0.2) / (T_OPEN1 - 0.2))
    if t <= T_HOLD1: return 2 * math.pi + 0.10 * _q((t - T_OPEN1) / (T_HOLD1 - T_OPEN1))
    return 2 * math.pi + 0.10 * (1 - _q((t - T_HOLD1) / (T_CLOSE1 - T_HOLD1)))

def smooth(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)

def pose(sc, rig, cam, lights, f):
    t = f / FPS
    E = E_of(t)
    K.set_explode(E)
    rig.rotation_euler = (0, 0, theta(f))
    # clic: pulso de escala y destello naranja
    d = f - CLICK_F
    s = 1.0
    flash = 1.0
    if 0 <= d < 10:
        s = 1.0 - 0.018 * math.exp(-d / 2.2) * math.cos(d * 1.3)
        flash = 1.0 + 2.2 * math.exp(-d / 2.5)
    rig.scale = (s, s, s)
    for L, e0 in lights: L.data.energy = e0 * flash
    # camara: se aleja a medida que el kit se abre
    k = smooth(E * 1.15)
    a = Vector((-1900, -3000, 850)); ta = Vector((40, 0, -60))
    b = Vector((-3100, -6200, 1900)); tb = Vector((0, 0, -40))
    cam.location = a.lerp(b, k); RL.look_at(cam, ta.lerp(tb, k))

def setup():
    sc, rig, M = K.build()
    RL.studio(sc)
    cam = RL.camera(sc, (-1750, -2750, 820), (40, 0, -60), lens=62)
    lights = [(bpy.data.objects[n], bpy.data.objects[n].data.energy) for n in ("Luz_Contra_Naranja", "Luz_Contra_Naranja_2")]
    sc.render.fps = FPS; sc.frame_start = 0; sc.frame_end = N - 1
    return sc, rig, cam, lights

if __name__ == "__main__":
    out = sys.argv[1]; samples = int(sys.argv[2]); scale = float(sys.argv[3])
    sc, rig, cam, lights = setup()
    if len(sys.argv) > 4 and sys.argv[4] == 'bake':
        for f in range(N):
            pose(sc, rig, cam, lights, f)
            for o in K.PARTS: o.keyframe_insert("location", frame=f)
            rig.keyframe_insert("rotation_euler", frame=f); rig.keyframe_insert("scale", frame=f)
            cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
            for L, e0 in lights: L.data.keyframe_insert("energy", frame=f)
        RL.cycles(sc, 1920, 1080, samples)
        bpy.ops.wm.save_as_mainfile(filepath=out); sys.exit()
    a, b, st = (int(x) for x in sys.argv[4:7]) if len(sys.argv) > 6 else (0, N, 1)
    clay = len(sys.argv) > 7 and sys.argv[7] == 'clay'
    RL.cycles(sc, int(1920 * scale), int(1080 * scale), samples)
    if clay: RL.clay_override(sc, True)
    os.makedirs(out, exist_ok=True)
    for f in range(a, b, st):
        p = f"{out}/f_{f:04d}.png"
        if os.path.exists(p): continue
        t0 = time.time(); pose(sc, rig, cam, lights, f); RL.render(sc, p)
        with open(out + "/tiempos.log", "a") as fh: fh.write(f"{f} {time.time() - t0:.1f}\n")
