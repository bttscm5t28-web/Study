"""
demo.py -- 12-second test render for synth.py.

Am9 -> Fmaj7 -> Cmaj7 -> Gsus2 at 90 BPM (one chord per bar) on the pad,
sub notes underneath, a sparse pluck melody with a dotted-eighth ping-pong
delay, soft off-beat hats, subtle ticks, a riser into a cinematic impact on
bar 3, a shimmer pad for the ending; mastered with bus reverb -> compressor
-> loudness normalisation (-14 LUFS) -> look-ahead limiter.

Writes build/synth_demo.wav (24-bit PCM) and build/synth_demo_spec.png
(log-frequency spectrogram, rendered with Pillow), then prints an analysis.
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import synth as S  # noqa: E402
from synth import (Track, bpm_grid, chord, pad, sub, pluck, hat, tick, riser, impact,  # noqa: E402
                   shimmer, delay, reverb, highpass, compress, normalize_lufs, limiter,
                   fade, n_samples, analyze, to_mono)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
OUT_WAV = os.path.join(BUILD, "synth_demo.wav")
OUT_PNG = os.path.join(BUILD, "synth_demo_spec.png")

SR = S.SR
BPM = 90.0
DURATION = 12.0
GRID = bpm_grid(BPM)
BEAT, BAR = GRID.beat_s, GRID.bar_s


def compose():
    """Return (wet_bus, dry_bus): the wet bus goes through the master reverb."""
    wet = Track(DURATION, SR)
    dry = Track(DURATION, SR)

    # --- harmony: pad + sub, one chord per bar ------------------------------
    progression = [("Am9", "A1"), ("Fmaj7", "F1"), ("Cmaj7", "C2"), ("Gsus2", "G1")]
    for i, (name, root) in enumerate(progression):
        notes = chord(name, 3)
        p = pad(notes, BAR, SR, brightness=0.42 + 0.08 * i, attack=1.6, release=2.8, seed=i)
        wet.add(p, GRID.at_bar(i), gain=0.6)
        s = sub(root, BAR - 0.08, SR, release=0.4)
        dry.add(s, GRID.at_bar(i), gain=0.55)

    # --- sparse pluck melody through a dotted-eighth ping-pong delay --------
    melody = [(0, 0.0, "E5"), (0, 2.5, "B4"), (1, 1.0, "C5"), (1, 3.0, "A4"),
              (2, 0.5, "G5"), (2, 2.0, "E5"), (3, 0.0, "D5"), (3, 1.5, "B4"), (3, 3.0, "A4")]
    plucks = Track(DURATION, SR)
    for k, (bar, beat, note) in enumerate(melody):
        plucks.add(pluck(note, 2.2, tone=0.45, sr=SR, seed=k), GRID.at_bar(bar, beat),
                   gain=0.5, pan=0.18 * (-1) ** k)
    wet.add(delay(plucks.mix(), 0.75 * BEAT, feedback=0.32, mix=0.22, ping_pong=True,
                  tail_s=0, sr=SR), 0.0)

    # --- rhythm: hats on the off-beats, subtle ticks in bars 3-4 ------------
    for b in range(int(DURATION / BEAT)):
        wet.add(hat(0.07, sr=SR, seed=b), GRID.at_beat(b + 0.5), gain=0.11, pan=0.25)
    for e in range(16, 32):
        wet.add(tick(sr=SR, seed=e), GRID.at_beat(e / 2.0), gain=0.05, pan=-0.2)

    # --- riser ending exactly on the impact at bar 3 (index 2) --------------
    hit_t = GRID.at_bar(2)
    r = riser(1.5 * BAR, 200.0, 4000.0, SR, seed=7)
    riser_start = (n_samples(hit_t, SR) - len(r)) / SR  # sample-exact end on the hit
    wet.add(r, riser_start, gain=0.42)
    imp = impact(3.5, SR, seed=3)
    dry.add(imp, hit_t, gain=0.85)
    wet.add(imp, hit_t, gain=0.25)  # a little into the bus reverb for glue

    # --- shimmer for the ending ----------------------------------------------
    wet.add(shimmer(1.2 * BAR, sr=SR, release=2.5), GRID.at_bar(3), gain=0.35)
    return wet, dry


def master(wet, dry):
    rv = reverb(wet.mix(), decay_s=3.4, mix=0.2, predelay_ms=25.0, damping=0.45, tail_s=0, sr=SR)
    mix = rv + dry.mix()
    mix = highpass(mix, 24.0, 0.7071, SR)
    mix = compress(mix, threshold_db=-20.0, ratio=2.5, attack_ms=15.0, release_ms=200.0,
                   knee_db=8.0, sr=SR)
    mix, lufs_before = normalize_lufs(mix, -14.0, SR)
    mix = limiter(mix, ceiling_db=-1.0, sr=SR)
    mix = fade(mix, 0.0, 600.0, SR)  # clean end of the 12 s cut
    return mix, lufs_before


# ----------------------------------------------------------------------------
# Spectrogram (Pillow)
# ----------------------------------------------------------------------------
_RAMP = [(8, 9, 20), (18, 34, 78), (30, 76, 138), (56, 130, 190), (122, 190, 226), (228, 246, 251)]


def _colormap(v):
    """Sequential single-hue ramp (dark -> light), v in 0..1 -> uint8 RGB."""
    v = np.clip(v, 0.0, 1.0) * (len(_RAMP) - 1)
    i = np.minimum(v.astype(int), len(_RAMP) - 2)
    f = (v - i)[..., None]
    ramp = np.array(_RAMP, dtype=np.float64)
    return (ramp[i] * (1 - f) + ramp[i + 1] * f).astype(np.uint8)


def spectrogram_png(x, path, sr, bar_s, n_fft=4096, width=1500, height=600, f_lo=30.0,
                    f_hi=20000.0, db_range=90.0):
    from PIL import Image, ImageDraw, ImageFont

    mono = to_mono(x)
    n = len(mono)
    hop = max(1, (n - n_fft) // (width - 1))
    pos = np.arange(width) * hop
    padded = np.concatenate([mono, np.zeros(n_fft)])
    frames = np.lib.stride_tricks.as_strided(padded, shape=(width, n_fft),
                                             strides=(padded.strides[0] * hop, padded.strides[0]))
    spec = np.abs(np.fft.rfft(frames * np.hanning(n_fft), axis=1))
    mag_db = 20.0 * np.log10(spec + 1e-9)
    mag_db -= mag_db.max()
    bins = np.fft.rfftfreq(n_fft, 1.0 / sr)
    rows = np.geomspace(f_lo, f_hi, height)
    img = np.empty((height, width))
    for j in range(width):
        img[::-1, j] = np.interp(rows, bins, mag_db[j])
    rgb = _colormap((img + db_range) / db_range)

    left, bottom, top = 64, 40, 12
    canvas = Image.new("RGB", (width + left + 12, height + top + bottom), (250, 250, 252))
    canvas.paste(Image.fromarray(rgb), (left, top))
    d = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.load_default(size=13)
    except TypeError:
        font = ImageFont.load_default()
    ink = (60, 60, 70)
    for f in (50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000):
        y = top + height - 1 - int(round((np.log(f / f_lo) / np.log(f_hi / f_lo)) * (height - 1)))
        label = f"{f // 1000}k" if f >= 1000 else str(f)
        d.line([(left - 4, y), (left, y)], fill=ink)
        d.text((left - 10 - 7 * len(label), y - 7), label, fill=ink, font=font)
    dur = n / sr
    for s in range(int(dur) + 1):
        xx = left + int(round((s * sr / hop)))
        if xx > left + width:
            break
        d.line([(xx, top + height), (xx, top + height + 4)], fill=ink)
        d.text((xx - 4, top + height + 6), f"{s}s", fill=ink, font=font)
    if bar_s:
        b = 0
        while b * bar_s < dur:
            xx = left + int(round(b * bar_s * sr / hop))
            d.line([(xx, top), (xx, top + height)], fill=(255, 255, 255, 60), width=1)
            d.text((xx + 3, top + 2), f"bar {b + 1}", fill=(235, 240, 245), font=font)
            b += 1
    d.text((left, top + height + 22), f"spectrogram | {sr} Hz | log frequency {int(f_lo)} Hz - {int(f_hi / 1000)} kHz | {int(db_range)} dB range",
           fill=ink, font=font)
    canvas.save(path)
    return path


# ----------------------------------------------------------------------------
def main():
    os.makedirs(BUILD, exist_ok=True)
    t0 = time.time()
    wet, dry = compose()
    t1 = time.time()
    mix, lufs_before = master(wet, dry)
    t2 = time.time()
    S.write_wav(OUT_WAV, mix, SR, bits=24)

    info = analyze(mix, SR, BAR)
    print(f"render: compose {t1 - t0:.1f} s, master {t2 - t1:.1f} s -> {OUT_WAV}")
    print(f"duration        : {info['duration_s']:.3f} s ({info['samples']} samples, {info['channels']} ch)")
    print(f"peak            : {info['peak_dbfs']:.2f} dBFS")
    print(f"loudness        : {info['lufs']:.2f} LUFS integrated (pre-normalisation {lufs_before:.2f} LUFS)")
    print(f"rms overall     : {info['rms_dbfs']:.2f} dBFS")
    for i, r in enumerate(info["rms_per_bar_dbfs"]):
        tag = f"bar {i + 1}" if (i + 1) * BAR <= DURATION + 1e-9 else "tail"
        print(f"rms {tag:9s}   : {r:.2f} dBFS")
    print(f"nan/inf samples : {info['nan_count']}")
    print(f"clipped samples : {info['clipped_samples']} (|x| >= 1.0)")
    ok = info["nan_count"] == 0 and info["clipped_samples"] == 0 and info["peak_dbfs"] <= -0.99
    print("checks          :", "OK (no NaN, no clipping, under -1 dBFS ceiling)" if ok else "PROBLEM")

    spectrogram_png(mix, OUT_PNG, SR, BAR)
    print(f"spectrogram     : {OUT_PNG}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
