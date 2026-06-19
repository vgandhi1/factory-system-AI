"""Procedural defect-image renderers (PIL only, no external assets).

Each part is a gray metal "plate" with bolt holes. A defect renderer draws a
flaw on the plate and returns its YOLO class id + pixel bounding box(es), so the
generator can write matching labels. Deterministic given the rng.
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw

# YOLO class order. VisionGuard's data.yaml must match this exactly.
CLASSES = ["surface", "dimension", "color", "missing_component"]
CLASS_ID = {name: i for i, name in enumerate(CLASSES)}

BG = (96, 98, 102)
PLATE = (132, 134, 140)
PLATE_EDGE = (70, 71, 75)
BOLT = (60, 61, 65)


def _plate_box(size: int) -> tuple[int, int, int, int]:
    m = int(size * 0.12)
    return (m, m, size - m, size - m)


def _bolt_positions(box: tuple[int, int, int, int]) -> list[tuple[int, int]]:
    x0, y0, x1, y1 = box
    pad = int((x1 - x0) * 0.12)
    return [(x0 + pad, y0 + pad), (x1 - pad, y0 + pad),
            (x0 + pad, y1 - pad), (x1 - pad, y1 - pad)]


def base_part(size: int, rng: random.Random) -> tuple[Image.Image, list, list]:
    """Return (image, plate_box, bolt_positions) with texture + bolts drawn."""
    img = Image.new("RGB", (size, size), BG)
    noise = Image.effect_noise((size, size), 22).convert("RGB")
    img = Image.blend(img, noise, 0.22)

    draw = ImageDraw.Draw(img)
    box = _plate_box(size)
    r = int(size * 0.04)
    draw.rounded_rectangle(box, radius=r, fill=PLATE, outline=PLATE_EDGE, width=3)

    bolts = _bolt_positions(box)
    br = max(4, int(size * 0.018))
    for (bx, by) in bolts:
        draw.ellipse((bx - br, by - br, bx + br, by + br), fill=BOLT)
    return img, box, bolts


# -- defect renderers: each returns list[(class_id, (x0,y0,x1,y1))] -----------

def _surface(img, box, bolts, rng):
    draw = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    cx = rng.randint(int(x0 + (x1 - x0) * 0.2), int(x0 + (x1 - x0) * 0.8))
    cy = rng.randint(int(y0 + (y1 - y0) * 0.2), int(y0 + (y1 - y0) * 0.8))
    span = int((x1 - x0) * rng.uniform(0.15, 0.3))
    bx0 = by0 = 10**9
    bx1 = by1 = -10**9
    for _ in range(rng.randint(3, 6)):
        ang = rng.uniform(0, math.pi)
        ln = span * rng.uniform(0.5, 1.0)
        dx, dy = math.cos(ang) * ln, math.sin(ang) * ln
        sx = cx + rng.randint(-span // 3, span // 3)
        sy = cy + rng.randint(-span // 3, span // 3)
        ex, ey = sx + dx, sy + dy
        draw.line((sx, sy, ex, ey), fill=(40, 40, 44),
                  width=rng.randint(1, 2))
        bx0, by0 = min(bx0, sx, ex), min(by0, sy, ey)
        bx1, by1 = max(bx1, sx, ex), max(by1, sy, ey)
    pad = 6
    return [(CLASS_ID["surface"], (bx0 - pad, by0 - pad, bx1 + pad, by1 + pad))]


def _dimension(img, box, bolts, rng):
    """Chip a corner off the plate (wrong dimension)."""
    draw = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    corner = rng.choice([(x1, y1), (x0, y1), (x1, y0), (x0, y0)])
    size = int((x1 - x0) * rng.uniform(0.12, 0.22))
    cx, cy = corner
    sx = -1 if cx > (x0 + x1) / 2 else 1
    sy = -1 if cy > (y0 + y1) / 2 else 1
    p = [(cx, cy), (cx + sx * size, cy), (cx, cy + sy * size)]
    draw.polygon(p, fill=BG)
    xs = [q[0] for q in p]
    ys = [q[1] for q in p]
    return [(CLASS_ID["dimension"], (min(xs), min(ys), max(xs), max(ys)))]


def _color(img, box, bolts, rng):
    """Discolored blotch (heat/contamination)."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    x0, y0, x1, y1 = box
    w = int((x1 - x0) * rng.uniform(0.15, 0.28))
    h = int(w * rng.uniform(0.6, 1.2))
    bx = rng.randint(int(x0 + (x1 - x0) * 0.15), int(x1 - (x1 - x0) * 0.15) - w)
    by = rng.randint(int(y0 + (y1 - y0) * 0.15), int(y1 - (y1 - y0) * 0.15) - h)
    hue = rng.choice([(176, 92, 40), (60, 100, 150), (150, 60, 130)])
    od.ellipse((bx, by, bx + w, by + h), fill=hue + (130,))
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"),
              (0, 0))
    return [(CLASS_ID["color"], (bx, by, bx + w, by + h))]


def _missing_component(img, box, bolts, rng):
    """Erase one bolt -> missing component, mark its location."""
    draw = ImageDraw.Draw(img)
    bx, by = rng.choice(bolts)
    br = max(6, int(img.size[0] * 0.026))
    draw.ellipse((bx - br, by - br, bx + br, by + br), fill=PLATE)  # cover bolt
    draw.ellipse((bx - br, by - br, bx + br, by + br), outline=(150, 60, 60),
                 width=2)  # red ring = expected-but-missing
    return [(CLASS_ID["missing_component"],
             (bx - br - 4, by - br - 4, bx + br + 4, by + br + 4))]


_RENDERERS = {
    "surface": _surface,
    "dimension": _dimension,
    "color": _color,
    "missing_component": _missing_component,
}


def render_part(size: int, defect_type: str | None, rng: random.Random):
    """Render a part. defect_type=None -> clean part (negative, no labels).

    Returns (PIL.Image, list[(class_id, (x0,y0,x1,y1))]).
    """
    img, box, bolts = base_part(size, rng)
    if not defect_type or defect_type == "none":
        return img, []
    fn = _RENDERERS[defect_type]
    labels = fn(img, box, bolts, rng)
    # clamp boxes to image
    clamped = []
    for cid, (a, b, c, d) in labels:
        a, c = sorted((max(0, a), min(size, c)))
        b, d = sorted((max(0, b), min(size, d)))
        clamped.append((cid, (a, b, c, d)))
    return img, clamped
