"""これから半年の発売カレンダー（タイムライン形式・波音リツ＋冥鳴ひまり）。

出典：ONE PIECE.com 公式ニュース(2026/11/6 特別番組)、ST-37/38 は公式商品ページで確認済み。
"""
from config import CTA_RESERVE, SHOP_NAME
from engine.render import W, card_sprite, ease_back, ease_out, img_sprite, lerp
from engine.render import Short
from engine.widgets import box_sprite, burst, cta_panel, fade, pop_in, stamp

EVENTS = [  # 日付, 名前, 補足, 色, 公式画像
    ("11/21", "神の支配", "OP-18／ウォーターセブン", (40, 40, 60), ["box_op18"]),
    ("12/19", "スタートデッキ2種", "ST-37・ST-38", (200, 60, 60), ["box_st37", "box_st38"]),
    ("1/30", "EAST BLUE", "EB-06", (40, 110, 200), ["box_eb06"]),
    ("2/27", "応答せよ、世界", "OP-19／エッグヘッド", (60, 150, 140), ["box_op19"]),
    ("4/24", "夢の一枚", "PEB-01／全カードキラ", (210, 160, 40), []),
]


def product(c, imgs, x, y, h, t, k=1.0):
    if not imgs:  # 画像未公開
        c.paste(card_sprite(int(h * 0.55), h, (210, 160, 40), "", "", "", back=True), x, y, scale=k)
        c.text("画像\n未公開", x, y, 44, scale=k, fnt="dela", fill=(255, 255, 255), stroke=6)
        return
    for j, name in enumerate(imgs):
        dx = (j - (len(imgs) - 1) / 2) * 90
        c.paste(img_sprite(name, h, shine=(t * 0.5 + j * 0.3) % 1.5), x + dx, y + j * 30, scale=k,
                rot=(j - (len(imgs) - 1) / 2) * -8)


def timeline(c, f, upto):
    t = f["t"]
    c.d.rectangle((150, 400, 162, 400 + 142 * len(EVENTS)), fill=(255, 255, 255, 120))
    for i, (date, name, sub, col, imgs) in enumerate(EVENTS[: upto + 1]):
        y = 465 + i * 142
        cur = i == upto
        k = ease_back(((t if cur else 9) - 0.0) / 0.35)
        c.d.ellipse((136, y - 20, 176, y + 20), fill=col + (255,), outline=(255, 255, 255), width=5)
        x = lerp(1100, 0, k)
        c.panel((200 + x, y - 65, 760 + x, y + 65), 34, fill=(255, 255, 255, 245 if cur else 200),
                outline=col + (255,) if cur else None, width=6 if cur else 0)
        c.text(date, 290 + x, y, 46, fnt="dela", fill=col)
        c.text(name, 380 + x, y - 22, 40, anchor="lm", fnt="noto", fill=(30, 30, 30), align="left")
        c.text(sub, 380 + x, y + 28, 28, anchor="lm", fnt="noto", fill=(110, 110, 120), align="left")
    imgs = EVENTS[upto][4]
    product(c, imgs, 905, 760, 420, t, ease_back(t / 0.4))


def intro(c, f):
    t = f["t"]
    burst(c, W / 2, 760, 900, t, (255, 120, 140), alpha=45)
    for i, name in enumerate(["box_op18", "box_st37", "box_eb06", "box_op19", "box_st38"]):
        k = ease_back((t - 0.1 - i * 0.1) / 0.35)
        c.paste(img_sprite(name, 420), 220 + i * 160, 740 + (i % 2) * 40, scale=k, rot=(2 - i) * 8)
    if f["li"] >= 1:
        stamp(c, "財布の準備は？", W / 2, 1090, f["lt"], 0.0, color=(200, 40, 60), size=100, rot=-4)


def step(i):
    def draw(c, f):
        timeline(c, f, i)
        if i == 4 and f["li"] >= 1:
            lt = f["t"] - (f["scene"].lines[1].start - f["scene"].start)
            stamp(c, "1パック8枚 全部キラ！", W / 2, 1165, lt, 0.0, color=(210, 160, 40), size=66, rot=-3)
    return draw


def outro(c, f):
    cta_panel(c, f["t"], SHOP_NAME, "予約は\n*お早めに*！", CTA_RESERVE, accent=(255, 120, 140))
    c.text("※2026/11/13時点の発表内容。発売日・内容は変更の可能性があります。", W / 2, 1200, 26, fnt="noto",
           fill=(255, 255, 255), stroke=3, max_w=1000)


def make():
    s = Short("v5_release_calendar", "ワンピカ\n*半年分*の発売日まとめ", ((40, 10, 30), (150, 40, 70)),
              bgm="chill", accent=(255, 120, 140))
    s.scene(intro,
            ("himari", "ねえリツ、これから*新弾*っていつ出るの？", "ねえリツ、これから新弾っていつ出るの？", "whoosh"),
            ("ritsu_queen", "半年で*5商品*よ。財布の準備はできてる？", "半年で5商品よ。財布の準備はできてる？", "impact"))
    s.scene(step(0),
            ("ritsu", "まず*11月21日*、第18弾*神の支配*。ウォーターセブン編ね。",
             "まず11月21日、第18弾、かみのしはい。ウォーターセブン編ね。", "pop"))
    s.scene(step(1),
            ("ritsu", "*12月19日*はスタートデッキが2種類。", "12月19日は、スタートデッキが2種類。", "pop"),
            ("himari", "始めたい友達を誘うチャンスだね。", None))
    s.scene(step(2),
            ("ritsu", "年明け*1月30日*はエクストラブースター、*イーストブルー*！",
             "年明け1月30日は、エクストラブースター、イーストブルー！", "pop"))
    s.scene(step(3),
            ("ritsu", "*2月27日*は第19弾、*応答せよ、世界*。テーマはエッグヘッド。",
             "2月27日は第19弾、おうとうせよ、せかい。テーマはエッグヘッド。", "pop"))
    s.scene(step(4),
            ("ritsu", "そして*4月24日*、新シリーズ*夢の一枚*。1パック440円で……",
             "そして4月24日、新シリーズ、ゆめのいちまい。1パック440円で", "kira"),
            ("ritsu_queen", "8枚*全部キラ*カードよ。", "8枚、全部キラカードよ。", "impact"),
            ("himari", "それは……開けたすぎる。", "それは、開けたすぎる。"))
    s.scene(outro,
            ("himari", "どれが*いちばん楽しみ*？コメントで教えて。", "どれがいちばん楽しみ？コメントで教えて。", "ding",
             0.12, 0.8))
    return s
