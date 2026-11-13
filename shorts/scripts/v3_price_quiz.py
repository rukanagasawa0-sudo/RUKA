"""クイズ「いま一番高いワンピースカードは？」（3択クイズ形式・No.7＋白上虎太郎＋玄野武宏）。

出典：ワンピースカード当たり・買取価格まとめ（onepiece-card-atari.jp）買取ランキング 2026/11/13。
"""
from config import SHOP_NAME
from engine.render import Line, W, card_sprite, clamp, ease_back, lerp
from engine.render import Short
from engine.widgets import burst, count, cta_panel, fade, pop_in, shake, stamp, yen

CHOICES = [  # ラベル, 弾, 色
    ("A", "ルフィ SP", "受け継がれる意志", (200, 50, 50)),
    ("B", "ロジャー GSP", "新たなる皇帝", (60, 60, 70)),
    ("C", "ルフィ SP", "新時代の主役", (210, 140, 30)),
]
ANSWER = 0


def choices(c, t, reveal=-1.0, picks=()):
    for i, (lab, nm, sub, col) in enumerate(CHOICES):
        k = ease_back((t - 0.1 - i * 0.15) / 0.35)
        x = 190 + i * 350
        y = 760
        dim = reveal >= 0 and i != ANSWER
        sc = k * (1 + (0.12 * ease_back(reveal / 0.4) if reveal >= 0 and i == ANSWER else 0))
        art = ("1位" if i == ANSWER else "×") if reveal >= 0 else "？"
        spr = card_sprite(280, 400, tuple(int(v * 0.35) for v in col) if dim else col, nm, sub, lab,
                          shine=(t * 0.5 + i * 0.3) % 1.6, art=art)
        c.paste(spr, x, y, scale=sc, alpha=0.45 if dim else 1)
        for who, pick, colr in picks:
            if pick == i:
                c.rrect((x - 110, y + 230, x + 110, y + 290), 30, fill=colr + (255,))
                c.text(who, x, y + 260, 36, fnt="round", fill=(255, 255, 255))


def q_scene(c, f):
    t = f["t"]
    c.panel((70, 380, 1010, 520), 40, fill=(255, 255, 255, 240))
    c.text("Q. 今いちばん*高い*カードは？", W / 2, 450, 64, fnt="dela", fill=(30, 30, 30), hl=(225, 30, 50))
    picks = []
    if f["li"] >= 2:
        picks.append(("虎太郎", 2, (240, 120, 30)))
    if f["li"] >= 3:
        picks.append(("玄野", 0, (70, 70, 90)))
    choices(c, t, picks=picks)


def countdown(c, f):
    t = f["t"]
    c.panel((70, 380, 1010, 520), 40, fill=(255, 255, 255, 240))
    c.text("Q. 今いちばん*高い*カードは？", W / 2, 450, 64, fnt="dela", fill=(30, 30, 30), hl=(225, 30, 50))
    choices(c, 9, picks=[("虎太郎", 2, (240, 120, 30)), ("玄野", 0, (70, 70, 90))])
    tt = (f["lt"] - f["line"].dur) if f["line"] else -1
    n = 3 - int(tt / 0.8) if tt >= 0 else 0
    if 1 <= n <= 3:
        k = ease_back((tt % 0.8) / 0.3)
        c.d.ellipse((W / 2 - 110, 1110 - 110, W / 2 + 110, 1110 + 110), fill=(225, 30, 50, 230))
        c.text(str(n), W / 2, 1105, 160, scale=k, fnt="dela", fill=(255, 255, 255), stroke=8)


