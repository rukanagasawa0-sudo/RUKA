"""字幕（名札含む）の領域に、画面中央の文字・画像がはみ出していないか全動画を検査する。
python3 shorts/tools/check_overlap.py [v1 ...]"""
import importlib, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import engine.widgets as wg
from make import SCRIPTS

wg.CHECK_MODE = True
Y0, Y1, X0, X1 = 1205, 1550, 30, 1050   # 字幕ボックス＋名札の範囲
keys = sys.argv[1:] or list(SCRIPTS)
bad_total = 0
for k in keys:
    modname, _, func = SCRIPTS[k].partition(":")
    s = getattr(importlib.import_module(modname), func or "make")().build()
    hits = []
    T = 0.0
    while T < s.duration:
        a = np.asarray(s.frame(T, sub=False, title=False))[Y0:Y1, X0:X1].astype(int)
        b = np.asarray(s.frame(T, sub=False, scene=False, title=False))[Y0:Y1, X0:X1].astype(int)
        diff = np.abs(a - b).sum(axis=2) > 60
        if diff.sum() > 150:
            ys = np.where(diff.any(axis=1))[0]
            hits.append((round(T, 1), int(ys.min() + Y0), int(ys.max() + Y0), int(diff.sum())))
        T += 1 / 15
    print(f"{k}: {'OK' if not hits else f'{len(hits)} frames overlap'}")
    for h in hits[:12]:
        print("   t=%.1f  y=%d-%d  px=%d" % h)
    bad_total += len(hits)
sys.exit(1 if bad_total else 0)
