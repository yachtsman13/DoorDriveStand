"""Эскиз 5 (рендер): зеркально — тормозной двигатель СЛЕВА (с натяжителем), испытуемый справа (неподвижный, заподлицо).
Зазор шкив–плита 5 мм. Зажим и упоры — дизайн пользователя («Каретка 1/2», «Упор») с доработкой.
Препятствие: 2 штыря через среднюю стойку, ведутся стальными пластинами спереди и сзади стойки."""
import itertools
import cadquery as cq
from model import (loc, profile, bracket, tnut, lever_screw, sleeve, washer, spring, foot, screw, nut,
                   Stand, PR, PLATE, PLATE_T, HOLE_EDGE, LUG_EDGE, Y_AX)
from model2 import pulley2, BELT_W
from model4 import check

L = 1500; XM = 750
PX = {'L': 10.0, 'R': 1200.0}                # тормозной слева (10 мм — запас натяжения), испытуемый справа заподлицо
GAP = 5.0
BZ = PLATE_T + GAP + 15                      # 23 — середина ремня от передней грани рамы
BT = 10.0                                    # толщина ремня PL
YBK = Y_AX + 51.0                            # 201 — спинка верхней ветви
YRT = YBK - BT                               # 191 — вершины рёбер
YC = (YBK + YRT) / 2                         # 196
CW = 24.26; CZ0, CZ1 = BZ - CW / 2, BZ + CW / 2
CL = 60.0                                    # длина зажима вдоль ремня
# губки пользователя: «Каретка 2» гладкая (пласт. 5 + блок 20), «Каретка 1» рифлёная (рёбра 5 + пласт. 5 + блок 18)
K2 = (YBK, YBK + 5, YBK + 25.2)              # 201 / 206 / 226,2
K1 = (YRT, YRT - 5, YRT - 5 - 18)            # 191 рёбра→ / 186 / 168
PIN_Y = ((K1[2] + K1[1]) / 2 + 0.5, (K2[1] + K2[2]) / 2)   # ≈177,5 и 216
PIN_D, STROKE = 8.0, 10.0
STEEL_T = 4.0
STOP_Y = (YC - 18.55, YC + 18.55)            # отверстия «Упора»: шаг 37,1 поперёк ремня
TOWER_H = 34.0                               # стойки упора 25 → 34 мм (ремень теперь шире перекрывается)

def plate5():
    p = cq.Workplane('XY').box(PLATE, PLATE, PLATE_T, centered=False)
    pts = [(HOLE_EDGE, HOLE_EDGE), (PLATE - HOLE_EDGE, HOLE_EDGE), (HOLE_EDGE, PLATE - HOLE_EDGE), (PLATE - HOLE_EDGE, PLATE - HOLE_EDGE)]
    p = p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints(pts).hole(8)
    ex = [(LUG_EDGE, 150), (PLATE - LUG_EDGE, 150)] + [(x, y) for x in (85, 215) for y in STOP_Y]
    p = p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints(ex).hole(4.5 if False else 6.5)
    return p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints([(150, 150)]).hole(30)

def belt5(x1, x2):
    ro, ri = 51.0, 51.0 - BT
    o = cq.Workplane('XY').slot2D(x2 - x1 + 2 * ro, 2 * ro).extrude(BELT_W)
    i = cq.Workplane('XY').slot2D(x2 - x1 + 2 * ri, 2 * ri).extrude(BELT_W)
    return o.cut(i).translate(((x1 + x2) / 2, Y_AX, BZ - BELT_W / 2))

def clamp5(c):
    """Зажим по образцу пользователя; доработка — блоки на всю длину 60 мм, чтобы торцы зажима
    по обе стороны ремня были сплошными (в них бьют упоры и штыри)."""
    box = lambda y0, y1: cq.Workplane('XY').box(CL, y1 - y0, CW, centered=(True, False, True)).translate((c, y0, BZ))
    up = box(K2[0], K2[2])
    lo = box(K1[2], K1[1])
    for i in range(6):
        z = BZ - BELT_W / 2 + i * 4.7
        lo = lo.union(cq.Workplane('YZ').polyline([(0, -2.0), (5.0, -0.6), (5.0, 0.6), (0, 2.0)]).close().extrude(CL).translate((c - CL / 2, K1[1], z)))
    lo = lo.intersect(box(K1[2], K1[0] + 0.01))
    for x in (-20, 20):
        for z in (BZ - 7.05, BZ + 7.05):
            h = cq.Workplane('XZ').center(c + x, z).circle(2.25).extrude(-80).translate((0, 150, 0))
            up = up.cut(h); lo = lo.cut(h)
    return up, lo

def ustop5(xc):
    """«Упор» пользователя: основание + 2 стойки 19 мм, зазор 18,1 под ремень; стойки подняты до 34 мм."""
    s = cq.Workplane('XY').box(20, 56.1, 5, centered=(True, True, False)).translate((xc, YC, PLATE_T))
    for y0 in (YC - 9.05 - 19, YC + 9.05):
        s = s.union(cq.Workplane('XY').box(20, 19, TOWER_H, centered=(True, False, False)).translate((xc, y0, PLATE_T)))
    for y in STOP_Y:
        s = s.cut(cq.Workplane('XY').circle(2.25).extrude(60).translate((xc, y, 0)))
    return s

