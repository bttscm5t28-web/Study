"""Transformer 讲解动画 —— 各章节场景。

渲染单个场景预览：  manim -ql scenes.py S07_AttentionMath
完整成片请用：      python build.py
"""
from common import *

SCENES = [
    "S00_Intro",
    "S01_Why",
    "S02_Architecture",
    "S03_Embedding",
    "S04_Position",
    "S05_QKV",
    "S06_AttentionMath",
    "S07_MultiHead",
    "S08_FFN",
    "S09_Decoder",
    "S10_Summary",
]


# ---------------------------------------------------------------- 00 开场
class S00_Intro(Narrated):
    def construct(self):
        names = ["ChatGPT", "机器翻译", "代码助手", "BERT", "语音识别", "文本摘要"]
        colors = [Q_COL, K_COL, V_COL, HL, PE_COL, W_COL]
        chips = VGroup()
        for i, (n, c) in enumerate(zip(names, colors)):
            ang = TAU * i / len(names) + PI / 6
            chips.add(token_box(n, color=c, size=30).move_to([4.3 * np.cos(ang), 2.2 * np.sin(ang), 0]))

        with self.say("从 ChatGPT 到机器翻译，", "今天最强大的 AI 模型，几乎都建立在同一个结构之上——") as s:
            self.play(LaggedStart(*[FadeIn(c, scale=0.6) for c in chips], lag_ratio=0.2), run_time=2.2)
            self.wait(max(0.0, s.left() - 1.3))
            self.play(*[c.animate.move_to(ORIGIN).scale(0.2).set_opacity(0) for c in chips], run_time=1.3)
        self.remove(chips)

        title = T("Transformer", 110, weight=BOLD).set_color_by_gradient(Q_COL, PE_COL, HL)
        with self.say("Transformer。"):
            self.play(GrowFromCenter(title), run_time=0.9)

        page = RoundedRectangle(corner_radius=0.08, width=6.4, height=3.3, stroke_width=0,
                                fill_color="#F5F5F0", fill_opacity=1)
        p_title = Tex(r"\textbf{Attention Is All You Need}", font_size=48, color="#111111")
        p_title.scale_to_fit_width(5.7)
        p_auth = Tex(r"Vaswani, Shazeer, Parmar, Uszkoreit, Jones, Gomez, Kaiser, Polosukhin",
                     font_size=20, color="#444444")
        p_auth.scale_to_fit_width(5.6)
        p_venue = Tex(r"NIPS 2017", font_size=26, color="#666666")
        p_lines = VGroup(*[Line(LEFT * 2.6, RIGHT * (2.6 - (1.6 if i == 3 else 0)), stroke_width=5, color="#C8C8C0")
                           for i in range(4)]).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        body = VGroup(p_title, p_auth, p_venue, p_lines).arrange(DOWN, buff=0.28).move_to(page)
        paper = VGroup(page, body).move_to(DOWN * 0.2)
        cn = T("“注意力，就是你所需要的一切”", 40, W_COL).next_to(paper, DOWN, buff=0.35)

        with self.say("它出自 2017 年谷歌团队的一篇论文，", "论文的名字翻译过来就是：", "“注意力，就是你所需要的一切”。") as s:
            self.play(title.animate.scale(0.5).to_edge(UP, buff=0.55), run_time=0.8)
            self.play(FadeIn(paper, shift=UP * 0.4), run_time=1.0)
            s.until(2)
            self.play(Write(cn), run_time=1.6)

        with self.say("接下来，我们用动画一步步把它拆开来看。"):
            self.play(FadeOut(paper), FadeOut(cn), title.animate.scale(1.6).move_to(ORIGIN), run_time=1.2)
            self.play(Circumscribe(title, color=W_COL, buff=0.3), run_time=1.5)
        self.play(FadeOut(title), run_time=0.6)


# ---------------------------------------------------------------- 01 为什么
class S01_Why(Narrated):
    def construct(self):
        self.play(self.chapter("01", "为什么需要 Transformer"))
        row = token_row(SENTENCE, size=28).move_to(UP * 0.1)
        rnn_label = T("RNN：像接力赛一样逐词传递", 30, K_COL).next_to(row, UP, buff=0.9)

        with self.say("在 Transformer 出现之前，处理句子主要靠循环神经网络，也就是 RNN。"):
            self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.2) for t in row], lag_ratio=0.1), run_time=1.5)
            self.play(FadeIn(rnn_label, shift=DOWN * 0.2))

        states = VGroup(*[Circle(radius=0.24, stroke_color=K_COL, stroke_width=2.5).next_to(t, DOWN, buff=0.55)
                          for t in row])
        ups = VGroup(*[Arrow(t.get_bottom(), c.get_top(), buff=0.05, stroke_width=2, color=MUTED,
                             max_tip_length_to_length_ratio=0.35) for t, c in zip(row, states)])
        links = VGroup(*[Arrow(states[i].get_right(), states[i + 1].get_left(), buff=0.04, color=K_COL,
                               stroke_width=3, max_tip_length_to_length_ratio=0.4) for i in range(6)])
        with self.say("它像接力赛一样，必须一个词一个词地按顺序读。") as s:
            step = max(0.35, (s.left() - 0.2) / 7)
            for i in range(7):
                anims = [GrowArrow(ups[i]), FadeIn(states[i], scale=0.5), row[i][0].animate.set_stroke(K_COL)]
                if i > 0:
                    anims += [GrowArrow(links[i - 1]), row[i - 1][0].animate.set_stroke(FG)]
                self.play(*anims, run_time=step)
            self.play(row[6][0].animate.set_stroke(FG), run_time=0.2)

        opac = [1.0, 0.72, 0.52, 0.37, 0.26, 0.17, 0.1]
        info = VGroup(*[Dot(states[i].get_center(), radius=0.15, color=HL).set_opacity(o) for i, o in enumerate(opac)])
        info_label = T("“小猫”的信息在传递中越来越弱", 26, HL).next_to(states, DOWN, buff=0.4)
        with self.say("句子一长，前面的信息就会在传递中逐渐丢失，"):
            self.play(row[0][0].animate.set_stroke(HL), LaggedStart(*[FadeIn(d, scale=0.3) for d in info], lag_ratio=0.3),
                      run_time=2.2)
            self.play(FadeIn(info_label, shift=UP * 0.2))

        slow = T("只能串行：第 7 步必须等前 6 步算完", 26, MUTED).move_to(info_label)
        with self.say("而且只能一步一步串行计算，训练起来很慢。"):
            self.play(FadeOut(info_label), FadeIn(slow))
            self.play(LaggedStart(*[Indicate(c, color=K_COL, scale_factor=1.3) for c in states], lag_ratio=0.35),
                      run_time=2.4)

        arcs = VGroup(*[arc_above(row[i], row[j], color=Q_COL, width=2, opacity=0.6)
                        for i in range(7) for j in range(i + 1, 7)])
        tf_label = T("Transformer：所有词同时直接相连", 30, Q_COL).next_to(row, DOWN, buff=0.8)
        with self.say("Transformer 换了一个思路：", "让句子中的每个词，都能同时直接看到其他所有词。") as s:
            self.play(FadeOut(VGroup(states, ups, links, info, slow, rnn_label)), row[0][0].animate.set_stroke(FG),
                      run_time=0.8)
            s.until(1)
            self.play(LaggedStart(*[Create(a) for a in arcs], lag_ratio=0.04), run_time=2.2)
            self.play(Write(tf_label), run_time=1.0)

        key = arc_above(row[IT], row[CAT], color=HL, width=6)
        big = T("注意力机制  Attention", 44, W_COL, weight=BOLD).move_to(tf_label)
        with self.say("再远的两个词，也只需要一步就能建立联系。", "这就是它的核心：注意力机制。") as s:
            self.play(arcs.animate.set_stroke(opacity=0.15), Create(key),
                      row[CAT][0].animate.set_stroke(HL), row[IT][0].animate.set_stroke(HL), run_time=1.4)
            s.until(1)
            self.play(ReplacementTransform(tf_label, big), run_time=1.0)
        self.clear_stage()


# ---------------------------------------------------------------- 02 整体结构
def arch_box(text, color, width=3.2, height=0.42, size=21):
    r = RoundedRectangle(corner_radius=0.08, width=width, height=height, stroke_color=color, stroke_width=2,
                         fill_color=color, fill_opacity=0.2)
    return VGroup(r, T(text, size, FG).move_to(r))


def norm_box(width=3.2):
    return arch_box("残差 & 层归一化", MUTED, width=width, height=0.28, size=16)


