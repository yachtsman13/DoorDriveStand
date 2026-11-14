import sys, trimesh, numpy as np, re, glob, os
A=sys.argv[1]
for f in sorted(glob.glob(A+'/*.STL')):
    m=trimesh.load(f)
    b=m.bounds
    print(os.path.basename(f)[:12], 'size',np.round(b[1]-b[0],2),'min',np.round(b[0],2),'vol',round(m.volume/1000,2),'cm3 watertight',m.is_watertight,'faces',len(m.faces))
for f in sorted(glob.glob(A+'/*.SLDPRT')):
    d=open(f,'rb').read()
    # utf-16 strings
    s=set(re.findall(rb'(?:[\x20-\x7e\x10-\x4f]\x00|[\x00-\xff]\x04){4,}',d))
    txt=[]
    for x in s:
        try:
            t=x.decode('utf-16le')
            if re.search('[А-Яа-я]{3,}',t): txt.append(t)
        except: pass
    print(os.path.basename(f)[:10], len(d), sorted(set(txt))[:25])
    print('  PNG' , d.count(b'\x89PNG'), 'BMP?', d.count(b'BM6'))
