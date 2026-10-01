"""
compose.py -- the complete score for 《从一个像素开始》 From One Pixel.

Implements docs/storyboard.md §1.4 (h) and §2 literally with the toolkit in
synth.py.  Grid: 75 BPM, bar 3.2 s, beat 0.8 s, 8th 0.4 s, 16th 0.2 s;
bar n starts at (n-1) * 3.2 s.  Output: music/track.wav, 48 kHz stereo
24-bit, exactly 76.8 s = 3,686,400 samples, digital silence 76.0-76.8.

Layout
  1. SCHEDULE  -- every time, note and level (edit here to retime)
  2. RENDER    -- instrument builders, buses, plate, master
  3. VERIFY    -- the numeric checks demanded by the brief
"""
import os
import sys
import time

import numpy as np
from scipy.signal import fftconvolve, resample_poly

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import synth as S  # noqa: E402
from synth import (Track, sine, saw, noise, adsr, fade, n_samples, lowpass, highpass,  # noqa: E402
                   bandpass, onepole_lp, delay, kick as synth_kick, pluck as synth_pluck,
                   limiter, normalize_lufs, measure_lufs, hz, db2lin, rms_dbfs, to_mono)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_WAV = os.path.join(ROOT, "music", "track.wav")
OUT_PNG = os.path.join(ROOT, "build", "track_spec.png")

# =============================================================================
# 1. SCHEDULE
# =============================================================================
SR = S.SR
BPM = 75.0
BAR, BEAT, E8, E16 = 3.2, 0.8, 0.4, 0.2
TOTAL_S = 76.8
N_TOTAL = 3_686_400
SILENCE_FROM = 76.0            # true digital silence from here to the end
HIT_T = 48.0                   # IMPACT
VACUUM = (46.4, 48.0)


def bar_t(n: int, beat: float = 0.0) -> float:
    """Start of bar n (1-based) plus ``beat`` beats (0-based)."""
    return (n - 1) * BAR + beat * BEAT


def grid(t0: float, t1: float, step: float):
    """Times t0, t0+step, ... < t1 (exact multiples, no float drift)."""
    k = int(round((t1 - t0) / step))
    return [round(t0 + i * step, 6) for i in range(k)]


# --- pad chords: (start, end, notes, attack_s, release_s, gain_db) -----------
PAD_CHORDS = [
    (12.8, 32.0, ["A2", "E3", "A3", "C4", "B4"], 3.0, 0.6, 0.0),          # Am(add9) opens
    (32.0, 38.4, ["F2", "C3", "A3", "C4", "E4"], 0.4, 0.6, 0.0),          # Fmaj7 lift
    (38.4, 41.6, ["D3", "F3", "A3", "C4", "E4"], 0.3, 0.5, 0.0),          # Dm9 turn
    (41.6, 48.0, ["G2", "D3", "B3", "D4", "A4"], 0.3, 0.3, 0.0),          # G(add9) rise (held -12 dB in vacuum)
    (48.0, 51.2, ["A2", "E3", "A3", "C4", "E4", "B4"], 0.08, 0.5, -3.5),  # IMPACT: full Am(add9) stack (-3.5 dB: air for the ticks)
    (51.2, 54.4, ["F2", "C3", "A3", "C4", "E4"], 0.3, 0.5, 0.0),          # Fmaj7
    (54.4, 57.6, ["G2", "D3", "G3", "B3", "D4"], 0.3, 0.5, 0.0),          # G
    (57.6, 60.8, ["C3", "E3", "G3", "B3", "D4"], 0.3, 0.6, 0.0),          # Cmaj9 half-time
    (60.8, 70.4, ["F2", "C3", "E3", "A3", "G4"], 0.6, 0.5, 0.0),          # Fmaj9 breath (pad only)
    (64.0, 70.4, ["E5"], 1.0, 0.5, -4.0),                                 # pad adds E5
]
PAD_DETUNE_CENTS = (-7.0, 0.0, 7.0)
PAD_PANS = (-0.6, 0.0, 0.6)

# --- pad filter = resolution (§1.4 h): (time, cutoff Hz), 100 ms glides ------
CUTOFF_STEPS = [
    (0.0, 400), (12.8, 400), (19.2, 600), (22.4, 900), (25.6, 1400), (28.8, 2200), (31.2, 3000),
    (32.0, 4000), (38.4, 400), (39.2, 600), (40.0, 900), (40.8, 4000),
    (41.6, 400), (42.4, 600), (42.8, 900), (43.2, 900), (43.6, 1400), (44.0, 2200),
    (44.4, 2200), (44.8, 4000), (46.4, 1400), (46.8, 900), (47.2, 600), (47.6, 400),
]
CUTOFF_SWEEP = (48.0, 51.2, 400, 4000)   # log-linear across the quadtree, then 4 kHz to the end
CUTOFF_GLIDE_S = 0.1

# --- pedal / sub: (root note in octave 2, start, end); A pedal 0-32 is the pixel tone
SUB_NOTES = [                   # (root, start, end[, attack_s])
    ("F2", 32.0, 38.4), ("D2", 38.4, 41.6), ("G2", 41.6, 46.4),
    ("A2", 48.0, 51.2, 0.5),    # the impact's own sub drop owns the first half second
    ("F2", 51.2, 54.4), ("G2", 54.4, 57.6), ("C2", 57.6, 60.8),
]

# --- ticks (110 Hz burst + 2.5 kHz click): (time, gain_db) -------------------
TICKS = [(0.8, -12.0)]
TICKS += [(t, -18.0) for t in grid(3.2, 6.4, BEAT)]          # bar 2, soft quarters
TICKS += [(t, -12.0) for t in grid(6.4, 12.8, BEAT)]         # bars 3-4 (incl. 12.0)
TICKS += [(75.2, -8.0)]                                      # final tick
# 13 quadtree ticks 48.4..50.8 (none at 51.0): (time, burst_amp, click_amp, click_hz) in pre-master amplitude.
# The click ramps +9.7 dB (0.30 -> 0.92) and rises log-linearly 2.5 -> 5 kHz (resolution rising); the 110 Hz
# burst stays quiet so the ticks never drive the limiter (which would pull the pad down with them).
QT_TICKS = [(t, 0.30, 0.30 * 10 ** (9.7 / 20 * i / 12), 2500.0 * 2.0 ** (i / 12))
            for i, t in enumerate(grid(48.4, 51.0, E16))]
