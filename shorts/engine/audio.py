"""BGM と効果音をその場で合成する（外部素材なし＝権利フリー）。"""
import numpy as np

SR = 48000


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _env(n, a=0.005, r=0.1):
    e = np.ones(n, dtype=np.float32)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr and nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def note_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


# ---------------- SFX ----------------
def sfx_pop():
    t = _t(0.12)
    f = 900 * np.exp(-t * 18) + 300
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30) * 0.5).astype(np.float32)


def sfx_whoosh(dur=0.35):
    n = int(dur * SR)
    noise = np.random.default_rng(1).standard_normal(n)
    # 簡易バンドパス：移動平均の差分でスイープ感
    out = np.zeros(n)
    k = np.linspace(40, 4, n).astype(int)
    cs = np.cumsum(noise)
    for i in range(n):
        j = max(0, i - k[i])
        out[i] = (cs[i] - cs[j]) / max(1, k[i])
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return (out * env * 0.9).astype(np.float32)


def sfx_ding(base=88):
    t = _t(0.9)
    s = np.zeros_like(t)
    for mult, amp in [(1, 1), (2.01, .5), (3.02, .25), (4.2, .12)]:
        s += amp * np.sin(2 * np.pi * note_hz(base) * mult * t)
    return (s * np.exp(-t * 4) * 0.25).astype(np.float32)


def sfx_correct():
    a = sfx_ding(84)
    b = sfx_ding(91)
    out = np.zeros(len(a) + int(0.1 * SR), dtype=np.float32)
    out[:len(a)] += a
    out[int(0.1 * SR):] += b
    return out


def sfx_tick():
    t = _t(0.05)
    return (np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90) * 0.35).astype(np.float32)


def sfx_drumroll(dur=1.2):
    n = int(dur * SR)
    out = np.zeros(n, dtype=np.float32)
    rng = np.random.default_rng(2)
    step = int(SR / 22)
    for i in range(0, n - step, step):
        hit = rng.standard_normal(step).astype(np.float32) * np.exp(-np.arange(step) / SR * 60)
        out[i:i + step] += hit * (0.15 + 0.25 * i / n)
    return out


def sfx_impact():
    t = _t(0.6)
    f = 120 * np.exp(-t * 6) + 40
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
    noise = np.random.default_rng(3).standard_normal(len(t)) * np.exp(-t * 25) * 0.3
    return ((body + noise) * 0.6).astype(np.float32)


def sfx_kira():
    out = np.zeros(int(0.8 * SR), dtype=np.float32)
    for i, n in enumerate([88, 91, 95, 100, 103]):
        s = sfx_ding(n)[: int(0.5 * SR)] * 0.6
        o = int(i * 0.06 * SR)
        out[o:o + len(s)] += s[: len(out) - o]
    return out


SFX = {
    "pop": sfx_pop, "whoosh": sfx_whoosh, "ding": sfx_ding, "correct": sfx_correct,
    "tick": sfx_tick, "drumroll": sfx_drumroll, "impact": sfx_impact, "kira": sfx_kira,
}


# ---------------- BGM ----------------
STYLES = {
    # (bpm, ルート進行(MIDI), スケール感, ドラムの強さ)
    "hype": (128, [57, 53, 48, 55], "minor", 1.0),
    "pop": (118, [48, 55, 57, 53], "major", 0.8),
    "quiz": (136, [50, 50, 55, 57], "major", 0.9),
    "chill": (96, [53, 52, 50, 48], "major", 0.5),
    "news": (112, [45, 41, 48, 43], "minor", 0.7),
}


def bgm(duration, style="pop", seed=0):
    bpm, roots, mode, drum = STYLES[style]
    beat = 60 / bpm
    bar = beat * 4
    n = int(duration * SR) + SR
    out = np.zeros(n, dtype=np.float32)
    third = 3 if mode == "minor" else 4

    def add(sig, start):
        i = int(start * SR)
        if i >= n:
            return
        e = min(n, i + len(sig))
        out[i:e] += sig[: e - i]

    kick_t = _t(0.25)
    kick = (np.sin(2 * np.pi * np.cumsum(60 + 90 * np.exp(-kick_t * 30)) / SR)
            * np.exp(-kick_t * 12) * 0.55 * drum).astype(np.float32)
    rng = np.random.default_rng(seed)
    hat_n = rng.standard_normal(int(0.04 * SR)).astype(np.float32)
    hat = np.diff(hat_n, prepend=0) * np.exp(-np.arange(len(hat_n)) / SR * 120) * 0.12 * drum
    clap_n = rng.standard_normal(int(0.15 * SR)).astype(np.float32)
    clap = clap_n * np.exp(-np.arange(len(clap_n)) / SR * 30) * 0.12 * drum

    t_bar = 0.0
    bi = 0
    while t_bar < duration + bar:
        root = roots[bi % len(roots)]
        # pad（三和音、柔らかい矩形っぽい音）
        pt = _t(bar)
        pad = np.zeros_like(pt)
        for iv in (0, third, 7, 12):
            f = note_hz(root + 12 + iv)
            pad += np.sin(2 * np.pi * f * pt) + 0.3 * np.sin(2 * np.pi * 2 * f * pt)
        pad *= _env(len(pt), 0.05, 0.2) * 0.03
        add(pad.astype(np.float32), t_bar)
        for b in range(4):
            tb = t_bar + b * beat
            add(kick, tb)
            if b in (1, 3):
                add(clap, tb)
            for h in range(2):
                add(hat, tb + h * beat / 2)
            # ベース（8分）
            for h in range(2):
                bt = _t(beat / 2 * 0.9)
                f = note_hz(root - 12 + (7 if (b == 3 and h == 1) else 0))
                bs = np.sign(np.sin(2 * np.pi * f * bt)) * 0.5 + np.sin(2 * np.pi * f * bt)
                add((bs * _env(len(bt), 0.003, 0.05) * 0.05).astype(np.float32), tb + h * beat / 2)
        # アルペジオ（16分、上で軽く）
        arp = [0, third, 7, 12, 7, third, 0, 7]
        for k in range(16):
            at = _t(beat / 4 * 0.8)
            f = note_hz(root + 24 + arp[k % len(arp)])
            s = np.sin(2 * np.pi * f * at) * np.exp(-at * 18) * 0.035
            add(s.astype(np.float32), t_bar + k * beat / 4)
        t_bar += bar
        bi += 1
    out = out[: int(duration * SR)]
    # フェードイン・アウト
    fi, fo = int(0.3 * SR), int(1.0 * SR)
    out[:fi] *= np.linspace(0, 1, fi)
    out[-fo:] *= np.linspace(1, 0, fo)
    return out
