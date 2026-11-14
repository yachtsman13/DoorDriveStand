import cadquery as cq
from model6 import build5
from model import COL
S = build5(480, False)
win = cq.Workplane('XY').box(150, 60, 80, centered=False).translate((-45, 90, -40)).val()   # y 90..150 — разрез по оси шпильки
A = cq.Assembly(name='SEC')
k = 0
for key, nm, shp, g, col in S.items:
    bb = shp.BoundingBox()
    if bb.xmax < -45 or bb.xmin > 105 or bb.ymin > 150 or bb.ymax < 90 or bb.zmin > 40 or bb.zmax < -40: continue
    try:
        c = shp.intersect(win)
    except Exception as e:
        print('skip', nm, e); continue
    if c.isNull() or c.Volume() < 1e-3: continue
    k += 1; A.add(cq.Workplane().add(c), name=nm, color=cq.Color(*COL[col]))
print(k); A.save('/home/claude/frame/stand/sec.glb')
