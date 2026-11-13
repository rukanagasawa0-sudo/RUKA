"""新弾「神の支配」30秒まとめ（チェックリスト形式・四国めたん＋春日部つむぎ）。

出典：ONE PIECE.com 公式ニュース(2026/11/6)、GameWith系まとめ（収録カードリスト）。
"""
import math

from config import CTA_RESERVE, SHOP_NAME
from engine.render import W, card_sprite, ease_back, img_sprite, lerp, text_sprite
from engine.render import Short
from engine.widgets import COLOR, box_sprite, burst, cta_panel, fade, pop_in, stamp

LEADERS = ["OP18-001", "OP18-022", "OP18-021", "OP18-041", "OP18-060", "OP18-079"]


def chip(c, n, label, y, t):
    k = pop_in(t, 0, 0.3)
    c.panel((60, y - 60, 1020, y + 60), 60, fill=(255, 255, 255, 235))
    c.d.ellipse((75, y - 48, 171, y + 48), fill=(233, 84, 140))
    c.text(str(n), 123, y, 60, fnt="dela", fill=(255, 255, 255))
    c.text(label, 200, y, 58, anchor="lm", fnt="noto", fill=(40, 40, 40), hl=(233, 84, 140),
           align="left", scale=k)


def intro(c, f):
    t = f["t"]
    burst(c, W / 2, 760, 900, t, (255, 140, 190), alpha=50)
    k = pop_in(t, 0.05)
    c.paste(img_sprite("box_op18b", 580, shine=(t * 0.4) % 1.5), W / 2, 700, scale=k,
            rot=math.sin(t * 2) * 3)
    stamp(c, "11/21(土)発売", W / 2, 1060, t, 0.5, color=(233, 84, 140), size=96, rot=-5)


def point1(c, f):
    t = f["t"]
    chip(c, 1, "*1パック240円*（税込）", 480, t)
    if t > 0.6:
        chip(c, 2, "1BOX 24パック *5,760円*", 680, t - 0.6)
    if f["li"] >= 1:
        lt = t - (f["scene"].lines[1].start - f["scene"].start)
        chip(c, 3, "テーマは *ウォーターセブン*", 880, lt)
    if f["li"] >= 2:
        stamp(c, "フランキー！ロビン！", W / 2, 1090, f["lt"], 0, color=(245, 160, 40), size=80, rot=-3)


def point2(c, f):
    t = f["t"]
    c.text("リーダーは*6種*", W / 2, 410, 84, fnt="dela", fill=(255, 255, 255), stroke=8, hl=(255, 220, 0))
    for i, cid in enumerate(LEADERS):
        k = ease_back((t - 0.15 - i * 0.18) / 0.35)
        x = 200 + (i % 3) * 340
        y = 655 + (i // 3) * 340
        spr = img_sprite("cards/" + cid, 310, shine=(t * 0.5 + i * 0.1) % 1.5,
                         glow=(255, 220, 0) if cid == "OP18-001" and f["li"] >= 1 else None)
        c.paste(spr, x, y, scale=k)


def point3(c, f):
    t = f["t"]
    burst(c, W / 2, 760, 900, t, (255, 230, 120), alpha=45)
    c.text("シークレットレア", W / 2, 410, 84, fnt="dela", fill=(255, 230, 80), stroke=8)
    for i, cid in enumerate(["OP18-118", "OP18-119"]):
        k = ease_back((t - 0.2 - i * 0.25) / 0.4)
        spr = img_sprite("cards/" + cid, 520, shine=(t * 0.5 + i * 0.4) % 1.6, glow=(255, 230, 120))
        c.paste(spr, 290 + i * 500, 760, scale=k, rot=(5 if i == 0 else -5) * k)
    if f["li"] >= 1:
        lt = t - (f["scene"].lines[1].start - f["scene"].start)
        c.panel((70, 1060, 1010, 1190), 40, fill=(20, 20, 30, 225), shadow=False)
        c.text("さらに *天野喜孝* 描き下ろしパラレルも！", W / 2, 1125, 50, fnt="noto", fill=(255, 255, 255),
               hl=(255, 220, 0), alpha=fade(lt))


def outro(c, f):
    t = f["t"]
    cta_panel(c, t, SHOP_NAME, "11/21(土)\n神の支配 発売！", CTA_RESERVE, accent=(255, 140, 190))
    c.text("※情報は2026/11/13時点。詳細は公式サイトをご確認ください。", W / 2, 1200, 26, fnt="noto",
           fill=(255, 255, 255), stroke=3, max_w=1000)


def make():
    s = Short("v2_op18_summary", "新弾*神の支配*\n買う前にこれだけ見て！", ((60, 20, 60), (200, 70, 120)),
              bgm="pop", accent=(255, 200, 230))
    s.scene(intro,
            ("tsumugi", "ねえねえ！来週発売の*新弾*、もうチェックした？", None, "whoosh"),
            ("metan", "*11月21日*発売の第18弾、*神の支配*。要点をサクッとまとめるわよ！",
             "11月21日発売の、第18弾、かみのしはい。要点をサクッとまとめるわよ！", "impact"))
    s.scene(point1,
            ("metan", "価格は*1パック240円*、1BOXは*5760円*。", "価格は1パック240円、1ボックスは5760円。", "pop"),
            ("metan", "テーマはなんと*ウォーターセブン編*！", "テーマはなんと、ウォーターセブン編！", "pop"),
            ("tsumugi", "やばっ！フランキーとかロビンの回じゃん！", None, "ding"))
    s.scene(point2,
            ("metan", "リーダーは*6種*。ルフィやフランキーに加えて……", "リーダーは6種。ルフィやフランキーに加えて", "whoosh"),
            ("tsumugi", "*カルー*がリーダー！？それは推せる〜！", "カルーがリーダー！？それは推せるー！", "pop"))
    s.scene(point3,
            ("metan", "シークレットは*ルフィ*と*シャムロック聖*！", "シークレットは、ルフィと、シャムロックせい！", "kira"),
            ("metan", "さらに*天野喜孝さん*の描き下ろしパラレルも収録！", "さらに、天野よしたかさんの描き下ろしパラレルも収録！", "pop"),
            ("tsumugi", "それ絶対*神引き*したいやつ……！", "それ絶対、神引きしたいやつ！"))
    s.scene(outro,
            ("metan", "発売日に後悔しないように、*保存*して見返してね。", "発売日に後悔しないように、保存して見返してね。", "whoosh"),
            ("tsumugi", "みんなは*どのリーダー*使う？コメントで教えて〜！", "みんなは、どのリーダー使う？コメントで教えてー！", "ding", 0.12, 0.8))
    return s
