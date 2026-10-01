#!/usr/bin/env bash
# Full pipeline: bake mosaic stages → synthesize score → render frames → mux.
set -euo pipefail
cd "$(dirname "$0")"
python3 tools/bake.py            # build/bake/*.png  (quantized stages + Earth quadtree generations)
python3 music/compose.py         # music/track.wav   (76.8 s procedural score)
node render.js --out output/from_one_pixel.mp4   # 1920x1080 30 fps H.264 + AAC
