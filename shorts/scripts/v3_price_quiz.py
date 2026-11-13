"""クイズ「いま一番高いワンピースカードは？」（3択クイズ形式・No.7＋白上虎太郎＋玄野武宏）。

価格：トレカラフテル通販（tcg-raftel.com）の販売価格 2026/11/13 時点。
画像は公式カードリストの、ラフテル掲載商品と同じ版（_p番号）を使用。
"""
from config import SHOP_NAME
from engine.render import Line, W, card_sprite, clamp, ease_back, img_sprite, lerp
from engine.render import Short
from engine.widgets import burst, count, cta_panel, fade, pop_in, shake, stamp, yen

CHOICES = [  # ラベル, 名前, 弾, 色, 公式画像
    ("A", "ルフィ 赤SP", "受け継がれる意志", (200, 50, 50), "OP13-118_p3"),
    ("B", "ロジャー 金SP", "新たなる皇帝", (60, 60, 70), "OP09-118_p2"),
    ("C", "ルフィ SP", "新時代の主役", (210, 140, 30), "OP05-119_p2"),
]
ANSWER = 0


def choices(c, t, reveal=-1.0, picks=()):
    for i, (lab, nm, sub, col, cid) in enumerate(CHOICES):
        k = ease_back((t - 0.1 - i * 0.15) / 0.35)
        x = 190 + i * 350
        y = 730
        win = reveal >= 0 and i == ANSWER
        dim = reveal >= 0 and i != ANSWER
        sc = k * (1 + (0.1 * ease_back(reveal / 0.4) if win else 0))
        spr = img_sprite("cards/" + cid, 400, shine=(t * 0.5 + i * 0.3) % 1.6, dim=0.6 if dim else 0,
                         glow=(255, 220, 60) if win else None)
        c.paste(spr, x, y, scale=sc)
        # A/B/C バッジ
        c.d.ellipse((x - 150, y - 230, x - 70, y - 150), fill=col + (255,), outline=(255, 255, 255), width=5)
        c.text(lab, x - 110, y - 192, 50, fnt="dela", fill=(255, 255, 255), alpha=clamp(k))
        c.text(nm, x, y + 232, 34, fnt="noto", fill=(255, 255, 255), stroke=5, alpha=clamp(k))
        c.text(sub, x, y + 272, 26, fnt="noto", fill=(255, 255, 255), stroke=4, alpha=clamp(k))
        if win:
            stamp(c, "1位", x, y - 40, reveal, 0.2, size=120, rot=-12)
        if dim:
            c.text("×", x, y - 30, 200, fnt="dela", fill=(225, 30, 50), stroke=10, alpha=clamp(reveal / 0.3))
        for who, pick, colr in picks:
            if pick == i:
                c.rrect((x - 100, y + 300, x + 100, y + 352), 26, fill=colr + (255,))
                c.text(who, x, y + 326, 32, fnt="round", fill=(255, 255, 255))


def q_scene(c, f):
    t = f["t"]
    c.panel((70, 380, 1010, 520), 40, fill=(255, 255, 255, 240))
    c.text("Q. 今いちばん*高い*カードは？", W / 2, 450, 64, fnt="dela", fill=(30, 30, 30), hl=(225, 30, 50))
    picks = []
    if f["li"] >= 2:
        picks.append(("コタロー", 1, (240, 120, 30)))
    if f["li"] >= 3:
        picks.append(("クロノ", 2, (70, 70, 90)))
    choices(c, t, picks=picks)


def countdown(c, f):
    t = f["t"]
    c.panel((70, 380, 1010, 520), 40, fill=(255, 255, 255, 240))
    c.text("Q. 今いちばん*高い*カードは？", W / 2, 450, 64, fnt="dela", fill=(30, 30, 30), hl=(225, 30, 50))
    choices(c, 9, picks=[("コタロー", 1, (240, 120, 30)), ("クロノ", 2, (70, 70, 90))])
    tt = (f["lt"] - f["line"].dur) if f["line"] else -1
    n = 3 - int(tt / 0.8) if tt >= 0 else 0
    if 1 <= n <= 3:
        k = ease_back((tt % 0.8) / 0.3)
        c.d.ellipse((W / 2 - 140, 730 - 140, W / 2 + 140, 730 + 140), fill=(225, 30, 50, 225),
                    outline=(255, 255, 255), width=8)
        c.text(str(n), W / 2, 722, 200, scale=k, fnt="dela", fill=(255, 255, 255), stroke=8)


