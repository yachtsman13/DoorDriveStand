"""Мини-библиотека чертежей: HLR-проекции OCC -> matplotlib, размеры задаются 3D-точками модели."""
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import cadquery as cq
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepLib import BRepLib
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GeomAbs import GeomAbs_Line
from OCP.BRep import BRep_Builder
from OCP.TopoDS import TopoDS_Compound

plt.rcParams['font.family'] = 'DejaVu Sans'
W, H = 420, 297
VIEWS = {'front': ((0, 0, 1), (1, 0, 0)), 'top': ((0, 1, 0), (1, 0, 0)), 'right': ((1, 0, 0), (0, 0, -1)),
         'left': ((-1, 0, 0), (0, 0, 1)), 'bottom': ((0, -1, 0), (1, 0, 0)), 'back': ((0, 0, -1), (-1, 0, 0)),
         'iso': ((1, 0.8, 1.2), (1, 0, -0.85))}

def compound(shapes):
    b = BRep_Builder(); c = TopoDS_Compound(); b.MakeCompound(c)
    for s in shapes:
        b.Add(c, s.wrapped if hasattr(s, 'wrapped') else (s if isinstance(s, TopoDS_Compound) else s.val().wrapped))
    return c

def _edges(comp):
    out = []
    if comp is None or comp.IsNull(): return out
    BRepLib.BuildCurves3d_s(comp)
    ex = TopExp_Explorer(comp, TopAbs_EDGE)
    while ex.More():
        e = TopoDS.Edge_s(ex.Current()); ex.Next()
        try:
            c = BRepAdaptor_Curve(e)
        except Exception:
            continue
        a, b = c.FirstParameter(), c.LastParameter()
        n = 2 if c.GetType() == GeomAbs_Line else 28
        pts = [c.Value(a + (b - a) * i / (n - 1)) for i in range(n)]
        out.append(np.array([(p.X(), p.Y()) for p in pts]))
    return out

def hlr(shape, n, x, hidden=True):
    w = shape if isinstance(shape, TopoDS_Compound) else (shape.wrapped if hasattr(shape, 'wrapped') else shape.val().wrapped)
    nv = np.array(n, float); nv /= np.linalg.norm(nv)
    xv = np.array(x, float); xv -= nv * xv.dot(nv); xv /= np.linalg.norm(xv)
    algo = HLRBRep_Algo(); algo.Add(w)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*nv), gp_Dir(*xv))))
    algo.Update(); algo.Hide()
    hs = HLRBRep_HLRToShape(algo)
    vis = []
    for f in (hs.VCompound, hs.OutLineVCompound, hs.Rg1LineVCompound):
        try: vis += _edges(f())
        except Exception: pass
    hid = []
    if hidden:
        for f in (hs.HCompound, hs.OutLineHCompound):
            try: hid += _edges(f())
            except Exception: pass
    return vis, hid, xv, np.cross(nv, xv)

