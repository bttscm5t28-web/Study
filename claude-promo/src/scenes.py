"""The film, scene by scene.  render(t, ctx) -> float32 frame.

  0:00  one pixel            一切，从一个像素开始。
  0:05  resolution rises     a blocky earth, 1x1 -> 32x32
  0:10  读 想 写 做 信        five capabilities, each resolving from pixels
  0:35  the ceiling          Claude 1 .. 5 stack up; Opus 5.5 breaks through
  0:45  the real world       night city -> glaciers -> Everest -> Bahamas -> Earth,
                             each world shrinking into one pixel of the next
  1:02  one pixel again      the earth folds into the pixel that types "Claude Opus 5.5"
"""
import math

import numpy as np

import assets
import timeline as T
from gfx import *  # noqa: F401,F403


# ====================================================================== context
class Ctx:
    def __init__(self):
        self.worlds = {}
        for name in assets.SOURCES:
            w = World(assets.world_path(name))
            if name == "earth":   # lift pure black space to the film's ink so the grid reads
                for n, a in w.levels.items():
                    w.levels[n] = a + INK * (1 - a)
                w.mean = w.levels[1][0, 0].copy()
                arr = np.asarray(w.img, np.float32) / 255.0
                arr = arr + INK * (1 - arr)
                w.img = Image.fromarray((arr * 255 + 0.5).astype(np.uint8))
            self.worlds[name] = w
        # act I: the clay pixel *is* the 1x1 level of the earth; it splits into the real colours
        import copy
        g = copy.copy(self.worlds["earth"])
        g.levels = dict(g.levels)
        g.levels[1] = CLAY[None, None, :].copy()
        self.genesis_earth = g
        self.montage = ["riyadh", "karakoram", "everest", "bahamas", "earth"]
        self.captions = {k: v[4] for k, v in assets.SOURCES.items()}
        self._landing = {}

    def landing(self, a, b, n):
        """Cell of world b (level n) that world a shrinks into."""
        key = (a, b, n)
        if key not in self._landing:
            if b == "earth":
                u, v = assets.EARTH_BAHAMAS
                cell = (min(n - 1, int(u * n)), min(n - 1, int(v * n)))
            else:   # the cell near the centre whose colour best matches a's average
                cols = self.worlds[b].levels[n]
                ma = self.worlds[a].mean
                lo, hi = int(n * 0.4), int(n * 0.6)
                sub = cols[lo:hi, lo:hi]
                d = np.sum((sub - ma) ** 2, axis=2)
                j, i = np.unravel_index(np.argmin(d), d.shape)
                cell = (lo + i, lo + j)
            self._landing[key] = cell
        return self._landing[key]


# ====================================================================== shared bits
def hud(frame, x, y, label, value, color_l, color_v, align="left", alpha=1.0, size=22):
    Text(label, "mono", "Regular", 13, tracking=2.5).draw(frame, x, y, color_l, align=align, alpha=alpha)
    Text(value, "mono", "Medium", size).draw(frame, x, y + 32, color_v, align=align, alpha=alpha)


def line_pair(frame, t, t0, t1, zh, en, x, y, zh_color, en_color, align="left", zh_size=44, en_size=26,
              zh_kind="serif", zh_weight="Regular", gap=48, exit_dur=0.35):
    """A Chinese line with its English counterpart, resolving in and dissolving out."""
    if t < t0 or t > t1:
        return
    ep = prog(t, t1 - exit_dur, t1)
    Text(zh, zh_kind, zh_weight, zh_size).draw(frame, x, y, zh_color, align=align,
                                               prog_fn=stagger(t, t0, 0.04, 0.5), exit_p=ep, rise=6)
    Text(en, "latin", "300Italic", en_size).draw(frame, x, y + gap, en_color, align=align,
                                                 prog_fn=stagger(t, t0 + 0.25, 0.012, 0.45), exit_p=ep)


# ====================================================================== act I: one pixel
EARTH_C = (960, 470)
EARTH_S1 = 560
PIXEL = 22


def scene_genesis(t, ctx):
    f = new_frame(INK)
    cx, cy = EARTH_C
    if T.PIXEL_APPEAR <= t < T.EXPAND:
        a = e_outback(prog(t, T.PIXEL_APPEAR, T.PIXEL_APPEAR + 0.42))
        k = math.floor((t - T.PIXEL_APPEAR) / T.BEAT)
        pulse = 0.0
        if k >= 1:
            pulse = 0.2 * math.exp(-(t - (T.PIXEL_APPEAR + k * T.BEAT)) / 0.16)
        square(f, cx, cy, PIXEL * a * (1 + pulse), CLAY)
    elif t >= T.EXPAND:
        u = e_io3(prog(t, T.EXPAND, T.EXPAND + 0.5))
        S = lerp(PIXEL, EARTH_S1, u)
        if t < T.SUBDIV[0]:
            square(f, cx, cy, S, CLAY)
        else:
            draw_world_resolving(f, ctx.genesis_earth, [1, 2, 4, 8, 16, 32], [T.EXPAND] + T.SUBDIV, 0.3, t,
                                 cx, cy, EARTH_S1, INK)

    # resolution read-out
    if t >= T.PIXEL_APPEAR + 0.3:
        k = sum(1 for s in T.SUBDIV if t >= s)
        n = 2 ** k
        al = smooth(prog(t, T.PIXEL_APPEAR + 0.3, T.PIXEL_APPEAR + 0.9))
        hud(f, 120, 990, "RESOLUTION", f"{n} × {n}", GRAY, IVORY, alpha=al * 0.9)
        hud(f, 1800, 990, "PIXELS", f"{n * n:,}", GRAY, IVORY, align="right", alpha=al * 0.9)

    line_pair(f, t, T.LINE1[0], T.LINE1[1], "一切，从一个像素开始。", "It all begins with a single pixel.",
              960, 870, IVORY, GRAY_L, align="center")
    line_pair(f, t, T.LINE2[0], T.LINE2[1], "分辨率每提升一次，世界就清晰一分。",
              "Every leap in resolution brings the world into focus.",
              960, 870, IVORY, GRAY_L, align="center")
    return f


# ====================================================================== act II: capabilities
CAPS = [
    dict(idx="01", tag="READ", ch="读", head="百万 token 上下文",
         zh="海量资料一次读完，前后贯通。",
         en="A 1M-token context window: everything in view at once."),
    dict(idx="02", tag="REASON", ch="想", head="先深思，再作答",
         zh="面对难题，层层推理，直到想清楚。",
         en="It reasons through hard problems before it answers."),
    dict(idx="03", tag="CODE", ch="写", head="68 万行代码迁移，不到一天",
         zh="一位早期测试者的实测：原本需要一个团队数周。",
         en="One early tester migrated 680,000 lines in under a day."),
    dict(idx="04", tag="ACT", ch="做", head="看懂屏幕，动手完成",
         zh="像人一样操作电脑，跨应用把任务做完。",
         en="It sees the screen, uses the computer, and gets the job done."),
    dict(idx="05", tag="TRUST", ch="信", head="更强大，也更值得信赖",
         zh="Anthropic 自动化行为审计中，迄今表现最好的模型。",
         en="The strongest performer to date on Anthropic's automated behavioral audit."),
]
LX = 150


