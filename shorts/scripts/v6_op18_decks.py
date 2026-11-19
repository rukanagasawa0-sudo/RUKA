"""新弾「神の支配」新リーダー5種のデッキレシピ紹介（九州そら＝司会、ずんだもん＝Aさん）。

デッキ画像：OPLAY TCG で作成されたもの（ユーザー提供・2026/11/17）。
数値（平均コスト・カウンター枚数など）は各デッキ画像に書かれている値。
"""
import os

from PIL import Image, ImageDraw

from config import CTA_RESERVE, SHOP_NAME
from engine.render import ROOT, W, Line, Short, ease_back, ease_in_out, img_sprite, lerp, text_sprite
from engine.widgets import burst, cta_panel, fade, pop_in

DECK_DIR = os.path.join(ROOT, "assets", "decks")
AREA = (40, 345, 1040, 1180)          # デッキ画像を映す枠（字幕の上まで）
AW, AH = AREA[2] - AREA[0], AREA[3] - AREA[1]
FULL = (540, 540, AH / 1080)          # 全体表示（中心x, 中心y, 倍率）

_img_cache, _mask = {}, None


def deck_img(name):
    if name not in _img_cache:
        _img_cache[name] = Image.open(os.path.join(DECK_DIR, f"deck_{name}.png")).convert("RGBA")
    return _img_cache[name]


def area_mask():
    global _mask
    if _mask is None:
        _mask = Image.new("L", (AW, AH), 0)
        ImageDraw.Draw(_mask).rounded_rectangle((0, 0, AW - 1, AH - 1), 36, fill=255)
    return _mask


def view(c, name, focus):
    """focus=(cx, cy, s) の範囲を枠いっぱいに映す。"""
    cx, cy, s = focus
    sw, sh = AW / s, AH / s
    x0, y0 = cx - sw / 2, cy - sh / 2
    # 画像からはみ出さないよう寄せる（画像より広い時は中央）
    x0 = (1080 - sw) / 2 if sw >= 1080 else min(max(0, x0), 1080 - sw)
    y0 = (1080 - sh) / 2 if sh >= 1080 else min(max(0, y0), 1080 - sh)
    src = deck_img(name).crop((int(x0), int(y0), int(x0 + sw), int(y0 + sh)))
    frame = Image.new("RGBA", (AW, AH), (14, 22, 40, 255))
    frame.alpha_composite(src.resize((AW, AH), Image.BILINEAR))
    c.d.rounded_rectangle((AREA[0] + 8, AREA[1] + 12, AREA[2] + 8, AREA[3] + 12), 36, fill=(0, 0, 0, 90))
    c.img.paste(frame, (AREA[0], AREA[1]), area_mask())
    c.d.rounded_rectangle(AREA, 36, outline=(255, 255, 255, 255), width=6)


def deck_scene(no, name, label, color, focuses, callouts=()):
    """focuses: セリフごとの注目位置（None なら全体）。callouts: セリフごとに大きく出す要点（None なら無し）。"""
    def draw(c, f):
        t, li = f["t"], max(0, f["li"])
        cur = focuses[li] or FULL
        prev = (focuses[li - 1] or FULL) if li > 0 else FULL
        since = (t - (f["scene"].lines[li].start - f["scene"].start)) if f["li"] >= 0 else t
        k = ease_in_out(since / 0.6)
        focus = tuple(lerp(prev[i], cur[i], k) for i in range(3))
        view(c, name, focus)
        # デッキ名の札
        pk = pop_in(t, 0.1)
        c.rrect((AREA[0] + 20, AREA[1] + 18, AREA[0] + 20 + 120 + len(label) * 46, AREA[1] + 96), 39,
                fill=color + (240,), outline=(255, 255, 255), width=4)
        c.text(f"{no} {label}", AREA[0] + 50, AREA[1] + 57, 44, anchor="lm", fnt="noto", fill=(255, 255, 255),
               align="left", scale=pk)
        # 要点（画像内の小さい数字の代わりに大きく出す）
        co = callouts[li] if f["li"] >= 0 and li < len(callouts) else None
        if co:
            ck = ease_back(since / 0.3)
            spr = text_sprite(co, 64, "noto", fill=(30, 30, 30), hl=color)
            w = spr.width + 70
            y = AREA[3] - 90
            c.rrect((W / 2 - w / 2, y - 58, W / 2 + w / 2, y + 58), 58, fill=(255, 255, 255, 250),
                    outline=color + (255,), width=8)
            c.paste(spr, W / 2, y + 4, scale=ck)
    return draw


