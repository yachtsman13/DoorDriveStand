"""Стенд проверки приводов дверей — механика. Профиль 30x30 (паз 8).
Система координат: X — вдоль стенда (0..1500), Y — вверх (0..300), Z — на оператора (рама Z=-300..0).
Все размеры в мм."""
import math
import cadquery as cq
from cadquery import Vector as V

# ------------------------------------------------------------------ параметры
L_FRAME, H_FRAME, D_FRAME = 1500, 300, 300
PR = 30                       # сечение профиля
L_LONG = L_FRAME - 2 * PR     # 1440
L_CROSS = H_FRAME - 2 * PR    # 240
X_MID = 750
PLATE = 300; PLATE_T = 3
PLATE_X0 = {'L': 40, 'R': 1160}          # левый край плиты (номинал)
HOLE_EDGE = 15                            # отверстия Ø8 от края плиты (шаг 270)
LUG_EDGE = 16                             # отверстие Ø6,5 под ушко от края
ROD_Z = PLATE_T + 16                      # ось тяги натяжителя: 19 от грани рамы
ANCH_Z = 3.2                              # якорь стоит на двух шайбах 1,6
BELT_Z = 40                               # плоскость ремня от грани рамы
PULLEY_D = 90; PULLEY_W = 26
BELT_W, BELT_T = 9.4, 4.5                 # ремень PL, 2 ручья (по зажиму: шаг рёбер 4,7)
Y_AX = 150                                # ось валов
Y_BELT_TOP = Y_AX + PULLEY_D / 2 + BELT_T  # 199.5 — спинка верхней ветви
CAR_X = 640                               # положение каретки на модели
STOP_X = (372, 1128)
OBST_X = 860                              # положение узла препятствия
SHOE_L, SHOE_T = 80, 14
PIN_Z = 7
# зажим ремня (посадка как у существующих деталей): 4×М4, 14,1 × 40
CL_W, CL_L, CL_DZ, CL_DX = 24.26, 60, 14.1, 40

def loc(origin, xdir, zdir):
    return cq.Location(cq.Plane(origin=V(*origin), xDir=V(*xdir), normal=V(*zdir)))

# ------------------------------------------------------------------ покупные детали (упрощённо, номинал)
def profile_section():
    s = cq.Workplane('XY').rect(PR, PR)
    slot = (cq.Workplane('XY').polyline([(-4.1, 15.1), (-4.1, 12.8), (-8.25, 12.8), (-8.25, 9.5), (-4.1, 5.8),
                                           (4.1, 5.8), (8.25, 9.5), (8.25, 12.8), (4.1, 12.8), (4.1, 15.1)]).close())
    return s, slot

def profile(L):
    """Профиль 30x30, паз 8. Ось — локальная Z, 0..L."""
    body = cq.Workplane('XY').rect(PR, PR).extrude(L).edges('|Z').fillet(1.5)
    pts = [(-4.1, 15.1), (-4.1, 12.8), (-8.25, 12.8), (-8.25, 9.5), (-4.1, 5.8), (4.1, 5.8), (8.25, 9.5), (8.25, 12.8), (4.1, 12.8), (4.1, 15.1)]
    for k in range(4):
        cut = cq.Workplane('XY').polyline(pts).close().extrude(L).rotate((0, 0, 0), (0, 0, 1), 90 * k)
        body = body.cut(cut)
    body = body.cut(cq.Workplane('XY').circle(3.4).extrude(L))
    return body

def cube():
    """3-сторонний кубический соединитель 30x30 (B943). Центр в начале координат."""
    return cq.Workplane('XY').box(PR, PR, PR).edges().chamfer(1.0)

def bracket():
    """Литой уголок 30x30 (A990), упрощённо. Внутренний угол в начале координат:
    полка 1 лежит на плоскости Y=0 вдоль +X, полка 2 — на плоскости X=0 вдоль +Y. Ширина по Z 26."""
    t, a, w = 4.5, 28, 26
    b = cq.Workplane('XY').box(a, t, w, centered=(False, False, True))
    b = b.union(cq.Workplane('XY').box(t, a, w, centered=(False, False, True)))
    rib = cq.Workplane('XY').polyline([(t, t), (a - 4, t), (t, a - 4)]).close().extrude(2.5)
    b = b.union(rib.translate((0, 0, w / 2 - 2.5))).union(rib.translate((0, 0, -w / 2)))
    b = b.cut(cq.Workplane('XZ').center(16, 0).circle(3.3).extrude(-t - 1))           # отв. в полке 1 (ось Y)
    b = b.cut(cq.Workplane('YZ').center(16, 0).circle(3.3).extrude(t + 1))             # отв. в полке 2 (ось X)
    return b

