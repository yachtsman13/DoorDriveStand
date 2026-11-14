import math
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
PX = {'L': 0.0, 'R': 1190.0}
PX0_R = 1200.0                # испытуемая плита: x0 = 1200 — шпильки в левых концах прорезей (макс. натяжение), рабочее 1190 (ход 1135..1200)
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
PIN_Y = (196.0 - 13.0, 196.0 + 13.0)       # «вилка» как у Упора: зазор между штырями 18 мм по центру ремня
PIN_D, STROKE = 8.0, 20.0
STEEL_T = 4.0
STOP_Y = (YC - 18.55, YC + 18.55)            # отверстия «Упора»: шаг 37,1 поперёк ремня
TOWER_H = 34.0                               # стойки упора 25 → 34 мм (ремень теперь шире перекрывается)

def csk4(L):
    """Винт М4 потай DIN 7991: плоскость головки Z=0, стержень в +Z."""
    h = cq.Solid.makeCone(4.0, 2.0, 2.0)
    return cq.Workplane('XY').add(h).union(cq.Workplane('XY').circle(2).extrude(L))

def csk5(L):
    """Винт М5 потай DIN 7991: плоскость головки Z=0, стержень в +Z."""
    h = cq.Solid.makeCone(5.0, 2.5, 2.5)
    return cq.Workplane('XY').add(h).union(cq.Workplane('XY').circle(2.5).extrude(L))

def tbolt(L):
    """Т-болт паз 8 (A252/A253/A254): Z=0 — поверхность профиля, головка-сухарь в пазу (Z<0), стержень в +Z."""
    h = cq.Workplane('XY').box(16, 11, 4, centered=(True, True, False)).translate((0, 0, -6.2)).edges('|Z').fillet(1.5)
    return h.union(cq.Workplane('XY').circle(3).extrude(L).translate((0, 0, -2.2)))

def knob(D=36.0, H=16.0, lobes=5, pocket=4.7):
    """Маховичок-звёздочка (печать PETG). Z=0 — опорный торец. Снизу шестигранное гнездо 10,2 под ключ глубиной 3,7
    под головку болта М6 DIN 933 (h=4): головка выступает на 0,3 мм, усилие затяжки идёт через металл."""
    k = cq.Workplane('XY').circle(D / 2).extrude(H)
    for i in range(lobes):
        a = 2 * math.pi * (i + 0.5) / lobes
        k = k.cut(cq.Workplane('XY').center(D / 2 * 1.08 * math.cos(a), D / 2 * 1.08 * math.sin(a)).circle(D * 0.16).extrude(H))
    k = k.edges('>Z').fillet(2.0)
    k = k.cut(cq.Workplane('XY').polygon(6, 10.2 / math.cos(math.pi / 6)).extrude(pocket))
    return k.cut(cq.Workplane('XY').circle(3.3).extrude(H))   # сквозное; гнездо под гайку DIN 934 (h=5): гайка выступает 0,3

def hexbolt(L):
    """Болт М6 DIN 933: опорная плоскость головки Z=0, головка +Z (4), стержень -Z."""
    return cq.Workplane('XY').circle(3).extrude(-L).union(cq.Workplane('XY').polygon(6, 10 / math.cos(math.pi / 6)).extrude(4))

def bar_paz8(L, holes):
    """Резьбовая планка в паз 8 (полоса 12x4, сталь), отв. М6. Z=0 — верх планки (под губками), X вдоль."""
    b = cq.Workplane('XY').box(L, 12, 4, centered=(False, True, False)).translate((0, 0, -4)).edges('|Z').fillet(1)
    for x in holes:
        b = b.cut(cq.Workplane('XY').center(x, 0).circle(2.5).extrude(-4))
    return b

def coil(L, D=16.0, d=2.5, n=None):
    """Пружина сжатия — настоящая спираль (для рендера). Ось Z, 0..L."""
    n = n or max(3, int(L / (d * 1.6)))
    pitch = (L - d) / n
    h = cq.Wire.makeHelix(pitch, L - d, D / 2 - d / 2)
    prof = cq.Workplane('XZ').center(D / 2 - d / 2, 0).circle(d / 2)
    sp = prof.sweep(cq.Workplane().add(h), isFrenet=True)
    return sp.translate((0, 0, d / 2))

