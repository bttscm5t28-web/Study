"""
synth.py -- a small procedural music synthesis toolkit (numpy + scipy only).

Aimed at a cinematic / minimal / premium promo score: warm detuned pads, a
clean deep sub, soft piano-like plucks, airy hats, a weighty impact with a
tail, risers and a lush, smooth reverb.

Design rules
------------
* Sample-accurate and deterministic.  Every stochastic element takes a
  ``seed``; all durations go through ``n_samples()`` (= round(dur * sr)) and
  every instrument returns an array whose length is exactly the documented
  value, so a BPM timeline can place events to the sample.
* Click-free.  Every instrument applies short raised-cosine fades at its ends.
* NaN-free.  Every public function sanitises its output; edge cases such as
  zero length, zero frequency or silence are handled explicitly.

Conventions
-----------
* ``SR = 48000`` by default.  Signals are float64 numpy arrays: mono as shape
  ``(n,)``, stereo as shape ``(n, 2)``.  Values are nominally in -1..1.
* ``freq`` arguments accept a scalar (Hz) or a per-sample array (Hz) for
  sweeps (an array of a different length is linearly resampled to fit).
* ``note`` arguments accept a note name (``'C3'``, ``'F#4'``, ``'Bb2'``), an
  ``int`` (MIDI number) or a ``float`` (Hz).
* Oscillator ``phase`` is in cycles (0..1).
* Effects take mono or stereo input; ``reverb``, ``delay``, ``chorus`` always
  return stereo.  Effect ``mix`` is an equal-power dry/wet crossfade.
"""
from __future__ import annotations

import math
import re
import struct
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy import signal as sps
from scipy.ndimage import minimum_filter1d

SR = 48000
TWO_PI = 2.0 * np.pi
_EPS = 1e-12
_FLOOR_DB = -80.0

__all__ = [
    "SR", "Track", "write_wav",
    "n_samples", "db2lin", "lin2db", "to_mono", "to_stereo", "sanitize", "fade",
    "declick", "pad_to", "pan_gains",
    "note_to_midi", "midi_to_hz", "midi_to_note", "hz",
    "sine", "saw", "triangle", "square", "noise",
    "adsr", "expdecay", "env", "swell",
    "lowpass", "highpass", "bandpass", "onepole_lp", "onepole_hp",
    "reverb", "delay", "chorus", "softclip", "saturate", "compress", "limiter",
    "measure_lufs", "normalize_lufs",
    "pad", "sub", "pluck", "keys", "kick", "impact", "hat", "snare", "clap",
    "tick", "riser", "downlifter", "shimmer",
    "Grid", "bpm_grid", "at_beat", "chord",
    "peak_dbfs", "rms_dbfs", "rms_per_bar", "analyze",
]


# ----------------------------------------------------------------------------
# Basic utilities
# ----------------------------------------------------------------------------
def n_samples(dur_s: float, sr: int = SR) -> int:
    """Number of samples for a duration (round(dur * sr), never negative)."""
    return max(0, int(round(float(dur_s) * sr)))


def db2lin(db):
    return np.power(10.0, np.asarray(db, dtype=np.float64) / 20.0)


def lin2db(x):
    return 20.0 * np.log10(np.maximum(np.abs(np.asarray(x, dtype=np.float64)), _EPS))


def sanitize(x):
    """Replace NaN/inf by 0 (in place when possible) and return the array."""
    x = np.asarray(x, dtype=np.float64)
    if not np.all(np.isfinite(x)):
        x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    return x


def to_stereo(x):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        return np.stack([x, x], axis=1)
    if x.ndim == 2 and x.shape[1] == 1:
        return np.repeat(x, 2, axis=1)
    return x


def to_mono(x):
    x = np.asarray(x, dtype=np.float64)
    return x if x.ndim == 1 else x.mean(axis=1)


def _col(e, x):
    """Broadcast a 1-D envelope against a mono or stereo signal."""
    return e[:, None] if x.ndim == 2 else e


def pad_to(x, n: int):
    """Zero-pad or truncate ``x`` along time to exactly ``n`` samples."""
    x = np.asarray(x, dtype=np.float64)
    n = max(0, int(n))
    if len(x) == n:
        return x
    if len(x) > n:
        return x[:n]
    shape = (n - len(x),) + x.shape[1:]
    return np.concatenate([x, np.zeros(shape)], axis=0)


def fade(x, in_ms: float = 3.0, out_ms: float = 3.0, sr: int = SR):
    """Raised-cosine fade in/out (returns a copy).  Safe for short signals."""
    x = np.array(x, dtype=np.float64, copy=True)
    n = len(x)
    if n == 0:
        return x
    n_in = min(n_samples(in_ms / 1000.0, sr), n)
    n_out = min(n_samples(out_ms / 1000.0, sr), n)
    if n_in > 1:
        w = 0.5 - 0.5 * np.cos(np.pi * np.arange(n_in) / n_in)
        x[:n_in] *= _col(w, x)
    if n_out > 1:
        w = 0.5 - 0.5 * np.cos(np.pi * np.arange(n_out) / n_out)[::-1]
        x[n - n_out:] *= _col(w, x)
    return x


declick = fade


def pan_gains(pan: float):
    """Equal-power pan law: pan -1..1 -> (gain_left, gain_right)."""
    p = float(np.clip(pan, -1.0, 1.0))
    th = (p + 1.0) * np.pi / 4.0
    return math.cos(th), math.sin(th)


def _balance_gains(pan: float):
    """Balance law for stereo material (centre = unity on both sides)."""
    p = float(np.clip(pan, -1.0, 1.0))
    return min(1.0, 1.0 - p), min(1.0, 1.0 + p)


def _rng(seed):
    return np.random.default_rng(None if seed is None else int(seed))


# ----------------------------------------------------------------------------
# Notes
# ----------------------------------------------------------------------------
_NOTE_RE = re.compile(r"^\s*([A-Ga-g])([#b♯♭]?)(-?\d+)\s*$")
_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def note_to_midi(name: str) -> int:
    """'C4' -> 60, 'A4' -> 69, 'F#3' -> 54, 'Bb2' -> 46."""
    m = _NOTE_RE.match(str(name))
    if not m:
        raise ValueError(f"bad note name: {name!r}")
    letter, acc, octave = m.groups()
    semi = _SEMITONES[letter.upper()]
    if acc in ("#", "♯"):
        semi += 1
    elif acc in ("b", "♭"):
        semi -= 1
    return 12 * (int(octave) + 1) + semi


def midi_to_hz(n):
    """MIDI note number (scalar or array) -> Hz (A4 = 440)."""
    return 440.0 * np.power(2.0, (np.asarray(n, dtype=np.float64) - 69.0) / 12.0)


def midi_to_note(n: int) -> str:
    n = int(round(n))
    return f"{_NAMES[n % 12]}{n // 12 - 1}"


def hz(note) -> float:
    """Note name / int MIDI number / float Hz -> frequency in Hz."""
    if isinstance(note, str):
        return float(midi_to_hz(note_to_midi(note)))
    if isinstance(note, (bool, np.bool_)):
        raise TypeError("note must be a name, MIDI int or Hz float")
    if isinstance(note, (int, np.integer)):
        return float(midi_to_hz(int(note)))
    return float(note)


# ----------------------------------------------------------------------------
# Oscillators
# ----------------------------------------------------------------------------
def _freq_array(freq, n: int, sr: int):
    """Per-sample frequency array of length n from a scalar or array."""
    if np.ndim(freq) == 0:
        return np.full(n, float(freq))
    f = np.asarray(freq, dtype=np.float64).ravel()
    if f.size == n:
        return f.copy()
    if f.size == 0 or n == 0:
        return np.zeros(n)
    if f.size == 1:
        return np.full(n, float(f[0]))
    return np.interp(np.linspace(0.0, 1.0, n), np.linspace(0.0, 1.0, f.size), f)


def _phase_cycles(freq, n: int, sr: int, phase0: float = 0.0):
    """Instantaneous phase in cycles; phase[k] = phase0 + sum_{j<k} f[j]/sr."""
    if np.ndim(freq) == 0:
        return phase0 + np.arange(n) * (float(freq) / sr)
    f = _freq_array(freq, n, sr)
    ph = np.cumsum(f)
    ph -= f
    return phase0 + ph / sr


def sine(freq, dur: float, sr: int = SR, phase: float = 0.0):
    """Sine oscillator.  ``freq`` scalar or per-sample array; ``phase`` in cycles."""
    n = n_samples(dur, sr)
    return np.sin(TWO_PI * _phase_cycles(freq, n, sr, phase))


def _polyblep(t, dt):
    """PolyBLEP residual for a unit step at phase 0 (t, dt in cycles)."""
    out = np.zeros_like(t)
    m = t < dt
    if m.any():
        tt = t[m] / dt[m]
        out[m] = tt + tt - tt * tt - 1.0
    m = t > 1.0 - dt
    if m.any():
        tt = (t[m] - 1.0) / dt[m]
        out[m] = tt * tt + tt + tt + 1.0
    return out


