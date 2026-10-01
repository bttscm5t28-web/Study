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
import numpy as np
from PIL import Image, ImageDraw, ImageFont

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
    'city':   dict(file='1474181487882-5abf3f0ba6c2.jpg', window=(0, 200), rotate=False),
    'earth':  dict(file='1451187580459-43490279c0fa.jpg', window=(0, 98), rotate=True),
    'sky':    dict(file='1444703686981-a3abbc4d4fe3_2880.jpg', window=(258, 840), rotate=False),
}

# ---- stages: (block, mode, brightness) -------------------------------------------------------
STAGES = {
    'face':   [(120, 'tok', 55), (60, 'tok2', 55), (60, 'tok2', 65), (30, 'tok', 75), (15, 'c8', 85),
               (5, 'c32', 92), (1, 'full', 100), (120, 'tok', 70)],
    'people': [(120, 'tok', 70), (60, 'tok2', 80), (30, 'tok', 90), (1, 'full', 100)],
    'city':   [(120, 'tok', 55), (60, 'tok2', 62), (30, 'tok', 70), (30, 'c8', 77), (15, 'c8', 85),
               (5, 'c32', 92), (5, 'full', 96), (1, 'full', 100),
               (5, 'c32', 90), (15, 'c8', 83), (60, 'tok2', 76), (120, 'tok', 70)],
    'earth':  [(120, 'tok', 55)],
    'sky':    [(1, 'full', 100)],
}
GRADED = {'city'}   # −25 % saturation, blue 10 % toward slate's blue, on the c8/c32/full stages