SX = (47.5, 252.5)        # оси прорезей: центры наружных концов 15 мм от краёв плиты
BRAKE_SLOT = False        # True — тормозная плита в варианте с прорезями
SLOT_L = 71.5              # прорезь 6,5x71,5: ход плиты 65 мм = x 35 (натяжение) + y 30 (монтаж), Optibelt Lb 2500..3000

def plate5(slotted=True):
    """slotted=True — плита испытуемого привода (и запасной вариант тормозной): 4 прорези 6,5x71,5, центры концов 15 мм от краёв,
    М5 потай под уголок упора зажима у левого края. slotted=False — плита тормозного двигателя: 4 отв. 6,5 в 15 мм от краёв."""
    p = cq.Workplane('XY').box(PLATE, PLATE, PLATE_T, centered=False)
    for y in (HOLE_EDGE, PLATE - HOLE_EDGE):
        if slotted:
            for x in SX:
                p = p.cut(cq.Workplane('XY').center(x, y).slot2D(SLOT_L, 6.5).extrude(PLATE_T))
        else:
            for x in (HOLE_EDGE, PLATE - HOLE_EDGE):
                p = p.cut(cq.Workplane('XY').center(x, y).circle(3.25).extrude(PLATE_T))
    ex = [(x, y) for x in (85, 215) for y in STOP_Y]
    p = p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints(ex).hole(6.5)
    p = p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints([(150, 150)]).hole(30)
    for (gx, gy), d in GX_POS.items():
        p = p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints([(gx, gy)]).hole(d + 0.3)
    if slotted:
        p = p.cut(cq.Workplane('XY').center(16, Y_ZH).circle(2.75).extrude(PLATE_T))      # М5 потай под уголок упора зажима
        p = p.cut(cq.Workplane('XY').add(cq.Solid.makeCone(5.2, 2.75, 2.45, cq.Vector(16, Y_ZH, 0))))
    return p

Y_ZH = 139.0      # ось толкающего зажима: полоса между нижней ветвью ремня (<=109) и кареткой (>=168)
ZH_OPEN = False