def chapter_text(f, t, cap, t0, t_exit):
    ep = prog(t, t_exit, t_exit + 0.4)
    Text(cap["idx"], "mono", "Medium", 22).draw(f, LX, 262, CLAY, prog_fn=stagger(t, t0, 0.05, 0.3), exit_p=ep)
    Text(cap["tag"], "mono", "Regular", 22, tracking=6).draw(f, LX + 50, 262, GRAY,
                                                            prog_fn=stagger(t, t0 + 0.05, 0.04, 0.3), exit_p=ep)
    Text(cap["ch"], "serif", "SemiBold", 300).draw(f, LX - 8, 612, INK, prog_fn=lambda i, n: prog(t, t0, t0 + 0.7),
                                                   block=60, exit_p=ep)
    Text(cap["head"], "serif", "Medium", 52).draw(f, LX, 742, INK, prog_fn=stagger(t, t0 + 0.3, 0.035, 0.45),
                                                  exit_p=ep, rise=5)
    Text(cap["zh"], "sans", "Regular", 27).draw(f, LX, 806, SLATE, prog_fn=stagger(t, t0 + 0.6, 0.018, 0.4),
                                                exit_p=ep)
    Text(cap["en"], "latin", "400Italic", 25).draw(f, LX, 850, GRAY, prog_fn=stagger(t, t0 + 0.8, 0.008, 0.4),
                                                   exit_p=ep)


def exit_dissolve(f, u, bg):
    """Pixel-dissolve the whole frame toward the background."""
    if u <= 0:
        return f
    b = int(round(lerp(1, 40, e_in3(u))))
    pixelate_frame(f, b)
    f += (bg - f) * e_in3(u)
    return f


# ---------------------------------------------------------------- 读 READ
class ReadVis:
    cols, rows, pw, ph, g = 18, 12, 40, 52, 10
    x0, y0 = 884, 156

    def __init__(self):
        rs = np.random.default_rng(5)
        self.pages = []
        for r in range(self.rows):
            for c in range(self.cols):
                lines = []
                for k in range(6):
                    L = rs.uniform(0.45, 0.95) if k else rs.uniform(0.35, 0.6)
                    col = SLATE if k == 0 else GRAY_L
                    lines.append((k, L, col))
                if rs.random() < 0.14:
                    k = rs.integers(1, 6)
                    lines[k] = (k, lines[k][1], CLAY)
                self.pages.append((c, r, lines, rs.random()))
        self.buf = None

    def detail(self):
        if self.buf is None:
            wpx = self.cols * (self.pw + self.g)
            hpx = self.rows * (self.ph + self.g)
            buf = np.empty((hpx, wpx, 3), np.float32)
            buf[:] = IVORY
            tmp_frame = buf
            for c, r, lines, _ in self.pages:
                px, py = c * (self.pw + self.g), r * (self.ph + self.g)
                tmp_frame[py:py + self.ph, px:px + self.pw] = PAPER
                tmp_frame[py:py + self.ph, px:px + 1] = GRAY_3
                tmp_frame[py:py + self.ph, px + self.pw - 1:px + self.pw] = GRAY_3
                tmp_frame[py:py + 1, px:px + self.pw] = GRAY_3
                tmp_frame[py + self.ph - 1:py + self.ph, px:px + self.pw] = GRAY_3
                for k, L, col in lines:
                    yy = py + 8 + k * 7
                    tmp_frame[yy:yy + 3, px + 6:px + 6 + int((self.pw - 12) * L)] = col
            self.buf = buf
        return self.buf

    def draw(self, f, lt):
        buf = self.detail()
        beam0, beam1 = 0.9, 3.9
        span = self.cols * (self.pw + self.g)
        bx = self.x0 - 24 + (span + 48) * e_io3(prog(lt, beam0, beam1))
        for c, r, lines, rnd in self.pages:
            px, py = self.x0 + c * (self.pw + self.g), self.y0 + r * (self.ph + self.g)
            d = (c / self.cols) * 0.35 + (r / self.rows) * 0.2 + rnd * 0.15
            ap = prog(lt, 0.1 + d, 0.3 + d)
            if ap <= 0:
                continue
            cxp = px + self.pw / 2
            if bx < cxp:   # unread: a flat block
                s = e_outback(ap, 2.0)
                rect(f, cxp - self.pw / 2 * s, py + self.ph / 2 - self.ph / 2 * s,
                     cxp + self.pw / 2 * s, py + self.ph / 2 + self.ph / 2 * s, GRAY_LL)
            else:          # read: the page resolves into detail
                bt = (bx - cxp) / 260.0
                b = int(round(lerp(13, 1, e_out3(bt))))
                bx0, by0 = c * (self.pw + self.g), r * (self.ph + self.g)
                tile = buf[by0:by0 + self.ph, bx0:bx0 + self.pw]
                if b > 1:
                    tile = pixelate(tile, b)
                f[py:py + self.ph, px:px + self.pw] = tile
        if beam0 - 0.1 < lt < beam1 + 0.25:
            ba = smooth(prog(lt, beam0 - 0.1, beam0 + 0.1)) * (1 - smooth(prog(lt, beam1, beam1 + 0.25)))
            ytop, ybot = self.y0 - 22, self.y0 + self.rows * (self.ph + self.g) + 12
            for k in range(14):
                rect(f, bx - 4 - k * 6, ytop, bx - k * 6 + 2, ybot, CLAY, alpha=ba * 0.05 * (1 - k / 14))
            vline(f, bx, ytop, ybot, 3, CLAY, alpha=ba)
        # counter
        r_ = e_io3(prog(lt, beam0, beam1))
        al = smooth(prog(lt, 0.3, 0.7))
        Text(f"{int(round(1_000_000 * r_)):,}", "mono", "Medium", 34).draw(f, self.x0, 948, INK, alpha=al)
        Text("TOKENS IN CONTEXT", "mono", "Regular", 14, tracking=2.5).draw(f, self.x0 + 210, 946, GRAY, alpha=al)
        Text("1M", "mono", "Medium", 14, tracking=2).draw(f, self.x0 + 890, 946, CLAY, align="right", alpha=al)


