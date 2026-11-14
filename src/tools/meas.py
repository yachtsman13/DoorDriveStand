import sys, trimesh, numpy as np, glob, os
A=sys.argv[1]
def loops(m, origin, normal):
    s=m.section(plane_origin=origin, plane_normal=normal)
    if s is None: return []
    p,_=s.to_planar() if hasattr(s,'to_planar') else s.to_2D()
    out=[]
    for e in p.entities:
        pts=p.vertices[e.points]
        mn,mx=pts.min(0),pts.max(0)
        out.append((np.round(mn,2),np.round(mx,2),len(pts)))
    return out, p
for f in sorted(glob.glob(A+'/*.STL')):
    m=trimesh.load(f); print('==',os.path.basename(f)[:8], np.round(m.bounds,2).tolist())
    b=m.bounds
    for ax,name in [(0,'x'),(1,'y'),(2,'z')]:
        for frac in (0.1,0.3,0.5,0.7,0.9):
            o=b[0]+(b[1]-b[0])*0.5; o=o.copy(); o[ax]=b[0][ax]+(b[1]-b[0])[ax]*frac
            n=np.zeros(3); n[ax]=1
            s=m.section(plane_origin=o, plane_normal=n)
            if s is None: continue
            d=s.discrete
            desc=[]
            for poly in d:
                q=np.delete(poly,ax,axis=1); mn,mx=q.min(0),q.max(0)
                desc.append('[%s..%s]'%(np.round(mn,1).tolist(),np.round(mx,1).tolist()))
            print(' %s=%.1f:'%(name,o[ax]),' '.join(desc))