QT_CLICK_TAU = 0.004                                         # click decay inside its 8 ms
STEP_TICKS = [24.0, 25.6, 27.2,                              # agent line fork / face 30->15 px / merge
              38.4, 38.8, 39.2, 40.0, 40.8, 41.6, 42.0]      # -16 dB band-passed noise
STEP_ACCENTS = {38.4: 6.0, 41.6: 6.0,                         # the two collapses (+6 dB, under the bright pad)
                27.2: 2.0}                                    # the merge snap shares its instant with kick + pluck + hat

# --- plucks: (time, note) ----------------------------------------------------
def _ostinato(t0, t1, notes):
    ts = grid(t0, t1, E8)
    return [(t, notes[i % len(notes)]) for i, t in enumerate(ts)]

PLUCKS = []
PLUCKS += _ostinato(12.8, 15.6, ["A3", "E4"])                              # ring flood, one per ring
PLUCKS += [(15.6, "E4", 1.0), (15.8, "G4", 2.0), (16.0, "A4", 3.0)]        # 16th pickup -> downbeat
PLUCKS += _ostinato(16.4, 19.2, ["E4", "A3"])
PLUCKS += [(19.2, "A3", 1.0), (19.4, "C4", 2.0), (19.6, "E4", 3.0), (19.8, "A4", 4.0)]  # 16th roll (numeral)
PLUCKS += _ostinato(20.0, 24.0, ["A3", "E4"])
PLUCKS += _ostinato(24.0, 27.2, ["A3", "E4", "A4", "E4"])                  # doubles (four lanes)
PLUCKS += _ostinato(27.2, 28.8, ["A3", "E4"])                              # back to two notes
PLUCKS += [(t, n, 6.0 + 6.0 * i / 7) for i, (t, n) in enumerate(zip(grid(28.8, 32.0, E8),
           ["A3", "C4", "E4", "A4", "C5", "E5", "A5", "C6"]))]                  # fill leads: +6 -> +12 dB, C6 loudest pluck
PLUCKS += _ostinato(32.0, 38.4, ["A3", "E4"])                              # under Fmaj7
PLUCKS += _ostinato(38.4, 41.6, ["D4", "A4"])                              # Dm9: D4-A4
PLUCKS += _ostinato(41.6, 46.4, ["G3", "D4"])                              # G(add9) rise
PLUCKS += _ostinato(51.2, 54.4, ["A3", "E4"])
PLUCKS += _ostinato(54.4, 57.6, ["G3", "D4"])
PLUCKS += [(t, n) for t, n in zip(grid(57.6, 60.8, BEAT), ["E4", "G4", "E4", "G4"])]  # half-time
PLUCK_DELAY = (0.6, 0.30, 0.3)       # dotted-8th time, feedback, mix

# --- kick (55 -> 40 Hz) ------------------------------------------------------
KICKS = [22.4, 24.0, 25.6, 27.2, 28.8, 30.4]                 # bars 8-10, beats 1 & 3
KICKS += grid(35.2, 38.4, BEAT)                              # bar 12 four-on-the-floor (bar 11 rests)
KICKS += grid(38.4, 41.6, BEAT)                              # bar 13
KICKS += grid(41.6, 46.4, BEAT)                              # bars 14-15, every beat, up to the vacuum
KICKS += grid(51.2, 57.6, BEAT)                              # bars 17-18
KICKS += [57.6, 59.2]                                        # bar 19 half-time

# --- hats: 16ths at -18 dB, accents -12 dB -----------------------------------
HAT_ACCENTS = [42.0] + grid(42.4, 44.8, E8)                  # 42.0 and the 8ths 42.4..44.4
HATS = [(t, -18.0) for t in grid(22.4, 46.4, E16)] + [(t, -18.0) for t in grid(51.2, 57.6, E16)]
HATS = [(t, (-12.0 if t in HAT_ACCENTS else g)) for t, g in HATS]

# --- shimmer: sine arpeggio on quarters, 1.6 s delay 50 % --------------------
SHIMMER_NOTES = ["A5", "C6", "E6", "G6"]
SHIMMER = [(t, SHIMMER_NOTES[i % 4], -26.0) for i, t in enumerate(grid(32.0, 38.4, BEAT))]
SHIMMER += [(t, SHIMMER_NOTES[i % 4], -20.0) for i, t in enumerate(grid(60.8, 70.4, BEAT))]
SHIMMER_DELAY = (1.6, 0.5, 0.5)

RISER = (41.6, 48.0, 200.0, 8000.0, "A3", "A5")              # start, end (peak sample), bp sweep, sine glide
AIRS = [                                                     # (time, kind, peak_dBFS in the final file, decay_s)
    (32.0, "swell", -24.0, 0.8),                             # the face: 0.8 s reversed air swell, peak on 32.0
    (44.8, "hit", -22.0, 1.0),                               # the city: air hit, 1.0 s decay
    (51.2, "hit", -18.0, 1.4),                               # the Earth: air hit, 1.4 s decay
]
SWELL = (46.4, 48.0)                                         # time-reversed pad-plate swell
CODA = (70.4, 74.4, 1.6)                                     # start, release start, release length

# --- energy curve per bar (§2.4); bar 15 = (first half, vacuum half) ---------
# Mapped to a fader ride of ENERGY_DB_PER_DECADE * log10(E) (14 -> 0.05 = -18 dB, 0.3 = -7 dB, 1 = 0 dB)
ENERGY_DB_PER_DECADE = 14.0
ENERGY = [0.05, 0.08, 0.12, 0.16, 0.26, 0.30, 0.36, 0.46, 0.50, 0.58, 0.50, 0.60, 0.64, 0.74,
          (0.82, 0.30), 1.00, 0.92, 0.84, 0.70, 0.36, 0.34, 0.30, 0.20, 0.08]

# --- levels (linear gain unless _DB) -----------------------------------------
G = dict(
    pixel=0.09, partials=1.0, sub=0.33, pad=0.45, pluck=0.57, kick=1.06, hat=0.55,
    tick=0.55, step=1.4, riser=0.30, swell=0.30, impact=1.0, shimmer=0.9, coda=0.5,
    wet=0.35,                       # plate return level vs dry
    send=dict(pad=1.0, pluck=0.45, hat=0.35, tick=0.05, riser=0.35, impact=0.9,
              shimmer=0.7, coda=0.6, kick=0.0, sub=0.0, air=0.6),
    duck_db=-3.0, duck_release_s=0.2,
    vacuum_pad_db=-12.0, vacuum_wet_keep=0.2, gate_ramp_s=0.005,
    lufs_target=-14.0, ceiling_dbtp=-1.0, ride_limit_db=10.0,
)


