"""これから半年の発売カレンダー（タイムライン形式・波音リツ＋冥鳴ひまり）。

出典：ONE PIECE.com 公式ニュース(2026/11/6 特別番組)、ST-37/38 は公式商品ページで確認済み。
"""
from config import CTA_RESERVE, SHOP_NAME
from engine.render import W, card_sprite, ease_back, ease_out, img_sprite, lerp, text_sprite
from engine.render import Short
from engine.widgets import box_sprite, burst, cta_panel, fade, pop_in, stamp

EVENTS = [  # 日付, 名前, 補足, 色, 公式画像
    ("11/21", "神の支配", "ブースター OP-18／ウォーターセブン・エルバフ・アラバスタ", (40, 40, 60), ["box_op18"]),
    ("12/19", "スタートデッキ2種", "ST-37 砂漠の王女と海賊たち／ST-38 バロックワークス", (200, 60, 60),
     ["box_st37", "box_st38"]),
    ("1/30", "EAST BLUE", "エクストラブースター EB-06", (40, 110, 200), ["box_eb06"]),
    ("2/27", "応答せよ、世界", "ブースター OP-19／エッグヘッド編", (60, 150, 140), ["box_op19"]),
    ("4/24", "夢の一枚", "PEB-01／1パック440円・全カードキラ", (210, 160, 40), []),
]


def product(c, imgs, x, y, h, t, k=1.0, label=True):
    if not imgs:  # 画像未公開
        c.paste(card_sprite(int(h * 0.62), h, (210, 160, 40), "", "", "", back=True), x, y, scale=k)
        if label:
            c.text("画像\n未公開", x, y, 60, scale=k, fnt="dela", fill=(255, 255, 255), stroke=7)
        return
    n = len(imgs)
    for j, name in enumerate(imgs):
        dx = (j - (n - 1) / 2) * 300
        c.paste(img_sprite(name, h, shine=(t * 0.5 + j * 0.3) % 1.5), x + dx, y, scale=k)


def chips(c, upto, t):
    """上部：5つの発売日。済み＝薄く、今＝色付き、これから＝枠だけ。"""
    w, gap = 184, 10
    x0 = (W - (w * 5 + gap * 4)) / 2
    for i, (date, _, _, col, _) in enumerate(EVENTS):
        x = x0 + i * (w + gap)
        box = (x, 372, x + w, 444)
        if i < upto:
            c.rrect(box, 36, fill=(255, 255, 255, 150))
            c.text(date, x + w / 2, 407, 40, fnt="dela", fill=(90, 90, 100))
        elif i == upto:
            k = ease_back(t / 0.3)
            c.rrect(box, 36, fill=col + (255,), outline=(255, 255, 255), width=4)
            c.text(date, x + w / 2, 407, 42, fnt="dela", fill=(255, 255, 255), scale=k)
        else:
            c.rrect(box, 36, outline=(255, 255, 255, 170), width=4)
            c.text(date, x + w / 2, 407, 40, fnt="dela", fill=(255, 255, 255), alpha=0.75)


def timeline(c, f, upto):
    t = f["t"]
    date, name, sub, col, imgs = EVENTS[upto]
    chips(c, upto, t)
    k = ease_back((t - 0.05) / 0.4)
    product(c, imgs, W / 2, 735, 520, t, k, label=not (upto == 4 and f["li"] >= 1))
    c.panel((80, 1020, 1000, 1172), 40, fill=(255, 255, 255, 245), outline=col + (255,), width=6)
    c.text(f"*{date}* {name}", W / 2, 1068, 62, fnt="dela", fill=(30, 30, 30), hl=col, max_w=880,
           alpha=min(1.0, max(0.0, t / 0.25)))
    size = 38
    while size > 24 and text_sprite(sub, size, "noto").width > 880:
        size -= 2
    c.text(sub, W / 2, 1135, size, fnt="noto", fill=(90, 90, 100), alpha=min(1.0, max(0.0, t / 0.25)))


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
            stamp(c, "1パック8枚\n全部キラ！", W / 2, 735, lt, 0.0, color=(210, 160, 40), size=76, rot=-6)
    return draw


def outro(c, f):
    cta_panel(c, f["t"], SHOP_NAME, "発売日を\n*チェック*！", CTA_RESERVE, accent=(255, 120, 140))
    c.text("※2026/11/13時点の発表内容。発売日・内容は変更の可能性があります。", W / 2, 1178, 24, fnt="noto",
           fill=(255, 255, 255), stroke=3, max_w=1000)


def make():
    s = Short("v5_release_calendar", "ワンピカ\n*半年分*の発売日まとめ", ((40, 10, 30), (150, 40, 70)),
              bgm="chill", accent=(255, 120, 140))
    s.scene(intro,
            ("himari", "ねえリツ、これから*新弾*っていつ出るの？", "ねえリツ、これから新弾っていつ出るの？", "whoosh"),
            ("ritsu_queen", "半年で*5商品*よ。財布の準備はできてる？", "半年で5商品よ。財布の準備はできてる？", "impact"))
    s.scene(step(0),
            ("ritsu", "まず*11月21日*、第18弾*神の支配*。舞台はウォーターセブン、エルバフ、アラバスタね。",
             "まず11月21日、第18弾、かみのしはい。舞台は、ウォーターセブン、エルバフ、アラバスタね。", "pop"))
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
             0.1, 0.7))
    return s
