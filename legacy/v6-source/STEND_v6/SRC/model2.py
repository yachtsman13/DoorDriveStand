"""Эскизные варианты каретки: Б — каретка на роликах 608 по отдельному рельсу-профилю; В — линейная направляющая MGN12H.
Общее: ремень PL 5 ручьёв (по шкиву пользователя), натяжение только с тормозной (правой) стороны,
концевые упоры на плитах у шкивов, препятствие бьёт в кронштейн каретки.
Координаты как в model.py: X вдоль, Y вверх, Z на оператора, рама Z −300..0."""
import math
import cadquery as cq
from model import (loc, profile, cube, bracket, tnut, lever_screw, standoff, sleeve, washer, spring, foot, screw, nut,
                   motor_dummy, Stand, PR, L_LONG, L_CROSS, X_MID, PLATE, PLATE_T, PLATE_X0, HOLE_EDGE, LUG_EDGE,
                   ROD_Z, ANCH_Z, BELT_Z, Y_AX, L_FRAME, CL_W, CL_DX, CL_DZ)

# ремень и шкив по STL пользователя: PL, 5 ручьёв, шаг 4,7; впадины Ø84, гребни Ø94, реборды Ø100, ширина 30, отв. Ø22 + шпонка 6
R_GROOVE, R_CREST, R_FLANGE, PW = 42.0, 47.0, 50.0, 30.0
BELT_W = 23.5
BELT_RI, BELT_RO = 47.2, 51.0          # условно: тело ремня над гребнями шкива / спинка (рёбра не показаны)
Y_BT = Y_AX + BELT_RO                  # 201 — спинка верхней ветви
Y_BB = Y_AX + 47.0                     # 197 — вершины рёбер губки входят в ручьи ремня
STOP_HOLES = ((85, 240), (85, 260), (215, 240), (215, 260))   # новые отв. Ø6,5 в плите под концевые упоры
ARM_Z0, ARM_Z1 = 55.0, 61.0            # вертикальная часть кронштейна (перед ремнём)
OBST_X = 860

def pulley2():
    """Шкив PL5 по STL пользователя (упрощённо): ось Z, центр в начале."""
    pts = [(11, -15), (R_FLANGE, -15), (R_FLANGE, -12.5), (R_GROOVE, -9.25)]
    z = -9.25
    for i in range(4):
        pts += [(R_CREST, z + 2.35), (R_GROOVE, z + 4.7)]; z += 4.7
    pts += [(R_FLANGE, 12.5), (R_FLANGE, 15), (11, 15)]
    prof = cq.Workplane('XZ').polyline(pts).close()
    p = prof.revolve(360, (0, 0, 0), (0, 1, 0))
    # плоскость XZ: локальная Y = мировая -Z → ось вращения вдоль Z
    p = p.cut(cq.Workplane('XY').box(6, 6, 40).translate((0, 11 + 2.5, 0)))
    return p

def belt2(x1, x2):
    o = cq.Workplane('XY').slot2D(x2 - x1 + 2 * BELT_RO, 2 * BELT_RO).extrude(BELT_W)
    i = cq.Workplane('XY').slot2D(x2 - x1 + 2 * BELT_RI, 2 * BELT_RI).extrude(BELT_W)
    return o.cut(i).translate(((x1 + x2) / 2, Y_AX, BELT_Z - BELT_W / 2))

def motor_plate2():
    p = cq.Workplane('XY').box(PLATE, PLATE, PLATE_T, centered=False)
    pts = [(HOLE_EDGE, HOLE_EDGE), (PLATE - HOLE_EDGE, HOLE_EDGE), (HOLE_EDGE, PLATE - HOLE_EDGE), (PLATE - HOLE_EDGE, PLATE - HOLE_EDGE)]
    p = p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints(pts).hole(8)
    p = p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints([(LUG_EDGE, PLATE / 2), (PLATE - LUG_EDGE, PLATE / 2)] + list(STOP_HOLES)).hole(6.5)
    return p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints([(PLATE / 2, PLATE / 2)]).hole(30)

