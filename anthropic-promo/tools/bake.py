#!/usr/bin/env python3
"""Pre-bake for 《从一个像素开始》 (docs/storyboard.md §1.1, §1.2, §1.4, §3 S10, §4, §5).

Produces, in build/bake/:
  {photo}_{block}_{mode}_b{brightness}.png   every quantized mosaic stage, at the stage's grid
                                             resolution (renderer upscales nearest-neighbour)
  earth_qt_g00.png … earth_qt_g14.png        the 15 Earth quadtree generations at 1920x1080
  earth_qt_depths.npz                        depth maps (216x384, one entry per 5-px cell) + split order
  manifest.json                              dims / block / mode / brightness per file, windows,
                                             P25/P80 thresholds and 16x9 token maps per photo
  check_face_grid.png, check_stages.png      gate (a) overlay and the quick-look contact sheet

Deterministic and idempotent: python3 tools/bake.py
"""
import json, os, sys, time
import glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import median_filter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PHOTOS = os.path.join(ROOT, 'assets', 'photos')
OUT = os.path.join(ROOT, 'build', 'bake')
FONT = os.path.join(ROOT, 'assets', 'fonts', 'Inter-600-normal.ttf')
W, H = 1920, 1080
BLOCKS = [120, 60, 30, 15, 5, 1]

# ---- palette (§1.2) ------------------------------------------------------------------------
INK, SLATE, PAPER, EMBER = 0, 1, 2, 3
TOKEN_RGB = np.array([[0x0B, 0x0B, 0x0E], [0x3A, 0x3F, 0x4B], [0xF3, 0xEF, 0xE7], [0xE8, 0x61, 0x3A]], np.float64)
TOKEN_CH = 'ISPE'
PAPER_PINNED_HI = np.array([0x86, 0x83, 0x80], np.float64)   # paper @ 55 %
PAPER_PINNED_LO = np.array([0x61, 0x5F, 0x5C], np.float64)   # paper @ 40 %
SLATE_BLUE = 0x4B

# ---- photos and windows (§4) ---------------------------------------------------------------
# window = (left, top); rotate = 180° before cropping. Face T may move in 10-px steps inside
# 40–100 only to keep the eye line in y 380–470 (gate a); the origin never moves.
SOURCES = {
    'face':   dict(file='1438761681033-6461ffad8d80.jpg', window=(0, 60), rotate=False),
    'people': dict(file='1511632765486-a01980e01a18.jpg', window=(0, 200), rotate=False),
    'city':   dict(file='1444723121867-7a241cacace9.jpg', window=(0, 200), rotate=False),   # Los Angeles aerial
    # STAR GUARD (earth only): the colour fed to the 4-token decision at 120/60/30 px (and to quadtree depths
    # 0-2, whose drawn colour is the token anyway) is a TRIMMED block mean that excludes the brightest
    # max(0.5 % of the cell's pixels, 16 pixels), pixels ranked by linear luminance. A star is a <= 4x4 cluster
    # (~0.1 % of a 120-px cell; 16 px is 1.8 % of a 30-px cell, where 0.5 % = 5 px would not cover it), while
    # the lit coast has far more lit pixels than that, so the paper/slate band is unaffected. P25/P80 are
    # computed from the same trimmed means. Real-colour stages (c8/c32/full, depths 3-5) are untouched.
    'earth':  dict(file='1451187580459-43490279c0fa.jpg', window=(0, 98), rotate=True,
                   star_guard=dict(frac=0.005, min_px=16, ink_floor=6)),
    # ink_floor: a cell whose trimmed-mean sRGB max channel is < 6 is INK regardless of the percentile.
    'sky':    dict(file='1444703686981-a3abbc4d4fe3_2880.jpg', window=(258, 840), rotate=False),
}

# ---- stages: (block, mode, brightness) -------------------------------------------------------
STAGES = {
    'face':   [(120, 'tok', 55), (60, 'tok2', 55), (60, 'tok2', 65), (30, 'tok', 75), (15, 'tok', 80), (15, 'c8', 85),
               (5, 'c8', 92), (5, 'c32', 92), (1, 'full', 100), (120, 'tok', 70)],
    'people': [(120, 'tok', 70), (60, 'tok2', 80), (30, 'tok', 90), (1, 'full', 100)],
    'city':   [(120, 'tok', 55), (60, 'tok2', 62), (30, 'tok', 70), (30, 'c8', 77), (15, 'c8', 85),
               (5, 'c8', 92), (5, 'c32', 96), (1, 'full', 100),
               (60, 'tok2', 60), (120, 'tok', 50)],          # reverse set reuses 15_c8_b85 and 30_tok_b70
    'earth':  [(120, 'tok', 70)],                            # = quadtree g00
    'sky':    [(1, 'full', 100)],
}
GRADED = set()      # no photo is graded (the Shanghai grade was dropped with the city swap)
PALETTE_GUARD = 40.0   # every c8/c32 palette entry must be within this sRGB distance of a real block mean

