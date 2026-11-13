"""トレカラフテル通販のカテゴリから (商品名, 価格, 在庫表示, URL) を取る。 python3 tools/raftel.py 284 [検索語]"""
import re, sys, urllib.request

def fetch(cat, page=1):
    url = f"https://www.tcg-raftel.com/product-list/{cat}" + (f"?page={page}" if page > 1 else "")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")

def items(cat):
    h = fetch(cat)
    out = []
    for blk in h.split('<div class="item_data">')[1:]:
        name = re.search(r'<span class="goods_name">(.*?)</span>', blk, re.S)
        price = re.search(r'class="figure">\s*([\d,]+)', blk) or re.search(r'([\d,]{3,})\s*円', blk)
        link = re.search(r'href="(https://www.tcg-raftel.com/product/\d+)"', blk)
        stock = "売切" if re.search(r'売り?切|SOLD|在庫なし', blk) else ""
        if name:
            out.append((re.sub(r'\s+', ' ', name.group(1)).strip(), price.group(1) if price else "?", stock,
                        link.group(1) if link else ""))
    return out

if __name__ == "__main__":
    cat, *pat = sys.argv[1:]
    for n, p, s, u in items(cat):
        if not pat or any(x in n for x in pat):
            print(p, s, n, u)
