"""One-shot build: fetch imagery -> synthesise the soundtrack -> render the film.

    python build.py            # full 1080p30 film -> output/
    python build.py --audio    # only re-render the soundtrack
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))

import assets  # noqa: E402
import music  # noqa: E402
import render  # noqa: E402

OUT = os.path.join(HERE, "output", "claude_opus_5_5_resolution.mp4")
WAV = os.path.join(HERE, "build", "soundtrack.wav")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", action="store_true", help="only build the soundtrack")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(WAV), exist_ok=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    assets.prepare()
    music.build(WAV)
    print("soundtrack ->", WAV)
    if not a.audio:
        render.run_video(OUT, WAV, workers=a.workers)
        render.run_poster(os.path.join(HERE, "output", "poster.jpg"))
