"""Single source of truth for timing. Music and picture both read from here,
so every cut, reveal and hit lands on the same beat.

96 BPM, 4/4 -> one beat = 0.625 s, one bar = 2.5 s. The film is 30 bars (75 s).
"""

BPM = 96
BEAT = 60.0 / BPM          # 0.625 s
BAR = 4 * BEAT             # 2.5 s
N_BARS = 30
DURATION = N_BARS * BAR    # 75.0 s
TAIL = 3.0                 # audio reverb tail rendered past the last frame (then faded)


def t(bar, beat=0.0):
    """Seconds at a given bar (0-based) and beat offset inside that bar."""
    return (bar * 4 + beat) * BEAT


# ---------------------------------------------------------------- Act I: one pixel
PIXEL_APPEAR = t(0, 2)                       # 1.25  the first pixel
LINE1 = (t(0, 2.6), t(1, 3.4))               # 一切，从一个像素开始。
EXPAND = t(2, 0)                             # 5.0   pixel opens into a square canvas
SUBDIV = [t(2, 1), t(2, 2), t(2, 3), t(3, 0), t(3, 1)]   # 2x2 .. 32x32
LINE2 = (t(2, 2.1), t(3, 3.2))               # 分辨率每提升一次……
WIPE1 = (t(3, 3.0), t(4, 0))                 # pixel-bloom wipe dark -> ivory

# ---------------------------------------------------------------- Act II: capabilities
CAPS = [t(4), t(6), t(8), t(10), t(12)]     # 读 想 写 做 信  (each 2 bars)
CAP_LEN = 2 * BAR
ALIGN_SNAP = t(13, 0)                        # scattered pixels snap into alignment

# ---------------------------------------------------------------- Act III: the ceiling
CEIL = t(14)
COLUMN_RISE = [t(14, 0), t(14, 1), t(14, 2), t(14, 3), t(15, 0)]   # Claude 1..5
COLUMN_LAST = (t(16, 0), t(17, 3.0))         # Opus 5.5 rises and breaks through
CEIL_LINE1 = (t(14, 0.4), t(15, 3.6))
CEIL_LINE2 = (t(16, 0.2), t(17, 2.6))
BREAK = t(17, 3.0)                           # 44.375 the ceiling shatters
DROP = t(18)                                 # 45.0

# ---------------------------------------------------------------- Act IV: the real world
MONTAGE = [t(18), t(19), t(20), t(21), t(22)]   # Bahamas, Karakoram, Riyadh, Everest, Earth
ZOOM_OUT_LEN = 0.75                          # each world shrinks into one pixel of the next
EARTH_LINE = (t(23, 0), t(25, 0) - 0.35)     # 从一个像素，到整个世界。

# ---------------------------------------------------------------- Act V: end card
SHRINK = (t(25, 0), t(25, 3.0))              # the earth folds back into a single pixel
TYPE = (t(26, 0), t(26, 0) + 15 * 0.075)     # "Claude Opus 5.5" typed by the pixel
TAGLINE = t(27, 0)
CREDITS = t(28, 0)
FADE_OUT = (t(29, 2.0), DURATION)