def tnut():
    """Т-гайка М6, паз 8 (C181). Локально: ось резьбы Z, верх гайки Z=0 (под губками паза)."""
    n = cq.Workplane('XY').box(15.5, 7.8, 3.0, centered=(True, True, False)).translate((0, 0, -3.0))
    n = n.union(cq.Workplane('XY').box(7.8, 7.8, 5.5, centered=(True, True, False)).translate((0, 0, -5.5)))
    return n.cut(cq.Workplane('XY').circle(3.0).extrude(-6))

def lever_screw(L):
    """Винт с рукояткой М6xL (A393..A398). Локально: опорный торец Z=0, резьба в -Z, рукоятка в +Z, рычаг вдоль +X."""
    s = cq.Workplane('XY').circle(3).extrude(-L)
    s = s.union(cq.Workplane('XY').circle(9).extrude(24))
    arm = cq.Workplane('XY').box(48, 12, 11, centered=(False, True, False)).translate((4, 0, 12)).edges('|Z').fillet(4)
    return s.union(arm)

def standoff(L=30):
    """Втулка с внутренней резьбой М6xL (C318), шестигранник S10. Ось Z, 0..L."""
    return cq.Workplane('XY').polygon(6, 10 / math.cos(math.pi / 6)).extrude(L).cut(cq.Workplane('XY').circle(3.0).extrude(L))

def sleeve(L=9):
    """Дистанционная втулка 6xL (B255): Ø10/Ø6,2."""
    return cq.Workplane('XY').circle(5).circle(3.1).extrude(L)

def washer(d=6.4, D=18, t=1.6):
    return cq.Workplane('XY').circle(D / 2).circle(d / 2).extrude(t)

def spring(L, D=16, wire=2.5):
    """Пружина сжатия (условно — трубка)."""
    return cq.Workplane('XY').circle(D / 2).circle(D / 2 - wire).extrude(L)

def foot():
    """Опора регулируемая Ø25 М6x20 (A918). Шпилька в +Z, подошва Z=-12..-4."""
    f = cq.Workplane('XY').circle(12.5).extrude(8).translate((0, 0, -16))
    f = f.union(cq.Workplane('XY').circle(3).extrude(28).translate((0, 0, -8)))
    return f.union(cq.Workplane('XY').polygon(6, 11.5).extrude(4).translate((0, 0, -8)))

def screw(d, L, head='cap'):
    """Винт: опорная плоскость головки Z=0, стержень в -Z."""
    hd, hh = {3: (5.6, 2.2), 4: (7, 4), 5: (8.5, 5), 6: (10, 6), 8: (13, 5.3)}[d]
    s = cq.Workplane('XY').circle(d / 2).extrude(-L)
    if head == 'hex':
        return s.union(cq.Workplane('XY').polygon(6, hd / math.cos(math.pi / 6)).extrude(hh))
    return s.union(cq.Workplane('XY').circle(hd / 2).extrude(hh))

def nut(d):
    s, h = {4: (7, 3.2), 5: (8, 4), 6: (10, 5)}[d]
    return cq.Workplane('XY').polygon(6, s / math.cos(math.pi / 6)).circle(d / 2).extrude(h)

# ------------------------------------------------------------------ детали изготовления
def motor_plate():
    """Плита двигателя 300x300x3 (алюминий). Начало — левый нижний задний угол; X вправо, Y вверх, Z толщина."""
    p = cq.Workplane('XY').box(PLATE, PLATE, PLATE_T, centered=False)
    pts = [(HOLE_EDGE, HOLE_EDGE), (PLATE - HOLE_EDGE, HOLE_EDGE), (HOLE_EDGE, PLATE - HOLE_EDGE), (PLATE - HOLE_EDGE, PLATE - HOLE_EDGE)]
    p = p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints(pts).hole(8)
    p = p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints([(LUG_EDGE, PLATE / 2), (PLATE - LUG_EDGE, PLATE / 2)]).hole(6.5)
    p = p.faces('>Z').workplane(origin=(0, 0, 0)).pushPoints([(PLATE / 2, PLATE / 2)]).hole(30)   # под вал — уточняется по двигателю
    return p

