"""縦型ショート動画(1080x1920)のレンダラー。

台本(Short)は「シーン」の並びで、各シーンは描画関数とセリフのリストを持つ。
セリフの音声長からタイムラインを自動で組み、PIL でフレームを描いて ffmpeg に流す。
"""
import math
import multiprocessing
import os
import subprocess
import wave
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import audio
from .tts import SR, synth

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30

FONTS = {
    "noto": os.path.join(ROOT, "fonts", "NotoSansJP-Black.ttf"),
    "round": os.path.join(ROOT, "fonts", "MPLUSRounded1c-ExtraBold.ttf"),
    "dela": os.path.join(ROOT, "fonts", "DelaGothicOne-Regular.ttf"),
}

# VOICEVOX キャラクター（style id は VOICEVOX ENGINE の /speakers 準拠）
CHARS = {
    "zunda": dict(name="ずんだもん", vv="ずんだもん", id=3, color=(92, 190, 70), speed=1.22),
    "zunda_ama": dict(name="ずんだもん", vv="ずんだもん", id=1, color=(92, 190, 70), speed=1.18),
    "zunda_namida": dict(name="ずんだもん", vv="ずんだもん", id=76, color=(92, 190, 70), speed=1.15),
    "metan": dict(name="四国めたん", vv="四国めたん", id=2, color=(233, 84, 140), speed=1.15),
    "metan_tsun": dict(name="四国めたん", vv="四国めたん", id=6, color=(233, 84, 140), speed=1.15),
    "tsumugi": dict(name="春日部つむぎ", vv="春日部つむぎ", id=8, color=(245, 160, 40), speed=1.15),
    "ryusei": dict(name="青山龍星", vv="青山龍星", id=13, color=(40, 110, 220), speed=1.2),
    "ryusei_hot": dict(name="青山龍星", vv="青山龍星", id=81, color=(40, 110, 220), speed=1.2),
    "kurono": dict(name="玄野武宏", vv="玄野武宏", id=11, color=(70, 70, 90), speed=1.15),
    "kurono_joy": dict(name="玄野武宏", vv="玄野武宏", id=39, color=(70, 70, 90), speed=1.15),
    "kotaro": dict(name="白上虎太郎", vv="白上虎太郎", id=12, color=(240, 120, 30), speed=1.15),
    "kotaro_wai": dict(name="白上虎太郎", vv="白上虎太郎", id=32, color=(240, 120, 30), speed=1.15),
    "kotaro_bikubiku": dict(name="白上虎太郎", vv="白上虎太郎", id=33, color=(240, 120, 30), speed=1.12),
    "sora": dict(name="九州そら", vv="九州そら", id=16, color=(60, 170, 220), speed=1.15),
    "ritsu": dict(name="波音リツ", vv="波音リツ", id=9, color=(200, 40, 60), speed=1.15),
    "ritsu_queen": dict(name="波音リツ", vv="波音リツ", id=65, color=(200, 40, 60), speed=1.12),
    "himari": dict(name="冥鳴ひまり", vv="冥鳴ひまり", id=14, color=(140, 90, 200), speed=1.15),
    "no7": dict(name="No.7", vv="No.7", id=30, color=(30, 30, 30), speed=1.15),
    "hau": dict(name="雨晴はう", vv="雨晴はう", id=10, color=(80, 180, 200), speed=1.15),
    "mochiko": dict(name="もち子さん", vv="もち子さん", id=20, color=(230, 120, 150), speed=1.15),
}


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_back(x):
    x = clamp(x)
    c1 = 1.9
    return 1 + (c1 + 1) * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def lerp(a, b, x):
    return a + (b - a) * x


# ---------------------------------------------------------------- text sprites
_font_cache = {}
_sprite_cache = {}
_hard_cache = {}


