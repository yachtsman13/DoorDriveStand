"""Вариант В: каретка на линейной направляющей MGN12H. Удар упоров и препятствия — в торец зажима по линии ремня.
Координаты: X вдоль стенда 0..1500, Y вверх, Z на оператора (рама Z −300..0). Размеры в мм."""
import math
import cadquery as cq
from model import (loc, profile, cube, bracket, tnut, lever_screw, standoff, sleeve, washer, spring, foot, screw, nut,
                   motor_dummy, Stand, PR, L_LONG, L_CROSS, X_MID, PLATE, PLATE_T, PLATE_X0, HOLE_EDGE, LUG_EDGE,
                   ROD_Z, ANCH_Z, BELT_Z, Y_AX, L_FRAME, CL_DX, CL_DZ)
from model2 import pulley2, BELT_W

# ---------------- ремень PL5 (по шкиву пользователя)
BELT_RI, BELT_RO = 47.2, 51.0           # условно: тело ремня над гребнями шкива / спинка
Y_BT = Y_AX + BELT_RO                    # 201 спинка верхней ветви
Y_RIB = Y_AX + 47.0                      # 197 вершины рёбер нижней губки
ZB0, ZB1 = BELT_Z - BELT_W / 2, BELT_Z + BELT_W / 2      # 28,25 .. 51,75
# ---------------- направляющая
RAIL_X0, RAIL_L = 250, 1000              # MGN12, 1000 мм
Y_RAIL = 300                             # низ рельса = верх профиля
BLK_L, BLK_W, BLK_H = 45.4, 27.0, 13.0   # MGN12H: длина, ширина, высота от низа рельса
Y_PL0, PL_T = Y_RAIL + BLK_H, 5.0        # площадка каретки 313..318
PL_Z0, PL_Z1 = -28.0, 74.0
# стойка каретки (профиль 30x30L)
ARM_Z0 = 38.0; ARM_Z1 = ARM_Z0 + 30      # 38..68
ARM_Y0 = 216.0                           # низ стойки
# зажим
J_X = 30.0                               # полудлина губок: ударные торцы на x = c ± 30
J_ZR0, J_ZR1 = 10.0, 26.0                # задняя «ударная» стенка зажима (за ремнём)
J_Y0, J_Y1 = 177.0, 213.0                # зажим по высоте
J_ZF = ARM_Z1 + 6                        # передний край верхней губки (лапка на стойке)
# упоры на плитах
STOP_LOCAL_X = (85, 215)
STOP_Y = (185, 205)                      # отв. Ø6,5 в плите под упор
PAD = 4.0
STOP_FACE = {'L': PLATE_X0['L'] + 215 + 10 + PAD, 'R': PLATE_X0['R'] + 85 - 10 - PAD}   # 269 / 1231
C_MIN, C_MAX = STOP_FACE['L'] + J_X, STOP_FACE['R'] - J_X                              # 299 / 1201
# узел реверса (заслонка на переставной стойке)
OBST_X = 900
G_W, G_T, STROKE = 20.0, 8.0, 10.0       # заслонка: ширина по X, толщина по Z, ход
G_Z_IN = 1.0                             # втянута: z 1..9; выдвинута: 11..19
G_Y0, G_Y1 = 106.0, 246.0                # заслонка по высоте
GU_Y = ((J_Y1 + 3, J_Y1 + 27), (J_Y0 - 27, J_Y0 - 3))   # направляющие: 216..240 и 150..174
SOL = dict(L=39, W=30, H=26)             # электромагнит JF-1039B (габарит сверить)
SOL_Y = 115.0                            # ось штока
SOL_X = 36.0                             # смещение оси электромагнита от оси стойки по X

def plate3():
    p = cq.Workplane('XY').box(PLATE, PLATE, PLATE_T, centered=False)
    pts = [(HOLE_EDGE, HOLE_EDGE), (PLATE - HOLE_EDGE, HOLE_EDGE), (HOLE_EDGE, PLATE - HOLE_EDGE), (PLATE - HOLE_EDGE, PLATE - HOLE_EDGE)]
    p = p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints(pts).hole(8)
    extra = [(LUG_EDGE, PLATE / 2), (PLATE - LUG_EDGE, PLATE / 2)] + [(x, y) for x in STOP_LOCAL_X for y in STOP_Y]
    p = p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints(extra).hole(6.5)
    return p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints([(PLATE / 2, PLATE / 2)]).hole(30)

