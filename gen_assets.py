"""
Generates the Play Store icon (512x512) and feature graphic (1024x500) for
Trading Signals, using the app's existing "Vault" palette (see
android-app/app/src/main/java/.../ui/theme/Color.kt) so the store presence
actually matches what's inside the app.

Mark concept: a gold ring with clock/dial ticks (the "vault door") holding a
bold ascending chevron (the trend) at its center. Gold is chrome only, never
direction — consistent with how the app itself uses it.
"""

import math
from PIL import Image, ImageDraw, ImageFont

# --- palette (exact hex from Color.kt) --------------------------------------
VAULT_BLACK = (10, 13, 18)
PANEL_DARK = (18, 22, 29)
GOLD = (198, 162, 77)
GOLD_HAIRLINE = (107, 86, 40)
TEXT_PRIMARY = (232, 234, 237)
TEXT_SECONDARY = (138, 147, 162)
MINT = (52, 211, 153)
CORAL = (251, 107, 107)

FONT_DIR = "C:/Windows/Fonts/"
SS = 4  # supersample factor for anti-aliasing


def vault_bg(size_w, size_h):
    """Subtle diagonal depth: vault black toward one corner, panel dark toward
    the other — never flat, never a loud gradient."""
    img = Image.new("RGB", (size_w, size_h), VAULT_BLACK)
    px = img.load()
    for y in range(size_h):
        for x in range(0, size_w, 2):  # step 2, fill pairs — cheap + plenty smooth
            t = (x / size_w * 0.6 + y / size_h * 0.4)
            r = round(VAULT_BLACK[0] + (PANEL_DARK[0] - VAULT_BLACK[0]) * t)
            g = round(VAULT_BLACK[1] + (PANEL_DARK[1] - VAULT_BLACK[1]) * t)
            b = round(VAULT_BLACK[2] + (PANEL_DARK[2] - VAULT_BLACK[2]) * t)
            px[x, y] = (r, g, b)
            if x + 1 < size_w:
                px[x + 1, y] = (r, g, b)
    return img


def draw_mark(draw, cx, cy, r, ring_color=GOLD, mark_color=GOLD, ticks=12,
              ring_width=None, tick_len=None, chevron_scale=1.0):
    """Ring with dial ticks + a bold ascending chevron at the center."""
    if ring_width is None:
        ring_width = max(2, round(r * 0.075))
    if tick_len is None:
        tick_len = r * 0.16

    # Ring
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ring_color, width=ring_width)

    # Dial ticks around the outside of the ring
    tick_w = max(1, round(ring_width * 0.6))
    for i in range(ticks):
        a = (i / ticks) * 2 * math.pi - math.pi / 2
        inner = r + ring_width * 0.9
        outer = inner + tick_len
        x1, y1 = cx + inner * math.cos(a), cy + inner * math.sin(a)
        x2, y2 = cx + outer * math.cos(a), cy + outer * math.sin(a)
        draw.line([x1, y1, x2, y2], fill=ring_color, width=tick_w)

    # Ascending chevron — a flat-ish first leg into a sharp breakout leg, like
    # a chart catching a trend, not a straight needle. The elbow has to be a
    # real angle change or it just reads as one diagonal line.
    s = r * 0.56 * chevron_scale
    p0 = (cx - s, cy + s * 0.30)
    p1 = (cx - s * 0.15, cy + s * 0.10)
    p2 = (cx + s * 0.95, cy - s * 0.95)
    stroke = max(3, round(r * 0.15))
    for a, b in [(p0, p1), (p1, p2)]:
        draw.line([a, b], fill=mark_color, width=stroke, joint="curve")
    for pt in (p0, p1, p2):
        rr = stroke / 2
        draw.ellipse([pt[0] - rr, pt[1] - rr, pt[0] + rr, pt[1] + rr], fill=mark_color)
    # Arrowhead at the top end
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    head = stroke * 1.6
    left = (p2[0] - head * math.cos(ang - math.radians(28)), p2[1] - head * math.sin(ang - math.radians(28)))
    right = (p2[0] - head * math.cos(ang + math.radians(28)), p2[1] - head * math.sin(ang + math.radians(28)))
    draw.polygon([p2, left, right], fill=mark_color)