class View:
    def __init__(self, sheet, shape, view, at, scale, hidden=True, lw=0.45, clip=None):
        n, x = VIEWS[view] if isinstance(view, str) else view
        vis, hid, self.xv, self.yv = hlr(shape, n, x, hidden)
        allp = np.vstack(vis) if vis else np.zeros((1, 2))
        self.mn = allp.min(axis=0); self.mx = allp.max(axis=0)
        self.s = scale; self.at = np.array(at, float); self.sheet = sheet
        self.w, self.h = (self.mx - self.mn) * scale
        ax = sheet.ax
        if clip is not None:
            q = np.array([[np.array(p, float).dot(self.xv), np.array(p, float).dot(self.yv)] for p in clip])
            self.mn = q.min(axis=0); self.mx = q.max(axis=0); self.w, self.h = (self.mx - self.mn) * scale
            self._clip = (self.at[0], self.at[1], self.at[0] + self.w, self.at[1] + self.h)
        else:
            self._clip = None
        from matplotlib.patches import Rectangle
        rect = Rectangle((self._clip[0], self._clip[1]), self._clip[2] - self._clip[0], self._clip[3] - self._clip[1], transform=ax.transData) if self._clip else None
        for e in hid:
            p = self._m(e); l, = ax.plot(p[:, 0], p[:, 1], color='#8a8a8a', lw=0.22, ls=(0, (3, 2)), solid_capstyle='butt', zorder=2)
            if rect is not None: l.set_clip_path(rect)
        for e in vis:
            p = self._m(e); l, = ax.plot(p[:, 0], p[:, 1], color='k', lw=lw, solid_capstyle='round', zorder=3)
            if rect is not None: l.set_clip_path(rect)

    def _m(self, p2):
        return (np.asarray(p2) - self.mn) * self.s + self.at
    def T(self, p):
        p = np.array(p, float)
        return self._m(np.array([p.dot(self.xv), p.dot(self.yv)]))
    # --- размеры
    def dim(self, p1, p2, off, axis='x', text=None, pre='', suf='', fs=6.5):
        """axis 'x' — горизонтальный размер, off — положение размерной линии (мм листа) от крайней точки: >0 вверх/вправо."""
        a, b = self.T(p1), self.T(p2)
        ax = self.sheet.ax; c = '#0b3d91'
        i = 0 if axis == 'x' else 1; j = 1 - i
        val = abs(b[i] - a[i]) / self.s
        if text is None:
            text = pre + (f'{val:.2f}'.rstrip('0').rstrip('.') if abs(val - round(val, 1)) > 1e-3 else f'{round(val, 1):g}').replace('.', ',') + suf
        lvl = (max(a[j], b[j]) + off) if off > 0 else (min(a[j], b[j]) + off)
        for p in (a, b):
            q0 = p.copy(); q1 = p.copy(); q0[j] += 1.0 * np.sign(lvl - p[j]) if abs(lvl - p[j]) > 1 else 0; q1[j] = lvl + 1.2 * np.sign(off)
            ax.plot([q0[0], q1[0]], [q0[1], q1[1]], color=c, lw=0.18, zorder=4)
        A = a.copy(); B = b.copy(); A[j] = lvl; B[j] = lvl
        small = abs(B[i] - A[i]) < 7
        if small:
            d = np.sign(B[i] - A[i]) or 1
            for P, sg in ((A, -1), (B, 1)):
                Q = P.copy(); Q[i] += sg * d * 4
                ax.annotate('', xy=P, xytext=Q, arrowprops=dict(arrowstyle='-|>,head_length=0.35,head_width=0.12', color=c, lw=0.25, shrinkA=0, shrinkB=0), zorder=4)
            ax.plot([A[0], B[0]], [A[1], B[1]], color=c, lw=0.18, zorder=4)
        else:
            ax.annotate('', xy=A, xytext=B, arrowprops=dict(arrowstyle='<|-|>,head_length=0.35,head_width=0.12', color=c, lw=0.25, shrinkA=0, shrinkB=0), zorder=4)
        m = (A + B) / 2
        if small:
            m = B.copy(); m[i] += (np.sign(B[i] - A[i]) or 1) * (4.5 + 0.55 * fs * len(text) / 2 * 0.6)
        if axis == 'x':
            ax.text(m[0], m[1] + 0.6, text, ha='center', va='bottom', fontsize=fs, color=c, zorder=5)
        else:
            ax.text(m[0] - 0.6, m[1], text, ha='right', va='center', fontsize=fs, color=c, rotation=90, rotation_mode='anchor', zorder=5) if False else \
                ax.text(m[0] - 0.7, m[1], text, ha='center', va='bottom', fontsize=fs, color=c, rotation=90, rotation_mode='anchor', zorder=5)
    def note(self, p, text, dx, dy, fs=6.5, ha=None, dot=True):
        a = self.T(p); t = a + np.array([dx, dy]); ax = self.sheet.ax; c = '#0b3d91'
        ax.plot([a[0], t[0]], [a[1], t[1]], color=c, lw=0.2, zorder=4)
        if dot: ax.plot([a[0]], [a[1]], marker='o', ms=1.2, color=c, zorder=4)
        ha = ha or ('left' if dx >= 0 else 'right')
        ax.text(t[0] + (0.8 if ha == 'left' else -0.8), t[1], text, ha=ha, va='center', fontsize=fs, color=c, zorder=5)
    def axis(self, p1, p2):
        a, b = self.T(p1), self.T(p2)
        self.sheet.ax.plot([a[0], b[0]], [a[1], b[1]], color='#c0392b', lw=0.2, ls=(0, (8, 2, 1.5, 2)), zorder=4)
    def label(self, text, dy=4, fs=7, below=False):
        y = self.at[1] - dy if below else self.at[1] + self.h + dy
        self.sheet.ax.text(self.at[0] + self.w / 2, y, text, ha='center', va='top' if below else 'bottom', fontsize=fs, style='italic')

class Sheet:
    def __init__(self, pdf, title, code, scale, material='', n=1, total=1):
        self.pdf = pdf
        self.fig = plt.figure(figsize=(W / 25.4, H / 25.4))
        ax = self.ax = self.fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off'); ax.set_aspect('equal')
        ax.plot([20, W - 5, W - 5, 20, 20], [5, 5, H - 5, H - 5, 5], color='k', lw=0.6)
        x0, y0, bw, bh = W - 5 - 185, 5, 185, 30
        ax.plot([x0, x0, x0 + bw], [y0, y0 + bh, y0 + bh], color='k', lw=0.6)
        for yy in (y0 + 10, y0 + 20): ax.plot([x0, x0 + bw], [yy, yy], color='k', lw=0.25)
        ax.plot([x0 + 120, x0 + 120], [y0, y0 + 20], color='k', lw=0.25)
        ax.text(x0 + 3, y0 + 25, title, fontsize=10, va='center', weight='bold')
        ax.text(x0 + 3, y0 + 15, code, fontsize=8, va='center')
        ax.text(x0 + 123, y0 + 15, f'Масштаб {scale}', fontsize=8, va='center')
        ax.text(x0 + 3, y0 + 5, material, fontsize=7, va='center')
        ax.text(x0 + 123, y0 + 5, f'Лист {n} / {total}', fontsize=8, va='center')
    def view(self, shape, view, at, scale, **kw):
        return View(self, shape, view, at, scale, **kw)
    def text(self, x, y, s, fs=7, **kw):
        self.ax.text(x, y, s, fontsize=fs, va=kw.pop('va', 'top'), **kw)
    def table(self, x, y, rows, widths, fs=6.5, rh=5.2, head=True):
        ax = self.ax; tw = sum(widths)
        for r, row in enumerate(rows):
            yy = y - r * rh
            ax.plot([x, x + tw], [yy, yy], color='k', lw=0.2)
            xx = x
            for c, cell in enumerate(row):
                ax.text(xx + 1.2, yy - rh / 2, str(cell), fontsize=fs, va='center', weight='bold' if (head and r == 0) else 'normal')
                xx += widths[c]
        yb = y - len(rows) * rh
        ax.plot([x, x + tw], [yb, yb], color='k', lw=0.2)
        xx = x
        for wd in widths + [0]:
            ax.plot([xx, xx], [y, yb], color='k', lw=0.2); xx += wd
    def save(self):
        self.pdf.savefig(self.fig); plt.close(self.fig)
