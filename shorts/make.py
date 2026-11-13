"""使い方:  python3 shorts/make.py [v1 v2 ...] [--preview]

--preview を付けると動画は作らず、数枚の静止画（output/preview）だけ書き出す。
"""
import importlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SCRIPTS = {
    "v1": "scripts.v1_box_ranking",
    "v2": "scripts.v2_op18_summary",
    "v3": "scripts.v3_price_quiz",
    "v4": "scripts.v4_meta_share",
    "v5": "scripts.v5_release_calendar",
}


def main(argv):
    preview = "--preview" in argv
    keys = [a for a in argv if not a.startswith("--")] or list(SCRIPTS)
    for k in keys:
        mod = importlib.import_module(SCRIPTS[k])
        s = mod.make()
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