class S02_Architecture(Narrated):
    def construct(self):
        self.play(self.chapter("02", "整体结构"))
        ex, dx = -3.3, 3.0

        # 编码器
        e_in = T("输入：我 爱 学习", 20, MUTED).move_to([ex, -2.5, 0])
        e_emb = arch_box("输入嵌入", EMB_COL).move_to([ex, -1.98, 0])
        e_plus = VGroup(Circle(0.16, stroke_color=PE_COL, stroke_width=2), T("+", 22, PE_COL)).move_to([ex, -1.47, 0])
        e_pe = T("位置编码", 18, PE_COL).next_to(e_plus, LEFT, buff=0.25)
        e_mha = arch_box("多头自注意力", Q_COL).move_to([ex, -0.75, 0])
        e_n1 = norm_box().move_to([ex, -0.33, 0])
        e_ffn = arch_box("前馈网络", V_COL).move_to([ex, 0.09, 0])
        e_n2 = norm_box().move_to([ex, 0.51, 0])
        e_layer = VGroup(e_mha, e_n1, e_ffn, e_n2)
        e_bg = SurroundingRectangle(e_layer, buff=0.14, corner_radius=0.12, stroke_color=FG, stroke_width=1.5,
                                    fill_color=PANEL, fill_opacity=1)
        e_nx = T("× N", 24, W_COL).next_to(e_bg, LEFT, buff=0.2)
        e_title = T("编码器 Encoder", 30, FG, weight=BOLD).move_to([ex, 1.75, 0])

        # 解码器
        d_in = T("输出（右移一位）", 20, MUTED).move_to([dx, -2.5, 0])
        d_emb = arch_box("输出嵌入", EMB_COL).move_to([dx, -1.98, 0])
        d_plus = VGroup(Circle(0.16, stroke_color=PE_COL, stroke_width=2), T("+", 22, PE_COL)).move_to([dx, -1.47, 0])
        d_pe = T("位置编码", 18, PE_COL).next_to(d_plus, RIGHT, buff=0.25)
        d_mmha = arch_box("掩码多头自注意力", Q_COL).move_to([dx, -0.75, 0])
        d_n1 = norm_box().move_to([dx, -0.33, 0])
        d_cross = arch_box("交叉注意力", K_COL).move_to([dx, 0.09, 0])
        d_n2 = norm_box().move_to([dx, 0.51, 0])
        d_ffn = arch_box("前馈网络", V_COL).move_to([dx, 0.93, 0])
        d_n3 = norm_box().move_to([dx, 1.35, 0])
        d_layer = VGroup(d_mmha, d_n1, d_cross, d_n2, d_ffn, d_n3)
        d_bg = SurroundingRectangle(d_layer, buff=0.14, corner_radius=0.12, stroke_color=FG, stroke_width=1.5,
                                    fill_color=PANEL, fill_opacity=1)
        d_nx = T("× N", 24, W_COL).next_to(d_bg, RIGHT, buff=0.2)
        d_lin = arch_box("线性层", MUTED, width=2.2).move_to([dx, 2.2, 0])
        d_soft = arch_box("Softmax", W_COL, width=2.2).move_to([dx, 2.72, 0])
        d_out = T("输出概率", 20, MUTED).move_to([dx, 3.2, 0])
        d_title = T("解码器\nDecoder", 28, FG, weight=BOLD).move_to([dx + 3.15, -0.2, 0])

        def up_arrow(a, b):
            return Arrow(a.get_top(), b.get_bottom(), buff=0.02, stroke_width=2.5, color=MUTED,
                         max_tip_length_to_length_ratio=0.5, max_stroke_width_to_length_ratio=20)

        e_arrows = VGroup(up_arrow(e_emb, e_plus), up_arrow(e_plus, e_bg))
        d_arrows = VGroup(up_arrow(d_emb, d_plus), up_arrow(d_plus, d_bg), up_arrow(d_bg, d_lin),
                          up_arrow(d_lin, d_soft))
        e_pe_arrow = Arrow(e_pe.get_right(), e_plus.get_left(), buff=0.05, stroke_width=2, color=PE_COL,
                           max_tip_length_to_length_ratio=0.4)
        d_pe_arrow = Arrow(d_pe.get_left(), d_plus.get_right(), buff=0.05, stroke_width=2, color=PE_COL,
                           max_tip_length_to_length_ratio=0.4)
        xv = 0.75
        top_y = e_bg.get_top()[1] + 0.35
        path = VMobject(stroke_color=K_COL, stroke_width=3).set_points_as_corners([
            e_bg.get_top(), [ex, top_y, 0], [xv, top_y, 0], [xv, d_cross.get_y(), 0],
            [d_bg.get_left()[0] - 0.05, d_cross.get_y(), 0]])
        tip = Arrow([d_bg.get_left()[0] - 0.4, d_cross.get_y(), 0], [d_cross.get_left()[0], d_cross.get_y(), 0],
                    buff=0, stroke_width=3, color=K_COL, max_tip_length_to_length_ratio=0.35)
        link = VGroup(path, tip)
        shadows = VGroup(*[bg.copy().set_fill(PANEL, 1).set_stroke(opacity=0.45 - 0.15 * k).shift((k + 1) * 0.09 * (UR))
                           for bg in (e_bg, d_bg) for k in range(2)])

        with self.say("先来看整体结构。", "原始的 Transformer 分为两大部分：左边是编码器，右边是解码器。") as s:
            s.until(1)
            self.play(FadeIn(e_bg), FadeIn(e_title, shift=DOWN * 0.2), run_time=1.0)
            self.wait(max(0.0, s.left() - 2.2))
            self.play(FadeIn(d_bg), FadeIn(d_title, shift=LEFT * 0.2), run_time=1.0)

        with self.say("编码器负责读懂输入的句子，"):
            parts = [e_in, e_emb, e_arrows[0], e_pe, e_pe_arrow, e_plus, e_arrows[1], e_mha, e_n1, e_ffn, e_n2]
            self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.1) for p in parts], lag_ratio=0.12), run_time=2.2)

        with self.say("解码器则参考编码器的理解，一个词一个词地生成输出。"):
            parts = [d_in, d_emb, d_arrows[0], d_pe, d_pe_arrow, d_plus, d_arrows[1], d_mmha, d_n1, d_cross, d_n2,
                     d_ffn, d_n3, d_arrows[2], d_lin, d_arrows[3], d_soft, d_out]
            self.play(LaggedStart(*[FadeIn(p, shift=UP * 0.1) for p in parts], lag_ratio=0.08), run_time=2.4)
            self.play(Create(path), run_time=1.0)
            self.play(GrowArrow(tip), run_time=0.4)

        with self.say("每一部分都由 N 个相同的层堆叠而成，论文中 N 等于 6。"):
            self.bring_to_back(shadows)
            self.play(FadeIn(shadows), FadeIn(e_nx, scale=1.4), FadeIn(d_nx, scale=1.4), run_time=1.0)
            self.play(Indicate(e_nx, color=W_COL), Indicate(d_nx, color=W_COL), run_time=1.2)

        with self.say("每一层里最核心的，是注意力和前馈网络这两个模块。"):
            self.play(*[Circumscribe(m, color=Q_COL, buff=0.05) for m in (e_mha, d_mmha, d_cross)], run_time=1.5)
            self.play(*[Circumscribe(m, color=V_COL, buff=0.05) for m in (e_ffn, d_ffn)], run_time=1.5)

        with self.say("下面，我们就从最底部的输入开始，逐个拆解。"):
            self.play(Circumscribe(VGroup(e_emb, e_plus, e_pe), color=EMB_COL, buff=0.1),
                      Circumscribe(VGroup(d_emb, d_plus, d_pe), color=EMB_COL, buff=0.1), run_time=1.6)
        self.clear_stage()


