"""Эскизы вариантов узла проверки реверса для варианта В (только для рендера)."""
import sys, cadquery as cq
sys.path.insert(0, '/home/claude/stand')
from model3 import *
from model import Stand, COL

def base(c):
    S0 = build3(c, False)
    S = Stand()
    for key, name, shp, grp, col in S0.items:
        if grp == 'UZEL_REVERSA':
            bb = shp.BoundingBox()
            keep = key in ('PROFIL_30x30L_L240', 'UGOLOK_30x30_A990') or ((bb.ymin > 238 or bb.ymax < 62) and key in ('VINT_M6x12_ISO7380', 'T_GAYKA_M6_PAZ8_C181'))
            if not keep: continue
        S.add(key, cq.Workplane().add(shp), None, col, grp)
    return S

X = OBST_X; XU = X + 30          # ось узла — сбоку от стойки
def solenoid_box(y, z1):
    return cq.Workplane('XY').box(30, 26, 39, centered=(True, True, False)).translate((XU, y, z1 - 39))

def opt1():
    """Соосный толкатель Ø12 по линии ремня, в заднюю стенку зажима."""
    c = XU - 6 - J_X
    S = base(c); g = 'REVERS_1'; yb = 196.0
    h = cq.Workplane('XY').box(30, 30, 49, centered=(True, True, False)).translate((XU, yb, -40))
    h = h.cut(cq.Workplane('XY').circle(6.2).extrude(60).translate((XU, yb, -45)))
    h = h.union(cq.Workplane('XY').box(30, 30, 4, centered=(True, True, False)).translate((XU, yb, -44)))
    S.add('KORPUS_TOLKATELYA', h.edges('|Z').fillet(2), None, 'print', g)
    S.add('TOLKATEL_D12', cq.Workplane('XY').circle(6).extrude(58).translate((XU, yb, -40)), None, 'red', g)
    S.add('ELEKTROMAGNIT', solenoid_box(yb, -44), None, 'dark', g)
    for y in (yb - 9, yb + 9):
        S.add('VINT_M6x40', cq.Workplane('YZ').circle(3).extrude(30).union(cq.Workplane('YZ').circle(5).extrude(6).translate((30, 0, 0)))
              .translate((X + 15 - 0.0, 0, 0)).translate((0, y, -15)), None, 'steel', g)
    return S, c

def opt2():
    """Откидной флажок: ось шарнира вдоль X, удар идёт вдоль оси — шарнир не проворачивает."""
    c = XU - 6 - J_X
    S = base(c); g = 'REVERS_2'; yp, zp = 222.0, 18.0
    br = cq.Workplane('XY').box(30, 26, 66, centered=(True, False, False)).translate((XU, 215, -40))
    br = br.cut(cq.Workplane('XY').box(12.6, 30, 40, centered=(True, False, False)).translate((XU, 212, -14)))
    br = br.cut(cq.Workplane('XY').box(6, 30, 40, centered=(True, False, False)).translate((XU, 225, -45)))   # канал тяги
    S.add('KRONSHTEYN_SHARNIRA', br, None, 'print', g)
    S.add('OS_SHARNIRA_D6', cq.Workplane('YZ').circle(3).extrude(32).translate((XU - 16, yp, zp)), None, 'steel', g)
    fl = cq.Workplane('XY').box(12, 44, 10, centered=(True, False, True)).translate((XU, 190, zp))
    fl = fl.cut(cq.Workplane('YZ').circle(3.1).extrude(14).translate((XU - 7, yp, zp)))
    S.add('FLAZHOK', fl.edges('|X').fillet(2), None, 'red', g)
    S.add('TYAGA', cq.Workplane('XY').circle(2).extrude(70).translate((XU, 231, -52)), None, 'steel', g)
    S.add('ELEKTROMAGNIT', solenoid_box(231, -44), None, 'dark', g)
    return S, c

def opt3():
    """Толкатель Ø12 в стойку каретки (выше ремня), удар принимает каретка MGN12H."""
    c = XU - 6 - 15
    S = base(c); g = 'REVERS_3'; yb = 228.0
    h = cq.Workplane('XY').box(30, 26, 76, centered=(True, True, False)).translate((XU, yb, -40))
    h = h.cut(cq.Workplane('XY').circle(6.2).extrude(90).translate((XU, yb, -45)))
    h = h.union(cq.Workplane('XY').box(30, 26, 4, centered=(True, True, False)).translate((XU, yb, -44)))
    S.add('KORPUS_TOLKATELYA', h.edges('|Z').fillet(2), None, 'print', g)
    S.add('TOLKATEL_D12', cq.Workplane('XY').circle(6).extrude(86).translate((XU, yb, -40)), None, 'red', g)
    S.add('ELEKTROMAGNIT', solenoid_box(yb, -44), None, 'dark', g)
    return S, c

if __name__ == '__main__':
    import itertools
    for name, f in (('r1', opt1), ('r2', opt2), ('r3', opt3)):
        S, c = f()
        its = [i for i in S.items]; bad = []
        sub = [i for i in its if i[3].startswith('REVERS') or i[3] in ('KARETKA', 'UZEL_REVERSA')]
        def ov(p, q):
            A, B = p.BoundingBox(), q.BoundingBox()
            return A.xmin < B.xmax - .05 and B.xmin < A.xmax - .05 and A.ymin < B.ymax - .05 and B.ymin < A.ymax - .05 and A.zmin < B.zmax - .05 and B.zmin < A.zmax - .05
        for a, b in itertools.combinations(sub, 2):
            if not (a[3].startswith('REVERS') or b[3].startswith('REVERS')) or not ov(a[2], b[2]): continue
            try: v = a[2].intersect(b[2]).Volume()
            except Exception: v = -1
            if abs(v) > 2 and not ('REMEN' in a[0] or 'REMEN' in b[0]) and not (a[0].startswith('VINT_M4') or b[0].startswith('VINT_M4')): bad.append((round(v, 1), a[1], b[1]))
        print(name, 'c=', c, 'clashes', bad[:8])
        S.finish().save(f'out/{name}.glb')