def diy_clamp(open_=False):
    """Самодельный толкающий рычажный зажим: щёки/рычаг/тяги — алюминий 3 мм, направляющая и ручка — PETG.
    Локально: Z=0 — верх переходной пластины, ось штока Z=15, наконечник в -X. Возвращает [(имя, тело, цвет)]."""
    ZA, XA, R, LK = 15.0, 115.0, 25.0, 50.0
    a0 = math.radians(183.0)                                 # закрыт: кривошип за мёртвой точкой на 3°
    ab = math.radians(63.0) if open_ else a0                 # открыт: рычаг повёрнут на 120°
    B = (XA + R * math.cos(ab), ZA + R * math.sin(ab))
    C = B[0] - math.sqrt(LK ** 2 - (B[1] - ZA) ** 2)
    C0 = XA + R * math.cos(a0) - math.sqrt(LK ** 2 - (R * math.sin(a0)) ** 2)
    sh = C - C0
    XZ = lambda: cq.Workplane('XZ')
    def plate(w, y0, t=3.0):                                  # эскиз в XZ -> пластина y0..y0+t
        return w.extrude(t).translate((0, y0 + t, 0))
    def bar(p, q, w):
        an = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0])); L = math.hypot(q[0] - p[0], q[1] - p[1])
        m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        return XZ().center(*m).rect(L, w).extrude(3).rotate((m[0], 0, m[1]), (m[0], 1, m[1]), -an)
    holes = lambda w, pts: [w := w.cut(XZ().center(*c).circle(3.05).extrude(40, both=True)) for c in pts][-1]
    out = []
    for sg in (1, -1):                                        # щёки — плоские (резка), к основанию через уголок 15x15x2
        ch = plate(XZ().polyline([(0, 0), (127, 0), (127, 22), (119, 30), (0, 30)]).close(), 19 if sg > 0 else -22)
        ch = holes(ch, [(XA, ZA)])
        for x in (30, 60):
            ch = ch.cut(cq.Workplane('XZ').center(x, 9).circle(2.2).extrude(40, both=True))
            ch = ch.cut(cq.Workplane('XY').add(cq.Solid.makeCone(4.2, 2.2, 2.0, cq.Vector(x, 19 * sg, 9), cq.Vector(0, sg, 0))))
        for x, z in ((5, 8), (13, 20)):                       # винты М4 направляющей
            ch = ch.cut(cq.Workplane('XZ').center(x, z).circle(2.2).extrude(40, both=True))
        out.append(('SHCHEKA_ZAZHIMA_AL3', ch, 'alu'))
        an = (cq.Workplane('YZ').polyline([(0, 0), (15 * sg, 0), (15 * sg, 2), (2 * sg, 2), (2 * sg, 15), (0, 15)]).close().extrude(90))
        an = an.translate((0, 22 * sg, 0))
        for x in (30, 60):
            an = an.cut(cq.Workplane('XZ').center(x, 9).circle(2.2).extrude(40, both=True))
        for x in (8, 48, 84):
            an = an.cut(cq.Workplane('XY').center(x, 30 * sg).circle(2.2).extrude(3))
        out.append(('UGOLOK_AL_15x15x2_L90', an, 'alu'))
        for x in (30, 60):
            out.append(('VINT_M4x10_DIN7991_shcheka', XZ().center(x, 9).circle(2).extrude(9).translate((0, 19 * sg + (9 if sg > 0 else 0) - (0 if sg > 0 else 0), 0)) if False else
                        cq.Workplane('XZ').center(x, 9).circle(2).extrude(10).translate((0, (29 if sg > 0 else -19), 0)), 'steel'))
            out.append(('GAYKA_M4_ugolok', XZ().center(x, 9).polygon(6, 7 / math.cos(math.pi / 6)).circle(2).extrude(3.2).translate((0, (27.2 if sg > 0 else -24), 0)), 'steel'))
        for x in (8, 48, 84):
            out.append(('GAYKA_M4_ugolok', cq.Workplane('XY').polygon(6, 7 / math.cos(math.pi / 6)).circle(2).extrude(3.2).translate((x, 30 * sg, 2)), 'steel'))
    gd = cq.Workplane('XY').box(18, 38, 29.5, centered=(False, True, False))          # направляющая (PETG), на неё ложится рычаг
    gd = gd.cut(cq.Workplane('YZ').center(0, ZA).circle(4.1).extrude(18))
    out.append(('NAPRAVLYAYUSHCHAYA_SHTOKA_PETG', gd, 'print'))
    hd = math.degrees(ab) - 15.0                                                   # рукоять на 15° от линии AB
    hr = math.radians(hd); H = (XA + 160 * math.cos(hr), ZA + 160 * math.sin(hr))
    lev = XZ().center(XA, ZA).circle(9).extrude(3).union(XZ().center(*B).circle(8).extrude(3))
    lev = lev.union(bar((XA, ZA), B, 16)).union(bar((XA, ZA), H, 12))
    lev = holes(lev, [(XA, ZA), B])
    for sg in (1, -1):
        out.append(('RYCHAG_ZAZHIMA_AL3', lev.translate((0, 13 if sg > 0 else -10, 0)), 'alu'))
    # эргономичная ручка (PETG): воротник, 3 пальцевых ложемента, грибок на конце; паз 6,2 под пластины рычага
    prof = [(0, 0), (0, 14), (2, 15.5), (6, 15), (11, 16.5), (16, 15), (21, 16.5), (26, 15), (31, 16.5), (37, 16), (43, 17.5), (48, 17), (51.5, 13), (53, 0)]
    gp = cq.Workplane('XY').spline(prof[1:-1], includeCurrent=False).lineTo(53, 0).lineTo(0, 0).lineTo(0, 14).close().revolve(360, (0, 0, 0), (1, 0, 0))
    for yc in (11.6, -11.6):                                                          # 2 паза под пластины рычага 3 мм
        gp = gp.cut(cq.Workplane('XY').box(42, 3.2, 12.4, centered=(False, True, True)).translate((0, yc, 0)))
    gp = gp.rotate((0, 0, 0), (0, 1, 0), -hd).translate((XA + 121 * math.cos(hr), 0, ZA + 121 * math.sin(hr)))
    out.append(('RUCHKA_ZAZHIMA_PETG', gp, 'black'))
    lk = XZ().center(*B).circle(6).extrude(3).union(XZ().center(C, ZA).circle(6).extrude(3)).union(bar(B, (C, ZA), 12))
    lk = holes(lk, [B, (C, ZA)])
    for sg in (1, -1):
        out.append(('TYAGA_ZAZHIMA_AL3', lk.translate((0, 10 if sg > 0 else -7, 0)), 'alu'))
    def pin(x, z, yh):
        p = XZ().center(x, z).circle(3).extrude(yh, both=True)
        hx6 = XZ().center(x, z).polygon(6, 10 / math.cos(math.pi / 6)).extrude(4)
        return p.union(hx6.translate((0, yh + 4, 0))).union(hx6.translate((0, -yh, 0)))
    out.append(('OS_M6_A', pin(XA, ZA, 22), 'steel'))
    for sg in (1, -1):
        out.append(('VTULKA_D10x6', XZ().center(XA, ZA).circle(5).circle(3).extrude(6).translate((0, 19 if sg > 0 else -13, 0)), 'zinc'))
    out.append(('OS_M6_B', pin(B[0], B[1], 13), 'steel'))
    out.append(('OS_M6_C', pin(C, ZA, 10), 'steel'))
    hx = lambda x0, L, af: cq.Workplane('YZ').center(0, ZA).polygon(6, af / math.cos(math.pi / 6)).extrude(L).translate((x0, 0, 0))
    out.append(('GAYKA_SOEDINITELNAYA_M8x24', holes(hx(C - 18, 24, 13), [(C, ZA)]), 'steel'))
    # подпружиненный наконечник: шпилька М8 -> 2 гайки (регулировка) -> шайба -> пружина + втулка-ограничитель -> скользящий наконечник с конусом
    SP_W, SP_FREE_STOP, TR = 10.0, 15.0, 5.0                 # пружина: рабочая длина 10, на упоре 15 (ход наконечника 5)
    spl = SP_FREE_STOP if open_ else SP_W
    ax = lambda w, x0: w.translate((x0, 0, 0))
    out.append(('SHPILKA_M8_shtok', ax(cq.Workplane('YZ').center(0, ZA).circle(4).extrude(C - 18 + 82 - sh), -82 + sh), 'steel'))
    out.append(('GAYKA_M8_reg', hx(-49.5 + sh, 6.5, 13), 'steel'))
    out.append(('GAYKA_M8_reg', hx(-56 + sh, 6.5, 13), 'steel'))
    out.append(('SHAYBA_M8', ax(cq.Workplane('YZ').center(0, ZA).circle(8).circle(4.2).extrude(1.0), -57 + sh), 'steel'))
    sp = coil(spl, D=16.0, d=2.2).rotate((0, 0, 0), (0, 1, 0), 90)
    out.append(('PRUZHINA_16x2.2x18', sp.translate((-57 + sh - spl, 0, ZA)), 'steel'))
    out.append(('VTULKA_OGRANICHITEL_11x8.4x9', ax(cq.Workplane('YZ').center(0, ZA).circle(5.5).circle(4.2).extrude(9), -66 + sh), 'zinc'))
    x1 = -57 + sh - spl                                       # задний торец наконечника
    tip = cq.Workplane('YZ').center(0, ZA).circle(7).extrude(17).translate((x1 - 17, 0, 0))
    tip = tip.union(cq.Workplane('XY').add(cq.Solid.makeCone(5, 1.2, 8, cq.Vector(x1 - 17, 0, ZA), cq.Vector(-1, 0, 0))))
    tip = tip.cut(cq.Workplane('YZ').center(0, ZA).circle(4.1).extrude(15).translate((x1 - 15, 0, 0)))
    out.append(('NAKONECHNIK_PODPRUZH_D14', tip, 'steel'))
    out.append(('VINT_STOPORNYY_M4', cq.Workplane('XY').center(x1 - 6, 0).circle(2).extrude(4).translate((0, 0, ZA + 5)), 'black'))
    return out

