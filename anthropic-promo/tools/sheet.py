#!/usr/bin/env python3
"""Make labeled contact sheets from stills: python tools/sheet.py build/stills out_prefix [cols]"""
import sys, glob, os, re
from PIL import Image, ImageDraw, ImageFont
d, out = sys.argv[1], sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
files = sorted(glob.glob(os.path.join(d, 't*.png')))
font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), '..', 'assets', 'fonts', 'Inter-600-normal.ttf'), 22)
tw, th = 1920 // cols, 1080 // cols
per = cols * cols
for s in range(0, len(files), per):
    sheet = Image.new('RGB', (cols * tw, (min(per, len(files) - s) + cols - 1) // cols * th), (30, 30, 30))
    dr = ImageDraw.Draw(sheet)
    for i, f in enumerate(files[s:s + per]):
        im = Image.open(f).convert('RGB').resize((tw, th), Image.LANCZOS)
        x, y = (i % cols) * tw, (i // cols) * th
        sheet.paste(im, (x, y))
        t = re.search(r't(\d+\.\d+)', os.path.basename(f)).group(1)
        dr.rectangle([x, y, x + 86, y + 30], fill=(0, 0, 0)); dr.text((x + 6, y + 3), f'{float(t):.2f}s', fill=(255, 220, 0), font=font)
    p = f'{out}_{s // per + 1}.jpg'; sheet.save(p, quality=90); print(p)
