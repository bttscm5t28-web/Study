"""Procedural soundtrack for the film: every note and sound is synthesised here
with numpy/scipy (no samples, no external audio).

Palette: felt piano, warm detuned-saw pads, additive plucks, FM "glass" pings
(the sound of a pixel), FM bell lead, sub bass, synthesized drums, noise risers,
impacts and whooshes, convolution reverb and ping-pong delay.

Harmony is in D major. A four-note rising motif (D-E-F#-A) runs through the film:
it is the piano line under the first pixel, the pitches of the subdivision ticks,
and in the climax each bar of the lead climbs higher than the last -- the
"ceiling" being pushed up, in sound.
"""
import numpy as np
from scipy import signal
from scipy.ndimage import maximum_filter1d, minimum_filter1d

import timeline as T

SR = 48000
LEN = T.DURATION + T.TAIL
N = int(LEN * SR)
rng = np.random.default_rng(20260922)


# ============================================================== helpers
def hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def secs(n):
    return np.arange(n) / SR


def _sos(kind, fc, order):
    return signal.butter(order, fc, kind, fs=SR, output="sos")


def lp(x, fc, order=2):
    return signal.sosfilt(_sos("lowpass", min(fc, SR * 0.45), order), x, axis=-1)


def hp(x, fc, order=2):
    return signal.sosfilt(_sos("highpass", fc, order), x, axis=-1)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos("bandpass", [lo, min(hi, SR * 0.45)], order), x, axis=-1)


def smooth_ramp(x):
    """0..1 -> 0..1 raised-cosine."""
    x = np.clip(x, 0.0, 1.0)
    return 0.5 - 0.5 * np.cos(np.pi * x)


def gate(t, dur, rel):
    """1 while the note is held, then an exponential release."""
    return np.where(t < dur, 1.0, np.exp(-(t - dur) / rel))


def polyblep(ph, dt):
    out = np.zeros_like(ph)
    m = ph < dt
    x = ph[m] / dt
    out[m] = 2 * x - x * x - 1
    m = ph > 1 - dt
    x = (ph[m] - 1) / dt
    out[m] = x * x + 2 * x + 1
    return out


def saw(f, n, ph0=0.0):
    dt = f / SR
    ph = (ph0 + dt * np.arange(n)) % 1.0
    return 2 * ph - 1 - polyblep(ph, dt)


def norm_rms(x, target):
    r = np.sqrt(np.mean(x ** 2)) + 1e-12
    return x * (target / r)


class Bus:
    def __init__(self, name):
        self.name = name
        self.x = np.zeros((2, N))

    def add(self, sig, t0, pan=0.0, gain=1.0):
        if sig.ndim == 1:
            a = (pan + 1) * np.pi / 4
            sig = np.stack([sig * np.cos(a), sig * np.sin(a)]) * np.sqrt(2)
        i0 = int(round(t0 * SR))
        if i0 < 0:
            sig = sig[:, -i0:]
            i0 = 0
        n = min(sig.shape[1], N - i0)
        if n > 0:
            self.x[:, i0:i0 + n] += gain * sig[:, :n]


# ============================================================== instruments
def piano(m, dur, vel=0.5):
    """Felt piano: inharmonic partials with two-stage decay, soft hammer, damper."""
    f = hz(m)
    n = int((dur + 0.9) * SR)
    t = secs(n)
    B = 0.00012 * (f / 130.0) ** 0.8
    tau = float(np.clip(3.2 * (261.6 / f) ** 0.55, 0.6, 7.0))
    tilt = 1.3 + (1 - vel) * 0.9
    y = np.zeros(n)
    for k in range(1, 29):
        fk = k * f * np.sqrt(1 + B * k * k)
        if fk > 12000:
            break
        ak = k ** -tilt * (0.35 + 0.65 * abs(np.sin(np.pi * k * 0.13)))
        tk = tau / (1 + 0.3 * (k - 1) ** 1.15)
        e = 0.6 * np.exp(-t / (tk * 0.22)) + 0.4 * np.exp(-t / tk)
        for d in (-0.7, 0.7):
            y += 0.5 * ak * e * np.sin(2 * np.pi * fk * 2 ** (d / 1200) * t + rng.random() * 6.283)
    y *= 1 - np.exp(-t / 0.005)
    y += lp(rng.standard_normal(n), 700) * np.exp(-t / 0.01) * 0.03
    y *= gate(t, dur, 0.22)
    y = lp(y, 2200 + 2600 * vel)
    return y * (0.3 + 0.7 * vel)


def pad(notes, dur, attack=1.4, release=1.8, cutoff=2000, detunes=(-13, -6, 0, 6, 13), width=0.9, seed=None):
    """Warm supersaw pad -> stereo (2, n)."""
    prng = np.random.default_rng(seed) if seed is not None else rng
    n = int((dur + release) * SR)
    t = secs(n)
    L = np.zeros(n)
    R = np.zeros(n)
    nv = len(detunes)
    for m in notes:
        f0 = hz(m)
        for k, c in enumerate(detunes):
            s = saw(f0 * 2 ** (c / 1200), n, prng.random())
            p = (k / (nv - 1) * 2 - 1) * width
            a = (p + 1) * np.pi / 4
            L += s * np.cos(a)
            R += s * np.sin(a)
    x = np.stack([L, R]) / np.sqrt(len(notes) * nv)
    x = lp(lp(x, cutoff), cutoff * 1.3)
    x = hp(x, 110)
    env = smooth_ramp(t / attack) * np.where(t < dur, 1.0, smooth_ramp(1 - (t - dur) / release))
    return x * env


