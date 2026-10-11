"""Generate the demo images.

The "before" page uses what a typical site ships: full-size JPEGs straight from
the camera or stock site. The "after" page uses the same pictures resized to
the sizes they are actually shown at and encoded as AVIF and WebP.

The pictures themselves are drawn procedurally (no stock photos, no licensing
questions). A light noise layer makes them compress like real photos.

Usage: python tools/make_images.py   (needs Pillow 11+)
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
BEFORE = ROOT / "before" / "img"
AFTER = ROOT / "after" / "img"

SCENES = {
    "hero": ((14, 30, 54), (233, 152, 98), (36, 62, 74)),
    "roastery": ((48, 33, 26), (196, 140, 92), (92, 64, 48)),
    "beans": ((30, 22, 18), (160, 98, 56), (70, 46, 32)),
    "cafe": ((22, 40, 38), (218, 186, 140), (60, 84, 76)),
}


def draw_scene(name, size):
    sky_top, sky_bottom, ground = SCENES[name]
    w, h = size
    rnd = random.Random(name)
    img = Image.new("RGB", size)
    px = ImageDraw.Draw(img)

    # Sky gradient
    for y in range(h):
        t = y / h
        color = tuple(int(a + (b - a) * t) for a, b in zip(sky_top, sky_bottom))
        px.line([(0, y), (w, y)], fill=color)

    # Three layers of hills
    for layer in range(3):
        base = int(h * (0.55 + layer * 0.12))
        shade = tuple(int(c * (0.55 + layer * 0.2)) for c in ground)
        points = [(0, h)]
        x = 0
        while x <= w:
            points.append((x, base - rnd.randint(0, int(h * 0.12))))
            x += rnd.randint(w // 14, w // 7)
        points += [(w, base), (w, h)]
        px.polygon(points, fill=shade)

    # Sun
    r = int(min(w, h) * 0.08)
    cx, cy = int(w * 0.72), int(h * 0.32)
    px.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(250, 214, 160))

    img = img.filter(ImageFilter.GaussianBlur(radius=max(1, w // 900)))
    noise = Image.effect_noise(size, 28).convert("RGB")
    return Image.blend(img, noise, 0.08)


def main():
    BEFORE.mkdir(parents=True, exist_ok=True)
    AFTER.mkdir(parents=True, exist_ok=True)

    # Before: oversized JPEGs at high quality, as often uploaded by site owners.
    for name in SCENES:
        size = (4000, 2400) if name == "hero" else (2400, 1600)
        draw_scene(name, size).save(BEFORE / f"{name}.jpg", quality=95)

    # After: resized to the rendered size (and 2x for sharp screens), modern formats.
    targets = {"hero": [800, 1200, 1600], "roastery": [400, 800], "beans": [400, 800], "cafe": [400, 800]}
    for name, widths in targets.items():
        source = Image.open(BEFORE / f"{name}.jpg")
        for width in widths:
            height = round(source.height * width / source.width)
            small = source.resize((width, height), Image.LANCZOS)
            small.save(AFTER / f"{name}-{width}.avif", quality=55)
            small.save(AFTER / f"{name}-{width}.webp", quality=72, method=6)

    for folder in (BEFORE, AFTER):
        total = sum(p.stat().st_size for p in folder.iterdir())
        print(f"{folder.relative_to(ROOT)}: {total / 1024:.0f} KB in {len(list(folder.iterdir()))} files")


if __name__ == "__main__":
    main()
