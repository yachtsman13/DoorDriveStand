import sys, os, cadquery as cq
sys.path.insert(0, '/home/claude/stand')
from model import build
S = build()
PR = ['POLZUN_KARETKI', 'KRONSHTEYN_KARETKI', 'GUBKA_RIFLENAYA', 'UPOR_KONCEVOY', 'KORPUS_PREPYATSTVIYA', 'KHOMUT_ELEKTROMAGNITA', 'SHTYR_M8_L36', 'PLITA_DVIGATELYA_300x300x3']
os.makedirs('out/stl', exist_ok=True)
for k in PR:
    w = S.shapes[k]; bb = w.val().BoundingBox()
    loc = w.translate((-bb.xmin, -bb.ymin, -bb.zmin))
    cq.exporters.export(loc, f'out/step/{k}.step')
    if k not in ('PLITA_DVIGATELYA_300x300x3', 'SHTYR_M8_L36'):
        cq.exporters.export(loc, f'out/stl/{k}.stl', tolerance=0.02, angularTolerance=0.1)
    print(k, round(bb.xlen,1), round(bb.ylen,1), round(bb.zlen,1), round(w.val().Volume()/1000,1),'cm3')
