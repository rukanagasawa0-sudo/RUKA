"""VOICEVOX 音声合成（HTTP API）。結果は shorts/cache/tts にキャッシュする。

ENGINE_URLS に VOICEVOX ENGINE 互換の URL を並べておくと上から順に試す。
ローカルで VOICEVOX を起動しているなら http://127.0.0.1:50021 を先頭に入れる。
"""
import hashlib
import io
import json
import os
import time
import urllib.parse
import urllib.request
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "tts")
ENGINE_URLS = [u for u in os.environ.get("VOICEVOX_URLS", "").split(",") if u] or [
    "http://127.0.0.1:50021",
    "https://jahirrrr-voicevox-engine.hf.space",
]
SR = 48000


def _post(url, data=None, timeout=120):
    req = urllib.request.Request(url, data=data, method="POST")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _wav_to_np(raw):
    with wave.open(io.BytesIO(raw)) as w:
        sr = w.getframerate()
        n = w.getnframes()
        ch = w.getnchannels()
        a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
    if ch == 2:
        a = a.reshape(-1, 2).mean(axis=1)
    if sr != SR:
        x_old = np.linspace(0, 1, len(a), endpoint=False)
        x_new = np.linspace(0, 1, int(len(a) * SR / sr), endpoint=False)
        a = np.interp(x_new, x_old, a).astype(np.float32)
    return a


def synth(text, speaker, speed=1.15, pitch=0.0, intonation=1.15, volume=1.0):
    """text を speaker(style id) で読み上げ、48kHz mono float32 の numpy 配列を返す。"""
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.sha1(json.dumps([text, speaker, speed, pitch, intonation, volume],
                                  ensure_ascii=False).encode()).hexdigest()[:16]
    path = os.path.join(CACHE, f"{key}.wav")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return _wav_to_np(f.read())
    last = None
    for base in ENGINE_URLS:
        for attempt in range(3):
            try:
                q = _post(f"{base}/audio_query?" + urllib.parse.urlencode(
                    {"text": text, "speaker": speaker}), timeout=30)
                q = json.loads(q)
                q.update(speedScale=speed, pitchScale=pitch, intonationScale=intonation,
                         volumeScale=volume, prePhonemeLength=0.02, postPhonemeLength=0.04,
                         outputSamplingRate=SR)
                raw = _post(f"{base}/synthesis?speaker={speaker}",
                            json.dumps(q).encode(), timeout=180)
                with open(path, "wb") as f:
                    f.write(raw)
                return _wav_to_np(raw)
            except Exception as e:  # noqa: BLE001 - try next engine / retry
                last = e
                if "127.0.0.1" in base:
                    break
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"VOICEVOX synthesis failed: {text!r}: {last}")