def build5(c=600, ext=False):
    S = Stand()
    Pl, Pc, Br, Tn = profile(L), profile(240), bracket(), tnut()
    S6 = screw(6, 12)
    ys, zs = (15, 285), (-15, -285)
    for y in ys:
        for z in zs:
            S.add('PROFIL_30x30_L1500', Pl, loc((0, y, z), (0, 1, 0), (1, 0, 0)))
    for x in (15, XM, 1485):
        for z in zs:
            if x == XM and z == -15:
                p = Pc.val().located(loc((x, PR, z), (1, 0, 0), (0, 1, 0)))
                for y in PIN_Y:
                    p = p.cut(cq.Workplane('XY').circle(6).extrude(40).translate((x, y, -35)).val())     # Ø12 — зазор, штырь стойки не касается
                S.add('STOYKA_SREDNYAYA_OTV_D12', cq.Workplane().add(p), None, 'alu2')
            else:
                S.add('PROFIL_30x30L_L240', Pc, loc((x, PR, z), (1, 0, 0), (0, 1, 0)), 'alu2')
        for y in ys:
            S.add('PROFIL_30x30L_L240', Pc, loc((x, y, -PR), (1, 0, 0), (0, 0, -1)), 'alu2')
    def br(origin, d1, d2):
        zz = cq.Vector(*d1).cross(cq.Vector(*d2))
        S.add('UGOLOK_30x30_A990', Br, loc(origin, d1, (zz.x, zz.y, zz.z)), 'zinc')
    for x, sx_list in ((XM, (1, -1)), (30, (1,)), (1470, (-1,))):
        xs = [(x + 15 * s, s) for s in sx_list] if x == XM else [(x, sx_list[0])]
        for xx, s in xs:
            for z in zs:
                br((xx, 270, z), (s, 0, 0), (0, -1, 0)); br((xx, 30, z), (s, 0, 0), (0, 1, 0))
            for y in ys:
                br((xx, y, -30), (s, 0, 0), (0, 0, -1)); br((xx, y, -270), (s, 0, 0), (0, 0, 1))
    for x in (70, 1430):
        for z in zs:
            S.add('OPORA_D25_M6x20_A918', foot(), loc((x, -12, z), (1, 0, 0), (0, 1, 0)), 'black')
    P5, Lv16, Lv50, W18 = plate5(), lever_screw(16), lever_screw(50), washer()
    Pu = pulley2()
    for side in ('L', 'R'):
        x0 = PX[side]; xc = x0 + 150; g = 'PRIVOD_' + side
        S.add('PLITA_DVIGATELYA_300x300x3', P5, loc((x0, 0, 0), (1, 0, 0), (0, 0, 1)), 'alu', g)
        for hx in (x0 + HOLE_EDGE, x0 + PLATE - HOLE_EDGE):
            for hy in (HOLE_EDGE, PLATE - HOLE_EDGE):
                S.add('VINT_S_RUKOYATKOY_M6x16_A393', Lv16, loc((hx, hy, PLATE_T + 6.6), (1 if hy > 150 else -1, 0.4 * (1 if hy > 150 else -1), 0), (0, 0, 1)), 'black', g)
                S.add('SHAYBA_M6_D18', W18, loc((hx, hy, PLATE_T), (1, 0, 0), (0, 0, 1)), 'steel', g)
                S.add('VTULKA_6x5_B229', sleeve(5), loc((hx, hy, PLATE_T + 1.6), (1, 0, 0), (0, 0, 1)), 'steel', g)
        mot = cq.Workplane('XY').circle(55).extrude(-160).union(cq.Workplane('XY').circle(11).extrude(BZ + 15))
        S.add('DVIGATEL_USLOVNO', mot, loc((xc, Y_AX, 0), (1, 0, 0), (0, 0, 1)), 'motor', g)
        S.add('SHKIV_PL5_D100', Pu, loc((xc, Y_AX, BZ), (1, 0, 0), (0, 0, 1)), 'print' if side == 'L' else 'print2', g)
        S.add('UPOR_POLZOVATELYA_H34', ustop5(x0 + (215 if side == 'L' else 85)), None, 'print', 'UPORY')
        if side == 'L':      # натяжитель — у тормозного (слева), тянет плиту наружу к торцу рамы
            S.add('UGOLOK_30x30_A990', bracket(), loc((x0, Y_AX, PLATE_T), (1, 0, 0), (0, -1, 0)), 'zinc', g)
            an = cq.Workplane('XY').box(4, 40, 60, centered=(False, True, False)).translate((-4, Y_AX, -30)).edges('|X').fillet(3)
            for z in (-15, PLATE_T + 16):
                an = an.cut(cq.Workplane('YZ').center(Y_AX, z).circle(3.3).extrude(4).translate((-4, 0, 0)))
            S.add('PLASTINA_YAKOR', an, None, 'zinc', g)
            S.add('VINT_M6x12_ISO7380', S6, loc((-4, Y_AX, -15), (0, 1, 0), (-1, 0, 0)), 'steel', g)
            zr = PLATE_T + 16
            S.add('GAYKA_M6', nut(6), loc((x0 + 4.5, Y_AX, zr), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('SHAYBA_M6_D18', W18, loc((-4, Y_AX, zr), (0, 1, 0), (-1, 0, 0)), 'steel', g)
            S.add('PRUZHINA_16x2.5x25', spring(18), loc((-5.6, Y_AX, zr), (0, 1, 0), (-1, 0, 0)), 'steel', g)
            S.add('SHAYBA_M6_D18', W18, loc((-23.6, Y_AX, zr), (0, 1, 0), (-1, 0, 0)), 'steel', g)
            S.add('VINT_S_RUKOYATKOY_M6x50_A398', Lv50, loc((-25.2, Y_AX, zr), (0, 1, 0), (-1, 0, 0)), 'black', g)
        else:                # фиксатор неподвижной плиты испытуемого привода
            fx = cq.Workplane('XY').box(20, 20, 12, centered=(False, True, False)).translate((x0 - 20.5, 15, 0)).edges('|Z').fillet(2)
            S.add('FIKSATOR_PLITY', fx, None, 'print', g)
    S.add('REMEN_PL5', belt5(PX['L'] + 150, PX['R'] + 150), None, 'belt', 'KARETKA')
    up, lo = clamp5(c)
    S.add('KARETKA_2_GLADKAYA', up, None, 'print2', 'KARETKA')
    S.add('KARETKA_1_RIFLENAYA', lo, None, 'print2', 'KARETKA')
    for x in (-20, 20):
        for z in (BZ - 7.05, BZ + 7.05):
            S.add('VINT_M4x60', screw(4, 60), loc((c + x, K2[2], z), (1, 0, 0), (0, 1, 0)), 'steel', 'KARETKA')
    # ---- узел реверса
    g = 'UZEL_REVERSA'; dz = STROKE if ext else 0.0
    sp = cq.Workplane('XY').box(30, 80, STEEL_T, centered=(True, True, False))
    for y in PIN_Y:
        sp = sp.cut(cq.Workplane('XY').circle(PIN_D / 2 + 0.05).extrude(10).translate((0, y - YC, -1)))
    for y in (-32, 32):
        sp = sp.cut(cq.Workplane('XY').circle(3.3).extrude(10).translate((0, y, -1)))
    S.add('PLASTINA_STALNAYA_PEREDNYAYA', sp.translate((XM, YC, 0)), None, 'steel', g)
    S.add('PLASTINA_STALNAYA_ZADNYAYA', sp.translate((XM, YC, -PR - STEEL_T)), None, 'steel', g)
    for y in (YC - 32, YC + 32):
        S.add('VINT_M6x12_ISO7380', S6, loc((XM, y, STEEL_T), (1, 0, 0), (0, 0, 1)), 'steel', g)
        S.add('VINT_M6x12_ISO7380', S6, loc((XM, y, -PR - STEEL_T), (1, 0, 0), (0, 0, -1)), 'steel', g)
    zt = 8.0                                   # торец штыря во втянутом положении (зазор до зажима ≈3 мм)
    yk0 = -PR - STEEL_T - 1 - 6 - STROKE       # пластина штырей втянута: −51..−45; выдвинута упирается в заднюю стальную
    for y in PIN_Y:
        S.add('SHTYR_D8', cq.Workplane('XY').circle(PIN_D / 2).extrude(zt - yk0).translate((XM, y, yk0 + dz)), None, 'red', g)
    S.add('PLASTINA_SHTYREY', cq.Workplane('XY').box(26, 60, 6, centered=(True, True, False)).translate((XM, YC, yk0 - 6 + dz)), None, 'alu', g)
    S.add('ELEKTROMAGNIT', cq.Workplane('XY').box(30, 26, 39, centered=(True, True, False)).translate((XM, YC, yk0 - 6 - 8 - 39)), None, 'dark', g)
    S.add('SHTOK', cq.Workplane('XY').circle(3).extrude(8 + dz).translate((XM, YC, yk0 - 6 - 8)), None, 'steel', g)
    for sx in (1, -1):
        ch = cq.Workplane('XY').box(6, 60, 110, centered=(False, True, False)).translate((XM + 15 if sx > 0 else XM - 21, YC, -110))
        S.add('SHCHEKA_DERZHATELYA', ch, None, 'print', g)
    S.add('PEREMYCHKA_DERZHATELYA', cq.Workplane('XY').box(30, 60, 4, centered=(True, True, False)).translate((XM, YC, -110)), None, 'print', g)
    return S

if __name__ == '__main__':
    import sys
    c, ext, tag = float(sys.argv[1]), sys.argv[2] == '1', sys.argv[3]
    S = build5(c, ext)
    if '--check' in sys.argv:
        for b in sorted(check(S, ('KARETKA', 'UZEL_REVERSA', 'UPORY', 'PRIVOD_R', 'PRIVOD_L')), reverse=True)[:25]: print('CLASH', b)
    S.finish().save(f'out/m5_{tag}.glb'); print('saved', tag, 'c', c)
