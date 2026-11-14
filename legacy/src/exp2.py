import sys, itertools, cadquery as cq
sys.path.insert(0,'/home/claude/stand')
from model2 import build2
var=sys.argv[1]; cx=float(sys.argv[2]) if len(sys.argv)>2 else 520
S=build2(var, cx); asm=S.finish()
print(var,'instances',len(S.items))
if '--check' in sys.argv:
    its=S.items; bbs=[i[2].BoundingBox() for i in its]; bad=[]
    def ov(a,b): return a.xmin<b.xmax-.05 and b.xmin<a.xmax-.05 and a.ymin<b.ymax-.05 and b.ymin<a.ymax-.05 and a.zmin<b.zmax-.05 and b.zmin<a.zmax-.05
    for i,j in itertools.combinations(range(len(its)),2):
        if not ov(bbs[i],bbs[j]): continue
        try: v=its[i][2].intersect(its[j][2]).Volume()
        except Exception: v=-1
        if abs(v)>2: bad.append((round(v,1),its[i][1],its[j][1]))
    for b in sorted(bad,reverse=True): print('CLASH',b)
    print('clashes',len(bad))
if '--glb' in sys.argv:
    asm.save(f'out/stend_{var}.glb'); asm.save(f'out/step/VARIANT_{var}.step'); print('saved')
