"""
《一 · ONE》原创配乐合成器 —— 纯 numpy，从零合成每一个声音。

120 BPM · 4/4 · A 小调（Am7 – Fmaj7 – Cmaj7 – G6）
1 拍 = 0.5 s，1 小节 = 2 s，全曲 32 小节 = 64 s，外加 4 s 混响尾音。

段落（与画面一一对应）：
  bar  0– 3   0– 8s  道生一      氛围铺底 + 第一个音（红点诞生）
  bar  4– 7   8–16s  一生二      半拍底鼓 + 低音进入
  bar  8–11  16–24s  二生三      四拍底鼓 + 踩镲 + 拍手
  bar 12–15  24–32s  三生万物    渐强：军鼓滚奏 + 噪声上升 + 滤波打开
  bar 16–23  32–48s  万物（高潮）全编制 + 琶音 + 侧链律动
  bar 24–27  48–56s  万物归一    鼓组撤出，只留铺底与拨弦
  bar 28–31  56–64s  大道至简    终章：冲击 + 收束和弦 Cmaj9
"""
import wave
import numpy as np

SR = 48000
BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT
LENGTH = 66.0
N = int(LENGTH * SR)
rng = np.random.default_rng(7)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def bar_t(b, beat=0.0):
    return b * BAR + beat * BEAT


class Bus:
    def __init__(self):
        self.x = np.zeros((2, N))

    def add(self, sig, t, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i >= N:
            return
        sig = sig[..., : N - i]
        l = np.cos((pan + 1) * np.pi / 4) * np.sqrt(2)
        r = np.sin((pan + 1) * np.pi / 4) * np.sqrt(2)
        if sig.ndim == 1:
            self.x[0, i:i + len(sig)] += sig * gain * l
            self.x[1, i:i + len(sig)] += sig * gain * r
        else:
            self.x[0, i:i + sig.shape[1]] += sig[0] * gain * l
            self.x[1, i:i + sig.shape[1]] += sig[1] * gain * r


# ---------------------------------------------------------------- filters

def fft_filter(x, lo=None, hi=None, slope=1.0):
    """柔和的频域高通 / 低通（巴特沃斯幅频曲线）。"""
    n = x.shape[-1]
    X = np.fft.rfft(x, axis=-1)
    f = np.fft.rfftfreq(n, 1 / SR)
    g = np.ones_like(f)
    if lo:
        g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (4 * slope))
    if hi:
        g *= 1 / np.sqrt(1 + (f / hi) ** (4 * slope))
    return np.fft.irfft(X * g, n=n, axis=-1)


def convolve(x, ir):
    n = x.shape[-1] + ir.shape[-1] - 1
    size = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, size, axis=-1) * np.fft.rfft(ir, size, axis=-1), size, axis=-1)
    return y[..., : x.shape[-1]]