def shoe():
    """Ползун каретки (печать PETG). Глобальные координаты при X каретки = 0."""
    s = cq.Workplane('XY').box(SHOE_L, 26, SHOE_T, centered=(True, False, False)).translate((0, 272, 0))
    s = s.union(cq.Workplane('XY').box(60, 40, SHOE_T, centered=(True, False, False)).translate((0, 232, 0)))
    s = s.edges('|Z').fillet(2)
    s = s.union(cq.Workplane('XY').box(SHOE_L, 7.7, 2.0, centered=(True, True, False)).translate((0, 285, -2.0)))   # ребро в паз
    for x in (-25, 25):                                                                # М6 в Т-гайки, цековка под DIN 912
        s = s.cut(cq.Workplane('XY').circle(3.3).extrude(SHOE_T + 3).translate((x, 285, -2.5)))
        s = s.cut(cq.Workplane('XY').circle(5.6).extrude(7).translate((x, 285, SHOE_T - 6.5)))
    for x in (-20, 20):                                                                # М5: гайка в кармане сзади
        s = s.cut(cq.Workplane('XY').circle(2.75).extrude(SHOE_T).translate((x, 250, 0)))
        s = s.cut(cq.Workplane('XY').polygon(6, 8.2 / math.cos(math.pi / 6)).extrude(7.2).translate((x, 250, 0)))
    return s

ARM_Z0, ARM_T = SHOE_T, 8
def arm():
    """Кронштейн каретки с гладкой губкой зажима (печать PETG)."""
    yb = Y_BELT_TOP
    a = cq.Workplane('XY').box(60, 268 - yb, ARM_T, centered=(True, False, False)).translate((0, yb, ARM_Z0))
    jaw = cq.Workplane('XY').box(CL_L, 7, BELT_Z + CL_W / 2 - ARM_Z0, centered=(True, False, False)).translate((0, yb, ARM_Z0))
    a = a.union(jaw)
    for x in (-30, 27):                                                               # косынки
        g = cq.Workplane('YZ').polyline([(yb + 7, ARM_Z0 + ARM_T), (yb + 7, BELT_Z + CL_W / 2), (yb + 7 + 24, ARM_Z0 + ARM_T)]).close().extrude(3)
        a = a.union(g.translate((x, 0, 0)))
    for x in (-20, 20):                                                               # пазы 5,5 x 30 под М5 (регулировка ±12)
        sl = cq.Workplane('XY').slot2D(30, 5.5, 90).extrude(ARM_T).translate((x, 250, ARM_Z0))
        a = a.cut(sl)
    for x in (-CL_DX / 2, CL_DX / 2):
        for z in (BELT_Z - CL_DZ / 2, BELT_Z + CL_DZ / 2):
            a = a.cut(cq.Workplane('XZ').center(x, z).circle(2.25).extrude(-(yb + 8)).translate((0, 0, 0)))
    return a

RIB_H, JAW_BASE = 5.1, 6.0
def jaw_ribbed():
    """Губка рифлёная (печать PETG): рёбра шаг 4,7 — как в существующей детали «Каретка 1», добавлены гнёзда под гайки М4."""
    ytop = Y_BELT_TOP - BELT_T            # вершины рёбер упираются в подошву ремня
    y0 = ytop - RIB_H - JAW_BASE
    j = cq.Workplane('XY').box(CL_L, JAW_BASE, CL_W, centered=(True, False, True)).translate((0, y0, BELT_Z))
    for i in range(6):
        zc = BELT_Z - CL_W / 2 + 0.4 + i * 4.7
        rib = cq.Workplane('YZ').polyline([(0, -2.0), (RIB_H, -0.6), (RIB_H, 0.6), (0, 2.0)]).close().extrude(CL_L).translate((-CL_L / 2, y0 + JAW_BASE, zc))
        j = j.union(rib)
    j = j.intersect(cq.Workplane('XY').box(CL_L, 40, CL_W, centered=(True, False, True)).translate((0, y0, BELT_Z)))
    for x in (-CL_DX / 2, CL_DX / 2):
        for z in (BELT_Z - CL_DZ / 2, BELT_Z + CL_DZ / 2):
            j = j.cut(cq.Workplane('XZ').center(x, z).circle(2.25).extrude(-(ytop + 1)))
            j = j.cut(cq.Workplane('XZ').center(x, z).polygon(6, 7.2 / math.cos(math.pi / 6)).extrude(-(y0 + 3.4)).translate((0, 0, 0)).intersect(
                cq.Workplane('XY').box(20, 3.4, 20, centered=(True, False, True)).translate((x, y0, z))))
    return j, y0

