"""新リーダー5種のデッキを1本ずつ紹介する動画（ずんだもん1人で読み上げ、名札は「司会」）。

デッキ画像：OPLAY TCG で作成されたもの（ユーザー提供・2026/11/17）。数値は各画像に書かれている値。
カード位置はデッキ画像（1080×1080）上の座標。
"""
from config import CTA_RESERVE, SHOP_NAME
from engine.render import W, Short, ease_back, ease_in_out, img_sprite, lerp, text_sprite
from engine.widgets import burst, cta_panel, pop_in
from engine.widgets import stamp as stamp_fn
from scripts.v6_op18_decks import AREA, FULL, view

CARDS = (540, 520, 1.1)


def card(x, y, s=2.0):
    return (x, y, s)


def intro_scene(leader_id, label, color):
    def draw(c, f):
        t = f["t"]
        burst(c, W / 2, 760, 950, t, tuple(min(255, v + 80) for v in color), alpha=55)
        k = ease_back((t - 0.05) / 0.4)
        c.paste(img_sprite("cards/" + leader_id, 640, shine=(t * 0.45) % 1.6, glow=(255, 230, 120)),
                W / 2, 740, scale=k, rot=-4 * (1 - k))
        pk = pop_in(t, 0.35)
        spr = text_sprite(label, 64, "noto", fill=(255, 255, 255))
        w = spr.width + 90
        c.rrect((W / 2 - w / 2, 1095, W / 2 + w / 2, 1175), 40, fill=color + (255,), outline=(255, 255, 255), width=5)
        c.paste(spr, W / 2, 1137, scale=pk)
    return draw


def deck_body(name, label, color, focuses, callouts, stamp=None):
    """stamp=(セリフ番号, 文字)：そのセリフ以降、デッキ画像の上に大きなスタンプを押す。"""
    def draw(c, f):
        t, li = f["t"], max(0, f["li"])
        cur = focuses[li] or FULL
        prev = (focuses[li - 1] or FULL) if li > 0 else FULL
        since = (t - (f["scene"].lines[li].start - f["scene"].start)) if f["li"] >= 0 else t
        k = ease_in_out(since / 0.6)
        view(c, name, tuple(lerp(prev[i], cur[i], k) for i in range(3)))
        c.rrect((AREA[0] + 20, AREA[1] + 18, AREA[0] + 20 + 80 + len(label) * 46, AREA[1] + 96), 39,
                fill=color + (240,), outline=(255, 255, 255), width=4)
        c.text(label, AREA[0] + 50, AREA[1] + 57, 44, anchor="lm", fnt="noto", fill=(255, 255, 255), align="left")
        if stamp and f["li"] >= stamp[0]:
            st = t - (f["scene"].lines[stamp[0]].start - f["scene"].start)
            stamp_fn(c, stamp[1], W / 2, (AREA[1] + AREA[3]) / 2 - 60, st, 0.1, size=200, rot=-12)
        co = callouts[li] if f["li"] >= 0 and li < len(callouts) else None
        if co:
            spr = text_sprite(co, 64, "noto", fill=(30, 30, 30), hl=color)
            w = spr.width + 70
            y = AREA[3] - 90
            c.rrect((W / 2 - w / 2, y - 58, W / 2 + w / 2, y + 58), 58, fill=(255, 255, 255, 250),
                    outline=color + (255,), width=8)
            c.paste(spr, W / 2, y + 4, scale=ease_back(since / 0.3))
    return draw


def outro(color):
    def draw(c, f):
        cta_panel(c, f["t"], SHOP_NAME, "11/21(土)\n神の支配 発売！", CTA_RESERVE, accent=color)
    return draw


