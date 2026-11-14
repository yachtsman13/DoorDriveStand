import sys, trimesh, numpy as np, glob, os, zlib, re
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
A=sys.argv[1]; out=sys.argv[2]
fs=sorted(glob.glob(A+'/*.STL'))
fig=plt.figure(figsize=(18,12))
k=1
for f in fs:
    m=trimesh.load(f)
    for el,az in [(25,-60),(25,120),(90,-90)]:
        ax=fig.add_subplot(3,3,k,projection='3d'); k+=1
        tri=m.vertices[m.faces]
        n=m.face_normals; L=np.array([0.4,-0.5,0.76]); sh=0.55+0.45*np.clip(n@L,-1,1)
        pc=Poly3DCollection(tri,facecolors=np.c_[sh*0.9,sh*0.55,sh*0.2],edgecolor=(0,0,0,0.15),linewidths=0.2)
        ax.add_collection3d(pc)
        b=m.bounds; c=(b[0]+b[1])/2; r=(b[1]-b[0]).max()/2
        ax.set_xlim(c[0]-r,c[0]+r);ax.set_ylim(c[1]-r,c[1]+r);ax.set_zlim(c[2]-r,c[2]+r)
        ax.view_init(el,az); ax.set_title(os.path.basename(f)[:8]+' '+str(np.round(b[1]-b[0],1)))
        ax.set_xlabel('x');ax.set_ylabel('y')
plt.tight_layout(); plt.savefig(out+'/stl.png',dpi=70)
# try previews inside SLDPRT
for f in sorted(glob.glob(A+'/*.SLDPRT')):
    d=open(f,'rb').read(); n=0
    for m_ in re.finditer(rb'\x78[\x01\x5e\x9c\xda]',d):
        try:
            o=zlib.decompressobj().decompress(d[m_.start():m_.start()+400000])
        except Exception: continue
        if o[:4]==b'\x89PNG' or o[:2]==b'BM' or b'PNG' in o[:16]:
            open(f'{out}/prev_{os.path.basename(f)[:8]}_{n}.bin','wb').write(o); n+=1
    # raw deflate chunks with names
    names=set()
    for m_ in re.finditer(rb'\x14\x00\x06\x00\x08\x00',d):
        pass
    print(os.path.basename(f)[:8],'previews',n, d[:8])
