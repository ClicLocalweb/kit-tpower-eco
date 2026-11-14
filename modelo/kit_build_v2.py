"""
Kit hidraulico (concepto no oficial inspirado en el T-Power ECO) - modelo completo en bpy.
Escala real: 1 unidad de Blender = 1 mm.
Cada pieza lleva: nombre, grupo, orden y vector de explosion (propiedades personalizadas).
Ejes: X = eje largo del deposito, Z = arriba, -Y = frente.
"""
import bpy, bmesh, math
from math import sin, cos, pi, radians, sqrt
from mathutils import Vector, Matrix

FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
ORANGE = (1.0, 0.33, 0.02, 1)

# ---------------------------------------------------------------- medidas (mm)
TANK_R = 230.0        # estimado (diametro 460)
TANK_CYL = 1060.0      # largo de la parte cilindrica (estimado)
HEAD_FLANGE = 25.0
HEAD_DEPTH = 75.0     # largo total = 860 + 2*(25+75) = 1060 (estimado)
SHELL_T = 3.0

PARTS = []


# ================================================================ utilidades
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 0.001
    sc.unit_settings.length_unit = 'MILLIMETERS'
    return sc


def T(x=0, y=0, z=0):
    return Matrix.Translation((x, y, z))


def AX(axis, loc=(0, 0, 0)):
    """Matriz que lleva el eje local Z al eje pedido y traslada a loc."""
    if isinstance(axis, str):
        d = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1),
             '-X': (-1, 0, 0), '-Y': (0, -1, 0), '-Z': (0, 0, -1)}[axis]
    else:
        d = axis
    q = Vector((0, 0, 1)).rotation_difference(Vector(d).normalized())
    return Matrix.Translation(loc) @ q.to_matrix().to_4x4()


def add_lathe(bm, prof, M=None, segs=64, closed=True):
    """prof: lista (a, r); a sobre eje local Z. closed=True une ultimo con primero."""
    M = M or Matrix()
    rings = []
    for a, r in prof:
        if r < 1e-6:
            rings.append([bm.verts.new(M @ Vector((0, 0, a)))])
        else:
            rings.append([bm.verts.new(M @ Vector((r * cos(2 * pi * i / segs), r * sin(2 * pi * i / segs), a)))
                          for i in range(segs)])
    n = len(rings)
    rng = range(n) if closed else range(n - 1)
    faces = []
    for k in rng:
        A, B = rings[k], rings[(k + 1) % n]
        if len(A) == 1 and len(B) == 1:
            continue
        for i in range(segs):
            j = (i + 1) % segs
            try:
                if len(A) == 1:
                    faces.append(bm.faces.new((A[0], B[j], B[i])))
                elif len(B) == 1:
                    faces.append(bm.faces.new((A[i], A[j], B[0])))
                else:
                    faces.append(bm.faces.new((A[i], A[j], B[j], B[i])))
            except ValueError:
                pass
    return faces


def add_prism(bm, pts, depth, M=None, z0=None):
    """Extruye un poligono (plano XY local) a lo largo de Z local. Centrado salvo z0."""
    M = M or Matrix()
    zb = -depth / 2 if z0 is None else z0
    bot = [bm.verts.new(M @ Vector((x, y, zb))) for x, y in pts]
    top = [bm.verts.new(M @ Vector((x, y, zb + depth))) for x, y in pts]
    n = len(pts)
    try:
        bm.faces.new(bot[::-1])
        bm.faces.new(top)
    except ValueError:
        pass
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))


def add_box(bm, sx, sy, sz, M=None):
    add_prism(bm, [(-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2)], sz, M)


def add_cyl(bm, r, h, M=None, segs=48, z0=None):
    zb = -h / 2 if z0 is None else z0
    add_lathe(bm, [(zb, 0), (zb, r), (zb + h, r), (zb + h, 0)], M, segs, closed=False)


def add_tube(bm, ro, ri, h, M=None, segs=48, z0=None):
    zb = -h / 2 if z0 is None else z0
    add_lathe(bm, [(zb, ri), (zb, ro), (zb + h, ro), (zb + h, ri)], M, segs)


def add_torus(bm, R, r, M=None, segs=48, rsegs=12):
    prof = [(r * sin(2 * pi * k / rsegs), R + r * cos(2 * pi * k / rsegs)) for k in range(rsegs)]
    add_lathe(bm, prof, M, segs)


def circle(r, n=32, cx=0, cy=0, a0=0):
    return [(cx + r * cos(a0 + 2 * pi * i / n), cy + r * sin(a0 + 2 * pi * i / n)) for i in range(n)]


def rrect(w, h, r, n=6):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, pi / 2),
                       (-w / 2 + r, -h / 2 + r, pi), (w / 2 - r, -h / 2 + r, 3 * pi / 2)):
        for i in range(n + 1):
            a = a0 + (pi / 2) * i / n
            pts.append((cx + r * cos(a), cy + r * sin(a)))
    return pts


def hull_pts(circles, n=20):
    """Contorno convexo de una lista de circulos (cx, cy, r)."""
    from mathutils.geometry import convex_hull_2d
    pts = []
    for cx, cy, r in circles:
        pts += circle(r, n, cx, cy)
    idx = convex_hull_2d(pts)
    return [pts[i] for i in idx]


def gear_pts(nt, rr, ro, a0=0):
    pts = []
    for t in range(nt):
        for f, r in ((0.0, rr), (0.18, rr), (0.34, ro), (0.66, ro), (0.82, rr)):
            a = a0 + 2 * pi * (t + f) / nt
            pts.append((r * cos(a), r * sin(a)))
    return pts


def fig8_pts(r, c, n=28):
    """Contorno de dos circulos de radio r con centros en (0, +-c)."""
    a = math.asin(c / r) if c < r else pi / 2
    pts = []
    for i in range(n + 1):          # circulo superior
        t = -a + (pi + 2 * a) * i / n
        pts.append((r * cos(t), c + r * sin(t)))
    for i in range(n + 1):          # circulo inferior
        t = pi - a + (pi + 2 * a) * i / n
        pts.append((r * cos(t), -c + r * sin(t)))
    return pts


def add_hexbolt(bm, d, length, M=None, head=None):
    """Bulon: cabeza hexagonal en z>=0, vastago hacia -z."""
    M = M or Matrix()
    s = head or d * 1.6
    add_prism(bm, circle(s / 2 / cos(pi / 6), 6), d * 0.65, M, z0=0)
    add_cyl(bm, d / 2, length, M, segs=16, z0=-length)


def add_hexnut(bm, d, M=None, h=None):
    h = h or d * 0.8
    add_prism(bm, circle(d * 0.92, 6), h, M)


def catmull(pts, samples=14):
    P = [Vector(p) for p in pts]
    P = [P[0] + (P[0] - P[1])] + P + [P[-1] + (P[-1] - P[-2])]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for s in range(samples):
            t = s / samples
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2].copy())
    return out


