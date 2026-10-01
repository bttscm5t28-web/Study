#!/usr/bin/env bash
# 下载片中用到的字体：Noto Sans/Serif SC（思源黑体/宋体）与 Inter
set -euo pipefail
cd "$(dirname "$0")" && mkdir -p fonts && cd fonts
CDN=https://cdn.jsdelivr.net/gh/notofonts/noto-cjk@main
for w in Thin Light Regular Medium Bold Black; do curl -fsSLO "$CDN/Sans/SubsetOTF/SC/NotoSansSC-$w.otf"; done
curl -fsSLO "$CDN/Serif/SubsetOTF/SC/NotoSerifSC-Bold.otf"
curl -fsSL -o inter.zip https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip
unzip -o -j -q inter.zip 'extras/ttf/Inter-Light.ttf' 'extras/ttf/Inter-Regular.ttf' 'extras/ttf/Inter-Medium.ttf' \
  'extras/ttf/Inter-SemiBold.ttf' 'extras/ttf/Inter-Bold.ttf' 'extras/ttf/InterDisplay-Light.ttf' \
  'extras/ttf/InterDisplay-Bold.ttf' 'extras/ttf/InterDisplay-Black.ttf'
rm inter.zip