def _saw_polyblep(freq, n: int, sr: int, phase0: float):
    """PolyBLEP sawtooth (kept as an alternative engine; ~-45 dB aliasing)."""
    f = _freq_array(freq, n, sr)
    dt = np.clip(np.abs(f) / sr, 1e-7, 0.5)
    t = np.mod(_phase_cycles(f, n, sr, phase0), 1.0)
    return (2.0 * t - 1.0) - _polyblep(t, dt)


# --- band-limited mip-mapped wavetables -------------------------------------
# One table per third-octave band (top frequency f_top); the table for a band
# holds exactly the harmonics that stay below Nyquist at f_top, so a tone
# anywhere in the band never aliases and loses at most the harmonics above
# sr/2 / 2^(1/3) (~19 kHz at 48 kHz).  4-point Hermite interpolation on an
# 8192-point table keeps interpolation noise around -85 dB.
_TABLE_SIZE = 8192
_TABLE_F_LO = 20.0
_TABLES: dict = {}


def _build_tables(kind: str, sr: int):
    key = (kind, int(sr))
    if key in _TABLES:
        return _TABLES[key]
    tops, tables = [], []
    j = 0
    while True:
        f_top = _TABLE_F_LO * 2.0 ** (j / 3.0)
        K = int(math.floor(0.5 * sr / f_top))
        if K < 1:
            break
        K = min(K, _TABLE_SIZE // 2 - 1)
        k = np.arange(1, K + 1, dtype=np.float64)
        spec = np.zeros(_TABLE_SIZE // 2 + 1, dtype=np.complex128)
        if kind == "saw":            # ramp 2t-1 = -(2/pi) sum sin(2 pi k t)/k
            spec[1:K + 1] = 2j / (np.pi * k)
        elif kind == "triangle":     # odd harmonics, 1/k^2, alternating sign
            amp = np.where(k % 2 == 1, (8.0 / np.pi ** 2) * (-1.0) ** ((k - 1) // 2) / k ** 2, 0.0)
            spec[1:K + 1] = -1j * amp
        else:
            raise ValueError(kind)
        # irfft of a one-sided spectrum gives (2/N) Re(X[k] e^{i theta}); with
        # X[k] = -i A/2 ... scaled by N/2 this yields A sin(theta) per harmonic.
        tbl = np.fft.irfft(spec) * (_TABLE_SIZE / 2.0)
        tops.append(f_top)
        # pad with one sample before and two after so Hermite reads need no modulo
        tables.append(np.concatenate([tbl[-1:], tbl, tbl[:2]]))
        j += 1
    _TABLES[key] = (np.array(tops), tables)
    return _TABLES[key]


def _wavetable_osc(kind: str, freq, n: int, sr: int, phase0: float):
    """Read the band-limited table set with per-sample table selection and
    4-point Hermite interpolation.  ``freq`` scalar or per-sample array."""
    f = _freq_array(freq, n, sr)
    tops, tables = _build_tables(kind, sr)
    ph = np.mod(_phase_cycles(f, n, sr, phase0), 1.0) * _TABLE_SIZE
    i0 = np.floor(ph).astype(np.int64)
    fr = ph - i0
    i0 %= _TABLE_SIZE
    band = np.clip(np.searchsorted(tops, np.abs(f), side="left"), 0, len(tables) - 1)
    out = np.empty(n)
    bands = [int(band[0])] if np.ndim(freq) == 0 else np.unique(band)
    for j in bands:
        m = slice(None) if np.ndim(freq) == 0 else (band == j)
        tbl = tables[j]
        i = i0[m] + 1                      # +1: table is padded by one sample at the front
        u = fr[m]
        xm1 = tbl[i - 1]
        x0 = tbl[i]
        x1 = tbl[i + 1]
        x2 = tbl[i + 2]
        c1 = 0.5 * (x1 - xm1)
        c2 = xm1 - 2.5 * x0 + 2.0 * x1 - 0.5 * x2
        c3 = 0.5 * (x2 - xm1) + 1.5 * (x0 - x1)
        out[m] = ((c3 * u + c2) * u + c1) * u + x0
    return out


def _saw_core(freq, n: int, sr: int, phase0: float, method: str = "wavetable"):
    if method == "polyblep":
        return _saw_polyblep(freq, n, sr, phase0)
    return _wavetable_osc("saw", freq, n, sr, phase0)


def saw(freq, dur: float, detune_cents=None, voices: int = 1, sr: int = SR,
        phase=None, seed: int = 0, method: str = "wavetable"):
    """
    Band-limited sawtooth, optionally as a detuned unison stack.

    method       : 'wavetable' (default; mip-mapped band-limited tables with
                   Hermite interpolation, aliasing ~-85 dB, sweeps supported)
                   or 'polyblep' (2-point PolyBLEP, ~-45 dB).
    detune_cents : None, a scalar (symmetric spread of ``voices`` voices across
                   +-detune_cents) or an explicit list of per-voice offsets.
    phase        : None -> seeded random start phase per voice (cycles).
    The stack is scaled by 1/sqrt(voices) to keep the level roughly constant.
    Note: a band-limited ramp overshoots its +-1 corners by ~18 % (Gibbs), so
    a single saw peaks at ~1.18 while its RMS stays 0.577.
    """
    n = n_samples(dur, sr)
    if n == 0:
        return np.zeros(0)
    if detune_cents is None:
        cents = np.zeros(max(1, int(voices)))
        if voices > 1:
            cents = np.linspace(-10.0, 10.0, int(voices))
    elif np.ndim(detune_cents) == 0:
        v = max(1, int(voices))
        cents = np.linspace(-float(detune_cents), float(detune_cents), v) if v > 1 else np.zeros(1)
    else:
        cents = np.asarray(detune_cents, dtype=np.float64).ravel()
    v = len(cents)
    rng = _rng(seed)
    if phase is None:
        phases = rng.random(v)
    else:
        phases = np.broadcast_to(np.asarray(phase, dtype=np.float64), (v,))
    base = _freq_array(freq, n, sr)
    out = np.zeros(n)
    for c, ph in zip(cents, phases):
        out += _saw_core(base * (2.0 ** (c / 1200.0)), n, sr, float(ph), method)
    return sanitize(out / math.sqrt(v))


def square(freq, dur: float, pw: float = 0.5, sr: int = SR, phase: float = 0.0,
           method: str = "wavetable"):
    """Band-limited pulse wave with pulse width ``pw`` (0..1), built as the
    difference of two band-limited saws offset by ``pw`` cycles."""
    n = n_samples(dur, sr)
    if n == 0:
        return np.zeros(0)
    pw = float(np.clip(pw, 0.01, 0.99))
    f = _freq_array(freq, n, sr)
    y = _saw_core(f, n, sr, phase, method) - _saw_core(f, n, sr, phase + pw, method) + (2.0 * pw - 1.0)
    return sanitize(y)


def triangle(freq, dur: float, sr: int = SR, phase: float = 0.0):
    """Band-limited triangle (mip-mapped wavetable)."""
    n = n_samples(dur, sr)
    if n == 0:
        return np.zeros(0)
    return sanitize(_wavetable_osc("triangle", freq, n, sr, phase))


def noise(dur: float, color: str = "white", sr: int = SR, seed: int = 0):
    """Seeded noise.  color: 'white' (uniform in -1..1), 'pink' (-3 dB/oct) or
    'brown' (-6 dB/oct); coloured noise is peak-normalised to 1."""
    n = n_samples(dur, sr)
    if n == 0:
        return np.zeros(0)
    rng = _rng(seed)
    w = rng.uniform(-1.0, 1.0, n)
    if color == "white":
        return w
    if color == "pink":
        # Paul Kellet's "refined" pink filter: a bank of one-pole filters.
        taps = [(0.99886, 0.0555179), (0.99332, 0.0750759), (0.96900, 0.1538520),
                (0.86650, 0.3104856), (0.55000, 0.5329522), (-0.7616, -0.0168980)]
        p = w * 0.5362
        for a, c in taps:
            p += sps.lfilter([c], [1.0, -a], w)
        p[1:] += 0.115926 * w[:-1]
    elif color == "brown":
        p = sps.lfilter([1.0], [1.0, -0.999], w)
    else:
        raise ValueError(f"unknown noise colour {color!r}")
    return _norm_peak(p, 1.0)


# ----------------------------------------------------------------------------
# Envelopes
# ----------------------------------------------------------------------------
def _rc_up(u, k: float = 4.0):
    """0..1 -> 0..1, concave 'RC charge' shape (fast start, soft landing)."""
    return (1.0 - np.exp(-k * u)) / (1.0 - math.exp(-k))


def _rc_down(u, k: float = 5.5):
    """0..1 -> 1..0, exponential approach that lands exactly on 0 at u = 1."""
    return (np.exp(-k * u) - math.exp(-k)) / (1.0 - math.exp(-k))


def adsr(dur: float, a: float = 0.01, d: float = 0.1, s: float = 0.8, r: float = 0.3,
         curve: str = "exp", sr: int = SR):
    """
    ADSR envelope.  The gate is open for ``dur`` seconds, then releases for
    ``r`` seconds; the returned array has length n_samples(dur) + n_samples(r)
    and ends exactly at 0.  ``curve`` 'exp' uses analogue-style RC curves,
    'lin' straight lines.  Release starts from the level reached at gate-off.
    """
    n_on = n_samples(dur, sr)
    n_r = n_samples(r, sr)
    n = n_on + n_r
    if n == 0:
        return np.zeros(0)
    a = max(0.0, float(a)); d = max(0.0, float(d)); r = max(0.0, float(r))
    s = float(np.clip(s, 0.0, 1.0))
    exp_ = (curve == "exp")
    t = np.arange(n) / sr

    def on_level(tt):
        tt = np.asarray(tt, dtype=np.float64)
        ua = np.clip(tt / a, 0.0, 1.0) if a > 0 else np.ones_like(tt)
        att = _rc_up(ua) if exp_ else ua
        if d > 0:
            ud = np.clip((tt - a) / d, 0.0, 1.0)
            dec = s + (1.0 - s) * (_rc_down(ud) if exp_ else (1.0 - ud))
        else:
            dec = np.where(tt >= a, s, 1.0)
        return np.where(tt < a, att, dec)

    e = on_level(t)
    if n_r > 0:
        level_off = float(on_level(np.array([n_on / sr]))[0]) if n_on > 0 else 0.0
        ur = np.clip((t - n_on / sr) / r, 0.0, 1.0)
        rel = level_off * (_rc_down(ur) if exp_ else (1.0 - ur))
        e = np.where(np.arange(n) < n_on, e, rel)
        e[-1] = 0.0
    return sanitize(e)


def expdecay(dur: float, tau: float, sr: int = SR, fade_out_ms: float = 5.0):
    """exp(-t/tau) over ``dur`` seconds, with a short raised-cosine landing at 0."""
    n = n_samples(dur, sr)
    if n == 0:
        return np.zeros(0)
    tau = max(float(tau), 1e-6)
    e = np.exp(-np.arange(n) / (tau * sr))
    return fade(e, 0.0, fade_out_ms, sr)


def env(points: Sequence[tuple], curve: str = "lin", sr: int = SR):
    """
    Break-point envelope from ``[(t_s, value), ...]``.  Length = n_samples(t_last).
    'lin' interpolates linearly; 'exp' interpolates geometrically (linear in
    dB) with a -80 dB floor, which is the natural shape for decays.
    """
    pts = sorted((float(t), float(v)) for t, v in points)
    if not pts:
        return np.zeros(0)
    n = n_samples(pts[-1][0], sr)
    if n == 0:
        return np.zeros(0)
    t = np.arange(n) / sr
    out = np.full(n, pts[0][1])
    floor = db2lin(_FLOOR_DB)
    for (t0, v0), (t1, v1) in zip(pts[:-1], pts[1:]):
        if t1 <= t0:
            out[t >= t0] = v1
            continue
        m = (t >= t0) & (t < t1)
        u = (t[m] - t0) / (t1 - t0)
        if curve == "exp":
            a0 = max(abs(v0), floor); a1 = max(abs(v1), floor)
            seg = a0 * np.power(a1 / a0, u)
            if v0 < 0 or v1 < 0:
                seg = seg * np.sign(v0 if v0 != 0 else v1)
        else:
            seg = v0 + (v1 - v0) * u
        out[m] = seg
    if pts[-1][1] == 0.0 and n > 0:
        out[-1] = 0.0
    return sanitize(out)


def swell(x, dur: float | None = None, sr: int = SR, k: float = 3.0):
    """Exponential fade-in (slow start, fast finish) over ``dur`` seconds
    (default: the whole signal)."""
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    if n == 0:
        return x.copy()
    n_f = n if dur is None else min(n, max(1, n_samples(dur, sr)))
    u = np.clip(np.arange(n) / n_f, 0.0, 1.0)
    g = (np.exp(k * u) - 1.0) / (math.exp(k) - 1.0)
    return x * _col(g, x)


# ----------------------------------------------------------------------------
# Filters
# ----------------------------------------------------------------------------
def _rbj(kind: str, f0, q: float, sr: int, gain_db: float = 0.0):
    """RBJ cookbook biquad(s) as normalised SOS rows, vectorised over f0."""
    f0 = np.clip(np.asarray(f0, dtype=np.float64), 1.0, 0.49 * sr)
    q = max(float(q), 0.05)
    w0 = TWO_PI * f0 / sr
    cs, sn = np.cos(w0), np.sin(w0)
    alpha = sn / (2.0 * q)
    if kind == "lp":
        b0 = (1.0 - cs) / 2.0; b1 = 1.0 - cs; b2 = (1.0 - cs) / 2.0
        a0 = 1.0 + alpha; a1 = -2.0 * cs; a2 = 1.0 - alpha
    elif kind == "hp":
        b0 = (1.0 + cs) / 2.0; b1 = -(1.0 + cs); b2 = (1.0 + cs) / 2.0
        a0 = 1.0 + alpha; a1 = -2.0 * cs; a2 = 1.0 - alpha
    elif kind == "bp":  # constant 0 dB peak gain
        b0 = alpha; b1 = np.zeros_like(alpha); b2 = -alpha
        a0 = 1.0 + alpha; a1 = -2.0 * cs; a2 = 1.0 - alpha
    elif kind == "highshelf":
        A = 10.0 ** (gain_db / 40.0)
        sa = 2.0 * math.sqrt(A) * alpha
        b0 = A * ((A + 1) + (A - 1) * cs + sa)
        b1 = -2.0 * A * ((A - 1) + (A + 1) * cs)
        b2 = A * ((A + 1) + (A - 1) * cs - sa)
        a0 = (A + 1) - (A - 1) * cs + sa
        a1 = 2.0 * ((A - 1) - (A + 1) * cs)
        a2 = (A + 1) - (A - 1) * cs - sa
    else:
        raise ValueError(kind)
    sos = np.stack([b0 / a0, b1 / a0, b2 / a0, np.ones_like(a0), a1 / a0, a2 / a0], axis=-1)
    return np.atleast_2d(sos)


def _biquad(x, kind: str, cutoff, q: float, sr: int, block: int = 64):
    """Run one RBJ biquad; ``cutoff`` scalar, or array -> block-wise automation."""
    x = np.asarray(x, dtype=np.float64)
    n = len(x)
    if n == 0:
        return x.copy()
    if np.ndim(cutoff) == 0:
        return sps.sosfilt(_rbj(kind, float(cutoff), q, sr), x, axis=0)
    c = _freq_array(cutoff, n, sr)
    block = max(1, int(block))
    nb = (n + block - 1) // block
    centres = np.minimum(np.arange(nb) * block + block // 2, n - 1)
    sos_all = _rbj(kind, c[centres], q, sr)              # (nb, 6)
    zi = np.zeros((2,) + x.shape[1:])                     # DF2T state carried across blocks
    y = np.empty_like(x)
    for i in range(nb):
        s = i * block
        e = min(n, s + block)
        row = sos_all[i]
        y[s:e], zi = sps.lfilter(row[:3], row[3:], x[s:e], zi=zi, axis=0)
    return y


def lowpass(x, cutoff, q: float = 0.7071, sr: int = SR, block: int = 64, order: int = 2):
    """2-pole (or 4-pole, ``order=4``) resonant lowpass.  ``cutoff`` may be a
    per-sample array (processed in ``block``-sample blocks with state carried)."""
    y = _biquad(x, "lp", cutoff, q, sr, block)
    if order >= 4:
        y = _biquad(y, "lp", cutoff, q, sr, block)
    return sanitize(y)


def highpass(x, cutoff, q: float = 0.7071, sr: int = SR, block: int = 64, order: int = 2):
    y = _biquad(x, "hp", cutoff, q, sr, block)
    if order >= 4:
        y = _biquad(y, "hp", cutoff, q, sr, block)
    return sanitize(y)


def bandpass(x, center, q: float = 1.0, sr: int = SR, block: int = 64, order: int = 2):
    y = _biquad(x, "bp", center, q, sr, block)
    if order >= 4:
        y = _biquad(y, "bp", center, q, sr, block)
    return sanitize(y)


def onepole_lp(x, cutoff: float, sr: int = SR):
    """One-pole 6 dB/oct lowpass (gentle tone control, zero-DC-error)."""
    x = np.asarray(x, dtype=np.float64)
    if len(x) == 0:
        return x.copy()
    a = math.exp(-TWO_PI * float(np.clip(cutoff, 1.0, 0.49 * sr)) / sr)
    return sanitize(sps.lfilter([1.0 - a], [1.0, -a], x, axis=0))


def onepole_hp(x, cutoff: float, sr: int = SR):
    x = np.asarray(x, dtype=np.float64)
    return x - onepole_lp(x, cutoff, sr)


# ----------------------------------------------------------------------------
# Effects
# ----------------------------------------------------------------------------
def _xfade_gains(mix: float):
    m = float(np.clip(mix, 0.0, 1.0))
    return math.cos(m * np.pi / 2.0), math.sin(m * np.pi / 2.0)


def _allpass(x, D: int, g: float):
    """Schroeder allpass  H(z) = (-g + z^-D) / (1 - g z^-D)  (block-vectorised)."""
    n = len(x)
    w = np.zeros(n)
    y = np.zeros(n)
    for s in range(0, n, D):
        e = min(n, s + D)
        wd = w[s - D:e - D] if s >= D else np.zeros(e - s)
        w[s:e] = x[s:e] + g * wd
        y[s:e] = -g * x[s:e] + (1.0 - g * g) * wd
    return y


def _nearest_prime(n: int) -> int:
    n = max(2, int(n))

    def is_prime(k):
        if k < 2 or k % 2 == 0:
            return k == 2
        return all(k % d for d in range(3, int(math.isqrt(k)) + 1, 2))

    for off in range(0, 200):
        if is_prime(n + off):
            return n + off
        if is_prime(n - off):
            return n - off
    return n


def _hadamard(n: int):
    H = np.array([[1.0]])
    while H.shape[0] < n:
        H = np.block([[H, H], [H, -H]])
    return H / math.sqrt(n)


# 16 delay lengths at the 44.1 kHz reference (~25-82 ms), nudged to primes
# after scaling to the working rate.
_FDN_44K = (1103, 1217, 1327, 1453, 1597, 1733, 1879, 2039,
            2203, 2371, 2557, 2749, 2953, 3167, 3391, 3631)
_AP_44K = (556, 441)


def _fdn(inL, inR, lengths, gains, damp):
    """
    16-line feedback delay network with a Hadamard mixing matrix and a
    one-pole lowpass per line.  Even lines are fed from ``inL`` and summed to
    the left output, odd lines from/to the right.  Each line is a ring buffer
    processed in blocks of min(lengths) samples, so the whole network stays
    vectorised.  Returns (wetL, wetR) made of the delayed, filtered line
    outputs (no zero-delay copy of the input).
    """
    n = len(inL)
    N = len(lengths)
    H = _hadamard(N)
    chunk = int(min(lengths))
    bufs = [np.zeros(D) for D in lengths]
    zi = np.zeros((N, 1))
    b, a = [1.0 - damp], [1.0, -damp]
    F = np.zeros((chunk, N))
    outL = np.zeros(n)
    outR = np.zeros(n)
    for s in range(0, n, chunk):
        e = min(n, s + chunk)
        c = e - s
        idxs = []
        for i, D in enumerate(lengths):
            idx = (s + np.arange(c)) % D          # oldest c samples of the ring
            idxs.append(idx)
            f, zi[i] = sps.lfilter(b, a, bufs[i][idx], zi=zi[i])
            F[:c, i] = gains[i] * f
        outL[s:e] = F[:c, 0::2].sum(axis=1)
        outR[s:e] = F[:c, 1::2].sum(axis=1)
        mixed = F[:c] @ H
        for i, D in enumerate(lengths):
            src = inL[s:e] if i % 2 == 0 else inR[s:e]
            bufs[i][idxs[i]] = src + mixed[:, i]
    return outL, outR


def reverb(x, decay_s: float = 3.0, mix: float = 0.3, predelay_ms: float = 20.0,
           damping: float = 0.4, width: float = 1.0, size: float = 1.0,
           lowcut_hz: float = 120.0, highcut_hz: float = 9000.0,
           tail_s: float | None = None, sr: int = SR):
    """
    Lush, smooth stereo reverb: pre-delay -> 2 input diffusers -> a 16-line
    Hadamard feedback-delay network (one-pole damping per line, prime delay
    lengths 25-82 ms * ``size``) -> 2 output allpasses per channel.  Every
    line's feedback is derived from ``decay_s`` (RT60) so all modes decay at
    the same rate, and the dense orthogonal mixing keeps the tail Gaussian
    rather than metallic.  Left and right are taken from disjoint line sets
    (decorrelated, ``width`` scales the side signal).  Returns stereo of
    length len(x) + n_samples(tail_s); ``tail_s=None`` adds ~1.1 * decay_s,
    ``tail_s=0`` keeps the input length (bus use).  ``mix`` is equal-power.
    """
    x = to_stereo(sanitize(x))
    n_in = len(x)
    if n_in == 0:
        return np.zeros((0, 2))
    if tail_s is None:
        tail_s = 1.1 * max(decay_s, 0.05)
    n = n_in + n_samples(tail_s, sr)
    dry = pad_to(x, n)
    decay_s = max(float(decay_s), 0.02)
    damp = float(np.clip(0.2 + 0.6 * float(damping), 0.0, 0.95))
    scale = sr / 44100.0 * max(float(size), 0.2)
    spread = int(round(23 * sr / 44100.0))
    pre = n_samples(predelay_ms / 1000.0, sr)
    src = np.zeros((n, 2))
    if pre < n:
        src[pre:] = dry[:n - pre]
    # mild cross-feed so a hard-panned source still excites both sides
    inL = 0.8 * src[:, 0] + 0.2 * src[:, 1]
    inR = 0.8 * src[:, 1] + 0.2 * src[:, 0]
    inL = _allpass(_allpass(inL, int(round(211 * scale)), 0.65), int(round(331 * scale)), 0.6)
    inR = _allpass(_allpass(inR, int(round(211 * scale)) + spread, 0.65),
                   int(round(331 * scale)) + spread, 0.6)
    lengths = [_nearest_prime(int(round(D * scale))) for D in _FDN_44K]
    gains = [min(0.9995, 10.0 ** (-3.0 * D / (decay_s * sr))) for D in lengths]
    wetL, wetR = _fdn(inL, inR, lengths, gains, damp)
    for A44 in _AP_44K:
        wetL = _allpass(wetL, int(round(A44 * scale)), 0.5)
        wetR = _allpass(wetR, int(round(A44 * scale)) + spread, 0.5)
    wet = np.stack([wetL, wetR], axis=1)
    # level: steady-state power of the network for noise input is about
    # 0.5 * sum_i 1/(1-g_i^2) per side; normalise so wet RMS ~ dry RMS.
    # (the factor 3.0 is an empirical correction, measured with white noise,
    # for the damping/mixing losses the simple formula ignores)
    norm = 0.5 * sum(1.0 / max(1.0 - g * g, 1e-4) for g in gains)
    wet *= 3.0 / math.sqrt(max(norm, 1.0))
    if lowcut_hz > 0:
        wet = highpass(wet, lowcut_hz, 0.7071, sr)
    if highcut_hz > 0:
        wet = lowpass(wet, highcut_hz, 0.5, sr)
    if width != 1.0:
        mid = 0.5 * (wet[:, 0] + wet[:, 1])
        side = 0.5 * (wet[:, 0] - wet[:, 1]) * float(width)
        wet = np.stack([mid + side, mid - side], axis=1)
    wet = fade(wet, 0.0, 30.0, sr)
    gd, gw = _xfade_gains(mix)
    return sanitize(gd * dry + gw * wet)


def delay(x, time_s: float = 0.375, feedback: float = 0.4, mix: float = 0.3,
          ping_pong: bool = True, damping_hz: float = 4500.0,
          tail_s: float | None = None, sr: int = SR):
    """
    Feedback delay with a one-pole lowpass in the loop.  Ping-pong bounces a
    mono sum L -> R -> L.  Returns stereo; ``tail_s=None`` adds enough tail
    for the repeats to fall below -60 dB (capped at 24 repeats).
    """
    x = to_stereo(sanitize(x))
    n_in = len(x)
    if n_in == 0:
        return np.zeros((0, 2))
    D = max(1, n_samples(time_s, sr))
    fb = float(np.clip(feedback, 0.0, 0.98))
    if tail_s is None:
        k = 1 if fb <= 0.0 else min(24, int(math.ceil(-3.0 / math.log10(fb))))
        tail_s = (k + 1) * D / sr
    n = n_in + n_samples(tail_s, sr)
    if n == 0:
        return np.zeros((0, 2))
    dry = pad_to(x, n)
    a = math.exp(-TWO_PI * float(np.clip(damping_hz, 20.0, 0.49 * sr)) / sr)
    b, aa = [1.0 - a], [1.0, -a]
    wet = np.zeros((n, 2))
    zi = [np.zeros(1), np.zeros(1)]
    mono = 0.5 * (dry[:, 0] + dry[:, 1])
    for s in range(0, n, D):
        e = min(n, s + D)
        if s >= D:
            prevL, prevR, src = wet[s - D:e - D, 0], wet[s - D:e - D, 1], dry[s - D:e - D]
            srcM = mono[s - D:e - D]
        else:
            prevL = prevR = srcM = np.zeros(e - s)
            src = np.zeros((e - s, 2))
        if ping_pong:
            l_in = srcM + fb * prevR
            r_in = fb * prevL
        else:
            l_in = src[:, 0] + fb * prevL
            r_in = src[:, 1] + fb * prevR
        wet[s:e, 0], zi[0] = sps.lfilter(b, aa, l_in, zi=zi[0])
        wet[s:e, 1], zi[1] = sps.lfilter(b, aa, r_in, zi=zi[1])
    wet = fade(wet, 0.0, 20.0, sr)
    gd, gw = _xfade_gains(mix)
    return sanitize(gd * dry + gw * wet)


def chorus(x, rate: float = 0.3, depth_ms: float = 3.0, mix: float = 0.4,
           voices: int = 2, base_ms: float = 12.0, sr: int = SR):
    """
    Stereo chorus: ``voices`` modulated delay taps (linear interpolation),
    LFO phases spread per voice and offset 90 degrees between L and R for
    width.  Returns stereo of the input length.
    """
    x = to_stereo(sanitize(x))
    n = len(x)
    if n == 0:
        return np.zeros((0, 2))
    voices = max(1, int(voices))
    t = np.arange(n) / sr
    pad = int(math.ceil((base_ms + depth_ms) * sr / 1000.0)) + 2
    xp = np.concatenate([np.zeros((pad, 2)), x], axis=0)
    idx = np.arange(n) + pad
    wet = np.zeros((n, 2))
    for v in range(voices):
        r = rate * (1.0 + 0.13 * v)
        for ch in range(2):
            ph = v / voices + 0.25 * ch
            d = (base_ms + depth_ms * np.sin(TWO_PI * (r * t + ph))) * sr / 1000.0
            pos = idx - d
            i = np.floor(pos).astype(np.int64)
            fr = pos - i
            i = np.clip(i, 0, n + pad - 2)
            wet[:, ch] += (1.0 - fr) * xp[i, ch] + fr * xp[i + 1, ch]
    wet /= voices
    gd, gw = _xfade_gains(mix)
    return sanitize(gd * x + gw * wet)


def softclip(x, drive: float = 1.0):
    """tanh saturation normalised to unity small-signal gain:
    y = tanh(drive * x) / drive.  Peaks are softly limited to tanh(drive)/drive."""
    x = sanitize(x)
    d = max(float(drive), 1e-4)
    return np.tanh(d * x) / d


def saturate(x, drive: float = 2.0, mix: float = 1.0):
    """tanh saturation with make-up so that |x| = 1 maps to 1; ``mix`` blends."""
    x = sanitize(x)
    d = max(float(drive), 1e-4)
    y = np.tanh(d * x) / math.tanh(d)
    m = float(np.clip(mix, 0.0, 1.0))
    return (1.0 - m) * x + m * y


def compress(x, threshold_db: float = -18.0, ratio: float = 3.0, attack_ms: float = 10.0,
             release_ms: float = 120.0, knee_db: float = 6.0, makeup_db: float = 0.0,
             rms_ms: float = 8.0, sr: int = SR, hop: int = 16):
    """
    Feed-forward RMS compressor (stereo-linked, soft knee).  Level detection
    is a one-pole RMS; attack/release ballistics run at a control rate of
    ``hop`` samples and are linearly interpolated back to audio rate.
    """
    x = sanitize(x)
    n = len(x)
    if n == 0:
        return x.copy()
    det = x * x if x.ndim == 1 else np.mean(x * x, axis=1)
    a = math.exp(-1.0 / max(rms_ms * 1e-3 * sr, 1.0))
    ms = sps.lfilter([1.0 - a], [1.0, -a], det)
    level_db = 10.0 * np.log10(ms + 1e-12)
    over = level_db - threshold_db
    slope = (1.0 / max(ratio, 1.0)) - 1.0
    w = max(knee_db, 1e-6) / 2.0
    gr = np.where(over > w, slope * over, 0.0)
    knee = (over > -w) & (over <= w)
    gr[knee] = slope * (over[knee] + w) ** 2 / (4.0 * w)
    hop = max(1, int(hop))
    nb = (n + hop - 1) // hop
    ctrl = pad_to(gr, nb * hop).reshape(nb, hop).min(axis=1)
    att = math.exp(-hop / max(attack_ms * 1e-3 * sr, 1.0))
    rel = math.exp(-hop / max(release_ms * 1e-3 * sr, 1.0))
    sm = np.empty(nb)
    s = 0.0
    for i in range(nb):
        v = ctrl[i]
        c = att if v < s else rel
        s = v + c * (s - v)
        sm[i] = s
    g_db = np.interp(np.arange(n), np.arange(nb) * hop + hop / 2.0, sm)
    gain = db2lin(g_db + makeup_db)
    return sanitize(x * _col(gain, x))


def limiter(x, ceiling_db: float = -1.0, lookahead_ms: float = 5.0,
            release_ms: float = 80.0, sr: int = SR):
    """
    Look-ahead brick-wall peak limiter (stereo-linked).  The gain curve is the
    sliding minimum of the required gain over the look-ahead window, smoothed
    by a moving average of the same length (guaranteeing no overshoot) and
    then held by a linear-in-dB release.  Output never exceeds the ceiling.
    """
    x = sanitize(x)
    n = len(x)
    if n == 0:
        return x.copy()
    ceiling = float(db2lin(ceiling_db))
    peak = np.abs(x) if x.ndim == 1 else np.max(np.abs(x), axis=1)
    req = np.minimum(1.0, ceiling / np.maximum(peak, 1e-9))
    L = max(2, n_samples(lookahead_ms / 1000.0, sr))
    m = minimum_filter1d(req, size=L, origin=-(L // 2), mode="nearest")
    cs = np.cumsum(np.concatenate([np.full(L - 1, m[0]), m]))
    avg = (cs[L - 1:] - np.concatenate([[0.0], cs[:-L]])) / L
    avg = np.minimum(avg, m)  # guard against rounding
    g_db = 20.0 * np.log10(np.maximum(avg, 1e-9))
    rel_samples = max(1.0, release_ms * 1e-3 * sr)
    slope = 12.0 / rel_samples  # dB per sample (12 dB recovers in release_ms)
    step = 1
    while step < n:
        g_db[step:] = np.minimum(g_db[step:], g_db[:-step] + slope * step)
        step *= 2
    gain = db2lin(np.minimum(g_db, 0.0))
    y = x * _col(gain, x)
    return sanitize(np.clip(y, -ceiling, ceiling))


# ----------------------------------------------------------------------------
# Loudness (ITU-R BS.1770 K-weighting, gated)
# ----------------------------------------------------------------------------
def _k_weighting_sos(sr: int):
    # Stage 1: high shelf (+4 dB), Stage 2: highpass.  Pre-warped design that
    # reproduces the ITU coefficients exactly at 48 kHz.
    f0, G, Q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    K = math.tan(math.pi * f0 / sr)
    Vh = 10.0 ** (G / 20.0)
    Vb = Vh ** 0.4996667741545416
    a0 = 1.0 + K / Q + K * K
    s1 = [(Vh + Vb * K / Q + K * K) / a0, 2.0 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0,
          1.0, 2.0 * (K * K - 1.0) / a0, (1.0 - K / Q + K * K) / a0]
    f0, Q = 38.13547087602444, 0.5003270373238773
    K = math.tan(math.pi * f0 / sr)
    a0 = 1.0 + K / Q + K * K
    s2 = [1.0, -2.0, 1.0, 1.0, 2.0 * (K * K - 1.0) / a0, (1.0 - K / Q + K * K) / a0]
    return np.array([s1, s2])


def measure_lufs(x, sr: int = SR) -> float:
    """Integrated loudness (LUFS) per ITU-R BS.1770-4 with absolute (-70) and
    relative (-10 LU) gating.  Returns -inf for silence."""
    x = to_stereo(sanitize(x))
    n = len(x)
    if n == 0:
        return float("-inf")
    y = sps.sosfilt(_k_weighting_sos(sr), x, axis=0)
    blk = n_samples(0.4, sr)
    hop = n_samples(0.1, sr)
    if n < blk:
        y = pad_to(y, blk)
        n = blk
    nb = 1 + (n - blk) // hop
    cs = np.concatenate([np.zeros((1, 2)), np.cumsum(y * y, axis=0)], axis=0)
    starts = np.arange(nb) * hop
    z = (cs[starts + blk] - cs[starts]) / blk            # (nb, 2) mean square
    zs = z.sum(axis=1)
    lk = -0.691 + 10.0 * np.log10(np.maximum(zs, 1e-30))
    keep = lk > -70.0
    if not keep.any():
        return float("-inf")
    rel_thr = -0.691 + 10.0 * np.log10(np.mean(zs[keep])) - 10.0
    keep &= lk > rel_thr
    if not keep.any():
        return float("-inf")
    return float(-0.691 + 10.0 * np.log10(np.mean(zs[keep])))


def normalize_lufs(x, target: float = -14.0, sr: int = SR):
    """Scale ``x`` to ``target`` LUFS.  Returns ``(y, measured_before)``."""
    x = sanitize(x)
    measured = measure_lufs(x, sr)
    if not np.isfinite(measured):
        return x.copy(), measured
    gain = float(db2lin(target - measured))
    return x * gain, measured


# ----------------------------------------------------------------------------
# Instruments
# ----------------------------------------------------------------------------
def _norm_peak(x, peak: float = 0.9):
    x = sanitize(x)
    p = float(np.max(np.abs(x))) if x.size else 0.0
    return x * (peak / p) if p > _EPS else x


def pad(notes, dur: float, sr: int = SR, brightness: float = 0.5, attack: float = 1.5,
        release: float = 2.5, voices: int = 5, detune: float = 14.0, width: float = 0.8,
        sub_octave: float = 0.15, chorus_mix: float = 0.35, seed: int = 0):
    """
    Warm, wide pad.  Per note: ``voices`` PolyBLEP saws spread over
    +-``detune`` cents and across the stereo field, plus a centre triangle for
    body and a quiet sub-octave sine; the stack goes through a slowly opening
    resonant 4-pole lowpass (range set by ``brightness`` 0..1), a slow ADSR
    and a subtle chorus; peak-normalised to 0.7.  Returns stereo of length
    n_samples(dur) + n_samples(release).
    """
    notes = [notes] if isinstance(notes, (str, int, float)) else list(notes)
    n_on = n_samples(dur, sr)
    n = n_on + n_samples(release, sr)
    if n == 0 or not notes:
        return np.zeros((n, 2))
    rng = _rng(seed)
    voices = max(1, int(voices))
    cents = np.linspace(-detune, detune, voices) if voices > 1 else np.zeros(1)
    pans = np.linspace(-width, width, voices) if voices > 1 else np.zeros(1)
    out = np.zeros((n, 2))
    for note in notes:
        f = hz(note)
        order = rng.permutation(voices)
        layer = np.zeros((n, 2))
        for i in range(voices):
            v = _saw_core(f * 2.0 ** (cents[i] / 1200.0), n, sr, float(rng.random()))
            gl, gr = pan_gains(pans[order[i]])
            layer[:, 0] += gl * v
            layer[:, 1] += gr * v
        layer /= math.sqrt(voices)
        tri = triangle(f, n / sr, sr, float(rng.random()))
        layer += 0.45 * tri[:n, None]
        if sub_octave > 0 and f / 2.0 >= 28.0:
            layer += sub_octave * sine(f / 2.0, n / sr, sr)[:n, None]
        out += layer
    out /= math.sqrt(len(notes))
    # slowly opening filter, closing a little during the release
    b = float(np.clip(brightness, 0.0, 1.0))
    c_lo = 180.0 + 320.0 * b
    c_hi = 700.0 + 7000.0 * b ** 1.6
    t = np.arange(n) / sr
    open_ = _rc_up(np.clip(t / max(attack * 1.3, 0.01), 0.0, 1.0), 3.0)
    close = 1.0 - 0.5 * np.clip((t - n_on / sr) / max(release, 0.01), 0.0, 1.0)
    cutoff = (c_lo + (c_hi - c_lo) * open_) * close
    out = lowpass(out, cutoff, 0.9, sr)
    out = lowpass(out, cutoff * 1.8, 0.55, sr)
    e = adsr(dur, attack, 0.6, 0.85, release, "exp", sr)
    out *= e[:n, None]
    out = chorus(out, 0.22, 3.0, chorus_mix, 2, 12.0, sr)
    out = highpass(out, 40.0, 0.7071, sr)
    return sanitize(fade(_norm_peak(out, 0.7), 5.0, 10.0, sr))


def sub(note, dur: float, sr: int = SR, attack: float = 0.012, release: float = 0.35,
        harmonic2: float = 0.12):
    """Clean sub bass: sine + a little 2nd harmonic, soft attack, exp release.
    Length n_samples(dur) + n_samples(release)."""
    f = hz(note)
    n_on = n_samples(dur, sr)
    n = n_on + n_samples(release, sr)
    if n == 0:
        return np.zeros(0)
    total = n / sr
    y = (sine(f, total, sr) + harmonic2 * sine(2.0 * f, total, sr)) / (1.0 + abs(harmonic2))
    y = y[:n] * adsr(dur, attack, 0.0, 1.0, release, "exp", sr)[:n]
    return sanitize(fade(y, 2.0, 3.0, sr))


def _ks_loop(exc, D: int, b: float, c: float, g: float):
    """Karplus-Strong loop: delay D + 2-tap lowpass [1-b, b] + 1st-order
    allpass (fractional tuning) + gain g.  Block-vectorised."""
    n = len(exc)
    y = np.zeros(n)
    zf = np.zeros(1)
    za = np.zeros(1)
    for s in range(0, n, D):
        e = min(n, s + D)
        delayed = y[s - D:e - D] if s >= D else np.zeros(e - s)
        f, zf = sps.lfilter([1.0 - b, b], [1.0], delayed, zi=zf)
        h, za = sps.lfilter([c, 1.0], [1.0, c], f, zi=za)
        y[s:e] = exc[s:e] + g * h
    return y


def pluck(note, dur: float, tone: float = 0.5, sr: int = SR, seed: int = 0,
          body: float = 0.35, hammer: float = 0.25):
    """
    Soft piano-like pluck: a Karplus-Strong string (lowpassed noise burst
    excitation, fractional-delay tuned loop) layered with a decaying sine
    'body' at the fundamental and a short lowpassed hammer thump.
    ``tone`` 0..1 darker..brighter.  Length n_samples(dur); peak-normalised.
    """
    f = max(hz(note), 20.0)
    n = n_samples(dur, sr)
    if n == 0:
        return np.zeros(0)
    tone = float(np.clip(tone, 0.0, 1.0))
    rng = _rng(seed)
    T = sr / f
    # excitation: ~one period of windowed noise, lowpassed by tone
    L = int(np.clip(round(T), 8, n))
    exc = np.zeros(n)
    exc[:L] = rng.uniform(-1.0, 1.0, L) * np.hanning(L)
    exc = lowpass(exc, 900.0 + 7000.0 * tone, 0.7071, sr)
    # loop filter + fractional allpass tuning
    b = 0.5 * (1.0 - 0.6 * tone)
    Dint = int(math.floor(T - b - 0.5))
    if Dint < 2:
        Dint = 2
    delta = T - Dint - b
    c = (1.0 - delta) / (1.0 + delta)
    g = min(0.9999, 10.0 ** (-3.0 * T / (0.85 * dur * sr)))
    string = _ks_loop(exc, Dint, b, c, g)
    string = _norm_peak(string, 1.0)
    t = np.arange(n) / sr
    body_sig = np.sin(TWO_PI * f * t) * np.exp(-t / max(dur * 0.22, 0.02))
    hm = rng.uniform(-1.0, 1.0, n) * np.exp(-t / 0.0025)
    hm = lowpass(hm, 2200.0, 0.7071, sr)
    y = string + body * body_sig + hammer * 0.6 * hm
    y = lowpass(y, 3500.0 + 9000.0 * tone, 0.6, sr)
    y = _norm_peak(y, 0.85) * expdecay(dur, max(dur, 0.01) * 10.0, sr, 20.0)
    return sanitize(fade(y, 2.0, 15.0, sr))


def keys(note, dur: float, sr: int = SR, velocity: float = 0.8, release: float = 0.4,
         tine: float = 0.3):
    """Electric-piano tone: 2-operator FM (1:1 ratio) whose modulation index
    decays over the note, plus a fast-decaying 'tine' partial.  Length
    n_samples(dur) + n_samples(release)."""
    f = hz(note)
    n_on = n_samples(dur, sr)
    n = n_on + n_samples(release, sr)
    if n == 0:
        return np.zeros(0)
    vel = float(np.clip(velocity, 0.0, 1.0))
    t = np.arange(n) / sr
    index = 0.15 + (0.5 + 2.2 * vel) * np.exp(-t / max(dur * 0.35, 0.05))
    mod = np.sin(TWO_PI * f * t) * index
    car = np.sin(TWO_PI * f * t + mod)
    y = car
    if tine > 0 and 14.0 * f < 0.45 * sr:
        y = y + tine * 0.25 * np.sin(TWO_PI * 14.0 * f * t) * np.exp(-t / 0.06)
    amp = adsr(dur, 0.004, max(dur * 0.6, 0.05), 0.3, release, "exp", sr)[:n]
    y = y * amp * (0.3 + 0.7 * vel)
    y = onepole_lp(y, 7000.0, sr)
    return sanitize(fade(y, 2.0, 5.0, sr))


def kick(dur: float = 1.0, pitch_start: float = 150.0, pitch_end: float = 45.0,
         click: float = 0.3, sr: int = SR, seed: int = 0, drive: float = 1.6):
    """Cinematic kick: exponential sine pitch sweep with tanh weight, plus a
    short bandpassed noise click.  Length n_samples(dur)."""
    n = n_samples(dur, sr)
    if n == 0:
        return np.zeros(0)
    t = np.arange(n) / sr
    f = pitch_end + (pitch_start - pitch_end) * np.exp(-t / 0.045)
    body = np.sin(TWO_PI * _phase_cycles(f, n, sr, 0.0))
    amp = np.exp(-t / max(dur * 0.28, 0.01)) * _rc_up(np.clip(t / 0.0015, 0.0, 1.0))
    body = np.tanh(drive * body * amp) / math.tanh(drive)
    y = body * 0.95
    if click > 0:
        rng = _rng(seed)
        cl = rng.uniform(-1.0, 1.0, n) * np.exp(-t / 0.002)
        cl = bandpass(cl, 2500.0, 1.0, sr)
        y = y + click * 0.6 * cl
    return sanitize(fade(_norm_peak(y, 0.95), 0.5, 15.0, sr))


def impact(dur: float = 3.0, sr: int = SR, seed: int = 0, reverb_mix: float = 0.5,
           boom_hz: float = 40.0):
    """
    The big cinematic hit: kick + lowpass-swept noise burst + HF crack, sent
    through a large reverb, layered with a dry sub boom.  Returns stereo of
    length n_samples(dur).
    """
    n = n_samples(dur, sr)
    if n == 0:
        return np.zeros((0, 2))
    t = np.arange(n) / sr
    rng = _rng(seed)
    k = pad_to(kick(min(1.2, dur), 210.0, 38.0, 0.5, sr, seed), n)
    nz_len = min(dur, 1.4)
    nz = noise(nz_len, "white", sr, seed + 1)
    tt = np.arange(len(nz)) / sr
    cut = 150.0 + 4500.0 * np.exp(-tt / 0.22)
    nz = lowpass(nz, cut, 0.8, sr, order=4) * np.exp(-tt / 0.28) * _rc_up(np.clip(tt / 0.003, 0, 1))
    nz = pad_to(nz, n)
    crack = rng.uniform(-1.0, 1.0, n) * np.exp(-t / 0.06)
    crack = highpass(crack, 2500.0, 0.7071, sr) * 0.25
    boom_f = boom_hz * (1.0 + 0.6 * np.exp(-t / 0.25))
    boom = np.sin(TWO_PI * _phase_cycles(boom_f, n, sr, 0.0))
    boom += 0.15 * np.sin(2.0 * TWO_PI * _phase_cycles(boom_f, n, sr, 0.0))
    boom *= np.exp(-t / max(dur * 0.3, 0.05)) * _rc_up(np.clip(t / 0.006, 0, 1))
    layered = 1.0 * k + 0.9 * nz + crack
    wet = reverb(layered, 2.8, reverb_mix, 8.0, 0.5, 1.0, 1.0, 100.0, 7000.0, 0.0, sr)
    out = wet + 0.9 * boom[:, None]
    out = softclip(out, 1.3)
    return sanitize(fade(_norm_peak(out, 0.95), 0.5, 120.0, sr))


def hat(dur: float = 0.08, open: bool = False, sr: int = SR, seed: int = 0, tone: float = 0.5):
    """Airy hi-hat: highpassed white noise with a fast exponential decay."""
    n = n_samples(dur, sr)
    if n == 0:
        return np.zeros(0)
    t = np.arange(n) / sr
    w = noise(dur, "white", sr, seed)
    y = highpass(w, 5500.0 + 3000.0 * tone, 0.7071, sr, order=4)
    y = lowpass(y, 15000.0, 0.7071, sr)
    tau = dur / (2.5 if open else 4.5)
    y *= np.exp(-t / max(tau, 1e-3)) * _rc_up(np.clip(t / 0.0006, 0, 1))
    return sanitize(fade(_norm_peak(y, 0.8), 0.3, 5.0, sr))


def snare(dur: float = 0.25, sr: int = SR, seed: int = 0):
    """Soft snare: bandpassed noise + a short pitched body."""
    n = n_samples(dur, sr)
    if n == 0:
        return np.zeros(0)
    t = np.arange(n) / sr
    w = noise(dur, "white", sr, seed)
    nz = highpass(bandpass(w, 1800.0, 0.6, sr), 400.0, 0.7071, sr) * np.exp(-t / (dur / 4.0))
    fb = 160.0 + 80.0 * np.exp(-t / 0.03)
    body = np.sin(TWO_PI * _phase_cycles(fb, n, sr, 0.0)) * np.exp(-t / 0.06)
    y = saturate(nz * 1.2 + 0.7 * body, 1.5, 0.6)
    return sanitize(fade(_norm_peak(y, 0.9), 0.3, 8.0, sr))


def clap(dur: float = 0.3, sr: int = SR, seed: int = 0):
    """Clap: three micro bursts 10 ms apart followed by a decaying tail."""
    n = n_samples(dur, sr)
    if n == 0:
        return np.zeros(0)
    t = np.arange(n) / sr
    w = bandpass(noise(dur, "white", sr, seed), 1500.0, 0.8, sr)
    e = np.zeros(n)
    for k in range(3):
        tk = t - 0.010 * k
        e += np.where(tk >= 0, np.exp(-tk / 0.006), 0.0)
    tk = t - 0.030
    e += np.where(tk >= 0, 0.9 * np.exp(-tk / (dur / 4.0)), 0.0)
    y = w * e
    return sanitize(fade(_norm_peak(y, 0.9), 0.3, 8.0, sr))


def tick(dur: float = 0.03, sr: int = SR, seed: int = 0, freq: float = 2400.0):
    """Tiny click for subtle rhythmic pulses."""
    n = n_samples(dur, sr)
    if n == 0:
        return np.zeros(0)
    t = np.arange(n) / sr
    y = np.sin(TWO_PI * freq * t) * np.exp(-t / 0.004)
    y += 0.5 * bandpass(noise(dur, "white", sr, seed), 5000.0, 1.0, sr) * np.exp(-t / 0.002)
    return sanitize(fade(_norm_peak(y, 0.8), 0.3, 3.0, sr))


def riser(dur: float, start_hz: float = 200.0, end_hz: float = 4000.0, sr: int = SR,
          seed: int = 0, note="A2", noise_mix: float = 0.6, curve: float = 2.0):
    """
    Riser: white noise + 5-voice saw sweeping up two octaves, through a
    resonant lowpass whose cutoff sweeps exponentially start_hz -> end_hz,
    with amplitude rising as u**curve so the peak lands on the last sample.
    Length exactly n_samples(dur).
    """
    n = n_samples(dur, sr)
    if n == 0:
        return np.zeros(0)
    u = np.arange(n) / max(n - 1, 1)
    cutoff = start_hz * (end_hz / start_hz) ** u
    nz = noise(dur, "white", sr, seed)
    nz = highpass(lowpass(nz, cutoff, 1.4, sr), 120.0, 0.7071, sr)
    f0 = hz(note)
    fsweep = f0 * 4.0 ** u
    sw = saw(fsweep, dur, [-12.0, -6.0, 0.0, 6.0, 12.0], sr=sr, seed=seed)
    sw = lowpass(sw, cutoff, 1.0, sr)
    amp = 0.03 + 0.97 * u ** max(curve, 0.1)
    y = (noise_mix * nz + (1.0 - noise_mix) * sw) * amp
    return sanitize(fade(_norm_peak(y, 0.9), 2.0, 1.0, sr))


def downlifter(dur: float = 2.0, start_hz: float = 6000.0, end_hz: float = 150.0,
               sr: int = SR, seed: int = 0, note="A3"):
    """Falling counterpart of ``riser``: cutoff and pitch sweep down while the
    amplitude decays.  Length n_samples(dur)."""
    n = n_samples(dur, sr)
    if n == 0:
        return np.zeros(0)
    u = np.arange(n) / max(n - 1, 1)
    cutoff = start_hz * (end_hz / start_hz) ** u
    nz = lowpass(noise(dur, "white", sr, seed), cutoff, 1.2, sr)
    fsweep = hz(note) * 0.25 ** u
    sw = lowpass(saw(fsweep, dur, [-10.0, 0.0, 10.0], sr=sr, seed=seed), cutoff, 0.9, sr)
    amp = np.exp(-u * 3.0) * _rc_up(np.clip(u * n / (0.01 * sr), 0, 1))
    y = (0.6 * nz + 0.4 * sw) * amp
    return sanitize(fade(_norm_peak(y, 0.9), 2.0, 20.0, sr))


def shimmer(dur: float, notes=("E5", "B5", "E6"), sr: int = SR, brightness: float = 0.6,
            seed: int = 0, release: float = 3.0):
    """High, airy pad for endings: a bright, highpassed pad with slow tremolo
    and a long reverb.  Returns stereo, length n_samples(dur) + n_samples(release)."""
    n = n_samples(dur, sr) + n_samples(release, sr)
    if n == 0:
        return np.zeros((0, 2))
    p = pad(list(notes), dur, sr, brightness, min(2.0, max(dur * 0.45, 0.05)), release,
            voices=4, detune=9.0, width=1.0, sub_octave=0.0, chorus_mix=0.5, seed=seed)
    p = highpass(p, 600.0, 0.7071, sr)
    t = np.arange(len(p)) / sr
    trem = 1.0 - 0.18 * (0.5 - 0.5 * np.cos(TWO_PI * 0.17 * t))
    p *= trem[:, None]
    out = reverb(p, 5.0, 0.55, 30.0, 0.5, 1.0, 1.0, 300.0, 11000.0, 0.0, sr)
    return sanitize(fade(_norm_peak(out, 0.6), 5.0, 30.0, sr))


# ----------------------------------------------------------------------------
# Sequencing helpers
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Grid:
    bpm: float
    beats_per_bar: int = 4

    @property
    def beat_s(self) -> float:
        return 60.0 / self.bpm

    @property
    def bar_s(self) -> float:
        return self.beat_s * self.beats_per_bar

    def at_beat(self, b: float) -> float:
        return b * self.beat_s

    def at_bar(self, bar: float, beat: float = 0.0) -> float:
        return bar * self.bar_s + beat * self.beat_s

    def __iter__(self):
        yield self.beat_s
        yield self.bar_s


def bpm_grid(bpm: float, beats_per_bar: int = 4) -> Grid:
    """``beat_s, bar_s = bpm_grid(90)`` also works (the Grid is iterable)."""
    return Grid(float(bpm), int(beats_per_bar))


def at_beat(b: float, bpm: float) -> float:
    return b * 60.0 / bpm


_CHORDS = {
    "": (0, 4, 7), "maj": (0, 4, 7), "M": (0, 4, 7),
    "m": (0, 3, 7), "min": (0, 3, 7),
    "maj7": (0, 4, 7, 11), "M7": (0, 4, 7, 11),
    "m7": (0, 3, 7, 10), "min7": (0, 3, 7, 10),
    "7": (0, 4, 7, 10),
    "m9": (0, 3, 7, 10, 14), "min9": (0, 3, 7, 10, 14),
    "maj9": (0, 4, 7, 11, 14), "M9": (0, 4, 7, 11, 14),
    "add9": (0, 4, 7, 14), "madd9": (0, 3, 7, 14),
    "sus2": (0, 2, 7), "sus4": (0, 5, 7), "5": (0, 7),
}
_CHORD_RE = re.compile(r"^\s*([A-Ga-g][#b]?)(-?\d)?(.*?)\s*$")


def chord(name: str, octave: int = 3):
    """
    'Am9' -> ['A3', 'C4', 'E4', 'G4', 'B4'].  The octave may be embedded
    ('A2m9') or passed separately.  Qualities: maj/'' min/m maj7 min7/m7 7
    min9/m9 maj9 add9 madd9 sus2 sus4 5.
    """
    m = _CHORD_RE.match(name)
    if not m:
        raise ValueError(f"bad chord name {name!r}")
    root, octv, quality = m.groups()
    if quality not in _CHORDS:
        raise ValueError(f"unknown chord quality {quality!r} in {name!r}")
    base = note_to_midi(f"{root}{octv if octv is not None else octave}")
    return [midi_to_note(base + iv) for iv in _CHORDS[quality]]


# ----------------------------------------------------------------------------
# Track and WAV output
# ----------------------------------------------------------------------------
class Track:
    """Fixed-length mix buffer.  ``add`` places a signal at ``at_s`` seconds
    (sample-accurate, cropped at both ends), with gain and equal-power pan
    (mono input) or balance (stereo input)."""

    def __init__(self, duration_s: float, sr: int = SR, stereo: bool = True):
        self.sr = int(sr)
        self.stereo = bool(stereo)
        self.n = n_samples(duration_s, self.sr)
        self.buf = np.zeros((self.n, 2) if self.stereo else (self.n,), dtype=np.float64)

    @property
    def duration_s(self) -> float:
        return self.n / self.sr

    def add(self, signal, at_s: float, gain: float = 1.0, pan: float = 0.0):
        sig = sanitize(np.asarray(signal, dtype=np.float64))
        if sig.size == 0 or self.n == 0:
            return self
        if sig.ndim == 1:
            if self.stereo:
                gl, gr = pan_gains(pan)
                sig = np.stack([sig * gl, sig * gr], axis=1)
        elif sig.ndim == 2 and sig.shape[1] == 2:
            if self.stereo:
                if pan != 0.0:
                    sig = sig * np.array(_balance_gains(pan))
            else:
                sig = sig.mean(axis=1)
        else:
            raise ValueError("signal must be (n,) or (n, 2)")
        start = int(round(float(at_s) * self.sr))
        s0 = max(0, start)
        e0 = min(self.n, start + len(sig))
        if e0 > s0:
            self.buf[s0:e0] += float(gain) * sig[s0 - start:e0 - start]
        return self

    def mix(self):
        return self.buf.copy()

    def render_wav(self, path: str, bits: int = 24):
        write_wav(path, self.buf, self.sr, bits)
        return path


def write_wav(path: str, x, sr: int = SR, bits: int = 24):
    """Write a PCM WAV (24-bit by default; 16 or 32-bit float also supported)."""
    x = sanitize(np.asarray(x, dtype=np.float64))
    if x.ndim == 1:
        x = x[:, None]
    ch = x.shape[1]
    x = np.clip(x, -1.0, 1.0)
    if bits == 24:
        q = np.round(x * 8388607.0).astype("<i4")
        raw = np.frombuffer(q.tobytes(), dtype=np.uint8).reshape(-1, 4)[:, :3].tobytes()
        fmt = 1
    elif bits == 16:
        raw = np.round(x * 32767.0).astype("<i2").tobytes()
        fmt = 1
    elif bits == 32:
        raw = x.astype("<f4").tobytes()
        fmt = 3
    else:
        raise ValueError("bits must be 16, 24 or 32")
    pad_byte = b"\x00" if len(raw) % 2 else b""
    block_align = ch * bits // 8
    header = (b"RIFF" + struct.pack("<I", 36 + len(raw) + len(pad_byte)) + b"WAVE"
              + b"fmt " + struct.pack("<IHHIIHH", 16, fmt, ch, int(sr), int(sr) * block_align,
                                       block_align, bits)
              + b"data" + struct.pack("<I", len(raw)))
    with open(path, "wb") as fh:
        fh.write(header)
        fh.write(raw)
        fh.write(pad_byte)


# ----------------------------------------------------------------------------
# Analysis helpers
# ----------------------------------------------------------------------------
def peak_dbfs(x) -> float:
    x = sanitize(x)
    return float(lin2db(np.max(np.abs(x)))) if x.size else float("-inf")


def rms_dbfs(x) -> float:
    x = sanitize(x)
    return float(10.0 * np.log10(np.mean(x * x) + 1e-30)) if x.size else float("-inf")


def rms_per_bar(x, bar_s: float, sr: int = SR):
    """RMS in dBFS for each bar-length window (last partial bar included)."""
    x = to_mono(sanitize(x))
    nb = max(1, n_samples(bar_s, sr))
    return [rms_dbfs(x[s:s + nb]) for s in range(0, len(x), nb)]


def analyze(x, sr: int = SR, bar_s: float | None = None) -> dict:
    """Duration, peak, integrated LUFS, per-bar RMS, NaN count and clipped
    sample count (|x| >= 1)."""
    x = np.asarray(x, dtype=np.float64)
    info = {
        "duration_s": len(x) / sr,
        "samples": int(len(x)),
        "channels": 1 if x.ndim == 1 else int(x.shape[1]),
        "nan_count": int(np.sum(~np.isfinite(x))),
        "clipped_samples": int(np.sum(np.abs(np.nan_to_num(x)) >= 1.0)),
        "peak_dbfs": peak_dbfs(x),
        "rms_dbfs": rms_dbfs(x),
        "lufs": measure_lufs(x, sr),
    }
    if bar_s:
        info["rms_per_bar_dbfs"] = rms_per_bar(x, bar_s, sr)
    return info