def plate_stop(xc, face_dir):
    """Концевой упор на плите (печать PETG + резиновая накладка): бьёт в кронштейн каретки. Глобальные координаты."""
    s = cq.Workplane('XY').box(20, 44, ARM_Z1 + 5 - PLATE_T, centered=(True, True, False)).translate((xc, 250, PLATE_T))
    s = s.edges('|Z').fillet(3)
    for y in (240, 260):
        s = s.cut(cq.Workplane('XY').circle(3.3).extrude(80).translate((xc, y, 0)))
        s = s.cut(cq.Workplane('XY').circle(5.6).extrude(80).translate((xc, y, 20)))
    pad = cq.Workplane('XY').box(4, 30, 20, centered=(False, True, False)).translate((xc + 10 if face_dir > 0 else xc - 14, 250, ARM_Z0 - 6))
    return s, pad

def arm2(cx, y_top, z0=2):
    """Кронштейн каретки, алюминий 6 мм: горизонтальная полка от каретки + вертикальная пластина перед ремнём до верхней губки."""
    h = cq.Workplane('XY').box(40, 6, ARM_Z1 - z0, centered=(True, False, False)).translate((cx, y_top - 6, z0))
    v = cq.Workplane('XY').box(40, y_top - (Y_BT - 2), ARM_Z1 - ARM_Z0, centered=(True, False, False)).translate((cx, Y_BT - 2, ARM_Z0))
    return h.union(v)

def jaws(cx):
    """Зажим ремня: верхняя гладкая губка (к кронштейну) и нижняя рифлёная (рёбра в ручьи ремня), 4×М4."""
    zc = BELT_Z
    up = cq.Workplane('XY').box(60, 12, ARM_Z0 - (zc - CL_W / 2), centered=(True, False, False)).translate((cx, Y_BT, zc - CL_W / 2))
    lo = cq.Workplane('XY').box(60, 10, CL_W, centered=(True, False, True)).translate((cx, Y_BB - 5.1 - 10, zc))
    for i in range(6):
        z = zc - CL_W / 2 + 0.4 + i * 4.7
        rib = cq.Workplane('YZ').polyline([(0, -2.0), (5.1, -0.6), (5.1, 0.6), (0, 2.0)]).close().extrude(60).translate((cx - 30, Y_BB - 5.1, z))
        lo = lo.union(rib)
    lo = lo.intersect(cq.Workplane('XY').box(60, 20, CL_W, centered=(True, False, True)).translate((cx, Y_BB - 15.1, zc)))
    for x in (-CL_DX / 2, CL_DX / 2):
        for z in (zc - CL_DZ / 2, zc + CL_DZ / 2):
            c = cq.Workplane('XZ').center(cx + x, z).circle(2.25).extrude(-60).translate((0, 160, 0))
            up = up.cut(c); lo = lo.cut(c)
    return up, lo

def roller608(flange_side):
    """Подшипник 608 Ø22×7 (+ реборда Ø28×1,5 с одной стороны). Ось Z, 0..7; реборда в +Z (flange_side=+1) или −Z."""
    r = cq.Workplane('XY').circle(11).circle(4).extrude(7)
    if flange_side:
        z0 = 7 if flange_side > 0 else -1.5
        r = r.union(cq.Workplane('XY').circle(14).circle(4).extrude(1.5).translate((0, 0, z0)))
    return r

def obst2():
    """Узел препятствия на переднем пазу верхнего переднего профиля: электромагнит толкает штырь Ø8 вперёд (по Z)
    в плоскость кронштейна каретки. Глобальные координаты при X узла = 0."""
    b = cq.Workplane('XY').box(56, 34, 50, centered=(True, False, False)).translate((0, 268, 0))
    b = b.cut(cq.Workplane('XY').box(32, 28, 40, centered=(True, False, False)).translate((0, 274, 4)))      # карман под электромагнит
    b = b.cut(cq.Workplane('XY').circle(4.2).extrude(60).translate((0, 288, 0)))                             # канал штыря
    for x in (-20, 20):
        b = b.cut(cq.Workplane('XY').circle(3.3).extrude(10).translate((x, 285, 0)))
    sol = cq.Workplane('XY').box(30, 26, 39, centered=(True, False, False)).translate((0, 275, 4.5))
    pin = cq.Workplane('XY').circle(4).extrude(10).translate((0, 288, 43.5))     # втянут: торец z=53,5 (кронштейн с 55)
    lid = cq.Workplane('XY').box(56, 4, 50, centered=(True, False, False)).translate((0, 302, 0))
    return b, sol, pin, lid