def pluck(m, dur=0.22, vel=1.0, bright=1.0):
    f = hz(m)
    n = int((dur + 0.6) * SR)
    t = secs(n)
    y = np.zeros(n)
    for k in range(1, 19):
        if k * f > 11000:
            break
        y += (1.0 / k) * np.exp(-t * (3.0 + 3.4 * (k - 1) / bright)) * np.sin(2 * np.pi * k * f * t)
    y *= (1 - np.exp(-t / 0.0015)) * gate(t, dur, 0.07)
    return y * vel * 0.5


def glass(m, vel=1.0, decay=1.5, ratio=3.5, index=1.6):
    """FM ping: the sound of a pixel."""
    f = hz(m)
    n = int(decay * 4.5 * SR)
    t = secs(n)
    I = index * np.exp(-t / 0.07)
    y = np.sin(2 * np.pi * f * t + I * np.sin(2 * np.pi * f * ratio * t))
    y += 0.22 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t / (decay * 0.35))
    y *= np.exp(-t / decay) * (1 - np.exp(-t / 0.0008))
    return y * vel * 0.4


def lead(m, dur, vel=1.0):
    """FM bell-brass lead with delayed vibrato and a soft saw body."""
    f = hz(m)
    n = int((dur + 1.6) * SR)
    t = secs(n)
    vib = 1 + 0.0032 * np.sin(2 * np.pi * 5.0 * t) * np.clip((t - 0.3) / 0.5, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    I = 0.3 + 1.3 * np.exp(-t / 0.16)
    y = np.sin(ph + I * np.sin(ph))
    y += 0.28 * np.sin(2 * ph + 0.6 * np.exp(-t / 0.1) * np.sin(3 * ph))
    env = (1 - np.exp(-t / 0.004)) * (0.6 + 0.4 * np.exp(-t / 0.4)) * gate(t, dur, 0.4)
    body = lp(saw(f, n), 2400) * 0.22 * (0.65 + 0.35 * np.exp(-t / 0.5))
    return (0.5 * y + body) * env * vel


def bass(m, dur, vel=1.0, grit=0.0):
    f = hz(m)
    n = int((dur + 0.25) * SR)
    t = secs(n)
    y = np.sin(2 * np.pi * f * t) + 0.22 * np.sin(4 * np.pi * f * t) + 0.06 * np.sin(6 * np.pi * f * t)
    if grit:
        y += grit * lp(saw(f * 2, n), 650)
    y *= (1 - np.exp(-t / 0.006)) * gate(t, dur, 0.06)
    return np.tanh(1.3 * y) / np.tanh(1.3) * vel * 0.5


def kick(vel=1.0, punch=1.0):
    n = int(0.7 * SR)
    t = secs(n)
    f = 46 + 120 * punch * np.exp(-t / 0.03) + 28 * np.exp(-t / 0.12)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.36)
    click = hp(rng.standard_normal(n), 2500) * np.exp(-t / 0.003) * 0.22
    y = np.tanh(1.6 * (body + click)) * np.clip((0.7 - t) / 0.1, 0, 1)
    return y * vel * 0.8


def clap(vel=1.0):
    n = int(0.7 * SR)
    t = secs(n)
    nz = bp(rng.standard_normal(n), 900, 3200)
    env = np.zeros(n)
    for d in (0.0, 0.011, 0.022, 0.033):
        env += (t >= d) * np.exp(-np.clip(t - d, 0, None) / 0.007)
    env += 0.55 * (t >= 0.033) * np.exp(-np.clip(t - 0.033, 0, None) / 0.16)
    return nz * env * vel * 0.3


def snare(vel=1.0):
    n = int(0.4 * SR)
    t = secs(n)
    nz = bp(rng.standard_normal(n), 1200, 7500) * np.exp(-t / 0.1)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.045)
    return (0.55 * nz + 0.4 * tone) * vel * 0.4


def hat(vel=1.0, open_=False):
    n = int((0.5 if open_ else 0.12) * SR)
    t = secs(n)
    y = hp(rng.standard_normal(n), 7500, 4) * np.exp(-t / (0.17 if open_ else 0.022))
    return y * vel * 0.12


def crash(vel=1.0, length=3.0):
    n = int(length * SR)
    t = secs(n)
    out = []
    for _ in range(2):
        nz = hp(rng.standard_normal(n), 3800, 2)
        met = sum(np.sin(2 * np.pi * fr * t + rng.random() * 6) for fr in (3170, 4410, 5230, 6750, 8010, 9270)) / 6
        y = (0.8 * nz + 0.3 * met) * np.exp(-t / 1.0) * (1 - np.exp(-t / 0.002))
        out.append(lp(y, 12000))
    return np.stack(out) * vel * 0.09