# ---------------------------------------------------------------- 03 词嵌入
class S03_Embedding(Narrated):
    def construct(self):
        self.play(self.chapter("03", "词嵌入：把文字变成向量"))
        sent = T("小猫没有过马路，因为它太累", 52).move_to(UP * 0.8)
        with self.say("第一步，要把文字变成计算机能处理的数字。"):
            self.play(Write(sent), run_time=1.8)

        row = token_row(SENTENCE, size=26, buff=0.3).move_to(UP * 2.35)
        groups = [[0, 1], [2, 3], [4], [5, 6], [8, 9], [10], [11, 12]]
        tok_note = T("词元 token", 22, MUTED).next_to(row, LEFT, buff=0.3)
        with self.say("句子会先被切分成一个个小单元，叫做词元，也就是 token。"):
            anims = [FadeOut(sent[7])]
            for i, g in enumerate(groups):
                anims += [ReplacementTransform(VGroup(*[sent[k] for k in g]), row[i][1]), FadeIn(row[i][0])]
            self.play(*anims, run_time=1.6)
            self.play(FadeIn(tok_note), run_time=0.6)

        vocab = ["……", "马路", "小猫", "太累", "它", "……"]
        t_rows = VGroup()
        for j, w in enumerate(vocab):
            lab = T(w, 22, MUTED if w == "……" else FG)
            cells = vec_col(rand_vec(8, 100 + j), EMB_COL, cell=0.22, horizontal=True)
            line = VGroup(lab, cells).arrange(RIGHT, buff=0.3)
            t_rows.add(line)
        t_rows.arrange(DOWN, buff=0.1, aligned_edge=RIGHT)
        t_title = T("嵌入表（词表中每个词一行）", 22, EMB_COL)
        table = VGroup(t_title, t_rows).arrange(DOWN, buff=0.18).move_to(DOWN * 1.6)
        t_box = SurroundingRectangle(table, buff=0.15, corner_radius=0.1, stroke_color=DIM, stroke_width=1.5)

        cols = VGroup(*[vec_col(rand_vec(8, 100 + (vocab.index(w) if w in vocab else 50 + i)), EMB_COL, cell=0.2)
                        .next_to(row[i], DOWN, buff=0.25) for i, w in enumerate(SENTENCE)])

        with self.say("每个词元都会到一张巨大的嵌入表里，查出属于自己的一个向量。") as s:
            self.play(FadeIn(table), Create(t_box), run_time=0.9)
            cat_row = t_rows[2]
            hl = SurroundingRectangle(cat_row, color=HL, buff=0.06)
            self.play(Create(hl), Indicate(row[CAT], color=HL), run_time=0.8)
            moving = cat_row[1].copy()
            self.play(moving.animate.rotate(-PI / 2).move_to(cols[CAT]), run_time=1.0)
            self.remove(moving)
            self.add(cols[CAT])
            rest = [i for i in range(7) if i != CAT]
            self.play(LaggedStart(*[FadeIn(cols[i], shift=DOWN * 0.3) for i in rest], lag_ratio=0.12),
                      FadeOut(hl), run_time=max(1.0, s.left() - 0.2))

        brace = Brace(cols[0], LEFT, color=W_COL)
        dim = MathTex(r"d_{\text{model}}=512", font_size=34, color=W_COL).next_to(brace, LEFT, buff=0.1)
        note = T("图中只画出 8 维", 20, MUTED).next_to(cols, DOWN, buff=0.3)
        with self.say("这个向量通常有几百甚至上千维，论文里用的是 512 维。"):
            self.play(FadeOut(VGroup(table, t_box)), FadeOut(tok_note), run_time=0.6)
            self.play(GrowFromCenter(brace), Write(dim), run_time=1.0)
            self.play(FadeIn(note), run_time=0.5)
        self.clear_stage()

        plane = NumberPlane(x_range=[-7, 7, 1], y_range=[-3, 3, 1], x_length=12.5, y_length=5.4,
                            background_line_style={"stroke_color": DIM, "stroke_width": 1, "stroke_opacity": 0.7},
                            axis_config={"stroke_color": MUTED, "stroke_width": 1.5}).shift(DOWN * 0.1)
        words = {
            "猫": ((-3.4, 1.3), V_COL), "狗": ((-2.5, 0.8), V_COL), "老虎": ((-4.5, 0.2), V_COL),
            "小狗": ((-1.9, 1.7), V_COL),
            "汽车": ((3.0, -1.2), Q_COL), "卡车": ((3.9, -0.7), Q_COL), "自行车": ((2.3, -1.9), Q_COL),
            "苹果": ((2.2, 1.8), K_COL), "香蕉": ((3.3, 1.5), K_COL),
        }
        label_dir = {"猫": UL, "狗": DR, "老虎": DL}
        dots = {}
        pts = VGroup()
        for w, ((x, y), c) in words.items():
            p = plane.c2p(x, y)
            d = Dot(p, radius=0.09, color=c)
            lab = T(w, 24, c).next_to(d, label_dir.get(w, UR), buff=0.06)
            dots[w] = d
            pts.add(VGroup(d, lab))
        with self.say("训练之后，意思相近的词，在向量空间中也会靠得更近。"):
            self.play(Create(plane), run_time=1.0)
            self.play(LaggedStart(*[FadeIn(p, scale=0.5) for p in pts], lag_ratio=0.12), run_time=2.2)

        near = DashedLine(dots["猫"].get_center(), dots["狗"].get_center(), color=V_COL, stroke_width=4)
        far = DashedLine(dots["猫"].get_center(), dots["汽车"].get_center(), color=HL, stroke_width=4)
        perp = np.array([0.49, 0.87, 0])
        near_l = T("近", 28, V_COL, weight=BOLD).move_to(near.get_center() + perp * 0.32)
        far_l = T("远", 28, HL, weight=BOLD).next_to(far.get_center(), DOWN, buff=0.15)
        with self.say("比如“猫”和“狗”离得很近，而它们和“汽车”离得很远。") as s:
            self.play(Create(near), FadeIn(near_l), run_time=1.0)
            self.wait(max(0.0, s.left() * 0.35))
            self.play(Create(far), FadeIn(far_l), run_time=1.2)
        self.clear_stage()


# ---------------------------------------------------------------- 04 位置编码
class S04_Position(Narrated):
    def construct(self):
        self.play(self.chapter("04", "位置编码：词的顺序"))
        ra = token_row(["猫", "追", "狗"], size=32).move_to([-3.3, 1.6, 0])
        rb = token_row(["狗", "追", "猫"], size=32).move_to([3.3, 1.6, 0])
        ta = T("猫追狗", 26, MUTED).next_to(ra, UP, buff=0.3)
        tb = T("狗追猫", 26, MUTED).next_to(rb, UP, buff=0.3)
        with self.say("不过这里有个问题：注意力是同时查看所有词的，", "它本身并不知道词的先后顺序。") as s:
            self.play(FadeIn(ra), FadeIn(rb), FadeIn(ta), FadeIn(tb), run_time=1.0)
            s.until(1)
            self.play(*[Wiggle(t) for t in [*ra, *rb]], run_time=1.5)

        bag_a = Circle(radius=1.05, stroke_color=MUTED, stroke_width=2).move_to([-3.3, -0.9, 0])
        bag_b = bag_a.copy().move_to([3.3, -0.9, 0])
        layout = {"猫": UP * 0.45 + LEFT * 0.3, "追": DOWN * 0.1 + RIGHT * 0.4, "狗": DOWN * 0.5 + LEFT * 0.35}
        eq = MathTex("=", font_size=90, color=W_COL).move_to([0, -0.9, 0])
        warn = T("意思却完全相反！", 28, HL).next_to(eq, DOWN, buff=0.9)
        with self.say("在它看来，“猫追狗”和“狗追猫”几乎没有区别。"):
            self.play(Create(bag_a), Create(bag_b), run_time=0.6)
            anims = []
            for r, bag in ((ra, bag_a), (rb, bag_b)):
                for tok in r:
                    word = tok[1].text
                    anims.append(tok.copy().animate.scale(0.8).move_to(bag.get_center() + layout[word]))
            self.play(*anims, run_time=1.3)
            self.play(Write(eq), FadeIn(warn), run_time=0.8)
        self.clear_stage()

        row = token_row(SENTENCE, size=24, buff=0.3).move_to(UP * 2.4)
        idx = VGroup(*[T(str(i), 22, PE_COL).next_to(row[i], DOWN, buff=0.12) for i in range(7)])
        with self.say("所以，我们要给每个位置额外加上一个“位置编码”。"):
            self.play(FadeIn(row), run_time=0.8)
            self.play(LaggedStart(*[FadeIn(i, shift=UP * 0.2) for i in idx], lag_ratio=0.1), run_time=1.2)

        freqs = [(2.0, np.sin), (2.0, np.cos), (0.8, np.sin), (0.3, np.cos)]
        base_y = [1.05, 0.2, -0.65, -1.5]
        amp = 0.32
        x0, dxp = row[0].get_x(), row[1].get_x() - row[0].get_x()

        def wave_point(k, p):
            w, f = freqs[k]
            return np.array([x0 + p * dxp, base_y[k] + amp * f(w * p), 0])

        waves = VGroup(*[ParametricFunction(lambda p, k=k: wave_point(k, p), t_range=[-0.35, 6.35],
                                            color=PE_COL, stroke_width=3) for k in range(4)])
        w_labels = VGroup(*[T(n, 20, MUTED).move_to([row.get_left()[0] - 0.75, base_y[k], 0])
                            for k, n in enumerate(["sin 高频", "cos 高频", "sin 中频", "cos 低频"])])
        guides = VGroup(*[DashedLine([row[i].get_x(), 1.55, 0], [row[i].get_x(), -1.9, 0], stroke_width=1.5,
                                     color=DIM, dash_length=0.08) for i in range(7)])
        formula = MathTex(r"PE_{(pos,\,2i)}=\sin\!\Big(\frac{pos}{10000^{2i/d}}\Big)\qquad "
                          r"PE_{(pos,\,2i+1)}=\cos\!\Big(\frac{pos}{10000^{2i/d}}\Big)",
                          font_size=30, color=PE_COL).move_to(DOWN * 2.35)
        with self.say("论文使用不同频率的正弦和余弦波来生成它。"):
            self.play(Create(guides), run_time=0.6)
            self.play(LaggedStart(*[Create(w) for w in waves], lag_ratio=0.25), FadeIn(w_labels), run_time=2.0)
            self.play(FadeIn(formula, shift=UP * 0.2), run_time=0.8)

        p = 3
        samples = VGroup(*[Dot(wave_point(k, p), radius=0.08, color=W_COL) for k in range(4)])
        pe_vals = [(freqs[k][1](freqs[k][0] * p) + 1) / 2 for k in range(4)]
        pe_vec = vec_col(pe_vals, PE_COL, cell=0.36).move_to([5.75, -0.2, 0])
        pe_lab = T("位置 3 的编码", 22, PE_COL).next_to(pe_vec, UP, buff=0.2)
        with self.say("每个位置在这些波上取值，就得到一个独一无二的编码向量。"):
            self.play(guides[p].animate.set_stroke(W_COL, width=3), row[p][0].animate.set_stroke(W_COL), run_time=0.6)
            self.play(LaggedStart(*[GrowFromCenter(d) for d in samples], lag_ratio=0.2), run_time=1.0)
            self.play(*[TransformFromCopy(samples[k], pe_vec[k]) for k in range(4)], FadeIn(pe_lab), run_time=1.3)
        self.clear_stage()

        emb = vec_col(rand_vec(8, 103), EMB_COL, cell=0.38)
        pe = vec_col([(np.sin(3 / 10000 ** (i / 8)) + 1) / 2 if i % 2 == 0 else (np.cos(3 / 10000 ** ((i - 1) / 8)) + 1) / 2
                      for i in range(8)], PE_COL, cell=0.38)
        out = vec_col((rand_vec(8, 103) + np.array([c.get_fill_opacity() for c in pe])) / 2, W_COL, cell=0.38)
        plus = MathTex("+", font_size=72)
        eq = MathTex("=", font_size=72)
        eqn = VGroup(emb, plus, pe, eq, out).arrange(RIGHT, buff=1.1).move_to(UP * 0.2)
        labels = VGroup(T("词向量（马路）", 28, EMB_COL).next_to(emb, DOWN, buff=0.35),
                        T("位置编码（3）", 28, PE_COL).next_to(pe, DOWN, buff=0.35),
                        T("输入向量", 28, W_COL).next_to(out, DOWN, buff=0.35))
        with self.say("把它直接加到词向量上，模型就能区分词的顺序了。") as s:
            self.play(FadeIn(emb), FadeIn(labels[0]), run_time=0.6)
            self.play(Write(plus), FadeIn(pe), FadeIn(labels[1]), run_time=0.8)
            self.play(Write(eq), TransformFromCopy(VGroup(emb, pe), out), FadeIn(labels[2]), run_time=1.2)
        self.clear_stage()


