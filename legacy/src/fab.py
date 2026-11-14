"""Файлы изготовления: DXF плоских деталей + PDF-чертежи с таблицей отверстий, STL печатных деталей, сводка JSON."""
import json, math, os
import numpy as np
import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import model6 as M
from model import PLATE, PLATE_T, HOLE_EDGE

OUT = '/home/claude/stand/pkg/STEND_v6'
for d in ('DXF', 'STL', 'PDF', 'STEP'):
    os.makedirs(f'{OUT}/{d}', exist_ok=True)
plt.rcParams['font.family'] = 'DejaVu Sans'


def face_xy(shape, normal):
    """Берёт плоскую грань с нормалью normal, кладёт в XY, левый нижний угол в 0,0."""
    w = shape if isinstance(shape, cq.Workplane) else cq.Workplane().add(shape)
    sel = {'+Z': '>Z', '+Y': '>Y'}[normal]
    f = w.faces(sel).val()
    if normal == '+Y':
        f = f.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), -90)
    bb = f.BoundingBox()
    f = f.translate(cq.Vector(-bb.xmin, -bb.ymin, -bb.zmin))
    return f


def ad_plate():
    LA = 151 + 20
    ad = cq.Workplane('XY').box(LA, 76, 4, centered=(False, True, False))
    for y in (-12, 12):
        ad = ad.cut(cq.Workplane('XY').center(151, y).slot2D(30, 6.5).extrude(4))
    for x in (8, 48, 84):
        for y in (-30, 30):
            ad = ad.cut(cq.Workplane('XY').center(6 + x, y).circle(2.2).extrude(4))
            ad = ad.cut(cq.Workplane('XY').add(cq.Solid.makeCone(4.2, 2.2, 2.0, cq.Vector(6 + x, y, 0))))
    return ad


def steel_plate():
    sp = cq.Workplane('XY').box(30, 80, M.STEEL_T, centered=(True, True, False))
    for y in M.PIN_Y:
        sp = sp.cut(cq.Workplane('XY').circle(M.PIN_D / 2 + 0.05).extrude(10).translate((0, y - M.YC, -1)))
    for y in (-34, 34):
        sp = sp.cut(cq.Workplane('XY').circle(3.3).extrude(10).translate((0, y, -1)))
    return sp


def clamp_parts():
    d = {}
    for nm, shp, col in M.diy_clamp(False):
        d.setdefault(nm, shp)
    return d


CP = clamp_parts()
# (код, наименование, тело, нормаль листа, материал, толщина, кол-во в базовом комплекте, примечание)
FLAT = [
    ('P01', 'Плита испытуемого привода (прорези 6,5×71,5)', M.plate5(True), '+Z', 'АМг2/АД31, лист', 3, 1, 'по 1 шт. на каждый испытуемый привод; отв. под двигатель — по месту'),
    ('P02', 'Плита тормозного двигателя (4 отв.)', M.plate5(False), '+Z', 'АМг2/АД31, лист', 3, 1, 'основной вариант'),
    ('P03', 'Плита тормозного двигателя с прорезями (вариант)', M.plate5(True), '+Z', 'АМг2/АД31, лист', 3, 0, 'опция: если будет второй такой же двигатель'),
    ('Z01', 'Щека зажима', CP['SHCHEKA_ZAZHIMA_AL3'], '+Y', 'АМг2/АД31, лист', 3, 2, 'сверлить парой'),
    ('Z02', 'Рычаг зажима', CP['RYCHAG_ZAZHIMA_AL3'], '+Y', 'АМг2/АД31, лист', 3, 2, 'сверлить парой'),
    ('Z03', 'Тяга зажима', CP['TYAGA_ZAZHIMA_AL3'], '+Y', 'АМг2/АД31, лист', 3, 2, 'сверлить парой'),
    ('Z04', 'Пластина переходная зажима', ad_plate(), '+Z', 'АМг2/АД31, лист', 3, 1, 'зенковка М4 — после резки'),
    ('R01', 'Пластина стальная узла реверса', steel_plate(), '+Z', 'Ст3, лист', 4, 2, 'отв. Ø8,1 — развернуть под штыри'),
    ('R02', 'Планка резьбовая в паз 8, L290 (тормозная сторона)', M.bar_paz8(290, [10, 280]), '+Z', 'Ст3, лист', 4, 2, 'отв. Ø5 — нарезать М6'),
    ('R03', 'Планка резьбовая в паз 8, L225 (испытуемая сторона)', M.bar_paz8(225, [10, 215]), '+Z', 'Ст3, лист', 4, 2, 'отв. Ø5 — нарезать М6'),
]
DENS = {'АМг2/АД31, лист': 2.68e-6, 'Ст3, лист': 7.85e-6}   # кг/мм3


def edge_pts(e, n=40):
    if e.geomType() == 'LINE':
        return [e.startPoint(), e.endPoint()]
    return [e.positionAt(i / (n - 1)) for i in range(n)]