def add_sweep(bm, path, radius, segs=16, caps=True):
    """Barre un circulo por una polilinea (marcos por transporte paralelo)."""
    path = [Vector(p) for p in path]
    n = len(path)
    tang = []
    for i in range(n):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, n - 1)]
        tang.append((b - a).normalized())
    up = Vector((0, 0, 1)) if abs(tang[0].z) < 0.9 else Vector((1, 0, 0))
    nrm = tang[0].cross(up).normalized()
    rings = []
    frames = []
    for i in range(n):
        if i > 0:
            q = tang[i - 1].rotation_difference(tang[i])
            nrm = (q @ nrm).normalized()
        bn = tang[i].cross(nrm).normalized()
        frames.append((path[i], nrm.copy(), bn))
        rr = radius(i / (n - 1)) if callable(radius) else radius
        rings.append([bm.verts.new(path[i] + rr * (cos(2 * pi * k / segs) * nrm + sin(2 * pi * k / segs) * bn))
                      for k in range(segs)])
    for i in range(n - 1):
        for k in range(segs):
            j = (k + 1) % segs
            bm.faces.new((rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]))
    if caps:
        bm.faces.new(rings[0][::-1])
        bm.faces.new(rings[-1])
    return frames


def helix_on_path(frames, R, turns_per_mm, per_turn=14):
    """Helice alrededor de un recorrido. Interpola entre marcos para que cada vuelta tenga puntos suficientes."""
    pts = []
    dist = 0.0
    step = 1.0 / (turns_per_mm * per_turn)          # mm entre puntos
    for i in range(len(frames) - 1):
        p0, n0, b0 = frames[i]
        p1, n1, b1 = frames[i + 1]
        seg = (p1 - p0).length
        k = max(1, int(math.ceil(seg / step)))
        for j in range(k):
            t = j / k
            p = p0.lerp(p1, t); n = n0.lerp(n1, t).normalized(); b = b0.lerp(b1, t).normalized()
            a = 2 * pi * turns_per_mm * (dist + seg * t)
            pts.append(p + R * (cos(a) * n + sin(a) * b))
        dist += seg
    return pts


def boolean_cut(bm, cutter_bm):
    """Resta cutter_bm de bm (solver exacto). Devuelve un bmesh nuevo."""
    m1 = bpy.data.meshes.new("_t"); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(m1); bm.free()
    m2 = bpy.data.meshes.new("_c"); bmesh.ops.recalc_face_normals(cutter_bm, faces=cutter_bm.faces)
    cutter_bm.to_mesh(m2); cutter_bm.free()
    o1 = bpy.data.objects.new("_t", m1); o2 = bpy.data.objects.new("_c", m2)
    col = bpy.context.scene.collection
    col.objects.link(o1); col.objects.link(o2)
    md = o1.modifiers.new("b", 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = o2; md.solver = 'EXACT'; md.use_self = True
    dg = bpy.context.evaluated_depsgraph_get()
    res = bpy.data.meshes.new_from_object(o1.evaluated_get(dg))
    out = bmesh.new(); out.from_mesh(res)
    bpy.data.objects.remove(o1); bpy.data.objects.remove(o2)
    bpy.data.meshes.remove(m1); bpy.data.meshes.remove(m2); bpy.data.meshes.remove(res)
    return out


def part(name, bm, grupo, orden, explode, mat, bevel=0.0, sharp=38, desc="", real=False):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    cname = "KIT_" + grupo
    col = bpy.data.collections.get(cname)
    if not col:
        col = bpy.data.collections.new(cname)
        bpy.context.scene.collection.children.link(col)
    col.objects.link(ob)
    xs = [v.co for v in me.vertices]
    mn = Vector((min(v.x for v in xs), min(v.y for v in xs), min(v.z for v in xs)))
    mx = Vector((max(v.x for v in xs), max(v.y for v in xs), max(v.z for v in xs)))
    c = (mn + mx) / 2
    me.transform(Matrix.Translation(-c))
    ob.location = c
    me.shade_smooth()
    me.set_sharp_from_angle(angle=radians(sharp))
    if bevel > 0:
        md = ob.modifiers.new("Bisel", 'BEVEL')
        md.width = bevel; md.segments = 2; md.limit_method = 'ANGLE'; md.angle_limit = radians(sharp)
        md.harden_normals = True
    me.materials.append(mat)
    ob["grupo"] = grupo
    ob["orden"] = orden
    ob["explode"] = [float(v) for v in explode]
    ob["base"] = [c.x, c.y, c.z]
    ob["descripcion"] = desc
    ob["fuente"] = "foto/ficha" if real else "generico/estimado"
    ob.parent = bpy.data.objects["RIG_giro"]
    PARTS.append(ob)
    return ob


# ================================================================ materiales
def _base(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    return m, nt, b, tc


def _set(b, **kw):
    names = {'color': 'Base Color', 'metal': 'Metallic', 'rough': 'Roughness', 'aniso': 'Anisotropic',
             'coat': 'Coat Weight', 'coat_rough': 'Coat Roughness', 'spec': 'Specular IOR Level',
             'alpha': 'Alpha', 'emit': 'Emission Color', 'emit_s': 'Emission Strength'}
    for k, v in kw.items():
        if names[k] in b.inputs:
            b.inputs[names[k]].default_value = v


def _noise_bump(nt, b, tc, scale, strength, detail=4.0, stretch=None, rough_var=0.0, rough=0.3, dist=0.2):
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    if stretch:
        mp.inputs["Scale"].default_value = stretch
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = strength
    bp.inputs["Distance"].default_value = dist
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    if rough_var > 0:
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.3; mr.inputs["From Max"].default_value = 0.7
        mr.inputs["To Min"].default_value = max(rough - rough_var, 0.02)
        mr.inputs["To Max"].default_value = rough + rough_var
        nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])


