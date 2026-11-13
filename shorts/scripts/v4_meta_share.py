"""今の環境、4人に1人がこのデッキ（データ解説形式・九州そら＋白上虎太郎）。

出典：TCGポータル 環境分析（2026/10/14〜11/13、スタンダード 196デッキ集計）。
"""
import math

from config import SHOP_NAME
from engine.render import W, ease_back, ease_out, lerp
from engine.render import Short
from engine.widgets import COLOR, burst, cta_panel, fade, pop_in, shake, stamp

SHARE = [("青ロックス", 25.0, COLOR["青"]), ("黄エネル", 8.7, COLOR["黄"]),
         ("赤緑ルフィ&エース", 8.2, (200, 90, 60)), ("緑シャンクス", 8.2, COLOR["緑"]),
         ("紫カイドウ", 7.7, COLOR["紫"]), ("その他", 42.2, (150, 150, 165))]


def people(c, t, n_hl, y=760):
    """4人のアイコン、そのうち1人がハイライト。"""
    for i in range(4):
        k = ease_back((t - i * 0.12) / 0.3)
        x = 210 + i * 220
        hl = i < n_hl
        col = COLOR["青"] if hl else (200, 200, 210)
        r = 70 * k
        c.d.ellipse((x - r * 0.6, y - 150 - r * 0.6, x + r * 0.6, y - 150 + r * 0.6), fill=col + (255,))
        c.d.rounded_rectangle((x - r, y - 60, x + r, y - 60 + r * 2.2), int(r * 0.6) + 1, fill=col + (255,))


def intro(c, f):
    t = f["t"]
    people(c, t, 1 if f["li"] >= 1 else 0)
    if f["li"] >= 1:
        lt = f["lt"]
        stamp(c, "4人に1人！", W / 2, 1080, lt, 0.1, color=COLOR["青"], size=110, rot=-5)


def donut(c, f):
    t = f["t"]
    cx, cy, R = W / 2, 760, 330
    p = ease_out((t - 0.1) / 1.6)
    total = 360 * p
    a0 = -90
    for name, v, col in SHARE:
        sweep = 360 * v / 100
        if a0 + 90 >= total:
            break
        a1 = min(a0 + sweep, -90 + total)
        pop = 25 if name == "青ロックス" and f["li"] >= 1 else 0
        mid = math.radians((a0 + a1) / 2)
        ox, oy = math.cos(mid) * pop, math.sin(mid) * pop
        c.d.pieslice((cx - R + ox, cy - R + oy, cx + R + ox, cy + R + oy), a0, a1, fill=col + (255,),
                     outline=(255, 255, 255), width=6)
        a0 += sweep
    c.d.ellipse((cx - 160, cy - 160, cx + 160, cy + 160), fill=(20, 40, 70, 255))
    c.text("196", cx, cy - 30, 96, fnt="dela", fill=(255, 255, 255))
    c.text("デッキ集計", cx, cy + 55, 40, fnt="noto", fill=(255, 255, 255))
    if f["li"] >= 1:
        k = pop_in(f["t"] - (f["scene"].lines[1].start - f["scene"].start))
        c.text("青ロックス\n*25.0%*", 830, 470, 56, scale=k, fnt="dela", fill=(255, 255, 255), stroke=6,
               hl=(120, 200, 255))


def ranking(c, f):
    t = f["t"]
    c.text("シェア TOP5", W / 2, 410, 80, fnt="dela", fill=(255, 255, 255), stroke=8)
    for i, (name, v, col) in enumerate(SHARE[:5]):
        y = 540 + i * 135
        k = ease_out((t - 0.1 - i * 0.12) / 0.6)
        c.text(name, 80, y, 46, anchor="lm", fnt="noto", fill=(255, 255, 255), stroke=5, align="left")
        bw = 640 * v / 25.0 * k
        c.rrect((80, y + 32, 80 + max(30, bw), y + 82), 25, fill=col + (255,))
        c.text(f"{v * k:.1f}%", 100 + max(30, bw), y + 57, 44, anchor="lm", fnt="dela", fill=(255, 255, 255),
               stroke=5, align="left")


