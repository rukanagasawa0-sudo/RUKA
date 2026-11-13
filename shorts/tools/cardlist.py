"""公式カードリストから (id, rarity, type, name, image_url) を取る。"""
import json, os, re, sys, urllib.request

BASE = "https://www.onepiece-cardgame.com"
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "cardlist")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def series(sid):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, f"{sid}.json")
    if os.path.exists(p):
        return json.load(open(p))
    h = fetch(f"{BASE}/cardlist/?search=true&series={sid}").decode()
    out = []
    for chunk in h.split('<dl class="modalCol" id="')[1:]:
        cid, body = chunk.split('"', 1)
        info = re.search(r'<span>([^<]*)</span> \| <span>([^<]*)</span> \| <span>([^<]*)</span>', body)
        name = re.search(r'<div class="cardName">([^<]*)</div>', body)
        img = re.search(r'data-src="\.\./(images/cardlist/card/[^"?]+)', body)
        color = re.search(r'<h3>色</h3>([^<]*)<', body)
        out.append(dict(id=cid, no=info.group(1) if info else "", rarity=info.group(2) if info else "",
                        type=info.group(3) if info else "", name=name.group(1) if name else "",
                        color=color.group(1) if color else "",
                        img=f"{BASE}/{img.group(1)}" if img else ""))
    json.dump(out, open(p, "w"), ensure_ascii=False, indent=0)
    return out


if __name__ == "__main__":
    sid, *pat = sys.argv[1:]
    for c in series(sid):
        if not pat or any(x in c["name"] or x == c["rarity"] or x in c["id"] for x in pat):
            print(c["id"], c["rarity"], c["type"], c["name"], c["color"])
