"""Эскиз (для рендера): без рельса, плиты заподлицо с торцами (угловое соединение без кубов),
шкивы почти вплотную к плите, препятствие — 2 штыря через среднюю стойку на общей пластине, толкает электромагнит."""
import math, itertools
import cadquery as cq
from model import (loc, profile, bracket, tnut, lever_screw, standoff, sleeve, washer, spring, foot, screw, nut,
                   motor_dummy, Stand, PR, PLATE, PLATE_T, HOLE_EDGE, LUG_EDGE, Y_AX)
from model2 import pulley2, BELT_W
from model3 import plate3, STOP_Y

L = 1500; XM = 750
PX = {'L': 0.0, 'R': 1190.0}                 # плиты: левая заподлицо с торцом, правая на 10 мм внутрь (ход натяжения)
BZ = PLATE_T + 2 + 15                         # ось ремня: шкив 30 мм в 2 мм от плиты → 20
RI, RO = 47.2, 51.0
YB0, YB1 = Y_AX + RI, Y_AX + RO               # 197,2 … 201 (условно тело ремня)
JX = 30.0
JZ0, JZ1 = BZ - 15, BZ + 15                   # губки по ширине ремня + 3 мм
YU0, YU1 = 201.0, 216.0                       # верхняя губка
YL0, YL1 = 177.0, 192.0                       # нижняя губка (+рёбра до 197)
PIN_Y = ((YL0 + YL1) / 2, (YU0 + YU1) / 2)    # 184,5 и 208,5
PIN_D, STROKE = 8.0, 10.0

def belt4(x1, x2):
    o = cq.Workplane('XY').slot2D(x2 - x1 + 2 * RO, 2 * RO).extrude(BELT_W)
    i = cq.Workplane('XY').slot2D(x2 - x1 + 2 * RI, 2 * RI).extrude(BELT_W)
    return o.cut(i).translate(((x1 + x2) / 2, Y_AX, BZ - BELT_W / 2))

def clamp4(c):
    up = cq.Workplane('XY').box(2 * JX, YU1 - YU0, JZ1 - JZ0, centered=(True, False, False)).translate((c, YU0, JZ0))
    lo = cq.Workplane('XY').box(2 * JX, YL1 - YL0, JZ1 - JZ0, centered=(True, False, False)).translate((c, YL0, JZ0))
    for i in range(6):
        z = BZ - BELT_W / 2 + i * 4.7
        lo = lo.union(cq.Workplane('YZ').polyline([(0, -2.0), (5.1, -0.6), (5.1, 0.6), (0, 2.0)]).close().extrude(2 * JX).translate((c - JX, YL1, z)))
    lo = lo.intersect(cq.Workplane('XY').box(2 * JX, 30, JZ1 - JZ0, centered=(True, False, False)).translate((c, YL0, JZ0)))
    for x in (-20, 20):
        for z in (BZ - 7.05, BZ + 7.05):
            h = cq.Workplane('XZ').center(c + x, z).circle(2.25).extrude(-60).translate((0, 160, 0))
            up = up.cut(h); lo = lo.cut(h)
    return up, lo

def ustop(xc, d):
    """Упор П-образный на плите (как ваш «Упор»): две стойки над и под ремнём, ремень проходит в зазоре."""
    s = cq.Workplane('XY').box(20, 49, 4, centered=(True, False, False)).translate((xc, 172, PLATE_T))
    for y0, y1 in ((172, 189.5), (203.5, 221)):
        s = s.union(cq.Workplane('XY').box(20, y1 - y0, JZ1 + 3 - PLATE_T, centered=(True, False, False)).translate((xc, y0, PLATE_T)))
    for y in STOP_Y:
        s = s.cut(cq.Workplane('XY').circle(3.3).extrude(60).translate((xc, y, 0)))
    pads = [cq.Workplane('XY').box(4, y1 - y0 - 2, JZ1 - JZ0, centered=(False, False, False)).translate((xc + 10 if d > 0 else xc - 14, y0 + 1, JZ0))
            for y0, y1 in ((172, 189.5), (203.5, 221))]
    return s, pads