def make_materials():
    M = {}
    # pintura negra en polvo, satinada (deposito)
    m, nt, b, tc = _base("Pintura_negra_satinada")
    _set(b, color=(0.012, 0.012, 0.013, 1), metal=0.0, rough=0.32, coat=0.35, coat_rough=0.18)
    _noise_bump(nt, b, tc, 1.6, 0.10, detail=2, rough_var=0.03, rough=0.32, dist=0.15)
    M['negro'] = m
    # negro texturado (soportes)
    m, nt, b, tc = _base("Pintura_negra_texturada")
    _set(b, color=(0.014, 0.014, 0.015, 1), rough=0.5)
    _noise_bump(nt, b, tc, 3.5, 0.35, detail=3, rough_var=0.06, rough=0.5, dist=0.2)
    M['negro_tex'] = m
    # acero pulido
    m, nt, b, tc = _base("Acero_pulido")
    _set(b, color=(0.78, 0.79, 0.80, 1), metal=1.0, rough=0.09)
    _noise_bump(nt, b, tc, 0.9, 0.015, detail=3, rough_var=0.03, rough=0.09, dist=0.05)
    M['pulido'] = m
    # acero cepillado
    m, nt, b, tc = _base("Acero_cepillado")
    _set(b, color=(0.62, 0.63, 0.65, 1), metal=1.0, rough=0.28, aniso=0.7)
    _noise_bump(nt, b, tc, 2.2, 0.12, detail=6, stretch=(0.02, 1.0, 1.0), rough_var=0.08, rough=0.28, dist=0.05)
    M['cepillado'] = m
    # cincado (conexiones y bulones)
    m, nt, b, tc = _base("Acero_cincado")
    _set(b, color=(0.70, 0.72, 0.74, 1), metal=1.0, rough=0.22)
    _noise_bump(nt, b, tc, 0.7, 0.05, detail=4, rough_var=0.07, rough=0.22, dist=0.05)
    M['cincado'] = m
    # fundicion de hierro (bomba)
    m, nt, b, tc = _base("Fundicion_hierro")
    _set(b, color=(0.11, 0.115, 0.12, 1), metal=1.0, rough=0.55)
    _noise_bump(nt, b, tc, 1.1, 0.55, detail=5, rough_var=0.1, rough=0.55, dist=0.35)
    M['fundicion'] = m
    # aluminio fundido (valvula, cabezal de filtro)
    m, nt, b, tc = _base("Aluminio_fundido")
    _set(b, color=(0.34, 0.35, 0.36, 1), metal=1.0, rough=0.45)
    _noise_bump(nt, b, tc, 1.4, 0.4, detail=5, rough_var=0.08, rough=0.42, dist=0.25)
    M['aluminio'] = m
    # fundicion pintada de gris (cuerpo de la valvula, como en el catalogo)
    m, nt, b, tc = _base("Fundicion_pintada_gris")
    _set(b, color=(0.07, 0.075, 0.082, 1), metal=0.0, rough=0.42, coat=0.15, coat_rough=0.3)
    _noise_bump(nt, b, tc, 1.2, 0.5, detail=5, rough_var=0.08, rough=0.42, dist=0.3)
    M['fund_gris'] = m
    # caucho
    m, nt, b, tc = _base("Caucho")
    _set(b, color=(0.016, 0.016, 0.017, 1), rough=0.62)
    _noise_bump(nt, b, tc, 2.5, 0.25, detail=3, rough_var=0.05, rough=0.62, dist=0.15)
    M['caucho'] = m
    # plastico naranja (unico color)
    m, nt, b, tc = _base("Plastico_naranja")
    _set(b, color=(0.9, 0.22, 0.01, 1), rough=0.38, coat=0.2, coat_rough=0.15, emit=ORANGE, emit_s=0.03)
    _noise_bump(nt, b, tc, 2.0, 0.05, detail=2, dist=0.1)
    M['naranja'] = m
    # tubo plastico negro (neumatico)
    m, nt, b, tc = _base("Poliamida_negra")
    _set(b, color=(0.01, 0.01, 0.011, 1), rough=0.22)
    M['poliamida'] = m
    # papel filtrante
    m, nt, b, tc = _base("Papel_filtrante")
    _set(b, color=(0.72, 0.70, 0.66, 1), rough=0.85)
    _noise_bump(nt, b, tc, 4.0, 0.3, detail=4, dist=0.2)
    M['papel'] = m
    # vidrio del visor
    m, nt, b, tc = _base("Visor")
    _set(b, color=(0.9, 0.45, 0.1, 1), rough=0.05, coat=1.0, emit=ORANGE, emit_s=0.25)
    M['visor'] = m
    # letras
    m, nt, b, tc = _base("Grafica_blanca")
    _set(b, color=(0.85, 0.85, 0.85, 1), rough=0.45)
    M['blanco'] = m
    m, nt, b, tc = _base("Grafica_naranja")
    _set(b, color=ORANGE, rough=0.4, emit=ORANGE, emit_s=0.35)
    M['graf_naranja'] = m
    # malla perforada (canasto de la boca de carga)
    m, nt, b, tc = _base("Malla_perforada")
    _set(b, color=(0.6, 0.61, 0.63, 1), metal=1.0, rough=0.3)
    sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
    at = nt.nodes.new("ShaderNodeMath"); at.operation = 'ARCTAN2'
    nt.links.new(sx.outputs["Y"], at.inputs[0]); nt.links.new(sx.outputs["X"], at.inputs[1])
    s1 = nt.nodes.new("ShaderNodeMath"); s1.operation = 'SINE'
    k1 = nt.nodes.new("ShaderNodeMath"); k1.operation = 'MULTIPLY'; k1.inputs[1].default_value = 26
    nt.links.new(at.outputs[0], k1.inputs[0]); nt.links.new(k1.outputs[0], s1.inputs[0])
    s2 = nt.nodes.new("ShaderNodeMath"); s2.operation = 'SINE'
    k2 = nt.nodes.new("ShaderNodeMath"); k2.operation = 'MULTIPLY'; k2.inputs[1].default_value = 0.9
    nt.links.new(sx.outputs["Z"], k2.inputs[0]); nt.links.new(k2.outputs[0], s2.inputs[0])
    mu = nt.nodes.new("ShaderNodeMath"); mu.operation = 'MULTIPLY'
    nt.links.new(s1.outputs[0], mu.inputs[0]); nt.links.new(s2.outputs[0], mu.inputs[1])
    ab = nt.nodes.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; nt.links.new(mu.outputs[0], ab.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath"); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.45
    nt.links.new(ab.outputs[0], lt.inputs[0]); nt.links.new(lt.outputs[0], b.inputs["Alpha"])
    M['malla'] = m
    return M


# ================================================================ texto curvado sobre el deposito
def tank_text(body, size, x_center, arc_center_deg, mat, name, R=TANK_R + 0.7):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = size
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    try:
        cu.font = bpy.data.fonts.load(FONT_BOLD)
    except Exception:
        pass
    ob = bpy.data.objects.new("_txt", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob)
    bm = bmesh.new(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    for _ in range(2):
        bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if e.calc_length() > size * 0.25], cuts=1)
        bmesh.ops.triangulate(bm, faces=bm.faces)
    a0 = radians(arc_center_deg)
    for v in bm.verts:
        a = a0 + v.co.y / R
        v.co = Vector((x_center + v.co.x, -R * cos(a), R * sin(a)))
    return bm


