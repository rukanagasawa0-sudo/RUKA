"""シーンで使い回す部品。"""
import math

from PIL import Image, ImageDraw

from .render import (H, W, Ctx, card_sprite, clamp, ease_back, ease_in_out, ease_out, lerp,
                     text_sprite, _sprite_cache)

# ワンピースカードの色（イメージ）
COLOR = {
    "赤": (215, 45, 50), "青": (40, 100, 210), "緑": (40, 160, 80), "紫": (130, 60, 180),
    "黒": (45, 45, 55), "黄": (230, 185, 20), "金": (210, 165, 40), "灰": (120, 125, 140),
}


def mix(a, b, k=0.5):
    return tuple(int(lerp(a[i], b[i], k)) for i in range(3))


def color_of(spec):
    """'赤青' のような2色指定は混色ではなく左右に分ける用に2色返す。"""
    cs = [COLOR[c] for c in spec if c in COLOR]
    return cs or [COLOR["灰"]]


def box_sprite(w, h, color, title, code="", accent=(255, 220, 0)):
    """未開封BOX（オリジナル図形）。"""
    key = ("box", w, h, color, title, code)
    if key in _sprite_cache:
        return _sprite_cache[key]
    depth = int(w * 0.18)
    img = Image.new("RGBA", (w + depth + 30, h + depth + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    dark = tuple(int(v * 0.6) for v in color)
    darker = tuple(int(v * 0.45) for v in color)
    ox, oy = 10, depth + 10
    d.polygon([(ox, oy), (ox + depth, oy - depth), (ox + w + depth, oy - depth), (ox + w, oy)], fill=dark)
    d.polygon([(ox + w, oy), (ox + w + depth, oy - depth), (ox + w + depth, oy + h - depth), (ox + w, oy + h)],
              fill=darker)
    d.rectangle((ox, oy, ox + w, oy + h), fill=color)
    d.rectangle((ox, oy + h * 0.08, ox + w, oy + h * 0.2), fill=(255, 255, 255, 70))
    d.rectangle((ox + 14, oy + 14, ox + w - 14, oy + h - 14), outline=(255, 255, 255, 160), width=5)
    size = int(w * 0.14)
    spr = text_sprite(title, size, "dela", fill=(255, 255, 255), stroke=6, stroke_fill=(0, 0, 0))
    while spr.width > w - 36 and size > 20:
        size -= 2
        spr = text_sprite(title, size, "dela", fill=(255, 255, 255), stroke=6, stroke_fill=(0, 0, 0))
    img.alpha_composite(spr, (ox + (w - spr.width) // 2, oy + int(h * 0.3)))
    if code:
        spr = text_sprite(code, int(w * 0.09), "noto", fill=accent, stroke=4, stroke_fill=(0, 0, 0))
        img.alpha_composite(spr, (ox + (w - spr.width) // 2, oy + int(h * 0.74)))
    _sprite_cache[key] = img
    return img


def burst(c, x, y, r, t, color=(255, 230, 80), n=18, alpha=110):
    """回転する放射線。"""
    pts = []
    for i in range(n):
        a0 = t * 0.6 + i * 2 * math.pi / n
        a1 = a0 + math.pi / n * 0.55
        pts = [(x, y), (x + math.cos(a0) * r, y + math.sin(a0) * r), (x + math.cos(a1) * r, y + math.sin(a1) * r)]
        c.d.polygon(pts, fill=color + (alpha,))


def pop_in(t, delay=0.0, dur=0.35):
    return ease_back((t - delay) / dur)


def fade(t, delay=0.0, dur=0.3):
    return ease_out((t - delay) / dur)


def count(t, value, delay=0.0, dur=1.0):
    return value * ease_out((t - delay) / dur)


def yen(v):
    return f"{int(round(v)):,}円"


def shake(t, amp=10, until=0.4, start=0.0):
    if not (start <= t < start + until):
        return 0, 0
    k = 1 - (t - start) / until
    return math.sin(t * 90) * amp * k, math.cos(t * 77) * amp * k


def stamp(c, s, x, y, t, delay, color=(225, 30, 50), size=96, rot=-8):
    if t < delay:
        return
    k = ease_back((t - delay) / 0.25)
    sc = lerp(2.2, 1.0, k)
    c.text(s, x, y, size, scale=sc, alpha=clamp((t - delay) / 0.12), rot=rot, fnt="dela",
           fill=color, stroke=10, stroke_fill=(255, 255, 255))


def cta_panel(c, t, shop, line1, line2, accent=(255, 220, 0), delay=0.0):
    k = ease_back((t - delay) / 0.4)
    if k <= 0:
        return
    y = lerp(1400, 820, k)
    c.panel((70, y - 330, 1010, y + 330), 44, fill=(20, 20, 30, 235), outline=accent + (255,), width=10)
    from config import SHOP_INFO
    c.text(shop, W / 2, y - 240, 72, fnt="dela", fill=accent, stroke=6, max_w=880)
    c.text(line1, W / 2, y - 60, 72, fnt="dela", fill=(255, 255, 255), stroke=6, max_w=880, hl=accent)
    c.text(line2, W / 2, y + 135, 50, fnt="noto", fill=(255, 255, 255), stroke=5, max_w=880, hl=accent)
    c.rrect((110, y + 235, 970, y + 300), 32, fill=accent + (255,))
    c.text(SHOP_INFO, W / 2, y + 266, 36, fnt="noto", fill=(20, 20, 30), max_w=840)
