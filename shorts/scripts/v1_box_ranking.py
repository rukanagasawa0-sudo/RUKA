"""値上がりBOXランキング（ランキング形式・青山龍星＋ずんだもん）。

出典：トレカの地図「ワンピースカード未開封ボックス買取相場」2026/11/13 時点。
"""
from config import CTA_RESERVE, SHOP_NAME
from engine.render import W, Line, Short, ease_back, ease_out, img_sprite, lerp
from engine.widgets import (box_sprite, burst, count, cta_panel, fade, pop_in, shake, stamp,
                            yen)

PACK = {"PRB-01": "box_prb01_01", "OP-11": "box_op11_01", "EB-02": "box_eb02_01",
        "OP-01": "box_op01_01", "OP-05": "box_op05_01"}

DATA = [  # 順位, 名前, 読み, 型番, 定価, 買取, 色
    (5, "ONE PIECE CARD\nTHE BEST", "ワンピースカード・ザ・ベスト", "PRB-01", 5500, 15800, (60, 60, 70)),
    (4, "神速の拳", "しんそくのこぶし", "OP-11", 5280, 19350, (200, 60, 40)),
    (3, "アニメ25周年\nコレクション", "アニメ25周年コレクション", "EB-02", 5280, 19925, (220, 150, 30)),
    (2, "ロマンスドーン", "ロマンスドーン", "OP-01", 4752, 24700, (30, 90, 180)),
    (1, "新時代の主役", "しんじだいのしゅやく", "OP-05", 5280, 32750, (170, 30, 60)),
]


def intro(c, f):
    t = f["t"]
    burst(c, W / 2, 760, 900, t, (255, 220, 60), alpha=60)
    k = pop_in(t, 0.1)
    c.paste(img_sprite("box_op05_01", 560, dim=0.85), W / 2, 720, scale=k)
    c.text("？", W / 2, 700, 260, scale=k, fnt="dela", fill=(255, 255, 255), stroke=12)
    c.text("定価 5,280円", W / 2, 1000, 56, alpha=fade(t, 0.3), fnt="dela", fill=(255, 255, 255), stroke=7)
    if f["li"] >= 2:
        dx, dy = shake(f["lt"], 14, 0.4)
        stamp(c, "定価の6倍超え!?", W / 2 + dx, 1080 + dy, f["lt"], 0.0, size=100)


def rank_scene(rank, name, code, price, buy, color):
    ratio = buy / price

    def draw(c, f):
        t = f["t"]
        k = pop_in(t, 0.0, 0.3)
        if rank == 1:
            burst(c, 300, 720, 700, t, (255, 230, 80), alpha=70)
        # 順位
        c.text(f"第{rank}位", 70, 420, 120, anchor="lm", scale=k, fnt="dela", fill=(255, 230, 80),
               stroke=10, stroke_fill=(0, 0, 0))
        # BOX
        bk = ease_back((t - 0.15) / 0.4)
        c.paste(img_sprite(PACK[code], 500, shine=(t * 0.45) % 1.5,
                           glow=(255, 220, 80) if rank == 1 else None), lerp(-300, 290, bk), 760,
                rot=6 * (1 - bk))
        c.text(code, 290, 990, 34, alpha=fade(t, 0.4), fnt="dela", fill=(255, 255, 255), stroke=5)
        # 定価 → 買取
        a = fade(t, 0.5)
        c.text("定価", 820, 560, 44, fnt="noto", fill=(255, 255, 255), stroke=4, alpha=a)
        c.text(yen(price), 820, 625, 64, fnt="noto", fill=(255, 255, 255), stroke=6, alpha=a)
        c.text("▼", 820, 705, 54, fnt="noto", fill=(255, 230, 80), stroke=4, alpha=a)
        c.text("買取相場", 820, 775, 44, fnt="noto", fill=(255, 255, 255), stroke=4, alpha=fade(t, 0.8))
        v = count(t, buy, 0.8, 1.2)
        c.text(yen(v), 820, 850, 78, fnt="dela", fill=(255, 80, 90), stroke=8, alpha=fade(t, 0.8))
        # 倍率バー
        bw = 940
        c.panel((70, 1010, 70 + bw, 1110), 50, fill=(0, 0, 0, 150), shadow=False)
        p = ease_out((t - 0.8) / 1.2)
        frac = min(1, (ratio * p) / 6.5)
        c.rrect((80, 1020, 80 + max(80, int((bw - 20) * frac)), 1100), 40, fill=(255, 80, 90, 255))
        c.text(f"×{lerp(1, ratio, p):.1f}倍", W / 2, 1060, 72, fnt="dela", fill=(255, 255, 255), stroke=8)

    return draw