def impact(vel=1.0, length=3.2, bright=1.0):
    n = int(length * SR)
    t = secs(n)
    f = 31 + 42 * np.exp(-t / 0.22)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 1.0)
    nz = lp(rng.standard_normal(n), 1500 * bright) * np.exp(-t / 0.22) * 0.45
    y = np.tanh(1.5 * (sub + nz)) * (1 - np.exp(-t / 0.002))
    return y * vel * 0.6


def boom(vel=1.0):
    """Soft low hit used on chapter starts."""
    n = int(1.6 * SR)
    t = secs(n)
    f = 44 + 30 * np.exp(-t / 0.08)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.5) * (1 - np.exp(-t / 0.003))
    y += lp(rng.standard_normal(n), 500) * np.exp(-t / 0.05) * 0.15
    return y * vel * 0.5


def noise_sweep(length, f0, f1, q=0.4, shape=1.3, env=None):
    """Noise through a band-pass that glides from f0 to f1 (log-frequency)."""
    n = int(length * SR)
    x = rng.standard_normal(n + 4096)
    f, tt, Z = signal.stft(x, SR, nperseg=2048)
    frac = np.clip(tt / length, 0, 1)
    fc = f0 * (f1 / f0) ** (frac ** shape)
    logf = np.log2(np.maximum(f, 20))[:, None]
    g = np.exp(-0.5 * ((logf - np.log2(fc)[None, :]) / q) ** 2)
    _, y = signal.istft(Z * g, SR, nperseg=2048)
    y = norm_rms(y[:n], 0.25)
    if env is not None:
        y *= env(np.arange(n) / n)
    return y


def riser(length):
    a = noise_sweep(length, 250, 9000, q=0.45, shape=1.4, env=lambda u: u ** 2.2)
    n = len(a)
    t = secs(n)
    f = 180 * (12) ** (t / length) ** 1.5
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / length) ** 3 * 0.12
    return a + tone


def whoosh(length, up=True):
    """up: swells into the next downbeat; down: recedes (used for zoom-outs)."""
    if up:
        return noise_sweep(length, 300, 6000, q=0.5, shape=1.0,
                           env=lambda u: u ** 2 * np.clip((1 - u) / 0.08, 0, 1))
    return noise_sweep(length, 5000, 200, q=0.5, shape=1.0,
                       env=lambda u: np.sin(np.pi * np.clip(u, 0, 1) ** 0.6) ** 2)


def click(vel=1.0):
    n = int(0.03 * SR)
    t = secs(n)
    y = bp(rng.standard_normal(n), 1500, 6000) * np.exp(-t / 0.004)
    y += 0.35 * np.sin(2 * np.pi * (2300 + rng.random() * 400) * t) * np.exp(-t / 0.006)
    return y * vel * 0.18


def snap():
    n = int(0.4 * SR)
    t = secs(n)
    tk = hp(rng.standard_normal(n), 2200) * np.exp(-t / 0.005)
    f = 1800 + 3200 * np.exp(-t / 0.018)
    chirp = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.035) * 0.5
    return (0.6 * tk + chirp) * 0.45


def make_ir(rt60, predelay=0.018, length=None):
    length = length or rt60 * 1.25
    n = int(length * SR)
    t = secs(n)
    chans = []
    for _ in range(2):
        w = rng.standard_normal(n)
        lo = lp(w, 450)
        hi = hp(w, 4200)
        mi = w - lo - hi
        x = (lo * np.exp(-6.91 * t / (rt60 * 1.15)) + mi * np.exp(-6.91 * t / rt60)
             + hi * np.exp(-6.91 * t / (rt60 * 0.38)))
        chans.append(x * (1 - np.exp(-t / 0.006)))
    ir = np.concatenate([np.zeros((2, int(predelay * SR))), np.stack(chans)], axis=1)
    return ir / np.sqrt(np.sum(ir ** 2, axis=1, keepdims=True))


def reverb(x, ir, mix):
    wet = np.stack([signal.fftconvolve(x[0], ir[0])[:N], signal.fftconvolve(x[1], ir[1])[:N]])
    return x + mix * wet


def pingpong(x, d_s, fb=0.42, mix=0.3, taps=7, damp=3800):
    d = int(d_s * SR)
    mono = 0.5 * (x[0] + x[1])
    y = x.copy()
    tap = mono
    for i in range(1, taps + 1):
        tap = lp(tap, damp)
        g = mix * fb ** (i - 1)
        ch = i % 2
        if i * d < N:
            y[ch, i * d:] += g * tap[:N - i * d]
    return y


def duck_curve(times, depth=0.35, rel=0.15):
    e = np.zeros(N)
    n = int(rel * 6 * SR)
    tt = secs(n)
    shape = (1 - np.exp(-tt / 0.004)) * np.exp(-tt / rel)
    for tk in times:
        i0 = int(tk * SR)
        seg = e[i0:i0 + n]
        np.maximum(seg, shape[:len(seg)], out=seg)
    return 1 - depth * e