# ---------------------------------------------------------------- 想 REASON
class ReasonVis:
    X = [912, 1080, 1248, 1416, 1584, 1752]
    NODES = {
        (0, 0): 540,
        (1, 0): 300, (1, 1): 540, (1, 2): 780,
        (2, 0): 220, (2, 1): 380, (2, 2): 500, (2, 3): 640, (2, 4): 760, (2, 5): 870,
        (3, 0): 180, (3, 1): 290, (3, 2): 420, (3, 3): 520, (3, 4): 610, (3, 5): 700, (3, 6): 820,
        (4, 0): 330, (4, 1): 470, (4, 2): 610, (4, 3): 760,
        (5, 0): 540,
    }
    PARENT = {
        (1, 0): (0, 0), (1, 1): (0, 0), (1, 2): (0, 0),
        (2, 0): (1, 0), (2, 1): (1, 0), (2, 2): (1, 1), (2, 3): (1, 1), (2, 4): (1, 2), (2, 5): (1, 2),
        (3, 0): (2, 0), (3, 1): (2, 0), (3, 2): (2, 1), (3, 3): (2, 2), (3, 4): (2, 3), (3, 5): (2, 4),
        (3, 6): (2, 5),
        (4, 0): (3, 1), (4, 1): (3, 2), (4, 2): (3, 4), (4, 3): (3, 5),
        (5, 0): (4, 1),
    }
    PATH = [(0, 0), (1, 0), (2, 1), (3, 2), (4, 1), (5, 0)]

    def layer_t(self, L):
        return 0.25 + L * 0.42

    def pos(self, k):
        return self.X[k[0]], self.NODES[k]

    def elbow(self, f, a, b, p, th, color, alpha):
        """Draw the first p (0..1) of an elbow connector a -> b."""
        (xa, ya), (xb, yb) = a, b
        xm = (xa + xb) / 2
        segs = [abs(xm - xa), abs(yb - ya), abs(xb - xm)]
        tot = sum(segs) * p
        if tot <= 0:
            return
        l1 = min(tot, segs[0])
        hline(f, xa, xa + l1, ya, th, color, alpha)
        tot -= l1
        if tot > 0:
            l2 = min(tot, segs[1])
            yy = ya + math.copysign(l2, yb - ya)
            vline(f, xm, min(ya, yy) - th / 2, max(ya, yy) + th / 2, th, color, alpha)
            tot -= l2
            if tot > 0:
                hline(f, xm, xm + min(tot, segs[2]), yb, th, color, alpha)

    def draw(self, f, lt):
        on_path = set(self.PATH)
        hi_t0, hi_t1 = 2.55, 3.3
        hp_ = prog(lt, hi_t0, hi_t1)
        for k, par in self.PARENT.items():
            L = k[0]
            if L == 5:
                continue
            t_edge = self.layer_t(L) - 0.3
            p = e_out3(prog(lt, t_edge, t_edge + 0.32))
            if p <= 0:
                continue
            pruned = k not in on_path and lt > self.layer_t(L + 1) + 0.25
            fade = smooth(prog(lt, self.layer_t(L + 1) + 0.25, self.layer_t(L + 1) + 0.6)) if not (k in on_path) else 0
            col = SLATE if not pruned else SLATE + (GRAY_LL - SLATE) * fade
            self.elbow(f, self.pos(par), self.pos(k), p, 2, col, 1.0)
        # highlighted reasoning path
        if hp_ > 0:
            segs = list(zip(self.PATH[:-1], self.PATH[1:]))
            per = 1.0 / len(segs)
            for i, (a, b) in enumerate(segs):
                q = clamp((hp_ - i * per) / per)
                if q > 0:
                    self.elbow(f, self.pos(a), self.pos(b), q, 3.2, CLAY, 1.0)
        # nodes
        for k in self.NODES:
            L = k[0]
            if L == 5:
                continue
            ap = prog(lt, self.layer_t(L) - 0.02, self.layer_t(L) + 0.2)
            if ap <= 0:
                continue
            x, y = self.pos(k)
            s = 13 * e_outback(ap, 2.2)
            col = SLATE
            if k not in on_path and lt > self.layer_t(L + 1) + 0.25:
                col = SLATE + (GRAY_LL - SLATE) * smooth(prog(lt, self.layer_t(L + 1) + 0.25, self.layer_t(L + 1) + 0.6))
            if k in on_path:
                idx = self.PATH.index(k)
                if hp_ * (len(self.PATH) - 1) >= idx - 0.01:
                    col = CLAY
                    s = 16
            square(f, x, y, s, col)
        # the answer
        ap = prog(lt, hi_t1 - 0.05, hi_t1 + 0.3)
        if ap > 0:
            x, y = self.pos((5, 0))
            pulse = 0.12 * math.exp(-max(0, lt - hi_t1 - 0.3) / 0.25) if lt > hi_t1 + 0.3 else 0
            s = 30 * e_outback(ap, 2.0) * (1 + pulse)
            square(f, x, y, s, CLAY)
            frame_rect(f, x - s / 2 - 10, y - s / 2 - 10, x + s / 2 + 10, y + s / 2 + 10, 1.5, CLAY,
                       alpha=0.6 * smooth(prog(lt, hi_t1 + 0.1, hi_t1 + 0.4)))
        al = smooth(prog(lt, 0.3, 0.7))
        dots = "." * (1 + int(lt * 4) % 3) if lt < hi_t1 else ""
        label = "THINKING" + dots if lt < hi_t1 else "ANSWER"
        Text(label, "mono", "Regular", 14, tracking=2.5).draw(f, 912, 948, CLAY if lt >= hi_t1 else GRAY, alpha=al)
        steps = int(np.interp(lt, [0.25, hi_t1], [1, 23]))
        Text(f"{steps:02d} STEPS", "mono", "Regular", 14, tracking=2.5).draw(f, 1752, 948, GRAY, align="right",
                                                                          alpha=al)


# ---------------------------------------------------------------- 写 CODE
class CodeVis:
    pitch = 20
    top, bot = 252, 846
    panels = ((884, 1306), (1370, 1792))

    def __init__(self):
        rs = np.random.default_rng(11)
        self.lines = []
        indent = 0
        for i in range(2209):
            if rs.random() < 0.18:
                indent = max(0, min(3, indent + rs.choice([-1, 1])))
            segs = []
            x = indent * 22
            for _ in range(rs.integers(1, 5)):
                L = rs.integers(18, 90)
                cls = rs.choice(5, p=[0.38, 0.2, 0.17, 0.15, 0.1])
                segs.append((x, L, cls))
                x += L + 8
                if x > 360:
                    break
            if rs.random() < 0.1:
                segs = []
            self.lines.append(segs)

    NEW_COLORS = (SLATE, CLAY, SKY, OLIVE, HEATHER)
    OLD_COLORS = (GRAY, GRAY_L, GRAY_L, GRAY, GRAY_L)

    def scroll(self, lt):
        # lines processed so far (accelerating, then easing to a stop)
        a, b = 0.6, 4.15
        u = prog(lt, a, b)
        return 2200 * e_io3(u) ** 1.35 + 8 * u

    def draw(self, f, lt):
        al = smooth(prog(lt, 0.15, 0.55))
        for (x0, x1), lab in zip(self.panels, ("LEGACY", "MIGRATED")):
            rect(f, x0, 196, x1, 870, PAPER, alpha=al)
            frame_rect(f, x0, 196, x1, 870, 1.5, GRAY_LL, alpha=al)
            Text(lab, "mono", "Regular", 13, tracking=2.5).draw(f, x0 + 20, 228, GRAY, alpha=al)
        if al < 0.05:
            return
        s = self.scroll(lt)
        speed = (self.scroll(lt + 0.02) - self.scroll(lt - 0.02)) / 0.04   # lines / s
        head = 560
        streak = min(10.0, speed * self.pitch / 30.0 * 0.4)
        first = int(s - (head - self.top) / self.pitch) - 1
        last = int(s + (self.bot - head) / self.pitch) + 1
        for i in range(max(0, first), min(len(self.lines), last + 1)):
            y = head + (i - s) * self.pitch
            if y < self.top or y > self.bot:
                continue
            edge = min(1.0, (y - self.top) / 40.0, (self.bot - y) / 40.0)
            done = i < s
            for pi, (x0, _) in enumerate(self.panels):
                if pi == 1 and not done:
                    continue
                for (sx, L, cls) in self.lines[i]:
                    col = (self.NEW_COLORS if pi == 1 else self.OLD_COLORS)[cls]
                    a = al * edge * (0.35 if (pi == 0 and done) else 1.0)
                    if pi == 1:
                        a *= smooth((s - i) / 1.5)
                    rect(f, x0 + 22 + sx, y - 3.5 - streak / 2, x0 + 22 + sx + L, y + 3.5 + streak / 2, col,
                         alpha=a * (1 - 0.6 * min(1, streak / 10)))
        # migration head
        for x0, x1 in self.panels:
            hline(f, x0 + 1, x1 - 1, head + self.pitch / 2, 1.5, CLAY, alpha=al * 0.8)
        # counter + progress
        p = s / 2208.0
        n = int(round(680_000 * min(1.0, p)))
        Text(f"{n:,}", "mono", "Medium", 34).draw(f, 884, 948, INK, alpha=al)
        Text("LINES MIGRATED", "mono", "Regular", 14, tracking=2.5).draw(f, 884 + 190, 946, GRAY, alpha=al)
        Text("< 1 DAY", "mono", "Medium", 14, tracking=2.5).draw(f, 1792, 946, CLAY, align="right", alpha=al)
        hline(f, 884, 1792, 900, 2, GRAY_LL, alpha=al)
        hline(f, 884, 884 + (1792 - 884) * min(1.0, p), 900, 2, CLAY, alpha=al)