def stop():
    """Упор концевой (печать PETG) в паз верхнего переднего профиля."""
    s = cq.Workplane('XY').box(30, 27, SHOE_T, centered=(True, False, False)).translate((0, 271.5, 0)).edges('|Z').fillet(2)
    s = s.union(cq.Workplane('XY').box(30, 7.7, 2.0, centered=(True, True, False)).translate((0, 285, -2.0)))
    s = s.cut(cq.Workplane('XY').circle(3.3).extrude(SHOE_T + 3).translate((0, 285, -2.5)))
    s = s.cut(cq.Workplane('XY').circle(5.6).extrude(7).translate((0, 285, SHOE_T - 6.5)))
    return s

# узел препятствия -----------------------------------------------------------
SOL = dict(L=39, W=30, H=26)      # электромагнит JF-1039B (тянущий-толкающий, ход 10) — габариты сверить!
PIN_D, PIN_L, STROKE = 8, 36, 10
Y_TOP = H_FRAME                   # верх профиля
PIN_TIP_UP = 300                  # торец штыря втянут (верх ползуна 298)
BOSS_TOP = 318
HEAD_UNDER_UP = PIN_TIP_UP + PIN_L          # 336
SHELF_Y0 = HEAD_UNDER_UP + 5.3 + 2.7        # 344: низ полки электромагнита
SHELF_T = 4
def obst_body():
    """Корпус узла препятствия (печать PETG). Глобальные координаты при X узла = 0."""
    b = cq.Workplane('XY').box(64, 10, 30 + 18, centered=(True, False, False)).translate((0, Y_TOP + 1, -30))   # основание + вылет
    b = b.union(cq.Workplane('XY').box(64, 1, 30, centered=(True, False, False)).translate((0, Y_TOP, -30)))      # опорная подошва на профиле
    b = b.union(cq.Workplane('XY').box(64, 1.8, 7.7, centered=(True, False, True)).translate((0, Y_TOP - 1.8, -15)))  # ребро в верхний паз
    b = b.union(cq.Workplane('XZ').center(0, PIN_Z).circle(10).extrude(-(BOSS_TOP - Y_TOP - 1)).translate((0, Y_TOP + 1, 0)))  # бобышка-направляющая
    top = SHELF_Y0 + SHELF_T + SOL['L'] + 2
    b = b.union(cq.Workplane('XY').box(39, top - (Y_TOP + 11), 6, centered=(True, False, False)).translate((0, Y_TOP + 11, PIN_Z - SOL['H'] / 2 - 6.5)))  # задняя стенка
    for x in (-19.5, 15.5):                                                                                       # щёки
        b = b.union(cq.Workplane('XY').box(4, top - (Y_TOP + 11), SOL['H'] + 0.5, centered=(False, False, False)).translate((x, Y_TOP + 11, PIN_Z - SOL['H'] / 2 - 0.5)))
    b = b.union(cq.Workplane('XY').box(35, SHELF_T, SOL['H'] + 0.5, centered=(True, False, False)).translate((0, SHELF_Y0, PIN_Z - SOL['H'] / 2 - 0.5)))  # полка
    b = b.cut(cq.Workplane('XZ').center(0, PIN_Z).circle(PIN_D / 2 + 0.2).extrude(-(SHELF_Y0 - Y_TOP + 2)).translate((0, Y_TOP - 2, 0)))   # канал штыря
    b = b.cut(cq.Workplane('XZ').center(0, PIN_Z).circle(3.5).extrude(-(SHELF_T + 2)).translate((0, SHELF_Y0 - 1, 0)))                  # отв. под толкатель
    for x in (-17.5, 17.5):                                                                                       # пилотные отв. Ø2,5 под саморезы хомута
        for y in (SHELF_Y0 + SHELF_T + 8, SHELF_Y0 + SHELF_T + SOL['L'] - 6):
            b = b.cut(cq.Workplane('XY').circle(1.5).extrude(-10).translate((x, y, PIN_Z + SOL['H'] / 2 + 0.2)))
    for x in (-25, 25):                                                                                           # М6 в Т-гайки верхнего паза
        b = b.cut(cq.Workplane('XZ').center(x, -15).circle(3.3).extrude(-14).translate((0, Y_TOP - 2, 0)))
    return b, top