# =============================================================================
# 2. RENDER
# =============================================================================
def automation(points, n=N_TOTAL, sr=SR):
    """Piecewise-linear gain curve from [(t, value), ...] (held before/after)."""
    t = np.arange(n) / sr
    pts = sorted(points)
    return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])


def gate_curve(windows, keep=0.0, ramp=G["gate_ramp_s"]):
    """1.0 everywhere except inside [a, b) windows -> ``keep`` (5 ms ramps)."""
    pts = [(0.0, 1.0)]
    for a, b in windows:
        pts += [(a, 1.0), (a + ramp, keep), (b - ramp, keep), (b, 1.0)]
    return automation(pts)


def duck_curve(times, depth_db=G["duck_db"], release_s=G["duck_release_s"], n=N_TOTAL, sr=SR):
    """Sidechain: drops to depth_db at each time, exponential recovery."""
    g = np.ones(n)
    depth = 1.0 - db2lin(depth_db)
    tau = release_s / 3.0
    tail = int(release_s * 2 * sr)
    shape = depth * np.exp(-np.arange(tail) / (tau * sr))
    shape[:n_samples(0.004)] *= np.linspace(0, 1, n_samples(0.004))  # 4 ms into the duck
    for t in times:
        i = n_samples(t)
        seg = min(tail, n - i)
        if seg > 0:
            g[i:i + seg] = np.minimum(g[i:i + seg], 1.0 - shape[:seg])
    return g


def cutoff_curve(n=N_TOTAL, sr=SR):
    """§1.4 (h): step function with 100 ms log glides, then the 48.0-51.2 sweep."""
    pts = []
    prev = CUTOFF_STEPS[0][1]
    for t, c in CUTOFF_STEPS:
        pts += [(t, np.log(prev)), (t + CUTOFF_GLIDE_S, np.log(c))]
        prev = c
    curve = np.exp(automation(pts))
    a, b, c0, c1 = CUTOFF_SWEEP
    i0, i1 = n_samples(a), n_samples(b)
    curve[i0:i1] = np.geomspace(c0, c1, i1 - i0)
    curve[i1:] = c1
    return curve


def pad_voices(notes, dur, attack, release, seed, curve="exp"):
    """3 detuned saws (+-7 cents) per note, panned L/C/R.  Stereo."""
    n = n_samples(dur) + n_samples(release)
    out = np.zeros((n, 2))
    env = adsr(dur, attack, 0.0, 1.0, release, curve)[:n]
    rng = np.random.default_rng(seed)
    for note in notes:
        f = hz(note)
        for c, p in zip(PAD_DETUNE_CENTS, PAD_PANS):
            v = saw(f, n / SR, [c], phase=rng.random())[:n]
            gl, gr = S.pan_gains(p)
            out[:, 0] += gl * v
            out[:, 1] += gr * v
    out /= np.sqrt(3 * len(notes))
    return out * env[:, None]


def tone(freq, dur, attack, release, gain=1.0, curve="exp"):
    n = n_samples(dur) + n_samples(release)
    return gain * sine(freq, n / SR)[:n] * adsr(dur, attack, 0.0, 1.0, release, curve)[:n]


def tick_sound(click=1.0, freq=2500.0, tau=0.0028, burst=1.0):
    """30 ms 110 Hz burst (amplitude ``burst``, 2 ms attack) + 8 ms click at ``freq``
    (amplitude 0.6 * ``click``, decay ``tau``)."""
    n = n_samples(0.03)
    t = np.arange(n) / SR
    y = burst * np.sin(2 * np.pi * 110.0 * t) * np.exp(-t / 0.012)
    y = fade(y, 2.0, 4.0)
    if click > 0:
        nc = n_samples(0.008)
        tc = np.arange(nc) / SR
        c = np.sin(2 * np.pi * freq * tc) * np.exp(-tc / tau)
        y[:nc] += 0.6 * click * fade(c, 0.2, 2.0)
    return y


def step_tick(seed):
    """12 ms band-passed noise 3-6 kHz."""
    n = n_samples(0.012)
    t = np.arange(n) / SR
    y = bandpass(noise(0.012, "white", seed=seed), 4200.0, 1.4) * np.exp(-t / 0.004)
    return S._norm_peak(fade(y, 0.5, 3.0), 0.9)


def kick_sound(seed=0):
    """Sine drop 55 -> 40 Hz + 5 ms noise click, low-passed (never club)."""
    body = synth_kick(0.6, 58.0, 40.0, click=0.0, drive=1.3, seed=seed)
    body = lowpass(body, 160.0, 0.7071)
    n = n_samples(0.005)
    t = np.arange(n) / SR
    click = lowpass(noise(0.005, "white", seed=seed + 100), 3000.0) * np.exp(-t / 0.0015)
    y = np.zeros(len(body))
    y[:n] += 0.12 * fade(click, 0.2, 1.0)
    y += body
    return S._norm_peak(fade(y, 0.5, 20.0), 0.9)


def hat_sound(seed):
    n = n_samples(0.06)
    t = np.arange(n) / SR
    y = highpass(noise(0.06, "white", seed=seed), 6000.0, 0.7071, order=4)
    y = onepole_lp(y, 9000.0) * np.exp(-t / 0.008)
    return S._norm_peak(fade(y, 0.3, 5.0), 0.8)


