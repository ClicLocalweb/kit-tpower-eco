import sys, time, bpy
sys.path.insert(0, '/home/claude/kit')
import kit_build as K, render_lib as RL
t=time.time()
sc, rig, M = K.build()
print("piezas:", len(K.PARTS), "build s:", round(time.time()-t,1))
RL.studio(sc)
out = sys.argv[1]; samples=int(sys.argv[2]); scale=float(sys.argv[3])
RL.cycles(sc, int(1920*scale), int(1080*scale), samples)
shots = sys.argv[4:]
cam = RL.camera(sc, (-1500,-2300,750), (0,0,-80), lens=62)
for s in shots:
    t=time.time()
    if s=='hero':
        K.set_explode(0); cam.location=(-1900,-3000,850); RL.look_at(cam,(40,0,-60)); cam.data.lens=62; cam.data.dof.use_dof=False
    elif s=='exp':
        K.set_explode(1); cam.location=(-3050,-6100,1900); RL.look_at(cam,(60,0,-20)); cam.data.lens=62; cam.data.dof.use_dof=False
    elif s=='int':
        K.set_explode(1); cam.location=(-620,-1750,-330); RL.look_at(cam,(-10,-520,-716)); cam.data.lens=58; cam.data.dof.use_dof=True; cam.data.dof.focus_distance=1400; cam.data.dof.aperture_fstop=0.02
    elif s=='val':
        K.set_explode(1); cam.location=(-700,-1500,1350); RL.look_at(cam,(120,0,900)); cam.data.lens=60
    if s.startswith('clay_'):
        RL.clay_override(sc, True); s2=s[5:]
        if s2=='hero': K.set_explode(0); cam.location=(-1750,-2750,820); RL.look_at(cam,(40,0,-60)); cam.data.dof.use_dof=False
        else: K.set_explode(1); cam.location=(-2600,-5200,1700); RL.look_at(cam,(60,0,20)); cam.data.dof.use_dof=False
    else:
        RL.clay_override(sc, False)
    if s=='save':
        K.set_explode(0); K.export_parts_csv(out+'/piezas.csv'); bpy.ops.wm.save_as_mainfile(filepath=out+'/kit_hidraulico.blend'); continue
    RL.render(sc, f"{out}/{s}.png"); print(s, "render s:", round(time.time()-t,1))