def reveal(c, f):
    t = f["t"]
    burst(c, 190, 760, 800, t, (255, 230, 80), alpha=60)
    c.panel((70, 380, 1010, 520), 40, fill=(255, 255, 255, 240))
    c.text("正解は… *A*！", W / 2, 450, 70, fnt="dela", fill=(30, 30, 30), hl=(225, 30, 50))
    choices(c, 9, reveal=t, picks=[("コタロー", 1, (240, 120, 30)), ("クロノ", 2, (70, 70, 90))])
    if f["li"] >= 2:
        lt = t - (f["scene"].lines[2].start - f["scene"].start)
        dx, dy = shake(lt, 12, 0.4, 1.4)
        c.panel((70, 1090, 1010, 1200), 36, fill=(20, 20, 30, 235), shadow=False)
        c.text("トレカラフテル販売価格", W / 2, 1112, 26, fnt="noto", fill=(255, 255, 255))
        c.text(yen(count(lt, 2480000, 0.0, 1.4)), W / 2 + dx, 1158 + dy, 60, fnt="dela",
               fill=(255, 220, 60), stroke=6)


def top3(c, f):
    t = f["t"]
    c.text("ラフテル販売価格 TOP3", W / 2, 420, 72, fnt="dela", fill=(255, 255, 255), stroke=8)
    rows = [("1位", "ルフィ レッドSP", "受け継がれる意志", 2480000, "OP13-118_p3"),
            ("2位", "ルフィ 海賊団SP", "世界最強の戦士", 1680000, "EB04-061_p3"),
            ("3位", "ルフィ 金SP", "神速の拳", 1580000, "OP05-119_p7")]
    for i, (r, nm, sub, v, cid) in enumerate(rows):
        k = ease_back((t - 0.1 - i * 0.25) / 0.35)
        y = 590 + i * 205
        x = lerp(-700, 0, k)
        c.panel((60 + x, y - 90, 1020 + x, y + 90), 40, fill=(255, 255, 255, 240))
        c.text(r, 130 + x, y, 54, fnt="dela", fill=(225, 30, 50))
        c.paste(img_sprite("cards/" + cid, 200), 270 + x, y)
        c.text(nm, 390 + x, y - 45, 44, anchor="lm", fnt="noto", fill=(40, 40, 40), align="left")
        c.text(sub, 390 + x, y + 2, 32, anchor="lm", fnt="noto", fill=(110, 110, 120), align="left")
        c.text(yen(v), 990 + x, y + 50, 54, anchor="rm", fnt="dela", fill=(30, 30, 30))
    if f["li"] >= 1:
        lt = t - (f["scene"].lines[1].start - f["scene"].start)
        stamp(c, "全部ルフィ！！", W / 2, 1150, lt, 0, size=64, rot=0)


def outro(c, f):
    t = f["t"]
    cta_panel(c, t, SHOP_NAME, "正解できた？\n*コメント*で教えて！", "※トレカラフテル通販の販売価格\n（2026/11/13時点・変動します）",
              accent=(255, 220, 60))


def make():
    s = Short("v3_price_quiz", "*3秒*で答えて！\n一番高いカードは？", ((10, 30, 60), (20, 120, 160)),
              bgm="quiz", accent=(255, 220, 60),
              names={"No.7": "司会 セブン・D・ナナ", "白上虎太郎": "見習い海賊 コタロー",
                     "玄野武宏": "鑑定士 “黒鉄”のクロノ"})
    s.scene(q_scene,
            ("no7", "クイズです。今いちばん*高い*ワンピースカードはどれでしょう？",
             "クイズです。今いちばん高いワンピースカードは、どれでしょう？", "ding"),
            ("no7", "A、B、Cの3択です。", None, "pop"),
            ("kotaro_bikubiku", "え、えっと…ロジャーは高そうだし…*B*かな？", "え、えっと、ロジャーは高そうだし、ビーかな？", "pop"),
            ("kurono", "甘いな。新時代のルフィは伝説だ。*C*で決まりだ。", "甘いな。新時代のルフィは伝説だ。シーで決まりだ。", "pop"))
    s.scene(countdown,
            Line("no7", "あなたも3秒で答えてください。", None, None, 0.0, 2.45,
                 after=(("tick", 0.0), ("tick", 0.8), ("tick", 1.6))))
    s.scene(reveal,
            ("no7", "正解は……*A*！受け継がれる意志の、レッドスーパーパラレルです。",
             "正解は、エー！受け継がれる意志の、レッドスーパーパラレルです。", "drumroll+correct"),
            ("kotaro_bikubiku", "えっ、*二人ともハズレ*！？", "えっ、二人ともハズレ！？", "pop"),
            ("no7", "トレカラフテルでの販売価格は、なんと*248万円*。", "トレカラフテルでの販売価格は、なんと248万円。", "impact"))
    s.scene(top3,
            ("kurono", "……ちなみに、トップ3は？", "ちなみに、トップスリーは？", "whoosh"),
            ("no7", "*全部ルフィ*です。さすが主人公ですね。", "全部ルフィです。さすが主人公ですね。", "impact"))
    s.scene(outro,
            ("no7", "あなたは正解できましたか？*コメント*で教えてください。",
             "あなたは正解できましたか？コメントで教えてください。", "ding", 0.05, 0.6))
    return s