# ---------------------------------------------------------------- 05 Q K V
class S05_QKV(Narrated):
    def construct(self):
        self.play(self.chapter("05", "自注意力：Q、K、V"))
        title = T("自注意力  Self-Attention", 60, W_COL, weight=BOLD)
        with self.say("现在，进入最核心的部分：自注意力。"):
            self.play(Write(title), run_time=1.5)
        self.play(FadeOut(title, shift=UP * 0.4), run_time=0.5)

        row = token_row(SENTENCE, size=30, buff=0.3).move_to(DOWN * 0.6)
        with self.say("看这句话：小猫没有过马路，因为它太累了。"):
            self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.2) for t in row], lag_ratio=0.12), run_time=1.8)

        qmark = T("？", 64, HL, weight=BOLD).next_to(row[IT], UP, buff=0.3)
        with self.say("这里的“它”，指的是谁？"):
            self.play(recolor_token(row[IT][0], HL), row[IT][1].animate.set_color(HL), FadeIn(qmark, scale=1.5),
                      run_time=0.8)

        guess = arc_above(row[IT], row[CAT], color=FG, width=3)
        guess = DashedVMobject(guess, num_dashes=30)
        with self.say("我们一眼就能看出是小猫。可是模型要怎么知道呢？") as s:
            self.play(FadeOut(qmark), Create(guess), recolor_token(row[CAT][0], HL), run_time=1.2)
            self.wait(max(0.0, s.left() - 1.0))
            self.play(FadeOut(guess), row[CAT][0].animate.set_stroke(FG).set_fill(FG, 0.08), run_time=0.6)

        weights = [0.60, 0.04, 0.03, 0.12, 0.04, 0.0, 0.05]
        arcs = VGroup(*[arc_above(row[IT], row[j], color=W_COL, width=1.5 + 14 * weights[j],
                                  opacity=0.35 + weights[j]) for j in range(7) if j != IT])
        w_labels = VGroup(*[T(f"{weights[j]:.2f}", 20, W_COL).next_to(row[j], DOWN, buff=0.2) for j in range(7) if j != IT])
        with self.say("办法是：让“它”去关注句子中的每一个词，", "看看谁和自己最相关。") as s:
            self.play(LaggedStart(*[Create(a) for a in arcs], lag_ratio=0.15), run_time=2.0)
            s.until(1)
            self.play(FadeIn(w_labels), Indicate(row[CAT], color=HL), run_time=1.4)
        self.clear_stage()

        x = vec_col(rand_vec(6, 7), EMB_COL, cell=0.32).move_to([-5.2, 0, 0])
        x_lab = T("“它”的向量 x", 22, EMB_COL).next_to(x, DOWN, buff=0.3)
        specs = [("W^Q", Q_COL, 1.9), ("W^K", K_COL, 0.0), ("W^V", V_COL, -1.9)]
        mats, m_labs, arrows_in = VGroup(), VGroup(), VGroup()
        for i, (name, col, y) in enumerate(specs):
            m = matrix_grid(6, 6, col, cell=0.2, seed=i + 1).move_to([-1.6, y, 0])
            mats.add(m)
            m_labs.add(MathTex(name, font_size=40, color=col).next_to(m, LEFT, buff=0.25))
            arrows_in.add(Arrow(x.get_right(), m_labs[-1].get_left(), buff=0.15, stroke_width=3, color=MUTED))
        with self.say("具体做法是：每个词向量都会分别乘以三个权重矩阵，"):
            self.play(FadeIn(x), FadeIn(x_lab), run_time=0.6)
            self.play(LaggedStart(*[AnimationGroup(GrowArrow(a), FadeIn(m), Write(l))
                                    for a, m, l in zip(arrows_in, mats, m_labs)], lag_ratio=0.3), run_time=2.0)

        names = [("查询 Query", "q", Q_COL), ("键 Key", "k", K_COL), ("值 Value", "v", V_COL)]
        outs, out_labs, arrows_out = VGroup(), VGroup(), VGroup()
        for i, ((cn, sym, col), m) in enumerate(zip(names, mats)):
            v = vec_col(rand_vec(6, 20 + i), col, cell=0.3, horizontal=True).move_to([1.9, m.get_y(), 0])
            outs.add(v)
            out_labs.add(VGroup(MathTex(sym, font_size=44, color=col), T(cn, 28, col)).arrange(RIGHT, buff=0.25)
                         .next_to(v, RIGHT, buff=0.35))
            arrows_out.add(Arrow(m.get_right(), v.get_left(), buff=0.15, stroke_width=3, color=col))
        with self.say("得到三个新的向量：查询 Q、键 K、和值 V。") as s:
            per = max(0.6, (s.left() - 0.2) / 3)
            for a, v, l in zip(arrows_out, outs, out_labs):
                self.play(GrowArrow(a), FadeIn(v, shift=RIGHT * 0.2), FadeIn(l), run_time=per)
        self.clear_stage()

        # 图书馆类比
        card = RoundedRectangle(width=3.0, height=1.7, corner_radius=0.15, stroke_color=Q_COL, stroke_width=3,
                                fill_color=Q_COL, fill_opacity=0.12).move_to([-4.6, 0.3, 0])
        card_txt = VGroup(T("我想了解：", 24, FG), T("猫的习性", 30, Q_COL, weight=BOLD)).arrange(DOWN, buff=0.15).move_to(card)
        card_lab = T("查询 Q", 26, Q_COL, weight=BOLD).next_to(card, UP, buff=0.25)
        tags = ["动物", "交通", "烹饪", "天文"]
        spines = ["#5C6BC0", "#26A69A", "#8D6E63", "#AB47BC"]
        books, tag_boxes, contents = VGroup(), VGroup(), VGroup()
        for i, (tg, sc) in enumerate(zip(tags, spines)):
            b = RoundedRectangle(width=1.05, height=2.1, corner_radius=0.06, stroke_color=sc, stroke_width=2,
                                 fill_color=sc, fill_opacity=0.35).move_to([0.9 + 1.55 * i, 0.3, 0])
            b.add(Line(b.get_corner(UL) + DOWN * 0.3 + RIGHT * 0.1, b.get_corner(UR) + DOWN * 0.3 + LEFT * 0.1,
                       stroke_color=sc, stroke_width=3))
            books.add(b)
            tag_boxes.add(token_box(tg, color=K_COL, size=22, width=1.0, height=0.5).next_to(b, UP, buff=0.15))
            page = VGroup(RoundedRectangle(width=1.0, height=0.62, corner_radius=0.05, stroke_color=V_COL,
                                           stroke_width=2, fill_color=V_COL, fill_opacity=0.15),
                          *[Line(LEFT * 0.32, RIGHT * 0.32, stroke_width=2, color=V_COL).shift(UP * (0.14 - 0.14 * k))
                            for k in range(3)])
            page[1:].move_to(page[0])
            contents.add(page.next_to(b, DOWN, buff=0.2))
        k_lab = T("键 K：书的标签", 24, K_COL).next_to(tag_boxes, UP, buff=0.7)
        v_lab = T("值 V：书的内容", 24, V_COL).next_to(contents, DOWN, buff=0.15)

        with self.say("可以把它想象成在图书馆里找书："):
            self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.2) for b in books], lag_ratio=0.15), FadeIn(card),
                      FadeIn(card_txt), run_time=1.6)
        with self.say("查询，是你想找什么；键，是每本书上的标签；") as s:
            self.play(Write(card_lab), Indicate(card_txt[1], color=Q_COL), run_time=1.0)
            self.wait(max(0.0, s.left() * 0.45))
            self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.2) for t in tag_boxes], lag_ratio=0.12), FadeIn(k_lab),
                      run_time=1.2)
        with self.say("而值 V，则是书中真正的内容。"):
            self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in contents], lag_ratio=0.12), FadeIn(v_lab),
                      run_time=1.2)

        match = [0.85, 0.05, 0.08, 0.02]
        scores = VGroup(*[T(f"匹配 {m:.2f}", 18, W_COL if m == max(match) else MUTED).next_to(t, UP, buff=0.12)
                          for t, m in zip(tag_boxes, match)])
        link = Arrow(card.get_right(), tag_boxes[0].get_left(), buff=0.12, color=W_COL, stroke_width=5)
        got = contents[0].copy()
        with self.say("查询和标签越匹配，你就从那本书里读到越多的内容。") as s:
            self.play(LaggedStart(*[FadeIn(sc, shift=UP * 0.15) for sc in scores], lag_ratio=0.2), run_time=1.2)
            self.play(GrowArrow(link), Indicate(tag_boxes[0], color=W_COL), run_time=0.9)
            self.play(got.animate.next_to(card, DOWN, buff=0.35).scale(1.2), run_time=1.1)
        self.clear_stage()


# ---------------------------------------------------------------- 06 注意力的计算
RAW = np.array([7.6, 2.2, 1.6, 4.4, 2.2, 4.4, 2.6])
SCALED = RAW / 2.0
WEIGHTS = softmax(SCALED)


