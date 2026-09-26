"""所有场景共用的配色、组件和“旁白同步”基类。"""
import json
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from manim import *

from tts import synth

ROOT = Path(__file__).resolve().parent
SUBS_DIR = ROOT / "build" / "subs"

FONT = "Noto Sans CJK SC"

BG = "#0D1117"
FG = "#E6EDF3"
MUTED = "#8B949E"
DIM = "#30363D"
PANEL = "#161B22"
Q_COL = "#4FC3F7"   # 查询 Query
K_COL = "#FFB74D"   # 键 Key
V_COL = "#81C784"   # 值 Value
HL = "#F06292"      # 强调色（“它”、“小猫”）
PE_COL = "#B39DDB"  # 位置编码
W_COL = "#FFD54F"   # 注意力权重
EMB_COL = "#90CAF9" # 词向量

# 内容区域下沿：再往下留给字幕
CONTENT_BOTTOM = -2.75

SENTENCE = ["小猫", "没有", "过", "马路", "因为", "它", "太累"]
IT = SENTENCE.index("它")
CAT = SENTENCE.index("小猫")


def T(text, size=32, color=FG, weight=NORMAL, **kw):
    return Text(text, font=FONT, font_size=size, color=color, weight=weight, **kw)


def token_box(word, color=FG, size=28, width=None, height=0.66, fill_opacity=0.08):
    label = T(word, size, color)
    w = width if width is not None else max(label.width + 0.4, 0.9)
    box = RoundedRectangle(
        corner_radius=0.12, width=w, height=height,
        stroke_color=color, stroke_width=2, fill_color=color, fill_opacity=fill_opacity,
    )
    label.move_to(box)
    return VGroup(box, label)


def token_row(words, size=28, buff=0.25, width=None, color=FG):
    width = width or max(max(T(w, size).width for w in words) + 0.4, 0.9)
    return VGroup(*[token_box(w, color=color, size=size, width=width) for w in words]).arrange(RIGHT, buff=buff)


def recolor_token(tok, color, fill_opacity=0.18):
    return tok.animate.set_stroke(color=color).set_fill(color, opacity=fill_opacity)


def vec_col(values, color, cell=0.24, horizontal=False, stroke=1.5):
    """一列（或一行）小方块表示向量，填充透明度对应数值大小。"""
    cells = VGroup()
    for v in values:
        sq = Square(side_length=cell, stroke_color=color, stroke_width=stroke)
        sq.set_fill(color, opacity=0.12 + 0.78 * float(np.clip(abs(v), 0, 1)))
        cells.add(sq)
    cells.arrange(RIGHT if horizontal else DOWN, buff=0)
    return cells


def matrix_grid(rows, cols, color, cell=0.22, values=None, seed=0):
    rng = np.random.default_rng(seed)
    if values is None:
        values = rng.uniform(0.05, 0.9, size=(rows, cols))
    grid = VGroup()
    for r in range(rows):
        for c in range(cols):
            sq = Square(side_length=cell, stroke_color=color, stroke_width=1)
            sq.set_fill(color, opacity=float(values[r][c]))
            sq.move_to([c * cell, -r * cell, 0])
            grid.add(sq)
    grid.center()
    return grid


def rand_vec(n, seed):
    rng = np.random.default_rng(seed)
    return rng.uniform(0.05, 1.0, n)


def arc_above(a, b, color=FG, width=3, opacity=1.0, height_scale=1.0):
    """在两个 token 上方画一条弧线。a、b 是 mobject。"""
    p1, p2 = a.get_top() + UP * 0.05, b.get_top() + UP * 0.05
    if p1[0] > p2[0]:
        p1, p2 = p2, p1
    dist = abs(p2[0] - p1[0])
    angle = -min(PI * 0.9, 0.55 * PI * height_scale + 0.02 * dist)
    return ArcBetweenPoints(p1, p2, angle=angle, stroke_color=color, stroke_width=width, stroke_opacity=opacity)


def arc_below(a, b, color=FG, width=3, opacity=1.0):
    p1, p2 = a.get_bottom() + DOWN * 0.05, b.get_bottom() + DOWN * 0.05
    if p1[0] > p2[0]:
        p1, p2 = p2, p1
    return ArcBetweenPoints(p1, p2, angle=PI * 0.55, stroke_color=color, stroke_width=width, stroke_opacity=opacity)


def softmax(x):
    x = np.asarray(x, dtype=float)
    e = np.exp(x - x.max())
    return e / e.sum()


class Seg:
    """一段旁白（可包含多句）。用来把动画卡在对应的句子上。"""

    def __init__(self, scene, start, starts, durs):
        self.scene, self.start, self.starts, self.durs = scene, start, starts, durs

    @property
    def now(self):
        return self.scene.renderer.time - self.start

    @property
    def total(self):
        return self.starts[-1] + self.durs[-1]

    def left(self, i=None):
        """距离第 i 句（默认最后一句）说完还剩多少秒。"""
        i = len(self.durs) - 1 if i is None else i
        return max(0.0, self.starts[i] + self.durs[i] - self.now)

    def until(self, i):
        """等到第 i 句开始。"""
        dt = self.starts[i] - self.now
        if dt > 1 / 30:
            self.scene.wait(dt)


class Narrated(Scene):
    GAP = 0.22

    def setup(self):
        self.camera.background_color = BG
        self.sub_events = []
        self.chapter_label = None

    @contextmanager
    def say(self, *lines, pad=0.25):
        start = self.renderer.time
        starts, durs, offset = [], [], 0.0
        for line in lines:
            path, dur = synth(line)
            self.add_sound(str(path), time_offset=offset)
            self.sub_events.append({"start": start + offset, "end": start + offset + dur, "text": line})
            starts.append(offset)
            durs.append(dur)
            offset += dur + self.GAP
        seg = Seg(self, start, starts, durs)
        yield seg
        remain = start + seg.total + pad - self.renderer.time
        if remain > 1 / 30:
            self.wait(remain)

    def chapter(self, num, title):
        bar = Rectangle(width=0.08, height=0.42, stroke_width=0, fill_color=HL, fill_opacity=1)
        label = VGroup(T(num, 22, HL, weight=BOLD), T(title, 22, MUTED)).arrange(RIGHT, buff=0.2)
        group = VGroup(bar, label).arrange(RIGHT, buff=0.18).to_corner(UL, buff=0.35)
        self.chapter_label = group
        return FadeIn(group, shift=RIGHT * 0.2)

    def clear_stage(self, run_time=0.6, keep=()):
        keep = set(keep) | ({self.chapter_label} if self.chapter_label else set())
        mobs = [m for m in self.mobjects if m not in keep]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=run_time)

    def tear_down(self):
        SUBS_DIR.mkdir(parents=True, exist_ok=True)
        out = {"scene": type(self).__name__, "duration": self.renderer.time, "events": self.sub_events}
        (SUBS_DIR / f"{type(self).__name__}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
