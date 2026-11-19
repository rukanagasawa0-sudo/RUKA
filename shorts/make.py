"""使い方:  python3 shorts/make.py [v2 v3 v5] [--preview]

--preview を付けると動画は作らず、数枚の静止画（output/preview）だけ書き出す。
"""
import importlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SCRIPTS = {
    "v2": "scripts.v2_op18_summary",
    "v3": "scripts.v3_price_quiz",
    "v5": "scripts.v5_release_calendar",
    "v6": "scripts.v6_op18_decks",
    "d1": "scripts.decks_single:allsunday",
    "d2": "scripts.decks_single:spandam",
    "d3": "scripts.decks_single:gunshikyu",
    "d4": "scripts.decks_single:carue",
    "d5": "scripts.decks_single:luffy",
    "d6": "scripts.decks_single:mihawk",
}


def main(argv):
    preview = "--preview" in argv
    keys = [a for a in argv if not a.startswith("--")] or list(SCRIPTS)
    for k in keys:
        modname, _, func = SCRIPTS[k].partition(":")
        s = getattr(importlib.import_module(modname), func or "make")()
        t0 = time.time()
        if preview:
            s.build()
            out = os.path.join(HERE, "output", "preview")
            os.makedirs(out, exist_ok=True)
            n = 8
            for i in range(n):
                pt = s.duration * (i + 0.5) / n
                s.frame(pt).save(os.path.join(out, f"{s.slug}_{i}.jpg"), quality=80)
            print(f"{k}: preview {s.duration:.1f}s ({time.time() - t0:.0f}s)")
        else:
            mp4 = s.render(os.path.join(HERE, "output"))
            print(f"{k}: {mp4} {s.duration:.1f}s ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main(sys.argv[1:])