def make_ir(rt=2.8, predelay=0.025, damp=5500):
    n = int(rt * 1.3 * SR)
    t = np.arange(n) / SR
    env = np.exp(-6.9 * t / rt)
    ir = rng.standard_normal((2, n)) * env
    # 越往后越暗：把早段与晚段分别滤波后交叉淡化
    dark = fft_filter(ir, lo=120, hi=damp * 0.35)
    bright = fft_filter(ir, lo=200, hi=damp)
    w = np.clip(t / (rt * 0.5), 0, 1)
    ir = bright * (1 - w) + dark * w
    ir[:, : int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    ir = np.concatenate([np.zeros((2, int(predelay * SR))), ir], axis=1)
    return ir / np.sqrt(np.sum(ir ** 2) / 2) * 0.5


# ---------------------------------------------------------------- instruments

def adsr(n, a, d, s, r, sus_len=None):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    sus_len = n - a - d - r if sus_len is None else int(sus_len * SR)
    sus_len = max(sus_len, 0)
    env = np.concatenate([
        np.linspace(0, 1, a, endpoint=False) ** 2 if a else [],
        np.linspace(1, s, d, endpoint=False) if d else [],
        np.full(sus_len, s),
        s * np.linspace(1, 0, r) ** 2 if r else [],
    ])
    out = np.zeros(n)
    out[: min(n, len(env))] = env[:n]
    return out


def pad(notes, dur, bright=1.0, attack=0.9, release=1.6):
    """失谐加法锯齿波铺底：温暖、宽阔。返回立体声。"""
    n = int((dur + release) * SR)
    t = np.arange(n) / SR
    out = np.zeros((2, n))
    cutoff = 900 + 2600 * bright
    for m in notes:
        f0 = hz(m)
        for k, (det, side) in enumerate([(-9, 0), (0, None), (9, 1)]):
            f = f0 * 2 ** (det / 1200)
            ph = rng.uniform(0, 2 * np.pi)
            vib = 0.0015 * np.sin(2 * np.pi * (0.2 + 0.07 * k) * t + ph)
            v = np.zeros(n)
            h = 1
            while f * h < min(cutoff * 2.2, 9000):
                amp = (1 / h) / np.sqrt(1 + (f * h / cutoff) ** 4)
                v += amp * np.sin(2 * np.pi * f * h * t * (1 + vib) + ph * h)
                h += 1
            if side is None:
                out += v * 0.7
            else:
                out[side] += v
                out[1 - side] += v * 0.35
    env = adsr(n, attack, 0.4, 0.85, release, sus_len=max(dur - attack - 0.4, 0))
    return out * env * 0.05


def fm_pluck(m, dur=1.6, bright=1.0, decay=3.2):
    """FM 玻璃质感拨弦 —— 片中所有“点”的声音。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    idx = bright * (2.4 * np.exp(-t * 9) + 0.25)
    mod = np.sin(2 * np.pi * f * 2 * t) * idx + 0.3 * np.exp(-t * 20) * np.sin(2 * np.pi * f * 7.01 * t)
    s = np.sin(2 * np.pi * f * t + mod)
    s += 0.25 * np.sin(2 * np.pi * f * 0.5 * t) * np.exp(-t * 4)
    env = np.exp(-t * decay) * np.minimum(t / 0.002, 1)
    return s * env * 0.22


def kick(punch=1.0):
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    f = 44 + 120 * np.exp(-t * 32) + 30 * np.exp(-t * 6)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 5.5)
    click = fft_filter(rng.standard_normal(n), lo=1500, hi=7000) * np.exp(-t * 300) * 0.25
    s = np.tanh((s + click) * 1.6 * punch)
    return s * 0.85


def clap():
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    noise = fft_filter(rng.standard_normal(n), lo=900, hi=5200)
    env = np.zeros(n)
    for k, off in enumerate([0, 0.011, 0.022]):
        tt = t - off
        env += np.where(tt >= 0, np.exp(-np.maximum(tt, 0) * 140), 0) * (0.8 if k < 2 else 0)
    tt = t - 0.033
    env += np.where(tt >= 0, np.exp(-np.maximum(tt, 0) * 16), 0)
    return noise * env * 0.22


def hat(open_=False):
    n = int((0.4 if open_ else 0.09) * SR)
    t = np.arange(n) / SR
    noise = fft_filter(rng.standard_normal(n), lo=7500, hi=15000)
    metal = sum(np.sign(np.sin(2 * np.pi * f * t)) for f in (5340, 7210, 8930, 10120)) * 0.08
    s = fft_filter(noise + metal, lo=6000)
    return s * np.exp(-t * (11 if open_ else 70)) * 0.11


def snare():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (190 + 60 * np.exp(-t * 40)) * t) * np.exp(-t * 25)
    noise = fft_filter(rng.standard_normal(n), lo=1800, hi=9000) * np.exp(-t * 22)
    return (body * 0.35 + noise * 0.5) * 0.3


def bass(m, dur):
    n = int((dur + 0.08) * SR)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.32 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    s = np.tanh(s * 1.3)
    return s * adsr(n, 0.012, 0.2, 0.8, 0.08, sus_len=dur - 0.2) * 0.32


def sweep_noise(dur, f0, f1, width=0.9, curve=2.0):
    """带通扫频噪声：上升（f0<f1）或下降的“风声”。"""
    n = int(dur * SR)
    win, hop = 2048, 512
    noise = rng.standard_normal((2, n + win))
    out = np.zeros((2, n + win))
    w = np.hanning(win)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    lf = np.log2(np.maximum(freqs, 1))
    for i in range(0, n, hop):
        p = (i / n) ** curve if f1 > f0 else 1 - (1 - i / n) ** curve
        fc = f0 * (f1 / f0) ** p
        mask = np.exp(-0.5 * ((lf - np.log2(fc)) / width) ** 2)
        seg = np.fft.irfft(np.fft.rfft(noise[:, i:i + win] * w, axis=-1) * mask, win, axis=-1)
        out[:, i:i + win] += seg * w
    out = out[:, :n]
    return out / (np.max(np.abs(out)) + 1e-9)


def impact():
    n = int(3.0 * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t * 9)) / SR) * np.exp(-t * 1.6)
    hit = fft_filter(rng.standard_normal(n), hi=2500) * np.exp(-t * 7) * 0.5
    s = np.tanh((boom + hit) * 1.4)
    return np.stack([s, s]) * 0.5


def shimmer(m, dur):
    """高处轻颤的正弦泛音，用在开场与结尾。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * hz(m) * k * t + k) / k ** 1.5 for k in (1, 2, 3))
    s *= 0.5 + 0.5 * np.sin(2 * np.pi * 5.5 * t)
    return s * adsr(n, dur * 0.45, 0.1, 0.9, dur * 0.45) * 0.02


