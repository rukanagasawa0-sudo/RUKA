"""公式カード画像からデッキリスト画像（1080×1080）を組む。

python3 shorts/tools/make_decklist.py mihawk
デッキ定義は DECKS に書く（カード番号: 枚数）。カード情報は assets/decks/<name>_cards.json（tools/cardlist.py で取得）。
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw  # noqa: E402

from engine.render import font, text_sprite  # noqa: E402

DECKS = {
    "mihawk": dict(
        title="ジュラキュール・ミホーク", color=(40, 150, 90), note="禁止前の構成（2026年9月）",
        leader="OP14-020",
        cards={"OP12-034": 4, "OP07-022": 4, "ST32-001": 4, "OP06-033": 4, "OP12-023": 4, "ST32-002": 4,
               "OP13-031": 3, "ST32-003": 3, "ST24-004": 3, "OP17-022": 3, "OP01-055": 4, "OP06-038": 4,
               "OP12-037": 2, "OP08-036": 2, "OP14-039": 2},
        badge="10/12〜 禁止",
    ),
}

CARD_DIR = os.path.join(HERE, "assets", "official", "cards")
S = 1080


def rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im, (0, 0), m)
    return out


def card_img(cid, w):
    im = Image.open(os.path.join(CARD_DIR, cid + ".png")).convert("RGBA")
    h = int(im.height * w / im.width)
    return rounded(im.resize((w, h), Image.LANCZOS), max(4, w // 22))


def build(name):
    d = DECKS[name]
    info = json.load(open(os.path.join(HERE, "assets", "decks", f"{name}_cards.json")))
    col = d["color"]
    img = Image.new("RGB", (S, S), (14, 22, 34))   # RGB にして半透明の塗りを正しく重ねる
    dr = ImageDraw.Draw(img, "RGBA")
    for y in range(S):  # うっすらデッキ色のグラデ
        k = y / S
        dr.line((0, y, S, y), fill=(int(14 + col[0] * 0.18 * k), int(22 + col[1] * 0.18 * k), int(34 + col[2] * 0.18 * k), 255))
    dr.rounded_rectangle((16, 16, S - 16, S - 16), 28, outline=(255, 255, 255, 40), width=2)

    # ヘッダー：リーダー＋名前
    leader = card_img(d["leader"], 158)
    img.paste(leader, (52, 46), leader)
    dr.text((252, 56), "ONE PIECEカードゲーム", font=font("noto", 22), fill=(200, 210, 225))
    dr.text((250, 88), d["title"], font=font("noto", 54), fill=(255, 255, 255))
    total = sum(d["cards"].values())
    dr.ellipse((254, 172, 276, 194), fill=col)
    dr.text((288, 166), f"{total} 枚", font=font("noto", 26), fill=(230, 235, 245))
    nw = int(font("noto", 22).getlength(d["note"]))
    dr.rounded_rectangle((252, 210, 252 + nw + 28, 248), 19, fill=(255, 255, 255, 34))
    dr.text((266, 213), d["note"], font=font("noto", 22), fill=(230, 235, 245))
    if d.get("badge"):
        b = text_sprite(d["badge"], 34, "dela", fill=(255, 255, 255))
        bw = b.width + 40
        dr.rounded_rectangle((S - 52 - bw, 168, S - 52, 230), 31, fill=(225, 30, 50))
        img.paste(b, (S - 52 - bw + 20, 199 - b.height // 2), b)

    # カード一覧（コスト順、キャラ→イベント→ステージ）
    order = {"CHARACTER": 0, "EVENT": 1, "STAGE": 2}
    ids = sorted(d["cards"], key=lambda c: (order.get(info[c]["type"], 3), int(info[c]["cost"] or 0), c))
    per_row, gap = 8, 8
    cw = (S - 104 - gap * (per_row - 1)) // per_row
    x0 = (S - (cw * per_row + gap * (per_row - 1))) // 2
    y = 284
    ch = int(cw * 838 / 600)
    badge_f = font("noto", 26)
    for i, cid in enumerate(ids):
        r, cpos = divmod(i, per_row)
        x = x0 + cpos * (cw + gap)
        yy = y + r * (ch + 12)
        dr.rounded_rectangle((x + 3, yy + 5, x + cw + 3, yy + ch + 5), 8, fill=(0, 0, 0, 120))
        ci = card_img(cid, cw)
        img.paste(ci, (x, yy), ci)
        n = f"×{d['cards'][cid]}"
        dr.rounded_rectangle((x + cw - 56, yy + ch - 42, x + cw - 5, yy + ch - 6), 9,
                             fill=(20, 30, 50, 235), outline=(255, 255, 255, 200), width=2)
        dr.text((x + cw - 30, yy + ch - 24), n, font=badge_f, fill=(255, 255, 255), anchor="mm")

    # 下：統計
    rows = (len(ids) + per_row - 1) // per_row
    top = y + rows * (ch + 12) + 14
    dr.rounded_rectangle((52, top, S - 52, S - 40), 22, fill=(255, 255, 255, 18), outline=(255, 255, 255, 40), width=2)
    costs = Counter()
    types = Counter()
    counters = Counter()
    for cid, n in d["cards"].items():
        c = info[cid]
        costs[int(c["cost"] or 0)] += n
        types[c["type"]] += n
        counters[c["counter"] if c["counter"] not in ("", "-") else "none"] += n
    avg = sum(k * v for k, v in costs.items()) / total
    f22, f26, f30 = font("noto", 20), font("noto", 22), font("noto", 26)
    dr.text((80, top + 18), "コストカーブ", font=f26, fill=(200, 210, 225))
    dr.text((420, top + 18), f"平均 {avg:.1f}", font=f26, fill=(200, 210, 225), anchor="ra")
    base = S - 84
    mx = max(costs.values())
    for i in range(11):
        v = costs.get(i, 0)
        bx = 82 + i * 31
        hgt = int((base - top - 90) * v / mx) if v else 0
        if v:
            dr.rectangle((bx, base - hgt, bx + 20, base), fill=col + (255,))
            dr.text((bx + 10, base - hgt - 6), str(v), font=f22, fill=(255, 255, 255), anchor="mb")
        dr.text((bx + 10, base + 8), "10+" if i == 10 else str(i), font=font("noto", 18), fill=(180, 190, 205), anchor="mt")
    dr.text((520, top + 18), "種類", font=f26, fill=(200, 210, 225))
    for j, (k, lab) in enumerate([("CHARACTER", "キャラ"), ("EVENT", "イベント"), ("STAGE", "ステージ")]):
        yy = top + 66 + j * 44
        dr.text((600, yy), str(types.get(k, 0)), font=f30, fill=(255, 255, 255), anchor="ra")
        dr.text((616, yy + 2), lab, font=f26, fill=(220, 225, 235))
    dr.text((760, top + 18), "カウンター", font=f26, fill=(200, 210, 225))
    for j, (k, lab) in enumerate([("1000", "+1000"), ("2000", "+2000"), ("none", "カウンター無")]):
        yy = top + 66 + j * 44
        dr.text((830, yy), str(counters.get(k, 0)), font=f30, fill=(255, 255, 255), anchor="ra")
        dr.text((846, yy + 2), lab, font=f26, fill=(220, 225, 235))
    out = os.path.join(HERE, "assets", "decks", f"deck_{name}.png")
    img.save(out)   # RGB
    print(out, f"avg={avg:.2f}", dict(costs), dict(types), dict(counters))
    return out


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "mihawk")