def toggle_clamp(open_=False):
    """Толкающий рычажный зажим GH-304-CM (условно, габариты уточнить по каталогу). Шток вдоль -X.
    Z=0 — опорная плоскость основания, ось штока Z=15, торец направляющей X=0, корпус в +X."""
    za = 15.0
    w = cq.Workplane('XY').box(70, 40, 4, centered=(False, True, False))
    for x in (8, 62):
        for y in (-14, 14):
            w = w.cut(cq.Workplane('XY').center(x, y).circle(2.75).extrude(4))
    w = w.union(cq.Workplane('YZ').center(0, za).circle(9).extrude(60))                    # направляющая
    w = w.union(cq.Workplane('XY').box(60, 18, za, centered=(False, True, False)).translate((0, 0, 4)))
    for y in (-8, 8):                                                                     # щёки шарнира
        w = w.union(cq.Workplane('XZ').polyline([(45, 4), (75, 4), (75, 34), (55, 34)]).close().extrude(2.5).translate((0, y + 1.25, 0)))
    st = 32.0 if open_ else 0.0
    rod = cq.Workplane('YZ').center(0, za).circle(6).extrude(-15).translate((st, 0, 0))   # шток Ø12
    rod = rod.union(cq.Workplane('YZ').center(0, za).circle(5).extrude(-31).translate((st, 0, 0)))  # винт М10
    rod = rod.union(cq.Workplane('YZ').center(0, za).polygon(6, 17 / math.cos(math.pi / 6)).extrude(-8).translate((st - 15.5, 0, 0)))  # гайки М10
    rod = rod.union(cq.Workplane('XY').add(cq.Solid.makeCone(3.0, 1.2, 5, cq.Vector(st - 31, 0, za), cq.Vector(-1, 0, 0))))  # конический наконечник в отв. уголка
    a = math.radians(100 if open_ else 12)
    piv = cq.Vector(70, 0, 30)
    hd = cq.Workplane('XY').box(110, 12, 8, centered=(False, True, True))
    hd = hd.union(cq.Workplane('YZ').circle(9).extrude(45).translate((80, 0, 0)))
    hd = hd.rotate((0, 0, 0), (0, 1, 0), -math.degrees(a)).translate(piv)
    return w, rod, hd