def font(name, size):
    k = (name, size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(FONTS[name], size)
    return _font_cache[k]


NO_HEAD = set("、。，．！？!?ー」』）)…・っゃゅょァィゥェォッャュョ〜")


def _segments(s):
    """'*' で囲んだ部分をハイライト扱いにして [(char, hl)] を返す。"""
    out, hl = [], False
    for ch in s:
        if ch == "*":
            hl = not hl
            continue
        out.append((ch, hl))
    return out


PARTICLES = set("はがをにでへともの")


def _break_cost(u):
    last = u[-1][0]
    if last in "。！？!?":
        return 0.0
    if last in "、…":
        return 0.4
    return 1.5


def _ctype(ch):
    o = ord(ch)
    if ch in NO_HEAD or ch in "」』）)】":
        return "close"
    if ch in "「『（(【":
        return "open"
    if 0x3041 <= o <= 0x309F:
        return "hira"
    if 0x30A0 <= o <= 0x30FF or ch == "ー":
        return "kata"
    if ch.isdigit() or ch in ",.%％/／:：+＋-−×~〜" or (ch.isascii() and ch.isalpha()):
        return "alnum"
    if ch == " ":
        return "space"
    return "kanji"


def _units(segs):
    """文節っぽい単位に分ける。強調(*)部分は1単位として途中で切らない。"""
    units, cur = [], []

    def flush():
        if cur:
            units.append(list(cur))
            cur.clear()

    for i, (ch, hl) in enumerate(segs):
        if cur:
            pch, phl = cur[-1]
            pt, ct = _ctype(pch), _ctype(ch)
            brk = False
            if hl and phl:
                brk = False                      # 強調語句の途中では切らない
            elif phl and not hl:
                brk = ct not in ("close", "hira")  # 強調の直後の助詞などはくっつける
            elif hl and not phl:
                brk = pt not in ("open",) and not (pt == "alnum" and ct == "alnum")
            elif pch in "、。！？!?…" and ct != "close":
                brk = True                       # 句読点の後
            elif pt == "space":
                brk = True
            elif pt == "close" and ct not in ("close",):
                brk = pch in "」』）)】"
            elif ct == "open":
                brk = True
            elif pt == "hira" and ct in ("kata", "alnum"):
                brk = True                       # ひらがなの後にカタカナ・数字
            elif pt == "hira" and ct == "kanji":
                run = 0                          # 直前のひらがなの長さ
                for c2, _ in reversed(cur):
                    if _ctype(c2) != "hira":
                        break
                    run += 1
                brk = run >= 2 or pch in PARTICLES   # 「買い取る」は切らない
            elif (pt == "hira" and pch in PARTICLES and ct == "hira" and ch not in PARTICLES and len(cur) >= 2
                  and _ctype(cur[-2][0]) in ("kanji", "kata", "alnum")):
                brk = True                       # 「カードは|どれ」
            if brk:
                flush()
        cur.append((ch, hl))
    flush()
    return units


def _fill(units, fnt, width):
    lines, cur, cw = [], [], 0.0
    for u in units:
        uw = fnt.getlength("".join(c for c, _ in u))
        if cur and cw + uw > width:
            lines.append(cur)
            cur, cw = [], 0.0
        cur = cur + u
        cw += uw
    if cur:
        lines.append(cur)
    return lines


def _hard_split(u, fnt, max_w):
    """1単位が長すぎる時だけ文字単位で割る。"""
    out, cur = [], []
    for ch in u:
        if cur and fnt.getlength("".join(c for c, _ in cur + [ch])) > max_w and ch[0] not in NO_HEAD:
            out.append(cur)
            cur = []
        cur.append(ch)
    if cur:
        out.append(cur)
    return out


def _layout(units, fnt, max_w, n):
    """units を n 行に分ける最良の区切り（区切り位置の自然さ＋行長のそろい具合）。"""
    ws = [fnt.getlength("".join(c for c, _ in u)) for u in units]
    total = sum(ws)
    avg = total / n
    m = len(units)
    INF = float("inf")
    dp = [[INF] * (n + 1) for _ in range(m + 1)]
    back = [[0] * (n + 1) for _ in range(m + 1)]
    dp[0][0] = 0.0
    for i in range(1, m + 1):
        for k in range(1, n + 1):
            w = 0.0
            for j in range(i - 1, -1, -1):
                w += ws[j]
                if w > max_w:
                    break
                if dp[j][k - 1] == INF:
                    continue
                cost = dp[j][k - 1] + 2.0 * ((w - avg) / max_w) ** 2
                if w < max_w * 0.22:
                    cost += 1.5                  # 極端に短い行は避ける
                if i < m:
                    cost += _break_cost(units[i - 1])
                if cost < dp[i][k]:
                    dp[i][k] = cost
                    back[i][k] = j
    if dp[m][n] == INF:
        return None
    lines, i = [], m
    for k in range(n, 0, -1):
        j = back[i][k]
        lines.append([ch for u in units[j:i] for ch in u])
        i = j
    return lines[::-1]


def wrap(segs, fnt, max_w):
    paras, cur = [], []
    for ch, hl in segs:
        if ch == "\n":
            paras.append(cur)
            cur = []
        else:
            cur.append((ch, hl))
    paras.append(cur)
    lines = []
    wrap.hard = False
    for para in paras:
        if not max_w or fnt.getlength("".join(c for c, _ in para)) <= max_w:
            lines.append(para)
            continue
        units = []
        for u in _units(para):
            if fnt.getlength("".join(c for c, _ in u)) > max_w:
                units.extend(_hard_split(u, fnt, max_w))
                wrap.hard = True
            else:
                units.append(u)
        n = len(_fill(units, fnt, max_w))
        best = _layout(units, fnt, max_w, n) or _fill(units, fnt, max_w)
        lines.extend(best)
    return lines


def text_sprite(s, size, fnt="noto", fill=(255, 255, 255), stroke=0, stroke_fill=(0, 0, 0),
                hl=(255, 220, 0), max_w=None, align="center", spacing=1.18, shadow=0):
    key = (s, size, fnt, fill, stroke, stroke_fill, hl, max_w, align, spacing, shadow)
    if key in _sprite_cache:
        return _sprite_cache[key]
    f = font(fnt, size)
    lines = wrap(_segments(s), f, max_w)
    _hard_cache[(s, size)] = wrap.hard
    lh = int(size * spacing)
    widths = [f.getlength("".join(c for c, _ in ln)) for ln in lines]
    pad = stroke + 6 + shadow
    w = int(max(widths or [1])) + pad * 2
    h = lh * len(lines) + pad * 2 + int(size * 0.25)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for li, ln in enumerate(lines):
        if align == "center":
            x = pad + (w - pad * 2 - widths[li]) / 2
        else:
            x = pad
        y = pad + li * lh
        for ch, ishl in ln:
            col = hl if ishl else fill
            if shadow:
                d.text((x + shadow, y + shadow), ch, font=f, fill=(0, 0, 0, 140),
                       stroke_width=stroke, stroke_fill=(0, 0, 0, 140))
            d.text((x, y), ch, font=f, fill=col, stroke_width=stroke, stroke_fill=stroke_fill)
            x += f.getlength(ch)
    _sprite_cache[key] = img
    return img


# ---------------------------------------------------------------- drawing context
class Ctx:
    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img, "RGBA")

    def paste(self, spr, x, y, anchor="mm", scale=1.0, alpha=1.0, rot=0):
        if scale <= 0.01 or alpha <= 0.01:
            return
        if scale != 1.0:
            spr = spr.resize((max(1, int(spr.width * scale)), max(1, int(spr.height * scale))),
                             Image.BILINEAR)
        if rot:
            spr = spr.rotate(rot, resample=Image.BILINEAR, expand=True)
        if alpha < 1.0:
            spr = spr.copy()
            a = spr.getchannel("A").point(lambda v: int(v * alpha))
            spr.putalpha(a)
        ax = {"l": 0, "m": 0.5, "r": 1}[anchor[0]]
        ay = {"t": 0, "m": 0.5, "b": 1}[anchor[1]]
        px, py = int(x - spr.width * ax), int(y - spr.height * ay)
        if px >= W or py >= H or px + spr.width <= 0 or py + spr.height <= 0:
            return
        sx, sy = max(0, -px), max(0, -py)
        ex, ey = min(spr.width, W - px), min(spr.height, H - py)
        self.img.alpha_composite(spr.crop((sx, sy, ex, ey)), (max(0, px), max(0, py)))

    def text(self, s, x, y, size=80, anchor="mm", scale=1.0, alpha=1.0, rot=0, **kw):
        spr = text_sprite(s, size, **kw)
        self.paste(spr, x, y, anchor, scale, alpha, rot)
        return spr

    def rrect(self, box, r=30, fill=None, outline=None, width=0):
        self.d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)

    def panel(self, box, r=36, fill=(255, 255, 255, 235), outline=None, width=0, shadow=True):
        if shadow:
            x0, y0, x1, y1 = box
            self.d.rounded_rectangle((x0 + 8, y0 + 12, x1 + 8, y1 + 12), r, fill=(0, 0, 0, 70))
        self.d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


