#!/usr/bin/env python3
"""Subset the big CJK fonts to only the glyphs the film uses, so the repo stays small.
Scans src/scenes.js + timeline.json for every character; keeps ASCII + punctuation too."""
import re, subprocess, sys, pathlib, json
root = pathlib.Path(__file__).resolve().parent.parent
text = (root / 'src' / 'scenes.js').read_text(encoding='utf8') + (root / 'timeline.json').read_text(encoding='utf8')
chars = set(text) | set(chr(c) for c in range(0x20, 0x7f)) | set('，。、：；！？“”‘’（）《》「」—…·×→•')
chars = {c for c in chars if ord(c) >= 0x20}
uni = ','.join(f'U+{ord(c):04X}' for c in sorted(chars))
src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'assets' / 'fonts'
out = root / 'assets' / 'fonts'
for f in sorted(src.glob('Noto*SC-*.ttf')):
    if f.name.endswith('.sub.ttf'): continue
    dst = out / (f.stem + '.sub.ttf')
    subprocess.run(['pyftsubset', str(f), f'--unicodes={uni}', f'--output-file={dst}', '--layout-features=*', '--no-hinting'], check=True)
    print(dst.name, dst.stat().st_size // 1024, 'KB')
print(len(chars), 'chars')