def automation(points):
    """Piecewise-linear gain curve from [(time, gain), ...]."""
    ts = np.array([p[0] for p in points]) * SR
    gs = np.array([p[1] for p in points])
    return np.interp(np.arange(N), ts, gs)


# ============================================================== harmony
# name: (pad voicing, arp notes, bass root)
CH = {
    "Dmaj9":  ([50, 57, 61, 64, 66], [62, 66, 69, 73, 76], 38),
    "Bm11":   ([47, 54, 57, 62, 64], [59, 62, 66, 69, 74], 35),
    "Gmaj9":  ([43, 50, 54, 57, 59], [62, 66, 67, 69, 74], 31),
    "Asus":   ([45, 52, 57, 59, 62], [59, 62, 64, 69, 71], 33),
    "A6":     ([45, 52, 57, 61, 66], [61, 64, 66, 69, 73], 33),
    "Em9":    ([52, 59, 62, 66, 67], [59, 62, 66, 67, 71], 40),
    "A7sus4": ([45, 52, 55, 62, 64], [57, 62, 64, 67, 69], 33),
    "G":      ([43, 50, 55, 59, 62], [62, 67, 71, 74, 79], 31),
    "A":      ([45, 52, 57, 61, 64], [64, 69, 73, 76, 81], 33),
    "Bm":     ([47, 54, 59, 62, 66], [66, 71, 74, 78, 83], 35),
    "A/C#":   ([49, 52, 57, 61, 64], [64, 69, 73, 76, 81], 37),
    "D":      ([50, 57, 62, 66, 69], [66, 69, 74, 78, 81], 38),
    "F#m":    ([42, 49, 54, 57, 61], [61, 66, 69, 73, 78], 42),
    "Gmaj7":  ([43, 50, 55, 59, 62, 66], [62, 66, 67, 71, 74], 31),
}

# (start bar, chord, length in bars)
PROG = [
    (2, "Dmaj9", 2),
    (4, "Dmaj9", 2), (6, "Bm11", 2), (8, "Gmaj9", 2), (10, "Asus", 1), (11, "A6", 1),
    (12, "Em9", 1), (13, "A7sus4", 1),
    (14, "G", 1), (15, "A", 1), (16, "Bm", 1), (17, "A/C#", 1),
    (18, "D", 1), (19, "A", 1), (20, "Bm", 1), (21, "F#m", 1), (22, "Gmaj7", 1),
    (23, "Dmaj9", 1), (24, "Bm11", 1),
    (25, "Gmaj9", 1), (26, "Asus", 1), (27, "Dmaj9", 3),
]


def chord_at(bar):
    for b0, name, ln in PROG:
        if b0 <= bar < b0 + ln:
            return name
    return None


ARP_PAT = [0, 2, 4, 2, 1, 3, 4, 3, 0, 2, 4, 3, 1, 2, 3, 4]