def analyse(f):
    wires = [f.outerWire()] + list(f.innerWires())
    per = sum(e.Length() for w in wires for e in w.Edges())
    holes = []
    for w in f.innerWires():
        bb = w.BoundingBox(); cx, cy = (bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2
        dx, dy = bb.xmax - bb.xmin, bb.ymax - bb.ymin
        kind = f'Ø{dx:.1f}' if abs(dx - dy) < 0.05 else f'паз {min(dx, dy):.1f}×{max(dx, dy):.1f}'
        holes.append((round(cx, 2), round(cy, 2), kind))
    bb = f.BoundingBox()
    return dict(perimeter=per, pierces=len(wires), area=f.Area(), w=bb.xlen, h=bb.ylen, holes=holes, wires=wires)


def draw_page(pdf, code, name, mat, t, qty, note, a, f):
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_axes([0.05, 0.3, 0.6, 0.62]); ax.set_aspect('equal'); ax.axis('off')
    for w in a['wires']:
        for e in w.Edges():
            p = np.array([(v.x, v.y) for v in edge_pts(e)])
            ax.plot(p[:, 0], p[:, 1], 'k-', lw=0.9)
    W, H = a['w'], a['h']
    off = max(W, H) * 0.06
    ax.annotate('', (0, -off), (W, -off), arrowprops=dict(arrowstyle='<->', lw=0.7))
    ax.text(W / 2, -off * 1.6, f'{W:.1f}', ha='center', va='top', fontsize=9)
    ax.annotate('', (-off, 0), (-off, H), arrowprops=dict(arrowstyle='<->', lw=0.7))
    ax.text(-off * 1.4, H / 2, f'{H:.1f}', ha='right', va='center', rotation=90, fontsize=9)
    for i, (x, y, k) in enumerate(a['holes'], 1):
        ax.text(x, y, str(i), fontsize=6, color='#c03', ha='center', va='center')
    ax.set_xlim(-off * 3, W + off); ax.set_ylim(-off * 3, H + off)
    tx = fig.add_axes([0.68, 0.08, 0.3, 0.84]); tx.axis('off')
    rows = [f'{i}. X={x:.2f}  Y={y:.2f}  {k}' for i, (x, y, k) in enumerate(a['holes'], 1)]
    tx.text(0, 1, 'Отверстия (от левого нижнего угла):\n' + '\n'.join(rows[:60]), va='top', fontsize=7, family='DejaVu Sans Mono')
    fig.text(0.05, 0.2, f'{code}  {name}', fontsize=13, weight='bold')
    fig.text(0.05, 0.155, f'Материал: {mat} {t} мм     Кол-во: {qty} шт.     Габарит {W:.1f}×{H:.1f}', fontsize=10)
    fig.text(0.05, 0.12, f'Длина реза {a["perimeter"] / 1000:.2f} м, врезок {a["pierces"]}. Неуказанные предельные отклонения ±0,1 (лазер).', fontsize=9)
    fig.text(0.05, 0.085, f'Примечание: {note}. Острые кромки притупить.', fontsize=9)
    fig.text(0.05, 0.04, 'Стенд испытания приводов дверей лифта, v6 — механика', fontsize=8, color='#555')
    pdf.savefig(fig); plt.close(fig)


summary = []
with PdfPages(f'{OUT}/PDF/Chertezhi_ploskih_detaley.pdf') as pdf:
    for code, name, shp, nrm, mat, t, qty, note in FLAT:
        f = face_xy(shp, nrm)
        a = analyse(f)
        cq.exporters.export(cq.Workplane('XY').add(f), f'{OUT}/DXF/{code}_{t}mm.dxf', 'DXF')
        draw_page(pdf, code, name, mat, t, qty, note, a, f)
        mass = a['area'] * t * DENS[mat]
        summary.append(dict(code=code, name=name, mat=mat, t=t, qty=qty, cut_m=round(a['perimeter'] / 1000, 3),
                            pierces=a['pierces'], w=round(a['w'], 1), h=round(a['h'], 1), mass_kg=round(mass, 3), note=note))

# ---- печатные детали (STL)
pr = cq.Workplane()
PRINT = [
    ('T01', 'Маховичок М6 Ø36 (под гайку DIN 934)', M.knob(), 8),
    ('T02', 'Ручка рычага зажима', CP['RUCHKA_ZAZHIMA_PETG'], 1),
    ('T03', 'Направляющая штока зажима', CP['NAPRAVLYAYUSHCHAYA_SHTOKA_PETG'], 1),
    ('T04', 'Наконечник подпружиненный (100% заполнение)', CP['NAKONECHNIK_PODPRUZH_D14'], 1),
    ('T05', 'Шкив PL5 Ø100 (посадка — под вал двигателя)', M.pulley2(), 2),
]
for code, name, shp, qty in PRINT:
    w = shp if isinstance(shp, cq.Workplane) else cq.Workplane().add(shp)
    bb = w.val().BoundingBox() if len(w.vals()) == 1 else cq.Compound.makeCompound(w.vals()).BoundingBox()
    cq.exporters.export(w, f'{OUT}/STL/{code}.stl', tolerance=0.02, angularTolerance=0.1)
    vol = sum(v.Volume() for v in w.vals())
    summary.append(dict(code=code, name=name, mat='PETG', qty=qty, vol_cm3=round(vol / 1000, 1),
                        w=round(bb.xlen, 1), h=round(bb.ylen, 1), d=round(bb.zlen, 1)))
json.dump(summary, open(f'{OUT}/summary.json', 'w'), ensure_ascii=False, indent=1)
for s in summary: print(s)