ASSETS = os.path.join(ROOT, "assets", "official")
COPYRIGHT = "画像：公式サイトより ©尾田栄一郎／集英社・フジテレビ・東映アニメーション"


def img_sprite(name, h, shine=0.0, dim=0.0, radius=None, glow=None):
    """公式画像（カード: 'cards/OP13-118_p3'、パック: 'box_op05_01'）を高さ h で返す。"""
    key = ("img", name, h, round(shine, 2), dim, radius, glow)
    if key in _sprite_cache:
        return _sprite_cache[key]
    path = None
    for ext in (".png", ".webp", ".jpg"):
        if os.path.exists(os.path.join(ASSETS, name + ext)):
            path = os.path.join(ASSETS, name + ext)
            break
    src = Image.open(path).convert("RGBA")
    bbox = src.getchannel("A").getbbox()
    if bbox:
        src = src.crop(bbox)
    w = max(1, int(src.width * h / src.height))
    im = src.resize((w, h), Image.LANCZOS)
    is_card = name.startswith("cards/")
    if is_card:  # 角丸
        r = radius if radius is not None else int(w * 0.045)
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
        im.putalpha(mask)
    if dim:
        dark = Image.new("RGBA", im.size, (0, 0, 0, int(255 * dim)))
        dark.putalpha(Image.eval(im.getchannel("A"), lambda v: int(v * dim)))
        im.alpha_composite(dark)
    if shine > 0:
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        sx = -w + shine * (w * 3)
        od.polygon([(sx, 0), (sx + w * 0.25, 0), (sx + w * 0.25 - h * 0.6, h), (sx - h * 0.6, h)],
                   fill=(255, 255, 255, 90))
        ov.putalpha(Image.composite(ov.getchannel("A"), Image.new("L", im.size, 0), im.getchannel("A")))
        im.alpha_composite(ov)
    pad = 24
    out = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    a = im.getchannel("A").point(lambda v: int(v * 0.55))
    sh.paste((0, 0, 0, 255), (pad + 8, pad + 12), a)
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    out.alpha_composite(sh)
    if glow:
        g = Image.new("RGBA", out.size, (0, 0, 0, 0))
        g.paste(glow + (255,), (pad, pad), im.getchannel("A"))
        g = g.filter(ImageFilter.GaussianBlur(14))
        out.alpha_composite(g)
        out.alpha_composite(g)
    out.alpha_composite(im, (pad, pad))
    _sprite_cache[key] = out
    return out


