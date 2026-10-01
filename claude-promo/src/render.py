"""Render the film: frames (multiprocess) -> ffmpeg (H.264) muxed with the soundtrack.

    python render.py                      # full film -> output/
    python render.py --stills 1.5 6 12    # preview stills (PNG) at given seconds
    python render.py --range 40 47        # render only a time range (preview mp4)
    python render.py --poster             # the key visual -> output/poster.jpg
"""
import argparse
import os
import subprocess
import sys
import time
from multiprocessing import Pool

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import timeline as T  # noqa: E402

FPS = 30
_CTX = None


def _init():
    global _CTX
    import scenes
    _CTX = scenes.make_ctx()


def to_u8(frame, seed):
    rs = np.random.default_rng(seed)
    noise = rs.random(frame.shape[:2], dtype=np.float32)[..., None] - 0.5   # 1 LSB dither against banding
    return np.clip(frame * 255.0 + noise, 0, 255).astype(np.uint8)


def _frame(i):
    import scenes
    t = i / FPS
    return to_u8(scenes.render(t, _CTX), i).tobytes()


def _still(t):
    import scenes
    return t, to_u8(scenes.render(t, _CTX), int(t * 1000))


def run_video(out, audio, t0=0.0, t1=None, workers=4, crf=19):
    t1 = T.DURATION if t1 is None else t1
    frames = range(int(round(t0 * FPS)), int(round(t1 * FPS)))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080",
           "-r", str(FPS), "-i", "-"]
    if audio:
        cmd += ["-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", audio]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p",
            "-profile:v", "high", "-tune", "film", "-movflags", "+faststart"]
    if audio:
        cmd += ["-c:a", "aac", "-b:a", "256k", "-shortest"]
    cmd += [out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    st = time.time()
    with Pool(workers, initializer=_init) as pool:
        for k, buf in enumerate(pool.imap(_frame, frames, chunksize=2)):
            p.stdin.write(buf)
            if k % 60 == 0:
                el = time.time() - st
                print(f"  frame {k}/{len(frames)}  {el:6.1f}s  ({(k + 1) / max(el, 1e-6):.1f} fps)", flush=True)
    p.stdin.close()
    p.wait()
    print(f"wrote {out} in {time.time() - st:.0f}s")


def run_poster(out):
    _init()
    import scenes
    Image.fromarray(to_u8(scenes.poster(_CTX), 0)).save(out, quality=92)
    print(out)


def run_stills(ts, outdir, workers=4):
    os.makedirs(outdir, exist_ok=True)
    with Pool(min(workers, len(ts)), initializer=_init) as pool:
        for t, img in pool.imap_unordered(_still, ts):
            path = os.path.join(outdir, f"still_{t:06.2f}.png")
            Image.fromarray(img).save(path)
            print(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--range", nargs=2, type=float)
    ap.add_argument("--out", default=None)
    ap.add_argument("--audio", default=os.path.join(HERE, "..", "build", "soundtrack.wav"))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--crf", type=int, default=19)
    ap.add_argument("--poster", action="store_true", help="render the key visual (output/poster.jpg)")
    a = ap.parse_args()
    if a.poster:
        run_poster(a.out or os.path.join(HERE, "..", "output", "poster.jpg"))
    elif a.stills:
        run_stills(a.stills, a.out or os.path.join(HERE, "..", "build", "stills"), a.workers)
    elif a.range:
        run_video(a.out or os.path.join(HERE, "..", "build", "preview.mp4"), a.audio, a.range[0], a.range[1],
                  a.workers, a.crf)
    else:
        run_video(a.out or os.path.join(HERE, "..", "output", "claude_opus_5_5_resolution.mp4"), a.audio,
                  workers=a.workers, crf=a.crf)
