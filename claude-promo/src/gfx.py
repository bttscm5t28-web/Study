"""Drawing primitives: palette, easing, anti-aliased rects, text with a
per-character "pixel resolve", and the mosaic engine that turns any square
image ("world") into a grid of flat pixels at any resolution.

Frames are float32 (H, W, 3) arrays in 0..1 (sRGB).
"""
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


# ---------------------------------------------------------------- palette (warm, quiet, one accent)
INK = hexc("#141413")
INK2 = hexc("#1E1D1B")
IVORY = hexc("#F0EEE6")
PAPER = hexc("#FAF9F5")
CLAY = hexc("#D97757")
CLAY_D = hexc("#C2603F")
SLATE = hexc("#3D3D3A")
GRAY = hexc("#87867F")
GRAY_L = hexc("#B0AEA5")
GRAY_LL = hexc("#D1CFC5")
GRAY_3 = hexc("#E3E1D8")
SKY = hexc("#6A9BCC")
OLIVE = hexc("#788C5D")
HEATHER = hexc("#9D8FB8")


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else (b if x > b else x)


def prog(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)


def lerp(a, b, u):
    return a + (b - a) * u


def e_out3(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def e_in3(x):
    x = clamp(x)
    return x ** 3


def e_io3(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def e_out5(x):
    x = clamp(x)
    return 1 - (1 - x) ** 5


def e_outexpo(x):
    x = clamp(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def e_inexpo(x):
    x = clamp(x)
    return 0.0 if x <= 0 else 2 ** (10 * x - 10)


def e_ioexpo(x):
    x = clamp(x)
    if x <= 0 or x >= 1:
        return x
    return 2 ** (20 * x - 10) / 2 if x < 0.5 else (2 - 2 ** (-20 * x + 10)) / 2


def e_outback(x, s=1.6):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def hash01(*k):
    """Deterministic pseudo-random in [0,1) from integers."""
    h = 2166136261
    for v in k:
        h = ((h ^ (int(v) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 1274126177) & 0xFFFFFFFF
    return (h & 0xFFFFFF) / float(0x1000000)


# ---------------------------------------------------------------- frame ops
def new_frame(color):
    f = np.empty((H, W, 3), np.float32)
    f[:] = color
    return f


def blend(frame, x0, y0, src, alpha):
    """Lerp `src` (colour (3,) or (h,w,3)) into frame at integer (x0, y0) by alpha (h,w)."""
    h, w = alpha.shape
    fx0, fy0 = max(0, x0), max(0, y0)
    fx1, fy1 = min(W, x0 + w), min(H, y0 + h)
    if fx0 >= fx1 or fy0 >= fy1:
        return
    a = alpha[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0, None]
    region = frame[fy0:fy1, fx0:fx1]
    if np.ndim(src) == 1:
        region += (src - region) * a
    else:
        region += (src[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0] - region) * a


def rect(frame, x0, y0, x1, y1, color, alpha=1.0):
    """Anti-aliased axis-aligned rectangle with sub-pixel edges."""
    x0, x1 = max(x0, -2), min(x1, W + 2)
    y0, y1 = max(y0, -2), min(y1, H + 2)
    if x1 <= x0 or y1 <= y0 or alpha <= 0.002:
        return
    ix0, iy0 = int(np.floor(x0)), int(np.floor(y0))
    ix1, iy1 = int(np.ceil(x1)), int(np.ceil(y1))
    xs = np.arange(ix0, ix1, dtype=np.float32)
    ys = np.arange(iy0, iy1, dtype=np.float32)
    cx = np.clip(np.minimum(xs + 1, x1) - np.maximum(xs, x0), 0, 1)
    cy = np.clip(np.minimum(ys + 1, y1) - np.maximum(ys, y0), 0, 1)
    blend(frame, ix0, iy0, color, np.outer(cy, cx) * np.float32(alpha))


def square(frame, cx, cy, s, color, alpha=1.0):
    rect(frame, cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2, color, alpha)


def hline(frame, x0, x1, y, th, color, alpha=1.0):
    rect(frame, x0, y - th / 2, x1, y + th / 2, color, alpha)


def vline(frame, x, y0, y1, th, color, alpha=1.0):
    rect(frame, x - th / 2, y0, x + th / 2, y1, color, alpha)


def frame_rect(frame, x0, y0, x1, y1, th, color, alpha=1.0):
    hline(frame, x0, x1, y0 + th / 2, th, color, alpha)
    hline(frame, x0, x1, y1 - th / 2, th, color, alpha)
    vline(frame, x0 + th / 2, y0 + th, y1 - th, th, color, alpha)
    vline(frame, x1 - th / 2, y0 + th, y1 - th, th, color, alpha)


def pixelate(img, b):
    """Block-average an (h,w[,c]) array with b x b blocks (grid anchored top-left)."""
    if b <= 1:
        return img
    h, w = img.shape[:2]
    H2, W2 = -(-h // b) * b, -(-w // b) * b
    pad = [(0, H2 - h), (0, W2 - w)] + [(0, 0)] * (img.ndim - 2)
    p = np.pad(img, pad, mode="edge")
    sh = (H2 // b, b, W2 // b, b) + img.shape[2:]
    m = p.reshape(sh).mean(axis=(1, 3))
    m = np.repeat(np.repeat(m, b, axis=0), b, axis=1)
    return m[:h, :w]


def pixelate_frame(frame, b, region=None):
    """Mosaic the frame in place (grid anchored to the frame origin, so blocks line up)."""
    if b <= 1:
        return
    if region is None:
        region = (0, 0, W, H)
    x0, y0, x1, y1 = region
    x0, y0 = (x0 // b) * b, (y0 // b) * b
    sub = frame[y0:y1, x0:x1]
    frame[y0:y1, x0:x1] = pixelate(sub, b)


# ---------------------------------------------------------------- fonts & text
NOTO = "/usr/share/fonts/opentype/noto"
FONTS = {
    "serif": lambda w: (f"{NOTO}/NotoSerifCJK-{w}.ttc", 2),     # 思源宋体 SC
    "sans": lambda w: (f"{NOTO}/NotoSansCJK-{w}.ttc", 2),       # 思源黑体 SC
    "latin": lambda w: (os.path.join(ROOT, "assets", "fonts", f"SourceSerif4Display-{w}.ttf"), 0),
    "mono": lambda w: (f"/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-{w}.ttf", 0),
    "inter": lambda w: (f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", 0),
}


@lru_cache(maxsize=None)
def font(kind, weight, size):
    path, idx = FONTS[kind](weight)
    return ImageFont.truetype(path, size, index=idx, layout_engine=ImageFont.Layout.RAQM)


@lru_cache(maxsize=8192)
def glyph(kind, weight, size, ch):
    """Alpha mask of one character, plus its top-left offset from the pen position on the baseline."""
    f = font(kind, weight, size)
    l, t, r, b = f.getbbox(ch, anchor="ls")
    pad = 3
    im = Image.new("L", (max(1, r - l) + 2 * pad, max(1, b - t) + 2 * pad), 0)
    ImageDraw.Draw(im).text((pad - l, pad - t), ch, font=f, fill=255, anchor="ls")
    return np.asarray(im, np.float32) / 255.0, l - pad, t - pad


@lru_cache(maxsize=4096)
def layout(text, kind, weight, size, tracking=0.0):
    """Pen x for each character (kerned) and the total advance."""
    f = font(kind, weight, size)
    xs = [f.getlength(text[:i]) + tracking * i for i in range(len(text))]
    width = f.getlength(text) + tracking * max(0, len(text) - 1)
    return tuple(xs), width


def text_width(text, kind, weight, size, tracking=0.0):
    return layout(text, kind, weight, size, tracking)[1]


class Text:
    """A line of text that can appear/disappear character by character with a pixel resolve.

    appear(i, n) -> 0..1 progress for char i.  Characters start as coarse blocks
    of their own shape and sharpen into the final glyph.
    """

    def __init__(self, text, kind="serif", weight="Regular", size=40, tracking=0.0):
        self.s, self.kind, self.weight, self.size, self.tracking = text, kind, weight, size, tracking
        self.xs, self.width = layout(text, kind, weight, size, tracking)

    def draw(self, frame, x, y, color, align="left", alpha=1.0, prog_fn=None, block=None, rise=0.0,
             exit_p=0.0):
        if alpha <= 0.003:
            return
        x0 = x - (self.width / 2 if align == "center" else (self.width if align == "right" else 0))
        n = len(self.s)
        block = block if block is not None else max(4, int(self.size / 5))
        for i, ch in enumerate(self.s):
            if ch == " ":
                continue
            p = 1.0 if prog_fn is None else prog_fn(i, n)
            if p <= 0:
                continue
            m, ox, oy = glyph(self.kind, self.weight, self.size, ch)
            a = alpha * min(1.0, p * 1.8)
            b = 1
            if p < 1:
                b = int(round(lerp(block, 1, e_out3(p))))
            if exit_p > 0:
                b = max(b, int(round(lerp(1, block, e_in3(exit_p)))))
                a *= 1 - e_in3(exit_p)
            mm = pixelate(m, b) if b > 1 else m
            dy = rise * (1 - e_out3(p))
            blend(frame, int(round(x0 + self.xs[i] + ox)), int(round(y + oy + dy)), color, mm * a)


def stagger(t, t0, per=0.035, dur=0.5):
    """prog_fn factory: char i starts at t0 + i*per and resolves over dur."""
    return lambda i, n: prog(t, t0 + i * per, t0 + i * per + dur)


# ---------------------------------------------------------------- worlds & the mosaic engine
class World:
    """A square photograph with a mip pyramid of flat-colour cells (1x1 .. 2048x2048)."""

    def __init__(self, path, pyramid=2048):
        img = Image.open(path).convert("RGB")
        self.img = img
        self.q = img.size[0]
        base = img.resize((pyramid, pyramid), Image.BOX) if self.q != pyramid else img
        a = np.asarray(base, np.float32) / 255.0
        self.levels = {pyramid: a}
        n = pyramid
        while n > 1:
            a = a.reshape(n // 2, 2, n // 2, 2, 3).mean(axis=(1, 3))
            n //= 2
            self.levels[n] = a
        self.mean = self.levels[1][0, 0].copy()

    def color_at(self, n, u, v):
        """Cell colour at level n for normalised coords (u, v)."""
        i = min(n - 1, int(u * n))
        j = min(n - 1, int(v * n))
        return self.levels[n][j, i]


def _span(lo, size, limit):
    a = max(0, int(np.floor(lo)))
    b = min(limit, int(np.ceil(lo + size)))
    return a, b


def gap_for(c):
    """Grid-line width (px) for a cell size c: visible tiles when big, invisible when tiny,
    and a little bolder when a single cell fills most of the screen."""
    if c < 5:
        return 0.0
    return (float(np.clip(c * 0.07, 1.0, 3.2)) + max(0.0, c - 120) * 0.004) * smooth((c - 5) / 6)


def world_cells(world, n, cx, cy, S):
    """Per-pixel cell lookup of a world square of side S centred at (cx, cy) at level n.

    Returns (x0, y0, img, gx, gy) where gx/gy are the fractional cell coords."""
    left, top = cx - S / 2, cy - S / 2
    x0, x1 = _span(left, S, W)
    y0, y1 = _span(top, S, H)
    if x1 <= x0 or y1 <= y0:
        return None
    c = S / n
    gx = (np.arange(x0, x1, dtype=np.float32) + 0.5 - left) / c
    gy = (np.arange(y0, y1, dtype=np.float32) + 0.5 - top) / c
    ix = np.clip(gx.astype(np.int32), 0, n - 1)
    iy = np.clip(gy.astype(np.int32), 0, n - 1)
    img = world.levels[n][iy[:, None], ix[None, :]]
    return x0, y0, img, gx, gy


def grid_mask(gx, gy, c, gap):
    """Boolean mask of grid lines (gap px wide, centred on the cell borders)."""
    if gap <= 0:
        return None
    h = gap / 2.0 / c
    fx = gx - np.floor(gx)
    fy = gy - np.floor(gy)
    mx = (fx < h) | (fx > 1 - h)
    my = (fy < h) | (fy > 1 - h)
    return my[:, None] | mx[None, :]


def draw_world_mosaic(frame, world, n, cx, cy, S, bg, gap=None, alpha=1.0):
    r = world_cells(world, n, cx, cy, S)
    if r is None:
        return
    x0, y0, img, gx, gy = r
    c = S / n
    g = gap_for(c) if gap is None else gap
    m = grid_mask(gx, gy, c, g)
    if m is not None:
        img = img.copy()
        img[m] = bg
    h, w = img.shape[:2]
    if alpha >= 1:
        frame[y0:y0 + h, x0:x0 + w] = img
    else:
        blend(frame, x0, y0, img, np.full((h, w), alpha, np.float32))


def draw_world_photo(frame, world, cx, cy, S, alpha=1.0):
    """Full-resolution (resampled) view of the world square."""
    left, top = cx - S / 2, cy - S / 2
    x0, x1 = _span(left, S, W)
    y0, y1 = _span(top, S, H)
    if x1 <= x0 or y1 <= y0:
        return
    k = world.q / S
    q = float(world.q)
    box = (min(max((x0 - left) * k, 0.0), q), min(max((y0 - top) * k, 0.0), q),
           min(max((x1 - left) * k, 0.0), q), min(max((y1 - top) * k, 0.0), q))
    if box[2] - box[0] < 1e-3 or box[3] - box[1] < 1e-3:
        return
    im = world.img.resize((x1 - x0, y1 - y0), Image.BICUBIC, box=box)
    a = np.asarray(im, np.float32) / 255.0
    if alpha >= 1:
        frame[y0:y1, x0:x1] = a
    else:
        blend(frame, x0, y0, a, np.full(a.shape[:2], alpha, np.float32))


def wave_delay(n, origin=(0.5, 0.5), jitter=0.25, seed=0):
    """Per-cell 0..1 delay for a wave spreading from `origin` (normalised) across an n x n grid."""
    key = (n, round(origin[0], 4), round(origin[1], 4), jitter, seed)
    if key in _WAVE:
        return _WAVE[key]
    c = (np.arange(n, dtype=np.float32) + 0.5) / n
    d = np.sqrt((c[None, :] - origin[0]) ** 2 + (c[:, None] - origin[1]) ** 2)
    d = d / max(d.max(), 1e-6)
    rs = np.random.default_rng(seed + n)
    d = (1 - jitter) * d + jitter * rs.random((n, n), dtype=np.float32)
    _WAVE[key] = d
    return d


_WAVE = {}


def draw_world_resolving(frame, world, levels, times, wave, t, cx, cy, S, bg, origin=(0.5, 0.5),
                         flash=0.22, photo_at=None, photo_fade=0.18):
    """Draw a world that resolves through `levels` (n0 < n1 < ...).

    Level k (k>=1) starts replacing level k-1 at times[k], cell by cell over `wave` seconds.
    If photo_at is given, the real photograph cross-fades in from that time.
    """
    k = 0
    for i, tk in enumerate(times):
        if t >= tk:
            k = i
    if photo_at is not None and t >= photo_at + photo_fade:
        draw_world_photo(frame, world, cx, cy, S)
        return
    n_new = levels[k]
    if k == 0 or t >= times[k] + wave:
        draw_world_mosaic(frame, world, n_new, cx, cy, S, bg)
    else:
        n_old = levels[k - 1]
        r_new = world_cells(world, n_new, cx, cy, S)
        r_old = world_cells(world, n_old, cx, cy, S)
        if r_new is None:
            return
        x0, y0, img_n, gxn, gyn = r_new
        _, _, img_o, gxo, gyo = r_old
        d = wave_delay(n_old, origin)
        io = np.clip(gyo.astype(np.int32), 0, n_old - 1)
        jo = np.clip(gxo.astype(np.int32), 0, n_old - 1)
        thr = times[k] + wave * d[io[:, None], jo[None, :]]
        on = (t >= thr)
        img = np.where(on[..., None], img_n, img_o)
        if flash > 0:   # newly split cells blink once (dark cells stay dark: no sparkle in space)
            lum = img_n @ np.array([0.3, 0.55, 0.15], np.float32)
            f = np.clip(1 - (t - thr) / 0.12, 0, 1) * on * flash * np.clip((lum - 0.12) * 3, 0, 1)
            img = img + (1 - img) * f[..., None]
        cn, co = S / n_new, S / n_old
        mn = grid_mask(gxn, gyn, cn, gap_for(cn))
        mo = grid_mask(gxo, gyo, co, gap_for(co))
        if mn is not None:
            img[mn & on] = bg
        if mo is not None:
            img[mo & ~on] = bg
        h, w = img.shape[:2]
        frame[y0:y0 + h, x0:x0 + w] = img
    if photo_at is not None and t >= photo_at:
        draw_world_photo(frame, world, cx, cy, S, alpha=smooth((t - photo_at) / photo_fade))


def bloom_mask(t, t0, dur, tile=120, origin=(W / 2, H / 2), spread=0.75, pop=0.28, seed=3):
    """Mask (H, W) of a pixel-bloom wipe: tiles grow from their centres, rippling out from origin."""
    nx, ny = -(-W // tile), -(-H // tile)
    cx = (np.arange(nx) + 0.5) * tile
    cy = (np.arange(ny) + 0.5) * tile
    d = np.sqrt((cx[None, :] - origin[0]) ** 2 + (cy[:, None] - origin[1]) ** 2)
    d = d / d.max()
    rs = np.random.default_rng(seed)
    d = 0.8 * d + 0.2 * rs.random(d.shape)
    start = t0 + d * (dur - pop) * spread / 0.75
    k = np.clip((t - start) / pop, 0, 1)
    k = 1 - (1 - k) ** 3
    xs = np.arange(W)
    ys = np.arange(H)
    lx = (xs % tile) - tile / 2 + 0.5
    ly = (ys % tile) - tile / 2 + 0.5
    kk = k[(ys // tile)[:, None], (xs // tile)[None, :]]
    half = kk * tile / 2
    return (np.abs(lx)[None, :] < half) & (np.abs(ly)[:, None] < half)