def belt3(x1, x2):
    o = cq.Workplane('XY').slot2D(x2 - x1 + 2 * BELT_RO, 2 * BELT_RO).extrude(BELT_W)
    i = cq.Workplane('XY').slot2D(x2 - x1 + 2 * BELT_RI, 2 * BELT_RI).extrude(BELT_W)
    return o.cut(i).translate(((x1 + x2) / 2, Y_AX, ZB0))

# ---------------- направляющая MGN12
def mgn_rail():
    r = cq.Workplane('XY').box(RAIL_L, 8, 12, centered=(False, False, True)).translate((RAIL_X0, Y_RAIL, -15))
    for i in range(RAIL_L // 25):
        x = RAIL_X0 + 12.5 + i * 25
        r = r.cut(cq.Workplane('XZ').center(x, -15).circle(1.75).extrude(-8).translate((0, Y_RAIL, 0)))
        r = r.cut(cq.Workplane('XZ').center(x, -15).circle(3.0).extrude(-4.5).translate((0, Y_RAIL + 3.5, 0)))
    return r

def mgn_block(c):
    b = cq.Workplane('XY').box(BLK_L, BLK_H - 3, BLK_W, centered=(True, False, True)).translate((c, Y_RAIL + 3, -15))
    ends = cq.Workplane('XY').box(4, BLK_H - 4, BLK_W - 2, centered=(True, False, True))
    b = b.union(ends.translate((c - BLK_L / 2 - 2, Y_RAIL + 4, -15))).union(ends.translate((c + BLK_L / 2 + 2, Y_RAIL + 4, -15)))
    b = b.cut(cq.Workplane('XY').box(BLK_L + 10, 5.2, 12.4, centered=(True, False, True)).translate((c, Y_RAIL + 2.8, -15)))
    for x in (-10, 10):
        for z in (-25, -5):
            b = b.cut(cq.Workplane('XZ').center(c + x, z).circle(1.25).extrude(-4).translate((0, Y_PL0 - 4, 0)))
    return b

def rail_cap(x, d):
    """Ограничитель у торца рельса (PETG), М6 в верхний паз профиля — страховка от схода каретки."""
    x0 = x - 12 if d < 0 else x
    s = cq.Workplane('XY').box(12, 14, 27, centered=(False, False, True)).translate((x0, Y_RAIL, -15)).edges('|Y').fillet(2)
    return s.cut(cq.Workplane('XZ').center(x0 + 6, -15).circle(3.3).extrude(-14).translate((0, Y_RAIL, 0)))

def carriage_plate(c):
    """Площадка каретки: лист Д16/АМг 5 мм, 70 × 102."""
    p = cq.Workplane('XY').box(70, PL_T, PL_Z1 - PL_Z0, centered=(True, False, False)).translate((c, Y_PL0, PL_Z0))
    p = p.edges('|Y').fillet(4)
    for x in (-10, 10):
        for z in (-25, -5):
            p = p.cut(cq.Workplane('XZ').center(c + x, z).circle(1.7).extrude(-PL_T).translate((0, Y_PL0, 0)))
    for x in (-31, 31):
        p = p.cut(cq.Workplane('XZ').center(c + x, (ARM_Z0 + ARM_Z1) / 2).circle(3.25).extrude(-PL_T).translate((0, Y_PL0, 0)))
    return p

JAW_HOLES = [(x, z) for x in (-CL_DX / 2, CL_DX / 2) for z in (BELT_Z - CL_DZ / 2, BELT_Z + CL_DZ / 2, 18.0)]
CB = 6.0      # глубина цековки под головку М4 в верхней губке

def jaw_upper(c):
    """Губка верхняя (PETG): над ремнём + задняя ударная стенка за ремнём + лапка на стойку."""
    j = cq.Workplane('XY').box(2 * J_X, J_Y1 - Y_BT, J_ZF - J_ZR0, centered=(True, False, False)).translate((c, Y_BT, J_ZR0))
    j = j.union(cq.Workplane('XY').box(2 * J_X, Y_BT - (Y_RIB - 4), J_ZR1 - J_ZR0, centered=(True, False, False)).translate((c, Y_RIB - 4, J_ZR0)))
    j = j.union(cq.Workplane('XY').box(30, 40, 6, centered=(True, False, False)).translate((c, J_Y1, ARM_Z1)))
    for y in (J_Y1 + 12, J_Y1 + 30):
        j = j.cut(cq.Workplane('XY').slot2D(10, 6.6, 90).extrude(6).translate((c, y, ARM_Z1)))
    for x, z in JAW_HOLES:
        j = j.cut(cq.Workplane('XZ').center(c + x, z).circle(2.25).extrude(-70).translate((0, 160, 0)))
        j = j.cut(cq.Workplane('XZ').center(c + x, z).circle(3.75).extrude(-CB - 1).translate((0, J_Y1 - CB, 0)))
    return j

def jaw_lower(c):
    """Губка нижняя рифлёная (PETG): 6 рёбер шаг 4,7 входят между ручьями PL5, гнёзда под гайки М4 снизу."""
    j = cq.Workplane('XY').box(2 * J_X, Y_RIB - 5.1 - J_Y0, ZB1 + 0.5 - J_ZR0, centered=(True, False, False)).translate((c, J_Y0, J_ZR0))
    j = j.union(cq.Workplane('XY').box(2 * J_X, Y_RIB - 4 - J_Y0, J_ZR1 - J_ZR0, centered=(True, False, False)).translate((c, J_Y0, J_ZR0)))
    for i in range(6):
        z = ZB0 + i * 4.7
        rib = cq.Workplane('YZ').polyline([(0, -2.0), (5.1, -0.6), (5.1, 0.6), (0, 2.0)]).close().extrude(2 * J_X).translate((c - J_X, Y_RIB - 5.1, z))
        j = j.union(rib)
    j = j.intersect(cq.Workplane('XY').box(2 * J_X, 40, ZB1 + 0.5 - J_ZR0, centered=(True, False, False)).translate((c, J_Y0, J_ZR0)))
    for x, z in JAW_HOLES:
        j = j.cut(cq.Workplane('XZ').center(c + x, z).circle(2.25).extrude(-40).translate((0, J_Y0 - 1, 0)))
        j = j.cut(cq.Workplane('XZ').center(c + x, z).polygon(6, 7.3 / math.cos(math.pi / 6)).extrude(-3.6).translate((0, J_Y0 - 0.2, 0)))
    return j

def end_stop(side):
    """Упор концевой на плите (PETG) + резиновая накладка; бьёт в торец зажима по линии ремня."""
    xc = PLATE_X0[side] + (215 if side == 'L' else 85)
    s = cq.Workplane('XY').box(20, 44, J_ZR1 - 2 - PLATE_T, centered=(True, False, False)).translate((xc, 173, PLATE_T)).edges('|Z').fillet(2)
    for y in STOP_Y:
        s = s.cut(cq.Workplane('XY').circle(3.3).extrude(40).translate((xc, y, 0)))
        s = s.cut(cq.Workplane('XY').circle(5.6).extrude(40).translate((xc, y, 14)))
    d = 1 if side == 'L' else -1
    pad = cq.Workplane('XY').box(PAD, 34, 14, centered=(False, False, False)).translate((xc + 10 if d > 0 else xc - 10 - PAD, 178, J_ZR0 - 1))
    return s, pad, xc

# ---------------- узел реверса
def post_cross_brackets(S, x, g):
    Br, Tn = bracket(), tnut()
    for sx in (1, -1):
        for y, d2 in ((270, (0, -1, 0)), (30, (0, 1, 0))):
            z = cq.Vector(sx, 0, 0).cross(cq.Vector(*d2))
            S.add('UGOLOK_30x30_A990', Br, loc((x + 15 * sx, y, -15), (sx, 0, 0), (z.x, z.y, z.z)), 'zinc', g)

GUIDE_ZF = 24.0
def gate_guide(x, y0, y1):
    """Направляющая заслонки (PETG): обхватывает стойку, крепится 2×М6 в боковые пазы; канал под заслонку открыт по Y."""
    h = y1 - y0
    g = cq.Workplane('XY').box(42, h, GUIDE_ZF, centered=(True, False, False)).translate((x, y0, 0))
    for sx in (1, -1):
        g = g.union(cq.Workplane('XY').box(5.8, h, 26, centered=(False, False, False)).translate((x + 15.2 if sx > 0 else x - 21, y0, -26)))
    g = g.cut(cq.Workplane('XY').box(G_W + 0.6, h + 2, G_T + STROKE + 1.4, centered=(True, False, False)).translate((x, y0 - 1, G_Z_IN - 0.4)))
    g = g.cut(cq.Workplane('YZ').center(y0 + h / 2, -15).circle(3.3).extrude(50).translate((x - 25, 0, 0)))
    return g

def gate(x, ext):
    """Заслонка: лист Д16Т s8 (лазер), с лапкой к штоку электромагнита."""
    z0 = G_Z_IN + (STROKE if ext else 0)
    g = cq.Workplane('XY').box(G_W, G_Y1 - G_Y0, G_T, centered=(True, False, False)).translate((x, G_Y0, z0))
    lug = cq.Workplane('XY').box(SOL_X + 8, 14, G_T, centered=(False, True, False)).translate((x, SOL_Y, z0))
    g = g.union(lug)
    g = g.cut(cq.Workplane('XY').circle(1.6).extrude(G_T).translate((x + SOL_X, SOL_Y, z0)))
    return g

def solenoid3(x, ext):
    """Электромагнит JF-1039B (условно): ось вдоль Z, шток вперёд."""
    s = cq.Workplane('XY').box(SOL['W'], SOL['H'], SOL['L'], centered=(True, True, False)).translate((x + SOL_X, SOL_Y, -SOL['L'] - 1))
    rod = cq.Workplane('XY').circle(3).extrude(1 + G_Z_IN + (STROKE if ext else 0)).translate((x + SOL_X, SOL_Y, -1))
    return s, rod

def sol_holder(x):
    """Держатель электромагнита (PETG): крепится к боковому пазу стойки 2×М6."""
    xs = x + SOL_X
    h = cq.Workplane('XY').box(SOL['W'] + 8, SOL['H'] + 8, SOL['L'] - 4, centered=(True, True, False)).translate((xs, SOL_Y, -SOL['L'] - 1))
    h = h.cut(cq.Workplane('XY').box(SOL['W'] + 0.4, SOL['H'] + 0.4, SOL['L'] + 2, centered=(True, True, False)).translate((xs, SOL_Y, -SOL['L'] - 3)))
    h = h.cut(cq.Workplane('XY').box(SOL['W'] - 6, SOL['H'] + 10, SOL['L'] - 14, centered=(True, True, False)).translate((xs, SOL_Y, -SOL['L'] + 6)))   # окна
    flange = cq.Workplane('XY').box(4, 56, 30, centered=(False, True, False)).translate((x + 15, SOL_Y, -30))
    h = h.union(flange)
    for y in (SOL_Y - 24, SOL_Y + 24):
        h = h.cut(cq.Workplane('YZ').center(y, -15).circle(3.3).extrude(6).translate((x + 14, 0, 0)))
    return h

def build3(c=520, gate_ext=False):
    S = Stand()
    P_long, P_cross = profile(L_LONG), profile(L_CROSS)
    Cb, Br, Tn = cube(), bracket(), tnut()
    S6x12 = screw(6, 12)
    ys, zs = (15, 285), (-15, -285)
    for y in ys:
        for z in zs:
            S.add('PROFIL_30x30_L1440', P_long, loc((PR, y, z), (0, 1, 0), (1, 0, 0)))
            for x in (15, 1485):
                S.add('KUB_30x30_B943', Cb, loc((x, y, z), (1, 0, 0), (0, 0, 1)), 'black')
    for x in (15, X_MID, 1485):
        for z in zs:
            S.add('PROFIL_30x30L_L240', P_cross, loc((x, PR, z), (1, 0, 0), (0, 1, 0)), 'alu2')
        for y in ys:
            S.add('PROFIL_30x30L_L240', P_cross, loc((x, y, -PR), (1, 0, 0), (0, 0, -1)), 'alu2')
    def br(origin, d1, d2, g='RAMA'):
        z = cq.Vector(*d1).cross(cq.Vector(*d2))
        S.add('UGOLOK_30x30_A990', Br, loc(origin, d1, (z.x, z.y, z.z)), 'zinc', g)
        o = cq.Vector(*origin)
        for a in (0, 1):
            p = o + (cq.Vector(*d1) if a else cq.Vector(*d2)) * 16; n = cq.Vector(*d2) if a else cq.Vector(*d1)
            S.add('VINT_M6x12_ISO7380', S6x12, loc((p + n * 4.5).toTuple(), (z.x, z.y, z.z), n.toTuple()), 'steel', g)
            S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((p - n * 2.3).toTuple(), (z.x, z.y, z.z), n.toTuple()), 'steel', g)
    for z in zs:
        for sx in (1, -1):
            br((X_MID + 15 * sx, 270, z), (sx, 0, 0), (0, -1, 0)); br((X_MID + 15 * sx, 30, z), (sx, 0, 0), (0, 1, 0))
    for y in ys:
        for sx in (1, -1):
            br((X_MID + 15 * sx, y, -30), (sx, 0, 0), (0, 0, -1)); br((X_MID + 15 * sx, y, -270), (sx, 0, 0), (0, 0, 1))
    for x, sx in ((30, 1), (1470, -1)):
        for z in zs:
            br((x, 270, z), (sx, 0, 0), (0, -1, 0)); br((x, 30, z), (sx, 0, 0), (0, 1, 0))
    for x in (70, 1430):
        for z in zs:
            S.add('OPORA_D25_M6x20_A918', foot(), loc((x, -12, z), (1, 0, 0), (0, 1, 0)), 'black')
            S.add('GAYKA_M6', nut(6), loc((x, -5, z), (1, 0, 0), (0, 1, 0)), 'steel')
            S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((x, 2.3, z), (0, 0, 1), (0, -1, 0)), 'steel')
    # ---------------- приводы
    Pl, Lv16, Lv50, St, W18 = plate3(), lever_screw(16), lever_screw(50), standoff(30), washer()
    Pu = pulley2()
    for side in ('L', 'R'):
        g = 'PRIVOD_ISPYTUEMYY' if side == 'L' else 'PRIVOD_TORMOZNOY'
        x0 = PLATE_X0[side]; xc = x0 + PLATE / 2
        S.add('PLITA_DVIGATELYA_300x300x3', Pl, loc((x0, 0, 0), (1, 0, 0), (0, 0, 1)), 'alu', g)
        for hx in (x0 + HOLE_EDGE, x0 + PLATE - HOLE_EDGE):
            for hy in (HOLE_EDGE, PLATE - HOLE_EDGE):
                S.add('SHAYBA_M6_D18', W18, loc((hx, hy, PLATE_T), (1, 0, 0), (0, 0, 1)), 'steel', g)
                S.add('VTULKA_6x5_B229', sleeve(5), loc((hx, hy, PLATE_T + 1.6), (1, 0, 0), (0, 0, 1)), 'steel', g)
                S.add('VINT_S_RUKOYATKOY_M6x16_A393', Lv16, loc((hx, hy, PLATE_T + 6.6), (1 if hy > 150 else -1, 0.4 * (1 if hy > 150 else -1), 0), (0, 0, 1)), 'black', g)
                S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((hx, hy, -2.3), (0, 1, 0), (0, 0, 1)), 'steel', g)
        S.add('DVIGATEL_USLOVNO', motor_dummy(), loc((xc, Y_AX, 0), (1, 0, 0), (0, 0, 1)), 'motor', g)
        S.add('SHKIV_PL5_D100', Pu, loc((xc, Y_AX, BELT_Z), (1, 0, 0), (0, 0, 1)), 'print2', g)
        st, pad, sxx = end_stop(side)
        S.add('UPOR_KONCEVOY_V', st, None, 'print', 'UPORY')
        S.add('NAKLADKA_REZINA_4', pad, None, 'black', 'UPORY')
        for y in STOP_Y:
            S.add('VINT_M6x20_DIN912', screw(6, 20), loc((sxx, y, 14), (1, 0, 0), (0, 0, 1)), 'steel', 'UPORY')
            S.add('GAYKA_M6', nut(6), loc((sxx, y, -5), (1, 0, 0), (0, 0, 1)), 'steel', 'UPORY')
        if side == 'R':
            xo, xe = x0 + PLATE, L_FRAME; xa = xe + 1
            S.add('UGOLOK_30x30_A990', Br, loc((xo, Y_AX, PLATE_T), (-1, 0, 0), (0, 1, 0)), 'zinc', g)
            S.add('VTULKA_REZB_M6x30_C318', St, loc((xo, Y_AX, ROD_Z), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('VINT_M6x8_ISO7380', screw(6, 8), loc((xo - 4.5, Y_AX, ROD_Z), (0, 1, 0), (-1, 0, 0)), 'steel', g)
            S.add('UGOLOK_30x30_A990', Br, loc((xa, Y_AX, ANCH_Z), (-1, 0, 0), (0, 1, 0)), 'zinc', g)
            S.add('SHAYBA_M6_D18', W18, loc((xe - 15, Y_AX, 0), (1, 0, 0), (0, 0, 1)), 'steel', g)
            S.add('SHAYBA_M6_D18', W18, loc((xe - 15, Y_AX, 1.6), (1, 0, 0), (0, 0, 1)), 'steel', g)
            S.add('VINT_M6x16_ISO7380', screw(6, 16), loc((xe - 15, Y_AX, ANCH_Z + 4.5), (1, 0, 0), (0, 0, 1)), 'steel', g)
            S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((xe - 15, Y_AX, -2.3), (1, 0, 0), (0, 0, 1)), 'steel', g)
            S.add('SHAYBA_M6_D18', W18, loc((xa, Y_AX, ROD_Z), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('PRUZHINA_16x2.5x25', spring(18), loc((xa + 1.6, Y_AX, ROD_Z), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('VTULKA_6x9_B255', sleeve(9), loc((xa + 1.6, Y_AX, ROD_Z), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('VTULKA_6x9_B255', sleeve(9), loc((xa + 10.6, Y_AX, ROD_Z), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('SHAYBA_M6_D18', W18, loc((xa + 19.6, Y_AX, ROD_Z), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('VINT_S_RUKOYATKOY_M6x50_A398', Lv50, loc((xa + 21.2, Y_AX, ROD_Z), (0, 1, 0), (1, 0, 0)), 'black', g)
        else:
            fx = cq.Workplane('XY').box(20, 20, 12, centered=(False, True, False)).translate((x0 + PLATE + 0.5, 15, 0)).edges('|Z').fillet(2)
            fx = fx.cut(cq.Workplane('XY').circle(3.3).extrude(12).translate((x0 + PLATE + 10.5, 15, 0)))
            S.add('FIKSATOR_PLITY', fx, None, 'print', g)
            S.add('VINT_M6x16_ISO7380', screw(6, 16), loc((x0 + PLATE + 10.5, 15, 12), (1, 0, 0), (0, 0, 1)), 'steel', g)
            S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((x0 + PLATE + 10.5, 15, -2.3), (0, 1, 0), (0, 0, 1)), 'steel', g)
    xl, xr = PLATE_X0['L'] + PLATE / 2, PLATE_X0['R'] + PLATE / 2
    S.add('REMEN_PL5_USLOVNO', belt3(xl, xr), None, 'belt', 'KARETKA')
    # ---------------- направляющая и каретка
    g = 'NAPRAVLYAYUSHCHAYA'
    S.add('RELS_MGN12_L1000', mgn_rail(), None, 'steel', g)
    T3 = cq.Workplane('XY').box(10, 7.8, 2.5, centered=(True, True, False)).translate((0, 0, -2.5)).union(
        cq.Workplane('XY').box(7.8, 7.8, 3, centered=(True, True, False)).translate((0, 0, -5.5))).cut(cq.Workplane('XY').circle(1.5).extrude(-6))
    for i in range(0, RAIL_L // 25, 2):
        x = RAIL_X0 + 12.5 + i * 25
        S.add('VINT_M3x10_DIN912', screw(3, 10), loc((x, Y_RAIL + 3.5, -15), (1, 0, 0), (0, 1, 0)), 'steel', g)
        S.add('T_GAYKA_M3_PAZ8', T3, loc((x, Y_RAIL - 2.3, -15), (0, 0, 1), (0, 1, 0)), 'steel', g)
    for xx, d in ((RAIL_X0, -1), (RAIL_X0 + RAIL_L, 1)):
        S.add('OGRANICHITEL_RELSA', rail_cap(xx, d), None, 'print2', g)
        S.add('VINT_M6x16_ISO7380', screw(6, 16), loc((xx + 6 * d, Y_RAIL + 14, -15), (1, 0, 0), (0, 1, 0)), 'steel', g)
        S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((xx + 6 * d, Y_RAIL - 2.3, -15), (0, 0, 1), (0, 1, 0)), 'steel', g)
    g = 'KARETKA'
    S.add('KARETKA_MGN12H', mgn_block(c), None, 'dark', g)
    S.add('PLOSHCHADKA_KARETKI_AL5', carriage_plate(c), None, 'alu2', g)
    for x in (-10, 10):
        for z in (-25, -5):
            S.add('VINT_M3x8_DIN912', screw(3, 8), loc((c + x, Y_PL0 + PL_T, z), (1, 0, 0), (0, 1, 0)), 'steel', g)
    zc = (ARM_Z0 + ARM_Z1) / 2
    S.add('PROFIL_30x30L_L97_STOYKA', profile(Y_PL0 - ARM_Y0), loc((c, ARM_Y0, zc), (1, 0, 0), (0, 1, 0)), 'alu', g)
    for sx in (1, -1):
        zz = cq.Vector(sx, 0, 0).cross(cq.Vector(0, -1, 0))
        S.add('UGOLOK_30x30_A990', Br, loc((c + 15 * sx, Y_PL0, zc), (sx, 0, 0), (zz.x, zz.y, zz.z)), 'zinc', g)
        S.add('VINT_M6x16_ISO7380', screw(6, 16), loc((c + 31 * sx, Y_PL0 + PL_T, zc), (1, 0, 0), (0, 1, 0)), 'steel', g)
        S.add('GAYKA_M6', nut(6), loc((c + 31 * sx, Y_PL0 - 4.5 - 5, zc), (1, 0, 0), (0, 1, 0)), 'steel', g)
        S.add('VINT_M6x12_ISO7380', S6x12, loc((c + 15 * sx + 4.5 * sx, Y_PL0 - 16, zc), (0, 0, 1), (sx, 0, 0)), 'steel', g)
        S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((c + 15 * sx - 2.3 * sx, Y_PL0 - 16, zc), (0, 0, 1), (sx, 0, 0)), 'steel', g)
    S.add('GUBKA_VERHNYAYA', jaw_upper(c), None, 'print2', g)
    S.add('GUBKA_NIZHNYAYA_RIFL', jaw_lower(c), None, 'print', g)
    for y in (J_Y1 + 12, J_Y1 + 30):
        S.add('VINT_M6x12_ISO7380', S6x12, loc((c, y, ARM_Z1 + 6), (1, 0, 0), (0, 0, 1)), 'steel', g)
        S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((c, y, ARM_Z1 - 2.3), (0, 1, 0), (0, 0, 1)), 'steel', g)
    for x, z in JAW_HOLES:
        S.add('VINT_M4x30_DIN912', screw(4, 30), loc((c + x, J_Y1 - CB, z), (1, 0, 0), (0, 1, 0)), 'steel', g)
        S.add('GAYKA_M4', nut(4), loc((c + x, J_Y0 + 0.1, z), (1, 0, 0), (0, 1, 0)), 'steel', g)
    # ---------------- узел реверса
    g = 'UZEL_REVERSA'
    x = OBST_X
    S.add('PROFIL_30x30L_L240', P_cross, loc((x, PR, -15), (1, 0, 0), (0, 1, 0)), 'alu2', g)
    for sx in (1, -1):
        for y, d2 in ((270, (0, -1, 0)), (30, (0, 1, 0))):
            br((x + 15 * sx, y, -15), (sx, 0, 0), d2, g)
    for (y0, y1) in GU_Y:
        S.add('NAPRAVLYAYUSHCHAYA_ZASLONKI', gate_guide(x, y0, y1), None, 'print', g)
        for sx in (1, -1):
            S.add('VINT_M6x12_ISO7380', S6x12, loc((x + 21 * sx, (y0 + y1) / 2, -15), (0, 1, 0), (sx, 0, 0)), 'steel', g)
            S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((x + 12.7 * sx, (y0 + y1) / 2, -15), (0, 1, 0), (sx, 0, 0)), 'steel', g)
    S.add('ZASLONKA_AL8', gate(x, gate_ext), None, 'alu', g)
    so, rod = solenoid3(x, gate_ext)
    S.add('ELEKTROMAGNIT_JF1039B', so, None, 'dark', g)
    S.add('SHTOK_ELEKTROMAGNITA', rod, None, 'steel', g)
    S.add('DERZHATEL_ELEKTROMAGNITA', sol_holder(x), None, 'print2', g)
    for y in (SOL_Y - 24, SOL_Y + 24):
        S.add('VINT_M6x12_ISO7380', S6x12, loc((x + 19, y, -15), (0, 1, 0), (1, 0, 0)), 'steel', g)
        S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((x + 12.7, y, -15), (0, 1, 0), (1, 0, 0)), 'steel', g)
    return S
