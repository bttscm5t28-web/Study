# 《从一个像素开始》 From One Pixel

A 76.8-second concept promo film for **Claude Fable 5.1**, Anthropic's most capable model, built entirely from code:
a deterministic Canvas 2D renderer, a procedural numpy/scipy score, and five photographs that are never cut to —
they *resolve*, from a flat four-colour mosaic to the real thing.

- 成片 Film: [`output/from_one_pixel.mp4`](output/from_one_pixel.mp4) · 1920×1080 · 30 fps · 76.8 s · H.264 + AAC
- 故事板 Storyboard bible: [`docs/storyboard.md`](docs/storyboard.md) (palette, grid, type, music, every snap to the frame)

## The idea

One ember square asks what it is. Every capability of the model adds one notch of resolution — *think, see, remember,
carry through, read the codebase* — until the answer lands: a face. Then the same grid zooms out — face → people → city →
planet — each arrival resolving faster and in more colour, until nothing is left to resolve and a person looks up at a
real sky. The last frame is the first pixel again.

**FLAT = GUESS, COLOUR = REAL.** Block sizes 120 / 60 / 30 px are drawn with four tokens only (ink, slate, paper,
ember); 15 px gets an 8-colour palette, 5 px 32 colours, 1 px the photograph. The score does the same: a single
110 Hz sine gains partials, a pulse, chords, and ends on the same A with its first eight harmonics.

| 时间 | 场景 | 文案 | 画面 |
| --- | --- | --- | --- |
| 0.0 | 一个像素 | 一个像素。 | one 120-px ember cell on ink |
| 6.4 | 先想，再答 | 它是什么？／先想，再答。 | the cell splits 2×2; a dial is set from LOW to MAX |
| 12.8 | 它开始看见 | 它开始看见。 | the 120-px field floods out from the origin, one ring per 8th |
| 19.2 | 记住全部 | 记住全部，不只片段。 | 60 px; the numeral rolls to 1,000,000 |
| 22.4 | 做到完成 | 一件事，做到底。 | 30 px; one line forks into four lanes and rejoins |
| 28.8 | 读遍代码 | 读遍代码，再写。 | 15 → 5 px in colour; the headline resolves through the mosaic |
| 32.0 | 原来，是一张脸 | 原来，是一张脸。 | the face, real, on the Fmaj7 |
| 38.4 | 不止一个人 | 不止一个人。 | collapse → people, resolving on beats |
| 41.6 | 是一座城 | 再远一些，是一座城。 | → a city at night (Los Angeles), resolving on 8ths, then reversed in the vacuum |
| 48.0 | 再高一些 | 再高一些，世界清晰了。 | IMPACT → Earth at night, a detail-first quadtree on 16ths |
| 54.4 | 边界 | 越有能力，越知边界。 | a hairline boundary closes around the world |
| 57.6 | 然后，抬头 | 然后，抬头。／每个上限，都是起点。 | a person under the Milky Way; nothing left to resolve |
| 70.4 | Claude Fable 5.1 | 我们迄今最强大的模型 · Anthropic | lockup, then the pixel returns |

Grid: 75 BPM, 24 bars, bar = 3.2 s = 96 frames, so every beat, 8th and 16th is frame-exact and every scene boundary
sits on a bar line. All copy is set under a hairline "ceiling" (「上限」) that lifts one grid row per scene and leaves
the frame just before the face lands.

## Build

```bash
pip install numpy scipy pillow fonttools      # python 3.11
# node 22 + playwright (Chromium) + ffmpeg are required
./build.sh
# or step by step:
python3 tools/bake.py                         # quantized mosaic stages + Earth quadtree → build/bake/
python3 music/compose.py                      # procedural score → music/track.wav
node render.js --out output/from_one_pixel.mp4
node render.js --stills 3.6,32.0,51.2 --dir build/stills   # frame stills for review
python3 tools/sync_check.py                   # audio ↔ picture hit-point check
```

Preview in a browser (needs the baked stages and the track): serve the folder, open `index.html?play=1`, click.

## Files

| path | role |
| --- | --- |
| `src/engine.js` | time-driven Canvas helpers: easing, tracked type, block mosaic, detail-first quadtree |
| `src/scenes.js` | the film — every frame is a pure function of `t` |
| `timeline.json` | the contract shared by picture and score: fps, BPM, duration, stage images |
| `tools/bake.py` | window crops, Oklab percentile quantizer, two-level 60-px rule, median-cut palettes, quadtree generations |
| `music/synth.py` | band-limited oscillators, envelopes, filters, FDN reverb, compressor, limiter, BS.1770 loudness, instruments |
| `music/compose.py` | the score, bar by bar, from the storyboard's hit table |
| `render.js` | Playwright drives Chromium frame by frame and pipes PNGs into ffmpeg |
| `tools/subset_fonts.py` | subsets the CJK fonts to the glyphs the film uses |

## Assets

Photographs are from Unsplash (licence: https://unsplash.com/license): `1438761681033-6461ffad8d80` (the face),
`1511632765486-a01980e01a18` (people), `1444723121867-7a241cacace9` (Los Angeles at night), `1451187580459-43490279c0fa`
(Earth at night, used rotated 180°), `1444703686981-a3abbc4d4fe3` (under the Milky Way).
Fonts (SIL Open Font License, via Google Fonts): Noto Serif SC, Noto Sans SC, Inter, Instrument Serif, Space Grotesk.
No logo is used; the brand appears as plain type. This is a concept piece, not an Anthropic publication.
