# FINAL STORYBOARD BIBLE — 《从一个像素开始》 From One Pixel
Claude Fable 5.1 concept promo · 1920×1080 · 30 fps · 76.8 s = 24 bars @ 75 BPM · Canvas 2D + numpy/scipy score

## 0. Logline, lineage, applied fixes
- Logline: a single ember square asks what it is. Every capability of Claude Fable 5.1 adds one notch of resolution — think, see, remember, carry through, read the codebase — until the answer lands: a face. Then the same grid zooms out — face → people → city → planet — each arrival resolving faster and in more colour, until nothing is left to resolve and a person looks up at a real sky. The last frame is the first pixel again.
- Base = winning concept "从一个像素开始" (one answer being refined; mosaic as the ONLY transition device; additive-synthesis score; 75 BPM so every subdivision is frame-exact).
- Grafted from the other concepts: (1) pad low-pass cutoff = the finest block size on screen ("the ear hears the picture open", from 分辨率); (2) "FLAT = GUESS, COLOUR = REAL" stated as a hard rule with colour-depth as its own rung in the city resolve (分辨率); (3) the CEILING rule 「上限」 — a hairline the copy may never rise above, lifting one grid row per resolve and leaving the frame in the bar before the face lands, so the face arrives on a frame with nothing else on it (再高一些); (4) the comparative copy ladder 再远一些 / 再高一些 feeding into 每个上限，都是起点 (再高一些); (5) a "people" rung (photo 38) so the scale ladder reads pixel → person → people → city → planet and the single-photo stretch is shorter (judges' fix); (6) hard rule of three and two speeds only (SNAP / GLIDE) formalised (分辨 · Resolve / 分辨率).
- Judges' fixes applied: origin cell at the face's native position (no upscale, 1× crop); face sequence trimmed by one bar; eyebrows capped at short noun phrases; English rewritten ("Every ceiling, the next floor."); mosaic-text starts at 30 px, never 48; quadtree defined on an exact-tiling ladder with a precomputed split order and a one-8th hold so the impact lands on a legible frame; bar-10 cue contradiction resolved (legibility on C5 at 30.4, the 5-px step on A5 at 31.2); photo 51 graded toward the palette; tail re-cut so the person lands ON the Cmaj9 at 57.6 and the breath is four bars; opening made audible on phone speakers; "black" is ink everywhere; the sampling rule is explicit (independent block sample per stage, anchored top-left, every size tiles 1920×1080 exactly); the 2×2 split is guaranteed to show variance.
- Revision 2 (every geometric and colour claim below was measured on the catalogue thumbs at the §4 windows: 16:9 window, 120-px block means, linear RGB → Oklab; the §5 gates re-measure on the fetch): origin re-derived from the real face position (column 9, row 4 — the nose sits on the column 8|9 boundary); per-photo percentile quantizer replaces fixed thresholds; the flood is 8 rings, complete on 15.6; photo 08 rotated 180° so the copy lands on space; photo 32 fetched at 2880 and windowed so the figure clears the headline and the copy sits on the ground; photos 38 and 51 windowed at the top of their vertical range; the paper token is pinned at 55 % on every flat stage and type turns to ink over the face's real-colour stages (the lake under the copy is paper-bright; no window of photo 54 avoids it — measured at every offset); the ceiling leaves 28.8–30.4, before colour arrives, because no 1-px hairline survives the bright sky at y 120; quadtree re-timed (generation 14 on the 51.2 downbeat) and re-specified as a deterministic quota; S08 re-timed so the copy leaves as the people arrive; dial payoff at 12.0; agent line arrives at 28.4; all exits 4 frames; numeral roll lands on 20.0; music timing contradictions removed; S06 headline shortened to 8 glyphs so it stays on the lake.

## 0b. Revision 3 — after the five-lens review of the rendered film (what the film actually does; where this differs from §1–§5 below, this section wins)
- Landings are visible jumps: the rung before a landing is never within one colour depth of real. Face: 25.6 → 15 px four tokens (80 %), 28.8 → 15 px @ 8 colours (85 %), 31.2 → 5 px @ 8 colours (92 %), 32.0 → real. City: 44.0 → 5 px @ 8 colours, 44.4 → 5 px @ 32 colours, 44.8 → real. Earth: generations 1–13 split to depth ≤ 4 (5 px) and stay in the 8-colour palette; generation 14 on 51.2 is one snap to real colour at 1 px over the whole frame.
- City photograph is 76 (Los Angeles city lights at night, aerial — amber on ink, in palette, no grade), not 51. Window T = 200. Copy unchanged (再远一些，是一座城。).
- The ceiling rule exits 27.2 → 28.8 (240 → 120 → off the top on the 28.8 snap, together with the agent line), so it leaves before colour arrives and is never drawn over a real-colour stage (§5.5 now holds).
- The impact is a lift, not a drop: city reverse brightness 85 / 70 / 60 / 50 % (15 / 30 / 60 / 120 px) and Earth generation 0 at 70 % rising to 100 % on 51.2.
- Copy: S04 「记住全部，不只片段。」 / 'All of it, not a fragment.' (English on the next 8th, 20.4); S05 「一件事，做到底。」; S06 eyebrow 'CLAUDE CODE · WHOLE CODEBASES', English 'Read it all. Then write.'; S08 English on 39.2; S09 copy held through the reverse (exit → 48.0); S11 「越有能力，越知边界。」; lockup 「我们迄今最强大的模型」 with 'Anthropic' entering together with it at 71.2; title 76 px.
- Type: eyebrows 20 px at 88 %; 「上限」 18 px at 70 %; full-width punctuation compressed to 0.55 em (标点挤压); mosaic-text stages are thresholded to pure ink cells.
- Devices: agent line 85 %; boundary on the grid (inset 120 px: x 120–1800, y 120–960); step ticks added at 24.0 / 25.6 / 27.2; pad cutoff 1.4 kHz at 25.6, 2.2 kHz at 28.8, 3 kHz at 31.2; closing ladder 1.4 k / 900 / 600 / 400 Hz on 46.4 / 46.8 / 47.2 / 47.6.
- Sky push-in 9 % over 12.8 s. H.264 stream tagged BT.709 / TV range.

## 1. Grid, palette, typography, motion language

### 1.1 Grid and origin
- Film grid: 120-px cells, 16 columns × 9 rows, anchored at (0,0). Columns 1–16, rows 1–9, 1-indexed.
- Block ladder for EVERY mosaic in the film: **120 / 60 / 30 / 15 / 5 / 1 px**. Each divides 1920 and 1080 exactly and nests into the previous one (÷2, ÷2, ÷2, ÷3, ÷5). No other block size ever touches an image. (Mosaic-text uses 30 / 15 / 5 / 1 on the text raster.)
- ORIGIN CELL = column 9, row 4 → x 960–1080, y 360–480, centre (1020, 420): her right eye and cheek — the cell just right of the nose, which sits on the column 8|9 boundary (x ≈ 960) in photo 54 at the film's window (§4: 1920-px 3:2 fetch, window top T = 60, eye line measured at y ≈ 435–450, inside row 4). The cell is warm skin and quantizes to ember by §1.2 (measured L 0.68, hue 55°). Derived, not chosen: gate (a) in §5 prints the fetch's token map before any scene is coded. If the fetch puts the eye line outside y 380–470, T is re-chosen in 10-px steps inside 40–100 and the origin stays column 9 / row 4; the face is centred in the 3:2 frame and a 1920-px fetch has no horizontal freedom, so the origin never moves by column.
- Copy safe area: x 160–1260 (max copy width 1100 px). The origin column lies inside that x-range; nothing overlaps because the only origin-centred device, the dial, bottoms out at y 593 and the copy block never rises above the eyebrow top (y 693 under a two-line headline). The copy block never moves.
- Element budget (rule of three): ground (field / photograph / ink) + copy block + one device. The ceiling rule is page structure and does not count.

### 1.2 Palette — four tokens, nothing else in any flat graphic
| token | hex | use |
|---|---|---|
| ink | #0B0B0E | background always; every "black" in this document is ink; the end frame; type over the face's real-colour stages (28.8–38.4) |
| paper | #F3EFE7 | all other type; hairlines at 45–70 % opacity; the field's paper token is pinned at 55 % (#868380) |
| ember | #E8613A | the single pixel (first and last frame); whatever the quantizer maps to ember; never type |
| slate | #3A3F4B | the quantizer's cool mid-tone; darken to #2E323C only if gate (c) fails |
- FLAT = GUESS, COLOUR = REAL. Colour depth by block size: 120 / 60 / 30 px → the 4 tokens only; 15 px → that photo's 8-colour median-cut palette; 5 px → 32 colours; 1 px → full colour. Photographs are the only source of other colours, and only from 15 px down. Exception: in S09 colour depth may lead resolution by one rung (30 px @ 8 colours, 5 px @ full) so colour arrives as its own beat.
- Brightness ladder: face 55 / 65 / 75 / 85 / 92 / 100 % (one step per block size); people 70 / 80 / 90 / 100 % (120 / 60 / 30 / 1 px); city 55 → 100 % across the resolve, back to 70 % across the reverse; planet 55 → 100 % linearly over the cascade. The ladder scales ember, slate and ink cells and every real colour. THE PAPER TOKEN IS PINNED: at every flat stage the field's paper cells render at 55 % (#868380) whatever the ladder says, so type (paper 100 %) always sits ≥ 3.2:1 above the brightest flat cell; the guess is never as bright as the answer.
- 4-token quantizer, per photo, by percentile: take the 144 block means at 120 px (linear RGB → Oklab), P25 and P80 of their L. ink = L < P25; slate = P25 … P80; paper = L > P80; ember overrides when hue ∈ [10°, 70°], chroma > 0.045 and L > P25. The two thresholds are frozen per photo and reused unchanged for its 60- and 30-px stages (and for quadtree depths 0–2 of photo 08). Measured on the thumbs at the §4 windows: 54 (P25 0.55 / P80 0.75) → ember column 9 rows 3–7 (cheek and jaw), ink in the hair columns 7 and 10–11 and at the eyes, paper on the sky row 1 and the lake's lit band (rows 5–7, columns 3–5 and 13), slate elsewhere (6 ember / 36 ink / 29 paper / 73 slate); 38 → ink figures (columns 7–11, rows 4–8) and an ink ground row, ember sun and lit hillside, paper sky; 51 → a horizontal band of paper and ember lights (rows 6–8) on slate, ink sky corners and river bottom; 08 rotated → slate ocean rows 1–2, paper/slate lit band rows 3–6, slate limb glow row 7, ink space rows 8–9; 76 → paper skyline band row 3 on slate, ink bottom row. At the 60-px stage each token may appear at the stage level or at stage − 15 % (two levels per token, split at that token's median L over the stage; pinned paper's levels are 55 / 40 %; no new hues) so the 2×2 split in S02 shows variance.
- TYPE COLOUR: paper everywhere except 28.8–38.4, the face's real-colour stages (15 px @ 8 colours, 5 px @ 32 colours, 1 px). There the lake under the copy block is paper-bright (sRGB 170–205 at every vertical offset of photo 54; measured), so every line is INK (#0B0B0E) at the usual opacities — headline 100 %, English 72 %, eyebrow 50 %, mosaic-text ink on transparent. The only ink type in the film: it begins on the frame colour arrives (28.8) and ends with the collapse (38.4).
- Grading: photo 51 at its 1-px stage −25 % saturation, blue channel pulled 10 % toward slate. Photos 38, 08, 32, 54 ungraded. Never a grade for luminance, never a scrim. No gradients, shadows, glow, blur, vignettes, particles, lens effects. No #000, no #FFF.
- Pre-bake in Python (PIL): for each (photo, block size) a quantized PNG at the §4 window; for photo 08 (rotated) the 15 quadtree generations as bitmaps; for the headline of S06 the 30/15/5-px text rasters (ink). The Canvas renderer only blits and draws hairlines/type.

### 1.3 Typography (all px at 1920×1080)
- HEADLINE zh — Noto Serif SC 600, 72 px, tracking +0.08em (advance 77.76 px per glyph), line-height 1.3 (94 px), paper 100 % (ink in S06–S07), left-aligned x = 160, baseline y = 880; two-line blocks: baselines 786 / 880; max two lines, max width 1100 px (14 glyphs).
- ENGLISH — Instrument Serif Italic 400, 32 px, tracking +0.01em, paper 72 % (ink 72 % in S06–S07), x = 160, baseline y = 932; always enters one beat after the Chinese.
- EYEBROW (facts) — Space Grotesk 500, 18 px, UPPERCASE, tracking +0.22em, paper 50 % (ink 50 % in S06), ' · ' separators, x = 160, baseline y = 800 (y = 706 under a two-line headline); short noun phrases only, max four.
- CEILING LABEL 「上限」 — Noto Sans SC 400, 14 px, tracking +0.20em, paper 50 %, right-aligned to x = 1260, baseline 18 px BELOW the rule (nothing sits above the ceiling).
- NUMERAL (S04) — Instrument Serif Regular, 200 px, paper 92 %, x = 160, baseline y = 560; digits drawn glyph-by-glyph at a fixed advance (tabular emulation), commas included.
- DIAL LABELS (S02) — Space Grotesk 500, 14 px, uppercase, tracking +0.20em, paper 55 %, baseline y = 575, beside the arc's open ends: 'LOW' right-aligned to x 878, 'MAX' left-aligned at x 1162 (the arc passes x 894 and x 1146 at that height, 16 px clear). Device labels, not copy: they may sit above the ceiling rule.
- MOSAIC-TEXT (S06) — the headline rastered to an offscreen canvas (ink on transparent) and block-sampled at 30 / 15 / 5 / 1 px, same position as a normal headline.
- LOCKUP (S13), the film's only centred composition: 'Claude Fable 5.1' Inter 500, 64 px, tracking −0.015em, paper 100 %, centred, baseline y = 528; 「我们能力最强的模型」 Noto Sans SC 300, 26 px, tracking +0.20em, paper 80 %, baseline y = 592; 'Anthropic' Inter 500, 24 px, tracking +0.18em, paper 65 %, baseline y = 648. Plain type, no mark, no rule.
- Type entry: 16-px rise + opacity; expo-out 420 ms on position, 300 ms on opacity; always on a beat or an 8th. EXIT: opacity only, 4 frames (133 ms), ending on the next downbeat — "exit → T" everywhere in this document means the fade occupies the four frames before T and the first frame of T is clean. The dial fade is the same 4 frames; the lockup fade is 9 frames (300 ms). Nothing else fades.

### 1.4 Motion language
(a) Two speeds only for cuts, block-size changes and hairlines. SNAP = one frame, on a beat subdivision, never tweened, never blurred: every cut and every block-size change. GLIDE = constant-speed hairline draws and ≤ 6 % push-ins on held photographs. Nothing in between; no easing on hairlines; no bounce, no overshoot. Type is the one thing that eases: it uses the §1.3 entry curve and the 4-frame exit, nothing else.
(b) Scale changes pass through the 120-px grid: real → 120 px (one snap) → block colours swap to the next subject (one snap, in-palette, so every intermediate frame is flat) → resolve. There are no crossfades anywhere in the film.
(c) Escalation, three ladders coupled: step time face 6.4 s → people 0.8 s (beats) → city 0.4 s (8ths) → planet 0.2 s (16ths); colour depth 4 tokens → 8 → 32 → full (the people rung goes flat → real in one snap, 30 px → 1 px); brightness 55 → 100 %.
(d) Hairlines: 1 px, constant speed, never rotate. The ceiling rule rises at 150 px/s (one grid row per beat); its exit is the same move continued — from 240 it rises two rows in two beats (28.8–30.4) and is out of frame on 30.4.
(e) Camera: one push-in per held photograph, linear, ≤ 6 %; never during a snapping bar; hairlines and type are never scaled (the push-in is applied to the photograph only).
(f) Sampling rule: every stage is an independent block-sample of the source photograph at block size b, grid anchored at (0,0). The quadtree uses the same ladder as nested depths 0–5; children per depth: 4, 4, 4, 9, 25 (60 → 30 → 15 are 2×2 splits, 15 → 5 is 3×3, 5 → 1 is 5×5).
(g) THE CEILING RULE (grafted): 1-px paper hairline at 50 %, x 160 → 1260, labelled 「上限」 at its right end. Drawn left→right over one beat at 6.4 at y = 600. It is the ceiling of the copy block: no eyebrow, headline, numeral or English ever rises above it. It lifts one grid row on every act-one scene downbeat — 480 at 12.8, 360 at 19.2, 240 at 22.4 — and at 28.8, the frame colour arrives, it lifts through 120 (29.6) and off the top on 30.4 (b10.3), the beat the codebase line becomes legible. The face lands at 32.0 on a frame with nothing on it but the photograph. The rule never returns: the zoom-out, the sky and the lockup are set with no ceiling on screen. (Only hairline that moves; the dial, the agent line and the boundary are drawn in place.)
(h) PAD FILTER = RESOLUTION (grafted): the pad's 2-pole low-pass cutoff is a step function of the finest block size on screen — 120 px → 400 Hz, 60 → 600, 30 → 900, 15 → 1.4 kHz, 5 → 2.2 kHz, 1 px → 4 kHz — gliding 100 ms at each snap; it closes with the city's reverse (46.4 → 47.6: 2.2 k → 1.4 k → 600 → 400 Hz; the pad is held at −12 dB through the vacuum so the close is audible), sweeps 400 → 4 kHz log-linearly across the quadtree (48.0 → 51.2, 4 kHz on the Fmaj7) and stays open to the end.
(i) The frame is never empty for more than one beat except the final ink; the only full-frame luminance jumps are the two reveals (32.0, 44.8) and the impact.

## 2. Music
- 75 BPM, 4/4. Bar = 240/75 = 3.200 s = 96 frames; beat 0.8 s = 24 f; 8th 0.4 s = 12 f; 16th 0.2 s = 6 f. 24 bars = 76.8 s = 2304 frames. Every scene boundary is a bar line; every snap is on a beat, 8th or 16th; every one of them is frame-exact. Notation below: "b7.3" = bar 7, beat 3 = 19.2 + 1.6 = 20.8 s; "+" = the 8th after that beat. Bar n starts at (n−1) × 3.2.
- Key: A minor (Aeolian) on a 110 Hz pedal; bVI (Fmaj7) for the first landing, iv (Dm9) for the turn, bVII (G add9) for the rise, relative major (Cmaj9) for the resolution chord that lands on the human; Fmaj9 breath; final unison A carrying harmonics 1–8 (the opening tone at full resolution).
- The score is additive synthesis made audible: one sine gains partials, a pulse, voices, chords, and ends on the same A with its full harmonic series. Same note, higher resolution.

### 2.1 Structure by bar
| bars | time | section | harmony | content |
|---|---|---|---|---|
| 1–2 | 0.0–6.4 | ONE TONE | A pedal | sine A2 110 Hz (carrier) + A1 55 Hz (support) + A3 220 Hz at −12 dB from frame 0; tick with click at 0.8; A3 rises to −6 dB at 3.2; soft quarter-note ticks from 3.2 (−18 dB) |
| 3–4 | 6.4–12.8 | PARTIALS | A pedal | E4 enters 6.4 (harmonic 3), A4 enters 9.6 (harmonic 4); harmonic 5 skipped so no major third colours the pedal; quarter ticks −12 dB |
| 5–7 | 12.8–22.4 | PULSE I | Am(add9) | pad opens at 400 Hz; pluck ostinato A3–E4 on 8ths with dotted-8th delay; a two-note 16th pickup 15.6–16.0 (flood finale) and a 16th roll 19.2–20.0 (numeral); no kick |
| 8–9 | 22.4–28.8 | PULSE II | Am(add9) | kick on 1 & 3 and 16th hats enter 22.4; pluck doubles to A3 E4 A4 E4 at 24.0, back to two notes at 27.2 |
| 10 | 28.8–32.0 | FILL | Am(add9) | eight ascending plucks on 8ths: A3 28.8 · C4 29.2 · E4 29.6 · A4 30.0 · C5 30.4 · E5 30.8 · A5 31.2 · C6 31.6 |
| 11–12 | 32.0–38.4 | LIFT | Fmaj7 | chord lifts on the face; kick rests all of bar 11 (the inhale), returns four-on-the-floor at 35.2; shimmer enters quietly |
| 13 | 38.4–41.6 | TURN | Dm9 | kick four-on-the-floor continues; pluck shifts to D4–A4; step ticks on 38.4 / 38.8 / 39.2 / 40.0 / 40.8 |
| 14–15 | 41.6–48.0 | RISE | G(add9) | 6.4-s riser ending on 48.0; kick on every beat; hats accent each 8th-note step; VACUUM 46.4–48.0: everything cuts except the riser, the 1.6-s reversed-reverb swell and the pad held at −12 dB (its cutoff closing 2.2 k → 400 Hz is the reverse, heard) |
| 16–19 | 48.0–60.8 | CLIMAX | Am(add9) · Fmaj7 · G · Cmaj9 | IMPACT 48.0 (bar 16 full stack); 13 ticks on 16ths 48.4–50.8; the last 16th of bar 16 (51.0) holds; Fmaj7 51.2 (generation 14, Earth real); G 54.4; bar 19 Cmaj9 half-time, hats off — the cut to the human lands on it |
| 20–22 | 60.8–70.4 | BREATH | Fmaj9 | pad only, no sub, no percussion; shimmer arpeggio with long delay from 60.8; the pad adds E5 (its 9th, an octave up) at 64.0 — brightest voicing of the film |
| 23–24 | 70.4–76.8 | CODA | A unison | all voices collapse to A2 with harmonics 1–8 at 1/n; 1.6-s release from 74.4 (ends 76.0); last tick 75.2; silence by 76.0; 0.8 s of silence to 76.8 |

### 2.2 Instrumentation (all synthesized in numpy/scipy)
1. PIXEL TONE — sine A2 110 Hz (the carrier; it must read on laptop and phone speakers) + sine A1 55 Hz at −6 dB (support only) + sine A3 220 Hz at −12 dB from frame 0 (rises to −6 dB at 3.2); 0.8-s attack.
2. PARTIALS — sines E4 330 Hz (6.4) and A4 440 Hz (9.6), 0.4-s attacks.
3. TICK — 30-ms 110 Hz sine burst with 2-ms attack + an 8-ms 2.5 kHz click component so it cuts through on any speaker; quarter notes in bars 2–4 (−18 → −12 dB); one per quadtree generation 48.4–50.8 (13 ticks); final tick 75.2.
4. STEP TICK — 12-ms band-passed noise 3–6 kHz at −16 dB; marks the collapse and swap snaps (38.4, 38.8, 41.6, 42.0) and the three beat-steps of S08 (39.2, 40.0, 40.8).
5. PAD — 3 detuned saws per voice (±7 cents), 2-pole low-pass whose cutoff follows the picture (§1.4 h), 3-s attack, into a 4-s synthetic plate (exponentially decaying noise IR, fftconvolve). Ducked −3 dB by the kick, 200-ms release. Held at −12 dB, not cut, through the vacuum 46.4–48.0.
6. PLUCK — Karplus–Strong string, 0.6-s decay, dotted-8th (0.6 s) feedback delay at 30 %.
7. KICK — sine drop 55 → 40 Hz over 120 ms + 5-ms noise click; low-passed so it never reads as club.
8. HAT — white noise, 6 kHz high-pass, 30-ms decay, 16ths at −18 dB, accents on 8ths.
9. RISER — band-passed noise sweeping 200 Hz → 8 kHz over 6.4 s (41.6 → 48.0) + a sine gliding A3 → A5 over the same span.
10. IMPACT — 40-ms noise burst + sub drop 60 → 30 Hz with 1.5-s decay into the plate, preceded by the 1.6-s time-reversed pad-reverb swell (46.4–48.0).
11. SHIMMER — sine arpeggio A5 C6 E6 G6 on quarter notes, 1.6-s delay at 50 % feedback, −20 dB.
12. CODA TONE — A2 with harmonics 1–8 at amplitude 1/n (soft organ-saw), gently low-passed, 1.6-s release from 74.4.
Mix: master −1 dBTP; 2 dB of headroom reserved for 48.0–49.0; sidechain only on pad/sub; reverb on a separate wet bus so the vacuum at 46.4 can gate it (5-ms ramp, keep 20 %).

### 2.3 Hit points (exact)
| t | bar.beat | music | picture |
|---|---|---|---|
| 0.0 | b1.1 | A2 + A1 fade in over 0.8 s, A3 under at −12 dB | ink |
| 0.8 | b1.2 | first tick (+ click) | ember pixel cuts in at the origin cell (x 960–1080, y 360–480) |
| 3.2 | b2.1 | A3 rises to −6 dB; soft quarter ticks begin | 「一个像素。」 rises |
| 6.4 | b3.1 | E4 enters; ticks −12 dB | pixel splits 2×2; dial starts; ceiling rule draws at y 600 |
| 9.6 | b4.1 | A4 enters | 「先想，再答。」 |
| 12.0 | b4.4 | tick | arc arrives at 5 o'clock; 'MAX' snaps in |
| 12.8 | b5.1 | pad Am(add9) opens at 400 Hz; ostinato starts | flood ring 1; dial gone (faded 12.6667–12.8); ceiling → 480 |
| 13.2 → 14.8 | 8ths b5.1+ → b5.3+ | one pluck per ring | rings 2–6 |
| 15.2 | b5.4 | — | ring 7 (columns 2 and 16) |
| 15.6 | b5.4+ | two-note 16th pickup | ring 8 — column 1: the flood reaches the copy's edge; field complete |
| 16.0 | b6.1 | pickup resolves on the downbeat | 「它开始看见。」 |
| 19.2 | b7.1 | 16th pluck roll 19.2–20.0; cutoff 600 Hz | field → 60 px (origin cell joins the field); numeral 0; ceiling → 360 |
| 19.4 / 19.6 / 19.8 | 16ths | roll | 1,000 / 10,000 / 100,000 |
| 20.0 | b7.2 | roll stops | numeral snaps to 1,000,000; headline |
| 22.4 | b8.1 | kick (1 & 3) + 16th hats; cutoff 900 Hz | field → 30 px; agent line starts; ceiling → 240 |
| 24.0 | b8.3 | pluck doubles | line forks into four lanes (x ≈ 587) |
| 25.6 | b9.1 | — | 「一件事，做到完成。」 |
| 27.2 | b9.3 | pluck back to two notes | lanes merge (x ≈ 1440) |
| 28.4 | b9.4+ | — | line reaches x 1760 and holds |
| 28.8 | b10.1 | pluck A3; cutoff 1.4 kHz | field → 15 px (8 colours); the snap cuts the line; ceiling begins its two-beat exit; type turns to ink |
| 29.2 / 29.6 / 30.0 | b10.1+ / 2 / 2+ | C4 / E4 / A4 | mosaic-text 30 / 15 / 5 px (ceiling passes y 120 at 29.6) |
| 30.4 | b10.3 | C5 | mosaic-text 1 px — legible; eyebrow; ceiling off the top |
| 30.8 | b10.3+ | E5 | English rises |
| 31.2 | b10.4 | A5; cutoff 2.2 kHz | field → 5 px |
| 31.6 | b10.4+ | C6 — last note before the lift | — |
| 32.0 | b11.1 | Fmaj7; kick rests; shimmer in; cutoff 4 kHz | face at 1 px, real; nothing else on screen |
| 32.8 | b11.2 | — | 「原来，是一张脸。」 (ink) |
| 35.2 | b12.1 | kick returns four-on-the-floor | — |
| 38.4 | b13.1 | Dm9; step tick; cutoff 400 Hz | face → 120-px blocks; type back to paper |
| 38.8 | b13.1+ | step tick | blocks swap to photo 38; 「不止一个人。」 rises |
| 39.2 | b13.2 | step tick; cutoff 600 Hz | 60 px |
| 39.6 | b13.2+ | — | 'Not one. Many.' |
| 40.0 | b13.3 | step tick; cutoff 900 Hz | 30 px |
| 40.8 | b13.4 | step tick; cutoff 4 kHz | 1 px, real; copy gone (exit → 40.8) |
| 41.6 | b14.1 | G(add9); riser begins; kick every beat | real → 120-px blocks |
| 42.0 | b14.1+ | hat accent | blocks swap to photo 51 |
| 42.4 → 44.4 | 8ths | hat accents; cutoff per step | 60 / 30 / 30@8col / 15 / 5 / 5@full |
| 44.8 | b15.1 | kick on the downbeat; cutoff 4 kHz | city at 1 px, real — 「再远一些，是一座城。」 |
| 46.4 | b15.3 | VACUUM: riser + reversed swell + pad at −12 dB closing | reverse 5 / 15 / 60 / 120 px on 46.4 / 46.8 / 47.2 / 47.6 |
| 48.0 | b16.1 | IMPACT + full Am(add9) stack | blocks swap to Earth; generation 0 held one 8th |
| 48.4 → 50.8 | 16ths | 13 ticks; cutoff sweeping 400 → 2.2 kHz | quadtree generations 1–13 |
| 51.0 | last 16th of bar 16 | — (no tick) | generation-13 state holds |
| 51.2 | b17.1 | Fmaj7; cutoff 4 kHz | generation 14: Earth fully real — 「再高一些，世界清晰了。」; boundary starts drawing |
| 54.4 | b18.1 | G | boundary closes — 「能力越大，边界越清。」 |
| 57.6 | b19.1 | Cmaj9, half-time, hats off | hard cut to photo 32 |
| 60.8 | b20.1 | Fmaj9 pad only; shimmer begins | 「然后，抬头。」 |
| 64.0 | b21.1 | pad adds E5 | 「每个上限，都是起点。」 |
| 70.4 | b23.1 | unison A2 with harmonics 1–8 | hard cut to ink; 'Claude Fable 5.1' rises |
| 74.4 | b24.2 | 1.6-s release begins | lockup fades (9 frames) |
| 75.2 | b24.3 | final tick | ember pixel returns at the origin cell |
| 76.0 | b24.4 | silence | ink |
| 76.8 | end | — | end |

### 2.4 Energy curve per bar (0–1)
bar 1 0.05 · 2 0.08 · 3 0.12 · 4 0.16 · 5 0.26 · 6 0.30 · 7 0.36 · 8 0.46 · 9 0.50 · 10 0.58 · 11 0.50 · 12 0.60 · 13 0.64 · 14 0.74 · 15 0.82 (0.30 in its last two beats) · 16 1.00 · 17 0.92 · 18 0.84 · 19 0.70 · 20 0.36 · 21 0.34 · 22 0.30 · 23 0.20 · 24 0.08
Shape: hold → pulses → fill → first landing (inhale) → turn → rise → vacuum → climax → resolution → breath → coda. Three dips are deliberate: bar 11 (kick rests on the face), the vacuum (46.4–48.0), and bar 20 (everything but the pad leaves under the sky).

## 3. Scenes — 0 → 76.8, no gaps, every boundary on a bar line
Conventions: times in seconds (bar.beat in brackets); "exit → T" = 4-frame opacity fade ending on T (§1.3); "snap" = one frame. Field = the full-frame block-sample of the current photograph on the film grid. Copy block = eyebrow (y 800) + headline (880) + English (932), left at x 160, under the ceiling rule while it exists. Headline lengths are given in glyphs (advance 77.76 px from x 160).

### S01 一个像素 · One Pixel — 0.0–6.4 (bars 1–2)
- Visual: ink, nothing. 0.8 (b1.2): a single 120×120 ember square snaps in at the ORIGIN CELL (x 960–1080, y 360–480) — one frame, no fade. It does not move, pulse or glow. 3.2 (b2.1): headline rises lower-left; 4.0: English; exit → 6.4. The square is the only coloured thing for 6.4 s; the tone is the only sound. Two elements: pixel, copy. Static camera.
- copy_zh: 一个像素。 · copy_en: One pixel.
- Mosaic: block 120, the origin cell of photo 54 quantized by §1.2 → ember (the quantizer's own output for that cell; gate (a) proves it on the fetch). No resolve yet.
- Photos: 54. Snaps to: b1.2 (pixel), b2.1 (headline), b2.2 (English).
- Transition: continuous — the square splits on the 6.4 downbeat.

### S02 先想 · Think First — 6.4–12.8 (bars 3–4)
- Visual: 6.4 (b3.1): the square splits in one snap into a 2×2 of 60-px cells — the four quadrants of the origin cell, 4 tokens at two brightness levels (§1.2), so the cells differ (measured on the thumb: ember-high, ember-low, ember-high, ink-high — temple, eye socket, cheek, brow: three distinct appearances): it has variance now, it is not one thing. Around it a 1-px paper arc (55 %), radius 200 px centred on (1020, 420), draws clockwise from 7 o'clock (920, 593) over the top to 5 o'clock (1120, 593) — 300°, open at the bottom, lowest points y 593, above the ceiling — at constant speed from 6.4, arriving at 12.0 (b4.4; 300° in 5.6 s = 53.6°/s). 'LOW' sits beside the 7-o'clock end from 6.4; 'MAX' snaps in beside the 5-o'clock end at 12.0 as the arc arrives and holds — the payoff is on screen for 20 clean frames before the dial (arc and both labels) fades 12.6667–12.8, so the flood begins on a frame with no dial. A dial being set, never a spinner. 6.4: ceiling rule draws left→right (one beat) at y 600, label 「上限」 at 7.2.
- Copy (two-line block): 「它是什么？」 line 1 (baseline 786) at 6.4; eyebrow 'ADAPTIVE THINKING · EFFORT DIAL' (baseline 706) at 8.0; 「先想，再答。」 line 2 (baseline 880) at 9.6; English 'What is it? Think first. Then answer.' (932) at 10.4; all exit → 12.8. Three elements: 2×2, dial, copy block (+ rule).
- copy_zh: 它是什么？／先想，再答。 · copy_en: What is it? Think first. Then answer.
- Mosaic: 120 → 2×2 at 60 px, origin cell only, snap on b3.1; 4 tokens at two levels.
- Photos: 54. Snaps to: b3.1 (split, line 1, rule), b3.3 (eyebrow), b4.1 (line 2), b4.2 (English), b4.4 ('MAX').
- Transition: dial fades over the four frames before 12.8; the flood begins exactly on the downbeat.

### S03 它开始看见 · It Begins to See — 12.8–19.2 (bars 5–6)
- Visual: the 120-px field floods outward from the origin cell (column 9, row 4) by Chebyshev rings d = 1…8, one per 8th: 12.8, 13.2, 13.6, 14.0, 14.4, 14.8, 15.2, 15.6 — complete on the last 8th of bar 5. Geometry: the rings reach the top edge at d = 3, the bottom at d = 5, the right edge at d = 7 and the left edge at d = 8, so rings 1–3 are full squares (8, 16, 24 cells), ring 4 lacks its top row (23), ring 5 reaches the bottom row (27), and the last three rings are column sweeps toward the copy: columns 3 & 15 (18 cells), columns 2 & 16 (18), column 1 alone (9) — the picture reaching the copy's edge on 15.6, one 8th before the headline. Each block = mean of photo 54 under the cell → 4 tokens, 55 %; the origin 2×2 keeps its 60-px cells through S03 (the centre stays one step ahead). Result: a flat colour chart, unreadable as a face: an ember column, ink hair, the lake's lit band as pinned paper (#868380) and slate — that is where the copy lives, at ≥ 3.2:1. 12.8–13.6: ceiling → 480.
- Copy: eyebrow 'VISION · DOCUMENTS · CHARTS' and 「它开始看见。」 (6 glyphs) at 16.0; 'It begins to see.' 16.8; exit → 19.2. Two elements: field, copy.
- copy_zh: 它开始看见。 · copy_en: It begins to see.
- Mosaic: ring-flood, 120 px, 4 tokens, 55 %; one ring per pluck on 8ths; a two-note 16th pickup under the last ring (15.6–16.0); stage 1 of the face sequence.
- Photos: 54. Snaps to: 8ths b5.1 → b5.4+; headline b6.1.
- Transition: continuous; the whole field steps 120 → 60 on 19.2.

### S04 记住全部 · All of It — 19.2–22.4 (bar 7)
- Visual: 19.2 (b7.1): field → 60 px (4 tokens at two levels, 65 %, paper pinned) in one snap — a vague warm shape against slate. The origin cell's lead ends here: it joins the field at 60 px (a lead would now mean colour in one cell, which §1.2 forbids). Upper-left, under the ceiling (now at 360): the numeral rolls 0 / 1,000 / 10,000 / 100,000 on 19.2 / 19.4 / 19.6 / 19.8 and snaps to 1,000,000 on 20.0 (digits snap, no bounce) together with the headline, holds. 19.2–20.0: ceiling → 360. Eyebrow '1M CONTEXT · 128K OUTPUT' and headline (12 glyphs) at 20.0 (b7.2); English 20.8; numeral and copy exit → 22.4. Three elements: field, numeral, copy. (Reading time 2.27 s — the only figures in the film, both from the brief.)
- copy_zh: 记住全部，而不只是片段。 · copy_en: All of it, not just the fragment.
- Mosaic: step 2 of the face sequence, 120 → 60 px, single snap on b7.1.
- Photos: 54. Snaps to: b7.1 (field, roll start), 16ths to b7.2 (lock, headline), b7.3 (English).
- Transition: field steps 60 → 30 on 22.4 as the kick enters.

### S05 做到完成 · Seen Through — 22.4–28.8 (bars 8–9)
- Visual: 22.4 (b8.1): field → 30 px (4 tokens, 75 %, paper pinned) — a person becomes legible, though not who. A 1-px paper line (70 %) starts at (160, 712) and draws rightward at a constant 266.67 px/s (1600 px in 6.0 s); at 24.0 (b8.3, x ≈ 587) it forks into four parallel lanes 24 px apart (y 676 / 700 / 724 / 748) — sub-agents — running side by side; at 27.2 (b9.3, x ≈ 1440) they merge back into one; the single line arrives at x 1760 at 28.4 (b9.4+) and holds, finished, for one 8th; the 28.8 snap cuts it (no fade). One task, branched, rejoined, finished. 22.4–23.2: ceiling → 240.
- Copy: eyebrow 'SUB-AGENTS · MANAGED AGENTS · TOOL USE · COMPUTER USE' at 23.2; headline (9 glyphs) at 25.6 (b9.1); English 26.4; copy exit → 28.8. Three elements: field, line, copy.
- copy_zh: 一件事，做到完成。 · copy_en: One task, seen through.
- Mosaic: step 3 of the face sequence, 60 → 30 px, single snap on b8.1.
- Photos: 54. Snaps to: b8.1 (field, line start, kick), b8.3 (fork, pluck doubles), b9.1 (headline), b9.3 (merge), b9.4+ (line arrives), b10.1 (line cut).
- Transition: field steps 30 → 15 on 28.8; mosaic-text begins.

### S06 读遍代码 · The Whole Codebase — 28.8–32.0 (bar 10)
- Visual: 28.8 (b10.1): field → 15 px (8 colours, 85 %) — colour arrives, and with it two things leave the paper world: type turns to ink (§1.2) and the ceiling rule begins its two-beat exit from 240, passing y 120 at 29.6 and leaving the top of the frame on 30.4. The headline is rendered THROUGH the mosaic at the normal headline position, in ink: 29.2 → 30-px blocks (illegible bars, 0.4 s), 29.6 → 15 px, 30.0 → 5 px, 30.4 → 1 px: legible exactly on beat 3, on the C5 pluck, the frame the ceiling is gone. Eyebrow 'CLAUDE CODE · CODE EXECUTION · WHOLE CODEBASES' (ink 50 %) at 30.4; English (ink 72 %) at 30.8; 31.2 (b10.4): field → 5 px (32 colours, 92 %) — the face nearly there, soft, still withheld; exit → 32.0. Two elements: field, copy. The film's first quick passage: six snaps in 2.4 s. The headline is 8 glyphs (ends x 782) so it stays on the lake, left of the neck's shadow (x ≥ 795), where ink holds ≥ 5:1; the English has no descenders, so the shirt's top edge (y ≈ 940 at x ≥ 510) stays clear of it.
- copy_zh: 读遍代码，再写。 · copy_en: It reads the whole codebase before it writes.
- Mosaic: field 30 → 15 (28.8) and 15 → 5 (31.2); mosaic-text 30 / 15 / 5 / 1 px on 29.2 / 29.6 / 30.0 / 30.4, each on an ascending pluck (C4 E4 A4 C5).
- Photos: 54. Snaps to: b10.1, b10.1+, b10.2, b10.2+, b10.3, b10.4.
- Transition: snap 5 → 1 px on 32.0 — the reveal.

### S07 原来是一张脸 · A Face — 32.0–38.4 (bars 11–12)
- Visual: 32.0 (b11.1): one snap to 1 px — photo 54 in full colour at 100 %: a young woman, calm, auburn hair, looking just past the lens, a pale lake and soft hills behind her, her eye on the origin cell where the pixel began. Nothing else is on screen: the ceiling left on 30.4 and no hairline is drawn here. Push-in 1.00 → 1.03 over 6.4 s (photograph only). One beat alone; headline (8 glyphs, ink) at 32.8, English (ink 72 %) 33.6; exit → 38.4. Two elements: photograph, copy. The first landing — the answer to the opening question, written in ink on the bright world.
- copy_zh: 原来，是一张脸。 · copy_en: So it was a face.
- Mosaic: final step of the face sequence, 5 → 1 px, full colour; the sequence has taken 19.2 s and six steps (120 / 60 / 30 / 15 / 5 / 1).
- Photos: 54. Snaps to: b11.1 (reveal, Fmaj7), b11.2 (headline), b11.3 (English), b12.1 (kick returns).
- Transition: real → 120-px blocks on 38.4 (the zoom-out begins; type returns to paper).

### S08 不止一个人 · Not One, Many — 38.4–41.6 (bar 13)
- Visual: 38.4 (b13.1): the real face collapses to 120-px blocks in one snap (4 tokens of photo 54, 70 %); type is paper again. 38.8 (b13.1+): the block colours swap to photo 38 (four friends, arms linked, facing a sunset, silhouettes) quantized to 4 tokens — paper sky, ember sun and lit hillside, ink figures and an ink ground row; the grid is the zoom-out, nothing else changes — and the headline rises on the same frame: the subject changes and the words name it. Resolve on BEATS: 39.2 (b13.2) → 60 px (4 tokens, 80 %), 40.0 (b13.3) → 30 px (4 tokens, 90 %), 40.8 (b13.4) → 1 px, real (100 %): people, together, looking out. The copy exits → 40.8, so the real photograph is held clean 40.8–41.6: the words leave as the people arrive (the sunlit ground under the copy block is too bright for paper type at 1 px; on the pinned flat stages it is slate and ink). English at 39.6 (b13.2+). Two elements. No camera.
- copy_zh: 不止一个人。 · copy_en: Not one. Many.
- Mosaic: real → 120 (snap) → colour swap → 60 / 30 / 1 on beats. Step time 0.8 s: 8× faster than the face, 2× slower than the city. Flat → real in one snap (30 px → 1 px): the boldest single step in the film. Scale: people.
- Photos: 54 → 38. Snaps to: b13.1, b13.1+, b13.2, b13.3, b13.4.
- Transition: real → 120-px blocks on 41.6.

### S09 是一座城 · A City — 41.6–48.0 (bars 14–15)
- Visual: 41.6 (b14.1): collapse to 120 px (4 tokens of photo 38, 70 %). 42.0 (b14.1+): swap to photo 51 (Shanghai, Pudong at night, Oriental Pearl Tower) at 4 tokens: a horizontal band of paper and ember lights on slate, reads as lights. Resolve on 8ths, resolution and colour as separate rungs: 42.4 → 60 px (4 tokens) · 42.8 → 30 px (4 tokens) · 43.2 → 30 px at 8 colours (colour arrives) · 43.6 → 15 px (8 colours) · 44.0 → 5 px (32 colours) · 44.4 → 5 px at full colour · 44.8 (b15.1) → 1 px, real, on the downbeat — graded (§1.2) so it sits in the palette and still reads instantly as Pudong; the Pearl Tower's spheres (tower at x ≈ 780–860, left of centre, spire tip ≈ 20 px below the top edge) are readable from 15 px, so the audience knows before the copy says. Brightness 55 → 100 % across the resolve. Hold 44.8–46.4 with headline (10 glyphs) at 44.8 on the river — the waterline is at y ≈ 820, so the copy block sits on the water below the skyline (gate (c): 95 % of its blocks ≥ 3:1 after the grade) — English at 45.6; exit → 46.4. Reverse on 8ths in the music vacuum: 46.4 → 5 px (32 col), 46.8 → 15 px (8 col), 47.2 → 60 px (4 tok), 47.6 → 120 px (4 tok); brightness down to 70 %. Two elements. No camera. The quick-snap passage: 13 snaps in 6.4 s.
- copy_zh: 再远一些，是一座城。 · copy_en: Further out: a city.
- Mosaic: real → 120 → swap → 8th-note resolve (7 rungs, 42.4–44.8) → hold → 8th-note reverse (4 rungs, 46.4–47.6). The fastest uniform resolve (0.4 s per rung) and the only reverse.
- Photos: 38 → 51 (alternate 76, Los Angeles, amber on ink, same window rule: drops in with no timing change). Snaps to: b14.1, b14.1+, every 8th b14.2 → b15.1, b15.3 → b15.4+.
- Transition: IMPACT on 48.0 — the 120-px blocks switch colour to Earth (no cut; the grid persists).

### S10 再高一些 · The World in Focus — 48.0–54.4 (bars 16–17)
- Visual: 48.0 (b16.1) IMPACT: on the same 120-px grid the block colours swap to photo 08 (Earth at night), rotated 180° — an orbital photograph has no canonical up — so the frame reads top to bottom: slate ocean and cloud (rows 1–2), the lit coast as paper and slate cells (rows 3–6, upper-middle), the limb's dark glow (row 7, slate), ink space (rows 8–9) — the copy's home, the darkest ground in the film; 75 % of cells non-ink at 120 px. Generation 0 holds one 8th (48.0–48.4): the hit lands on a legible planet. Quadtree: 13 generations on 16ths at 48.4, 48.6, … 50.8; the generation-13 state holds through 51.0; generation 14 (1 px, full colour) snaps on 51.2 with the Fmaj7, the headline and the first pixel of the boundary — the second landing has a picture change. Depth ladder 120 / 60 / 30 / 15 / 5 / 1 (depths 0–5). Split policy, deterministic quota (§5.6): resolution score S = Σ leaf area × depth/5 ÷ frame area; each generation ranks every leaf below depth 5 by luminance variance × area and splits in rank order (one depth per split) until S reaches that generation's target — 0.03, 0.05, 0.08, 0.12, 0.17, 0.23, 0.30, 0.38, 0.47, 0.57, 0.68, 0.80 for generations 1–12 (generation 1 = ≈ 15 % of root blocks), generation 13 first forces every leaf to depth ≥ 4 (5 px) then continues to 0.90, generation 14 forces depth 5 → S = 1.00, fully real on 51.2 (b17.1). Every tick changes ≥ 2 % of the frame's resolution; lit coastlines and the limb sharpen first, the ocean later, black space only in the forced passes. Colour by depth: 0–2 → 4 tokens (photo 08's frozen thresholds), 3 → 8 colours, 4 → 32, 5 → full. Brightness 55 → 100 % linearly 48.0 → 51.2. The split order is precomputed in Python and the 15 states (generations 0–14) shipped as bitmaps. Push-in 1.00 → 1.04 from 51.2 to 57.6 (photograph only).
- 51.2: headline 「再高一些，世界清晰了。」 (11 glyphs); 52.0: English; exit → 54.4. 51.2–54.4: THE BOUNDARY — a 1-px paper hairline (70 %) draws a rectangle inset 96 px from the frame edge (x 96–1824, y 96–984), clockwise from the top-left corner at constant speed (perimeter 5232 px over 3.2 s = 1635 px/s), closing exactly on 54.4: a boundary drawn deliberately around the world. Three elements: planet, frame, copy.
- copy_zh: 再高一些，世界清晰了。 · copy_en: Higher still: the world, in focus.
- Mosaic: colour swap on the 120-px grid → one-8th hold → 13 detail-first quadtree generations on 16ths → hold one 16th → generation 14 on b17.1. The deepest and fastest resolve: 0.2 s per generation.
- Photos: 51 → 08. Snaps to: b16.1 (impact), every 16th b16.1+ → b16.4+ (48.4 → 50.8), b17.1 (real, headline, frame starts), b17.2 (English).
- Transition: continuous; the Earth carries into S11 inside the closed frame.

### S11 边界 · The Boundary — 54.4–57.6 (bar 18)
- Visual: the Earth continues inside the closed hairline frame; push-in continues. Eyebrow 'SAFEGUARDS · BY DESIGN' and headline (10 glyphs) at 54.4 (b18.1) as the frame closes; English 55.2; exit → 57.6. Three elements: planet, frame, copy. Nothing draws, nothing snaps: the quietest picture before the sky.
- copy_zh: 能力越大，边界越清。 · copy_en: More capable. Clearer boundaries.
- Mosaic: none — the world stays real; the only mark is the finished boundary.
- Photos: 08. Snaps to: b18.1 (copy), b19.1 (cut).
- Transition: hard cut on 57.6 to photo 32, on the Cmaj9 — the chord of resolution becomes the human.

### S12 然后，抬头 · Look Up — 57.6–70.4 (bars 19–22)
- Visual: 57.6 (b19.1): hard cut to photo 32 at 1 px — it arrives already real, with no mosaic at all: a person standing small on dark ground, right of centre (x ≈ 1170–1240, columns 10–11, feet on the horizon at y ≈ 790), the Milky Way entering from the top edge, a warm band at the horizon, the ground filling y 790–1080 — the copy's home. Human scale against cosmic scale. Push-in 1.00 → 1.06 over 12.8 s centred on the figure's feet (1205, 790), so the horizon stays put and the viewer finds the person as the camera does. One bar alone (57.6–60.8) while the groove dissolves. 60.8 (b20.1): 「然后，抬头。」 (6 glyphs) rises (baseline 880) as the pad goes solo; 61.6: 'Then, look up.'; both exit → 64.0. 64.0 (b21.1): 「每个上限，都是起点。」 (10 glyphs, ends x 937, ≥ 230 px clear of the figure); 64.8: 'Every ceiling, the next floor.'; exit → 70.4. One thought at a time. Two elements: photograph, copy. The long breath: nothing snaps for 12.8 s.
- copy_zh: 然后，抬头。／每个上限，都是起点。 · copy_en: Then, look up. / Every ceiling, the next floor.
- Mosaic: none — deliberately. The one photograph that never passes through the grid: nothing is left to resolve.
- Photos: 32. Snaps to: b19.1 (cut), b20.1 / b20.2 (line 1), b21.1 / b21.2 (line 2), b23.1 (cut out).
- Transition: hard cut to ink on 70.4.

### S13 Claude Fable 5.1 · Anthropic — 70.4–76.8 (bars 23–24)
- Visual: 70.4 (b23.1): hard cut to ink. 'Claude Fable 5.1' rises at centre (baseline 528); 71.2: 「我们能力最强的模型」 (592); 72.0: 'Anthropic' (648) — plain type, no mark, no rule. Hold, perfectly still. 74.4 (b24.2): the lockup fades (9 frames, 300 ms). 75.2 (b24.3): the single 120-px ember square returns at the ORIGIN CELL (x 960–1080, y 360–480), where it began, for one beat. 76.0 (b24.4): one-frame cut to ink. 76.8: end. One lockup, then one pixel — the next beginning.
- copy_zh: 我们能力最强的模型 · copy_en: Claude Fable 5.1 / Anthropic
- Mosaic: the pixel returns: one 120-px ember cell at the origin, 75.2–76.0. The film's first and last block are the same cell.
- Photos: none. Snaps to: b23.1, b23.2, b23.3, b24.2, b24.3, b24.4.
- Transition: ink at 76.0; 0.8 s of ink and silence to 76.8.

## 4. Photo list (five photographs; each carries a rung of the ladder)
Prep rule for every photograph: fetch at the chosen width W (1920, or 2880 where horizontal freedom is needed — Unsplash serves both), downscale so the shorter side ≥ 1080 at that width, then crop one 1920×1080 window at the stated offset (L, T); never upscale. A 1920-px 3:2 fetch is 1920×1280 and allows only T ∈ [0, 200]; a 2880-px fetch is 2880×1920 and allows L ∈ [0, 960], T ∈ [0, 840]. The windows below were set on the catalogue thumbs (±4 px at film scale) and are confirmed by the §5 gates on the fetch.
| # | content | role | window and prep |
|---|---|---|---|
| 54 | young woman portrait, soft light, calm; auburn hair, pale lake and hills behind | THE FACE — origin of the film; the thing being resolved for 32 s (S01–S07); 4-token / 8 / 32 / full stages pre-baked at 120 / 60 / 30 / 15 / 5 px | W 1920 (1920×1280), window x 0–1920, y 60–1140 (T = 60): eye line at y ≈ 435–450 (row 4), nose on the column 8|9 boundary, her hair just touching the top edge, the shirt's top edge at y ≈ 940 for x ≥ 510 (below the English baseline). T may move in 10-px steps inside 40–100 only to keep the eye line in y 380–470. The lake under the copy block is bright at every T (measured 1.6–2.4:1 against paper at 1 px) — hence pinned paper on the flat stages and ink type 28.8–38.4; the origin cell quantizes to ember |
| 38 | four friends arm in arm facing a sunset, silhouettes | PEOPLE — the first zoom-out rung (S08); graphic silhouettes read at 30 px; sky quantizes to paper and ember on ink figures | W 1920, window y 200–1280 (T = 200): figures in columns 7–11, heads at row 2, ink ground row 9; the copy block is on screen only over the flat stages (slate and ink under it); no grade. Held alternate: 79 (three friends, arms raised; its copy area passes gate (c) at 1 px if the copy must ever sit on the real photograph) |
| 51 | Shanghai Pudong at night, Oriental Pearl Tower | CITY (S09) — recognition beat for the Chinese audience | W 1920, window y 200–1280 (T = 200): Pearl Tower at x ≈ 780–860 (column 7, left of centre — a 1920 fetch has no horizontal freedom and a 2880 fetch cannot hold the tower's spheres and the river in one window), spire tip ≈ 20 px below the top edge (a clip of ≤ 10 px of the antenna is accepted; T is never lowered below 190), waterline at y ≈ 820, the river filling rows 8–9 under the copy; 1-px stage graded −25 % saturation, blue → slate 10 %. Alternate: 76 (Los Angeles aerial, amber on ink), same window (T = 200, measured 99 % of copy blocks ≥ 3:1), identical timing |
| 08 | Earth at night from space, city lights | PLANET (S10–S11) — the climax; quadtree source | W 1920 (1920×1276), ROTATED 180°, window y 98–1178 (the centre crop): slate ocean rows 1–2, lit band rows 3–6 (upper-middle), limb glow row 7, ink space rows 8–9; the copy block lands on the glow and pure ink (measured ≥ 15:1 under every line); ≥ 25 % non-ink cells is satisfied by construction (percentile quantizer) — gate (d) checks the band's placement instead |
| 32 | person under the Milky Way, warm horizon | LOOK UP (S12) — arrives real, never mosaicked; the breath | W 2880 (2880×1920, required — no 1920 window passes gate (c) or clears the figure), window x 258–2178, y 840–1920: figure at x ≈ 1170–1240 with feet on the horizon at y ≈ 790, the Milky Way band entering from the top edge, the ground (Y ≤ 0.02) under the whole copy block; push-in centred on (1205, 790) |
Not used by design: 09 / 86 (an object rung after the face would reverse the zoom-out); 56 (second face — the people rung does this better); 52 / 53 / 55 / 58 / 59 are portrait-orientation sources and fail gate (c) at every offset; 76 held as the city alternate, 79 as the people alternate.

## 5. Build order, gates, risks
1. HARD GATES — run on the fetched photographs at the §4 windows and printed as token maps / contrast maps before any scene is coded; a failed gate changes the window or the alternate, never the rule: (a) photo 54 at 120 px, percentile tokens — the origin cell (column 9, row 4) must be ember and the eye line must sit in y 380–470; the full 16×9 map is printed and compared with §1.2's description (ember column 9, ink hair columns 7 and 10–11, pinned paper on the lake's lit band); if the eye line is out, re-choose T inside 40–100, never the origin; (b) the S02 2×2 — four 60-px quadrants with the two-level rule must show ≥ 3 distinct appearances (measured on the thumb: ember-high, ember-low, ember-high, ink-high); if the fetch gives fewer than two, hand-set ember 85 % / ember 70 % / paper 55 % / slate 65 % and strike the word "honest" from any deck; (c) legibility, two parts: flat stages — paper type over pinned paper (55 %), slate (55–90 %), ember (55–90 %) and ink cells is ≥ 3.2:1 by construction, verify it survives the H.264 encode on the 55 / 65 / 75 % fields and darken slate to #2E323C if the slate cells wash out; real-colour stages — for every line that sits on a 15-px, 5-px or 1-px stage, ≥ 95 % of the 30-px blocks under the glyph box must be ≥ 3:1 against that line's type colour (ink for 28.8–38.4, paper otherwise), measured on the thumbs: S06 8-glyph headline 100 %, S06 English 100 %, S07 100 %, S09 on 51 95 % (76: 99 %), S10/S11 100 %, S12 100 %; a failure swaps 51 → 76 or re-chooses T within the stated bands — never a scrim, never a luminance grade, never a type-colour change beyond §1.2; (d) photo 08 rotated at 120 px — the paper/slate band must occupy rows 3–6 and rows 8–9 must be all ink (print the map); (e) photo 51 at 120 / 60 / 30 px — the paper and ember cells must form one horizontal band (rows 6–8) so the swap at 42.0 reads as "lights" (measured 29 paper + 2 ember of 144 at 120 px); (f) the 30-px mosaic-text bar for one 8th — intended, check for taste.
2. Opening audibility: the 110 Hz carrier plus the −12 dB A3 and the 2.5 kHz click on every tick are what make bars 1–4 exist on a phone speaker; the 55 Hz sub is support only. Check on a phone before locking the mix.
3. 75 BPM at 30 fps is what makes every subdivision frame-exact (96 / 24 / 12 / 6 f) and every exit 4 frames. If the renderer's frame rate changes, re-derive the grid before moving any boundary.
4. The dial never rotates or loops; it draws once, arrives on b4.4 and stops at MAX. The agent line arrives on b9.4+ and is cut by the b10.1 snap; it never crosses the origin column at face height (it runs at y 676–748, below the face). The boundary frame is the only rectangle in the film.
5. Hairline visibility: the ceiling rule at 1 px / 50 % paper is enough on ink and slate cells and on pinned paper; if the H.264 encode loses it, raise it to 60 %, never to 2 px; it is never drawn over a real-colour stage (it leaves on 30.4, before any bright sky can swallow it). The agent line (70 %) crosses pinned-paper cells in rows 6–7; if the encode loses it there, raise it to 85 %. The label 「上限」 stays attached through every rise and through the exit.
6. Quadtree determinism: per-leaf variance of the source luminance via summed-area tables; the resolution score S and its target table (§S10) drive a deterministic quota per generation (rank by variance × area, split in rank order, one depth per split, children re-ranked next generation; generation 13 forces depth ≥ 4 first, generation 14 forces depth 5); the ordered split list and the 15 generation bitmaps are stored; the renderer draws one image per frame. No tuned threshold: the targets guarantee a visible change on every tick and the ranking guarantees coast-first, ocean-later, space-last.
7. Figures in the film: exactly two — 1,000,000 and 128K — both from the brief, both monochrome. Names: "Claude Fable 5.1", "Anthropic", and, in one eyebrow, "CLAUDE CODE" — the one product name beyond the brief's allowed-name list; it appears in the brief's capability facts, so it stays. No logo; the wordmark is plain Inter.
8. Palette discipline: the only out-of-token colour before 15 px is none; pinned paper (#868380) is paper at 55 %, not a fifth token; the only saturated frame is the city at 1 px for 1.6 s, graded; the only ink type is the face's real-colour stages. If the client prefers purity, 76 replaces 51 with no timing change.
9. The coda pixel (75.2–76.0) is a structural bookend; if it feels precious, cut it and let the lockup fade to ink at 76.0 with no change to the music.
10. Short cut (64.0 s = 20 bars, if needed): drop bar 13 (S08), bars 21–22 (the second breath line moves to 60.8) and bar 24 (coda becomes one bar, pixel at 72.0); re-time the music sections to match; the bar grid holds.