# ---- quadtree (§3 S10, §5.6) ---------------------------------------------------------------
QT_TARGETS = [0.03, 0.05, 0.08, 0.12, 0.17, 0.23, 0.30, 0.38, 0.47, 0.57, 0.68, 0.80]
QT_G13_TARGET = 0.90
QT_CS = [24, 12, 6, 3, 1]            # leaf size in 5-px cells for depths 0–4
QT_BS = [120, 60, 30, 15, 5, 1]      # block size per depth
QT_MAXD = 4                          # generations 1–13 split to depth <= 4 (5 px); g14 = depth 5 (real) everywhere
# S = mean(depth)/4 over depths 0–4; depth 0–2 tokens, depth 3 and 4 the 8-colour palette, depth 5 real.


# =============================================================================================
# colour maths
# =============================================================================================
_LUT_LIN = np.empty(256, np.float64)
for _i in range(256):
    _c = _i / 255.0
    _LUT_LIN[_i] = _c / 12.92 if _c <= 0.04045 else ((_c + 0.055) / 1.055) ** 2.4


def lin_to_srgb(y):
    y = np.clip(y, 0.0, 1.0)
    s = np.where(y <= 0.0031308, 12.92 * y, 1.055 * np.power(y, 1 / 2.4) - 0.055)
    return s * 255.0


def to_u8(x):
    return np.clip(np.rint(x), 0, 255).astype(np.uint8)


def oklab(lin):
    """linear sRGB (…,3) -> (L, a, b) arrays."""
    r, g, b = lin[..., 0], lin[..., 1], lin[..., 2]
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = np.cbrt(l), np.cbrt(m), np.cbrt(s)
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    bb = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, a, bb


