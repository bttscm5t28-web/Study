# Transformer 机制讲解动画

一段约 7 分钟的中文讲解动画，配有旁白和字幕，从零讲清楚 Transformer 是怎么工作的。

- 成片：[`output/transformer_explained.mp4`](output/transformer_explained.mp4)（1080p · 30fps）
- 字幕：[`output/transformer_explained.srt`](output/transformer_explained.srt)
- 旁白稿：[`output/narration.md`](output/narration.md)

## 章节

| 时间 | 章节 | 内容 |
| --- | --- | --- |
CHAPTERS

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