def ban(c, f):
    t = f["t"]
    dx, dy = shake(t, 14, 0.4, 0.2)
    c.panel((120, 440, 960, 1000), 40, fill=(255, 255, 255, 235))
    c.text("10/12 禁止改訂", W / 2, 530, 64, fnt="dela", fill=(30, 30, 30))
    c.text("ジュラキュール・ミホーク\n（OP14-020）", W / 2, 700, 56, fnt="noto", fill=(30, 30, 30))
    stamp(c, "禁止", W / 2 + dx, 870 + dy, t, 0.2, size=140, rot=-10)
    if f["li"] >= 1:
        lt = f["t"] - (f["scene"].lines[1].start - f["scene"].start)
        c.text("→ *青ロックス*一強に", W / 2, 1120, 64, fnt="dela", fill=(255, 255, 255), stroke=7,
               alpha=fade(lt), hl=(120, 200, 255))


def tip(c, f):
    t = f["t"]
    burst(c, W / 2, 760, 900, t, (120, 200, 255), alpha=40)
    c.panel((90, 420, 990, 1110), 44, fill=(255, 255, 255, 240))
    c.text("勝ちたいなら…", W / 2, 510, 60, fnt="dela", fill=(40, 100, 210))
    rows = ["① *ロックス対策*を組み込む", "② 自分のデッキで*ロックス戦*を練習", "③ *11/21 新弾*で環境が動く！"]
    for i, r in enumerate(rows):
        a = fade(t, 0.3 + i * 0.5)
        c.text(r, 140, 640 + i * 150, 50, anchor="lm", fnt="noto", fill=(30, 30, 30), hl=(225, 30, 50),
               alpha=a, align="left")


def outro(c, f):
    cta_panel(c, f["t"], SHOP_NAME, "デッキパーツ\n探しはお店で！", "あなたの使用デッキは？\n*コメント*で教えて！",
              accent=(120, 200, 255))
    c.text("※TCGポータル集計（2026/10/14〜11/13・196デッキ）", W / 2, 1200, 26, fnt="noto",
           fill=(255, 255, 255), stroke=3)


def make():
    s = Short("v4_meta_share", "今の環境…\n*4人に1人*がこのデッキ", ((10, 25, 60), (30, 90, 160)),
              bgm="news", accent=(120, 200, 255))
    s.scene(intro,
            ("kotaro", "ねえ、最近の大会って*どのデッキ*が多いの？", "ねえ、最近の大会って、どのデッキが多いの？", "whoosh"),
            ("sora", "直近1か月の集計だと、*4人に1人*が同じデッキなの。", "直近1か月の集計だと、4人に1人が同じデッキなの。", "impact"))
    s.scene(donut,
            ("sora", "196デッキの集計で……", "196デッキの集計で", "pop"),
            ("sora", "トップは*青ロックス*、シェア*25%*！", "トップは、あおロックス。シェア25パーセント！", "impact"))
    s.scene(ranking,
            ("sora", "2位以下は*8%台*の団子状態。", "2位以下は、8パーセント台のだんご状態。", "whoosh"),
            ("kotaro_bikubiku", "ロックスだけ*ずば抜けてる*……！", "ロックスだけ、ずば抜けてる！"))
    s.scene(ban,
            ("sora", "きっかけは10月の改訂で*ミホークが禁止*になったこと。", "きっかけは、10月の改訂で、ミホークが禁止になったこと。", "impact"),
            ("kotaro", "それで*ロックス一強*に！", "それで、ロックス一強に！", "ding"))
    s.scene(tip,
            ("kotaro_wai", "じゃあ僕も*ロックス*使えば勝てる！？", "じゃあ僕も、ロックス使えば勝てる！？", "pop"),
            ("sora", "逆に*対策*を積めば有利がとれる。新弾で環境も*動く*わよ。",
             "逆に、対策を積めば有利がとれる。新弾で環境も動くわよ。"))
    s.scene(outro,
            ("sora", "あなたの*使用デッキ*は何？コメントで教えてね。", "あなたの使用デッキは何？コメントで教えてね。", "ding",
             0.12, 0.8))
    return s