def pop(m):
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * hz(m) * t) * np.exp(-t * 60) * 0.06


# ---------------------------------------------------------------- score

CHORDS = {
    "Am7": [57, 60, 64, 67],
    "Fmaj7": [53, 57, 60, 64],
    "Cmaj7": [55, 59, 60, 64],
    "G6": [55, 59, 62, 64],
    "Cmaj9": [48, 55, 59, 62, 64],
}
ROOT = {"Am7": 33, "Fmaj7": 29, "Cmaj7": 36, "G6": 31, "Cmaj9": 36}
LOOP = ["Am7", "Fmaj7", "Cmaj7", "G6"]
MOTIF = {
    "Am7": [(0, 76), (3, 81), (6, 79)],
    "Fmaj7": [(0, 76), (3, 84), (6, 81)],
    "Cmaj7": [(0, 79), (3, 76), (6, 74)],
    "G6": [(0, 74), (3, 79), (6, 76)],
    "Cmaj9": [(0, 79), (3, 83), (6, 86)],
}


def chord_of(b):
    if b == 28:
        return "Fmaj7"
    if b == 29:
        return "G6"
    if b >= 30:
        return "Cmaj9"
    return LOOP[b % 4]


def main():
    drums, padb, pluckb, bassb, fx, verb_send = Bus(), Bus(), Bus(), Bus(), Bus(), Bus()
    kicks = []

    def K(t, g=1.0):
        drums.add(kick(), t, g)
        kicks.append((t, g))

    # ---- 铺底与低音
    for b in range(32):
        c = chord_of(b)
        if b >= 30 and b > 30:
            continue
        dur = BAR * (2 if b == 30 else 1) + (0.0 if b < 30 else 2.0)
        bright = 0.35
        if 8 <= b < 12:
            bright = 0.55
        if 12 <= b < 16:
            bright = 0.5 + 0.5 * (b - 12) / 4
        if 16 <= b < 24:
            bright = 1.0
        if 24 <= b < 28:
            bright = 0.6
        if b >= 28:
            bright = 0.9
        gain = 0.55 + 0.45 * min(b / 2, 1) if b < 4 else 1.0
        if b == 0:
            p = pad(CHORDS[c], BAR, bright, attack=1.8)
        else:
            p = pad(CHORDS[c], dur, bright, attack=0.35 if b in (16, 28) else 0.25)
        padb.add(p, bar_t(b), gain)
        verb_send.add(p, bar_t(b), gain * 0.5)
        if 4 <= b < 24 or 28 <= b <= 30:
            bl = BAR if b < 30 else BAR * 2 + 1.5
            bassb.add(bass(ROOT[c], bl - 0.02), bar_t(b), 0.9 if b < 8 else 1.0)

    # ---- 拨弦动机（红点的声音）
    pluckb.add(fm_pluck(81, 3.0, 0.8, decay=1.4), 2.0, 1.0)  # 红点诞生
    verb_send.add(fm_pluck(81, 3.0, 0.8, decay=1.4), 2.0, 1.2)
    for b in range(2, 31):
        if b == 15:  # 渐强最后一小节让位给滚奏
            continue
        c = chord_of(b)
        for step, m in MOTIF[c]:
            if b == 30 and step > 0:
                continue
            t = bar_t(b) + step * BEAT / 2
            g = 0.75 if b < 16 else 0.9
            br = 0.7 if b < 16 else 1.0
            s = fm_pluck(m, 1.8, br)
            pan = [-0.25, 0.25, 0.0][MOTIF[c].index((step, m)) % 3]
            pluckb.add(s, t, g, pan)
            verb_send.add(s, t, g * (0.9 if 24 <= b < 28 else 0.5), pan)
            if 16 <= b < 24:
                pluckb.add(fm_pluck(m + 12, 1.2, 0.6, decay=5), t, 0.25, -pan)

    # ---- 高潮琶音（16 分音符）
    for b in range(16, 24):
        notes = [m + 12 for m in CHORDS[chord_of(b)]]
        order = [0, 2, 1, 3, 2, 3, 1, 2]
        for s16 in range(16):
            m = notes[order[s16 % 8] % len(notes)] + (12 if s16 % 8 == 7 else 0)
            t = bar_t(b) + s16 * BEAT / 4
            acc = 1.0 if s16 % 4 == 0 else 0.6
            sig = fm_pluck(m, 0.35, 0.5, decay=14)
            pluckb.add(sig, t, 0.28 * acc, -0.45 if s16 % 2 else 0.45)
            verb_send.add(sig, t, 0.1)

    # ---- 鼓组
    for b in range(4, 8):  # 一生二：半拍底鼓
        K(bar_t(b, 0), 0.7)
        K(bar_t(b, 2), 0.55)
    for b in range(8, 12):  # 二生三：律动建立
        for bt in range(4):
            K(bar_t(b, bt), 0.85)
            drums.add(hat(), bar_t(b, bt + 0.5), 0.8, 0.3)
        drums.add(clap(), bar_t(b, 1), 0.8)
        drums.add(clap(), bar_t(b, 3), 0.8)
        verb_send.add(clap(), bar_t(b, 1), 0.3)
        verb_send.add(clap(), bar_t(b, 3), 0.3)
    for b in range(12, 16):  # 三生万物：渐强
        if b < 14:
            for bt in range(4):
                K(bar_t(b, bt), 0.9)
        for s16 in range(16):
            drums.add(hat(), bar_t(b, s16 / 4), 0.35 + 0.35 * (s16 % 2), 0.3)
        if b == 13:
            for bt in range(4):
                drums.add(snare(), bar_t(b, bt), 0.5)
        if b == 14:
            for e in range(8):
                drums.add(snare(), bar_t(b, e / 2), 0.7 + 0.04 * e)
        if b == 15:
            for s16 in range(14):
                drums.add(snare(), bar_t(b, s16 / 4), 0.85 + 0.04 * s16)
    for b in list(range(16, 24)) + [28, 29]:  # 高潮与终章
        for bt in range(4):
            if b == 23 and bt >= 2:
                continue
            K(bar_t(b, bt), 1.0)
            drums.add(hat(), bar_t(b, bt + 0.5), 0.9, 0.3)
            drums.add(hat(), bar_t(b, bt + 0.25), 0.3, -0.3)
            drums.add(hat(), bar_t(b, bt + 0.75), 0.3, -0.3)
        drums.add(clap(), bar_t(b, 1), 1.0)
        verb_send.add(clap(), bar_t(b, 1), 0.35)
        if not (b == 23):
            drums.add(clap(), bar_t(b, 3), 1.0)
            verb_send.add(clap(), bar_t(b, 3), 0.35)
        if b % 4 == 0:
            drums.add(hat(open_=True), bar_t(b, 0), 1.6)
    for b in range(24, 28):  # 万物归一：心跳般的轻底鼓
        K(bar_t(b, 0), 0.35)

    # ---- 效果：上升、冲击、转场气声
    fx.add(sweep_noise(6.0, 300, 9000, width=0.6) * 0.3, 26.0)
    rise = np.arange(int(4 * SR)) / SR
    tone = np.sin(2 * np.pi * np.cumsum(220 * 2 ** (rise / 4 * 2)) / SR) * (rise / 4) ** 2 * 0.05
    fx.add(tone, 28.0)
    for t_imp, g in [(32.0, 1.0), (56.0, 0.9), (60.0, 0.6)]:
        fx.add(impact(), t_imp, g)
        verb_send.add(impact(), t_imp, 0.4 * g)
        drums.add(hat(open_=True), t_imp, 2.0)
    for t_sw in [7.0, 15.0, 23.0, 46.5]:  # 段落之间的气声
        fx.add(sweep_noise(1.0, 600, 5000, width=0.7, curve=1.5) * 0.06 * np.hanning(int(SR))[None], t_sw)
    fx.add(sweep_noise(2.0, 8000, 300, width=0.7) * 0.07, 48.0)
    fx.add(sweep_noise(2.0, 400, 7000, width=0.6) * 0.1, 54.0)
    # 开场与结尾的高处泛音
    fx.add(shimmer(88, 7.0), 0.0, 1.0, 0.3)
    fx.add(shimmer(91, 6.0), 60.0, 1.0, -0.3)
    verb_send.add(shimmer(88, 7.0), 0.0, 1.0)
    # 终章：钟声般的大和弦
    for i, m in enumerate([72, 76, 79, 83, 86]):
        s = fm_pluck(m, 6.0, 1.0, decay=0.8)
        pluckb.add(s, 60.0 + i * 0.03, 0.55, (i - 2) * 0.2)
        verb_send.add(s, 60.0 + i * 0.03, 0.8)
    # 万物（网格）出现时的点状音
    for i in range(12):
        fx.add(pop(84 + [0, 3, 7, 10, 12, 15][i % 6]), 24.0 + i * 0.125, 0.8, (i % 5 - 2) * 0.3)

    # ---- 侧链：底鼓压缩铺底与低音，形成“呼吸感”
    env = np.ones(N)
    t_all = np.arange(N) / SR
    for t, g in kicks:
        i = int(t * SR)
        seg = t_all[i:i + int(0.45 * SR)] - t
        duck = 1 - 0.7 * g * np.exp(-seg / 0.11) * (seg >= 0)
        env[i:i + len(seg)] = np.minimum(env[i:i + len(seg)], duck)
    padb.x *= env
    bassb.x *= env ** 1.3
    pluckb.x *= 0.6 + 0.4 * env

    verb = convolve(verb_send.x, make_ir())
    mix = drums.x * 1.0 + padb.x * 0.85 + pluckb.x * 0.9 + bassb.x * 0.95 + fx.x * 1.0 + verb * 0.55

    # ---- 母带：低切、柔和饱和、淡出、归一化到 -1 dBFS
    mix = fft_filter(mix, lo=28)
    mix /= np.max(np.abs(mix))
    mix = np.tanh(mix * 1.5) / np.tanh(1.5)
    fade = np.ones(N)
    fs, fe = int(63.0 * SR), int(LENGTH * SR)
    fade[fs:fe] = np.linspace(1, 0, fe - fs) ** 2
    mix *= fade
    mix = mix / np.max(np.abs(mix)) * 10 ** (-1 / 20)

    pcm = (mix.T * 32767).astype(np.int16)
    with wave.open("build/music.wav", "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote build/music.wav", LENGTH, "s")


if __name__ == "__main__":
    import os
    os.makedirs("build", exist_ok=True)
    main()
