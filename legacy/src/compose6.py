import sys, glob, numpy as np, trimesh
sys.path.insert(0, '/home/claude/stand')
from model6 import YBK, YRT, YC, BZ, PX, PLATE_T
A = '/mnt/user-data/attachments/32727b44-56bd-544a-a338-1ba88c39662d/'
K2 = trimesh.load(glob.glob(A + '0e66*')[0]); K1 = trimesh.load(glob.glob(A + '8b19*')[0]); U = trimesh.load(glob.glob(A + '8f70*')[0])
M = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1.0]])
def place(mesh, f):
    m = mesh.copy(); v = m.vertices.copy(); m.vertices = np.array([f(*p) for p in v]); m.fix_normals(); return m
def col(m, rgb):
    m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=[int(255*v) for v in rgb] + [255], metallicFactor=0.1, roughnessFactor=0.5)); return m
def add(scene, m, name):
    scene.add_geometry(m, node_name=name, geom_name=name, transform=M)
def compose(src, dst, c):
    s = trimesh.load(src)
    cz0 = BZ - 24.26 / 2
    add(s, col(place(K2, lambda x, y, z: (c - 30 + z, YBK + y, cz0 + x)), (0.13, 0.33, 0.85)), 'KARETKA_2_polzovatelya')
    add(s, col(place(K1, lambda x, y, z: (c - 30 + z, YRT - 23 + y, cz0 + x)), (0.13, 0.33, 0.85)), 'KARETKA_1_polzovatelya')
    for xs, sg in ((PX['L'] + 215, -1), (PX['R'] + 85, 1)):  # раструб (лок. y=0) к каретке
        add(s, col(place(U, lambda x, y, z, xs=xs, sg=sg: (xs - sg * 10 + sg * y, YC - 28.05 + x, PLATE_T + z)), (0.92, 0.45, 0.1)), f'UPOR_polzovatelya_{int(xs)}')
    s.export(dst); print('ok', dst)
if __name__ == '__main__':
    compose(sys.argv[1], sys.argv[2], float(sys.argv[3]))