def riser_sound():
    """Band-passed noise 200 Hz -> 8 kHz + sine A3 -> A5 over 6.4 s; its
    peak is its very last sample (placed on the impact sample)."""
    t0, t1, f0, f1, n0, n1 = RISER
    n = n_samples(t1 - t0) + 1
    u = np.arange(n) / (n - 1)
    centre = f0 * (f1 / f0) ** u
    nz = bandpass(noise(n / SR, "white", seed=21)[:n], centre, 1.6)
    nz = S._norm_peak(onepole_lp(nz, 7500.0), 1.0)
    fs = hz(n0) * (hz(n1) / hz(n0)) ** u
    ph = 2 * np.pi * (np.cumsum(fs) - fs) / SR
    ph += (np.pi / 2 - ph[-1])              # sine ends exactly on its crest
    sn = np.sin(ph)
    amp = 0.03 + 0.97 * u ** 3.0
    taper = np.ones(n)
    k = n_samples(0.004)
    taper[-k:] = np.linspace(1.0, 0.0, k)   # noise hands over to the sine in the last 4 ms
    y = amp * (0.62 * sn + 0.42 * nz * taper)
    y[:n_samples(0.003)] *= np.linspace(0, 1, n_samples(0.003))
    m = np.abs(y[:-1]).max()
    if abs(y[-1]) <= m:                     # guarantee the peak on the last sample
        y[-1] = np.sign(y[-1] or 1.0) * m * 1.001
    tail = n_samples(0.005)                 # 5 ms release after the peak (under the impact)
    return np.concatenate([y, y[-1] * (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, tail)))])


def air_swell(dur=0.8, seed=31):
    """Band-passed noise 2-8 kHz rising exponentially to its peak on the last sample."""
    n = n_samples(dur) + 1
    t = np.arange(n) / SR
    nz = lowpass(highpass(noise(n / SR, "white", seed=seed)[:n], 2000.0), 8000.0)
    y = nz * np.exp(6.0 * (t / t[-1] - 1.0))          # -52 dB -> 0 dB
    y[:n_samples(0.02)] *= np.linspace(0, 1, n_samples(0.02))
    m = np.abs(y[:-1]).max()
    if abs(y[-1]) <= m:
        y[-1] = np.sign(y[-1] or 1.0) * m * 1.001      # the peak sample is the last one
    tail = n_samples(0.003)
    y = np.concatenate([y, y[-1] * (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, tail)))])
    return S._norm_peak(y, 1.0)


def air_hit(decay_s=1.0, seed=32):
    """Noise 3-9 kHz with an exponential decay (tau = decay_s / 4), 2 ms attack."""
    n = n_samples(decay_s * 1.6)
    t = np.arange(n) / SR
    nz = lowpass(highpass(noise(n / SR, "white", seed=seed)[:n], 3000.0), 9000.0)
    y = nz * np.exp(-t / (decay_s / 4.0)) * np.clip(t / 0.002, 0, 1)
    return S._norm_peak(fade(y, 0.5, 30.0), 1.0)


def plate_ir(decay_s=4.0, seed=11, predelay_ms=10.0):
    """Synthetic plate: exponentially decaying stereo noise, darker as it decays."""
    n = n_samples(decay_s)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    ir = rng.standard_normal((n, 2))
    tau = decay_s / 6.91
    low = lowpass(ir, 500.0)
    high = highpass(ir, 2500.0)
    mid = ir - low - high
    e = lambda k: np.exp(-t / (tau * k))[:, None]
    ir = low * e(1.1) + mid * e(1.0) + high * e(0.55)
    ir = lowpass(highpass(ir, 150.0), 7000.0, 0.5)
    ir = fade(ir, 8.0, 60.0)
    ir = np.concatenate([np.zeros((n_samples(predelay_ms / 1000), 2)), ir])
    return ir / np.sqrt((ir ** 2).sum(axis=0))      # unity power gain for noise


def convolve_stereo(x, ir):
    out = np.zeros_like(x)
    for c in range(2):
        out[:, c] = fftconvolve(x[:, c], ir[:, c])[:len(x)]
    return out


def impact_sound(ir):
    """40 ms noise burst + sub drop 60 -> 30 Hz (1.5 s decay) + low body."""
    dur = 3.0
    n = n_samples(dur)
    t = np.arange(n) / SR
    burst = np.zeros(n)
    nb = n_samples(0.04)
    burst[:nb] = lowpass(noise(0.04, "white", seed=5), 6500.0, 0.6) * np.exp(-np.arange(nb) / SR / 0.012)
    burst = fade(burst, 0.5, 10.0)
    f = 30.0 + 30.0 * np.exp(-t / 0.18)
    drop = np.sin(2 * np.pi * (np.cumsum(f) - f) / SR) * np.exp(-t / 0.45)
    drop *= np.clip(t / 0.004, 0, 1)
    body = S.pad_to(lowpass(synth_kick(0.9, 190.0, 42.0, click=0.3, seed=9), 1500.0), n)
    dry = 0.3 * burst + 1.0 * drop + 0.3 * body
    dry = S.softclip(dry, 1.6)
    return S._norm_peak(fade(dry, 0.3, 200.0), 1.0)


def reversed_swell(ir):
    """1.6 s time-reversed plate response of the Am(add9) stack (46.4 -> 48.0)."""
    chord = pad_voices(["A2", "E3", "A3", "C4", "E4", "B4"], 0.3, 0.01, 0.2, seed=77)
    chord = lowpass(chord, 1800.0, 0.75)
    wet = convolve_stereo(S.pad_to(chord, n_samples(1.6)), ir)[::-1]
    u = np.arange(len(wet)) / (len(wet) - 1)
    wet *= (0.05 + 0.95 * u ** 2.5)[:, None]
    wet = fade(wet, 20.0, 3.0)
    return S._norm_peak(wet, 1.0)


def coda_tone():
    """A2 with harmonics 1-8 at 1/n, gently low-passed; 1.6 s release from 74.4."""
    t0, rel_t, rel = CODA
    dur = rel_t - t0
    n = n_samples(dur) + n_samples(rel)
    t = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * 110.0 * k * t) / k for k in range(1, 9))
    y = lowpass(y, 2500.0, 0.6)
    y = S._norm_peak(y, 1.0) * adsr(dur, 0.5, 0.0, 1.0, rel, "exp")[:n]
    return fade(y, 3.0, 3.0)


