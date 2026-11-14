"""v2（神の支配まとめ）のサムネイルを作る。 python3 shorts/thumbs/make_thumb_v2.py"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from PIL import Image, ImageDraw  # noqa: E402

from config import SHOP_NAME  # noqa: E402
from engine.render import Ctx, img_sprite, text_sprite  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "output")


def background(w, h):
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    top, bot = (45, 12, 50), (200, 60, 120)
    for y in range(h):
        k = y / h
        d.line((0, y, w, y), fill=tuple(int(top[i] * (1 - k) + bot[i] * k) for i in range(3)) + (255,))
    # 放射線
    cx, cy = w / 2, h * 0.45
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    r = max(w, h) * 1.2
    for i in range(22):
        a0 = i * 2 * math.pi / 22
        a1 = a0 + math.pi / 22 * 0.55
        od.polygon([(cx, cy), (cx + math.cos(a0) * r, cy + math.sin(a0) * r),
                    (cx + math.cos(a1) * r, cy + math.sin(a1) * r)], fill=(255, 200, 230, 55))
    img.alpha_composite(ov)
    return img


def vertical():
    W, H = 1080, 1920
    img = background(W, H)
    c = Ctx(img)
    # 上：大きな見出し
    c.text("新弾", W / 2, 190, 120, fnt="dela", fill=(255, 230, 80), stroke=10)
    c.text("神の支配", W / 2, 380, 220, fnt="dela", fill=(255, 255, 255), stroke=14, stroke_fill=(120, 20, 60))
    # 中央：BOX と 天野パラレル2枚
    c.paste(img_sprite("cards/amano_OP18-119", 640, glow=(255, 230, 120)), 255, 900, rot=10)
    c.paste(img_sprite("cards/amano_OP17-119", 640, glow=(255, 230, 120)), 825, 900, rot=-10)
    c.paste(img_sprite("box_op18b", 780), W / 2, 950)
    # 下：フック
    c.rrect((50, 1400, 1030, 1720), 60, fill=(255, 255, 255, 245), outline=(233, 84, 140, 255), width=12)
    c.text("買う前に\n*これだけ見て！*", W / 2, 1560, 112, fnt="dela", fill=(30, 30, 30), hl=(225, 30, 50))
    # 発売日バッジ
    c.d.ellipse((780, 1250, 1060, 1530), fill=(225, 30, 50, 255), outline=(255, 255, 255), width=10)
    c.text("11/21\n発売", 920, 1390, 72, fnt="dela", fill=(255, 255, 255), rot=-8)
    c.text(SHOP_NAME, W / 2, 1810, 64, fnt="dela", fill=(255, 255, 255), stroke=6)
    out = os.path.join(OUT, "v2_thumbnail_1080x1920.png")
    img.convert("RGB").save(out)
    return out


def horizontal():
    W, H = 1280, 720
    img = background(W, H)
    c = Ctx(img)
    c.paste(img_sprite("cards/amano_OP18-119", 440, glow=(255, 230, 120)), 790, 420, rot=9)
    c.paste(img_sprite("cards/amano_OP17-119", 440, glow=(255, 230, 120)), 930, 440, rot=-3)
    c.paste(img_sprite("box_op18b", 560), 1120, 420)
    c.text("新弾", 260, 110, 90, fnt="dela", fill=(255, 230, 80), stroke=8)
    c.text("神の支配", 320, 270, 150, fnt="dela", fill=(255, 255, 255), stroke=12, stroke_fill=(120, 20, 60))
    c.rrect((30, 400, 660, 640), 46, fill=(255, 255, 255, 245), outline=(233, 84, 140, 255), width=10)
    c.text("買う前に\n*これだけ見て！*", 345, 520, 84, fnt="dela", fill=(30, 30, 30), hl=(225, 30, 50))
    c.d.ellipse((560, 30, 740, 210), fill=(225, 30, 50, 255), outline=(255, 255, 255), width=8)
    c.text("11/21\n発売", 650, 120, 48, fnt="dela", fill=(255, 255, 255), rot=-8)
    out = os.path.join(OUT, "v2_thumbnail_1280x720.png")
    img.convert("RGB").save(out)
    return out


if __name__ == "__main__":
    print(vertical())
    print(horizontal())