def card_sprite(w, h, color, label="", sub="", rarity="", shine=0.0, back=False, art=""):
    """著作物を使わない「カード風」オリジナル図形。"""
    key = ("card", w, h, color, label, sub, rarity, round(shine, 2), back, art)
    if key in _sprite_cache:
        return _sprite_cache[key]
    img = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle((26, 30, w + 26, h + 30), 24, fill=(0, 0, 0, 90))
    if back:
        d.rounded_rectangle((20, 20, w + 20, h + 20), 24, fill=(25, 30, 60), outline=(230, 190, 80), width=8)
        for i in range(6):
            d.ellipse((20 + w / 2 - 30 - i * 18, 20 + h / 2 - 30 - i * 18,
                       20 + w / 2 + 30 + i * 18, 20 + h / 2 + 30 + i * 18), outline=(230, 190, 80, 90), width=3)
    else:
        c0 = tuple(min(255, int(v * 1.25 + 30)) for v in color)
        for yy in range(h):
            k = yy / h
            col = tuple(int(lerp(c0[i], color[i], k)) for i in range(3))
            d.line((20, 20 + yy, w + 20, 20 + yy), fill=col)
        mask = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((20, 20, w + 20, h + 20), 24, fill=255)
        base = Image.new("RGBA", img.size, (0, 0, 0, 0))
        base.paste(img, (0, 0), mask)
        img = base
        d = ImageDraw.Draw(img, "RGBA")
        d.rounded_rectangle((20, 20, w + 20, h + 20), 24, outline=(255, 255, 255), width=7)
        d.rounded_rectangle((44, 44, w - 4, h * 0.62), 14, fill=(255, 255, 255, 60))
        if art:
            spr = text_sprite(art, int(h * 0.3), "dela", fill=(255, 255, 255, 230), stroke=8,
                              stroke_fill=tuple(int(v * 0.6) for v in color))
            img.alpha_composite(spr, (20 + (w - spr.width) // 2, int(20 + h * 0.32 - spr.height / 2)))
        if shine > 0:
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
            od = ImageDraw.Draw(ov)
            sx = -w + shine * (w * 3)
            od.polygon([(sx, 0), (sx + 90, 0), (sx + 90 - h, h + 40), (sx - h, h + 40)], fill=(255, 255, 255, 120))
            ov.putalpha(Image.composite(ov.getchannel("A"), Image.new("L", img.size, 0), mask))
            img.alpha_composite(ov)
        if rarity:
            spr = text_sprite(rarity, int(w * 0.16), "dela", fill=(255, 230, 120), stroke=5, stroke_fill=(60, 30, 0))
            img.alpha_composite(spr, (40, 36))
        if label:
            size = int(w * 0.13)
            spr = text_sprite(label, size, "noto", fill=(255, 255, 255), stroke=6, stroke_fill=(0, 0, 0))
            while spr.width > w - 24 and size > 14:
                size -= 2
                spr = text_sprite(label, size, "noto", fill=(255, 255, 255), stroke=6, stroke_fill=(0, 0, 0))
            img.alpha_composite(spr, (20 + (w - spr.width) // 2, int(20 + h * 0.66)))
        if sub:
            spr = text_sprite(sub, int(w * 0.09), "noto", fill=(255, 255, 255), stroke=4, stroke_fill=(0, 0, 0))
            img.alpha_composite(spr, (20 + (w - spr.width) // 2, int(20 + h * 0.86)))
    _sprite_cache[key] = img
    return img


# ---------------------------------------------------------------- tempo
TEMPO = 1.08         # 全キャラ共通の話速倍率（少し速め。上げすぎると会話が不自然になる）
MAX_PAUSE = 0.25     # 読点などで空く無音の上限（秒）
TURN_GAP = 0.28      # 話者が交代する時の間（秒）。同じ人が続ける時は Line.gap


def tighten(wav, max_pause=MAX_PAUSE, thr=0.012, win=0.01):
    """セリフ内の長すぎる無音（読点の間など）を max_pause まで詰める。"""
    n = int(win * SR)
    if len(wav) < n * 4:
        return wav
    frames = len(wav) // n
    loud = np.abs(wav[: frames * n]).reshape(frames, n).max(axis=1) > thr
    keep = np.ones(frames, dtype=bool)
    lim = int(max_pause / win)
    i = 0
    while i < frames:
        if not loud[i]:
            j = i
            while j < frames and not loud[j]:
                j += 1
            if i > 0 and j < frames and j - i > lim:   # 文中の無音だけ（頭と末尾は除く）
                keep[i + lim // 2: j - lim // 2] = False
            i = j
        else:
            i += 1
    mask = np.repeat(keep, n)
    out = np.concatenate([wav[: frames * n][mask], wav[frames * n:]])
    return out.astype(np.float32)


# ---------------------------------------------------------------- script model
@dataclass
class Line:
    spk: str
    text: str
    say: str = None
    sfx: str = None
    gap: float = 0.1
    hold: float = 0.0
    after: tuple = ()      # ((効果音名, セリフ終了後の秒), ...)
    # 計算値
    start: float = 0.0
    dur: float = 0.0
    wav: object = None


@dataclass
class Scene:
    draw: object
    lines: list
    sfx: str = None
    min_dur: float = 0.0
    title: bool = True
    start: float = 0.0
    dur: float = 0.0
    sub: bool = True


@dataclass
class Short:
    slug: str
    title: str             # 上部に常時表示するフック（*で強調）
    bg: tuple              # 背景グラデ (上色, 下色)
    bgm: str = "pop"
    bgm_gain: float = 0.55
    scenes: list = field(default_factory=list)
    accent: tuple = (255, 220, 0)
    uses_official: bool = True
    names: dict = field(default_factory=dict)
    show_credit: bool = False   # 画面下の小さいクレジット（VOICEVOX名・画像表記）。概要欄に書くので既定はオフ   # 画面に出す名前の上書き {VOICEVOX名: 表示名}

    def scene(self, draw, *lines, **kw):
        ls = [l if isinstance(l, Line) else Line(*l) for l in lines]
        self.scenes.append(Scene(draw, ls, **kw))
        return self

    # ---------------------------------------------------------- timeline
    def build(self):
        t = 0.0
        prev_vv, prev_gap = None, 0.0
        for sc in self.scenes:
            sc.start = t
            lt = 0.25 if sc is self.scenes[0] else 0.05
            for ln in sc.lines:
                ch = CHARS[ln.spk]
                ln.wav = tighten(synth(ln.say or ln.text.replace("*", ""), ch["id"],
                                       speed=round(ch["speed"] * TEMPO, 2)))
                if prev_vv is not None and prev_vv != ch["vv"]:
                    lt += max(0.0, TURN_GAP - prev_gap)   # 掛け合いの「間」
                prev_vv, prev_gap = ch["vv"], ln.gap + ln.hold
                ln.start = t + lt
                ln.dur = len(ln.wav) / SR
                lt += ln.dur + ln.gap + ln.hold
            sc.dur = max(lt + 0.1, sc.min_dur)
            t += sc.dur
        self.duration = t + 0.4
        return self

    def mix(self, path):
        n = int(self.duration * SR) + SR
        voice = np.zeros(n, dtype=np.float32)
        fx = np.zeros(n, dtype=np.float32)

        def add(buf, sig, at, gain=1.0):
            i = int(at * SR)
            e = min(n, i + len(sig))
            buf[i:e] += sig[: e - i] * gain

        for sc in self.scenes:
            if sc.sfx:
                for name in sc.sfx.split("+"):
                    add(fx, audio.SFX[name](), sc.start, 0.9)
            for ln in sc.lines:
                add(voice, ln.wav, ln.start, 1.0)
                if ln.sfx:
                    for name in ln.sfx.split("+"):
                        add(fx, audio.SFX[name](), max(0, ln.start - 0.05), 0.9)
                for name, dt in ln.after:
                    add(fx, audio.SFX[name](), ln.start + ln.dur + dt, 0.9)
        music = audio.bgm(n / SR, self.bgm)
        # ダッキング：声がある所は BGM を下げる
        envv = np.abs(voice)
        k = int(0.15 * SR)
        envv = np.convolve(envv, np.ones(k) / k, mode="same")
        duck = 1 - 0.55 * np.clip(envv * 25, 0, 1)
        out = voice * 1.0 + fx * 0.8 + music * self.bgm_gain * duck
        peak = np.max(np.abs(out)) or 1
        out = out / peak * 0.92
        out = out[: int(self.duration * SR)]
        pcm = (out * 32767).astype(np.int16)
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())

    # ---------------------------------------------------------- frames
    def _bg(self):
        if hasattr(self, "_bg_img"):
            return self._bg_img
        top, bot = self.bg
        arr = np.zeros((H, W, 3), dtype=np.float32)
        k = np.linspace(0, 1, H)[:, None]
        for i in range(3):
            arr[:, :, i] = top[i] * (1 - k) + bot[i] * k
        self._bg_img = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
        # 斜めストライプ（集中線風）を薄く
        ov = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        for x in range(-H * 2, W * 2, 90):
            od.polygon([(x, 0), (x + 40, 0), (x + 40 + H * 2, H * 2), (x + H * 2, H * 2)],
                       fill=(255, 255, 255, 14))
        self._stripes = ov
        return self._bg_img

    def frame(self, T, sub=True, scene=True, title=True):
        img = self._bg().copy()
        off = int((T * 40) % 90)
        img.alpha_composite(self._stripes.crop((off, off, off + W, off + H)))
        # 漂う光の粒
        d = ImageDraw.Draw(img, "RGBA")
        for i in range(14):
            ph = i * 1.7
            x = (i * 157 + T * (12 + i % 5 * 6)) % (W + 200) - 100
            y = (H * 0.15 + (i * 263) % int(H * 0.75) + math.sin(T * 0.8 + ph) * 40)
            r = 10 + (i % 4) * 12
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 22 + (i % 3) * 10))
        c = Ctx(img)
        sc = self.scenes[-1]
        for s in self.scenes:
            if s.start <= T < s.start + s.dur:
                sc = s
                break
        lt = T - sc.start
        li, lp, cur = -1, 0.0, None
        for i, ln in enumerate(sc.lines):
            if T >= ln.start:
                li, cur = i, ln
                lp = (T - ln.start) / max(ln.dur, 0.01)
        info = dict(T=T, t=lt, dur=sc.dur, li=li, lp=lp, line=cur, scene=sc,
                    lt=(T - cur.start) if cur else -1, short=self)
        if scene:
            sc.draw(c, info)
        if sc.title and title:
            self.draw_title(c, T)
        if sub and sc.sub and cur is not None:
            self.draw_sub(c, cur, T)
        if self.show_credit:
            self.draw_credit(c)
        # 進行バー
        p = T / self.duration
        c.d.rectangle((0, H - 10, int(W * p), H), fill=self.accent + (255,))
        return img.convert("RGB")

    def draw_title(self, c, T):
        c.d.rectangle((0, 70, W, 330), fill=(0, 0, 0, 150))
        c.d.rectangle((0, 70, W, 80), fill=self.accent + (255,))
        c.d.rectangle((0, 320, W, 330), fill=self.accent + (255,))
        pulse = 1 + 0.015 * math.sin(T * 6)
        c.text(self.title, W / 2, 200, 84, scale=pulse, fnt="dela", fill=(255, 255, 255),
               stroke=8, stroke_fill=(0, 0, 0), hl=self.accent, max_w=1000, spacing=1.15)

    def draw_sub(self, c, ln, T):
        ch = CHARS[ln.spk]
        x0, y0, x1, y1 = 40, 1255, 1040, 1540
        k = ease_back((T - ln.start) / 0.18)
        col = ch["color"]
        c.panel((x0, y0, x1, y1), 34, fill=(255, 255, 255, 240), outline=col + (255,), width=8)
        # 名札
        tag = text_sprite(self.names.get(ch["vv"], ch["name"]), 40, "round", fill=(255, 255, 255))
        tw = tag.width + 70
        c.rrect((x0 + 30, y0 - 40, x0 + 30 + tw, y0 + 30), 30, fill=col + (255,))
        bounce = abs(math.sin((T - ln.start) * 9)) * 6 if T < ln.start + ln.dur else 0
        c.d.ellipse((x0 + 42, y0 - 28 - bounce, x0 + 82, y0 + 12 - bounce), fill=(255, 255, 255))
        c.d.ellipse((x0 + 52, y0 - 18 - bounce, x0 + 72, y0 + 2 - bounce), fill=col)
        c.paste(tag, x0 + 92, y0 - 5, "lm")
        size = 66
        spr = text_sprite(ln.text, size, "noto", fill=(30, 30, 30), hl=(225, 30, 50), max_w=900)
        while (spr.height > (y1 - y0 - 40) or _hard_cache.get((ln.text, size))) and size > 40:
            size -= 4
            spr = text_sprite(ln.text, size, "noto", fill=(30, 30, 30), hl=(225, 30, 50), max_w=900)
        c.paste(spr, (x0 + x1) / 2, (y0 + y1) / 2 + 8, "mm", scale=lerp(0.85, 1, k))

    def draw_credit(self, c):
        if not hasattr(self, "_credit"):
            names = []
            for sc in self.scenes:
                for ln in sc.lines:
                    n = CHARS[ln.spk]["vv"]
                    if n not in names:
                        names.append(n)
            self._credit = "VOICEVOX:" + "／".join(names)
        c.text(self._credit, 50, 1580, 28, anchor="lm", fnt="noto", fill=(255, 255, 255),
               stroke=3, align="left")
        if getattr(self, "uses_official", False):
            c.text(COPYRIGHT, 50, 1622, 24, anchor="lm", fnt="noto", fill=(255, 255, 255),
                   stroke=3, align="left")

    # ---------------------------------------------------------- output
    def render(self, out_dir, preview_times=()):
        os.makedirs(out_dir, exist_ok=True)
        self.build()
        wav = os.path.join(out_dir, f"{self.slug}.wav")
        mp4 = os.path.join(out_dir, f"{self.slug}.mp4")
        self.mix(wav)
        for pt in preview_times:
            self.frame(pt).save(os.path.join(out_dir, f"{self.slug}_{pt:05.1f}.jpg"), quality=85)
        nframes = int(self.duration * FPS)
        jobs = max(1, (os.cpu_count() or 2))
        bounds = [nframes * i // jobs for i in range(jobs + 1)]
        parts = [os.path.join(out_dir, f".{self.slug}_part{i}.mp4") for i in range(jobs)]
        global _CURRENT
        _CURRENT = self
        ctx = multiprocessing.get_context("fork")
        with ctx.Pool(jobs) as pool:
            pool.starmap(_render_part, [(bounds[i], bounds[i + 1], parts[i]) for i in range(jobs)])
        lst = os.path.join(out_dir, f".{self.slug}_parts.txt")
        with open(lst, "w") as f:
            f.writelines(f"file '{os.path.basename(p)}'\n" for p in parts)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                        "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", mp4], check=True)
        for p in parts + [lst, wav]:
            os.remove(p)
        return mp4


_CURRENT = None


def _render_part(a, b, path):
    s = _CURRENT
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(a, b):
        p.stdin.write(s.frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
