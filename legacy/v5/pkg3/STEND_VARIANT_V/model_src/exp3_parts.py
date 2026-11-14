import sys, os, cadquery as cq
sys.path.insert(0, '/home/claude/stand')
from model3 import build3
S = build3(520, False)
O = 'out/v3'
os.makedirs(O + '/step_detali', exist_ok=True); os.makedirs(O + '/stl_pechat', exist_ok=True); os.makedirs(O + '/dxf_laser', exist_ok=True)
first = {}
for k, n, shp, g, c in S.items:
    first.setdefault(k, shp)
PRINT = ['GUBKA_VERHNYAYA', 'GUBKA_NIZHNYAYA_RIFL', 'UPOR_KONCEVOY_V', 'NAPRAVLYAYUSHCHAYA_ZASLONKI', 'DERZHATEL_ELEKTROMAGNITA', 'OGRANICHITEL_RELSA', 'FIKSATOR_PLITY']
SKIP = {'DVIGATEL_USLOVNO', 'REMEN_PL5_USLOVNO', 'SHTOK_ELEKTROMAGNITA'}
for k, shp in first.items():
    if k in SKIP: continue
    bb = shp.BoundingBox()
    s0 = shp.translate(cq.Vector(-bb.xmin, -bb.ymin, -bb.zmin))
    cq.exporters.export(cq.Workplane().add(s0), f'{O}/step_detali/{k}.step')
    if k in PRINT:
        cq.exporters.export(cq.Workplane().add(s0), f'{O}/stl_pechat/{k}.stl', tolerance=0.02, angularTolerance=0.1)
# DXF лазерных деталей: контур в плоскости листа
def dxf(k, axis, fname):
    shp = first[k]; bb = shp.BoundingBox()
    w = cq.Workplane().add(shp.translate(cq.Vector(-bb.xmin, -bb.ymin, -bb.zmin)))
    if axis == 'Y':   # толщина по Y → повернуть так, чтобы толщина была по Z
        w = cq.Workplane().add(w.val().rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 90))
        b2 = w.val().BoundingBox(); w = cq.Workplane().add(w.val().translate(cq.Vector(0, -b2.ymin, -b2.zmin)))
    t = w.val().BoundingBox().zlen
    sec = w.section(t / 2)
    cq.exporters.export(sec, f'{O}/dxf_laser/{fname}.dxf')
    print(fname, round(w.val().BoundingBox().xlen, 1), round(w.val().BoundingBox().ylen, 1), 't', round(t, 1))
dxf('PLOSHCHADKA_KARETKI_AL5', 'Y', 'POZ5_PLOSHCHADKA_KARETKI_s5')
dxf('ZASLONKA_AL8', 'Z', 'POZ6_ZASLONKA_s8')
dxf('PLITA_DVIGATELYA_300x300x3', 'Z', 'POZ4_PLITA_300x300x3_s3')
print('ok')
