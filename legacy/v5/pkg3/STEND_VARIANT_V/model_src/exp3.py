import sys, itertools, json, cadquery as cq
sys.path.insert(0,'/home/claude/stand')
from model3 import build3
cx=float(sys.argv[1]); ext='--ext' in sys.argv; tag=sys.argv[2]
S=build3(cx, ext); asm=S.finish()
print('instances',len(S.items))
IGN={('REMEN_PL5_USLOVNO','VINT_M4x30_DIN912'),('REMEN_PL5_USLOVNO','SHKIV_PL5_D100')}
if '--check' in sys.argv:
    its=S.items; bbs=[i[2].BoundingBox() for i in its]; bad=[]
    def ov(a,b): return a.xmin<b.xmax-.05 and b.xmin<a.xmax-.05 and a.ymin<b.ymax-.05 and b.ymin<a.ymax-.05 and a.zmin<b.zmax-.05 and b.zmin<a.zmax-.05
    for i,j in itertools.combinations(range(len(its)),2):
        if not ov(bbs[i],bbs[j]): continue
        if (its[i][0],its[j][0]) in IGN or (its[j][0],its[i][0]) in IGN: continue
        try: v=its[i][2].intersect(its[j][2]).Volume()
        except Exception: v=-1
        if abs(v)>2: bad.append((round(v,1),its[i][1],its[j][1]))
    for b in sorted(bad,reverse=True): print('CLASH',b)
    print('clashes',len(bad))
if '--save' in sys.argv:
    asm.save(f'out/v3_{tag}.glb')
    json.dump(S.count, open(f'out/v3_counts.json','w'), ensure_ascii=False, indent=1)
    if '--step' in sys.argv:
        import os; os.makedirs('out/v3/step',exist_ok=True)
        asm.save('out/v3/step/STEND_VARIANT_V_SBORKA.step')
    print('saved')
