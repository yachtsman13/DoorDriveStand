"""Печатный шкив HTD 5M 28T под ремень 15 мм + рендер."""
import math, sys
from pathlib import Path
import cadquery as cq
from model import Stand

HP, NZ = 5.0, 28
PD = HP * NZ / math.pi; OD = PD - 1.143
H_TOOTH, H_BELT = 2.06, 3.8
R_LAND = OD / 2; R_BACK = R_LAND + H_BELT - H_TOOTH
HUB_H, FL_T, TW, R_FL, R_HUB = 9.0, 1.5, 16.5, 26.0, 16.0
RG = 1.6                                   # радиус впадины
RC = R_LAND - H_TOOTH + RG                 # центр дуги впадины

def groove2d(a, r=RG, ext=3.0):
    c = cq.Vector(RC * math.cos(a), RC * math.sin(a))
    w = cq.Workplane('XY').center(c.x, c.y).circle(r)
    rect = (cq.Workplane('XY').center((RC + ext / 2) * math.cos(a), (RC + ext / 2) * math.sin(a))
            .rect(ext, 2 * r).val().rotate(cq.Vector((RC + ext / 2) * math.cos(a), (RC + ext / 2) * math.sin(a), 0),
                                           cq.Vector((RC + ext / 2) * math.cos(a), (RC + ext / 2) * math.sin(a), 1), math.degrees(a)))
    return w, rect

def pulley(bore=12.0):
    hub = cq.Workplane('XY').circle(R_HUB).extrude(HUB_H)
    f1 = cq.Workplane('XY').circle(R_FL).extrude(FL_T).translate((0, 0, HUB_H))
    z0 = HUB_H + FL_T
    rim = cq.Workplane('XY').circle(R_LAND).extrude(TW).translate((0, 0, z0))
    for i in range(NZ):
        a = 2 * math.pi * i / NZ
        g = cq.Workplane('XY').center(RC * math.cos(a), RC * math.sin(a)).circle(RG).extrude(TW)
        g = g.union(cq.Workplane('XY').box(3.0, 2 * RG, TW, centered=(False, True, False))
                    .translate((RC, 0, 0)).rotate((0, 0, 0), (0, 0, 1), math.degrees(a)))
        rim = rim.cut(g.translate((0, 0, z0)))
    rim = rim.faces('>Z').edges().chamfer(0.3) if False else rim
    p = hub.union(f1).union(rim)
    # крепление наружной реборды: 3 отв. под саморез/М3 в торце венца
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.5
        p = p.cut(cq.Workplane('XY').center(14 * math.cos(a), 14 * math.sin(a)).circle(1.25).extrude(10).translate((0, 0, z0 + TW - 10)))
    p = p.cut(cq.Workplane('XY').circle(bore / 2).extrude(60).translate((0, 0, -1)))
    # клеммная ступица: прорезь + стяжной М4 (головка в цековке с одной стороны, гайка в шестигранном кармане с другой)
    p = p.cut(cq.Workplane('XY').box(1.6, 20, HUB_H + 0.01, centered=(True, False, False)).translate((0, 0, -0.005)))
    yc, zc = bore / 2 + 4.6, HUB_H / 2
    p = p.cut(cq.Workplane('YZ').center(yc, zc).circle(2.2).extrude(40, both=True))
    p = p.cut(cq.Workplane('YZ').center(yc, zc).circle(3.7).extrude(20).translate((5.0, 0, 0)))
    p = p.cut(cq.Workplane('YZ').center(yc, zc).polygon(6, 8.1).extrude(-20).translate((-5.0, 0, 0)))
    return p

def flange():
    f = cq.Workplane('XY').circle(R_FL).circle(8.5).extrude(FL_T + 0.5)
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.5
        f = f.cut(cq.Workplane('XY').center(14 * math.cos(a), 14 * math.sin(a)).circle(1.7).extrude(5))
        f = f.cut(cq.Workplane('XY').add(cq.Solid.makeCone(1.7, 3.2, 1.5, cq.Vector(14 * math.cos(a), 14 * math.sin(a), FL_T + 0.5), cq.Vector(0, 0, -1))))
    return f