def block_means(lin, b):
    """Independent block-mean sample at block size b, anchored at (0,0), linear light."""
    if b == 1:
        return lin
    return lin.reshape(H // b, b, W // b, b, 3).mean(axis=(1, 3))


def trimmed_block_means(lin, b, frac, min_px):
    """Block mean over each b-px cell after dropping its brightest max(ceil(frac*n), min_px) pixels (by Rec.709 Y
    of linear light). Used only for the token decision of a star-guarded photo."""
    n = b * b
    k = max(int(np.ceil(frac * n)), min_px)
    if k <= 0:
        return block_means(lin, b)
    cells = lin.reshape(H // b, b, W // b, b, 3).transpose(0, 2, 1, 3, 4).reshape(H // b, W // b, n, 3)
    Y = 0.2126 * cells[..., 0] + 0.7152 * cells[..., 1] + 0.0722 * cells[..., 2]
    keep = n - k
    idx = np.argpartition(Y, keep - 1, axis=-1)[..., :keep]
    return np.take_along_axis(cells, idx[..., None], axis=2).mean(axis=2)


def quantize_tokens(lin_means, p25, p80):
    L, a, b = oklab(lin_means)
    C = np.hypot(a, b)
    hue = np.degrees(np.arctan2(b, a)) % 360.0
    tok = np.where(L < p25, INK, SLATE)
    tok = np.where((L > p80) & (tok != INK), PAPER, tok)
    ember = (L > p25) & (hue >= 10.0) & (hue <= 70.0) & (C > 0.045)
    tok = np.where(ember, EMBER, tok)
    return tok.astype(np.int8), L


def token_lut(bright, two_level=False):
    """(4[,2],3) float colours: ink/slate/ember scaled by b/100, paper pinned."""
    hi = TOKEN_RGB * (bright / 100.0)
    hi[PAPER] = PAPER_PINNED_HI
    if not two_level:
        return np.rint(hi)
    lo = TOKEN_RGB * ((bright - 15) / 100.0)
    lo[PAPER] = PAPER_PINNED_LO
    return np.rint(np.stack([lo, hi], axis=1))     # [token, level(0=lo,1=hi), rgb]


def two_level_mask(tok, L):
    """Within each token, cells with L above that token's median L (over the stage) -> level 1."""
    hi = np.zeros(tok.shape, np.int8)
    for t in range(4):
        m = tok == t
        if m.any():
            hi[m & (L > np.median(L[m]))] = 1
    return hi


def median_cut(srgb_u8, n):
    """PIL median-cut palette on the small image, no dither; returns the remapped RGB uint8."""
    im = Image.fromarray(srgb_u8, 'RGB')
    q = im.quantize(colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    out = np.asarray(q.convert('RGB'))
    # palette guard: every palette entry must be within PALETTE_GUARD of a real block mean of this stage
    pal = np.unique(out.reshape(-1, 3), axis=0).astype(np.float64)
    real = srgb_u8.reshape(-1, 3).astype(np.float64)
    worst = 0.0
    for c in pal:
        worst = max(worst, float(np.sqrt(((real - c) ** 2).sum(1)).min()))
    assert worst <= PALETTE_GUARD, f'palette guard: entry {worst:.1f} sRGB from every real pixel (n={n})'
    median_cut.last_guard = (len(pal), round(worst, 2))
    return out


def nearest_palette(srgb_u8, palette_u8):
    """Map every pixel to the nearest entry of a fixed palette (sRGB euclidean)."""
    pal = np.unique(palette_u8.reshape(-1, 3), axis=0).astype(np.int32)
    px = srgb_u8.reshape(-1, 3).astype(np.int32)
    d = ((px[:, None, :] - pal[None, :, :]) ** 2).sum(2)
    return pal[d.argmin(1)].astype(np.uint8).reshape(srgb_u8.shape)


def grade_city(srgb):
    """−25 % saturation (toward luma), blue pulled 10 % toward slate's blue (#4B). sRGB float in/out."""
    y = 0.2126 * srgb[..., 0] + 0.7152 * srgb[..., 1] + 0.0722 * srgb[..., 2]
    out = y[..., None] + 0.75 * (srgb - y[..., None])
    out[..., 2] = out[..., 2] + 0.10 * (SLATE_BLUE - out[..., 2])
    return np.clip(out, 0, 255)


def scale(rgb_u8, bright):
    return to_u8(rgb_u8.astype(np.float64) * (bright / 100.0))


def tokmap_strings(tok):
    return [''.join(TOKEN_CH[t] for t in row) for row in tok]


def print_tokmap(name, tok):
    print(f'  {name} token map ({tok.shape[1]}x{tok.shape[0]}):')
    print('        ' + ''.join(f'{c + 1:<2}'[:2] if tok.shape[1] <= 16 else '' for c in range(tok.shape[1])))
    for r, s in enumerate(tokmap_strings(tok)):
        print(f'  row {r + 1:2d}  ' + (' '.join(s) if tok.shape[1] <= 16 else s))


# =============================================================================================
# photo loading
# =============================================================================================
class Photo:
    def __init__(self, name):
        spec = SOURCES[name]
        self.name = name
        im = Image.open(os.path.join(PHOTOS, spec['file'])).convert('RGB')
        self.src_size = im.size
        if spec['rotate']:
            im = im.transpose(Image.Transpose.ROTATE_180)
        L, T = spec['window']
        assert L >= 0 and T >= 0 and L + W <= im.size[0] and T + H <= im.size[1], (name, im.size, spec['window'])
        self.window = (L, T, L + W, T + H)
        self.srgb = np.asarray(im.crop(self.window))            # (1080,1920,3) uint8
        self.lin = _LUT_LIN[self.srgb]                           # linear light float64
        self._means = {}
        self._tok_means = {}
        self._base = {}
        self.guard = {}
        self.star_guard = spec.get('star_guard')
        # frozen 4-token thresholds from the 144 (star-guarded, if so) block means at 120 px
        self.L120 = oklab(self.tok_means(120))[0]
        self.p25, self.p80 = float(np.percentile(self.L120, 25)), float(np.percentile(self.L120, 80))

    def means(self, b):
        if b not in self._means:
            self._means[b] = block_means(self.lin, b)
        return self._means[b]

    def tok_means(self, b):
        """The linear block means the 4-token decision sees: plain, or star-guarded trimmed means."""
        if not self.star_guard:
            return self.means(b)
        if b not in self._tok_means:
            self._tok_means[b] = trimmed_block_means(self.lin, b, self.star_guard['frac'], self.star_guard['min_px'])
        return self._tok_means[b]

    def tokens(self, b):
        tok, L = quantize_tokens(self.tok_means(b), self.p25, self.p80)
        if self.star_guard and self.star_guard.get('ink_floor'):
            floor = lin_to_srgb(self.tok_means(b)).max(axis=-1) < self.star_guard['ink_floor']
            tok = np.where(floor, INK, tok).astype(np.int8)
        return tok, L

    def base(self, b, mode):
        """Brightness-independent stage data. tok/tok2 -> (tok, L); c8/c32/full -> sRGB uint8."""
        key = (b, mode)
        if key in self._base:
            return self._base[key]
        if mode in ('tok', 'tok2'):
            val = self.tokens(b)
        else:
            srgb = lin_to_srgb(self.means(b))
            if self.name in GRADED:
                srgb = grade_city(srgb)
            srgb = to_u8(srgb)
            if mode == 'c8':
                srgb = median_cut(srgb, 8); self.guard[key] = median_cut.last_guard
            elif mode == 'c32':
                srgb = median_cut(srgb, 32); self.guard[key] = median_cut.last_guard
            val = srgb
        self._base[key] = val
        return val

    def render(self, b, mode, bright):
        """Stage image at grid resolution (H/b, W/b, 3) uint8."""
        if mode == 'tok':
            tok, _ = self.base(b, mode)
            return token_lut(bright)[tok].astype(np.uint8)
        if mode == 'tok2':
            tok, L = self.base(b, mode)
            return token_lut(bright, True)[tok, two_level_mask(tok, L)].astype(np.uint8)
        return scale(self.base(b, mode), bright)


# =============================================================================================
# Earth quadtree
# =============================================================================================
def sat_block_stats(Y, bs):
    """Per-block mean and variance of Y for aligned blocks of size bs, via summed-area tables."""
    S1 = np.zeros((H + 1, W + 1)); S1[1:, 1:] = Y.cumsum(0).cumsum(1)
    S2 = np.zeros((H + 1, W + 1)); S2[1:, 1:] = (Y * Y).cumsum(0).cumsum(1)
    ys = np.arange(0, H + 1, bs); xs = np.arange(0, W + 1, bs)
    def box(S):
        G = S[np.ix_(ys, xs)]
        return G[1:, 1:] - G[:-1, 1:] - G[1:, :-1] + G[:-1, :-1]
    n = bs * bs
    m = box(S1) / n
    v = np.maximum(box(S2) / n - m * m, 0.0)
    return m, v


def bake_quadtree(earth, manifest):
    t0 = time.time()
    Y = 0.2126 * earth.lin[..., 0] + 0.7152 * earth.lin[..., 1] + 0.0722 * earth.lin[..., 2]
    Yf = median_filter(Y, size=5)            # a <= 4x4 star never earns a split
    frame = float(W * H)
    score = []
    for d in range(QT_MAXD):
        bs = QT_BS[d]
        _, var = sat_block_stats(Yf, bs)
        score.append(var * (bs * bs))          # luminance variance × leaf area
    # colour sources at 5-px resolution for depths 0–4 (uniform inside every 5-px cell)
    tok_px5, tok_d = [], []
    for d in range(3):
        tok, _ = earth.tokens(QT_BS[d]); tok_d.append(tok)
        tok_px5.append(np.repeat(np.repeat(tok, QT_CS[d], 0), QT_CS[d], 1))
    c8_15 = earth.base(15, 'c8')                                    # the 8-colour palette (median-cut on 15-px means)
    c8_px5_d3 = np.repeat(np.repeat(c8_15, 3, 0), 3, 1)
    c8_px5_d4 = nearest_palette(to_u8(lin_to_srgb(earth.means(5))), c8_15)   # 5-px means in the same 8 colours
    real = earth.srgb

    D = np.zeros((H // 5, W // 5), np.int8)
    gens, splits = [D.copy()], []

    def S_of(D):
        return float(np.minimum(D, QT_MAXD).mean()) / QT_MAXD

    def split_until(D, target):
        cand = []
        for d in range(QT_MAXD):
            cs = QT_CS[d]
            m = D[::cs, ::cs] == d
            if m.any():
                ij = np.argwhere(m)
                cand.append(np.column_stack([score[d][m], np.full(len(ij), d), ij]))
        cand = np.concatenate(cand) if cand else np.zeros((0, 4))
        order = np.lexsort((cand[:, 3], cand[:, 2], cand[:, 1], -cand[:, 0]))   # score desc, then d,i,j
        cand = cand[order]
        dS = np.array([QT_BS[int(d)] ** 2 for d in cand[:, 1]]) / QT_MAXD / frame
        s0 = S_of(D)
        if s0 >= target:
            return cand[:0, 1:].astype(np.int16)
        n = min(int(np.searchsorted(s0 + np.cumsum(dS), target)) + 1, len(cand))
        chosen = cand[:n]
        for d in range(QT_MAXD):
            sel = chosen[chosen[:, 1] == d]
            if len(sel) == 0:
                continue
            cs = QT_CS[d]
            g = np.zeros((D.shape[0] // cs, D.shape[1] // cs), bool)
            g[sel[:, 2].astype(int), sel[:, 3].astype(int)] = True
            D[np.repeat(np.repeat(g, cs, 0), cs, 1)] = d + 1
        return chosen[:, 1:].astype(np.int16)

    for g in range(1, 13):
        D = D.copy(); splits.append(split_until(D, QT_TARGETS[g - 1])); gens.append(D)
    D = D.copy(); D[D < 3] = 3; splits.append(split_until(D, QT_G13_TARGET)); gens.append(D)   # g13: force >= 15 px
    D = D.copy(); D[:] = 5; splits.append(np.zeros((0, 3), np.int16)); gens.append(D)           # g14: real everywhere

    print('  quadtree generations (S = mean(depth)/4, change = fraction of frame whose depth changed;')
    print('  space = non-ink TOKEN leaves at depths 0/1/2 inside rows 8-9, i.e. grey blocks drawn in space):')
    print('    gen  target   S        change   bright   leaves d0..d5                          space d0/d1/d2')
    rows, images = [], []
    for g, D in enumerate(gens):
        bright = 100.0 if g == 14 else 70.0 + 30.0 * (0.2 * g / 3.2)
        lut = token_lut(bright)
        small = np.zeros((H // 5, W // 5, 3), np.uint8)
        for d in range(3):
            m = D == d
            small[m] = lut[tok_px5[d]][m]
        m = D == 3; small[m] = scale(c8_px5_d3, bright)[m]
        m = D == 4; small[m] = scale(c8_px5_d4, bright)[m]
        full = np.repeat(np.repeat(small, 5, 0), 5, 1)
        m5 = np.repeat(np.repeat(D == 5, 5, 0), 5, 1)
        if m5.any():
            full[m5] = scale(real, bright)[m5]
        images.append(full)
        fn = f'earth_qt_g{g:02d}.png'
        Image.fromarray(full, 'RGB').save(os.path.join(OUT, fn))
        S = S_of(D) if g < 14 else 1.0
        change = float((D != gens[g - 1]).mean()) if g else 0.0
        counts = [int((D[::QT_CS[d], ::QT_CS[d]] == d).sum()) for d in range(5)] + [int((D == 5).sum() * 25)]
        target = '' if g == 0 else (QT_TARGETS[g - 1] if g <= 12 else (QT_G13_TARGET if g == 13 else 1.0))
        assert g == 0 or change >= 0.02, f'g{g}: change {change:.3f} < 2 %'
        assert g == 14 or int(D.max()) <= QT_MAXD, f'g{g}: depth 5 before g14'
        space, space_pos = [], []
        for d in range(3):
            cs, bs = QT_CS[d], QT_BS[d]
            r0 = 840 // bs
            m = (D[::cs, ::cs] == d)[r0:] & (tok_d[d][r0:] != INK)
            space.append(int(m.sum()))
            space_pos += [dict(depth=d, row=round((int(r) + r0) * bs / 120 + 1, 2), col=round(int(c) * bs / 120 + 1, 2))
                          for r, c in np.argwhere(m)]
        print(f'    {g:3d}  {str(target):6}  {S:.4f}   {change * 100:5.1f} %   {bright:5.1f}   {str(counts):40s} {space}')
        rows.append(dict(gen=g, target=(None if target == '' else target), S=round(S, 5), change=round(change, 5),
                         brightness=round(bright, 4), leaves=counts, space_nonink_token_leaves=space,
                         space_nonink_positions=space_pos))
        manifest['files'][fn] = dict(photo='earth', grid=[W, H], block='quadtree', mode='qt', brightness=round(bright, 4),
                                     gen=g, S=round(S, 5), change=round(change, 5))
    bad_space = [r['gen'] for r in rows[:14] if r['space_nonink_token_leaves'] != [0, 0, 0]]
    assert not bad_space, f'non-ink token leaves in rows 8-9 at generations {bad_space}'
    # g13 -> g14 must visibly change rows 3-7: >= 30 % of their pixels move by more than 8 sRGB levels
    diff = np.abs(images[14][240:840].astype(np.int16) - images[13][240:840].astype(np.int16)).max(axis=2)
    frac_changed = float((diff > 8).mean())
    print(f'  g13 -> g14: {frac_changed * 100:.1f} % of pixels in rows 3-7 change by > 8 sRGB levels (need >= 30 %)')
    assert frac_changed >= 0.30, f'g13->g14 changes only {frac_changed:.3f} of rows 3-7'
    np.savez_compressed(os.path.join(OUT, 'earth_qt_depths.npz'), depths=np.stack(gens),
                        **{f'splits_g{g + 1:02d}': s for g, s in enumerate(splits)})
    manifest['quadtree'] = dict(targets=QT_TARGETS, g13_target=QT_G13_TARGET, depth_block=QT_BS, max_depth_before_g14=QT_MAXD,
                                score='mean(depth)/4', colour_by_depth='0-2 tokens, 3-4 the 8-colour palette, 5 real',
                                brightness='70 + 30*(0.2g/3.2), g14 = 100', ranking='variance of median_filter(Y, 5) × area',
                                g13_to_g14_rows3_7_changed=round(frac_changed, 4), generations=rows,
                                luminance='Rec.709 Y of linear light', depths_file='earth_qt_depths.npz')
    print(f'  quadtree done in {time.time() - t0:.1f} s')
    return gens


# =============================================================================================
# gates and check images
# =============================================================================================
def face_grid_overlay(face):
    im = Image.fromarray(face.srgb, 'RGB').convert('RGBA')
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    font = ImageFont.truetype(FONT, 22)
    for x in range(0, W + 1, 120):
        dr.line([(x, 0), (x, H)], fill=(255, 255, 255, 110), width=1)
    for y in range(0, H + 1, 120):
        dr.line([(0, y), (W, y)], fill=(255, 255, 255, 110), width=1)
    dr.rectangle([960, 360, 1079, 479], outline=(232, 97, 58, 255), width=4)
    dr.rectangle([0, 380, W, 470], outline=(60, 220, 60, 255), width=2)
    dr.text((1090, 384), 'eye band y 380-470', fill=(60, 220, 60, 255), font=font)
    dr.text((964, 364), 'ORIGIN c9 r4', fill=(232, 97, 58, 255), font=font)
    for c in range(16):
        dr.text((c * 120 + 4, 2), str(c + 1), fill=(255, 255, 0, 255), font=font)
    for r in range(9):
        dr.text((4, r * 120 + 24), f'r{r + 1}', fill=(255, 255, 0, 255), font=font)
    for y in range(300, 560, 20):
        dr.line([(0, y), (40, y)], fill=(0, 255, 255, 255), width=1)
        dr.text((44, y - 10), str(y), fill=(0, 255, 255, 255), font=ImageFont.truetype(FONT, 14))
    Image.alpha_composite(im, ov).convert('RGB').save(os.path.join(OUT, 'check_face_grid.png'))


def run_gates(photos, manifest):
    res = {}
    print('\nGATES')
    # (a) face origin cell + map
    face = photos['face']
    tok, _ = face.tokens(120)
    print_tokmap('(a) face 120 px', tok)
    counts = {TOKEN_CH[t]: int((tok == t).sum()) for t in range(4)}
    origin = TOKEN_CH[tok[3, 8]]
    ok = origin == 'E'
    print(f'  (a) origin cell (col 9,row 4) = {origin}  -> {"PASS" if ok else "FAIL"};  counts {counts};  '
          f'window T={face.window[1]}  P25={face.p25:.3f} P80={face.p80:.3f}  (eye line: view check_face_grid.png)')
    res['a_origin_ember'] = ok
    # (b) 2x2 of the origin cell under the two-level rule
    tok60, L60 = face.base(60, 'tok2')
    hi = two_level_mask(tok60, L60)
    img60_55 = face.render(60, 'tok2', 55)
    quads = []
    for r in (6, 7):
        for c in (16, 17):
            t = TOKEN_CH[tok60[r, c]]; lvl = 'hi' if hi[r, c] else 'lo'
            quads.append((f'{t}-{lvl}', '#%02X%02X%02X' % tuple(img60_55[r, c])))
    distinct = len(set(q[0] for q in quads))
    ok = distinct >= 3
    print(f'  (b) origin 2x2 at 60 px (b55): {quads} -> {distinct} distinct -> {"PASS" if ok else "FAIL"}')
    res['b_quadrants'] = dict(quadrants=quads, distinct=distinct, ok=ok)
    # (d) earth rotated 120-px map
    earth = photos['earth']
    tok, _ = earth.tokens(120)
    print_tokmap('(d) earth 120 px (rotated 180)', tok)
    band_rows = [r + 1 for r in range(9) if ((tok[r] == PAPER) | (tok[r] == SLATE)).sum() >= 8]
    paper_rows = sorted(set(int(r) + 1 for r in np.argwhere(tok == PAPER)[:, 0]))
    L120 = earth.L120
    bad = []
    for r, c in np.argwhere(tok[7:9] != INK) + [7, 0]:
        cell = earth.srgb[r * 120:(r + 1) * 120, c * 120:(c + 1) * 120]
        mx = cell.reshape(-1, 3).max(0)
        bad.append(dict(row=int(r) + 1, col=int(c) + 1, token=TOKEN_CH[tok[r, c]], L=round(float(L120[r, c]), 4),
                        cell_mean_srgb=[round(float(v), 1) for v in cell.reshape(-1, 3).mean(0)],
                        cell_max_srgb=[int(v) for v in mx],
                        cause='star (bright point in a black cell)' if mx.max() > 150 else 'diffuse limb glow'))
    rows89_ink = len(bad) == 0
    ok = rows89_ink and all(r in band_rows for r in (3, 4, 5, 6))
    non_ink = float((tok != INK).mean())
    print(f'  (d) paper rows {paper_rows}; paper/slate-majority rows {band_rows}; rows 8-9 all ink: {rows89_ink}; '
          f'non-ink {non_ink * 100:.0f} %; P25={earth.p25:.4f} P80={earth.p80:.4f} -> {"PASS" if ok else "FAIL"}')
    for b_ in bad:
        print(f'      non-ink cell in rows 8-9: row {b_["row"]} col {b_["col"]} = {b_["token"]}, L {b_["L"]} vs P25 {earth.p25:.4f}; '
              f'cell mean sRGB {b_["cell_mean_srgb"]}, max {b_["cell_max_srgb"]} -> {b_["cause"]}')
    res['d_earth_band'] = dict(paper_rows=paper_rows, band_rows=band_rows, rows_8_9_ink=rows89_ink, offending=bad, ok=ok)
    # (e) city maps at 120/60/30
    city = photos['city']
    tok, _ = city.tokens(120)
    print_tokmap('(e) city 120 px', tok)
    e = {}
    for b in (120, 60, 30):
        t, _ = city.tokens(b)
        lit = (t == PAPER) | (t == EMBER)
        per_row = lit.sum(1)                                   # at the b-px grid
        rows120 = np.add.reduceat(per_row, np.arange(0, t.shape[0], 120 // b))   # fold to 120-px rows
        total = int(lit.sum())
        inside = int(rows120[5:8].sum())
        pk = int(np.argmax(rows120))
        lo, hi = pk, pk                                                        # maximal run of non-empty rows around the peak
        while lo > 0 and rows120[lo - 1] > 0: lo -= 1
        while hi < 8 and rows120[hi + 1] > 0: hi += 1
        band = list(range(lo + 1, hi + 2))
        contiguous = True                                                       # by construction; empty rows end the band
        centroid = float((rows120 * np.arange(1, 10)).sum() / max(total, 1))
        outside = 1.0 - sum(int(rows120[r - 1]) for r in band) / max(total, 1)
        e[b] = dict(paper=int((t == PAPER).sum()), ember=int((t == EMBER).sum()), per_row120=[int(x) for x in rows120],
                    band_rows=band, contiguous=contiguous, centroid_row=round(centroid, 2),
                    outside_band=round(outside, 3), in_rows_6_8=round(inside / max(total, 1), 3))
        print(f'  (e) city {b:3d} px: paper {e[b]["paper"]}, ember {e[b]["ember"]}; lit cells per 120-px row {e[b]["per_row120"]}; '
              f'band rows {band} (centroid row {centroid:.2f}, {outside * 100:.0f} % of lit cells outside); '
              f'{e[b]["in_rows_6_8"] * 100:.0f} % inside rows 6-8')
    # "one contiguous lit band": the band = the maximal run of rows holding any paper/ember cell around the densest
    # row; its centroid must lie in rows 2-8 and < 25 % of the paper+ember cells may lie outside it.
    ok = all(e[b]['contiguous'] and 2.0 <= e[b]['centroid_row'] <= 8.0 and e[b]['outside_band'] < 0.25 for b in e)
    print(f'  (e) -> {"PASS" if ok else "FAIL"} (one contiguous lit band, centroid in rows 2-8, < 25 % of lit cells outside it, at 120/60/30 px)')
    res['e_city_band'] = dict(e, ok=ok)
    manifest['gates'] = res
    manifest['notes'] = [
        'face T=60 kept: eye line measured at y ~440-450 on check_face_grid.png (band 380-470); origin cell (col 9,row 4) is ember.',
        'earth T=98 kept, STAR GUARD on (trimmed mean, brightest max(0.5 %, 16 px) of each cell excluded from the token '
        'decision): the star cells no longer quantize to slate at any token depth. Gate (d) rows 8-9 all-ink still fails by '
        'exactly one cell, now (8,4) = the limb glow dipping into row 8 at the left: the percentile rule fixes 36 ink cells, '
        'the frame has 37 dark cells (32 space + 5 limb-edge cells in rows 6-7 on the right, where the tilted limb sits '
        'higher), so the brightest dark cell is always slate; scanned every T 84-120 with the guard, (8,4) fails at all of '
        'them (T <= 90 adds (8,3)/(8,5), T >= 120 adds (9,9)). The copy block (y <= 940, rows 7-8) still sits on glow and ink.',
        'city = Los Angeles aerial (1444723121867), T=200, ungraded.',
    ]
    return res


def contact_sheet(tiles):
    cols = 5
    tw, th = 480, 270
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw, rows * th), (24, 24, 28))
    dr = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(FONT, 18)
    for i, (label, arr) in enumerate(tiles):
        im = Image.fromarray(arr, 'RGB').resize((tw, th), Image.NEAREST)
        x, y = (i % cols) * tw, (i // cols) * th
        sheet.paste(im, (x, y))
        dr.rectangle([x, y, x + 8 + 9 * len(label) + 4, y + 24], fill=(0, 0, 0))
        dr.text((x + 4, y + 2), label, fill=(255, 220, 0), font=font)
    sheet.save(os.path.join(OUT, 'check_stages.png'))


# =============================================================================================
def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    manifest = dict(grid=dict(cell=120, cols=16, rows=9, blocks=BLOCKS, frame=[W, H]),
                    palette=dict(ink='#0B0B0E', slate='#3A3F4B', paper='#F3EFE7', ember='#E8613A',
                                 paper_pinned='#868380', paper_pinned_low='#615F5C'),
                    photos={}, files={})
    photos = {n: Photo(n) for n in SOURCES}
    expected = {f'{n}_{b}_{m}_b{br}.png' for n, st in STAGES.items() for b, m, br in st} | {f'earth_qt_g{g:02d}.png' for g in range(15)}
    for f in glob.glob(os.path.join(OUT, '*.png')):
        if os.path.basename(f) not in expected and not os.path.basename(f).startswith('check_'):
            os.remove(f); print('  removed stale', os.path.basename(f))
    tiles = []
    print('STAGES')
    for name, stages in STAGES.items():
        p = photos[name]
        tok120, _ = p.tokens(120)
        manifest['photos'][name] = dict(file=SOURCES[name]['file'], source_size=list(p.src_size),
                                        rotate180=SOURCES[name]['rotate'], window=list(p.window),
                                        P25=round(p.p25, 5), P80=round(p.p80, 5), tokmap120=tokmap_strings(tok120),
                                        graded=name in GRADED, star_guard=SOURCES[name].get('star_guard'))
        for b, mode, bright in stages:
            img = p.render(b, mode, bright)
            fn = f'{name}_{b}_{mode}_b{bright}.png'
            Image.fromarray(img, 'RGB').save(os.path.join(OUT, fn))
            manifest['files'][fn] = dict(photo=name, grid=[img.shape[1], img.shape[0]], block=b, mode=mode, brightness=bright)
            tiles.append((fn[:-4], img))
            gtxt = ''
            if (b, mode) in p.guard:
                npal, worst = p.guard[(b, mode)]
                gtxt = f'   palette guard: {npal} colours, worst {worst:5.1f} sRGB from a real mean (<= {PALETTE_GUARD:.0f})'
                manifest['files'][fn]['palette_guard'] = dict(colours=npal, worst_distance=worst)
            print(f'  {fn:28s} {img.shape[1]:4d}x{img.shape[0]:<4d}{gtxt}')
    gens = bake_quadtree(photos['earth'], manifest)
    for g in range(15):
        tiles.append((f'earth_qt_g{g:02d}', np.asarray(Image.open(os.path.join(OUT, f'earth_qt_g{g:02d}.png')))))
    run_gates(photos, manifest)
    face_grid_overlay(photos['face'])
    contact_sheet(tiles)
    with open(os.path.join(OUT, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=1)
    print(f'\nwrote {len(manifest["files"])} stage files + manifest.json, check_face_grid.png, check_stages.png '
          f'to {OUT} in {time.time() - t0:.1f} s')


if __name__ == '__main__':
    main()