GX_POS = {(105.0, 55.0): 16, (195.0, 55.0): 12}   # GX16-4 — питание двигателя, GX12-6 — энкодер

def gx_socket(d):
    """Разъём GX панельный: Z=0 — передняя плоскость плиты (толщина 3 в -Z)."""
    af = d + 6
    w = cq.Workplane('XY').circle(d / 2).extrude(14)                                           # резьбовой корпус спереди
    w = w.union(cq.Workplane('XY').polygon(6, af / math.cos(math.pi / 6)).circle(d / 2).extrude(3))  # гайка спереди
    w = w.union(cq.Workplane('XY').circle(d / 2 + 2.5).extrude(-2).translate((0, 0, -3)))        # бурт сзади
    w = w.union(cq.Workplane('XY').circle(d / 2 - 1).extrude(-16).translate((0, 0, -5)))          # хвостовик с лепестками
    return w

def gx_plug(d):
    p = cq.Workplane('XY').circle(d / 2 + 1.8).extrude(38).translate((0, 0, 8))
    return p.union(cq.Workplane('XY').circle(3).extrude(40).translate((0, 0, 46)))

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
    for x in (15, XM, 1485):                      # уголки «стойка — поперечина» во всех узлах торцевых и средней рамок
        for zp, dz_ in ((-30, -1), (-270, 1)):
            for y, dy in ((270, -1), (30, 1)):
                br((x, y, zp), (0, dy, 0), (0, 0, dz_))
    for x in (70, 1430):
        for z in zs:
            S.add('OPORA_D25_M6x20_A918', foot(), loc((x, -12, z), (1, 0, 0), (0, 1, 0)), 'black')
    Lv16, Lv50, W18 = lever_screw(16), lever_screw(50), washer()
    Pu = pulley2(); TB20, TB16, KN, HB12 = tbolt(20), tbolt(16), knob(), hexbolt(12)
    for side in ('L', 'R'):
        x0 = PX[side]; xc = x0 + 150; g = 'PRIVOD_' + side
        sl = (side == 'R') or BRAKE_SLOT
        S.add('PLITA_ISPYTUEMOGO_300x300x3_PROREZI' if sl else 'PLITA_TORMOZNOGO_300x300x3_OTV', plate5(sl), loc((x0, 0, 0), (1, 0, 0), (0, 0, 1)), 'alu', g)
        # шпильки из рамы: резьбовая планка в пазу + шпилька
        if side == 'L': hx = [HOLE_EDGE, PLATE - HOLE_EDGE]                 # тормозной: неподвижно, x0 = 0 (с прорезями — по наружным концам)
        else:           hx = [PX0_R + SX[0] - SLOT_L / 2 + 3.25, PX0_R + SX[1] - SLOT_L / 2 + 3.25]   # испытуемый: шпильки в левых концах прорезей при x0 = PX0_R
        bl = hx[1] - hx[0] + 20; bx0 = hx[0] - 10
        for hy in (HOLE_EDGE, PLATE - HOLE_EDGE):
            S.add(f'PLANKA_PAZ8_12x4_L{bl:.0f}', bar_paz8(bl, [10, bl - 10]), loc((bx0, hy, -2.3), (1, 0, 0), (0, 0, 1)), 'zinc', g)
            for x in hx:
                S.add('SHPILKA_M6x20', cq.Workplane('XY').circle(3).extrude(20), loc((x, hy, -8.6), (1, 0, 0), (0, 0, 1)), 'steel', g)
                S.add('SHAYBA_M6_D18', W18, loc((x, hy, PLATE_T), (1, 0, 0), (0, 0, 1)), 'steel', g)
                S.add('GAYKA_M6', nut(6), loc((x, hy, PLATE_T + 1.6), (1, 0, 0), (0, 0, 1)), 'steel', g)
                S.add('MAHOVICHOK_M6_D36', KN, loc((x, hy, PLATE_T + 1.9), (1, 0, 0), (0, 0, 1)), 'print', g)
        mot = cq.Workplane('XY').circle(55).extrude(-160).union(cq.Workplane('XY').circle(11).extrude(BZ + 15))
        S.add('DVIGATEL_USLOVNO', mot, loc((xc, Y_AX, 0), (1, 0, 0), (0, 0, 1)), 'motor', g)
        S.add('SHKIV_PL5_D100', Pu, loc((xc, Y_AX, BZ), (1, 0, 0), (0, 0, 1)), 'print' if side == 'L' else 'print2', g)
        for (gx, gy), d in GX_POS.items():
            S.add(f'RAZEM_GX{d}_ROZETKA', gx_socket(d), loc((x0 + gx, gy, PLATE_T), (1, 0, 0), (0, 0, 1)), 'steel', g)
            S.add(f'RAZEM_GX{d}_VILKA', gx_plug(d), loc((x0 + gx, gy, PLATE_T), (1, 0, 0), (0, 0, 1)), 'black', g)
        if sl:                                  # уголок упора зажима — у левого края плиты с прорезями
            S.add('UGOLOK_30x30_A990', bracket(), loc((x0, Y_ZH, PLATE_T), (1, 0, 0), (0, -1, 0)), 'zinc', g)
            S.add('VINT_M5x16_DIN7991', csk5(16), loc((x0 + 16, Y_ZH, 0.2), (1, 0, 0), (0, 0, 1)), 'steel', g)
            S.add('SHAYBA_M5', washer(5.3, 10, 1.0), loc((x0 + 16, Y_ZH, PLATE_T + 4.5), (1, 0, 0), (0, 0, 1)), 'steel', g)
            S.add('GAYKA_M5_DIN985', cq.Workplane('XY').polygon(6, 8 / math.cos(math.pi / 6)).circle(2.5).extrude(5), loc((x0 + 16, Y_ZH, PLATE_T + 5.5), (1, 0, 0), (0, 0, 1)), 'steel', g)
    # ---- натяжение: доп. вертикальная стойка + толкающий рычажный зажим по оси Y_ZH, упор в уголок на плите
    g = 'NATYAZHENIE'
    XR = PX['R'] - 87.5                      # торец направляющей зажима; конус садится на кромку отв. уголка у левого края испытуемой плиты
    XS = XR - 145                            # доп. стойка — за щеками зажима
    S.add('STOYKA_DOP_PROFIL_30x30L_L240', Pc, loc((XS, PR, -15), (1, 0, 0), (0, 1, 0)), 'alu2', g)
    for s_ in (1, -1):
        br((XS + 15 * s_, 270, -15), (s_, 0, 0), (0, -1, 0)); br((XS + 15 * s_, 30, -15), (s_, 0, 0), (0, 1, 0))
    LA = 151 + 20
    ad = cq.Workplane('XY').box(LA, 76, 4, centered=(False, True, False))
    for y in (-12, 12):                      # пазы вдоль X: подвижка зажима
        ad = ad.cut(cq.Workplane('XY').center(151, y).slot2D(30, 6.5).extrude(4))
    for x in (8, 48, 84):
        for y in (-30, 30):
            ad = ad.cut(cq.Workplane('XY').center(6 + x, y).circle(2.2).extrude(4))
            ad = ad.cut(cq.Workplane('XY').add(cq.Solid.makeCone(4.2, 2.2, 2.0, cq.Vector(6 + x, y, 0))))
    S.add('PLASTINA_PEREHODNAYA_ZAZHIMA_AL3', ad.rotate((0, 0, 0), (0, 0, 1), 180).translate((XR + 6, Y_ZH, 0)), None, 'zinc', g)
    for y in (Y_ZH - 12, Y_ZH + 12):
        S.add('T_BOLT_M6x16_PAZ8_A252', TB16, loc((XS, y, 0), (1, 0, 0), (0, 0, 1)), 'steel', g)
        S.add('SHAYBA_M6', washer(6.4, 12, 1.6), loc((XS, y, 4), (1, 0, 0), (0, 0, 1)), 'steel', g)
        S.add('GAYKA_M6', nut(6), loc((XS, y, 5.6), (1, 0, 0), (0, 0, 1)), 'steel', g)
    for x in (8, 48, 84):
        for y in (-30, 30):
            S.add('VINT_M4x10_DIN7991', csk4(10), loc((XR - x, Y_ZH + y, 0.1), (1, 0, 0), (0, 0, 1)), 'steel', g)
    for nm, shp, col in diy_clamp(ZH_OPEN):
        S.add(nm, shp.rotate((0, 0, 0), (0, 0, 1), 180).translate((XR, Y_ZH, 4)), None, col, g)
    S.add('REMEN_PL5', belt5(PX['L'] + 150, PX['R'] + 150), None, 'belt', 'KARETKA')
    for x in (-20, 20):
        for z in (BZ - 7.05, BZ + 7.05):
            S.add('VINT_M4x20_DIN7991', csk4(20), loc((c + x, YRT - 23 + 20, z), (1, 0, 0), (0, 1, 0)), 'steel', 'KARETKA')
            S.add('GAYKA_M4', nut(4), loc((c + x, YBK + 3.0, z), (1, 0, 0), (0, 1, 0)), 'steel', 'KARETKA')
    # ---- узел реверса
    g = 'UZEL_REVERSA'; dz = STROKE if ext else 0.0
    sp = cq.Workplane('XY').box(30, 80, STEEL_T, centered=(True, True, False))
    for y in PIN_Y:
        sp = sp.cut(cq.Workplane('XY').circle(PIN_D / 2 + 0.05).extrude(10).translate((0, y - YC, -1)))
    for y in (-34, 34):
        sp = sp.cut(cq.Workplane('XY').circle(3.3).extrude(10).translate((0, y, -1)))
    S.add('PLASTINA_STALNAYA_PEREDNYAYA', sp.translate((XM, YC, 0)), None, 'steel', g)
    S.add('PLASTINA_STALNAYA_ZADNYAYA', sp.translate((XM, YC, -PR - STEEL_T)), None, 'steel', g)
    for y in (YC - 34, YC + 34):
        S.add('VINT_M6x12_ISO7380', S6, loc((XM, y, STEEL_T), (1, 0, 0), (0, 0, 1)), 'steel', g)
        S.add('VINT_M6x12_ISO7380', S6, loc((XM, y, -PR - STEEL_T), (1, 0, 0), (0, 0, -1)), 'steel', g)
    zt = STEEL_T                               # втянутый штырь — заподлицо со стальной пластиной
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
    if '--open' in sys.argv: globals()['ZH_OPEN'] = True
    if '--brakeslot' in sys.argv: globals()['BRAKE_SLOT'] = True
    S = build5(c, ext)
    if '--check' in sys.argv:
        for b in sorted(check(S, ('KARETKA', 'UZEL_REVERSA', 'UPORY', 'PRIVOD_R', 'PRIVOD_L', 'NATYAZHENIE')), reverse=True)[:25]: print('CLASH', b)
    S.finish().save(f'out/m5_{tag}.glb'); print('saved', tag, 'c', c)