def build(slug, name, leader_id, label, color, intro_line, body_lines, focuses, callouts, bg, stamp=None,
          outro_line=None, title=None):
    s = Short(slug, title or f"神の支配 新リーダー\n*{label}*デッキ", bg, bgm="pop", accent=tuple(min(255, v + 90) for v in color),
              names={"ずんだもん": "司会"})
    s.scene(intro_scene(leader_id, label, color), ("zunda",) + intro_line + ("whoosh",))
    s.scene(deck_body(name, label, color, focuses, callouts, stamp),
            *[ln if ln[0] in ("zunda", "zunda_namida", "zunda_ama") else ("zunda",) + ln for ln in body_lines])
    s.scene(outro(tuple(min(255, v + 90) for v in color)),
            ("zunda",) + (outro_line or ("このデッキ、使ってみたいのだ？*コメント*で教えてほしいのだ！",
                                         "このデッキ、使ってみたいのだ？コメントで教えてほしいのだ！")) + ("ding", 0.1, 0.7))
    return s


def allsunday():
    return build(
        "d1_allsunday", "allsunday", "OP18-041", "ミス・オールサンデー", (40, 100, 210),
        ("*神の支配*の新リーダー、青の*ミス・オールサンデー*デッキを紹介するのだ！",
         "かみのしはいの新リーダー、青の、ミス・オールサンデーデッキを紹介するのだ！"),
        [("*Mr.ナンバーズ*がずらりと並ぶ、バロックワークスのデッキなのだ。",
          "ミスターナンバーズがずらりと並ぶ、バロックワークスのデッキなのだ。", "pop"),
         ("切り札は9コストの*Mr.0&ミス・オールサンデー*！", "切り札は、9コストの、ミスターゼロアンドミスオールサンデー！", "kira"),
         ("カウンター+1000が*24枚*で、守りも固いのだ。", "カウンタープラス千が、24枚で、守りも固いのだ。", "pop")],
        [CARDS, card(677, 630), None],
        ["*バロックワークス*", "切り札 *9コスト*", "カウンター+1000 *×24*"],
        ((10, 25, 60), (30, 90, 170)))


def spandam():
    return build(
        "d2_spandam", "spandam", "OP18-079", "スパンダム", (190, 150, 20),
        ("*神の支配*の新リーダー、黒黄の*スパンダム*デッキを紹介するのだ！",
         "かみのしはいの新リーダー、黒黄の、スパンダムデッキを紹介するのだ！"),
        [("平均コストは*5.4*。重めのデッキなのだ。", "平均コストは、5.4。重めのデッキなのだ。", "pop"),
         ("*7コスト*の海軍やCP9がずらり！", "7コストの、海軍や、シーピーナインがずらり！", "pop"),
         ("切り札は*バスターコール*なのだ！", "切り札は、バスターコールなのだ！", "kira")],
        [None, (622, 545, 1.35), card(752, 720)],
        ["平均コスト *5.4*", "*7コスト*がずらり", "切り札 *バスターコール*"],
        ((30, 25, 10), (120, 100, 20)))


def gunshikyu():
    return build(
        "d3_gunshikyu", "gunshikyu", "OP18-060", "軍子宮", (130, 60, 180),
        ("*神の支配*の紫黒の新リーダー、*神の騎士団*デッキを紹介するのだ！",
         "かみのしはいの、紫黒の新リーダー、神の騎士団デッキを紹介するのだ！"),
        [("1コストが*20枚*！序盤からどんどん展開するのだ。", "1コストが、20枚！序盤から、どんどん展開するのだ。", "pop"),
         ("*シャムロック聖*や10コストの大型で、一気に決めるのだ！", "シャムロックせいや、10コストの大型で、一気に決めるのだ！", "kira"),
         ("ステージの*五芒星*も4枚入ってるのだ。", "ステージの、ごぼうせいも、4枚入ってるのだ。", "pop")],
        [None, (290, 684, 1.45), card(950, 684)],
        ["1コスト *×20*", "*8〜10コスト*で決める", "ステージ *五芒星*"],
        ((25, 10, 40), (90, 40, 130)))