# ============================================================== composition
def compose():
    B = {k: Bus(k) for k in ("pad", "piano", "arp", "lead", "bass", "drums", "glass", "fx", "drone")}
    tb = T.t
    beat = T.BEAT

    # ---------------------------------------------------------- drone (intro)
    n = int(11.5 * SR)
    tt = secs(n)
    dr = sum(a * np.sin(2 * np.pi * hz(m) * tt + rng.random() * 6) for m, a in ((26, 0.7), (33, 0.35), (38, 0.4), (45, 0.12)))
    dr *= 1 + 0.15 * np.sin(2 * np.pi * 0.21 * tt)
    air = hp(lp(rng.standard_normal(n), 5000), 1200) * 0.05 * (1 + 0.5 * np.sin(2 * np.pi * 0.13 * tt))
    env = smooth_ramp(tt / 3.0) * smooth_ramp((11.5 - tt) / 2.2)
    B["drone"].add(np.stack([(dr + air) * env, (dr + np.roll(air, 977)) * env]) * 0.16, 0.0)

    # ---------------------------------------------------------- pads
    for b0, name, ln in PROG:
        notes = CH[name][0]
        dur = ln * T.BAR
        if b0 == 2:          # intro: opens up as the pixel subdivides
            x = pad(notes, dur, attack=2.2, release=1.2, cutoff=900, seed=11)
            x2 = pad(notes, dur, attack=2.2, release=1.2, cutoff=3200, seed=11)
            u = smooth_ramp(secs(x.shape[1]) / (dur * 0.9))
            x = x * (1 - u) + x2 * u
            B["pad"].add(x, tb(b0), gain=0.55)
            continue
        cutoff = {4: 2200, 6: 2400, 8: 2600, 10: 2700, 11: 2800, 12: 1400, 13: 1600}.get(b0, 2200)
        if 14 <= b0 <= 17:
            cutoff = 1800 + (b0 - 14) * 700
        if 18 <= b0 <= 22:
            cutoff = 4200
        if b0 >= 23:
            cutoff = 1700
        rel = 1.6 if b0 < 27 else 4.5
        att = 0.35 if 14 <= b0 <= 22 else (1.0 if b0 >= 23 else 0.8)
        g = 0.62 if 18 <= b0 <= 22 else 0.5
        B["pad"].add(pad(notes, dur, attack=att, release=rel, cutoff=cutoff), tb(b0), gain=g)
        if 18 <= b0 <= 22:   # octave-up shimmer layer in the climax
            B["pad"].add(pad([m + 12 for m in notes[1:]], dur, attack=0.25, release=1.2, cutoff=6000), tb(b0), gain=0.16)

    # ---------------------------------------------------------- arpeggio
    for bar in range(4, 23):
        name = chord_at(bar)
        if name is None or bar in (12,):
            continue
        arp = CH[name][1]
        step = 0.5 if bar < 6 else 0.25          # eighths, then sixteenths
        nsteps = int(4 / step)
        bright = 0.8 if bar < 14 else (1.0 + (bar - 14) * 0.25 if bar < 18 else 1.8)
        lvl = 0.75 if bar < 14 else (0.75 + (bar - 14) * 0.05 if bar < 18 else 0.85)
        if bar == 13:
            lvl = 0.35
        for s in range(nsteps):
            pos = s * step
            idx = ARP_PAT[s % 16] if step == 0.25 else ARP_PAT[(2 * s) % 16]
            acc = 1.0 if pos % 1 == 0 else (0.75 if pos % 0.5 == 0 else 0.55)
            m = arp[idx]
            B["arp"].add(pluck(m, dur=step * beat * 0.9, vel=acc * lvl, bright=bright), tb(bar, pos),
                         pan=0.35 * np.sin(s * 1.7 + bar))

    # ---------------------------------------------------------- bass
    for bar in range(4, 30):
        name = chord_at(bar)
        if name is None:
            continue
        r = CH[name][2]
        if 4 <= bar < 12:
            for pos in (0, 2):
                B["bass"].add(bass(r, 1.9 * beat, vel=0.32 if bar < 8 else 0.4), tb(bar, pos))
        elif bar == 13:
            B["bass"].add(bass(r, 3.8 * beat, vel=0.5), tb(bar, 0))
        elif 14 <= bar < 18:
            for k in range(8):
                v = 0.7 + 0.04 * (bar - 14)
                B["bass"].add(bass(r, 0.45 * beat, vel=v, grit=0.15), tb(bar, k * 0.5))
        elif 18 <= bar < 23:
            for k in range(8):
                m = r + (12 if k % 2 else 0)
                B["bass"].add(bass(m, 0.42 * beat, vel=0.9, grit=0.3), tb(bar, k * 0.5))
        elif 23 <= bar < 27:
            B["bass"].add(bass(r, 3.9 * beat, vel=0.45), tb(bar, 0))
        elif bar == 27:
            B["bass"].add(bass(r, 3 * T.BAR, vel=0.38), tb(bar, 0))

    # ---------------------------------------------------------- drums
    D = B["drums"]
    kicks = []

    def K(bar, pos, v=1.0, punch=1.0):
        kicks.append(tb(bar, pos))
        D.add(kick(v, punch), tb(bar, pos))

    for bar in (4, 5):
        K(bar, 0, 0.55, 0.6)
    for bar in (6, 7):
        K(bar, 0, 0.65, 0.7)
        K(bar, 2.5, 0.5, 0.6)
    for bar in range(8, 12):
        K(bar, 0, 0.75)
        K(bar, 2.5, 0.6)
        D.add(clap(0.55), tb(bar, 2), pan=0.05)
        for k in range(4):
            D.add(hat(0.6), tb(bar, k + 0.5), pan=0.3)
        for k in range(16):
            D.add(hat(0.18 + 0.1 * (k % 2)), tb(bar, k * 0.25), pan=-0.35)
    K(13, 2, 0.5, 0.5)
    for bar in range(14, 18):
        for b_ in range(4):
            if bar == 17 and b_ == 3:
                break
            K(bar, b_, 0.65 + 0.1 * (bar - 14))
        if bar >= 15:
            for b_ in (1, 3):
                if not (bar == 17 and b_ == 3):
                    D.add(clap(0.6 + 0.08 * (bar - 15)), tb(bar, b_))
            step = 0.5 if bar == 15 else 0.25
            for k in range(int(4 / step)):
                if bar == 17 and k * step >= 3:
                    break
                D.add(hat(0.35 + 0.25 * ((k * step) % 1 == 0.5)), tb(bar, k * step), pan=0.25)
    # snare roll into the break
    roll = [(tb(17, 0) + k * beat / 4, 0.25 + 0.03 * k) for k in range(8)]
    roll += [(tb(17, 2) + k * beat / 8, 0.5 + 0.05 * k) for k in range(8)]
    for tk, v in roll:
        D.add(snare(min(v, 0.95)), tk, pan=0.1)
    # the climax
    for bar in range(18, 23):
        for b_ in range(4):
            K(bar, b_, 1.0)
            D.add(hat(0.55, open_=True), tb(bar, b_ + 0.5), pan=0.2)
        for b_ in (1, 3):
            D.add(clap(0.85), tb(bar, b_))
        for k in range(16):
            D.add(hat(0.22 + 0.12 * (k % 2)), tb(bar, k * 0.25), pan=-0.3)
    K(23, 0, 0.8)
    for tc, v in ((T.DROP, 1.0), (T.MONTAGE[4], 1.0), (tb(23), 0.7)):
        D.add(crash(v), tc)

    # ---------------------------------------------------------- lead (climax melody: every bar peaks higher)
    LEAD = [
        (18, [(74, 0, 1.5), (76, 1.5, 0.5), (78, 2, 1), (81, 3, 1)]),
        (19, [(76, 0, 1.5), (78, 1.5, 0.5), (81, 2, 1), (83, 3, 1)]),
        (20, [(78, 0, 1.5), (81, 1.5, 0.5), (83, 2, 1), (86, 3, 1)]),
        (21, [(81, 0, 1.5), (83, 1.5, 0.5), (85, 2, 1), (88, 3, 1)]),
        (22, [(86, 0, 1.5), (88, 1.5, 0.5), (90, 2, 5.0)]),
    ]
    for bar, notes in LEAD:
        for m, pos, ln in notes:
            B["lead"].add(lead(m, ln * beat * 0.95, vel=0.9), tb(bar, pos), pan=0.0)
            B["lead"].add(lead(m - 12, ln * beat * 0.95, vel=0.32), tb(bar, pos), pan=-0.2)

    # ---------------------------------------------------------- piano
    P = B["piano"]
    for m, pos, v in ((74, 0, 0.42), (76, 1.5, 0.34), (78, 2, 0.38), (81, 3, 0.36)):
        P.add(piano(m, 2.4, v), tb(1, pos), pan=0.15)
    P.add(piano(50, 3.0, 0.3), tb(1, 0), pan=-0.3)
    for c in T.CAPS[:4]:
        name = chord_at(int(round(c / T.BAR)))
        pv = CH[name][0]
        P.add(piano(pv[0] - 12, 3.5, 0.35), c, pan=-0.3)
        P.add(piano(pv[-1] + 12, 3.0, 0.3), c + beat * 0.02, pan=0.25)
    for m, pos in ((64, 0), (71, 0.5), (74, 1.5), (78, 2.5)):
        P.add(piano(m, 3.0, 0.3), tb(12, pos), pan=0.1)
    for m, pos, v in ((74, 0, 0.45), (76, 1.5, 0.36), (78, 2, 0.4), (81, 3, 0.38),
                      (78, 4, 0.34), (76, 5.5, 0.3), (74, 6, 0.36)):
        P.add(piano(m, 3.0, v), tb(23, pos), pan=0.15)
    for m in (38, 50, 57):
        P.add(piano(m, 4.5, 0.35), tb(23, 0), pan=-0.25)
    for m in (43, 55):
        P.add(piano(m, 2.4, 0.3), tb(25, 0), pan=-0.25)
    for m in (45, 57):
        P.add(piano(m, 2.4, 0.3), tb(26, 0), pan=-0.25)
    for m, v in ((38, 0.4), (50, 0.36), (57, 0.32), (66, 0.3), (73, 0.26), (76, 0.24)):
        P.add(piano(m, 6.5, v), T.TAGLINE + (m % 5) * 0.012, pan=(m - 60) / 40)
    for m, pos, v in ((74, 0, 0.32), (76, 1.5, 0.27), (78, 2, 0.3), (81, 3, 0.28)):
        P.add(piano(m, 3.5, v), tb(28, pos), pan=0.2)

    # ---------------------------------------------------------- glass: the voice of the pixel
    G = B["glass"]
    G.add(glass(86, 0.7, decay=2.2), T.PIXEL_APPEAR, pan=0.0)
    for k, (tk, m) in enumerate(zip(T.SUBDIV, (74, 76, 78, 81, 86))):
        G.add(glass(m, 0.5 + 0.08 * k, decay=1.4), tk, pan=(-0.4, 0.4, -0.2, 0.2, 0.0)[k])
        G.add(click(0.6), tk)
    for c in T.CAPS[:4]:
        name = chord_at(int(round(c / T.BAR)))
        top = CH[name][1]
        G.add(glass(top[-1] + 12, 0.35, decay=1.8), c + 0.01, pan=0.3)
        G.add(glass(top[2] + 12, 0.25, decay=1.8), c + 0.03, pan=-0.3)
    # scattered pixels -> alignment
    pent = [74, 76, 78, 81, 83, 86, 88, 90, 93]
    tk = T.CAPS[4] + 0.15
    while tk < T.ALIGN_SNAP - 0.08:
        u = (tk - T.CAPS[4]) / (T.ALIGN_SNAP - T.CAPS[4])
        G.add(glass(pent[rng.integers(len(pent))], 0.10 + 0.08 * u, decay=0.35, index=2.5),
              tk, pan=rng.uniform(-0.9, 0.9))
        tk += rng.uniform(0.05, 0.16) * (1.2 - 0.6 * u)
    for m in (81, 86, 88):
        G.add(glass(m, 0.5, decay=2.4), T.ALIGN_SNAP, pan=(m - 86) / 8)
    # columns stacking up (a quick climbing glissando per column)
    scale = [62, 64, 66, 69, 71, 74, 76, 78, 81, 83, 86, 88, 90, 93, 95, 98]
    heights = [4, 6, 8, 10, 12]
    for ci, (tc, h) in enumerate(zip(T.COLUMN_RISE, heights)):
        for k in range(h):
            G.add(glass(scale[k + ci], 0.14 + 0.02 * k, decay=0.5), tc + k * 0.032, pan=-0.6 + ci * 0.25)
    t0, t1 = T.COLUMN_LAST
    k = 0
    tk = t0
    while tk < t1:
        u = (tk - t0) / (t1 - t0)
        G.add(glass(scale[k % len(scale)] + 12 * (k // len(scale) % 2), 0.10 + 0.12 * u, decay=0.45), tk, pan=0.55)
        k += 1
        tk += 0.16 * (1 - u) ** 1.5 + 0.03
    for m in (86, 90, 93, 98):
        G.add(glass(m, 0.35, decay=1.2, index=3.0), T.BREAK + rng.uniform(0, 0.03), pan=rng.uniform(-0.8, 0.8))
    G.add(glass(86, 0.6, decay=2.0), T.SHRINK[1], pan=0.0)
    for i in range(15):
        G.add(click(rng.uniform(0.7, 1.0)), T.TYPE[0] + i * 0.075, pan=-0.3 + i * 0.04)
    G.add(glass(81, 0.35, decay=3.0), T.TAGLINE + 0.02, pan=0.2)
    G.add(glass(86, 0.32, decay=3.2), T.t(28, 3.6), pan=0.0)

    # ---------------------------------------------------------- fx
    F = B["fx"]
    F.add(boom(0.4), T.PIXEL_APPEAR)
    F.add(boom(0.4), T.EXPAND)
    F.add(whoosh(0.9, up=True), T.WIPE1[1] - 0.85, pan=0.0, gain=0.5)
    F.add(impact(0.45, bright=0.6), T.CAPS[0])
    for c in T.CAPS[1:4]:
        F.add(whoosh(0.45, up=True), c - 0.42, gain=0.28)
        F.add(boom(0.75), c)
    F.add(boom(0.6), T.CAPS[0])
    F.add(snap(), T.ALIGN_SNAP)
    F.add(impact(0.5, bright=0.7), T.ALIGN_SNAP)
    F.add(riser(T.BREAK - T.t(15, 2)), T.t(15, 2), gain=0.55)
    # the shatter, then a held breath before the drop
    n = int(0.6 * SR)
    tt = secs(n)
    crack = hp(rng.standard_normal(n), 1500) * np.exp(-tt / 0.05) * 0.5
    F.add(np.stack([crack, np.roll(crack, 211)]), T.BREAK)
    rev = crash(0.9, 2.0)[:, ::-1]
    rev = rev[:, -int((T.DROP - T.BREAK) * SR):]
    F.add(rev * 2.2, T.BREAK)
    F.add(impact(1.0), T.DROP)
    for i, tm in enumerate(T.MONTAGE[1:], start=1):
        F.add(whoosh(T.ZOOM_OUT_LEN + 0.1, up=False), tm - T.ZOOM_OUT_LEN - 0.05, gain=0.45, pan=0.0)
        F.add(impact(0.75 if i < 4 else 1.0, bright=0.8), tm)
    # the scan line sweeping across the earth, left to right
    sc = noise_sweep(1.55, 700, 7000, q=0.6, shape=1.0, env=lambda u: np.sin(np.pi * np.clip(u, 0, 1)) ** 1.5)
    pa = (np.linspace(-0.8, 0.8, len(sc)) + 1) * np.pi / 4
    F.add(np.stack([sc * np.cos(pa), sc * np.sin(pa)]) * np.sqrt(2), T.MONTAGE[4] + 0.05, gain=0.2)
    rev2 = crash(0.8, 2.0)[:, ::-1][:, -int(1.2 * SR):]
    F.add(rev2 * 1.6, T.MONTAGE[4] - 1.2)
    F.add(whoosh(1.4, up=False), T.t(23) - 0.2, gain=0.3)
    F.add(whoosh(T.SHRINK[1] - T.SHRINK[0], up=False), T.SHRINK[0], gain=0.4)
    F.add(boom(0.45), T.TAGLINE)

    # ---------------------------------------------------------- buses -> mix
    duck_drop = duck_curve([k for k in kicks if T.DROP - 0.01 <= k < T.t(23)], depth=0.38)
    hall = make_ir(3.0)
    room = make_ir(1.4, predelay=0.01)
    big = make_ir(4.5, predelay=0.03)

    B["pad"].x *= duck_drop
    B["bass"].x *= duck_curve([k for k in kicks if T.DROP - 0.01 <= k < T.t(23)], depth=0.55, rel=0.11)
    B["arp"].x = pingpong(B["arp"].x, 0.75 * beat, fb=0.38, mix=0.3)

    stems = {
        "drone": reverb(B["drone"].x, hall, 0.4) * 0.9,
        "pad": reverb(B["pad"].x, hall, 0.45) * 0.42,
        "piano": reverb(B["piano"].x, hall, 0.5) * 0.85,
        "arp": reverb(B["arp"].x, hall, 0.35) * 0.30,
        "lead": reverb(pingpong(B["lead"].x, 0.75 * beat, fb=0.3, mix=0.18), big, 0.45) * 0.46,
        "bass": B["bass"].x * 0.62,
        "drums": reverb(B["drums"].x, room, 0.18) * 0.62,
        "glass": reverb(B["glass"].x, big, 0.7) * 0.55,
        "fx": reverb(B["fx"].x, big, 0.35) * 0.8,
    }
    # fader ride: quiet open, the climax at full level, then a calmer landing
    ride = automation([(0, 0.48), (9.8, 0.5), (10.0, 0.68), (30, 0.66), (32.4, 0.56), (35, 0.64),
                       (44.3, 0.9), (45, 1.0), (57.3, 1.0), (57.7, 0.66), (62.5, 0.6), (75, 0.56),
                       (LEN, 0.56)])
    for k in stems:
        stems[k] = stems[k] * ride
    return stems


# ============================================================== mastering
def master(stems):
    x = sum(stems.values())
    x = hp(x, 28, 2)
    x = shelf(x, 90, -2.0, "low")     # less sub rumble, more of the music on small speakers
    x = shelf(x, 5500, 2.5, "high")   # a little air
    # gentle glue compression
    a = np.exp(-1 / (0.05 * SR))
    pw = signal.lfilter([1 - a], [1, -a], np.max(x ** 2, axis=0))
    lvl = np.sqrt(np.maximum(pw, 1e-12))
    thr = 10 ** (-14 / 20)
    gain = np.minimum(1.0, (lvl / thr) ** (1 / 1.35 - 1))
    b = np.exp(-1 / (0.12 * SR))
    gain = signal.lfilter([1 - b], [1, -b], gain)
    x = x * gain
    # loudness: put the climax at about -12.5 dBFS RMS
    i0, i1 = int(T.DROP * SR), int(T.t(23) * SR)
    rms = np.sqrt(np.mean(x[:, i0:i1] ** 2))
    x *= 10 ** (-12.5 / 20) / rms
    # look-ahead peak limiter at -1 dBFS
    ceiling = 10 ** (-1.0 / 20)
    L = int(0.003 * SR)
    pk = maximum_filter1d(np.max(np.abs(x), axis=0), size=2 * L + 1)
    g = np.minimum(1.0, ceiling / np.maximum(pk, 1e-9))
    g = minimum_filter1d(g, size=2 * L + 1)
    win = np.hanning(L) / np.hanning(L).sum()
    g = np.convolve(g, win, mode="same")
    x = x * g
    x = np.clip(x, -ceiling, ceiling)
    # fade out
    t = secs(N)
    f0, f1 = T.FADE_OUT
    x *= np.where(t < f0, 1.0, np.cos(0.5 * np.pi * np.clip((t - f0) / (f1 - f0), 0, 1)))
    return x[:, :int(T.DURATION * SR)]


def shelf(x, f0, gain_db, kind="high", S=0.7):
    """RBJ shelving EQ."""
    A = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    cw, sw = np.cos(w0), np.sin(w0)
    al = sw / 2 * np.sqrt((A + 1 / A) * (1 / S - 1) + 2)
    sq = 2 * np.sqrt(A) * al
    if kind == "high":
        b = [A * ((A + 1) + (A - 1) * cw + sq), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - sq)]
        a = [(A + 1) - (A - 1) * cw + sq, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - sq]
    else:
        b = [A * ((A + 1) - (A - 1) * cw + sq), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - sq)]
        a = [(A + 1) + (A - 1) * cw + sq, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - sq]
    b = np.array(b) / a[0]
    a = np.array(a) / a[0]
    return signal.lfilter(b, a, x, axis=-1)


def write_wav(path, x):
    from scipy.io import wavfile
    y = np.clip(x.T, -1, 1)
    wavfile.write(path, SR, (y * 32767).astype(np.int16))


def build(path):
    stems = compose()
    mix = master(stems)
    write_wav(path, mix)
    return stems, mix


if __name__ == "__main__":
    import sys
    import time
    t0 = time.time()
    out = sys.argv[1] if len(sys.argv) > 1 else "soundtrack.wav"
    stems, mix = build(out)
    for k, v in stems.items():
        print(f"{k:6s} peak {20*np.log10(np.max(np.abs(v))+1e-9):6.1f} dB  rms {20*np.log10(np.sqrt(np.mean(v**2))+1e-9):6.1f} dB")
    print("master peak", 20 * np.log10(np.max(np.abs(mix))), "rms", 20 * np.log10(np.sqrt(np.mean(mix ** 2))))
    print(f"done in {time.time()-t0:.1f}s -> {out}")