class S06_AttentionMath(Narrated):
    def construct(self):
        self.play(self.chapter("06", "注意力是怎么算的"))
        row = token_row(SENTENCE, size=24, buff=0.3, width=1.05).move_to([0.45, 2.75, 0])
        row[IT][0].set_stroke(HL).set_fill(HL, 0.15)
        row[IT][1].set_color(HL)
        keys = VGroup(*[vec_col(rand_vec(4, 40 + j), K_COL, cell=0.22).next_to(row[j], DOWN, buff=0.22) for j in range(7)])
        k_lab = T("键 k", 22, K_COL).next_to(keys, RIGHT, buff=0.35)
        q = vec_col(rand_vec(4, 60), Q_COL, cell=0.22).move_to([-5.6, keys.get_y(), 0])
        q_lab = T("“它”的查询 q", 22, Q_COL).next_to(q, UP, buff=0.2)

        with self.say("我们以“它”为例，看看注意力具体是怎么算的。"):
            self.play(FadeIn(row), run_time=0.7)
            self.play(FadeIn(q, shift=RIGHT * 0.2), FadeIn(q_lab), LaggedStart(*[FadeIn(k) for k in keys], lag_ratio=0.08),
                      FadeIn(k_lab), run_time=1.5)

        num_y = 0.75
        raw_nums = VGroup(*[T(f"{v:.1f}", 26, FG).move_to([row[j].get_x(), num_y, 0]) for j, v in enumerate(RAW)])
        step = T("① 点积 q·k", 24, W_COL).move_to([-5.6, num_y, 0])
        with self.say("第一步，用“它”的查询向量 q，和每个词的键向量 k 做点积。") as s:
            self.play(FadeIn(step), run_time=0.5)
            per = max(0.3, (s.left() - 0.3) / 7)
            for j in range(7):
                ghost = q.copy()
                self.play(ghost.animate.move_to(keys[j]).set_opacity(0.0), FadeIn(raw_nums[j], shift=DOWN * 0.2),
                          run_time=per)
                self.remove(ghost)

        with self.say("点积越大，说明两个词越相关。"):
            self.play(Indicate(raw_nums[CAT], color=HL, scale_factor=1.5), Indicate(row[CAT], color=HL), run_time=1.5)

        scaled = VGroup(*[T(f"{v:.1f}", 26, FG).move_to(raw_nums[j]) for j, v in enumerate(SCALED)])
        step2 = VGroup(T("②", 24, W_COL), MathTex(r"\div\sqrt{d_k}", font_size=34, color=W_COL)).arrange(RIGHT, buff=0.12)
        step2.move_to(step)
        with self.say("第二步，把分数除以根号 d k，防止数值太大。"):
            self.play(ReplacementTransform(step, step2), run_time=0.6)
            self.play(*[ReplacementTransform(a, b) for a, b in zip(raw_nums, scaled)], run_time=1.2)

        base_y, max_h = -0.95, 1.35
        bars = VGroup()
        for j, w in enumerate(WEIGHTS):
            b = Rectangle(width=0.62, height=max(0.02, max_h * w / WEIGHTS.max()), stroke_width=0,
                          fill_color=HL if j == CAT else W_COL, fill_opacity=0.85)
            b.move_to([row[j].get_x(), base_y, 0], aligned_edge=DOWN)
            bars.add(b)
        baseline = Line([row.get_left()[0], base_y, 0], [row.get_right()[0], base_y, 0], color=DIM, stroke_width=2)
        w_nums = VGroup(*[T(f"{w:.2f}", 26, HL if j == CAT else W_COL).move_to(scaled[j]) for j, w in enumerate(WEIGHTS)])
        step3 = T("③ softmax", 24, W_COL).move_to(step2)
        sum_note = T("总和 = 1", 22, MUTED).move_to([-5.6, base_y + 0.3, 0])
        with self.say("再经过 softmax，变成总和为 1 的注意力权重。"):
            self.play(ReplacementTransform(step2, step3), run_time=0.5)
            self.play(Create(baseline), *[ReplacementTransform(a, b) for a, b in zip(scaled, w_nums)],
                      *[GrowFromEdge(b, DOWN) for b in bars], run_time=1.5)
            self.play(FadeIn(sum_note), run_time=0.5)

        with self.say("可以看到，“它”把大部分注意力，都给了“小猫”。"):
            self.play(Circumscribe(VGroup(bars[CAT], w_nums[CAT], row[CAT]), color=HL, buff=0.12), run_time=1.6)

        v_y = -1.95
        vals = VGroup(*[vec_col(rand_vec(4, 80 + j), V_COL, cell=0.2, horizontal=True).move_to([row[j].get_x(), v_y, 0])
                        for j in range(7)])
        v_lab = T("值 v", 22, V_COL).next_to(vals, LEFT, buff=0.4)
        z = vec_col(rand_vec(4, 80), V_COL, cell=0.3).move_to([6.25, -1.3, 0])
        z.set_stroke(HL, width=2.5)
        z_lab = T("新的“它”", 22, HL).next_to(z, UP, buff=0.2)
        z_formula = MathTex(r"z=\sum_j w_j\,v_j", font_size=30, color=FG).next_to(z, DOWN, buff=0.25)
        step4 = T("④ 加权求和", 24, W_COL).move_to(step3)
        with self.say("第三步，用这些权重，对所有词的值向量 v 加权求和。") as s:
            self.play(FadeIn(vals, shift=UP * 0.2), FadeIn(v_lab), ReplacementTransform(step3, step4), run_time=0.9)
            self.play(*[vals[j].animate.set_opacity(0.15 + 0.85 * WEIGHTS[j] / WEIGHTS.max()) for j in range(7)],
                      run_time=0.8)
            ghosts = [vals[j].copy() for j in range(7)]
            self.play(*[g.animate.move_to(z).scale(0.3) for g in ghosts], FadeIn(z, run_time=1.6), run_time=1.6)
            for g in ghosts:
                self.remove(g)
            self.play(FadeIn(z_lab), Write(z_formula), run_time=max(0.6, min(1.2, s.left())))

        note = T("主要融合了“小猫”的信息", 22, HL).next_to(z_formula, DOWN, buff=0.15)
        note.shift(LEFT * max(0.0, note.get_right()[0] - 6.9))
        with self.say("得到的新向量，就融合了“小猫”的信息，", "“它”也就“知道”了自己指的是谁。"):
            self.play(Indicate(bars[CAT], color=HL), FadeIn(note), run_time=1.4)
            self.play(Circumscribe(z, color=HL), run_time=1.4)
        self.clear_stage()

        rows = np.array([
            [0.55, 0.10, 0.05, 0.10, 0.05, 0.10, 0.05],
            [0.20, 0.40, 0.25, 0.05, 0.03, 0.02, 0.05],
            [0.10, 0.20, 0.30, 0.30, 0.03, 0.02, 0.05],
            [0.10, 0.05, 0.35, 0.40, 0.03, 0.02, 0.05],
            [0.05, 0.10, 0.05, 0.05, 0.40, 0.10, 0.25],
            list(WEIGHTS),
            [0.30, 0.03, 0.02, 0.02, 0.13, 0.30, 0.20],
        ])
        rows = rows / rows.sum(axis=1, keepdims=True)
        cell = 0.56
        heat = VGroup()
        for r in range(7):
            for c in range(7):
                sq = Square(cell, stroke_color=BG, stroke_width=2).set_fill(W_COL, opacity=0.08 + 0.92 * rows[r, c] / 0.6)
                sq.move_to([c * cell, -r * cell, 0])
                heat.add(sq)
        heat.move_to([-3.2, -0.35, 0])
        col_labs = VGroup(*[T(w, 18, K_COL).next_to(heat[c], UP, buff=0.12) for c, w in enumerate(SENTENCE)])
        row_labs = VGroup(*[T(w, 18, Q_COL).next_to(heat[r * 7], LEFT, buff=0.12) for r, w in enumerate(SENTENCE)])
        k_axis = T("键 K（被关注的词）→", 20, K_COL).next_to(col_labs, UP, buff=0.15)
        q_axis = T("查询 Q ↓", 20, Q_COL).next_to(row_labs, UP, buff=0.12).align_to(row_labs, RIGHT)
        it_box = SurroundingRectangle(VGroup(*heat[IT * 7: IT * 7 + 7]), color=HL, buff=0.03)
        with self.say("实际上，句子中的每个词，都在同时做同样的计算，") as s:
            self.play(FadeIn(col_labs), FadeIn(row_labs), FadeIn(k_axis), FadeIn(q_axis), run_time=0.8)
            self.play(LaggedStart(*[FadeIn(VGroup(*heat[r * 7: r * 7 + 7])) for r in range(7)], lag_ratio=0.15),
                      run_time=1.8)
            self.play(Create(it_box), run_time=0.6)

        formula = MathTex(r"\mathrm{Attention}(Q,K,V)=\mathrm{softmax}\left(\frac{QK^{\top}}{\sqrt{d_k}}\right)V",
                          substrings_to_isolate=["Q", "K", "V"], font_size=38)
        formula.set_color_by_tex("Q", Q_COL).set_color_by_tex("K", K_COL).set_color_by_tex("V", V_COL)
        formula.move_to([2.95, 0.4, 0])
        f_box = SurroundingRectangle(formula, color=W_COL, buff=0.25, corner_radius=0.1)
        f_note = T("整篇论文最核心的一行", 24, W_COL).next_to(f_box, DOWN, buff=0.3)
        with self.say("写成矩阵形式，就是这个公式——", "这也是整篇论文最核心的一行。") as s:
            self.play(Write(formula), run_time=2.0)
            s.until(1)
            self.play(Create(f_box), FadeIn(f_note, shift=UP * 0.2), run_time=1.0)
        self.clear_stage()