def obst_strap(top):
    """Хомут электромагнита (печать PETG)."""
    h = SOL['L'] + 2
    s = cq.Workplane('XY').box(46, h, 4, centered=(True, False, False)).translate((0, SHELF_Y0 + SHELF_T, PIN_Z + SOL['H'] / 2 + 0.2))
    for x in (-17.5, 17.5):
        for y in (SHELF_Y0 + SHELF_T + 8, SHELF_Y0 + SHELF_T + SOL['L'] - 6):
            s = s.cut(cq.Workplane('XY').circle(1.7).extrude(5).translate((x, y, PIN_Z + SOL['H'] / 2)))
    return s

def solenoid():
    s = cq.Workplane('XY').box(SOL['W'], SOL['L'], SOL['H'], centered=(True, False, True)).translate((0, SHELF_Y0 + SHELF_T, PIN_Z))
    s = s.union(cq.Workplane('XZ').center(0, PIN_Z).circle(5).extrude(-12).translate((0, SHELF_Y0 + SHELF_T + SOL['L'], 0)))     # якорь сверху
    s = s.union(cq.Workplane('XZ').center(0, PIN_Z).circle(2).extrude(-(SHELF_T + 1.5)).translate((0, SHELF_Y0 - 1.5, 0)))  # толкатель
    return s

def pin():
    """Штырь препятствия: болт М8x60 DIN 931 с отрезанной резьбой, гладкий стержень 36. Втянут."""
    p = cq.Workplane('XZ').center(0, PIN_Z).circle(PIN_D / 2).extrude(-PIN_L).translate((0, PIN_TIP_UP, 0))
    return p.union(cq.Workplane('XZ').center(0, PIN_Z).polygon(6, 13 / math.cos(math.pi / 6)).extrude(-5.3).translate((0, HEAD_UNDER_UP, 0)))

# условные изделия -----------------------------------------------------------
def motor_dummy():
    m = cq.Workplane('XY').circle(55).extrude(-160)
    return m.union(cq.Workplane('XY').circle(7).extrude(BELT_Z + PULLEY_W / 2 + 2))

def pulley():
    return cq.Workplane('XY').circle(PULLEY_D / 2).circle(7).extrude(PULLEY_W).translate((0, 0, -PULLEY_W / 2))

def belt(x1, x2):
    r_in, r_out = PULLEY_D / 2, PULLEY_D / 2 + BELT_T
    o = cq.Workplane('XY').slot2D(x2 - x1 + 2 * r_out, 2 * r_out).extrude(BELT_W)
    i = cq.Workplane('XY').slot2D(x2 - x1 + 2 * r_in, 2 * r_in).extrude(BELT_W)
    return o.cut(i).translate(((x1 + x2) / 2, Y_AX, BELT_Z - BELT_W / 2))

# ------------------------------------------------------------------ сборка
COL = dict(alu=(0.80, 0.82, 0.85), alu2=(0.72, 0.75, 0.79), black=(0.08, 0.08, 0.09), steel=(0.62, 0.64, 0.67), zinc=(0.75, 0.77, 0.8),
           print=(0.90, 0.42, 0.07), print2=(0.15, 0.36, 0.85), dark=(0.2, 0.22, 0.25), motor=(0.33, 0.41, 0.50), belt=(0.1, 0.1, 0.1), red=(0.8, 0.1, 0.1))

