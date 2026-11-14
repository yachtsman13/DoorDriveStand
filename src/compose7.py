import sys
from pathlib import Path
import numpy as np
import trimesh
from model7 import YBK, YRT, YC, BZ, PX, PLATE_T

A = Path(__file__).resolve().parent.parent / 'assets' / 'source' / 'STL'


def load_part(prefix):
    matches = sorted(A.glob(prefix + '*'))
    if len(matches) != 1:
        raise RuntimeError(
            f'Ожидался один STL {prefix}*, найдено: {len(matches)}'
        )
    return trimesh.load(matches[0])


K2 = load_part('0e66')
K1 = load_part('8b19')
U = load_part('8f70')
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
    for xs, sg in ((PX['L'] + 215, -1), (PX['R'] + 85, 1)):  # раструб (лок. y=0) к каретке
        add(s, col(place(U, lambda x, y, z, xs=xs, sg=sg: (xs - sg * 10 + sg * y, YC - 28.05 + x, PLATE_T + z)), (0.92, 0.45, 0.1)), f'UPOR_polzovatelya_{int(xs)}')
    s.export(dst); print('ok', dst)
if __name__ == '__main__':
    compose(sys.argv[1], sys.argv[2], float(sys.argv[3]))