def build2(var='B', car_x=520):
    S = Stand()
    P_long, P_cross = profile(L_LONG), profile(L_CROSS)
    Cb, Br, Tn = cube(), bracket(), tnut()
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
    def br(origin, d1, d2, group='RAMA'):
        z = cq.Vector(*d1).cross(cq.Vector(*d2))
        S.add('UGOLOK_30x30_A990', Br, loc(origin, d1, (z.x, z.y, z.z)), 'zinc', group)
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
    # --- плиты: левая (испытуемый привод) неподвижна, правая (тормозной) с натяжителем
    Pl, Lv16, Lv50, St, Sl, W18 = motor_plate2(), lever_screw(16), lever_screw(50), standoff(30), sleeve(9), washer()
    Pu = pulley2()
    for side, s in (('L', -1), ('R', 1)):
        g = 'PRIVOD_ISPYTUEMYY' if side == 'L' else 'PRIVOD_TORMOZNOY_NATYAZHENIE'
        x0 = PLATE_X0[side]; xc = x0 + PLATE / 2
        S.add('PLITA_DVIGATELYA_300x300x3', Pl, loc((x0, 0, 0), (1, 0, 0), (0, 0, 1)), 'alu', g)
        for hx in (x0 + HOLE_EDGE, x0 + PLATE - HOLE_EDGE):
            for hy in (HOLE_EDGE, PLATE - HOLE_EDGE):
                S.add('SHAYBA_M6_D18', W18, loc((hx, hy, PLATE_T), (1, 0, 0), (0, 0, 1)), 'steel', g)
                S.add('VTULKA_6x5_B229', sleeve(5), loc((hx, hy, PLATE_T + 1.6), (1, 0, 0), (0, 0, 1)), 'steel', g)
                S.add('VINT_S_RUKOYATKOY_M6x16_A393', Lv16, loc((hx, hy, PLATE_T + 6.6), (1 if hy > 150 else -1, 0.4 * (1 if hy > 150 else -1), 0), (0, 0, 1)), 'black', g)
        S.add('DVIGATEL_USLOVNO', motor_dummy(), loc((xc, Y_AX, 0), (1, 0, 0), (0, 0, 1)), 'motor', g)
        S.add('SHKIV_PL5_D100', Pu, loc((xc, Y_AX, BELT_Z), (1, 0, 0), (0, 0, 1)), 'print' if side == 'R' else 'print2', g)
        # концевой упор на плите, у шкива
        sx = (x0 + 215) if side == 'L' else (x0 + 85)
        st, pad = plate_stop(sx, 1 if side == 'L' else -1)
        S.add('UPOR_NA_PLITE', st, None, 'print', 'UPORY')
        S.add('NAKLADKA_REZINOVAYA', pad, None, 'black', 'UPORY')
        for y in (240, 260):
            S.add('VINT_M6x25_DIN912', screw(6, 25), loc((sx, y, 20), (1, 0, 0), (0, 0, 1)), 'steel', 'UPORY')
        if side == 'R':          # натяжитель только у тормозного двигателя
            xo, xe = x0 + PLATE, L_FRAME; xa = xe + 1
            S.add('UGOLOK_30x30_A990', Br, loc((xo, Y_AX, PLATE_T), (-1, 0, 0), (0, 1, 0)), 'zinc', g)
            S.add('VTULKA_REZB_M6x30_C318', St, loc((xo, Y_AX, ROD_Z), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('UGOLOK_30x30_A990', Br, loc((xa, Y_AX, ANCH_Z), (-1, 0, 0), (0, 1, 0)), 'zinc', g)
            S.add('SHAYBA_M6_D18', W18, loc((xe - 15, Y_AX, 0), (1, 0, 0), (0, 0, 1)), 'steel', g)
            S.add('SHAYBA_M6_D18', W18, loc((xe - 15, Y_AX, 1.6), (1, 0, 0), (0, 0, 1)), 'steel', g)
            S.add('SHAYBA_M6_D18', W18, loc((xa, Y_AX, ROD_Z), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('PRUZHINA_16x2.5x25', spring(18), loc((xa + 1.6, Y_AX, ROD_Z), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('SHAYBA_M6_D18', W18, loc((xa + 19.6, Y_AX, ROD_Z), (0, 1, 0), (1, 0, 0)), 'steel', g)
            S.add('VINT_S_RUKOYATKOY_M6x50_A398', Lv50, loc((xa + 21.2, Y_AX, ROD_Z), (0, 1, 0), (1, 0, 0)), 'black', g)
        else:                    # фиксатор положения неподвижной плиты (печать) в нижнем переднем пазу
            S.add('FIKSATOR_PLITY', cq.Workplane('XY').box(20, 20, 12, centered=(False, True, False)).translate((x0 + PLATE, 15, 0)).edges('|Z').fillet(2),
                  None, 'print', g)
    xl, xr = PLATE_X0['L'] + PLATE / 2, PLATE_X0['R'] + PLATE / 2
    S.add('REMEN_PL5_USLOVNO', belt2(xl, xr), None, 'belt', 'KARETKA')
    g = 'KARETKA'
    # --- направляющая и каретка
    if var == 'B':
        Y0 = 330                                          # низ рельса-профиля (зазор 30 под нижние ролики)
        S.add('PROFIL_30x30_L1500_RELS', profile(1500), loc((0, Y0 + 15, -15), (0, 1, 0), (1, 0, 0)), 'alu', 'NAPRAVLYAYUSHCHAYA')
        for x in (45, 400, 750, 1100, 1455):
            S.add('VTULKA_REZB_M6x30_C318', standoff(30), loc((x, 300, -15), (1, 0, 0), (0, 1, 0)), 'steel', 'NAPRAVLYAYUSHCHAYA')
            S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((x, 297.7, -15), (1, 0, 0), (0, 1, 0)), 'steel', 'NAPRAVLYAYUSHCHAYA')
            S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((x, Y0 + 2.3, -15), (1, 0, 0), (0, -1, 0)), 'steel', 'NAPRAVLYAYUSHCHAYA')
        c = car_x
        L = 110; ZF0, ZB1 = 2.0, -32.0                    # передняя щека z 2..10, задняя −40..−32
        Ytop = Y0 + 30 + 22 + 5                            # низ верхней перемычки
        body = cq.Workplane('XY').box(L, Ytop + 8 - 308, 8, centered=(True, False, False)).translate((c, 308, ZF0))
        body = body.union(cq.Workplane('XY').box(L, Ytop + 8 - 308, 8, centered=(True, False, False)).translate((c, 308, ZB1 - 8)))
        body = body.union(cq.Workplane('XY').box(L, 8, ZF0 + 8 - (ZB1 - 8), centered=(True, False, False)).translate((c, Ytop, ZB1 - 8)))
        for x in (-40, 40):
            for y in (Y0 - 11, Y0 + 30 + 11):
                body = body.cut(cq.Workplane('XY').circle(4.1).extrude(80).translate((c + x, y, -60)))
        S.add('KARETKA_KORPUS_AL', body, None, 'alu2', g)
        for x in (-40, 40):
            # верхние ролики: передний ряд (реборда к оператору), задний ряд (реборда назад)
            S.add('PODSHIPNIK_608ZZ_S_REBORDOY', roller608(1), loc((c + x, Y0 + 30 + 11, -7.0), (1, 0, 0), (0, 0, 1)), 'steel', g)
            S.add('PODSHIPNIK_608ZZ_S_REBORDOY', roller608(1), loc((c + x, Y0 + 30 + 11, -23.0), (1, 0, 0), (0, 0, -1)), 'steel', g)
            S.add('PODSHIPNIK_608ZZ_S_REBORDOY', roller608(1), loc((c + x, Y0 - 11, -7.0), (1, 0, 0), (0, 0, 1)), 'steel', g)
            S.add('PODSHIPNIK_608ZZ_S_REBORDOY', roller608(1), loc((c + x, Y0 - 11, -23.0), (1, 0, 0), (0, 0, -1)), 'steel', g)
            # оси: верхние — сквозной болт М8×55, нижние — консольные М8×20 с каждой щеки
            S.add('BOLT_M8x55', screw(8, 55, 'hex'), loc((c + x, Y0 + 41, ZF0 + 8), (1, 0, 0), (0, 0, 1)), 'steel', g)
            S.add('BOLT_M8x16', screw(8, 17, 'hex'), loc((c + x, Y0 - 11, ZF0 + 8), (1, 0, 0), (0, 0, 1)), 'steel', g)
            S.add('BOLT_M8x16', screw(8, 17, 'hex'), loc((c + x, Y0 - 11, ZB1 - 8), (1, 0, 0), (0, 0, -1)), 'steel', g)
        y_top = 318
    else:   # var C — MGN12H на верхней грани верхнего переднего профиля
        rail = cq.Workplane('XY').box(1400, 8, 12, centered=(False, False, True)).translate((50, 300, -15))
        for i in range(56):
            rail = rail.cut(cq.Workplane('XZ').center(62.5 + i * 25, -15).circle(1.75).extrude(-8).translate((0, 300, 0)))
        S.add('RELS_MGN12_L1400', rail, None, 'steel', 'NAPRAVLYAYUSHCHAYA')
        c = car_x
        blk = cq.Workplane('XY').box(45.4, 10, 27, centered=(True, False, True)).translate((c, 303, -15))
        blk = blk.cut(cq.Workplane('XY').box(46, 7, 12.6, centered=(True, False, True)).translate((c, 303, -15)))
        blk = blk.union(cq.Workplane('XY').box(4, 7, 22, centered=(True, False, True)).translate((c - 24.7, 305, -15)))
        blk = blk.union(cq.Workplane('XY').box(4, 7, 22, centered=(True, False, True)).translate((c + 24.7, 305, -15)))
        S.add('KARETKA_MGN12H', blk, None, 'dark', g)
        pl = cq.Workplane('XY').box(70, 6, 61 + 28, centered=(True, False, False)).translate((c, 313, -28))
        S.add('KARETKA_PLITA_AL', pl, None, 'alu2', g)
        for x in (-10, 10):
            for z in (-25, -5):
                S.add('VINT_M3x10_DIN912', screw(3, 10), loc((c + x, 319, z), (1, 0, 0), (0, 1, 0)), 'steel', g)
        y_top = 313
    S.add('KRONSHTEYN_KARETKI_AL', arm2(c, y_top, 10) if var == 'B' else arm2(c, y_top, 2), None, 'alu', g)
    up, lo = jaws(c)
    S.add('GUBKA_GLADKAYA', up, None, 'print2', g)
    S.add('GUBKA_RIFLENAYA_PL5', lo, None, 'print2', g)
    for x in (-CL_DX / 2, CL_DX / 2):
        for z in (BELT_Z - CL_DZ / 2, BELT_Z + CL_DZ / 2):
            S.add('VINT_M4x40_DIN912', screw(4, 40), loc((c + x, Y_BT + 12, z), (1, 0, 0), (0, 1, 0)), 'steel', g)
    # --- препятствие
    b, sol, pin, lid = [w.translate((OBST_X, 0, 0)) for w in obst2()]
    S.add('KORPUS_PREPYATSTVIYA_2', b, None, 'print', 'UZEL_PREPYATSTVIYA')
    S.add('KRYSHKA_PREPYATSTVIYA', lid, None, 'print2', 'UZEL_PREPYATSTVIYA')
    S.add('ELEKTROMAGNIT_JF1039B', sol, None, 'dark', 'UZEL_PREPYATSTVIYA')
    S.add('SHTYR_D8', pin, None, 'steel', 'UZEL_PREPYATSTVIYA')
    for x in (-20, 20):
        S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((OBST_X + x, 285, -2.3), (0, 1, 0), (0, 0, 1)), 'steel', 'UZEL_PREPYATSTVIYA')
    return S