# ================================================================ construccion
def build():
    sc = reset_scene()
    rig = bpy.data.objects.new("RIG_giro", None)
    sc.collection.objects.link(rig)
    M = make_materials()
    R = TANK_R
    hx = TANK_CYL / 2

    # ------------------------------------------------ DEPOSITO
    G = "deposito"
    FILL_X, FILT_X = -410.0, 230.0
    bm = bmesh.new()
    prof = [(-hx, R), (-hx + 35, R), (-hx + 41, R + 6), (-hx + 69, R + 6), (-hx + 75, R),
            (hx - 75, R), (hx - 69, R + 6), (hx - 41, R + 6), (hx - 35, R), (hx, R),
            (hx, R - SHELL_T), (-hx, R - SHELL_T)]
    add_lathe(bm, prof, AX('X'), segs=128)
    cb = bmesh.new()
    add_cyl(cb, 36, 80, AX('Z', (FILL_X, 0, R)), segs=48)
    add_cyl(cb, 44, 80, AX('Z', (FILT_X, 0, R)), segs=48)
    add_cyl(cb, 16, 60, AX('Z', (-190, -70, -R + 8)), segs=32)
    bm = boolean_cut(bm, cb)
    # brida soldada del filtro de retorno, patas soldadas, cupla de succion
    add_tube(bm, 72, 44, 14, AX('Z', (FILT_X, 0, R - 3)), z0=0)
    add_tube(bm, 50, 36, 10, AX('Z', (FILL_X, 0, R - 3)), z0=0)
    for sx_ in (-400, 400):
        for sy_ in (-130, 130):
            add_box(bm, 70, 60, 50, T(sx_, sy_, -R + 12))
            add_box(bm, 90, 80, 8, T(sx_, sy_, -R - 16))
    sy_ = -70
    add_tube(bm, 26, 16, 36, AX('Z', (-190, sy_, -sqrt(R * R - sy_ * sy_) - 28)), z0=0)
    part("Deposito_Cuerpo", bm, G, 0, (0, 0, 0), M['negro'], bevel=0.8,
         desc="Cuerpo cilindrico de chapa, con bandas de refuerzo, patas y bridas soldadas", real=True)

    def head_prof(t=SHELL_T):
        pr = [(0, R)]
        n = 20
        for i in range(n + 1):
            a = (pi / 2) * i / n
            pr.append((HEAD_FLANGE + HEAD_DEPTH * sin(a), R * cos(a)))
        for i in range(n, -1, -1):
            a = (pi / 2) * i / n
            pr.append((HEAD_FLANGE + (HEAD_DEPTH - t) * sin(a), max((R - t) * cos(a), 0)))
        pr.append((0, R - t))
        # quitar radios cero duplicados
        out = []
        for a_, r_ in pr:
            if out and r_ < 1e-6 and out[-1][1] < 1e-6 and abs(out[-1][0] - a_) < 1e-6:
                continue
            out.append((a_, r_))
        return out

    def head_x(rad):
        return HEAD_FLANGE + HEAD_DEPTH * sqrt(max(1 - (rad / R) ** 2, 0))

    for side, sgn in (("Izq", -1), ("Der", 1)):
        bm = bmesh.new()
        add_lathe(bm, head_prof(), AX('X' if sgn > 0 else '-X', (sgn * hx, 0, 0)), segs=128)
        add_torus(bm, R + 0.5, 3.0, AX('X', (sgn * (hx + 1), 0, 0)), segs=128, rsegs=8)
        if sgn < 0:
            for zz in (95, 15):
                rad = sqrt(110 ** 2 + zz ** 2)
                add_tube(bm, 24, 15, 14, AX('-X', (-hx - head_x(rad) + 6, -110, zz)), z0=0, segs=32)
        part(f"Deposito_Tapa_{side}", bm, G, 6, (sgn * 210, 0, 0), M['negro'], bevel=0.6,
             desc="Tapa bombeada del deposito", real=True)

    # deflector interno (generico)
    bm = bmesh.new()
    add_tube(bm, R - SHELL_T - 1, 70, 3, AX('X', (-40, 0, 0)), segs=96)
    part("Deposito_Deflector", bm, G, 0, (0, 0, 0), M['cepillado'],
         desc="Chapa rompeolas interna (generica)")

    # visores de nivel
    for i, zz in enumerate((95, 15)):
        rad = sqrt(110 ** 2 + zz ** 2)
        x0 = -hx - head_x(rad) - 6
        bm = bmesh.new()
        Mv = AX('-X', (x0, -110, zz))
        add_prism(bm, circle(21, 6), 10, Mv, z0=0)
        add_tube(bm, 17, 11, 6, Mv, z0=10, segs=32)
        part(f"Visor_Nivel_{i + 1}_Cuerpo", bm, G, 7, (-330, 0, 0), M['pulido'], bevel=0.5,
             desc="Visor de nivel de aceite", real=True)
        bm = bmesh.new()
        add_cyl(bm, 11.5, 4, Mv, z0=9, segs=32)
        part(f"Visor_Nivel_{i + 1}_Cristal", bm, G, 7, (-330, 0, 0), M['visor'], desc="Cristal del visor")

    # boca de carga
    bm = bmesh.new()
    add_lathe(bm, [(0, 36), (150, 36), (150, 44), (160, 44), (160, 32), (0, 32)], AX('Z', (FILL_X, 0, R + 6)))
    part("Carga_Cuello", bm, G, 5, (0, 0, 160), M['negro'], bevel=0.6, desc="Cuello de la boca de carga", real=True)
    bm = bmesh.new()
    add_lathe(bm, [(-140, 0), (-140, 27), (0, 27), (0, 34), (3, 34), (3, 25), (-137, 25), (-137, 0)],
              AX('Z', (FILL_X, 0, R + 166)), segs=48, closed=False)
    part("Carga_Canasto_Filtro", bm, G, 5, (0, 0, 310), M['malla'], desc="Canasto filtro de la boca de carga (generico)")
    bm = bmesh.new()
    Mc = AX('Z', (FILL_X, 0, R + 168))
    add_prism(bm, gear_pts(40, 53, 55.5), 46, Mc, z0=0)
    add_lathe(bm, [(46, 0), (46, 53), (52, 49), (58, 30), (60, 0)], Mc, closed=False)
    add_cyl(bm, 46, 8, Mc, z0=-6)
    part("Carga_Tapa_Respiradero", bm, G, 5, (0, 0, 400), M['negro_tex'], bevel=0.5,
         desc="Tapa con respiradero y filtro de aire", real=True)
    bm = bmesh.new()
    add_torus(bm, 49, 2.2, AX('Z', (FILL_X, 0, R + 166)), rsegs=8)
    part("Carga_Aro_Naranja", bm, G, 5, (0, 0, 355), M['naranja'], desc="Aro de sello de la tapa (generico)")

    # tapon de drenaje (generico)
    bm = bmesh.new()
    Md = AX('-Z', (190, 60, -sqrt(R * R - 60 * 60) + 2))
    add_prism(bm, circle(13, 6), 9, Md, z0=0)
    add_cyl(bm, 9, 4, Md, z0=-4, segs=20)
    part("Deposito_Tapon_Drenaje", bm, G, 8, (0, 0, -70), M['cincado'], bevel=0.4, desc="Tapon de drenaje (generico)")

    # graficas (sin logo oficial)
    bm = tank_text("T-POWER ECO", 66, 0, 25, M['blanco'], "txt1")
    part("Grafica_Nombre", bm, G, 0, (0, 0, 0), M['blanco'], desc="Nombre del modelo en texto plano, sin logo oficial")
    bm = tank_text("KIT HIDRAULICO  ·  200 L  ·  CONCEPTO", 20, 0, 8.5, M['graf_naranja'], "txt2")
    part("Grafica_Subtitulo", bm, G, 0, (0, 0, 0), M['graf_naranja'], desc="Leyenda de concepto")
    bm = bmesh.new()
    Rr = R + 0.7
    a1, a2 = radians(14.3), radians(15.1)
    v = [bm.verts.new((-235, -Rr * cos(a1), Rr * sin(a1))), bm.verts.new((235, -Rr * cos(a1), Rr * sin(a1))),
         bm.verts.new((235, -Rr * cos(a2), Rr * sin(a2))), bm.verts.new((-235, -Rr * cos(a2), Rr * sin(a2)))]
    bm.faces.new(v)
    part("Grafica_Linea", bm, G, 0, (0, 0, 0), M['graf_naranja'], desc="Linea grafica")

    # ------------------------------------------------ FILTRO DE RETORNO
    G = "filtro"
    ZT = R + 11
    bm = bmesh.new()
    add_tube(bm, 70, 45, 2.5, AX('Z', (FILT_X, 0, ZT)), z0=0)
    part("Filtro_Junta", bm, G, 4, (0, 0, 270), M['caucho'], desc="Junta del cabezal (generica)")
    bm = bmesh.new()
    Mf = AX('Z', (FILT_X, 0, ZT + 2.5))
    add_prism(bm, gear_pts(44, 33, 40), 190, Mf, z0=-200)
    add_lathe(bm, [(-204, 0), (-204, 41), (-198, 41), (-198, 0)], Mf, closed=False, segs=48)
    part("Filtro_Elemento", bm, G, 4, (0, 0, 215), M['papel'], sharp=60,
         desc="Elemento filtrante plisado (catalogo: 150 L/min; forma generica)")
    bm = bmesh.new()
    add_lathe(bm, [(-10, 26), (-10, 42), (-4, 42), (-4, 26)], Mf, segs=48)
    add_lathe(bm, [(-204, 0), (-204, 42), (-200, 42), (-200, 0)], Mf, closed=False, segs=48)
    part("Filtro_Tapas_Elemento", bm, G, 4, (0, 0, 215), M['cincado'], bevel=0.4, desc="Tapas metalicas del elemento")
    bm = bmesh.new()
    add_lathe(bm, [(0, 30), (0, 72), (12, 72), (16, 60), (58, 60), (62, 72), (72, 72), (72, 30)], Mf, segs=64)
    add_box(bm, 150, 96, 10, T(FILT_X, 0, ZT + 2.5 + 67))
    add_cyl(bm, 24, 30, AX('Y', (FILT_X, 62, ZT + 38)), z0=-4, segs=32)
    part("Filtro_Cabezal", bm, G, 4, (0, 0, 350), M['aluminio'], bevel=1.2,
         desc="Cabezal del filtro de retorno, base de la valvula", real=True)
    bm = bmesh.new()
    Mi = AX('-Y', (FILT_X, -58, ZT + 38))
    add_cyl(bm, 20, 26, Mi, z0=0, segs=40)
    add_prism(bm, gear_pts(20, 20.5, 22.5), 14, Mi, z0=26)
    part("Filtro_Indicador", bm, G, 4, (0, -110, 350), M['naranja'], bevel=0.6,
         desc="Tapa / indicador de saturacion del filtro (en la foto es verde; aca naranja)", real=True)

    # ------------------------------------------------ VALVULA
    G = "valvula"
    VX, VZ = FILT_X, ZT + 2.5 + 72 + 46      # centro del cuerpo
    VE = 480.0                               # elevacion del grupo en la explosion
    bm = bmesh.new()
    add_box(bm, 104, 104, 96, T(VX, 0, VZ))                                   # bloque central
    add_cyl(bm, 31, 34, AX('X', (VX - 52, 0, VZ + 2)), z0=-34, segs=40)       # tambor del resorte
    add_prism(bm, rrect(78, 78, 12), 30, AX('X', (VX + 52, 0, VZ + 2)), z0=0)  # asiento del actuador neumatico (cuadrado, como en el catalogo)
    add_cyl(bm, 22, 22, AX('Z', (VX, 0, VZ - 48)), z0=-22, segs=40)           # rosca 1"-11 BSP de apoyo (azul en el catalogo)
    # brida triangular del puerto grande, con 3 bulones
    FLX, FLZ = VX - 14, VZ + 2
    tri = [(0, 0, 33)] + [(31 * cos(pi / 2 + 2 * pi * k / 3 + pi / 3), 31 * sin(pi / 2 + 2 * pi * k / 3 + pi / 3), 11) for k in range(3)]
    Mfl = Matrix.Translation((FLX, -52, FLZ)) @ Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # local XY -> mundo XZ, local Z -> -Y
    add_prism(bm, hull_pts(tri), 10, Mfl, z0=0)
    for k in range(3):
        a_ = pi / 2 + 2 * pi * k / 3 + pi / 3
        add_hexbolt(bm, 7, 12, AX('-Y', (FLX + 31 * cos(a_), -62, FLZ + 31 * sin(a_))))
    add_cyl(bm, 15, 8, AX('-Y', (VX + 34, -52, VZ - 4)), z0=0, segs=32)       # puerto de presion
    add_cyl(bm, 16, 12, AX('Z', (VX - 22, 0, VZ + 48)), z0=0, segs=32)         # puerto superior (tapon)
    add_cyl(bm, 14, 10, AX('Z', (VX + 30, 0, VZ + 48)), z0=0, segs=32)         # puerto superior (limitadora)
    cb = bmesh.new()
    add_cyl(cb, 22, 44, AX('-Y', (FLX, -30, FLZ)), z0=0, segs=32)
    add_cyl(cb, 11, 40, AX('-Y', (VX + 34, -30, VZ - 4)), z0=0, segs=32)
    add_cyl(cb, 10, 34, AX('Z', (VX - 22, 0, VZ + 30)), z0=0, segs=24)
    add_cyl(cb, 9, 30, AX('Z', (VX + 30, 0, VZ + 30)), z0=0, segs=24)
    bm = boolean_cut(bm, cb)
    part("Valvula_Cuerpo", bm, G, 3, (0, 0, VE), M['fund_gris'], bevel=1.5,
         desc="Cuerpo de la valvula direccional de vuelco (catalogo: 140 L/min, 1\" BSP, 190 bar)", real=True)
    # corredera (generica)
    bm = bmesh.new()
    pr = [(-110, 0), (-110, 8), (-96, 8), (-96, 12.6)]
    for a, b_ in ((-70, -52), (-22, -6), (20, 36), (62, 80)):
        pr += [(a, 12.6), (a + 3, 8.5), (b_ - 3, 8.5), (b_, 12.6)]
    pr += [(100, 12.6), (100, 8), (112, 8), (112, 0)]
    add_lathe(bm, pr, AX('X', (VX, 0, VZ)), closed=False, segs=48)
    part("Valvula_Corredera", bm, G, 3, (-250, 0, VE), M['pulido'], bevel=0.3,
         desc="Corredera (spool) - interno generico")
    # resorte de centrado
    bm = bmesh.new()
    hp = [Vector((VX - 92 - t * 34 / 60, 15 * cos(t * 2 * pi * 6 / 60), VZ + 15 * sin(t * 2 * pi * 6 / 60))) for t in range(61)]
    add_sweep(bm, hp, 1.8, segs=8)
    part("Valvula_Resorte", bm, G, 3, (-345, 0, VE), M['pulido'], desc="Resorte de centrado - interno generico")
    bm = bmesh.new()
    add_torus(bm, 22, 2.4, AX('X', (VX - 85, 0, VZ)), rsegs=8)
    part("Valvula_Oring_Izq", bm, G, 3, (-405, 0, VE), M['caucho'], desc="O-ring - interno generico")
    bm = bmesh.new()
    add_lathe(bm, [(0, 0), (0, 20), (-4, 31), (-44, 31), (-50, 26), (-50, 0)], AX('X', (VX - 84, 0, VZ)), closed=False, segs=48)
    part("Valvula_Tapa_Resorte", bm, G, 3, (-440, 0, VE), M['fund_gris'], bevel=0.8, desc="Tapa del resorte", real=True)
    # mando neumatico
    bm = bmesh.new()
    add_cyl(bm, 27, 9, AX('X', (VX + 96, 0, VZ)), segs=40)
    add_cyl(bm, 8, 20, AX('X', (VX + 106, 0, VZ)), segs=20)
    part("Valvula_Piston_Neumatico", bm, G, 3, (215, 0, VE), M['pulido'], bevel=0.4, desc="Piston del mando neumatico - interno generico")
    bm = bmesh.new()
    add_torus(bm, 27, 2.4, AX('X', (VX + 96, 0, VZ)), rsegs=8)
    part("Valvula_Oring_Piston", bm, G, 3, (215, 0, VE), M['caucho'], desc="O-ring del piston - interno generico")
    bm = bmesh.new()
    Ma = AX('X', (VX + 84, 0, VZ + 2))
    add_prism(bm, rrect(78, 78, 12), 60, Ma, z0=0)
    add_prism(bm, rrect(66, 66, 10), 5, Ma, z0=60)
    part("Valvula_Mando_Neumatico", bm, G, 3, (330, 0, VE), M['fund_gris'], bevel=0.8, desc="Actuador neumatico de la valvula (forma del catalogo; medidas estimadas)", real=True)
    bm = bmesh.new()
    for yy in (-27, 27):
        for zz in (-27, 27):
            Mt = AX('X', (VX + 149, yy, VZ + 2 + zz))
            add_cyl(bm, 5.5, 7, Mt, z0=0, segs=16)                 # cabeza allen
            add_cyl(bm, 3.2, 70, Mt, z0=-70, segs=12)              # vastago
    part("Valvula_Mando_Tornillos", bm, G, 3, (430, 0, VE), M['cincado'], bevel=0.3, desc="Tornillos del actuador neumatico", real=True)
    bm = bmesh.new()
    for zz in (-14, 16):
        Mr = AX('X', (VX + 149, 0, VZ + 2 + zz))
        add_prism(bm, circle(8, 6), 6, Mr, z0=0)
        add_cyl(bm, 6.5, 14, Mr, z0=6, segs=16)
        add_cyl(bm, 6.5, 16, AX('Y', (VX + 149 + 14, 0, VZ + 2 + zz)), z0=0, segs=16)   # codo
    part("Valvula_Mando_Racores", bm, G, 3, (500, 0, VE), M['caucho'], bevel=0.3, desc="Racores de aire del actuador", real=True)
    bm = bmesh.new()
    for zz in (-14, 16):
        add_tube(bm, 7.6, 4, 3, AX('Y', (VX + 149 + 14, 17, VZ + 2 + zz)), segs=20)
    part("Valvula_Mando_Anillos", bm, G, 3, (500, 60, VE), M['naranja'], bevel=0.2, desc="Anillos de los racores de aire (en el catalogo son azules; aca naranja)", real=True)
    # limitadora (generica)
    bm = bmesh.new()
    Ml = AX('Z', (VX + 30, 0, VZ + 58))
    add_cyl(bm, 10, 34, Ml, z0=-34, segs=24)
    add_prism(bm, circle(17, 6), 12, Ml, z0=0)
    add_cyl(bm, 9, 16, Ml, z0=12, segs=24)
    add_prism(bm, circle(10, 6), 8, Ml, z0=28)
    part("Valvula_Limitadora", bm, G, 3, (0, 0, VE + 130), M['pulido'], bevel=0.4,
         desc="Cartucho de valvula limitadora de presion - generico")
    bm = bmesh.new()
    Mp = AX('-Y', (VX - 14, -60, VZ + 2))
    add_cyl(bm, 18, 14, Mp, z0=-12, segs=32)
    add_prism(bm, gear_pts(14, 22, 24), 11, Mp, z0=2)
    part("Valvula_Tapon_Grande", bm, G, 3, (0, -150, VE), M['naranja'], bevel=0.5,
         desc="Tapon del puerto grande (en el catalogo es amarillo; aca naranja)", real=True)
    bm = bmesh.new()
    Mp = AX('Z', (VX - 22, 0, VZ + 58))
    add_cyl(bm, 10, 12, Mp, z0=-12, segs=24)
    add_prism(bm, gear_pts(12, 14, 16), 9, Mp, z0=0)
    part("Valvula_Tapon_Superior", bm, G, 3, (0, 0, VE + 215), M['naranja'], bevel=0.4,
         desc="Tapon del puerto superior (en el catalogo es amarillo; aca naranja)", real=True)

    # ------------------------------------------------ SOPORTES
    G = "soportes"
    ZL = -R - 20                 # cara inferior de las patas soldadas (aprox)
    for i, (sx_, sy_) in enumerate(((-400, -130), (-400, 130), (400, -130), (400, 130))):
        bm = bmesh.new()
        Ms = AX('Z', (sx_, sy_, ZL - 32))
        add_lathe(bm, [(0, 0), (0, 30), (4, 33), (28, 33), (32, 30), (32, 0)], Ms, closed=False, segs=40)
        part(f"Soporte_Silentblock_{i + 1}", bm, G, 8, (0, 0, -95), M['caucho'], desc="Taco de goma antivibratorio", real=True)
        bm = bmesh.new()
        add_hexbolt(bm, 12, 40, AX('-Z', (sx_, sy_, ZL - 32 - 6)))
        part(f"Soporte_Bulon_Taco_{i + 1}", bm, G, 10, (0, 0, -330), M['cincado'], bevel=0.3, desc="Bulon del taco")
    ZC = ZL - 32                 # cara superior de los travesaños
    for i, sx_ in enumerate((-400, 400)):
        bm = bmesh.new()
        u = [(-40, 0), (40, 0), (40, -60), (34, -60), (34, -6), (-34, -6), (-34, -60), (-40, -60)]
        add_prism(bm, u, 620, Matrix.Translation((sx_, 0, ZC)) @ Matrix.Rotation(pi / 2, 4, 'X'))
        cb = bmesh.new()
        for k in range(-6, 7):
            if abs(k * 42) in (126,):
                continue
            add_cyl(cb, 7, 30, AX('Z', (sx_, k * 42, ZC - 3)), segs=16)
        bm = boolean_cut(bm, cb)
        part(f"Soporte_Travesano_{i + 1}", bm, G, 9, (0, 0, -190), M['negro_tex'], bevel=0.8,
             desc="Travesaño perforado de apoyo", real=True)
        for j, sy_ in enumerate((-314, 314)):
            bm = bmesh.new()
            pl = [(-70, 0), (70, 0), (70, -70), (40, -265), (-40, -265), (-70, -70)]
            add_prism(bm, pl, 8, Matrix.Translation((sx_, sy_, ZC)) @ Matrix.Rotation(pi / 2, 4, 'X'))
            sg = 1 if sy_ > 0 else -1
            add_box(bm, 80, 50, 8, T(sx_, sy_ - sg * 25, ZC - 265 + 4))
            part(f"Soporte_Placa_Chasis_{i * 2 + j + 1}", bm, G, 9, (0, sg * 120, -190), M['negro_tex'], bevel=0.8,
                 desc="Placa de fijacion al chasis", real=True)
            bm = bmesh.new()
            for xx in (-45, 45):
                add_hexbolt(bm, 10, 26, AX((0, sg, 0), (sx_ + xx, sy_ + sg * 4, ZC - 30)))
            part(f"Soporte_Bulones_Placa_{i * 2 + j + 1}", bm, G, 10, (0, sg * 230, -190), M['cincado'], bevel=0.3,
                 desc="Bulones de la placa")

    # soporte de bomba (concepto)
    PX, PZ = 0.0, ZC - 164.0     # centro de la bomba
    bm = bmesh.new()
    add_box(bm, 800 - 80, 60, 8, T(0, 0, ZC - 60 - 4))
    add_prism(bm, rrect(190, 150, 16), 8, AX('X', (PX - 79, 0, PZ + 12)))
    cb = bmesh.new()
    add_cyl(cb, 41, 40, AX('X', (PX - 79, 0, PZ + 27)), segs=40)
    bm = boolean_cut(bm, cb)
    part("Soporte_Bomba", bm, G, 9, (0, 0, -190), M['negro_tex'], bevel=0.8,
         desc="Soporte de la bomba bajo el deposito (disposicion de concepto: en el camion la bomba va en la toma de fuerza)")

    # ------------------------------------------------ BOMBA (internos genericos)
    G = "bomba"
    PE = Vector((0, -520, -250))
    CD = 27.0                     # semidistancia entre ejes
    prof_body = rrect(124, 176, 30)   # en el plano local XY -> mundo (Y, Z) al llevar Z a X

    def MX(x):                    # eje local Z -> X del mundo; local X->Y? usamos rotacion fija
        return Matrix.Translation((PX + x, 0, PZ)) @ Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))

    def ex(dx):
        return (PE.x + dx, PE.y, PE.z)

    # cuerpo
    bm = bmesh.new()
    add_prism(bm, prof_body, 100, MX(0))
    add_cyl(bm, 30, 10, AX('-Y', (PX, -62, PZ)), z0=0, segs=32)
    cb = bmesh.new()
    add_prism(cb, fig8_pts(33, CD), 120, MX(0))
    add_cyl(cb, 19, 40, AX('-Y', (PX, -40, PZ)), z0=0, segs=32)
    for yy in (-44, 44):
        for zz in (-70, 70):
            add_cyl(cb, 6.5, 130, AX('X', (PX, yy, PZ + zz)), segs=16)
    bm = boolean_cut(bm, cb)
    part("Bomba_Cuerpo", bm, G, 11, ex(0), M['fundicion'], bevel=1.2,
         desc="Cuerpo de la bomba de engranajes (catalogo: 82 cm3/rev; geometria generica)", real=True)
    # engranajes
    for nm, zc, shaft in (("Motriz", CD, True), ("Conducido", -CD, False)):
        bm = bmesh.new()
        Mg = MX(0) @ Matrix.Translation((0, zc, 0))
        add_prism(bm, gear_pts(12, 22.5, 32.2, a0=(0 if shaft else pi / 12)), 50, Mg)
        if shaft:
            add_cyl(bm, 11, 185, Mg, z0=-135, segs=32)
            add_prism(bm, gear_pts(8, 15.5, 18.0), 62, Mg, z0=-136)
        else:
            add_cyl(bm, 11, 96, Mg, segs=32)
        part(f"Bomba_Engranaje_{nm}", bm, G, 11, ex(-125), M['pulido'], bevel=0.0, sharp=30,
             desc=("Engranaje motriz con eje estriado" if shaft else "Engranaje conducido") + " - interno generico")
    # bujes
    for nm, x0, dx in (("Delantero", -37.5, -215), ("Trasero", 37.5, 140)):
        bm = bmesh.new()
        add_prism(bm, fig8_pts(32.6, CD), 24, MX(x0))
        cb = bmesh.new()
        for zc in (CD, -CD):
            add_cyl(cb, 11.3, 40, MX(x0) @ Matrix.Translation((0, zc, 0)), segs=32)
        bm = boolean_cut(bm, cb)
        part(f"Bomba_Buje_{nm}", bm, G, 11, ex(dx), M['cepillado'], bevel=0.5,
             desc="Bloque de bujes - interno generico")
    # brida delantera
    bm = bmesh.new()
    add_prism(bm, prof_body, 18, MX(-59))
    add_prism(bm, rrect(150, 150, 14), 10, MX(-63) @ Matrix.Translation((0, CD, 0)))
    add_cyl(bm, 40, 8, MX(-72) @ Matrix.Translation((0, CD, 0)), segs=48)
    cb = bmesh.new()
    add_cyl(cb, 14, 60, MX(-60) @ Matrix.Translation((0, CD, 0)), segs=32)
    for yy in (-60, 60):
        for zz in (-60, 60):
            add_cyl(cb, 6, 30, MX(-63) @ Matrix.Translation((yy, CD + zz, 0)), segs=16)
    bm = boolean_cut(bm, cb)
    part("Bomba_Brida", bm, G, 11, ex(-310), M['fundicion'], bevel=1.0, desc="Brida de montaje delantera (4 agujeros)", real=True)
    bm = bmesh.new()
    add_tube(bm, 20, 11.5, 7, MX(-80) @ Matrix.Translation((0, CD, 0)), segs=40)
    part("Bomba_Reten", bm, G, 11, ex(-390), M['caucho'], bevel=0.5, desc="Reten del eje - interno generico")
    # tapa trasera
    bm = bmesh.new()
    add_prism(bm, prof_body, 26, MX(63))
    add_cyl(bm, 28, 12, MX(76), z0=0, segs=32)
    cb = bmesh.new()
    add_cyl(cb, 15, 60, MX(76), z0=-10, segs=32)
    bm = boolean_cut(bm, cb)
    part("Bomba_Tapa_Trasera", bm, G, 11, ex(255), M['fundicion'], bevel=1.0, desc="Tapa trasera con salida de presion", real=True)
    bm = bmesh.new()
    for yy in (-44, 44):
        for zz in (-70, 70):
            add_hexbolt(bm, 11, 140, AX('X', (PX + 76, yy, PZ + zz)))
    part("Bomba_Bulones", bm, G, 11, ex(400), M['cincado'], bevel=0.3, desc="Bulones pasantes del cuerpo")

    # ------------------------------------------------ MANGUERAS Y CONEXIONES
    G = "mangueras"

    def fitting(bm, p, d, r):
        Mq = AX(d, p)
        add_cyl(bm, r * 1.25, r * 2.2, Mq, z0=-r * 2.2, segs=32)          # casquillo prensado
        add_prism(bm, circle(r * 1.55, 6), r * 0.9, Mq, z0=0)             # tuerca
        add_cyl(bm, r * 0.95, r * 0.7, Mq, z0=r * 0.9, segs=24)

    # succion: del deposito (abajo) a la entrada de la bomba (-Y)
    p_tank = Vector((-190, -70, -sqrt(R * R - 70 * 70) - 30))
    p_pump = Vector((PX, -84, PZ))
    pts = [p_tank + Vector((0, 0, -22)), p_tank + Vector((-6, -30, -70)), Vector((-150, -200, PZ - 30)),
           Vector((-60, -215, PZ - 12)), p_pump + Vector((0, -70, 0)), p_pump + Vector((0, -22, 0))]
    path = catmull(pts, 16)
    bm = bmesh.new()
    fr = add_sweep(bm, path, 21, segs=24)
    part("Manguera_Succion", bm, G, 2, (-780, -200, -120), M['caucho'], desc="Manguera de succion", real=True)
    bm = bmesh.new()
    add_sweep(bm, helix_on_path(fr[6:-6], 23.5, 1 / 16.0), 3.2, segs=8)
    part("Manguera_Succion_Espiral", bm, G, 2, (-780, -200, -120), M['poliamida'], desc="Espiral protector", real=True)
    bm = bmesh.new()
    fitting(bm, p_tank + Vector((0, 0, -22)), (0, 0, 1), 16)
    fitting(bm, p_pump + Vector((0, -22, 0)), (0, 1, 0), 16)
    part("Manguera_Succion_Conexiones", bm, G, 2, (-780, -200, -120), M['cincado'], bevel=0.4, desc="Conexiones de la manguera de succion", real=True)

    # presion: de la tapa trasera de la bomba al puerto frontal de la valvula
    q0 = Vector((PX + 88, 0, PZ)); q1 = Vector((VX + 34, -58, VZ - 4))
    pts = [q0 + Vector((22, 0, 0)), q0 + Vector((100, -20, 0)), Vector((235, -170, PZ + 10)),
           Vector((285, -330, -320)), Vector((330, -395, -120)), Vector((340, -365, 80)), Vector((315, -280, 250)),
           q1 + Vector((10, -110, -10)), q1 + Vector((0, -24, 0))]
    path = catmull(pts, 16)
    bm = bmesh.new()
    fr = add_sweep(bm, path, 14, segs=20)
    part("Manguera_Presion", bm, G, 1, (260, -330, 60), M['caucho'], desc="Manguera de presion", real=True)
    bm = bmesh.new()
    fitting(bm, q0 + Vector((22, 0, 0)), (-1, 0, 0), 11.5)
    fitting(bm, q1 + Vector((0, -24, 0)), (0, 1, 0), 11.5)
    part("Manguera_Presion_Conexiones", bm, G, 1, (260, -330, 60), M['cincado'], bevel=0.4, desc="Conexiones de la manguera de presion", real=True)

    # ------------------------------------------------ MANDO NEUMATICO (accesorios)
    G = "neumatica"
    XR = hx + HEAD_FLANGE
    bm = bmesh.new()
    coil = []
    turns = 7
    for t in range(turns * 48 + 1):
        a = 2 * pi * t / 48
        k = t / (turns * 48)
        rr = (205 - 34 * k) * R / 250
        coil.append(Vector((hx + 75 + 16 * k + 2.0 * sin(a * 3.1), rr * cos(a), rr * sin(a))))
    add_sweep(bm, coil, 3.2, segs=8)
    part("Neumatica_Rollo_Tubo", bm, G, 1, (360, 0, 0), M['poliamida'], desc="Rollo de tubo neumatico", real=True)
    # mando de cabina: comando neumatico de 3 posiciones con LED (forma tomada del catalogo, ACV311100)
    OX = XR + HEAD_DEPTH + 90
    JX = 480                                             # todo el comando se aleja del deposito en la explosion
    Mj = AX('-Y', (OX, 0, 0))                            # local Z -> frente (-Y); local Y -> arriba; local X -> X
    # cuerpo de valvula de aluminio, detras de la placa
    bm = bmesh.new()
    add_prism(bm, rrect(72, 66, 9), 50, Mj, z0=-53)
    add_prism(bm, rrect(50, 46, 8), 8, Mj, z0=-61)
    part("Neumatica_Mando_Valvula", bm, G, 1, (JX, 190, 0), M['aluminio'], bevel=1.2,
         desc="Cuerpo de valvula de aire del comando (aluminio)", real=True)
    bm = bmesh.new()
    for xx in (-24, 0, 24):
        Mf = AX('Y', (OX + xx, 61, -6))
        add_prism(bm, circle(8, 6), 6, Mf, z0=0)
        add_cyl(bm, 6, 14, Mf, z0=6, segs=16)
    part("Neumatica_Mando_Racores", bm, G, 1, (JX, 300, 0), M['cincado'], bevel=0.3, desc="Racores de aire del comando", real=True)
    # placa de fijacion
    bm = bmesh.new()
    add_prism(bm, rrect(104, 104, 10), 6, Mj, z0=-3)
    cb = bmesh.new()
    for xx in (-41, 41):
        for yy in (-41, 41):
            add_cyl(cb, 3.6, 30, Mj @ Matrix.Translation((xx, yy, 0)), segs=16)
    bm = boolean_cut(bm, cb)
    part("Neumatica_Mando_Base", bm, G, 1, (JX, 80, 0), M['negro_tex'], bevel=0.8,
         desc="Placa de fijacion del comando neumatico (forma del catalogo; medidas estimadas)", real=True)
    # carcasa con la ranura de las 3 posiciones
    bm = bmesh.new()
    add_prism(bm, rrect(82, 82, 18), 28, Mj, z0=3)
    add_prism(bm, rrect(68, 72, 16), 12, Mj, z0=31)
    cb = bmesh.new()
    add_prism(cb, rrect(20, 56, 9.5), 40, Mj, z0=14)
    bm = boolean_cut(bm, cb)
    part("Neumatica_Mando_Cuerpo", bm, G, 1, (JX, -30, 0), M['negro_tex'], bevel=1.0,
         desc="Carcasa del comando neumatico de 3 posiciones", real=True)
    # palanca
    bm = bmesh.new()
    add_cyl(bm, 7, 66, Mj, z0=8, segs=24)
    add_cyl(bm, 9, 26, AX('X', (OX, -14, 0)), segs=20)
    part("Neumatica_Mando_Palanca", bm, G, 1, (JX, -150, 0), M['cepillado'], bevel=0.3, desc="Palanca del comando", real=True)
    # perilla
    bm = bmesh.new()
    add_lathe(bm, [(58, 0), (58, 14), (62, 19), (70, 21.5), (98, 21.5), (101, 26), (121, 26), (125, 23.5), (127, 19), (127, 0)],
              Mj, closed=False, segs=48)
    part("Neumatica_Mando_Perilla", bm, G, 1, (JX, -260, 0), M['caucho'], bevel=0.0, desc="Perilla del comando", real=True)
    bm = bmesh.new()
    add_cyl(bm, 18, 2.5, Mj, z0=126, segs=40)
    part("Neumatica_Mando_Etiqueta", bm, G, 1, (JX, -340, 0), M['naranja'], desc="Disco de color de la perilla (en el catalogo es amarillo; aca naranja)", real=True)
    # traba de seguridad
    bm = bmesh.new()
    add_prism(bm, rrect(18, 34, 4), 11, Mj @ Matrix.Translation((0, 47, 0)), z0=14)
    add_prism(bm, rrect(18, 12, 3), 16, Mj @ Matrix.Translation((0, 58, 0)), z0=22)
    part("Neumatica_Mando_Traba", bm, G, 1, (JX, -30, 110), M['naranja'], bevel=0.6,
         desc="Traba de seguridad del comando (en el catalogo es amarilla; aca naranja)", real=True)
    # LED
    bm = bmesh.new()
    add_cyl(bm, 4.5, 4, Mj @ Matrix.Translation((24, -26, 0)), z0=41, segs=20)
    part("Neumatica_Mando_LED", bm, G, 1, (JX, -110, -60), M['graf_naranja'], desc="Luz LED indicadora", real=True)

    return sc, rig, M


# ================================================================ explosion / animacion
def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (6 * t - 15) + 10)


def set_explode(E, stagger=0.45):
    """E en [0,1]. Las piezas salen escalonadas segun su 'orden'."""
    omax = max(o["orden"] for o in PARTS) or 1
    for o in PARTS:
        d = stagger * (o["orden"] / omax)
        f = ease((E - d) / (1 - stagger)) if E < 1 else 1.0
        b = Vector(o["base"]); v = Vector(o["explode"])
        o.location = b + v * f


def export_parts_csv(path):
    import csv
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["nombre", "grupo", "orden", "explode_x_mm", "explode_y_mm", "explode_z_mm",
                    "ancho_x_mm", "prof_y_mm", "alto_z_mm", "material", "fuente", "descripcion"])
        for o in sorted(PARTS, key=lambda o: (o["orden"], o.name)):
            d = o.dimensions
            e = o["explode"]
            w.writerow([o.name, o["grupo"], o["orden"], round(e[0]), round(e[1]), round(e[2]),
                        round(d.x, 1), round(d.y, 1), round(d.z, 1), o.data.materials[0].name, o["fuente"], o["descripcion"]])