def outro(c, f):
    t = f["t"]
    if f["li"] < 2:
        k = pop_in(t, 0.0)
        c.paste(img_sprite("box_op18b", 560, shine=(t * 0.4) % 1.5), W / 2, 700, scale=k)
        stamp(c, "1BOX 5,760円", W / 2, 1080, t, 0.6, color=(255, 200, 40), size=90, rot=-4)
    else:
        cta_panel(c, f["lt"] if f["li"] == 2 else 9, SHOP_NAME, "第18弾 神の支配", CTA_RESERVE)
    c.text("※2026/11/13時点の買取相場（トレカの地図調べ）。相場は日々変動します。",
           W / 2, 1200, 26, fnt="noto", fill=(255, 255, 255), stroke=3, max_w=1000)


def make():
    s = Short("v1_box_ranking", "定価の*6倍*!?\n値上がりBOX TOP5", ((25, 10, 40), (120, 20, 40)),
              bgm="hype", accent=(255, 210, 40))
    s.scene(intro,
            ("ryusei_hot", "定価*5280円*のBOXが、今いくらで買い取られてるか知ってるか？",
             "定価5280円のボックスが、今いくらで買い取られてるか知ってるか？", "whoosh"),
            ("zunda", "え、せいぜい*2倍*くらいなのだ？", "え、せいぜい2倍くらいなのだ？"),
            ("ryusei_hot", "甘い！買取価格が*定価の何倍か*、ランキングで見ていくぞ！", None, "impact"))
    for rank, name, say, code, price, buy, color in DATA:
        ratio = buy / price
        lines = [Line("ryusei_hot", f"第{rank}位！*{name.replace(chr(10), '')}*",
                      f"第{rank}位！{say}！", "drumroll+impact" if rank <= 2 else "pop")]
        if rank == 5:
            lines.append(Line("zunda", f"定価5500円が*{yen(buy)}*！？", f"定価5500円が、{buy}円！？"))
        if rank == 4:
            lines.append(Line("zunda", "ルフィの*金のSP*が入ってる弾なのだ！", "ルフィの金のエスピーが入ってる弾なのだ！"))
        if rank == 2:
            lines.append(Line("zunda", f"記念すべき*第1弾*！約{ratio:.1f}倍なのだ！", f"記念すべき第1弾！約{ratio:.1f}倍なのだ！"))
        if rank == 1:
            lines.append(Line("ryusei_hot", f"定価5280円が…*{yen(buy)}*！約*{ratio:.1f}倍*だ！",
                              f"定価5280円が、{buy}円！約{ratio:.1f}倍だ！", "kira"))
            lines.append(Line("zunda_namida", "なんで当時買っておかなかったのだ……"))
        s.scene(rank_scene(rank, name, code, price, buy, color), *lines, min_dur=3.0)
    s.scene(outro,
            ("ryusei", "そして*11月21日*、第18弾*神の支配*が発売！", "そして11月21日、第18弾、かみのしはいが発売！", "whoosh"),
            ("zunda", "今度こそ*発売日に確保*しておくのだ！"),
            ("ryusei_hot", "君が持ってるBOXも*コメント*で教えてくれ！", None, "ding", 0.12, 0.8))
    return s