# ---------------------------------------------------------------- 做 ACT
class ActVis:
    win = (884, 168, 1792, 900)
    side = (884, 210, 1084, 900)
    fields = [(1120, 322), (1120, 402), (1120, 482), (1120, 562)]
    field_w, field_h = 330, 36
    button = (1120, 650, 1268, 694)
    # cursor waypoints: (time, x, y, click?)
    PATH = [(0.95, 1700, 840, False), (1.45, 984, 384, True), (1.9, 1180, 340, True), (2.35, 1180, 420, True),
            (2.8, 1180, 500, True), (3.4, 1194, 672, True)]
    TYPE = [(2.0, 0, 0.62), (2.45, 1, 0.44), (2.9, 2, 0.8)]

    def cursor(self, lt):
        P = self.PATH
        if lt <= P[0][0]:
            return P[0][1], P[0][2]
        for (t0, x0, y0, _), (t1, x1, y1, _) in zip(P[:-1], P[1:]):
            if lt <= t1:
                u = e_io3(prog(lt, t0 + 0.05, t1 - 0.05))
                # slight arc
                mx, my = (x0 + x1) / 2, (y0 + y1) / 2 - 40
                x = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * mx + u * u * x1
                y = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * my + u * u * y1
                return x, y
        return P[-1][1], P[-1][2]

    def scene(self, f, lt):
        x0, y0, x1, y1 = self.win
        rect(f, x0, y0, x1, y1, PAPER)
        frame_rect(f, x0, y0, x1, y1, 2, GRAY_LL)
        hline(f, x0, x1, y0 + 42, 2, GRAY_LL)
        for k in range(3):
            square(f, x0 + 24 + k * 22, y0 + 21, 10, GRAY_LL)
        rect(f, x0 + 380, y0 + 13, x1 - 380, y0 + 29, GRAY_3)
        # sidebar
        vline(f, self.side[2], y0 + 42, y1, 2, GRAY_3)
        sel = lt >= 1.5
        for i in range(8):
            yy = 252 + i * 44
            is_sel = sel and i == 3
            if is_sel:
                rect(f, x0 + 2, yy - 18, self.side[2] - 1, yy + 18, GRAY_3)
                rect(f, x0 + 2, yy - 18, x0 + 6, yy + 18, CLAY)
            square(f, x0 + 34, yy, 12, CLAY if is_sel else GRAY_L)
            rect(f, x0 + 52, yy - 4, x0 + 52 + (90 + (i * 37) % 60), yy + 4, SLATE if is_sel else GRAY_L)
        # main: title + fields
        rect(f, 1120, 248, 1440, 264, SLATE)
        rect(f, 1120, 276, 1300, 284, GRAY_LL)
        for i, (fx, fy) in enumerate(self.fields):
            rect(f, fx, fy - 26, fx + 70 + i * 13, fy - 20, GRAY_L)
            frame_rect(f, fx, fy - 12, fx + self.field_w, fy - 12 + self.field_h, 1.5, GRAY_LL)
        for (tt, i, L) in self.TYPE:
            p = prog(lt, tt, tt + 0.32)
            if p > 0:
                fx, fy = self.fields[i]
                n = int(p * 12)
                for k in range(n):
                    rect(f, fx + 14 + k * (L * 300 / 12), fy - 1, fx + 14 + (k + 0.8) * (L * 300 / 12), fy + 7, SLATE)
        # chart on the right
        cx0 = 1500
        base = 640
        for k in range(5):
            target = [0.45, 0.7, 0.55, 0.85, 0.65][k]
            grow = sum(e_out3(prog(lt, tt + 0.1, tt + 0.5)) for tt, _, _ in self.TYPE) / 3
            hh = 220 * (0.25 + 0.75 * target * grow)
            col = GRAY_LL if grow < 0.99 or k != 3 else CLAY
            rect(f, cx0 + k * 52, base - hh, cx0 + k * 52 + 34, base, col)
        hline(f, cx0 - 10, cx0 + 262, base + 1, 2, GRAY_L)
        # button
        bx0, by0, bx1, by1 = self.button
        pressed = prog(lt, 3.45, 3.6)
        rect(f, bx0, by0, bx1, by1, CLAY_D if 0 < pressed < 1 else CLAY)
        rect(f, bx0 + 34, (by0 + by1) / 2 - 3, bx1 - 34, (by0 + by1) / 2 + 3, PAPER)
        # done toast
        tp = prog(lt, 3.6, 3.9)
        if tp > 0:
            a = e_out3(tp)
            ty = 760 + 14 * (1 - a)
            rect(f, 1120, ty, 1500, ty + 70, IVORY, alpha=a)
            frame_rect(f, 1120, ty, 1500, ty + 70, 1.5, GRAY_LL, alpha=a)
            square(f, 1152, ty + 35, 20, CLAY, alpha=a)
            rect(f, 1180, ty + 25, 1340, ty + 33, SLATE, alpha=a)
            rect(f, 1180, ty + 41, 1420, ty + 47, GRAY_L, alpha=a)

    def draw(self, f, lt):
        vis = prog(lt, 0.1, 0.95)
        if vis <= 0:
            return
        x0, y0, x1, y1 = self.win
        tmp = f[y0 - 8:y1 + 8, x0 - 8:x1 + 8].copy()
        self.scene(f, lt)
        if vis < 1:      # first it sees the screen: blocky, then sharp
            b = int(round(lerp(36, 1, e_out3(vis))))
            sub = f[y0 - 8:y1 + 8, x0 - 8:x1 + 8]
            sub[:] = pixelate(sub, b)
            a = smooth(vis * 2.5)
            sub[:] = tmp + (sub - tmp) * a
        # scanning brackets
        bp_ = prog(lt, 0.1, 0.95)
        if bp_ < 1:
            pad = 40 * (1 - e_out3(bp_))
            al = 1 - smooth(prog(lt, 0.8, 1.05))
            L = 46
            for (cx, cy, sx, sy) in ((x0 - pad, y0 - pad, 1, 1), (x1 + pad, y0 - pad, -1, 1),
                                     (x0 - pad, y1 + pad, 1, -1), (x1 + pad, y1 + pad, -1, -1)):
                rect(f, min(cx, cx + sx * L), cy - 1.5, max(cx, cx + sx * L), cy + 1.5, CLAY, alpha=al)
                rect(f, cx - 1.5, min(cy, cy + sy * L), cx + 1.5, max(cy, cy + sy * L), CLAY, alpha=al)
        # cursor = the pixel
        if lt >= self.PATH[0][0]:
            cx, cy = self.cursor(lt)
            ca = smooth(prog(lt, self.PATH[0][0], self.PATH[0][0] + 0.2))
            for (tc, px, py, clk) in self.PATH[1:]:
                rp = prog(lt, tc, tc + 0.4)
                if clk and 0 < rp < 1:
                    s = 14 + 46 * e_out3(rp)
                    frame_rect(f, px - s / 2, py - s / 2, px + s / 2, py + s / 2, 2, CLAY, alpha=(1 - rp) * 0.9)
            click = any(0 < lt - tc < 0.12 for tc, _, _, c in self.PATH[1:] if c)
            sz = 16 * (0.8 if click else 1.0)
            square(f, cx, cy, sz + 6, PAPER, alpha=ca)
            square(f, cx, cy, sz, CLAY, alpha=ca)
        al = smooth(prog(lt, 0.3, 0.7))
        Text("COMPUTER USE", "mono", "Regular", 14, tracking=2.5).draw(f, 884, 948, GRAY, alpha=al)
        steps = sum(1 for tc, _, _, c in self.PATH[1:] if c and lt >= tc)
        Text(f"{steps} / 5 ACTIONS", "mono", "Regular", 14, tracking=2.5).draw(f, 1792, 948,
                                                                              CLAY if steps == 5 else GRAY,
                                                                              align="right", alpha=al)