def intro(c, f):
    t = f["t"]
    burst(c, W / 2, 770, 950, t, (120, 200, 255), alpha=45)
    leaders = ["OP18-041", "OP18-079", "OP18-060", "OP18-001", "OP18-022"]
    for i, cid in enumerate(leaders):
        k = ease_back((t - 0.1 - i * 0.12) / 0.35)
        x = W / 2 + (i - 2) * 190
        y = 780 + abs(i - 2) * 40
        c.paste(img_sprite("cards/" + cid, 420), x, y, scale=k, rot=(2 - i) * 7)
    if f["li"] >= 1:
        lt = f["lt"]
        c.text("新リーダー*5種*", W / 2, 1110, 92, fnt="dela", fill=(255, 255, 255), stroke=6,
               hl=(255, 220, 60), scale=ease_back(lt / 0.3))


def outro(c, f):
    cta_panel(c, f["t"], SHOP_NAME, "11/21(土)\n神の支配 発売！", CTA_RESERVE, accent=(120, 200, 255))


# 注目位置（画像の座標・倍率）
LEADER = (420, 190, 1.6)
CARDS = (540, 520, 1.1)
UPPER = (540, 470, 1.0)


def make():
    s = Short("v6_op18_decks", "新弾*神の支配*\n新リーダー5種のデッキ", ((12, 18, 40), (30, 70, 130)),
              bgm="pop", accent=(120, 200, 255),
              names={"九州そら": "司会", "ずんだもん": "Aさん"})
    s.scene(intro,
            ("zunda", "*神の支配*の新リーダー、どう組めばいいのだ？", "かみのしはいの新リーダー、どう組めばいいのだ？",
             "whoosh"),
            ("sora", "組まれたばかりの*5つのデッキ*を、一気に見ていくわよ！", "組まれたばかりの、5つのデッキを、一気に見ていくわよ！",
             "impact"))
    s.scene(deck_scene("①", "allsunday", "ミス・オールサンデー", (40, 100, 210),
                       [None, CARDS, UPPER], [None, "*バロックワークス*", "カウンター+1000 *×24*"]),
            ("sora", "まずは青の*ミス・オールサンデー*。", "まずは、青の、ミス・オールサンデー。", "pop"),
            ("sora", "*Mr.ナンバーズ*がずらりと並ぶ、バロックワークスのデッキね。",
             "ミスターナンバーズがずらりと並ぶ、バロックワークスのデッキね。"),
            ("zunda", "カウンター+1000が*24枚*！守りも固いのだ。", "カウンタープラス千が、24枚！守りも固いのだ。"))
    s.scene(deck_scene("②", "spandam", "スパンダム", (60, 60, 70),
                       [UPPER, CARDS], ["平均コスト *5.4*", "*7コスト*の大型キャラ"]),
            ("sora", "黒黄の*スパンダム*は、平均コスト*5.4*。", "黒黄のスパンダムは、平均コスト5.4。", "pop"),
            ("sora", "7コストの*大型キャラ*で押し切るデッキよ。", "7コストの、大型キャラで押し切るデッキよ。"))
    s.scene(deck_scene("③", "gunshikyu", "軍子宮", (130, 60, 180),
                       [None, CARDS], ["*神の騎士団*", "1コスト *×20*"]),
            ("sora", "紫黒の新リーダーは、*神の騎士団*で固めた構成。", "紫黒の新リーダーは、神の騎士団で固めた構成。", "pop"),
            ("zunda", "1コストが*20枚*もあるのだ！", "1コストが、20枚もあるのだ！"))
    s.scene(deck_scene("④", "carue", "カルー", (200, 50, 60),
                       [None, CARDS], ["*50枚すべてキャラ*", "カウンター+1000 *×34*"]),
            ("sora", "赤青の*カルー*は、*50枚全部がキャラ*！", "赤青のカルーは、50枚全部がキャラ！", "pop"),
            ("zunda", "カウンター+1000も*34枚*。アラバスタ王国が大集合なのだ！",
             "カウンタープラス千も、34枚。アラバスタ王国が大集合なのだ！"))
    s.scene(deck_scene("⑤", "luffy", "ルフィ", (40, 150, 90),
                       [None, CARDS], ["平均コスト *2.5*", "イベント *×14*"]),
            ("sora", "最後は緑の*ルフィ*。平均コスト*2.5*の超軽量デッキよ。", "最後は、緑のルフィ。平均コスト2.5の、超軽量デッキよ。",
             "pop"),
            ("zunda", "イベントも*14枚*！ゴムゴムで畳みかけるのだ。", "イベントも、14枚！ゴムゴムで畳みかけるのだ。"))
    s.scene(outro,
            ("sora", "あなたが使いたいのは*どのリーダー*？コメントで教えてね。", "あなたが使いたいのは、どのリーダー？コメントで教えてね。",
             "ding", 0.1, 0.7))
    return s