def belt_wrap(a0=math.radians(20), a1=math.radians(200), tail=40):
    """Ремень с охватом 180° + хвосты по касательной (вид зацепления)."""
    z0 = HUB_H + FL_T + (TW - 15) / 2
    ring = cq.Workplane('XY').circle(R_BACK).circle(R_LAND).extrude(15)
    wedge = cq.Workplane('XY').polyline([(0, 0)] + [(60 * math.cos(a0 + (a1 - a0) * k / 20), 60 * math.sin(a0 + (a1 - a0) * k / 20)) for k in range(21)]).close().extrude(15)
    b = ring.intersect(wedge)
    for i in range(NZ):
        a = 2 * math.pi * i / NZ
        if a0 + 0.05 < a < a1 - 0.05:
            t = cq.Workplane('XY').center(RC * math.cos(a), RC * math.sin(a)).circle(RG - 0.15).extrude(15)
            t = t.union(cq.Workplane('XY').box(3.0, 2 * (RG - 0.15), 15, centered=(False, True, False)).translate((RC, 0, 0)).rotate((0, 0, 0), (0, 0, 1), math.degrees(a)))
            b = b.union(t.intersect(cq.Workplane('XY').circle(R_LAND + 0.01).circle(RC - RG + 0.15).extrude(15)))
    # хвосты
    for a, sg in ((a0, 1), (a1, -1)):
        tx, ty = -math.sin(a) * sg, math.cos(a) * sg        # направление «от шкива»
        nx, ny = math.cos(a), math.sin(a)
        L = tail
        pts = [(R_LAND * nx, R_LAND * ny), (R_BACK * nx, R_BACK * ny),
               (R_BACK * nx - tx * L, R_BACK * ny - ty * L), (R_LAND * nx - tx * L, R_LAND * ny - ty * L)]
        b = b.union(cq.Workplane('XY').polyline(pts).close().extrude(15))
        k = 2.5
        while k < L - 2:
            cx, cy = R_LAND * nx - tx * k, R_LAND * ny - ty * k
            q = [(cx + tx * 1.6, cy + ty * 1.6), (cx + tx * 1.0 - nx * H_TOOTH, cy + ty * 1.0 - ny * H_TOOTH),
                 (cx - tx * 1.0 - nx * H_TOOTH, cy - ty * 1.0 - ny * H_TOOTH), (cx - tx * 1.6, cy - ty * 1.6)]
            b = b.union(cq.Workplane('XY').polyline(q).close().extrude(15))
            k += HP
    return b.translate((0, 0, z0))

def screw(d, L, head_d, head_h, csk=False):
    s = cq.Workplane('XY').circle(d / 2).extrude(-L)
    h = cq.Workplane('XY').add(cq.Solid.makeCone(head_d / 2, d / 2, head_h)) if csk else cq.Workplane('XY').circle(head_d / 2).extrude(head_h)
    if csk: h = h.translate((0, 0, -head_h))
    return s.union(h)

if __name__ == '__main__':
    mode = sys.argv[1]
    S = Stand()
    p = pulley()
    S.add('SHKIV_HTD5M_28T', p, None, 'print', 'SHKIV')
    ex = 22 if mode == 'x' else 0
    zt = HUB_H + FL_T + TW
    S.add('REBORDA', flange().translate((0, 0, zt + ex)), None, 'print', 'SHKIV')
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.5
        S.add('VINT_M3x8_potay', screw(3, 8, 6, 1.7, True).translate((14 * math.cos(a), 14 * math.sin(a), zt + FL_T + 0.5 + 2 * ex)), None, 'steel', 'KREPEZH')
    yc, zc = 6 + 4.6, HUB_H / 2
    S.add('VINT_M4x16_DIN912', screw(4, 16, 7, 4).rotate((0, 0, 0), (0, 1, 0), -90).translate((5 + 4 + ex * 0.8, yc, zc)), None, 'steel', 'KREPEZH')
    S.add('GAYKA_M4', cq.Workplane('YZ').polygon(6, 7.9).circle(2).extrude(3.2).translate((-5 - 3.2 - ex * 0.8, yc, zc)), None, 'zinc', 'KREPEZH')
    S.add('VAL_D12', cq.Workplane('XY').circle(5.95).extrude(32).translate((0, 0, -6)), None, 'steel', 'VAL')
    if mode == 'a':
        S.add('REMEN_HTD5M_15', belt_wrap(), None, 'belt', 'REMEN')
    out_dir = Path(__file__).resolve().parent.parent / 'out'
    out_dir.mkdir(exist_ok=True)
    S.finish().save(str(out_dir / f'm7_pulley_{mode}.glb'))
    print('ok', mode, round(PD, 2), round(OD, 2))