def build4(c=520, ext=False):
    S = Stand()
    Pl, Pc, Br, Tn = profile(L), profile(240), bracket(), tnut()
    S6 = screw(6, 12)
    ys, zs = (15, 285), (-15, -285)
    for y in ys:
        for z in zs:
            S.add('PROFIL_30x30_L1500', Pl, loc((0, y, z), (0, 1, 0), (1, 0, 0)))
    post_mid = None
    for x in (15, XM, 1485):
        for z in zs:
            if x == XM and z == -15:
                p = Pc.val().located(loc((x, PR, z), (1, 0, 0), (0, 1, 0)))
                for y in PIN_Y:
                    p = p.cut(cq.Workplane('XY').circle(PIN_D / 2 + 0.2).extrude(40).translate((x, y, -35)).val())
                S.add('STOYKA_SREDNYAYA_S_OTV', cq.Workplane().add(p), None, 'alu2')
            else:
                S.add('PROFIL_30x30L_L240', Pc, loc((x, PR, z), (1, 0, 0), (0, 1, 0)), 'alu2')
        for y in ys:
            S.add('PROFIL_30x30L_L240', Pc, loc((x, y, -PR), (1, 0, 0), (0, 0, -1)), 'alu2')
    def br(origin, d1, d2):
        zz = cq.Vector(*d1).cross(cq.Vector(*d2))
        S.add('UGOLOK_30x30_A990', Br, loc(origin, d1, (zz.x, zz.y, zz.z)), 'zinc')
    for z in zs:
        for sx in (1, -1):
            br((XM + 15 * sx, 270, z), (sx, 0, 0), (0, -1, 0)); br((XM + 15 * sx, 30, z), (sx, 0, 0), (0, 1, 0))
    for y in ys:
        for sx in (1, -1):
            br((XM + 15 * sx, y, -30), (sx, 0, 0), (0, 0, -1)); br((XM + 15 * sx, y, -270), (sx, 0, 0), (0, 0, 1))
    for x, sx in ((30, 1), (1470, -1)):              # углы без кубов: торцевые стойки и поперечины на уголках (+ торцевой винт М8)
        for z in zs:
            br((x, 270, z), (sx, 0, 0), (0, -1, 0)); br((x, 30, z), (sx, 0, 0), (0, 1, 0))
        for y in ys:
            br((x, y, -30), (sx, 0, 0), (0, 0, -1)); br((x, y, -270), (sx, 0, 0), (0, 0, 1))
    for x in (70, 1430):
        for z in zs:
            S.add('OPORA_D25_M6x20_A918', foot(), loc((x, -12, z), (1, 0, 0), (0, 1, 0)), 'black')
    # ---- плиты, двигатели, шкивы, упоры
    P3, Lv16, Lv50, W18 = plate3(), lever_screw(16), lever_screw(50), washer()
    Pu = pulley2()
    for side in ('L', 'R'):
        x0 = PX[side]; xc = x0 + 150; g = 'PRIVOD_' + side
        S.add('PLITA_DVIGATELYA_300x300x3', P3, loc((x0, 0, 0), (1, 0, 0), (0, 0, 1)), 'alu', g)
        for hx in (x0 + HOLE_EDGE, x0 + PLATE - HOLE_EDGE):
            for hy in (HOLE_EDGE, PLATE - HOLE_EDGE):
                S.add('VINT_S_RUKOYATKOY_M6x16_A393', Lv16, loc((hx, hy, PLATE_T + 6.6), (1 if hy > 150 else -1, 0.4 * (1 if hy > 150 else -1), 0), (0, 0, 1)), 'black', g)
                S.add('SHAYBA_M6_D18', W18, loc((hx, hy, PLATE_T), (1, 0, 0), (0, 0, 1)), 'steel', g)
                S.add('VTULKA_6x5_B229', sleeve(5), loc((hx, hy, PLATE_T + 1.6), (1, 0, 0), (0, 0, 1)), 'steel', g)
        S.add('DVIGATEL_USLOVNO', cq.Workplane('XY').circle(55).extrude(-160).union(cq.Workplane('XY').circle(11).extrude(BZ + 15)), loc((xc, Y_AX, 0), (1, 0, 0), (0, 0, 1)), 'motor', g)
        S.add('SHKIV_PL5_D100', Pu, loc((xc, Y_AX, BZ), (1, 0, 0), (0, 0, 1)), 'print2' if side == 'L' else 'print', g)
        sx = x0 + (215 if side == 'L' else 85)
        st, pads = ustop(sx, 1 if side == 'L' else -1)
        S.add('UPOR_P_OBRAZNYY', st, None, 'print', 'UPORY')
        for p in pads: S.add('NAKLADKA', p, None, 'black', 'UPORY')
        if side == 'R':      # натяжитель: ушко на плите → винт М6×50 через уголок на торце рамы → пружина
            xl = x0 + PLATE - LUG_EDGE + 16          # угол ушка у кромки плиты
            S.add('UGOLOK_30x30_A990', bracket(), loc((xl, Y_AX, PLATE_T), (-1, 0, 0), (0, 1, 0)), 'zinc', g)
            an = cq.Workplane('XY').box(4, 40, 60, centered=(False, True, False)).translate((L, Y_AX, -30)).edges('|X').fillet(3)
            for z in (-15, PLATE_T + 16):
                an = an.cut(cq.Workplane('YZ').center(Y_AX, z).circle(3.3).extrude(4).translate((L, 0, 0)))
            S.add('PLASTINA_YAKOR_4MM', an, None, 'zinc', g)
            S.add('VINT_M6x12_ISO7380', S6, loc((L + 4, Y_AX, -15), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('GAYKA_M6', nut(6), loc((xl - 4.5 - 5, Y_AX, PLATE_T + 16), (0, 1, 0), (1, 0, 0)), 'steel', g)
            xa = L + 4.0
            S.add('SHAYBA_M6_D18', W18, loc((xa, Y_AX, PLATE_T + 16), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('PRUZHINA_16x2.5x25', spring(18), loc((xa + 1.6, Y_AX, PLATE_T + 16), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('SHAYBA_M6_D18', W18, loc((xa + 19.6, Y_AX, PLATE_T + 16), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('VINT_S_RUKOYATKOY_M6x50_A398', Lv50, loc((xa + 21.2, Y_AX, PLATE_T + 16), (0, 1, 0), (1, 0, 0)), 'black', g)
        else:
            fx = cq.Workplane('XY').box(20, 20, 12, centered=(False, True, False)).translate((x0 + PLATE + 0.5, 15, 0)).edges('|Z').fillet(2)
            S.add('FIKSATOR_PLITY', fx, None, 'print', g)
    S.add('REMEN_PL5', belt4(PX['L'] + 150, PX['R'] + 150), None, 'belt', 'KARETKA')
    up, lo = clamp4(c)
    S.add('GUBKA_VERHNYAYA', up, None, 'print2', 'KARETKA')
    S.add('GUBKA_NIZHNYAYA', lo, None, 'print', 'KARETKA')
    for x in (-20, 20):
        for z in (BZ - 7.05, BZ + 7.05):
            S.add('VINT_M4x40', screw(4, 40), loc((c + x, YU1, z), (1, 0, 0), (0, 1, 0)), 'steel', 'KARETKA')
            S.add('GAYKA_M4', nut(4), loc((c + x, YL0 - 3.2, z), (1, 0, 0), (0, 1, 0)), 'steel', 'KARETKA')
    # ---- узел реверса на средней стойке
    g = 'UZEL_REVERSA'; dz = STROKE if ext else 0.0
    for y in PIN_Y:
        S.add('SHTYR_D8', cq.Workplane('XY').circle(PIN_D / 2).extrude(48).translate((XM, y, -45 + dz)), None, 'red', g)
    yk = cq.Workplane('XY').box(28, 49, 5, centered=(True, True, False)).translate((XM, (PIN_Y[0] + PIN_Y[1]) / 2, -50 + dz))
    S.add('PLASTINA_SHTYREY', yk, None, 'alu', g)
    ys_ = (PIN_Y[0] + PIN_Y[1]) / 2
    S.add('ELEKTROMAGNIT', cq.Workplane('XY').box(30, 26, 39, centered=(True, True, False)).translate((XM, ys_, -102)), None, 'dark', g)
    S.add('SHTOK', cq.Workplane('XY').circle(3).extrude(13 + dz - 0.01).translate((XM, ys_, -63)), None, 'steel', g)
    for sx in (1, -1):    # щёки держателя на боковых пазах стойки
        ch = cq.Workplane('XY').box(6, 60, 106, centered=(False, True, False)).translate((XM + 15 if sx > 0 else XM - 21, ys_, -106))
        S.add('SHCHEKA_DERZHATELYA', ch, None, 'print', g)
        for y in (ys_ - 20, ys_ + 20):
            S.add('VINT_M6x12_ISO7380', S6, loc((XM + 21 * sx, y, -15), (0, 1, 0), (sx, 0, 0)), 'steel', g)
    S.add('PEREMYCHKA_DERZHATELYA', cq.Workplane('XY').box(42, 60, 4, centered=(True, True, False)).translate((XM, ys_, -106)), None, 'print', g)
    return S

def check(S, groups=('KARETKA', 'UZEL_REVERSA', 'UPORY', 'PRIVOD_R', 'PRIVOD_L')):
    its = S.items; bad = []
    def ov(A, B): return A.xmin < B.xmax - .05 and B.xmin < A.xmax - .05 and A.ymin < B.ymax - .05 and B.ymin < A.ymax - .05 and A.zmin < B.zmax - .05 and B.zmin < A.zmax - .05
    bbs = [i[2].BoundingBox() for i in its]
    for i, j in itertools.combinations(range(len(its)), 2):
        if its[i][3] not in groups and its[j][3] not in groups: continue
        if not ov(bbs[i], bbs[j]): continue
        if {its[i][0], its[j][0]} & {'VINT_M4x40', 'SHTOK'} and ('REMEN_PL5' in (its[i][0], its[j][0]) or 'PLASTINA_SHTYREY' in (its[i][0], its[j][0]) or 'ELEKTROMAGNIT' in (its[i][0], its[j][0])): continue
        if {its[i][0], its[j][0]} == {'REMEN_PL5', 'SHKIV_PL5_D100'}: continue
        try: v = its[i][2].intersect(its[j][2]).Volume()
        except Exception: v = -1
        if abs(v) > 2: bad.append((round(v, 1), its[i][1], its[j][1]))
    return bad

if __name__ == '__main__':
    import sys
    c, ext, tag = float(sys.argv[1]), sys.argv[2] == '1', sys.argv[3]
    S = build4(c, ext)
    if '--check' in sys.argv:
        for b in sorted(check(S), reverse=True)[:25]: print('CLASH', b)
    S.finish().save(f'out/m4_{tag}.glb'); print('saved', tag)