def render(verbose=True):
    t_start = time.time()
    ir = plate_ir()
    bus = {k: Track(TOTAL_S) for k in ("pad", "sub", "pluck", "kick", "hat", "tick", "riser",
                                       "swell", "impact", "shimmer", "coda")}

    # --- pixel tone + partials (A pedal 0 -> 32.0) ---------------------------
    g = G["pixel"]
    bus["sub"].add(tone(110.0, 32.0, 0.8, 0.4, g, "lin"), 0.0)                       # A2 carrier
    bus["sub"].add(tone(55.0, 32.0, 0.8, 0.4, g * db2lin(-6), "lin"), 0.0)           # A1 support
    a3 = tone(220.0, 16.0, 0.8, 0.0, g, "lin")
    a3 *= automation([(0.0, db2lin(-12)), (3.2, db2lin(-12)), (3.5, db2lin(-6)),
                      (12.8, db2lin(-6)), (16.0, 0.0)], len(a3))
    bus["sub"].add(a3, 0.0)                                                          # A3 -12 -> -6 dB at 3.2
    p = G["partials"] * g
    e4 = tone(330.0, 9.6, 0.4, 0.0, p * db2lin(-10))
    e4 *= automation([(0.0, 1.0), (6.4, 1.0), (9.6, 0.0)], len(e4))
    bus["sub"].add(e4, 6.4)                                                          # harmonic 3
    a4 = tone(440.0, 6.4, 0.4, 0.0, p * db2lin(-12))
    a4 *= automation([(0.0, 1.0), (3.2, 1.0), (6.4, 0.0)], len(a4))
    bus["sub"].add(a4, 9.6)                                                          # harmonic 4
    bus["sub"].add(tone(110.0, 32.0 - 12.8, 3.0, 0.4, G["sub"], "lin"), 12.8)        # pedal lifts with the pad
    bus["sub"].add(tone(55.0, 32.0 - 12.8, 3.0, 0.4, G["sub"] * db2lin(-6), "lin"), 12.8)
    for ev in SUB_NOTES:                                                             # pedal follows the harmony
        root, t0, t1, att = (ev + (0.03,))[:4]
        f2 = hz(root)
        bus["sub"].add(tone(f2, t1 - t0, att, 0.08, G["sub"]), t0)
        bus["sub"].add(tone(f2 / 2, t1 - t0, att, 0.08, G["sub"] * db2lin(-6)), t0)

    # --- pad --------------------------------------------------------------------
    for i, (t0, t1, notes, a, r, gdb) in enumerate(PAD_CHORDS):
        bus["pad"].add(pad_voices(notes, t1 - t0, a, r, seed=100 + i, curve="lin" if a >= 2 else "exp"),
                       t0, gain=db2lin(gdb))
    pad = lowpass(bus["pad"].buf, cutoff_curve(), 0.75)                              # PAD FILTER = RESOLUTION
    pad *= gate_curve([VACUUM], keep=db2lin(G["vacuum_pad_db"]))[:, None]           # held at -12 dB
    pad *= G["pad"]

    # --- plucks through the dotted-8th delay --------------------------------------
    for k, ev in enumerate(PLUCKS):
        t, note, gdb = (ev + (0.0,))[:3]
        bus["pluck"].add(synth_pluck(note, 0.6, tone=0.35, seed=k), t, gain=G["pluck"] * db2lin(gdb), pan=0.12 * (-1) ** k)
    dt, fb, mix = PLUCK_DELAY
    plk = delay(bus["pluck"].buf, dt, fb, mix, ping_pong=True, tail_s=0)

    # --- drums ---------------------------------------------------------------------
    kk = kick_sound()
    for t in KICKS:
        bus["kick"].add(kk, t, gain=G["kick"])
    for i, (t, gdb) in enumerate(HATS):
        bus["hat"].add(hat_sound(300 + i), t, gain=G["hat"] * db2lin(gdb), pan=0.2)
    for t, gdb in TICKS:
        bus["tick"].add(tick_sound(), t, gain=G["tick"] * db2lin(gdb))
    for t, b_amp, c_amp, f in QT_TICKS:
        bus["tick"].add(tick_sound(c_amp / 0.6, f, QT_CLICK_TAU, b_amp), t, gain=1.0)
    for i, t in enumerate(STEP_TICKS):
        acc = STEP_ACCENTS.get(t, 0.0)
        bus["tick"].add(step_tick(500 + i), t, gain=G["step"] * db2lin(-16.0 + acc), pan=-0.15)

    # --- riser, reversed swell, impact ------------------------------------------------
    rs = riser_sound()
    bus["riser"].add(rs, RISER[0], gain=G["riser"])
    sw = reversed_swell(ir)
    bus["swell"].add(sw, SWELL[1] - len(sw) / SR, gain=G["swell"])
    bus["impact"].add(impact_sound(ir), HIT_T, gain=G["impact"])

    # --- shimmer -----------------------------------------------------------------------
    for i, (t, note, gdb) in enumerate(SHIMMER):
        n = n_samples(0.9)
        tt = np.arange(n) / SR
        s = np.sin(2 * np.pi * hz(note) * tt) * np.exp(-tt / 0.22)
        bus["shimmer"].add(fade(s, 15.0, 30.0), t, gain=G["shimmer"] * db2lin(gdb), pan=0.3 * (-1) ** i)
    d_t, d_fb, d_mix = SHIMMER_DELAY
    shm = delay(bus["shimmer"].buf, d_t, d_fb, d_mix, ping_pong=True, tail_s=0)
    shm *= gate_curve([(70.4, TOTAL_S)], keep=0.0, ramp=0.05)[:, None]              # collapse at 70.4

    # --- coda ----------------------------------------------------------------------------
    bus["coda"].add(coda_tone(), CODA[0], gain=G["coda"])

    # --- sidechain + vacuum gates ------------------------------------------------------------
    duck = duck_curve(KICKS)[:, None]
    pad *= duck
    sub = bus["sub"].buf * duck
    sub *= automation([(bar_t(8), 1.0), (bar_t(8) + 0.05, db2lin(-2)), (bar_t(11), db2lin(-2)),      # pedal -2 dB
                       (bar_t(11) + 0.05, 1.0), (bar_t(12), 1.0), (bar_t(12) + 0.05, db2lin(-2)),  # under the kick
                       (bar_t(20), db2lin(-2)), (bar_t(20) + 0.05, 1.0)])[:, None]
    vac = gate_curve([VACUUM])[:, None]
    sub *= vac
    plk *= vac
    kick_b = bus["kick"].buf * vac
    hat_b = bus["hat"].buf * vac
    shm *= vac

    layers = dict(pad=pad, sub=sub, pluck=plk, kick=kick_b, hat=hat_b, tick=bus["tick"].buf,
                  riser=bus["riser"].buf, swell=bus["swell"].buf, impact=bus["impact"].buf,
                  shimmer=shm, coda=bus["coda"].buf)

    # --- plate on its own wet bus (gated in the vacuum, dipped at the coda) ---------------
    send = sum(G["send"].get(k, 0.0) * v for k, v in layers.items())
    wet = convolve_stereo(send, ir)
    wet *= gate_curve([VACUUM], keep=G["vacuum_wet_keep"])[:, None]
    wet *= automation([(70.4, 1.0), (70.46, 0.1), (71.4, 1.0)])[:, None]
    dry = sum(layers.values())
    mix = dry + G["wet"] * wet
    mix = highpass(mix, 22.0, 0.7071)

    # --- fader ride to the §2.4 energy curve, then master ------------------------------
    ride = energy_ride(mix)
    mix *= ride[:, None]
    lufs_pre = measure_lufs(mix)
    norm = float(db2lin(G["lufs_target"] - lufs_pre))
    # air landings: added after the ride so their peaks land at the specified final levels
    wet_gate = gate_curve([VACUUM], keep=G["vacuum_wet_keep"])[:, None]
    air_dry, air_wet = Track(TOTAL_S), Track(TOTAL_S)
    for i, (t, kind, peak_db, dec) in enumerate(AIRS):
        snd = air_swell(dec, seed=31 + i) if kind == "swell" else air_hit(dec, seed=31 + i)
        at = (n_samples(t) - n_samples(dec)) / SR if kind == "swell" else t   # swell's peak sample = n_samples(t)
        amp = float(db2lin(peak_db)) / norm * np.sqrt(2.0)   # mono -> equal-power centre pan is -3 dB per side
        air_dry.add(snd, at, gain=amp)
        air_wet.add(convolve_stereo(S.to_stereo(snd), ir), at, gain=amp * G["send"]["air"])
    layers["air"] = air_dry.buf
    mix = mix + air_dry.buf + G["wet"] * air_wet.buf * wet_gate
    mix *= norm
    hit_win = (n_samples(HIT_T), n_samples(HIT_T + 0.35))          # the hit itself, before the first tick
    peak_in = S.peak_dbfs(mix[hit_win[0]:hit_win[1]])
    ceiling = G["ceiling_dbtp"] - 0.2
    for _ in range(4):                                       # true-peak safe limiting
        lim = limiter(mix, ceiling, lookahead_ms=5.0, release_ms=120.0)
        tp = true_peak_dbtp(lim)
        if tp <= G["ceiling_dbtp"] + 1e-3:
            break
        ceiling -= (tp - G["ceiling_dbtp"]) + 0.05
    gr_hit = S.peak_dbfs(lim[hit_win[0]:hit_win[1]]) - peak_in
    master = lim * automation([(SILENCE_FROM - 0.3, 1.0), (SILENCE_FROM, 0.0)])[:, None]
    master[n_samples(SILENCE_FROM):] = 0.0
    master = S.pad_to(master, N_TOTAL)
    info = dict(lufs_pre=lufs_pre, norm=norm, limiter_ceiling=ceiling, gr_at_hit_db=gr_hit,
                render_s=time.time() - t_start, ride_db=20 * np.log10(ride[::n_samples(BAR)]))
    return master, layers, info


