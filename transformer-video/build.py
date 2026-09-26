"""一键生成成片：渲染全部场景 → 拼接 → 生成字幕 → 烧录字幕。

    python build.py            # 1080p30 成片
    python build.py --preview  # 480p15 快速预览
    python build.py --only S06_AttentionMath   # 只重渲染某几个场景（其余沿用已有结果）
"""
import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from scenes import SCENES

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
OUT = ROOT / "output"
SUBS = BUILD / "subs"
NAME = "transformer_explained"


def render(scene, quality):
    cmd = ["manim", "render", str(ROOT / "scenes.py"), scene, "--media_dir", str(BUILD / "media"),
           "--disable_caching", "--progress_bar", "none", "-v", "WARNING"]
    cmd += ["-ql"] if quality == "preview" else ["--resolution", "1920,1080", "--frame_rate", "30"]
    print(f"  渲染 {scene} ...", flush=True)
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stdout[-3000:], res.stderr[-3000:], file=sys.stderr)
        return scene
    return None


def video_path(scene, quality):
    sub = "480p15" if quality == "preview" else "1080p30"
    return BUILD / "media" / "videos" / "scenes" / sub / f"{scene}.mp4"


def duration(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", str(path)], text=True)
    return float(out.strip())


def fmt(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def subtitle_text(text):
    # 中文字幕习惯：去掉句末的逗号、句号等
    return text.rstrip("，。；：、——").strip()


def build_srt(offsets):
    entries = []
    for scene, off in offsets:
        data = json.loads((SUBS / f"{scene}.json").read_text())
        for ev in data["events"]:
            entries.append((off + ev["start"], off + ev["end"], subtitle_text(ev["text"]), ev["text"]))
    srt = []
    for i, (a, b, text, _) in enumerate(entries, 1):
        srt.append(f"{i}\n{fmt(a)} --> {fmt(b + 0.15)}\n{text}\n")
    return "\n".join(srt), entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--only", nargs="*", help="只渲染这些场景")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--no-render", action="store_true")
    args = ap.parse_args()
    quality = "preview" if args.preview else "final"

    todo = [] if args.no_render else (args.only or SCENES)
    if todo:
        print(f"渲染 {len(todo)} 个场景（{quality}）")
        with ThreadPoolExecutor(args.jobs) as pool:
            failed = [s for s in pool.map(lambda s: render(s, quality), todo) if s]
        if failed:
            sys.exit(f"渲染失败：{failed}")

    OUT.mkdir(exist_ok=True)
    BUILD.mkdir(exist_ok=True)
    listing = BUILD / "concat.txt"
    listing.write_text("".join(f"file '{video_path(s, quality)}'\n" for s in SCENES))
    joined = BUILD / f"joined_{quality}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", str(joined)], check=True)

    offsets, t = [], 0.0
    for s in SCENES:
        offsets.append((s, t))
        t += duration(video_path(s, quality))
    srt, entries = build_srt(offsets)
    suffix = "" if quality == "final" else "_preview"
    srt_path = OUT / f"{NAME}{suffix}.srt"
    srt_path.write_text(srt, encoding="utf-8")

    style = ("FontName=Noto Sans CJK SC,FontSize=18,PrimaryColour=&H00F3EDE6,OutlineColour=&HC0000000,"
             "BorderStyle=1,Outline=1.6,Shadow=0,MarginV=14,Bold=0")
    final = OUT / f"{NAME}{suffix}.mp4"
    vf = f"subtitles={srt_path}:force_style='{style}'"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(joined), "-vf", vf, "-c:v", "libx264",
                    "-preset", "slow" if quality == "final" else "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-movflags", "+faststart", str(final)], check=True)

    if quality == "final":
        lines = ["# 旁白 / 字幕稿", ""]
        for scene, off in offsets:
            data = json.loads((SUBS / f"{scene}.json").read_text())
            lines.append(f"## [{fmt(off)[:8]}] {scene}")
            lines.append("")
            lines += [ev["text"] for ev in data["events"]]
            lines.append("")
        (OUT / "narration.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"完成：{final}（{t / 60:.1f} 分钟）")


if __name__ == "__main__":
    main()