# ---------------------------------------------------------------- 07 多头注意力
class S07_MultiHead(Narrated):
    def construct(self):
        self.play(self.chapter("07", "多头注意力"))
        ys = [1.75, 0.15, -1.45]
        heads = VGroup(*[token_row(SENTENCE, size=22, buff=0.16, width=0.9).move_to([-0.95, y, 0]) for y in ys])
        cols = [HL, Q_COL, V_COL]
        h_labs = VGroup(*[VGroup(T(f"头 {i + 1}", 24, cols[i], weight=BOLD), T(t, 18, MUTED)).arrange(DOWN, buff=0.08)
                          .move_to([-5.9, ys[i] + 0.15, 0]) for i, t in enumerate(["指代关系", "相邻的词", "因果 / 句法"])])
        pairs = [
            [(IT, CAT, 1.0), (IT, 3, 0.25)],
            [(0, 1, 0.8), (1, 2, 0.8), (2, 3, 0.8), (3, 4, 0.8), (4, 5, 0.8), (5, 6, 0.8)],
            [(4, 6, 1.0), (1, 2, 0.7), (2, 3, 0.6)],
        ]
        arcs = [VGroup(*[arc_above(heads[h][a], heads[h][b], color=cols[h], width=2 + 5 * w, opacity=0.4 + 0.6 * w,
                                   height_scale=0.55) for a, b, w in pairs[h]]) for h in range(3)]

        with self.say("但一个注意力头，往往只能捕捉一种关系，", "而语言中的关系是多种多样的。") as s:
            self.play(FadeIn(heads[0]), run_time=0.7)
            self.play(LaggedStart(*[Create(a) for a in arcs[0]], lag_ratio=0.3), run_time=1.2)

        more = T("…… 论文中共 8 个头", 22, MUTED).move_to([-0.95, -2.4, 0])
        with self.say("所以 Transformer 会同时使用多个注意力头，论文中用了 8 个。"):
            self.play(TransformFromCopy(heads[0], heads[1]), TransformFromCopy(heads[0], heads[2]), run_time=1.2)
            self.play(FadeIn(more), run_time=0.6)

        with self.say("有的头关注指代关系，比如“它”对应“小猫”；"):
            self.play(FadeIn(h_labs[0]), Indicate(arcs[0][0], color=HL), run_time=1.4)
        with self.say("有的头关注相邻的词；"):
            self.play(FadeIn(h_labs[1]), LaggedStart(*[Create(a) for a in arcs[1]], lag_ratio=0.15), run_time=1.4)
        with self.say("还有的头关注因果或句法关系，比如“因为”连着“太累”。"):
            self.play(FadeIn(h_labs[2]), LaggedStart(*[Create(a) for a in arcs[2]], lag_ratio=0.2), run_time=1.6)

        zs = VGroup(*[vec_col(rand_vec(4, 300 + h), cols[h], cell=0.22).move_to([3.75, ys[h], 0]) for h in range(3)])
        z_arrows = VGroup(*[Arrow(heads[h].get_right(), zs[h].get_left(), buff=0.15, stroke_width=3, color=cols[h],
                                  max_tip_length_to_length_ratio=0.3) for h in range(3)])
        z_labs = VGroup(*[MathTex(f"z_{h + 1}", font_size=30, color=cols[h]).next_to(zs[h], UP, buff=0.1) for h in range(3)])
        with self.say("每个头使用各自的 Q、K、V 矩阵，独立完成计算，"):
            self.play(LaggedStart(*[AnimationGroup(GrowArrow(a), FadeIn(z), FadeIn(l))
                                    for a, z, l in zip(z_arrows, zs, z_labs)], lag_ratio=0.3), run_time=1.8)

        concat = VGroup(*[z.copy() for z in zs]).arrange(DOWN, buff=0).move_to([4.95, 0.15, 0])
        c_lab = T("拼接", 20, FG).next_to(concat, UP, buff=0.15)
        wo = MathTex(r"W^O", font_size=34, color=FG).move_to([5.8, 0.15, 0])
        final = vec_col(rand_vec(4, 400), FG, cell=0.26).move_to([6.5, 0.15, 0])
        f_lab = T("输出", 20, FG).next_to(final, UP, buff=0.15)
        with self.say("最后把所有头的结果拼接起来，再通过一个线性层融合。") as s:
            self.play(FadeOut(z_labs), *[ReplacementTransform(zs[h], concat[h]) for h in range(3)], FadeOut(z_arrows),
                      FadeIn(c_lab), run_time=1.4)
            self.play(FadeIn(wo, shift=RIGHT * 0.2), run_time=0.5)
            self.play(TransformFromCopy(concat, final), FadeIn(f_lab), run_time=1.2)

        with self.say("这样，模型就能从多个角度，同时理解一句话。"):
            self.play(*[Indicate(VGroup(arcs[h]), color=cols[h]) for h in range(3)], run_time=1.5)
        self.clear_stage()


