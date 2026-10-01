#!/usr/bin/env bash
# Extract review material from a rendered MP4: a still every 0.8 s (one per beat) + key frames at full res, then contact sheets.
set -euo pipefail
V=${1:-build/film_v2.mp4}; OUT=${2:-build/review}
rm -rf "$OUT"; mkdir -p "$OUT/beats" "$OUT/keys"
ffmpeg -v error -y -i "$V" -vf "fps=1.25" -start_number 0 "$OUT/beats/b%03d.png"   # 1.25 fps = one frame per 0.8 s
python3 - "$OUT" <<'PY'
import sys, os, glob
from PIL import Image, ImageDraw, ImageFont
out = sys.argv[1]; files = sorted(glob.glob(f'{out}/beats/b*.png'))
font = ImageFont.truetype('assets/fonts/Inter-600-normal.ttf', 20)
cols, rows = 4, 4; tw, th = 480, 270
for s in range(0, len(files), cols*rows):
    chunk = files[s:s+cols*rows]
    sheet = Image.new('RGB', (cols*tw, ((len(chunk)+cols-1)//cols)*th), (30,30,30)); d = ImageDraw.Draw(sheet)
    for i, f in enumerate(chunk):
        im = Image.open(f).convert('RGB').resize((tw, th), Image.LANCZOS); x, y = (i%cols)*tw, (i//cols)*th
        sheet.paste(im, (x, y)); t = (s+i)*0.8
        d.rectangle([x, y, x+96, y+28], fill=(0,0,0)); d.text((x+6, y+3), f'{t:5.1f}s b{int(t//3.2)+1}.{int((t%3.2)//0.8)+1}', fill=(255,220,0), font=font)
    sheet.save(f'{out}/beats_sheet_{s//(cols*rows)+1}.jpg', quality=90)
print(len(files), 'beat frames')
PY
for t in 1.0 3.6 7.2 11.6 13.4 16.4 20.4 23.6 26.0 29.3 30.6 31.5 33.0 36.0 39.0 40.4 41.2 42.6 43.4 45.2 46.6 48.2 49.0 50.0 50.9 51.4 53.2 55.0 59.0 62.0 66.0 70.8 72.8 75.5; do
  ffmpeg -v error -y -ss $t -i "$V" -frames:v 1 "$OUT/keys/t${t}.png"
done
ls "$OUT"/beats_sheet_*.jpg | wc -l; ls "$OUT/keys" | wc -l
