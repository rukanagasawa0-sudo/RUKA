"""公式カード画像を assets/official/cards に保存。 python3 tools/getcard.py OP13-118_p1 ..."""
import os, sys, urllib.request
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "official", "cards")
os.makedirs(OUT, exist_ok=True)
for cid in sys.argv[1:]:
    p = os.path.join(OUT, f"{cid}.png")
    if os.path.exists(p):
        continue
    req = urllib.request.Request(f"https://www.onepiece-cardgame.com/images/cardlist/card/{cid}.png",
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(p, "wb") as f:
        f.write(r.read())
    print("ok", cid)