# ---------------------------------------------------------------- 08 前馈 / 残差 / 归一化
class S08_FFN(Narrated):
    def construct(self):
        self.play(self.chapter("08", "前馈网络 · 残差连接 · 层归一化"))
        sizes = [4, 10, 4]
        xs = [-3.0, 0.0, 3.0]
        layers = VGroup()
        for n, x in zip(sizes, xs):
            layers.add(VGroup(*[Circle(0.15, stroke_color=V_COL, stroke_width=2).set_fill(V_COL, 0.05)
                                for _ in range(n)]).arrange(DOWN, buff=0.16).move_to([x, 0.3, 0]))
        edges = VGroup()
        for a, b in ((0, 1), (1, 2)):
            for n1 in layers[a]:
                for n2 in layers[b]:
                    edges.add(Line(n1.get_center(), n2.get_center(), stroke_width=1, color=DIM,
                                   buff=0.15))
        dims = VGroup(*[T(t, 22, MUTED).next_to(layers[i], DOWN, buff=0.35).set_y(-2.35)
                        for i, t in enumerate(["512 维", "2048 维（扩大 4 倍）", "512 维"])])
        with self.say("注意力层之后，是一个前馈神经网络。"):
            self.play(FadeIn(layers), Create(edges), run_time=1.6)
            self.play(FadeIn(dims), run_time=0.6)

        with self.say("它对每个位置单独处理：先把向量扩展到四倍维度，再压缩回来。") as s:
            for li in range(3):
                anims = [layers[li].animate.set_fill(V_COL, opacity=0.8)]
                if li > 0:
                    sub = VGroup(*edges[(li - 1) * 40: li * 40])
                    anims.append(ShowPassingFlash(sub.copy().set_stroke(V_COL, width=2.5), time_width=0.6))
                self.play(*anims, run_time=max(0.7, (s.left() - 0.3) / 3))
        self.clear_stage()

        left = VGroup(T("注意力", 32, Q_COL, weight=BOLD), T("词与词之间交流、收集信息", 24, FG)).arrange(DOWN, buff=0.2)
        right = VGroup(T("前馈网络", 32, V_COL, weight=BOLD), T("每个词独立加工、“思考”", 24, FG)).arrange(DOWN, buff=0.2)
        dots_l = VGroup(*[Dot(radius=0.12, color=Q_COL) for _ in range(4)]).arrange(RIGHT, buff=0.6)
        arcs_l = VGroup(*[arc_above(dots_l[i], dots_l[j], color=Q_COL, width=2, height_scale=0.8)
                          for i in range(4) for j in range(i + 1, 4)])
        pic_l = VGroup(arcs_l, dots_l)
        dots_r = VGroup(*[Dot(radius=0.12, color=V_COL) for _ in range(4)]).arrange(RIGHT, buff=0.6)
        loops_r = VGroup(*[Square(0.34, stroke_color=V_COL, stroke_width=2).next_to(d, UP, buff=0.12) for d in dots_r])
        pic_r = VGroup(loops_r, dots_r)
        card_l = VGroup(pic_l, left).arrange(DOWN, buff=0.5).move_to([-3.4, 0.1, 0])
        card_r = VGroup(pic_r, right).arrange(DOWN, buff=0.5).move_to([3.4, 0.1, 0])
        card_r[0].align_to(card_l[0], DOWN)
        VGroup(card_l, card_r).scale(1.25)
        with self.say("如果说注意力负责“收集信息”，那前馈网络就负责“加工和思考”。") as s:
            self.play(FadeIn(card_l, shift=UP * 0.2), run_time=1.0)
            self.wait(max(0.0, s.left() * 0.35))
            self.play(FadeIn(card_r, shift=UP * 0.2), run_time=1.0)
        self.clear_stage()

        x_in = vec_col(rand_vec(6, 500), EMB_COL, cell=0.26, horizontal=True).move_to([0, -2.3, 0])
        x_lab = MathTex("x", font_size=40, color=EMB_COL).next_to(x_in, LEFT, buff=0.3)
        sub = arch_box("子层：注意力 或 前馈网络", Q_COL, width=4.4, height=0.75, size=24).move_to([0, -1.0, 0])
        plus = VGroup(Circle(0.25, stroke_color=HL, stroke_width=3), MathTex("+", font_size=40, color=HL)).move_to([0, 0.35, 0])
        ln = arch_box("层归一化 LayerNorm", W_COL, width=4.0, height=0.7, size=24).move_to([0, 1.45, 0])
        x_out = vec_col(rand_vec(6, 501), FG, cell=0.26, horizontal=True).move_to([0, 2.65, 0])
        a1 = Arrow(x_in.get_top(), sub.get_bottom(), buff=0.08, color=MUTED, stroke_width=3)
        a2 = Arrow(sub.get_top(), plus.get_bottom(), buff=0.05, color=MUTED, stroke_width=3)
        a3 = Arrow(plus.get_top(), ln.get_bottom(), buff=0.05, color=MUTED, stroke_width=3)
        a4 = Arrow(ln.get_top(), x_out.get_bottom(), buff=0.08, color=MUTED, stroke_width=3)
        skip_pts = [x_in.get_right() + RIGHT * 0.1, [3.2, -2.3, 0], [3.2, 0.35, 0], plus.get_right() + RIGHT * 0.05]
        skip = VMobject(stroke_color=HL, stroke_width=4).set_points_as_corners(skip_pts)
        skip_tip = Arrow(skip_pts[2] + LEFT * 0.6 + RIGHT * 0.2, skip_pts[3], buff=0, color=HL, stroke_width=4,
                         max_tip_length_to_length_ratio=0.5)
        skip_lab = T("残差连接", 24, HL, weight=BOLD).next_to([3.2, -1.0, 0], RIGHT, buff=0.2)
        formula = MathTex(r"\mathrm{LayerNorm}\big(x+\mathrm{Sublayer}(x)\big)", font_size=30, color=FG).move_to([-4.55, 0.35, 0])

        with self.say("此外，每个子层周围，还有两个关键设计。"):
            self.play(FadeIn(x_in), FadeIn(x_lab), GrowArrow(a1), FadeIn(sub), run_time=1.2)
            self.play(GrowArrow(a2), FadeIn(plus), GrowArrow(a3), FadeIn(ln), GrowArrow(a4), FadeIn(x_out), run_time=1.2)

        with self.say("第一个是残差连接：把输入直接加到输出上，", "让信息和梯度，可以畅通地穿过很深的网络；") as s:
            self.play(Create(skip), run_time=1.0)
            self.play(GrowArrow(skip_tip), FadeIn(skip_lab), run_time=0.6)
            self.play(Write(formula), run_time=1.0)
            s.until(1)
            for _ in range(2):
                dot = Dot(radius=0.12, color=HL).move_to(skip_pts[0])
                self.play(MoveAlongPath(dot, skip), run_time=1.1, rate_func=linear)
                self.remove(dot)

        rng = np.random.default_rng(9)
        raw = rng.normal(0, 1, 8) * np.array([2.2, 0.3, 1.5, 3.0, 0.4, 2.5, 0.8, 1.9])
        norm = (raw - raw.mean()) / raw.std()

        def bars_for(vals, scale):
            g = VGroup()
            for v in vals:
                h = max(0.02, abs(v) * scale)
                r = Rectangle(width=0.2, height=h, stroke_width=0, fill_color=W_COL, fill_opacity=0.85)
                r.move_to([0, 0, 0], aligned_edge=DOWN if v >= 0 else UP)
                g.add(r)
            g.arrange(RIGHT, buff=0.06, aligned_edge=ORIGIN)
            for r, v in zip(g, vals):
                r.move_to([r.get_x(), 0, 0], aligned_edge=DOWN if v >= 0 else UP)
            return g

        before = bars_for(raw, 0.24)
        after = bars_for(norm, 0.24)
        shift = np.array([5.3, 1.75, 0]) - before.get_center()
        before.shift(shift)
        after.shift(shift)
        before_l = T("归一化前：忽大忽小", 20, MUTED).move_to([5.3, 0.5, 0])
        after_l = T("归一化后：均值 0、方差 1", 20, W_COL).move_to(before_l)
        with self.say("第二个是层归一化，让每一层的数值保持稳定。"):
            self.play(Indicate(ln, color=W_COL), FadeIn(before), FadeIn(before_l), run_time=1.2)
            self.play(Transform(before, after), Transform(before_l, after_l), run_time=1.2)
        self.clear_stage()

        blocks = VGroup(*[arch_box(f"第 {i + 1} 层", Q_COL if i % 2 == 0 else V_COL, width=3.4, height=0.55, size=22)
                          for i in range(6)]).arrange(UP, buff=0.18).move_to([-1.2, 0.35, 0])
        inp = token_row(["小猫", "没有", "过", "马路", "…"], size=18, buff=0.1, width=0.66).next_to(blocks, DOWN, buff=0.3)
        levels = VGroup(
            T("词语本身", 22, MUTED).next_to(VGroup(blocks[0], blocks[1]), RIGHT, buff=1.2),
            T("短语 / 句法", 22, FG).next_to(VGroup(blocks[2], blocks[3]), RIGHT, buff=1.2),
            T("语义 / 指代 / 推理", 22, W_COL).next_to(VGroup(blocks[4], blocks[5]), RIGHT, buff=1.2),
        )
        levels.align_to(levels[0], LEFT)
        up = Arrow([levels.get_left()[0] - 0.45, blocks.get_bottom()[1], 0], [levels.get_left()[0] - 0.45, blocks.get_top()[1], 0],
                   color=W_COL, stroke_width=4, buff=0)
        up_l = T("越来越抽象", 20, W_COL).rotate(PI / 2).next_to(up, LEFT, buff=0.1)
        with self.say("把这样的层堆叠许多次，模型就能学到越来越抽象的语言规律。") as s:
            self.play(FadeIn(inp), run_time=0.5)
            self.play(LaggedStart(*[FadeIn(b, shift=UP * 0.3) for b in blocks], lag_ratio=0.2), run_time=2.0)
            self.play(GrowArrow(up), FadeIn(up_l), LaggedStart(*[FadeIn(l) for l in levels], lag_ratio=0.3), run_time=1.5)
        self.clear_stage()