def energy_ride(mix):
    """Smooth per-bar gain (<= +-ride_limit dB) aligning bar RMS with §2.4."""
    m = to_mono(mix)
    nb = n_samples(BAR)
    targets, centres = [], []
    for i, e in enumerate(ENERGY):
        if isinstance(e, tuple):
            targets += [e[0], e[1]]
            centres += [i * BAR + 0.8, i * BAR + 2.4]
        else:
            targets.append(e)
            centres.append(i * BAR + 1.6)
    meas = []
    for c in centres:
        half = 1.6 if c not in (14 * BAR + 0.8, 14 * BAR + 2.4) else 0.8
        seg = m[n_samples(c - half):n_samples(c + half)]
        meas.append(np.sqrt(np.mean(seg ** 2)) + 1e-9)
    ref_i = centres.index(15 * BAR + 1.6)   # bar 16 is the reference (energy 1.0)
    meas = np.array(meas)
    target_db = ENERGY_DB_PER_DECADE * np.log10(np.array(targets))
    meas_db = 20 * np.log10(meas / meas[ref_i])
    ride_db = np.clip(target_db - meas_db, -G["ride_limit_db"], G["ride_limit_db"])
    ride_db[ref_i] = 0.0
    # interpolate in dB, but step (not glide) across the vacuum boundaries and the impact
    pts = list(zip(centres, ride_db))
    t = np.arange(N_TOTAL) / SR
    curve = np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    v0, v1 = VACUUM
    i_v0, i_v1 = n_samples(v0), n_samples(v1)
    vac_db = ride_db[centres.index(14 * BAR + 2.4)]
    curve[i_v0:i_v1] = vac_db
    curve[i_v1:n_samples(HIT_T + BAR)] = 0.0       # bar 16 untouched (reference, impact headroom)
    curve[n_samples(14 * BAR):i_v0] = ride_db[centres.index(14 * BAR + 0.8)]
    g = 10 ** (curve / 20.0)
    g[i_v0 - n_samples(0.005):i_v0] = np.linspace(g[i_v0 - n_samples(0.005) - 1], g[i_v0], n_samples(0.005))
    return g


def loudness_range(x, sr=SR):
    """EBU R128 loudness range (LU): 3 s short-term windows, 10th-95th percentile after gating."""
    from scipy.signal import sosfilt
    y = sosfilt(S._k_weighting_sos(sr), S.to_stereo(x), axis=0)
    win, hop = n_samples(3.0), n_samples(0.5)
    cs = np.concatenate([np.zeros((1, 2)), np.cumsum(y * y, axis=0)])
    starts = np.arange(0, len(y) - win, hop)
    z = ((cs[starts + win] - cs[starts]) / win).sum(axis=1)
    st = -0.691 + 10 * np.log10(np.maximum(z, 1e-30))
    st = st[st > -70.0]
    if len(st) == 0:
        return 0.0
    rel = -0.691 + 10 * np.log10(np.mean(10 ** ((st + 0.691) / 10))) - 20.0
    st = st[st > rel]
    return float(np.percentile(st, 95) - np.percentile(st, 10))