def carue():
    return build(
        "d4_carue", "carue", "OP18-001", "カルー", (200, 50, 60),
        ("*神の支配*の新リーダー、赤青の*カルー*デッキを紹介するのだ！",
         "かみのしはいの新リーダー、赤青の、カルーデッキを紹介するのだ！"),
        [("なんと*50枚全部がキャラ*！イベントは0枚なのだ。", "なんと、50枚全部がキャラ！イベントは、0枚なのだ。", "pop"),
         ("*ビビ*に*チャカ*に*ペル*。アラバスタ王国が大集合なのだ！", "ビビに、チャカに、ペル。アラバスタ王国が大集合なのだ！", "kira"),
         ("カウンター+1000が*34枚*。守りもバッチリなのだ。", "カウンタープラス千が、34枚。守りもバッチリなのだ。", "pop")],
        [None, (606, 634, 1.35), None],
        ["*50枚すべてキャラ*", "*アラバスタ王国*", "カウンター+1000 *×34*"],
        ((45, 10, 15), (160, 40, 50)))


def luffy():
    return build(
        "d5_luffy", "luffy", "OP18-022", "ルフィ", (40, 150, 90),
        ("*神の支配*の新リーダー、緑の*ルフィ*デッキを紹介するのだ！",
         "かみのしはいの新リーダー、緑の、ルフィデッキを紹介するのだ！"),
        [("平均コストは*2.5*！超軽量のデッキなのだ。", "平均コストは、2.5！超軽量のデッキなのだ。", "pop"),
         ("*ココロ*や*チムニー*、ウォーターセブンの仲間も入ってるのだ。", "ココロや、チムニー、ウォーターセブンの仲間も入ってるのだ。",
          "pop"),
         ("イベントも*14枚*！*ゴムゴムの巨人*で畳みかけるのだ！", "イベントも、14枚！ゴムゴムの巨人で、畳みかけるのだ！", "kira")],
        [None, (468, 440, 1.25), card(816, 634)],
        ["平均コスト *2.5*", "*ウォーターセブン*の仲間", "イベント *×14*"],
        ((10, 35, 20), (30, 120, 70)))


def mihawk():
    """禁止前の緑ミホーク（メルカード 2026/9 版の標準構成を公式画像で組んだデッキ画像）。"""
    return build(
        "d6_mihawk", "mihawk", "OP14-020", "ミホーク", (40, 150, 90),
        ("禁止になった最強デッキ、緑の*ミホーク*デッキを紹介するのだ！",
         "禁止になった最強デッキ、緑の、ミホークデッキを紹介するのだ！"),
        [("1コストが*24枚*！*ペローナ*と*お玉*で、序盤からサーチするのだ。",
          "1コストが、24枚！ペローナと、お玉で、序盤からサーチするのだ。", "pop"),
         ("中盤は*ロー*と*ミホーク*で、どんどん追加展開！", "中盤は、ローと、ミホークで、どんどん追加展開！", "pop"),
         ("最後は*シャンクス*で全員レストにして、一気に殴り切るのだ！", "最後は、シャンクスで、全員レストにして、一気に殴り切るのだ！",
          "kira"),
         ("zunda_namida", "でも*10月12日*から*禁止*……今は大会で使えないのだ……", "でも、10月12日から禁止。今は大会で使えないのだ。",
          "impact"),
         ("新しいテキストの*プロモ版*が、大会やイベントで配られる予定なのだ！", "新しいテキストの、プロモ版が、大会やイベントで配られる予定なのだ！",
          "ding")],
        [card(232, 364, 1.7), card(908, 364, 1.7), card(170, 536, 1.9), None, None],
        ["1コスト *×24*", "*追加展開*", "切り札 *シャンクス*", "*10/12〜 禁止*", "*救済プロモ* 配布予定"],
        ((8, 30, 20), (30, 110, 60)),
        stamp=(3, "禁止"),
        title="禁止された最強デッキ\n*緑ミホーク*",
        outro_line=("ミホーク、また使いたいのだ？*コメント*で教えてほしいのだ！",
                    "ミホーク、また使いたいのだ？コメントで教えてほしいのだ！"))
