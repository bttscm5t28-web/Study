"""Fetch the NASA public-domain photographs used in the film and cut them into
square "worlds" (the renderer treats every image as a square that can be
pixelated, resolved, and shrunk into a single pixel of the next one).

All images: NASA Image and Video Library (images.nasa.gov), public domain.
"""
import os
import urllib.request

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, "build", "cache")
WORLDS = os.path.join(ROOT, "build", "worlds")

# name: (NASA id, square-crop centre (x, y) as fractions, side as a fraction of the short edge, output px, caption)
SOURCES = {
    "riyadh":    ("iss033e020288", (0.50, 0.50), 1.00, 2832,
                  "RIYADH AT NIGHT  ·  ISS033-E-20288"),
    "karakoram": ("iss069e060266", (0.52, 0.50), 1.00, 3072,
                  "KARAKORAM GLACIERS  ·  ISS069-E-60266"),
    "everest":   ("iss008e13304", (0.50, 0.50), 1.00, 2008,
                  "EVEREST & MAKALU  ·  ISS008-E-13304"),
    "bahamas":   ("iss065e144117", (0.56, 0.50), 1.00, 3072,
                  "THE BAHAMAS  ·  ISS065-E-144117"),
    "earth":     ("GSFC_20171208_Archive_e001386", (0.50, 0.487), 0.90, 4096,
                  "BLUE MARBLE  ·  NASA / NOAA  ·  SUOMI NPP VIIRS"),
}
# where the Bahamas sit on the Blue Marble square (used for the last zoom-out)
EARTH_BAHAMAS = (0.8467, 0.4233)

CREDITS = {
    "iss033e020288": "Riyadh, Saudi Arabia at night, photographed by an Expedition 33 crew member on the ISS (13 Nov 2012).",
    "iss069e060266": "Glaciers of the Karakoram range, photographed from the ISS (15 Aug 2023).",
    "iss008e13304": "Mt. Everest and Makalu, photographed by an Expedition 8 crew member on the ISS (28 Jan 2004).",
    "iss065e144117": "Shallow waters off the Bahamas, photographed from the ISS by Shane Kimbrough (23 Jun 2021).",
    "GSFC_20171208_Archive_e001386": "Blue Marble 2012, NASA/NOAA/GSFC/Suomi NPP/VIIRS/Norman Kuring.",
}


def fetch(nasa_id):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, nasa_id + ".jpg")
    if not os.path.exists(path):
        url = f"https://images-assets.nasa.gov/image/{nasa_id}/{nasa_id}~orig.jpg"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (concept film build)"})
        with urllib.request.urlopen(req, timeout=300) as r, open(path + ".part", "wb") as f:
            f.write(r.read())
        os.replace(path + ".part", path)
    return path


FONTS = os.path.join(ROOT, "assets", "fonts")
# Source Serif 4 Display (SIL OFL), fetched from Google Fonts at build time
SERIF_CSS = ("https://fonts.googleapis.com/css2?family=Source+Serif+4:"
             "ital,opsz,wght@0,60,300;0,60,400;0,60,600;1,60,300;1,60,400&display=swap")


def fetch_fonts():
    import re
    os.makedirs(FONTS, exist_ok=True)
    want = ["300", "400", "600", "300Italic", "400Italic"]
    if all(os.path.exists(os.path.join(FONTS, f"SourceSerif4Display-{w}.ttf")) for w in want):
        return
    ua = {"User-Agent": "Mozilla/4.0"}   # an old UA makes the CSS API hand out plain TTF files
    css = urllib.request.urlopen(urllib.request.Request(SERIF_CSS, headers=ua), timeout=60).read().decode()
    for style, weight, url in re.findall(r"font-style: (\w+);\s*font-weight: (\d+);.*?src: url\((.*?)\)", css, re.S):
        name = f"SourceSerif4Display-{weight}{'Italic' if style == 'italic' else ''}.ttf"
        with urllib.request.urlopen(urllib.request.Request(url, headers=ua), timeout=120) as r:
            open(os.path.join(FONTS, name), "wb").write(r.read())


def world_path(name):
    return os.path.join(WORLDS, name + ".png")


def prepare(force=False):
    fetch_fonts()
    os.makedirs(WORLDS, exist_ok=True)
    for name, (nid, (cx, cy), frac, out, _) in SOURCES.items():
        dst = world_path(name)
        if os.path.exists(dst) and not force:
            continue
        im = Image.open(fetch(nid)).convert("RGB")
        w, h = im.size
        side = frac * min(w, h)
        x0 = min(max(cx * w - side / 2, 0), w - side)
        y0 = min(max(cy * h - side / 2, 0), h - side)
        sq = im.resize((out, out), Image.LANCZOS, box=(x0, y0, x0 + side, y0 + side))
        sq.save(dst, optimize=True)
        print("world", name, sq.size)


if __name__ == "__main__":
    prepare(force=True)
