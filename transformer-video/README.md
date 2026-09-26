# Transformer 机制讲解动画

一段 7 分钟的中文讲解动画，配有旁白和字幕，从零讲清楚 Transformer 是怎么工作的。

- 成片：[`output/transformer_explained.mp4`](output/transformer_explained.mp4)（1080p · 30fps）
- 字幕：[`output/transformer_explained.srt`](output/transformer_explained.srt)
- 旁白稿：[`output/narration.md`](output/narration.md)

## 章节

| 时间 | 章节 | 内容 |
| --- | --- | --- |
| 00:00 | 开场 | Transformer 与论文 *Attention Is All You Need* |
| 00:23 | 01 为什么需要 Transformer | RNN 逐词接力、信息衰减、无法并行 vs. 所有词直接相连 |
| 00:59 | 02 整体结构 | 编码器 / 解码器、N=6 层堆叠、注意力 + 前馈网络 |
| 01:30 | 03 词嵌入 | 切分 token、查嵌入表、d_model=512、语义空间 |
| 02:02 | 04 位置编码 | “猫追狗”≠“狗追猫”、正弦/余弦位置编码、与词向量相加 |
| 02:33 | 05 自注意力：Q、K、V | “它”指谁？三个权重矩阵、图书馆类比 |
| 03:21 | 06 注意力是怎么算的 | 点积 → ÷√dₖ → softmax → 加权求和，注意力矩阵与公式 |
| 04:11 | 07 多头注意力 | 指代 / 相邻 / 句法等不同的头、拼接 + W^O |
| 04:49 | 08 前馈网络 · 残差 · 层归一化 | 512→2048→512、残差连接、LayerNorm、多层堆叠 |
| 05:28 | 09 解码器 | 掩码自注意力、交叉注意力、softmax 概率、逐词生成 |
| 06:18 | 10 总结 | 五个要点回顾，GPT 只用解码器 |

## 用到的例子

全片贯穿同一个句子：**“小猫没有过马路，因为它太累”**。
看“它”如何通过注意力找到“小猫”：点积打分 → 除以 √dₖ → softmax → 对值向量加权求和，
最后推广到矩阵形式 `Attention(Q,K,V) = softmax(QKᵀ/√dₖ)V`。
解码器部分用“我爱学习 → I love learning”演示掩码和逐词生成。

## 自己生成

动画用 [Manim Community](https://www.manim.community/) 绘制，旁白用离线语音合成
[Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)（通过 [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) 运行，
普通话男声 `zm_yunxi`，中英混读），字幕由 ffmpeg/libass 烧录。

系统依赖（Ubuntu）：

```bash
apt-get install ffmpeg libpango1.0-dev libcairo2-dev pkg-config fonts-noto-cjk \
    texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended dvisvgm
pip install -r requirements.txt
```

生成：

```bash
python build.py              # 1080p 成片 → output/
python build.py --preview    # 480p 快速预览
python build.py --only S06_AttentionMath   # 只重渲染某个场景，其余沿用已有结果
manim -ql scenes.py S07_MultiHead          # 单独预览一个场景
```

首次运行会从 Hugging Face 下载语音模型（约 380 MB）到 `voices/`，合成结果缓存在 `build/tts/`。

## 文件结构

| 文件 | 作用 |
| --- | --- |
| `scenes.py` | 各章节的动画场景，旁白文本直接写在对应动画旁边 |
| `common.py` | 配色、通用组件，以及 `Narrated.say()`：播放旁白并让动画与语音对齐、记录字幕时间 |
| `tts.py` | Kokoro 语音合成与缓存 |
| `build.py` | 并行渲染 → 拼接 → 生成 SRT → 烧录字幕、响度归一化 |

改旁白只需改 `scenes.py` 里 `self.say(...)` 的文字，时长和字幕会自动跟着变。
