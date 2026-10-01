#!/usr/bin/env bash
# 一键成片：字体 → 配乐 → 逐帧渲染 → 合成
set -euo pipefail
cd "$(dirname "$0")"
[ -f fonts/NotoSerifSC-Bold.otf ] || ./fetch_fonts.sh
python3 music.py                      # → build/music.wav
node render.js video                  # → build/video.mp4（需要 playwright）
ffmpeg -y -loglevel error -i build/video.mp4 -i build/music.wav \
  -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart output/one.mp4
echo "done → output/one.mp4"