def true_peak_dbtp(x):
    up = resample_poly(x, 4, 1, axis=0)
    return float(20 * np.log10(np.max(np.abs(up)) + 1e-12))


# =============================================================================
# 3. VERIFY
# =============================================================================
def onset_db(m, t, win=0.03, pre=0.05):
    """Energy in the 30 ms after t vs the 50 ms before, in dB (m may be band-limited)."""
    i = n_samples(t)
    post = m[i:i + n_samples(win)]
    before = m[max(0, i - n_samples(pre)):i]
    if len(post) == 0 or len(before) == 0:
        return float("nan")
    return 10 * np.log10((np.mean(post ** 2) + 1e-12) / (np.mean(before ** 2) + 1e-12))


BANDS = {"hf": "hats/step ticks: > 1.5 kHz", "click": "ticks: 2.5 kHz band, 10 ms", "mid": "plucks: > 600 Hz",
         "lf": "kicks: < 160 Hz", "full": "broadband"}


def band_views(m):
    return {"full": m, "hf": highpass(m, 1500.0, order=4), "mid": highpass(m, 600.0, order=4),
            "lf": lowpass(m, 160.0, order=4), "click": bandpass(m, 2500.0, 1.5),
            "step": bandpass(m, 4200.0, 1.4)}


def hit_onset_db(views, t, kind, freq=None):
    """Best band for the hit type: ticks by their click band (8 ms), kicks by LF or
    their click, plucks by their attack (> 600 Hz or > 1.5 kHz)."""
    if kind == "click":
        if freq is not None and abs(freq - 2500.0) > 1.0:
            key = ("click", round(freq))
            if key not in views:
                views[key] = bandpass(views["full"], freq, 1.5)
            return onset_db(views[key], t, win=0.008)
        return onset_db(views["click"], t, win=0.008)
    if kind == "lf":
        return max(onset_db(views["lf"], t, win=0.04), onset_db(views["hf"], t, win=0.01))
    if kind == "mid":
        return max(onset_db(views["mid"], t), onset_db(views["hf"], t, win=0.01))
    if kind == "hf":
        return max(onset_db(views["hf"], t, win=0.015), onset_db(views["step"], t, win=0.008))
    return onset_db(views["full"], t)


