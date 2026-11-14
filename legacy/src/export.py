import os, sys, json, itertools, cadquery as cq
from model import build
out = sys.argv[1] if len(sys.argv) > 1 else 'out'
os.makedirs(out + '/step', exist_ok=True); os.makedirs(out + '/stl', exist_ok=True)
S = build(); asm = S.finish()
print('instances', len(S.items))
for k, v in sorted(S.count.items()): print(f'{v:4d}  {k}')
json.dump(S.count, open(out + '/counts.json', 'w'), ensure_ascii=False, indent=1)
# interference check (bbox prefilter)
if '--check' in sys.argv:
    its = S.items; bbs = [i[2].BoundingBox() for i in its]; bad = []
    def ov(a, b): return a.xmin < b.xmax - .05 and b.xmin < a.xmax - .05 and a.ymin < b.ymax - .05 and b.ymin < a.ymax - .05 and a.zmin < b.zmax - .05 and b.zmin < a.zmax - .05
    for i, j in itertools.combinations(range(len(its)), 2):
        if not ov(bbs[i], bbs[j]): continue
        try: v = its[i][2].intersect(its[j][2]).Volume()
        except Exception as e: v = -1
        if abs(v) > 2.0: bad.append((round(v, 1), its[i][1], its[j][1]))
    for b in sorted(bad, reverse=True): print('CLASH', b)
    print('clashes', len(bad))
if '--noexport' not in sys.argv:
    asm.save(out + '/step/STEND_SBORKA.step')
    asm.save(out + '/stend.glb')
    for k, shp in S.shapes.items():
        cq.exporters.export(shp, f'{out}/step/{k}.step')
    print('exported')