# ---------------------------------------------------------------- 09 解码器
class S09_Decoder(Narrated):
    def construct(self):
        self.play(self.chapter("09", "解码器：逐词生成"))
        src = T("我爱学习", 56).move_to([-3.2, 0.4, 0])
        tgt = T("I love learning", 56).move_to([3.4, 0.4, 0])
        src_l = T("输入（中文）", 24, MUTED).next_to(src, UP, buff=0.35)
        tgt_l = T("输出（英文）", 24, MUTED).next_to(tgt, UP, buff=0.35)
        arr = Arrow(src.get_right(), tgt.get_left(), buff=0.35, color=W_COL, stroke_width=5)
        with self.say("最后来看解码器，我们拿翻译来举例：", "输入中文“我爱学习”，目标是输出对应的英文句子。") as s:
            self.play(FadeIn(src), FadeIn(src_l), run_time=0.8)
            s.until(1)
            self.play(GrowArrow(arr), run_time=0.7)
            self.play(FadeIn(tgt, shift=LEFT * 0.2), FadeIn(tgt_l), run_time=1.0)
        self.clear_stage()

        words = ["<开始>", "I", "love", "learning"]
        n, cell = 4, 0.9
        grid = VGroup()
        for r in range(n):
            for c in range(n):
                sq = Square(cell, stroke_color=BG, stroke_width=3)
                sq.set_fill(W_COL, opacity=0.55 if c <= r else 0.0)
                sq.move_to([c * cell, -r * cell, 0])
                grid.add(sq)
        grid.move_to([-2.0, -0.35, 0])
        cl = VGroup(*[T(w, 18, K_COL).next_to(grid[c], UP, buff=0.15) for c, w in enumerate(words)])
        rl = VGroup(*[T(w, 18, Q_COL).next_to(grid[r * n], LEFT, buff=0.18) for r, w in enumerate(words)])
        masked = VGroup(*[grid[r * n + c] for r in range(n) for c in range(n) if c > r])
        crosses = VGroup(*[VGroup(Line(sq.get_corner(UL), sq.get_corner(DR)), Line(sq.get_corner(UR), sq.get_corner(DL)))
                           .scale(0.45).set_stroke(MUTED, 2) for sq in masked])
        expl = VGroup(
            T("每一行只能看到", 26, FG), T("自己和之前的词", 26, W_COL, weight=BOLD),
            T("灰色 = 被遮住的“未来”", 24, MUTED),
        ).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to([3.6, -0.3, 0])
        with self.say("解码器每次只生成一个词，而且只能看到已经生成的部分。",
                      "所以它的自注意力要加上掩码，把未来的位置全部遮住，", "防止训练时“偷看答案”。") as s:
            self.play(FadeIn(cl), FadeIn(rl), run_time=0.8)
            self.play(LaggedStart(*[FadeIn(grid[r * n + c]) for r in range(n) for c in range(n) if c <= r],
                                  lag_ratio=0.08), run_time=1.6)
            s.until(1)
            self.play(masked.animate.set_fill(DIM, opacity=1.0), LaggedStart(*[Create(x) for x in crosses], lag_ratio=0.1),
                      run_time=1.5)
            self.play(FadeIn(expl[0:2], shift=LEFT * 0.2), run_time=0.8)
            s.until(2)
            self.play(FadeIn(expl[2]), run_time=0.6)
        self.clear_stage()

        enc = arch_box("编码器", FG, width=2.4, height=1.3, size=28).move_to([-4.7, 0.2, 0])
        src_row = token_row(["我", "爱", "学习"], size=22, buff=0.15, width=0.72).next_to(enc, DOWN, buff=0.6)
        src_arrows = VGroup(*[Arrow(t.get_top(), [t.get_x(), enc.get_bottom()[1], 0], buff=0.06, color=MUTED,
                                    stroke_width=2, max_tip_length_to_length_ratio=0.3) for t in src_row])
        mem = VGroup(*[vec_col(rand_vec(4, 600 + i), K_COL, cell=0.2) for i in range(3)]).arrange(RIGHT, buff=0.22)
        mem.next_to(enc, UP, buff=0.45)
        mem_l = T("上下文向量", 20, K_COL).next_to(mem, UP, buff=0.15)
        mem_arrow = Arrow(enc.get_top(), mem.get_bottom(), buff=0.05, color=MUTED, stroke_width=2.5,
                          max_tip_length_to_length_ratio=0.3)

        dec = arch_box("解码器", FG, width=2.6, height=1.3, size=28).move_to([0.0, 0.2, 0])
        dec_x0 = dec.get_left()[0] - 0.6
        with self.say("开始生成时，编码器先把整句输入读完，变成一组上下文向量。") as s:
            self.play(FadeIn(src_row), FadeIn(enc), run_time=0.8)
            self.play(LaggedStart(*[GrowArrow(a) for a in src_arrows], lag_ratio=0.2), run_time=0.8)
            self.play(GrowArrow(mem_arrow), LaggedStart(*[FadeIn(m, shift=UP * 0.2) for m in mem], lag_ratio=0.2),
                      FadeIn(mem_l), run_time=1.2)

        seq = VGroup(token_box("<开始>", color=Q_COL, size=18, width=0.95, height=0.5))
        seq.move_to([dec_x0 + 0.475, -1.55, 0])

        def seq_arrow():
            return Arrow([seq.get_x(), seq.get_top()[1], 0], [seq.get_x(), dec.get_bottom()[1], 0], buff=0.06,
                         color=MUTED, stroke_width=2.5, max_tip_length_to_length_ratio=0.3)

        in_arrow = seq_arrow()
        cross = VGroup(*[CurvedArrow(m.get_right() + RIGHT * 0.05, dec.get_left() + UP * (0.35 - 0.3 * i),
                                     angle=-PI / 5, color=K_COL, stroke_width=2.5, tip_length=0.15)
                         for i, m in enumerate(mem)])
        cross_l = T("交叉注意力", 20, K_COL).move_to([-2.2, 2.05, 0])
        with self.say("解码器通过交叉注意力，用自己的查询，去这些向量中寻找相关的信息。"):
            self.play(FadeIn(dec), FadeIn(seq), GrowArrow(in_arrow), run_time=1.0)
            self.play(LaggedStart(*[Create(c) for c in cross], lag_ratio=0.2), FadeIn(cross_l), run_time=1.5)
            self.play(Indicate(dec, color=K_COL), run_time=0.9)

        cands = [
            ["I", "We", "My", "Me", "<结束>"],
            ["love", "like", "enjoy", "am", "<结束>"],
            ["learning", "study", "to", "school", "<结束>"],
            ["<结束>", ".", "!", "and", "a"],
        ]
        probs = [
            [0.82, 0.07, 0.05, 0.03, 0.01],
            [0.78, 0.12, 0.05, 0.02, 0.01],
            [0.71, 0.14, 0.08, 0.03, 0.02],
            [0.88, 0.06, 0.03, 0.01, 0.01],
        ]
        px, bar_x0, bar_len = 3.35, 3.65, 2.6
        ys = [1.2 - 0.55 * i for i in range(5)]
        p_title = T("下一个词的概率", 22, W_COL).move_to([4.7, 1.85, 0])
        lin_arrow = Arrow(dec.get_right(), [2.45, 0.2, 0], buff=0.08, color=MUTED, stroke_width=3)
        lin_l = VGroup(T("线性层", 16, MUTED), T("+ softmax", 16, MUTED)).arrange(DOWN, buff=0.04).next_to(lin_arrow, UP, buff=0.08)

        def prob_panel(k):
            g = VGroup()
            for i, (w, p) in enumerate(zip(cands[k], probs[k])):
                col = W_COL if i == 0 else MUTED
                lab = T(w, 20, col).move_to([px, ys[i], 0], aligned_edge=RIGHT)
                bar = Rectangle(width=max(0.03, bar_len * p), height=0.3, stroke_width=0, fill_color=col,
                                fill_opacity=0.85 if i == 0 else 0.5).move_to([bar_x0, ys[i], 0], aligned_edge=LEFT)
                num = T(f"{p:.2f}", 16, col).next_to(bar, RIGHT, buff=0.1)
                g.add(VGroup(lab, bar, num))
            return g

        panel = prob_panel(0)
        with self.say("再经过线性层和 softmax，就得到词表中每个词的概率。"):
            self.play(GrowArrow(lin_arrow), FadeIn(lin_l), FadeIn(p_title), run_time=0.9)
            self.play(LaggedStart(*[FadeIn(r[0]) for r in panel], lag_ratio=0.1),
                      LaggedStart(*[GrowFromEdge(r[1], LEFT) for r in panel], lag_ratio=0.1),
                      LaggedStart(*[FadeIn(r[2]) for r in panel], lag_ratio=0.1), run_time=1.6)

        def append_step(k, rt):
            nonlocal panel, in_arrow
            word = cands[k][0]
            col = HL if word == "<结束>" else Q_COL
            new_tok = token_box(word, color=col, size=18, width=0.95 if len(word) > 4 else 0.8, height=0.5)
            new_tok.next_to(seq, RIGHT, buff=0.1)
            chosen = panel[0][0]
            self.play(Circumscribe(panel[0], color=W_COL, buff=0.06), run_time=rt * 0.3)
            self.play(TransformFromCopy(chosen, new_tok), run_time=rt * 0.35)
            seq.add(new_tok)
            new_arrow = seq_arrow()
            self.play(Transform(in_arrow, new_arrow), run_time=rt * 0.15)
            if k + 1 < len(cands):
                new_panel = prob_panel(k + 1)
                self.play(ReplacementTransform(panel, new_panel), run_time=rt * 0.2)
                panel = new_panel

        with self.say("选出概率最高的词，接到输入的末尾，再去预测下一个词。") as s:
            per = max(1.3, (s.left() - 0.2) / 2)
            append_step(0, per)
            append_step(1, per)

        with self.say("如此循环，直到生成结束符为止。") as s:
            per = max(1.2, (s.left() - 0.3) / 2)
            append_step(2, per)
            append_step(3, per)
            result = T("I love learning", 34, W_COL, weight=BOLD).move_to([0.3, 2.55, 0])
        self.play(FadeIn(result, shift=DOWN * 0.2), Circumscribe(VGroup(*seq[1:4]), color=W_COL), run_time=1.2)
        self.wait(0.4)
        self.clear_stage()


# ---------------------------------------------------------------- 10 总结
class S10_Summary(Narrated):
    def construct(self):
        self.play(self.chapter("10", "总结"))
        items = [
            ("1", "词嵌入 + 位置编码", "文字 → 带顺序信息的向量", EMB_COL),
            ("2", "自注意力", "每个词直接和所有词交流", Q_COL),
            ("3", "多头注意力", "从多个角度理解句子", K_COL),
            ("4", "前馈网络 + 残差 + 归一化", "网络很深也能稳定训练", V_COL),
            ("5", "解码器", "带掩码，一个词一个词地生成", HL),
        ]
        rows = VGroup()
        for num, head, desc, col in items:
            badge = VGroup(Circle(0.3, stroke_color=col, stroke_width=3).set_fill(col, 0.2), T(num, 26, col, weight=BOLD))
            text = VGroup(T(head, 32, col, weight=BOLD), T(desc, 27, FG)).arrange(RIGHT, buff=0.5)
            rows.add(VGroup(badge, text).arrange(RIGHT, buff=0.35))
        rows.arrange(DOWN, buff=0.36, aligned_edge=LEFT).move_to([0, 0.6, 0])
        lines = [
            "文字先变成词向量，再加上位置编码；",
            "自注意力，让每个词都能直接和所有词交流；",
            "多头注意力，从多个角度同时理解句子；",
            "前馈网络、残差连接和层归一化，让很深的网络依然稳定有效；",
            "解码器再借助掩码，一个词一个词地生成结果。",
        ]
        with self.say("最后，我们把整个流程串起来回顾一遍："):
            self.wait(0.3)
        for r, line in zip(rows, lines):
            with self.say(line):
                self.play(FadeIn(r, shift=RIGHT * 0.3), run_time=0.8)

        bottom = T("高效并行  +  擅长捕捉远距离关系  →  大语言模型的基石", 30, W_COL, weight=BOLD).move_to(DOWN * 2.3)
        with self.say("正因为能够高效并行，又擅长捕捉远距离的关系，", "Transformer 成为了如今大语言模型的基石，",
                      "像 GPT 这样的模型，用的就是其中的解码器部分。") as s:
            self.play(Write(bottom), run_time=1.6)
            s.until(2)
            self.play(Indicate(rows[4], color=HL, scale_factor=1.05), run_time=1.5)
        self.clear_stage()

        title = T("Transformer", 100, weight=BOLD).set_color_by_gradient(Q_COL, PE_COL, HL)
        sub = Tex(r"\textit{Attention Is All You Need}", font_size=44, color=MUTED).next_to(title, DOWN, buff=0.4)
        thanks = T("感谢观看", 36, FG).next_to(sub, DOWN, buff=0.6)
        with self.say("感谢观看！"):
            self.play(FadeOut(self.chapter_label), GrowFromCenter(title), run_time=1.0)
            self.play(FadeIn(sub), FadeIn(thanks, shift=UP * 0.2), run_time=0.8)
        self.wait(1.5)
        self.play(FadeOut(VGroup(title, sub, thanks)), run_time=1.0)