# ---- quadtree (§3 S10, §5.6) ---------------------------------------------------------------
QT_TARGETS = [0.03, 0.05, 0.08, 0.12, 0.17, 0.23, 0.30, 0.38, 0.47, 0.57, 0.68, 0.80]
QT_G13_TARGET = 0.90
QT_CS = [24, 12, 6, 3, 1]            # leaf size in 5-px cells for depths 0–4
QT_BS = [120, 60, 30, 15, 5, 1]      # block size per depth


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
    return np.asarray(q.convert('RGB'))


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
        self._base = {}
        # frozen 4-token thresholds from the 144 block means at 120 px
        self.L120 = oklab(self.means(120))[0]
        self.p25, self.p80 = float(np.percentile(self.L120, 25)), float(np.percentile(self.L120, 80))

    def means(self, b):
        if b not in self._means:
            self._means[b] = block_means(self.lin, b)
        return self._means[b]

    def tokens(self, b):
        return quantize_tokens(self.means(b), self.p25, self.p80)

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
                srgb = median_cut(srgb, 8)
            elif mode == 'c32':
                srgb = median_cut(srgb, 32)
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
    frame = float(W * H)
    score = []
    for d in range(5):
        bs = QT_BS[d]
        _, var = sat_block_stats(Y, bs)
        score.append(var * (bs * bs))          # luminance variance × leaf area
    # colour sources at 5-px resolution for depths 0–4 (uniform inside every 5-px cell)
    tok_px5 = []
    for d in range(3):
        tok, _ = earth.tokens(QT_BS[d])
        tok_px5.append(np.repeat(np.repeat(tok, QT_CS[d], 0), QT_CS[d], 1))
    c8_px5 = np.repeat(np.repeat(earth.base(15, 'c8'), 3, 0), 3, 1)
    c32_px5 = earth.base(5, 'c32')
    real = earth.srgb

    D = np.zeros((H // 5, W // 5), np.int8)
    gens, splits = [D.copy()], []

    def S_of(D):
        return float(D.mean()) / 5.0

    def split_until(D, target):
        cand = []
        for d in range(5):
            cs = QT_CS[d]
            m = D[::cs, ::cs] == d
            if m.any():
                ij = np.argwhere(m)
                cand.append(np.column_stack([score[d][m], np.full(len(ij), d), ij]))
        cand = np.concatenate(cand) if cand else np.zeros((0, 4))
        order = np.lexsort((cand[:, 3], cand[:, 2], cand[:, 1], -cand[:, 0]))   # score desc, then d,i,j
        cand = cand[order]
        dS = np.array([QT_BS[int(d)] ** 2 for d in cand[:, 1]]) / 5.0 / frame
        s0 = S_of(D)
        if s0 >= target:
            return cand[:0]
        n = int(np.searchsorted(s0 + np.cumsum(dS), target)) + 1
        n = min(n, len(cand))
        chosen = cand[:n]
        for d in range(5):
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
    D = D.copy(); D[D < 4] = 4; splits.append(split_until(D, QT_G13_TARGET)); gens.append(D)   # g13
    D = D.copy(); D[:] = 5; splits.append(np.zeros((0, 3), np.int16)); gens.append(D)           # g14

    # compose and save
    print('  quadtree generations (S = resolution score, change = fraction of frame whose depth changed):')
    print('    gen  target   S        change   bright   leaves d0..d5')
    rows = []
    for g, D in enumerate(gens):
        bright = 100.0 if g == 14 else 55.0 + 45.0 * (0.2 * g / 3.2)
        lut = token_lut(bright)
        small = np.zeros((H // 5, W // 5, 3), np.uint8)
        for d in range(3):
            m = D == d
            small[m] = lut[tok_px5[d]][m]
        m = D == 3; small[m] = scale(c8_px5, bright)[m]
        m = D == 4; small[m] = scale(c32_px5, bright)[m]
        full = np.repeat(np.repeat(small, 5, 0), 5, 1)
        m5 = np.repeat(np.repeat(D == 5, 5, 0), 5, 1)
        if m5.any():
            full[m5] = scale(real, bright)[m5]
        fn = f'earth_qt_g{g:02d}.png'
        Image.fromarray(full, 'RGB').save(os.path.join(OUT, fn))
        S = S_of(D)
        change = float((D != gens[g - 1]).mean()) if g else 0.0
        counts = [int((D[::QT_CS[d], ::QT_CS[d]] == d).sum()) for d in range(5)] + [int((D == 5).sum() * 25)]
        target = '' if g == 0 else (QT_TARGETS[g - 1] if g <= 12 else (QT_G13_TARGET if g == 13 else 1.0))
        flag = '' if (g == 0 or change >= 0.02) else '   <-- FAIL (< 2 %)'
        print(f'    {g:3d}  {str(target):6}  {S:.4f}   {change * 100:5.1f} %   {bright:5.1f}   {counts}{flag}')
        rows.append(dict(gen=g, target=(None if target == '' else target), S=round(S, 5), change=round(change, 5),
                         brightness=round(bright, 4), leaves=counts))
        manifest['files'][fn] = dict(photo='earth', grid=[W, H], block='quadtree', mode='qt', brightness=round(bright, 4),
                                     gen=g, S=round(S, 5), change=round(change, 5))
    np.savez_compressed(os.path.join(OUT, 'earth_qt_depths.npz'), depths=np.stack(gens),
                        **{f'splits_g{g + 1:02d}': s for g, s in enumerate(splits)})
    manifest['quadtree'] = dict(targets=QT_TARGETS, g13_target=QT_G13_TARGET, depth_block=QT_BS, generations=rows,
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
    rows89_ink = bool((tok[7:9] == INK).all())
    paper_rows = sorted(set(int(r) + 1 for r in np.argwhere(tok == PAPER)[:, 0]))
    ok = rows89_ink and all(r in band_rows for r in (3, 4, 5, 6))
    non_ink = float((tok != INK).mean())
    print(f'  (d) paper rows {paper_rows}; paper/slate-majority rows {band_rows}; rows 8-9 all ink: {rows89_ink}; '
          f'non-ink {non_ink * 100:.0f} % -> {"PASS" if ok else "FAIL"}')
    res['d_earth_band'] = dict(paper_rows=paper_rows, band_rows=band_rows, rows_8_9_ink=rows89_ink, ok=ok)
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
        e[b] = dict(paper=int((t == PAPER).sum()), ember=int((t == EMBER).sum()),
                    per_row120=[int(x) for x in rows120], in_rows_6_8=round(inside / max(total, 1), 3))
        print(f'  (e) city {b:3d} px: paper {e[b]["paper"]}, ember {e[b]["ember"]}; lit cells per 120-px row {e[b]["per_row120"]}; '
              f'{e[b]["in_rows_6_8"] * 100:.0f} % inside rows 6-8')
    ok = all(e[b]['in_rows_6_8'] >= 0.8 for b in e)
    print(f'  (e) -> {"PASS" if ok else "FAIL"} (>= 80 % of paper+ember cells inside rows 6-8 at every block size)')
    res['e_city_band'] = dict(e, ok=ok)
    manifest['gates'] = res
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
    tiles = []
    print('STAGES')
    for name, stages in STAGES.items():
        p = photos[name]
        tok120, _ = p.tokens(120)
        manifest['photos'][name] = dict(file=SOURCES[name]['file'], source_size=list(p.src_size),
                                        rotate180=SOURCES[name]['rotate'], window=list(p.window),
                                        P25=round(p.p25, 5), P80=round(p.p80, 5), tokmap120=tokmap_strings(tok120),
                                        graded=name in GRADED)
        for b, mode, bright in stages:
            img = p.render(b, mode, bright)
            fn = f'{name}_{b}_{mode}_b{bright}.png'
            Image.fromarray(img, 'RGB').save(os.path.join(OUT, fn))
            manifest['files'][fn] = dict(photo=name, grid=[img.shape[1], img.shape[0]], block=b, mode=mode, brightness=bright)
            tiles.append((fn[:-4], img))
            print(f'  {fn:28s} {img.shape[1]:4d}x{img.shape[0]:<4d}')
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