def verify(master, layers, info):
    ok = True
    m = to_mono(master)
    print("=" * 72)
    print(f"render time          : {info['render_s']:.1f} s")
    print(f"samples              : {len(master)} (required {N_TOTAL}) -> {'OK' if len(master) == N_TOTAL else 'FAIL'}")
    ok &= len(master) == N_TOTAL
    nan = int(np.sum(~np.isfinite(master)))
    print(f"nan/inf              : {nan}")
    ok &= nan == 0
    tp = true_peak_dbtp(master)
    lufs = measure_lufs(master)
    lra = loudness_range(master)
    print(f"true peak            : {tp:.2f} dBTP (ceiling {G['ceiling_dbtp']}), sample peak {S.peak_dbfs(master):.2f} dBFS")
    print(f"integrated loudness  : {lufs:.2f} LUFS (pre-normalisation {info['lufs_pre']:.2f}); LRA {lra:.1f} LU; limiter ceiling used {info['limiter_ceiling']:.2f} dB, gain change at the hit {info['gr_at_hit_db']:+.2f} dB")
    ok &= tp <= G["ceiling_dbtp"] + 0.05
    ok &= abs(lufs - G["lufs_target"]) <= 0.3
    # per-bar RMS vs energy curve
    rms = np.array([rms_dbfs(m[n_samples(i * BAR):n_samples((i + 1) * BAR)]) for i in range(24)])
    tgt = np.array([e if not isinstance(e, tuple) else e[0] for e in ENERGY])
    tgt_db = ENERGY_DB_PER_DECADE * np.log10(tgt) + rms[15]
    print("bar  rms(dBFS) target  ride")
    for i in range(24):
        print(f"{i + 1:3d}  {rms[i]:7.2f}  {tgt_db[i]:7.2f}  {info['ride_db'][i]:+5.1f}")
    corr = np.corrcoef(rms, np.log10(tgt))[0, 1]
    v_a = rms_dbfs(m[n_samples(44.8):n_samples(46.4)])
    v_b = rms_dbfs(m[n_samples(46.4):n_samples(48.0)])
    checks = {
        "rise bars 1-10 monotone": all(rms[i] < rms[i + 1] + 0.3 for i in range(9)),
        "dip at bar 11": rms[10] < rms[9],
        "bar 15 vacuum half quieter by > 6 dB": v_b < v_a - 6.0,
        "bar 16 loudest": int(np.argmax(rms)) == 15,
        "dip at bar 20": rms[19] < rms[18] - 3.0,
        "corr(rms_db, energy_db) > 0.95": corr > 0.95,
    }
    print(f"vacuum: 44.8-46.4 {v_a:.2f} dBFS vs 46.4-48.0 {v_b:.2f} dBFS; corr {corr:.3f}")
    for k, v in checks.items():
        print(f"  [{'OK' if v else 'FAIL'}] {k}")
        ok &= v
    # onset checks
    hits = [(0.8, "first tick", "click")] + [(t, "ring pluck", "mid") for t in grid(12.8, 15.6, E8)]
    hits += [(15.6, "pickup", "mid"), (15.8, "pickup", "mid"), (16.0, "downbeat", "mid")]
    hits += [(t, "roll", "mid") for t in (19.2, 19.4, 19.6, 19.8)]
    hits += [(22.4, "kick+hats", "lf"), (24.0, "kick / double", "lf")] + [(t, "fill pluck", "mid") for t in grid(28.8, 32.0, E8)]
    hits += [(35.2, "kick returns", "lf")] + [(t, "step tick", "hf") for t in STEP_TICKS] + [(t, "hat accent", "hf") for t in HAT_ACCENTS]
    hits += [(48.0, "IMPACT", "full")] + [(t, "qt tick", "click", f) for t, _, _, f in QT_TICKS]
    hits += [(32.0, "air swell", "air"), (44.8, "air hit", "air"), (51.2, "air hit", "air")]
    hits += [(51.2, "Fmaj7 kick", "lf"), (54.4, "G kick", "lf"), (57.6, "Cmaj9 kick", "lf"), (75.2, "final tick", "click")]
    views = band_views(m)
    print("onsets (energy 30 ms after vs 50 ms before, dB; band-limited per hit type: " + ", ".join(f"{k} = {v}" for k, v in BANDS.items()) + "):")
    lf40 = lowpass(m, 150.0, order=4)
    hf40 = highpass(m, 1200.0, order=4)
    print("  time   hit            band   rise   | 40 ms windows: LF<150 Hz  HF>1.2 kHz")
    qt_hf = []
    for ev in hits:
        t, name, band = ev[:3]
        freq = ev[3] if len(ev) > 3 else None
        if band == "air":
            d = onset_db(views["hf"], t, win=0.04, pre=0.04)
            flag = "info"                                     # airs are checked on their own layer below
        else:
            d = hit_onset_db(views, t, band, freq)
            flag = "OK" if d > 3.0 else "FAIL"
            ok &= d > 3.0
        lf_r = onset_db(lf40, t, win=0.04, pre=0.04)
        hf_r = onset_db(hf40, t, win=0.04, pre=0.04)
        if name == "qt tick":
            qt_hf.append(hf_r)
        print(f"  {t:6.2f} {name:14s} [{band:5s}] {d:+6.1f} {flag:4s} | LF {lf_r:+6.1f}  HF {hf_r:+6.1f}")
    new_steps = {t: onset_db(views["step"], t, win=0.012) for t in (24.0, 25.6, 27.2)}
    print("new step ticks, 3-6 kHz band rise (dB): " + ", ".join(f"{t} {d:+.1f}" for t, d in new_steps.items())
          + f" -> {'OK' if min(new_steps.values()) >= 8.0 else 'FAIL'} (>= +8 dB required)")
    ok &= min(new_steps.values()) >= 8.0
    qt_ok = min(qt_hf) >= 8.0
    print(f"quadtree ticks HF(>1.2 kHz, 40 ms) rise: min {min(qt_hf):+.1f} dB, max {max(qt_hf):+.1f} dB -> {'OK' if qt_ok else 'FAIL'} (>= +8 dB required)")
    ok &= qt_ok
    air = np.max(np.abs(layers["air"]), axis=1) * info["norm"]   # the air layer's per-channel peak at its final level
    for t, kind, peak_db, dec in AIRS:
        a0 = n_samples(t - (dec if kind == "swell" else 0.0))
        seg = air[a0:n_samples(t + (0.01 if kind == "swell" else dec * 1.6))]
        pk_t = (a0 + int(np.argmax(np.abs(seg)))) / SR
        good = abs(S.peak_dbfs(seg) - peak_db) < 0.2 and (kind != "swell" or abs(pk_t - t) < 1e-6)
        print(f"  air {kind:5s} at {t:5.1f}: peak {S.peak_dbfs(seg):+.1f} dBFS (spec {peak_db:+.0f}) at sample {a0 + int(np.argmax(np.abs(seg)))} = {pk_t:.5f} s -> {'OK' if good else 'FAIL'}")
        ok &= good
    d51 = max(hit_onset_db(views, 51.0, b) for b in ("click", "hf", "lf"))
    d51_mid = hit_onset_db(views, 51.0, "mid")
    print(f"  51.00 (must be silent)      {d51:+6.1f} in the tick/kick bands {'OK' if d51 < 1.0 else 'FAIL'}"
          f"   (> 600 Hz band {d51_mid:+.1f} dB = the pad's continuous 400 -> 4 kHz sweep, not an event)")
    ok &= d51 < 1.0
    # loudest transient in the file: among onsets (>= 6 dB rise), the one with the highest level
    hop = n_samples(0.01)
    w = n_samples(0.03)
    e = np.array([np.mean(m[i:i + w] ** 2) for i in range(0, len(m) - w, hop)])
    pre = np.concatenate([np.full(5, 1e-12), e[:-5]])
    rise = 10 * np.log10((e + 1e-12) / (pre + 1e-12))
    level = np.where(rise >= 6.0, e, 0.0)
    t_max = np.argmax(level) * hop / SR
    good = HIT_T - 0.01 <= t_max <= HIT_T + 0.05           # inside the impact's 40 ms burst
    print(f"loudest transient    : window at {t_max:.2f} s (level {10 * np.log10(level.max() + 1e-12):.1f} dBFS, rise {rise[np.argmax(level)]:.1f} dB) -> {'OK' if good else 'FAIL'}")
    ok &= good
    a, b = n_samples(HIT_T), n_samples(HIT_T + 0.3)
    print("layer peaks in 48.0-48.3 (dBFS, pre-master): " + ", ".join(f"{k} {S.peak_dbfs(v[a:b]):.1f}" for k, v in layers.items() if np.max(np.abs(v[a:b])) > 1e-4))
    # riser peak sample
    r = layers["riser"]
    i_peak = int(np.argmax(np.abs(to_mono(r))))
    print(f"riser peak sample    : {i_peak} (required {int(HIT_T * SR)}) -> {'OK' if i_peak == int(HIT_T * SR) else 'FAIL'}")
    ok &= i_peak == int(HIT_T * SR)
    # silence
    tail = master[n_samples(SILENCE_FROM):]
    print(f"silence 76.0-76.8    : max |x| = {np.max(np.abs(tail)) if len(tail) else 0} over {len(tail)} samples -> {'OK' if len(tail) == n_samples(0.8) and np.max(np.abs(tail)) == 0 else 'FAIL'}")
    ok &= len(tail) == n_samples(0.8) and np.max(np.abs(tail)) == 0
    # clicks
    dif = np.abs(np.diff(m))
    loc = np.sqrt(np.convolve(m ** 2, np.ones(960) / 960, "same")) + 1e-6
    ratio = dif / loc[1:]
    ratio[n_samples(47.99):n_samples(48.01)] = 0      # the impact onset is a transient by design
    print(f"click scan           : max jump/localRMS {ratio.max():.2f} at {ratio.argmax() / SR:.3f} s (click if > 10)")
    ok &= ratio.max() < 10
    print("RESULT               :", "ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    return ok


def main():
    master, layers, info = render()
    S.write_wav(OUT_WAV, master, SR, bits=24)
    print(f"wrote {OUT_WAV}")
    ok = verify(master, layers, info)
    from demo import spectrogram_png
    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    spectrogram_png(master, OUT_PNG, SR, BAR, width=1900, height=640)
    print(f"spectrogram          : {OUT_PNG}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