class Stand:
    def __init__(self):
        self.asm = cq.Assembly(name='STEND_PRIVODOV_DVEREY')
        self.items = []          # (key, instance name, shape(global), group)
        self.shapes = {}
        self.count = {}
        self.sub = {}
    def add(self, key, shape, location=None, color='alu', group='RAMA'):
        """key — имя детали (одна модель на все экземпляры при заданном location)."""
        n = self.count.get(key, 0) + 1; self.count[key] = n
        if location is not None:
            if key not in self.shapes: self.shapes[key] = shape
            shp = self.shapes[key]
        else:
            shp = shape; location = cq.Location()
            self.shapes.setdefault(key, shape)
        if group not in self.sub:
            self.sub[group] = cq.Assembly(name=group)
        self.sub[group].add(shp, name=f'{key}__{n}', loc=location, color=cq.Color(*COL[color]))
        self.items.append((key, f'{key}__{n}', shp.val().located(location) if location else shp.val(), group, color))
    def finish(self):
        for g, a in self.sub.items():
            self.asm.add(a, name=g)
        return self.asm

def build():
    S = Stand()
    P_long, P_cross = profile(L_LONG), profile(L_CROSS)
    Cb, Br, Tn = cube(), bracket(), tnut()
    ys, zs = (15, 285), (-15, -285)
    # --- рама
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
    def br(origin, d1, d2, group='RAMA', nuts=((1, 0), (0, 1))):
        z = V(*d1).cross(V(*d2))
        S.add('UGOLOK_30x30_A990', Br, loc(origin, d1, (z.x, z.y, z.z)), 'zinc', group)
        o = V(*origin)
        for a, b in nuts:   # винт М6х12 + Т-гайка в каждой полке
            if a:
                p = o + V(*d1) * 16; n = V(*d2)
            else:
                p = o + V(*d2) * 16; n = V(*d1)
            S.add('VINT_M6x12_DIN7380', screw(6, 12), loc((p + n * 4.5).toTuple(), (z.x, z.y, z.z), n.toTuple()), 'steel', group)
            S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((p - n * 2.3).toTuple(), (z.x, z.y, z.z), n.toTuple()), 'steel', group)
    for z in zs:                                      # средняя рамка: стойки
        for sx in (1, -1):
            br((X_MID + 15 * sx, 270, z), (sx, 0, 0), (0, -1, 0))
            br((X_MID + 15 * sx, 30, z), (sx, 0, 0), (0, 1, 0))
    for y in ys:                                      # средняя рамка: поперечины
        for sx in (1, -1):
            br((X_MID + 15 * sx, y, -30), (sx, 0, 0), (0, 0, -1))
            br((X_MID + 15 * sx, y, -270), (sx, 0, 0), (0, 0, 1))
    for x, sx in ((30, 1), (1470, -1)):               # усиление торцевых рамок
        for z in zs:
            br((x, 270, z), (sx, 0, 0), (0, -1, 0))
            br((x, 30, z), (sx, 0, 0), (0, 1, 0))
    for x in (70, 1430):                              # опоры
        for z in zs:
            S.add('OPORA_D25_M6x20_A918', foot(), loc((x, -12, z), (1, 0, 0), (0, 1, 0)), 'black')
            S.add('GAYKA_M6', nut(6), loc((x, -5, z), (1, 0, 0), (0, 1, 0)), 'steel')
            S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((x, 2.3, z), (0, 0, 1), (0, -1, 0)), 'steel')
    # --- торцы: плита, двигатель (условно), натяжитель
    Pl, Lv16, Lv50, St, Sl, W18 = motor_plate(), lever_screw(16), lever_screw(50), standoff(30), sleeve(9), washer()
    for side, s in (('L', -1), ('R', 1)):
        g = 'UZEL_NATYAZHENIYA_' + side
        x0 = PLATE_X0[side]; xc = x0 + PLATE / 2
        xo = x0 + PLATE if s > 0 else x0              # наружная кромка плиты
        xe = L_FRAME if s > 0 else 0                  # торец рамы
        xa = xe + s                                   # наружная грань уголка-якоря (отверстие по оси стойки)
        S.add('PLITA_DVIGATELYA_300x300x3', Pl, loc((x0, 0, 0), (1, 0, 0), (0, 0, 1)), 'alu', g)
        for hx in (x0 + HOLE_EDGE, x0 + PLATE - HOLE_EDGE):
            for hy in (HOLE_EDGE, PLATE - HOLE_EDGE):
                S.add('SHAYBA_M6_D18', W18, loc((hx, hy, PLATE_T), (1, 0, 0), (0, 0, 1)), 'steel', g)
                S.add('VTULKA_6x5_B229', sleeve(5), loc((hx, hy, PLATE_T + 1.6), (1, 0, 0), (0, 0, 1)), 'steel', g)
                S.add('VINT_S_RUKOYATKOY_M6x16_A393', Lv16, loc((hx, hy, PLATE_T + 6.6), (1 if hy > 150 else -1, 0.4 * (1 if hy > 150 else -1), 0), (0, 0, 1)), 'black', g)
                S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((hx, hy, -2.3), (0, 1, 0), (0, 0, 1)), 'steel', g)
        # ушки на плите (оба края — плита универсальная)
        for e, d in ((x0, 1), (x0 + PLATE, -1)):
            S.add('UGOLOK_30x30_A990', Br, loc((e, Y_AX, PLATE_T), (d, 0, 0), (0, -d, 0)), 'zinc', g)   # Z_лок = d1×d2: d×(0,0,1)...
        # тяга: ушко наружной кромки -> втулка М6х30 -> уголок-якорь на стойке -> пружина -> винт с рукояткой
        S.add('VTULKA_REZB_M6x30_C318', St, loc((xo, Y_AX, ROD_Z), (0, 1, 0), (s, 0, 0)), 'steel', g)
        S.add('VINT_M6x8_DIN7380', screw(6, 8), loc((xo - 4.5 * s, Y_AX, ROD_Z), (0, 1, 0), (-s, 0, 0)), 'steel', g)
        S.add('UGOLOK_30x30_A990', Br, loc((xa, Y_AX, ANCH_Z), (-s, 0, 0), (0, s, 0)), 'zinc', g)      # якорь (на 2 шайбах = 3 мм)
        S.add('SHAYBA_M6_D18', W18, loc((xe - 15 * s, Y_AX, 0), (1, 0, 0), (0, 0, 1)), 'steel', g)
        S.add('SHAYBA_M6_D18', W18, loc((xe - 15 * s, Y_AX, 1.6), (1, 0, 0), (0, 0, 1)), 'steel', g)
        S.add('VINT_M6x16_DIN7380', screw(6, 16), loc((xe - 15 * s, Y_AX, ANCH_Z + 4.5), (1, 0, 0), (0, 0, 1)), 'steel', g)
        S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((xe - 15 * s, Y_AX, -2.3), (1, 0, 0), (0, 0, 1)), 'steel', g)
        SPR_W = 18                                     # рабочая длина пружины = 2 втулки по 9
        S.add('SHAYBA_M6_D18', W18, loc((xa, Y_AX, ROD_Z), (0, 1, 0), (s, 0, 0)), 'steel', g)
        S.add('PRUZHINA_16x2.5x25', spring(SPR_W), loc((xa + 1.6 * s, Y_AX, ROD_Z), (0, 1, 0), (s, 0, 0)), 'steel', g)
        S.add('VTULKA_6x9_B255', Sl, loc((xa + 1.6 * s, Y_AX, ROD_Z), (0, 1, 0), (s, 0, 0)), 'steel', g)
        S.add('VTULKA_6x9_B255', Sl, loc((xa + 10.6 * s, Y_AX, ROD_Z), (0, 1, 0), (s, 0, 0)), 'steel', g)
        S.add('SHAYBA_M6_D18', W18, loc((xa + (1.6 + SPR_W) * s, Y_AX, ROD_Z), (0, 1, 0), (s, 0, 0)), 'steel', g)
        S.add('VINT_S_RUKOYATKOY_M6x50_A398', Lv50, loc((xa + (3.2 + SPR_W) * s, Y_AX, ROD_Z), (0, 1, 0), (s, 0, 0)), 'black', g)
        # условно: двигатель, шкив
        S.add('DVIGATEL_USLOVNO', motor_dummy(), loc((xc, Y_AX, 0), (1, 0, 0), (0, 0, 1)), 'motor', g)
        S.add('SHKIV_D90_USLOVNO', pulley(), loc((xc, Y_AX, BELT_Z), (1, 0, 0), (0, 0, 1)), 'print', g)
    xl, xr = PLATE_X0['L'] + PLATE / 2, PLATE_X0['R'] + PLATE / 2
    S.add('REMEN_PL_USLOVNO', belt(xl, xr), None, 'belt', 'KARETKA')
    # --- каретка
    g = 'KARETKA'
    mv = lambda w: w.translate((CAR_X, 0, 0))
    S.add('POLZUN_KARETKI', mv(shoe()), None, 'print2', g)
    S.add('KRONSHTEYN_KARETKI', mv(arm()), None, 'print', g)
    jr, jy0 = jaw_ribbed()
    S.add('GUBKA_RIFLENAYA', mv(jr), None, 'print2', g)
    for x in (-25, 25):
        S.add('VINT_M6x16_DIN912', screw(6, 16), loc((CAR_X + x, 285, SHOE_T - 6.5), (1, 0, 0), (0, 0, 1)), 'steel', g)
        S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((CAR_X + x, 285, -2.6), (0, 1, 0), (0, 0, 1)), 'steel', g)
    for x in (-20, 20):
        S.add('VINT_M5x20_DIN912', screw(5, 20), loc((CAR_X + x, 250, ARM_Z0 + ARM_T + 1.0), (1, 0, 0), (0, 0, 1)), 'steel', g)
        S.add('SHAYBA_M5', washer(5.3, 10, 1.0), loc((CAR_X + x, 250, ARM_Z0 + ARM_T), (1, 0, 0), (0, 0, 1)), 'steel', g)
        S.add('GAYKA_M5', nut(5), loc((CAR_X + x, 250, 3.1), (1, 0, 0), (0, 0, 1)), 'steel', g)
    for x in (-CL_DX / 2, CL_DX / 2):
        for z in (BELT_Z - CL_DZ / 2, BELT_Z + CL_DZ / 2):
            S.add('VINT_M4x25_DIN912', screw(4, 25), loc((CAR_X + x, Y_BELT_TOP + 7, z), (1, 0, 0), (0, 1, 0)), 'steel', g)
            S.add('GAYKA_M4', nut(4), loc((CAR_X + x, jy0 + 0.1, z), (1, 0, 0), (0, 1, 0)), 'steel', g)
    for sx in STOP_X:
        S.add('UPOR_KONCEVOY', stop().translate((sx, 0, 0)), None, 'print', g)
        S.add('VINT_M6x16_DIN912', screw(6, 16), loc((sx, 285, SHOE_T - 6.5), (1, 0, 0), (0, 0, 1)), 'steel', g)
        S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((sx, 285, -2.6), (0, 1, 0), (0, 0, 1)), 'steel', g)
    # --- узел препятствия
    g = 'UZEL_PREPYATSTVIYA'
    ob, top = obst_body()
    mo = lambda w: w.translate((OBST_X, 0, 0))
    S.add('KORPUS_PREPYATSTVIYA', mo(ob), None, 'print', g)
    S.add('KHOMUT_ELEKTROMAGNITA', mo(obst_strap(top)), None, 'print2', g)
    S.add('ELEKTROMAGNIT_JF1039B', mo(solenoid()), None, 'dark', g)
    S.add('SHTYR_M8_L36', mo(pin()), None, 'steel', g)
    S.add('PRUZHINA_VOZVRATA_10x0.6x20', spring(HEAD_UNDER_UP - BOSS_TOP, 10.5, 0.6), loc((OBST_X, BOSS_TOP, PIN_Z), (1, 0, 0), (0, 1, 0)), 'steel', g)
    for x in (-25, 25):
        S.add('SHAYBA_M6', washer(6.4, 12, 1.6), loc((OBST_X + x, Y_TOP + 11, -15), (1, 0, 0), (0, 1, 0)), 'steel', g)
        S.add('VINT_M6x20_DIN912', screw(6, 20), loc((OBST_X + x, Y_TOP + 12.6, -15), (1, 0, 0), (0, 1, 0)), 'steel', g)
        S.add('T_GAYKA_M6_PAZ8_C181', Tn, loc((OBST_X + x, Y_TOP - 2.6, -15), (0, 0, 1), (0, 1, 0)), 'steel', g)
    for x in (-17.5, 17.5):
        for y in (SHELF_Y0 + SHELF_T + 8, SHELF_Y0 + SHELF_T + SOL['L'] - 6):
            S.add('SAMOREZ_3x12', screw(3, 12), loc((OBST_X + x, y, PIN_Z + SOL['H'] / 2 + 4.2), (1, 0, 0), (0, 0, 1)), 'steel', g)
    return S

if __name__ == '__main__':
    S = build()
    print(sorted(S.count.items()))
