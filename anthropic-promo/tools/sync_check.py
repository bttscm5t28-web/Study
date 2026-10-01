#!/usr/bin/env python3
"""Independent audio↔picture sync check: for every visual snap in the storyboard, measure whether the
score has a transient there. Energy in [t, t+30ms] vs the 60 ms before. Prints a table; exits 1 if a
listed 'must' hit is missing. Usage: python3 tools/sync_check.py [music/track.wav]"""
import sys, numpy as np
from scipy.io import wavfile
path = sys.argv[1] if len(sys.argv) > 1 else 'music/track.wav'
sr, x = wavfile.read(path)
x = x.astype(np.float64); x = x / (2 ** 31 if x.dtype == np.float64 and np.abs(x).max() > 2 else 1)
if x.ndim == 2: x = x.mean(axis=1)
x = x / (np.abs(x).max() or 1)
n = len(x); dur = n / sr
print(f'{path}: {dur:.3f} s, {n} samples, sr {sr}')
# hit list: (time, label, must)
hits = [(0.8,'first tick',1),(3.2,'A3 rises',0),(6.4,'E4 enters / split',1),(9.6,'A4 enters',0),(12.0,'tick / MAX',1),
        (12.8,'pad+pluck ring 1',1),(13.2,'ring 2',1),(13.6,'ring 3',1),(14.0,'ring 4',1),(14.4,'ring 5',1),(14.8,'ring 6',1),(15.2,'ring 7',0),(15.6,'ring 8 pickup',1),(16.0,'headline',1),
        (19.2,'60px / roll',1),(19.4,'roll',1),(19.6,'roll',1),(19.8,'roll',1),(20.0,'1,000,000',1),
        (22.4,'30px kick',1),(24.0,'fork',1),(25.6,'15px headline',1),(27.2,'merge',1),
        (28.8,'15px A3',1),(29.2,'C4',1),(29.6,'E4',1),(30.0,'A4',1),(30.4,'C5',1),(30.8,'E5',1),(31.2,'A5 5px',1),(31.6,'C6',1),
        (32.0,'FACE Fmaj7',1),(35.2,'kick returns',1),
        (38.4,'collapse',1),(38.8,'swap people',1),(39.2,'60px',1),(40.0,'30px',1),(40.8,'1px',1),
        (41.6,'collapse G',1),(42.0,'swap city',1),(42.4,'60',1),(42.8,'30',1),(43.2,'30c8',1),(43.6,'15',1),(44.0,'5',1),(44.4,'5full',1),(44.8,'CITY real',1),
        (46.4,'vacuum/rev 5',0),(46.8,'rev 15',0),(47.2,'rev 60',0),(47.6,'rev 120',0),
        (48.0,'IMPACT',1)] + [(48.4+0.2*i, f'qt gen {i+1}',1) for i in range(13)] + [(51.0,'(no tick)',-1),(51.2,'EARTH real Fmaj7',1),(54.4,'G boundary closes',1),(57.6,'SKY Cmaj9',1),
        (60.8,'pad solo',0),(64.0,'E5',0),(70.4,'unison A',1),(75.2,'final tick',1)]
def energy(a, b):
    i, j = int(a * sr), int(b * sr); seg = x[max(0, i):max(0, j)]
    return float(np.sqrt(np.mean(seg ** 2)) + 1e-9) if len(seg) else 1e-9
fails = 0
print(f'{"t":>6} {"label":22} {"post/pre dB":>12}  result')
for t, label, must in hits:
    pre = energy(t - 0.06, t - 0.01); post = energy(t, t + 0.03)
    db = 20 * np.log10(post / pre)
    if must == -1: ok = db < 3; res = 'ok (silent as required)' if ok else 'UNEXPECTED transient'
    elif must == 1: ok = db > 2.0; res = 'ok' if ok else 'MISSING'
    else: ok = True; res = 'ok' if db > 2 else '(soft)'
    if not ok: fails += 1
    print(f'{t:6.2f} {label:22} {db:12.1f}  {res}')
# global transient peak
env = np.array([energy(t, t + 0.03) for t in np.arange(0, dur - 0.03, 0.01)])
tp = env.argmax() * 0.01
print(f'loudest 30 ms window at {tp:.2f} s (impact expected at 48.00)')
tail = x[int(76.0 * sr):]
print('silence 76.0-76.8:', 'ok' if len(tail) and np.abs(tail).max() == 0 else f'NOT silent (max {np.abs(tail).max() if len(tail) else "n/a"})')
print(f'{fails} must-hits missing')
sys.exit(1 if fails else 0)