def reveal(c, f):
    t = f["t"]
    burst(c, 190, 760, 800, t, (255, 230, 80), alpha=60)
    c.panel((70, 380, 1010, 520), 40, fill=(255, 255, 255, 240))
    c.text("正解は… *A*！", W / 2, 450, 70, fnt="dela", fill=(30, 30, 30), hl=(225, 30, 50))
    choices(c, 9, reveal=t, picks=[("虎太郎", 2, (240, 120, 30)), ("玄野", 0, (70, 70, 90))])
    if f["li"] >= 1:
        lt = t - (f["scene"].lines[1].start - f["scene"].start)
        dx, dy = shake(lt, 12, 0.4, 1.4)
        c.panel((80, 1075, 1000, 1215), 40, fill=(20, 20, 30, 230), shadow=False)
        c.text("推定買取 " + yen(count(lt, 2085000, 0.0, 1.4)), W / 2 + dx, 1145 + dy, 76, fnt="dela",
               fill=(255, 220, 60), stroke=6)


def top3(c, f):
    t = f["t"]
    c.text("買取ランキング TOP3", W / 2, 420, 78, fnt="dela", fill=(255, 255, 255), stroke=8)
    rows = [("1位", "ルフィ SP（受け継がれる意志）", 2085000), ("2位", "ルフィ SP（世界最強の戦士）", 1485000),
            ("3位", "ルフィ 金SP（神速の拳）", 1035000)]
    for i, (r, nm, v) in enumerate(rows):
        k = ease_back((t - 0.1 - i * 0.25) / 0.35)
        y = 570 + i * 190
        x = lerp(-600, 0, k)
        c.panel((60 + x, y - 80, 1020 + x, y + 80), 40, fill=(255, 255, 255, 240))
        c.text(r, 140 + x, y, 56, fnt="dela", fill=(225, 30, 50))
        c.text(nm, 230 + x, y - 28, 40, anchor="lm", fnt="noto", fill=(40, 40, 40), align="left")
        c.text(yen(v), 990 + x, y + 30, 54, anchor="rm", fnt="dela", fill=(30, 30, 30))
    if f["li"] >= 1:
        lt = t - (f["scene"].lines[1].start - f["scene"].start)
        stamp(c, "全部ルフィ！！", W / 2, 1140, lt, 0, size=100, rot=-6)


def outro(c, f):
    t = f["t"]
    cta_panel(c, t, SHOP_NAME, "正解できた？\n*コメント*で教えて！", "※推定買取は2026/11/13時点\n相場は日々変動します",
              accent=(255, 220, 60))


def make():
    s = Short("v3_price_quiz", "*3秒*で答えて！\n一番高いカードは？", ((10, 30, 60), (20, 120, 160)),
              bgm="quiz", accent=(255, 220, 60))
    s.scene(q_scene,
            ("no7", "クイズです。今いちばん*高い*ワンピースカードはどれでしょう？",
             "クイズです。今いちばん高いワンピースカードは、どれでしょう？", "ding"),
            ("no7", "A、B、Cの3択です。", None, "pop"),
            ("kotaro_bikubiku", "え、えっと…ロジャーは高そうだし…*C*かな？", "え、えっと、ロジャーは高そうだし、シーかな？", "pop"),
            ("kurono", "いや、*A*だな。あれは別格だ。", "いや、エーだな。あれは別格だ。", "pop"))
    s.scene(countdown,
            Line("no7", "あなたも3秒で答えてください。", None, None, 0.0, 2.45,
                 after=(("tick", 0.0), ("tick", 0.8), ("tick", 1.6))))
    s.scene(reveal,
            ("no7", "正解は……*A*！受け継がれる意志のルフィSPです。", "正解は、エー！受け継がれる意志の、ルフィ、エスピーです。",
             "drumroll+correct"),
            ("no7", "推定買取価格は、なんと*約208万円*。", "推定買取価格は、なんと約208万円。", "impact"),
            ("kotaro_wai", "208万！？ ぼく一生かかっても引けないよ〜！", "208万！？ぼく一生かかっても引けないよー！"))
    s.scene(top3,
            ("kurono_joy", "ちなみにトップ3は……", "ちなみにトップスリーは", "whoosh"),
            ("kurono_joy", "*全部ルフィ*だ！さすが主人公。", "全部ルフィだ！さすが主人公。", "impact"))
    s.scene(outro,
            ("no7", "あなたは正解できましたか？*コメント*で教えてください。",
             "あなたは正解できましたか？コメントで教えてください。", "ding", 0.12, 0.8))
    return s
