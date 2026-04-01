"""Generate email icon PNGs — 176x176 (2x retina for 88pt display)."""

import math
import os
from PIL import Image, ImageDraw

SIZE = 176
R = 40  # corner radius (2x)
BG = (253, 243, 228)        # #FDF3E4
AMBER = (234, 166, 70)      # #EAA646
AMBER_DARK = (232, 146, 74) # #E8924A
AMBER_LIGHT = (234, 166, 70, 60)
WHITE = (255, 255, 255)
CREAM = (253, 248, 240)

OUT = os.path.dirname(__file__)


def rounded_rect_mask(size, radius):
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return mask


def new_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    bg = Image.new("RGBA", (SIZE, SIZE), BG)
    mask = rounded_rect_mask((SIZE, SIZE), R)
    img.paste(bg, mask=mask)
    return img, ImageDraw.Draw(img)


def draw_capsule():
    img, d = new_icon()

    # Capsule body (pill shape)
    cx, cy = SIZE // 2, SIZE // 2
    pw, ph = 56, 90
    px, py = cx - pw // 2, cy - ph // 2

    # Outer capsule
    d.rounded_rectangle([px, py, px + pw, py + ph], radius=pw // 2, outline=AMBER, width=4)

    # Band across middle
    d.line([(px, cy), (px + pw, cy)], fill=AMBER, width=4)

    # Lock circle on top half
    lock_cy = cy - 16
    d.ellipse([cx - 7, lock_cy - 7, cx + 7, lock_cy + 7], fill=AMBER)
    # Lock body below
    d.rounded_rectangle([cx - 5, lock_cy + 2, cx + 5, lock_cy + 14], radius=2, fill=AMBER)

    # Keyhole
    d.ellipse([cx - 2, lock_cy - 2, cx + 2, lock_cy + 2], fill=BG)
    d.rectangle([cx - 1, lock_cy + 1, cx + 1, lock_cy + 6], fill=BG)

    # Sparkles
    for sx, sy, sr in [(140, 36, 5), (150, 50, 3), (130, 28, 3)]:
        d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=AMBER_DARK + (140,))

    # Small time chevron at bottom
    bcy = cy + 28
    pts = [(cx - 14, bcy + 6), (cx, bcy - 4), (cx + 14, bcy + 6)]
    d.line(pts, fill=AMBER_DARK + (160,), width=3, joint="curve")

    # Apply mask
    final = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    mask = rounded_rect_mask((SIZE, SIZE), R)
    final.paste(img, mask=mask)
    final.save(os.path.join(OUT, "icon-capsule.png"))
    print("Generated icon-capsule.png")


def draw_globe():
    img, d = new_icon()
    cx, cy = SIZE // 2, SIZE // 2
    r = 44

    # Filled light circle background
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CREAM)

    # Land masses (soft blobs)
    for lx, ly, lr, alpha in [
        (cx - 14, cy - 16, 14, 50), (cx + 12, cy + 8, 16, 40),
        (cx - 18, cy + 12, 10, 40), (cx + 4, cy - 24, 8, 35),
    ]:
        d.ellipse([lx - lr, ly - lr, lx + lr, ly + lr], fill=AMBER + (alpha,))

    # Equator
    d.ellipse([cx - r, cy - 14, cx + r, cy + 14], outline=AMBER + (100,), width=2)

    # Meridian
    d.ellipse([cx - 14, cy - r, cx + 14, cy + r], outline=AMBER + (100,), width=2)

    # Outer ring
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=AMBER, width=4)

    # Connection dots
    for dx, dy in [(-12, -14), (14, 10)]:
        px, py = cx + dx, cy + dy
        d.ellipse([px - 5, py - 5, px + 5, py + 5], fill=AMBER_DARK)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=WHITE)

    # Dashed connection line
    x1, y1, x2, y2 = cx - 12, cy - 14, cx + 14, cy + 10
    steps = 12
    for i in range(steps):
        if i % 2 == 0:
            t1, t2 = i / steps, (i + 1) / steps
            lx1 = x1 + (x2 - x1) * t1
            ly1 = y1 + (y2 - y1) * t1
            lx2 = x1 + (x2 - x1) * t2
            ly2 = y1 + (y2 - y1) * t2
            d.line([(lx1, ly1), (lx2, ly2)], fill=AMBER_DARK + (130,), width=2)

    final = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    mask = rounded_rect_mask((SIZE, SIZE), R)
    final.paste(img, mask=mask)
    final.save(os.path.join(OUT, "icon-globe.png"))
    print("Generated icon-globe.png")


def draw_timeline():
    img, d = new_icon()

    # Trail waypoints (bottom-left to top-right)
    points = [(36, 140), (56, 110), (76, 96), (100, 76), (120, 52)]

    # Draw dashed trail
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        dist = math.hypot(x2 - x1, y2 - y1)
        segs = int(dist / 8)
        for s in range(segs):
            if s % 2 == 0:
                t1 = s / segs
                t2 = min((s + 1) / segs, 1.0)
                d.line([
                    (x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1),
                    (x1 + (x2 - x1) * t2, y1 + (y2 - y1) * t2),
                ], fill=AMBER + (160,), width=3)

    # Waypoint dots along trail
    for i, (px, py) in enumerate(points[:-1]):
        alpha = 80 + i * 40
        sr = 5 + i
        d.ellipse([px - sr, py - sr, px + sr, py + sr], fill=AMBER + (min(alpha, 200),))
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=AMBER + (min(alpha + 40, 240),))

    # Location pin at the end
    pin_x, pin_y = points[-1]
    pin_w, pin_h = 28, 36

    # Pin shadow
    d.ellipse([pin_x - 8, pin_y + 14, pin_x + 8, pin_y + 18], fill=AMBER_DARK + (50,))

    # Pin body
    pin_top = pin_y - 12
    # Draw pin as polygon + circle
    d.polygon([
        (pin_x, pin_y + 12),
        (pin_x - 14, pin_top),
        (pin_x + 14, pin_top),
    ], fill=AMBER_DARK)
    d.ellipse([pin_x - 14, pin_top - 14, pin_x + 14, pin_top + 14], fill=AMBER_DARK)

    # Pin inner circle (white)
    d.ellipse([pin_x - 7, pin_top - 7, pin_x + 7, pin_top + 7], fill=WHITE)

    # Pin center dot
    d.ellipse([pin_x - 3, pin_top - 3, pin_x + 3, pin_top + 3], fill=AMBER_DARK)

    final = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    mask = rounded_rect_mask((SIZE, SIZE), R)
    final.paste(img, mask=mask)
    final.save(os.path.join(OUT, "icon-timeline.png"))
    print("Generated icon-timeline.png")


if __name__ == "__main__":
    draw_capsule()
    draw_globe()
    draw_timeline()
    print("Done!")
