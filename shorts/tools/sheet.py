import sys
from PIL import Image, ImageDraw, ImageFont
out, *ids = sys.argv[1:]
cols = 7
m = Image.new('RGB', (260 * cols, 400 * ((len(ids) + cols - 1) // cols)), 'white')
d = ImageDraw.Draw(m); f = ImageFont.truetype('fonts/NotoSansJP-Black.ttf', 22)
for i, c in enumerate(ids):
    im = Image.open(f'assets/official/cards/{c}.png').convert('RGB'); im.thumbnail((250, 350))
    m.paste(im, ((i % cols) * 260, (i // cols) * 400)); d.text(((i % cols) * 260, (i // cols) * 400 + 355), c, fill='black', font=f)
m.save(out)