def make_icon(path, size=512):
    hi = size * SS
    img = vault_bg(hi, hi)
    draw = ImageDraw.Draw(img)
    cx = cy = hi / 2
    r = hi * 0.30
    draw_mark(draw, cx, cy, r)
    img = img.resize((size, size), Image.LANCZOS)
    img.save(path)
    print(f"wrote {path} ({size}x{size})")


def make_feature_graphic(path, w=1024, h=500):
    hi_w, hi_h = w * SS, h * SS
    img = vault_bg(hi_w, hi_h)
    draw = ImageDraw.Draw(img)

    # Faint ascending hairline, confined to the lower band under the text —
    # floor-level atmosphere, never crossing behind the headline.
    pts = [(0, hi_h * 0.94), (hi_w * 0.4, hi_h * 0.90), (hi_w * 0.68, hi_h * 0.92),
           (hi_w * 0.85, hi_h * 0.80), (hi_w, hi_h * 0.83)]
    draw.line(pts, fill=GOLD_HAIRLINE, width=max(1, round(hi_h * 0.0025)), joint="curve")

    # Mark, left side — fully inset, never bleeding off the canvas edge.
    r = hi_h * 0.27
    cx, cy = r * 1.35, hi_h * 0.5
    draw_mark(draw, cx, cy, r, ticks=10)

    # Wordmark + tagline, right of the mark. Font size is fit to the
    # available width rather than fixed, so the title never runs off the
    # right edge of the canvas.
    text_x = cx + r * 1.5
    max_title_w = hi_w - text_x - hi_w * 0.035

    title = "Trading Signals"
    title_size = int(hi_h * 0.155)
    title_font = ImageFont.truetype(FONT_DIR + "georgiab.ttf", title_size)
    while title_size > 10:
        bbox = draw.textbbox((0, 0), title, font=title_font)
        if bbox[2] - bbox[0] <= max_title_w:
            break
        title_size -= 4
        title_font = ImageFont.truetype(FONT_DIR + "georgiab.ttf", title_size)

    tag_font = ImageFont.truetype(FONT_DIR + "segoeui.ttf", int(hi_h * 0.062))

    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_h = bbox[3] - bbox[1]
    title_y = hi_h * 0.36 - title_h
    draw.text((text_x, title_y), title, font=title_font, fill=TEXT_PRIMARY)

    tag = "Live gold signals, delivered instantly"
    draw.text((text_x, hi_h * 0.60), tag, font=tag_font, fill=TEXT_SECONDARY)

    # BUY / SELL chips echoing the in-app card system
    chip_font = ImageFont.truetype(FONT_DIR + "segoeuib.ttf", int(hi_h * 0.052))

    def chip(x, y, label, color):
        pad_x, pad_y = int(hi_h * 0.028), int(hi_h * 0.018)
        bbox = draw.textbbox((0, 0), label, font=chip_font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        w_box, h_box = tw + pad_x * 2, th + pad_y * 2
        radius = h_box / 2
        draw.rounded_rectangle([x, y, x + w_box, y + h_box], radius=radius,
                                fill=None, outline=color, width=max(2, int(hi_h * 0.006)))
        draw.text((x + pad_x, y + pad_y - bbox[1]), label, font=chip_font, fill=color)
        return w_box

    chip_y = hi_h * 0.755
    w0 = chip(text_x, chip_y, "BUY  \u25B2", MINT)
    chip(text_x + w0 + hi_w * 0.02, chip_y, "SELL  \u25BC", CORAL)

    img = img.resize((w, h), Image.LANCZOS)
    img.save(path)
    print(f"wrote {path} ({w}x{h})")


if __name__ == "__main__":
    import os
    out = os.path.dirname(os.path.abspath(__file__))
    make_icon(os.path.join(out, "play-icon-512.png"))
    make_feature_graphic(os.path.join(out, "feature-graphic-1024x500.png"))