# ---------------------------------------------------------------- 信 TRUST: scattered pixels snap into alignment
class TrustVis:
    gx, gy, pitch, size = 14, 10, 54, 38
    ox, oy = 1010, 262

    def __init__(self):
        rs = np.random.default_rng(23)
        n = 160
        self.p = []
        for i in range(n):
            col = [GRAY, GRAY_L, SLATE, CLAY][rs.choice(4, p=[0.38, 0.3, 0.2, 0.12])]
            self.p.append(dict(
                x=rs.uniform(60, 1860), y=rs.uniform(60, 1020), s=rs.uniform(10, 30), col=col,
                vx=rs.uniform(-60, 60), vy=rs.uniform(-40, 40), fx=rs.uniform(0.7, 2.2), fy=rs.uniform(0.7, 2.2),
                ph=rs.uniform(0, 6.28), d=rs.uniform(0, 0.6), lag=rs.uniform(0, 0.14)))
        order = rs.permutation(n)
        centre = (self.gx // 2, self.gy // 2)
        for k, i in enumerate(order):
            if k < self.gx * self.gy:
                c, r = k % self.gx, k // self.gx
                self.p[i]["tx"] = self.ox + c * self.pitch + self.size / 2
                self.p[i]["ty"] = self.oy + r * self.pitch + self.size / 2
                self.p[i]["tcol"] = CLAY if (c, r) == centre else GRAY_LL
            else:
                self.p[i]["tx"] = None

    def draw(self, f, t):
        t0 = T.CAPS[4]
        snap = T.ALIGN_SNAP
        say0, say1 = t0 + 0.35, snap - 0.02
        for q in self.p:
            ap = prog(t, t0 + 0.1 + q["d"], t0 + 0.35 + q["d"])
            if ap <= 0:
                continue
            lt = t - t0
            x = q["x"] + q["vx"] * lt * 0.6 + 14 * math.sin(q["fx"] * lt * 3 + q["ph"])
            y = q["y"] + q["vy"] * lt * 0.6 + 14 * math.cos(q["fy"] * lt * 3 + q["ph"])
            s = q["s"] * e_outback(ap, 2.0)
            col = q["col"]
            a = 1.0
            if t >= snap:
                u = e_outexpo(prog(t, snap + q["lag"], snap + q["lag"] + 0.55))
                xs = q["x"] + q["vx"] * (snap - t0) * 0.6 + 14 * math.sin(q["fx"] * (snap - t0) * 3 + q["ph"])
                ys = q["y"] + q["vy"] * (snap - t0) * 0.6 + 14 * math.cos(q["fy"] * (snap - t0) * 3 + q["ph"])
                if q["tx"] is None:
                    x, y = xs, ys
                    a = 1 - smooth(prog(t, snap, snap + 0.25))
                    s = q["s"] * (1 - 0.5 * u)
                else:
                    x, y = lerp(xs, q["tx"], u), lerp(ys, q["ty"], u)
                    s = lerp(q["s"], self.size, u)
                    col = col + (q["tcol"] - col) * u
                    settle = prog(t, snap + 0.7, snap + 1.0)
                    if 0 < settle < 1:
                        s *= 1 + 0.06 * math.sin(settle * math.pi)
            if say0 < t < say1 + 0.3 and 520 < x < 1400 and 470 < y < 640:
                a *= 1 - 0.8 * smooth(prog(t, say0, say0 + 0.3)) * (1 - smooth(prog(t, say1, say1 + 0.3)))
            square(f, x, y, s, col, alpha=a)
        line_pair(f, t, say0, say1, "能力越强，越需要对齐。", "The more capable it becomes, the more alignment matters.",
                  960, 556, INK, GRAY, align="center", zh_size=46, exit_dur=0.25)
        if t >= snap:
            al = smooth(prog(t, snap + 0.4, snap + 0.8))
            Text("ALIGNED", "mono", "Regular", 14, tracking=2.5).draw(f, self.ox, 948, CLAY, alpha=al)
            Text(f"{self.gx * self.gy} / {self.gx * self.gy}", "mono", "Regular", 14, tracking=2.5).draw(
                f, self.ox + (self.gx - 1) * self.pitch + self.size, 948, GRAY, align="right", alpha=al)


def scene_caps(t, ctx):
    f = new_frame(IVORY)
    i = min(4, int((t - T.CAPS[0]) // T.CAP_LEN))
    t0 = T.CAPS[i]
    lt = t - t0
    cap = CAPS[i]
    if i < 4:
        vis = ctx.vis[i]
        vis.draw(f, lt)
        chapter_text(f, t, cap, t0, t0 + 4.55)
        return exit_dissolve(f, prog(t, t0 + 4.55, t0 + 4.98), IVORY)
    ctx.vis[4].draw(f, t)
    chapter_text(f, t, cap, T.ALIGN_SNAP + 0.1, t0 + 4.55)
    return exit_dissolve(f, prog(t, t0 + 4.55, t0 + 4.98), IVORY)


# ====================================================================== act III: the ceiling
GROUND = 930
PITCH = 40
SQ = 33
COLS_X = [960 + (i - 2.5) * 196 for i in range(6)]
NAMES = [("CLAUDE 1", "2023"), ("CLAUDE 2", "2023"), ("CLAUDE 3", "2024"), ("CLAUDE 4", "2025"),
         ("CLAUDE 5", "2026"), ("OPUS 5.5", "2026")]
HEIGHTS = [4, 6, 8, 10, 12]


def last_column_ticks():
    t0, t1 = T.COLUMN_LAST
    ticks, tk = [], t0
    while tk < t1:
        ticks.append(tk)
        u = (tk - t0) / (t1 - t0)
        tk += 0.16 * (1 - u) ** 1.5 + 0.03
    return ticks


LAST_TICKS = last_column_ticks()


def column_height(i, t):
    """Continuous height (in squares) of column i at time t."""
    if i < 5:
        t0 = T.COLUMN_RISE[i]
        return clamp((t - t0) / 0.032 + 1, 0, HEIGHTS[i]) if t >= t0 else 0.0
    if t < LAST_TICKS[0]:
        return 0.0
    ts = LAST_TICKS + [LAST_TICKS[-1] + 0.03]
    k = np.searchsorted(ts, t, side="right") - 1
    k = min(k, len(ts) - 2)
    frac = clamp((t - ts[k]) / (ts[k + 1] - ts[k]))
    h = k + 1 + frac
    if t > T.BREAK:   # keeps shooting up after it breaks through
        h += (t - T.BREAK) * 30
    return h


def scene_ceiling(t, ctx, fragments=True):
    f = new_frame(IVORY)
    hs = [column_height(i, t) for i in range(6)]
    top5 = GROUND - hs[5] * PITCH
    pan = max(0.0, 300 - top5)          # camera climbs with the last column
    # the ceiling: pushed up by whichever column reaches it
    yc = 560.0
    for i in range(5):
        yc = min(yc, GROUND - hs[i] * PITCH - 14)
    yc = min(yc, top5 - 14) if t < T.BREAK else yc
    # ground + labels
    hline(f, 380, 1540, GROUND + pan + 2, 2, GRAY_LL)
    for i, x in enumerate(COLS_X):
        a = smooth(prog(t, T.CEIL + 0.05 * i, T.CEIL + 0.4 + 0.05 * i))
        Text(NAMES[i][0], "mono", "Medium", 16, tracking=1.5).draw(f, x, GROUND + pan + 40, CLAY if i == 5 else SLATE,
                                                                 align="center", alpha=a)
        Text(NAMES[i][1], "mono", "Regular", 14, tracking=1.5).draw(f, x, GROUND + pan + 62, GRAY, align="center",
                                                                  alpha=a)
    # columns of pixels
    shades = [GRAY_LL, GRAY_L, GRAY, hexc("#6B6A64"), SLATE]
    for i in range(6):
        h = hs[i]
        col = CLAY if i == 5 else shades[i]
        n_full = int(math.floor(h))
        for k in range(int(math.ceil(h))):
            y = GROUND + pan - (k + 0.5) * PITCH
            if y < -40:
                break
            pop = 1.0 if k < n_full else (h - n_full)
            s = SQ * e_outback(pop, 2.0)
            for dx in (-PITCH / 2, PITCH / 2):
                square(f, COLS_X[i] + dx, y, s, col)
    # before it rises, Opus 5.5 waits at the base like a cursor, blinking on the beat
    w0, w1 = T.COLUMN_RISE[4] + 0.3, T.COLUMN_LAST[0]
    if w0 <= t < w1:
        k = (t - w0) / T.BEAT
        on = (k % 1) < 0.55
        a = smooth(prog(t, w0, w0 + 0.2))
        if on:
            for dx in (-PITCH / 2, PITCH / 2):
                square(f, COLS_X[5] + dx, GROUND + pan - 0.5 * PITCH, SQ, CLAY, alpha=a)
    # the ceiling line
    ys = yc + pan
    if t < T.BREAK:
        hline(f, 120, 1800, ys, 2, INK, alpha=0.9)
        Text("上限  CEILING", "mono", "Regular", 14, tracking=2).draw(f, 1800, ys - 14, GRAY, align="right")
        # quiet altitude ticks
        for k in range(-6, 30):
            yy = GROUND + pan - k * 120
            if 0 < yy < H:
                hline(f, 60, 76, yy, 1.5, GRAY_LL)
    else:
        # the line shatters where the column punched through
        ys_b = ctx.break_y + pan
        u = t - T.BREAK
        rp = clamp(u / 0.6)
        sz = 40 + 900 * e_out3(rp)
        frame_rect(f, COLS_X[5] - sz / 2, ys_b - sz / 2, COLS_X[5] + sz / 2, ys_b + sz / 2, 3, CLAY,
                   alpha=(1 - rp) * 0.9)
        rs = np.random.default_rng(99)
        for k in range(90):
            x0 = rs.uniform(120, 1800)
            dxc = x0 - COLS_X[5]
            near = math.exp(-abs(dxc) / 300)
            vx = dxc * 0.9 * near + rs.uniform(-80, 80)
            vy = -rs.uniform(200, 900) * (0.3 + near)
            x = x0 + vx * u
            y = ys_b + vy * u + 900 * u * u
            s = rs.uniform(3, 9)
            a = 1 - smooth(u / 0.6)
            square(f, x, y, s, INK if rs.random() < 0.8 else CLAY, alpha=a)
    line_pair(f, t, T.CEIL_LINE1[0], T.CEIL_LINE1[1], "每一代，都在推高智能的上限。",
              "Every generation raises the ceiling.", LX, 170, INK, GRAY, zh_size=46)
    line_pair(f, t, T.CEIL_LINE2[0], T.CEIL_LINE2[1], "而今天的上限，是明天的起点。",
              "Today's ceiling is tomorrow's floor.", LX, 170, INK, GRAY, zh_size=46)
    return f


def ceiling_break_point(t):
    hs5 = column_height(5, t)
    top5 = GROUND - hs5 * PITCH
    pan = max(0.0, 300 - top5)
    return COLS_X[5], top5 + pan


# ====================================================================== act IV: the real world
HOLD = {"riyadh": (960, 540, 1920), "karakoram": (960, 540, 1920), "everest": (960, 560, 1920),
        "bahamas": (960, 540, 1920), "earth": (960, 470, 880)}
PUSH = 0.055
N_LAND = 64


def world_view(name, t, i):
    """Hold view of montage world i at time t (centre and side, with a slow push-in)."""
    t0 = T.MONTAGE[i]
    t1 = T.MONTAGE[i + 1] if i + 1 < len(T.MONTAGE) else T.SHRINK[0] + 0.4
    cx, cy, S = HOLD[name]
    k = PUSH if name != "earth" else 0.08
    return cx, cy, S * (1 + k * smooth(prog(t, t0, t1)))


def draw_shrinking(f, world, cx, cy, S, bg, final_col=None, k_end=0.0):
    """A world drawn at side S, losing resolution as it gets smaller (cells stay >= ~3 px,
    and collapse to a single flat pixel as k_end -> 1)."""
    if S >= 420 and k_end <= 0:
        draw_world_photo(f, world, cx, cy, S)
        return
    cmin = lerp(3.2, max(S, 3.2), k_end)
    n = 1
    while n * 2 <= 2048 and S / (n * 2) >= cmin:
        n *= 2
    if final_col is not None and n == 1:
        square(f, cx, cy, S, world.mean + (final_col - world.mean) * k_end)
        return
    draw_world_mosaic(f, world, n, cx, cy, S, bg, gap=0)


def scene_montage(t, ctx):
    names = ctx.montage
    i = max(k for k in range(len(names)) if t >= T.MONTAGE[k] - (T.ZOOM_OUT_LEN if k > 0 else 0))
    name = names[i]
    world = ctx.worlds[name]
    f = new_frame(INK)
    T0 = T.MONTAGE[i]
    if i > 0 and t < T0:
        # ---- zoom out: world a shrinks into one pixel of world b
        a = names[i - 1]
        wa = ctx.worlds[a]
        cxa, cya, Sa0 = world_view(a, T0 - T.ZOOM_OUT_LEN, i - 1)
        cxb, cyb, Sb = world_view(name, T0, i)
        n = N_LAND
        c_end = Sb / n
        u = prog(t, T0 - T.ZOOM_OUT_LEN, T0)
        e = e_io3(u)
        Sa = math.exp(lerp(math.log(Sa0), math.log(c_end), e))
        w = (1 / Sa - 1 / Sa0) / (1 / c_end - 1 / Sa0)
        ci, cj = ctx.landing(a, name, n)
        dA = np.array([ci + 0.5 - n / 2, cj + 0.5 - n / 2])
        # screen centre the camera sits on: from a's hold centre to b's
        base = np.array([lerp(cxa, cxb, w), lerp(cya, cyb, w)])
        A = base + w * dA * Sa
        B = base + (w - 1) * dA * Sa
        draw_world_mosaic(f, world, n, B[0], B[1], Sa * n, INK)
        g = gap_for(Sa)
        inner = Sa - g
        k_end = smooth(prog(u, 0.55, 0.98))
        draw_shrinking(f, wa, A[0], A[1], inner, INK, final_col=world.color_at(n, (ci + 0.5) / n, (cj + 0.5) / n),
                       k_end=k_end)
    else:
        cx, cy, S = world_view(name, t, i)
        if i == 0:
            levels = [16, 32, 64, 128, 256, 512, 1024]
            times = [T0, T0 + 0.28, T0 + 0.46, T0 + 0.62, T0 + 0.76, T0 + 0.88, T0 + 1.0]
            draw_world_resolving(f, world, levels, times, 0.2, t, cx, cy, S, INK, origin=ctx.break_uv,
                                 photo_at=T0 + 1.12)
        elif name == "earth":
            earth_scan(f, world, t, T0, cx, cy, S)
        else:
            levels = [64, 128, 256, 512, 1024]
            times = [T0, T0 + 0.1, T0 + 0.28, T0 + 0.46, T0 + 0.62]
            draw_world_resolving(f, world, levels, times, 0.22, t, cx, cy, S, INK, photo_at=T0 + 0.78)
        if i == 0 and t < T0 + 0.4:
            # bloom: cells pop out of the breakthrough point over the ceiling scene
            under = scene_ceiling(t, ctx)
            m = world_bloom_mask(t, T0, 0.36, cx, cy, S, 16, ctx.break_px)
            f = np.where(m[..., None], f, under)
    # caption read-out over a soft floor shade
    shade_hud(f, t, i, name, ctx)
    if name == "earth":
        line_pair(f, t, T.EARTH_LINE[0], T.EARTH_LINE[1], "从一个像素，到整个世界。",
                  "From a single pixel to the whole world.", 960, 990, IVORY, GRAY_L, align="center", zh_size=46,
                  gap=46)
    return f


EARTH_SCAN = (0.05, 1.6)


def earth_scan(f, world, t, T0, cx, cy, S):
    """The last reveal: a clay scan line sweeps the planet from 64 x 64 to full resolution."""
    b0, b1 = T0 + EARTH_SCAN[0], T0 + EARTH_SCAN[1]
    u = e_io3(prog(t, b0, b1))
    x_l, x_r = cx - S / 2 - 60, cx + S / 2 + 60
    xb = lerp(x_l, x_r, u)
    if u < 1:
        draw_world_mosaic(f, world, 64, cx, cy, S, INK)
    if u > 0:
        if u >= 1:
            draw_world_photo(f, world, cx, cy, S)
        else:
            tmp = new_frame(INK)
            draw_world_photo(tmp, world, cx, cy, S)
            xi = int(clamp(round(xb), 0, W))
            f[:, :xi] = tmp[:, :xi]
    if 0 < u < 1 or (t >= b0 and t < b1 + 0.3):
        a = smooth(prog(t, b0, b0 + 0.15)) * (1 - smooth(prog(t, b1 - 0.1, b1 + 0.25)))
        y0, y1 = cy - S / 2 - 30, cy + S / 2 + 30
        for k in range(12):
            rect(f, xb - 5 - k * 7, y0, xb - k * 7 + 1, y1, CLAY, alpha=a * 0.045 * (1 - k / 12))
        vline(f, xb, y0, y1, 3, CLAY, alpha=a)
        Text("FULL RESOLUTION", "mono", "Regular", 14, tracking=2.5).draw(f, xb - 24, y1 + 28, GRAY_L,
                                                                          align="right", alpha=a)
        Text("64 × 64", "mono", "Regular", 14, tracking=2.5).draw(f, xb + 24, y1 + 28, GRAY_L, alpha=a)


_FLOOR = None


def floor_shade():
    global _FLOOR
    if _FLOOR is None:
        y = np.arange(H, dtype=np.float32)
        _FLOOR = (np.clip((y - (H - 230)) / 230, 0, 1) ** 1.6 * 0.55).astype(np.float32)
    return _FLOOR


def shade_hud(f, t, i, name, ctx):
    t0 = T.MONTAGE[i]
    t_out = (T.MONTAGE[i + 1] - T.ZOOM_OUT_LEN) if i + 1 < len(T.MONTAGE) else T.EARTH_LINE[0] - 0.2
    t_in = t0 + (0.6 if name != "earth" else EARTH_SCAN[1] + 0.2)
    a = smooth(prog(t, t_in, t_in + 0.4)) * (1 - smooth(prog(t, t_out - 0.25, t_out)))
    if a <= 0:
        return
    if name != "earth":
        f[-230:] *= (1 - floor_shade()[-230:] * a)[:, None, None]
    Text(f"0{i + 1} / 05", "mono", "Medium", 13, tracking=2).draw(f, 120, 1032, CLAY, alpha=a)
    Text(ctx.captions[name], "mono", "Regular", 13, tracking=2).draw(f, 214, 1032, IVORY, alpha=a * 0.9)
    Text("NASA  ·  PUBLIC DOMAIN", "mono", "Regular", 13, tracking=2).draw(f, 1800, 1032, GRAY_L, align="right",
                                                                         alpha=a * 0.8)


def world_bloom_mask(t, t0, dur, cx, cy, S, n, origin_px, pop=0.16):
    left, top = cx - S / 2, cy - S / 2
    c = S / n
    xs = np.arange(W, dtype=np.float32) + 0.5
    ys = np.arange(H, dtype=np.float32) + 0.5
    gx = (xs - left) / c
    gy = (ys - top) / c
    ix, iy = np.floor(gx), np.floor(gy)
    ccx = (ix + 0.5) * c + left
    ccy = (iy + 0.5) * c + top
    d = np.sqrt((ccx[None, :] - origin_px[0]) ** 2 + (ccy[:, None] - origin_px[1]) ** 2)
    d = d / 2200.0
    jit = ((ix[None, :] * 7919 + iy[:, None] * 104729) % 97) / 97.0
    start = t0 + (0.85 * d + 0.15 * jit) * (dur - pop)
    k = e_out3_arr(np.clip((t - start) / pop, 0, 1))
    fx = gx - ix - 0.5
    fy = gy - iy - 0.5
    return (np.abs(fx)[None, :] < k / 2) & (np.abs(fy)[:, None] < k / 2)


def e_out3_arr(x):
    return 1 - (1 - x) ** 3


# ====================================================================== act V: one pixel, again
WORD = "Claude Opus 5.5"
WORD_SIZE = 124
WORD_Y = 520
CUR = 30


def word_geom():
    xs, width = layout(WORD, "latin", "400", WORD_SIZE, 0.0)
    x0 = 960 - width / 2 - CUR * 0.6
    return xs, width, x0


def scene_end(t, ctx):
    f = new_frame(INK)
    earth = ctx.worlds["earth"]
    xs, width, x0 = word_geom()
    s0, s1 = T.SHRINK
    cx, cy, S0 = world_view("earth", s0, 4)
    if t < s1:
        u = e_io3(prog(t, s0, s1))
        S = math.exp(lerp(math.log(S0), math.log(PIXEL), u))
        draw_shrinking(f, earth, cx, cy, S, INK, final_col=CLAY, k_end=smooth(prog(t, s0 + 0.9, s1)))
        return f
    # the pixel travels to the start of the wordmark, then types it
    ty0, ty1 = T.TYPE
    n_typed = int(clamp((t - ty0) / 0.075 + 1, 0, len(WORD))) if t >= ty0 else 0
    if n_typed == 0:
        pen = 0.0
    elif n_typed < len(WORD):
        pen = xs[n_typed]
    else:
        pen = width
    target = (x0 + pen + CUR * 0.75, WORD_Y - CUR / 2)
    start = (x0 + CUR * 0.75 * 0, WORD_Y - CUR / 2)
    if t < ty0:
        u = e_io3(prog(t, s1 + 0.05, ty0 - 0.02))
        px, py = lerp(cx, start[0], u), lerp(cy, start[1], u)
    else:
        prev = xs[n_typed - 1] if 1 <= n_typed <= len(WORD) else 0.0
        k = clamp((t - (ty0 + (n_typed - 1) * 0.075)) / 0.05)
        px = x0 + lerp(prev, pen, e_out3(k)) + CUR * 0.75
        py = target[1]
    # typed characters
    for i in range(n_typed):
        ch = WORD[i]
        if ch == " ":
            continue
        tc = ty0 + i * 0.075
        p = prog(t, tc, tc + 0.16)
        col = IVORY if i < 6 else GRAY_L
        weight = "400" if i < 6 else "300"
        m, ox, oy = glyph("latin", weight, WORD_SIZE, ch)
        b = int(round(lerp(14, 1, e_out3(p))))
        mm = pixelate(m, b) if b > 1 else m
        blend(f, int(round(x0 + xs[i] + ox)), int(round(WORD_Y + oy)), col, mm * min(1, p * 2))
    # the cursor blinks on the beat once typing is done
    vis = True
    if t > ty1 + 0.4:
        vis = ((t - (ty1 + 0.4)) % T.BEAT) < T.BEAT * 0.58
    if vis:
        square(f, px, py, CUR, CLAY)
    line_pair(f, t, T.TAGLINE, T.DURATION + 1, "智能，全分辨率。", "Intelligence, in full resolution.",
              960, 650, GRAY_LL, GRAY, align="center", zh_size=40, zh_weight="Light", gap=46)
    a = smooth(prog(t, T.CREDITS, T.CREDITS + 0.8))
    Text("CONCEPT FILM   ·   IMAGERY: NASA, PUBLIC DOMAIN   ·   MUSIC, TYPE & MOTION GENERATED IN CODE",
         "mono", "Regular", 12, tracking=2).draw(f, 960, 1030, GRAY, align="center", alpha=a * 0.75)
    fo = prog(t, T.FADE_OUT[0], T.FADE_OUT[1])
    if fo > 0:
        f *= 1 - smooth(fo)
    return f


# ====================================================================== dispatcher
def render(t, ctx):
    if t < T.WIPE1[0]:
        return scene_genesis(t, ctx)
    if t < T.WIPE1[1]:
        a = scene_genesis(t, ctx)
        b = new_frame(IVORY)
        m = bloom_mask(t, T.WIPE1[0], T.WIPE1[1] - T.WIPE1[0], tile=120, origin=EARTH_C)
        return np.where(m[..., None], b, a)
    if t < T.CEIL:
        return scene_caps(t, ctx)
    if t < T.DROP:
        return scene_ceiling(t, ctx)
    if t < T.SHRINK[0]:
        return scene_montage(t, ctx)
    return scene_end(t, ctx)


def make_ctx():
    ctx = Ctx()
    ctx.vis = [ReadVis(), ReasonVis(), CodeVis(), ActVis(), TrustVis()]
    bx, by = ceiling_break_point(T.BREAK)
    ctx.break_px = (bx, max(by, 0.0))
    ctx.break_y = GROUND - column_height(5, T.BREAK) * PITCH - 14
    cx, cy, S = HOLD["riyadh"]
    ctx.break_uv = ((bx - (cx - S / 2)) / S, (max(by, 0.0) - (cy - S / 2)) / S)
    return ctx


# ====================================================================== key visual
def poster(ctx):
    """Still: the earth half pixels, half photograph, split by the clay line."""
    f = new_frame(INK)
    earth = ctx.worlds["earth"]
    cx, cy, S = 960, 500, 860
    draw_world_photo(f, earth, cx, cy, S)
    left = new_frame(INK)
    draw_world_mosaic(left, earth, 32, cx, cy, S, INK)
    split = 960
    f[:, :split] = left[:, :split]
    vline(f, split, cy - S / 2 - 30, cy + S / 2 + 30, 3, CLAY)
    Text("32 × 32", "mono", "Regular", 14, tracking=2.5).draw(f, split - 24, cy + S / 2 + 58, GRAY_L, align="right")
    Text("FULL RESOLUTION", "mono", "Regular", 14, tracking=2.5).draw(f, split + 24, cy + S / 2 + 58, GRAY_L)
    Text("Claude Opus 5.5", "latin", "400", 40).draw(f, 120, 1012, IVORY)
    Text("智能，全分辨率。", "serif", "Light", 26).draw(f, 1800, 1010, GRAY_LL, align="right")
    return f
