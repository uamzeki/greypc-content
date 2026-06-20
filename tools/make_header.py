#!/usr/bin/env python3
"""Grey PC branded blog header generator.
Usage: python3 make_header.py "Article Title" output.png [kicker]
Produces a 1200x675 on-brand featured image. No external services."""
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 675
TITLE = sys.argv[1] if len(sys.argv) > 1 else "Grey PC"
OUT   = sys.argv[2] if len(sys.argv) > 2 else "header.png"
KICKER= sys.argv[3] if len(sys.argv) > 3 else "GREY PC  ·  BAHRAIN"

BOLD  = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
SEMI  = "/usr/share/fonts/truetype/google-fonts/Poppins-SemiBold.ttf"
LIGHT = "/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf"
import os
if not os.path.exists(SEMI): SEMI = BOLD

ACCENT = (56, 189, 248)   # sky-blue tech accent
TOP    = (14, 16, 21)     # near-black grey
BOT    = (28, 35, 51)     # deep slate

# vertical gradient
base = Image.new("RGB", (W, H), TOP)
top = Image.new("RGB", (W, H), TOP)
bot = Image.new("RGB", (W, H), BOT)
mask = Image.new("L", (W, H))
md = mask.load()
for y in range(H):
    v = int(255 * (y / H) ** 1.1)
    for x in range(W):
        md[x, y] = v
base = Image.composite(bot, top, mask)
d = ImageDraw.Draw(base)

# faint diagonal accent panel on the right
panel = Image.new("RGBA", (W, H), (0,0,0,0))
pd = ImageDraw.Draw(panel)
pd.polygon([(W*0.66, 0), (W, 0), (W, H), (W*0.50, H)], fill=(56,189,248,16))
pd.polygon([(W*0.78, 0), (W, 0), (W, H), (W*0.64, H)], fill=(56,189,248,12))
base = Image.alpha_composite(base.convert("RGBA"), panel).convert("RGB")
d = ImageDraw.Draw(base)

# subtle dot grid
for gy in range(60, H-40, 46):
    for gx in range(70, int(W*0.62), 46):
        d.ellipse([gx, gy, gx+2, gy+2], fill=(255,255,255,12))

MX = 70
# kicker
fk = ImageFont.truetype(SEMI, 26)
d.text((MX, 70), KICKER.upper(), font=fk, fill=(150,160,175))
# accent bar
d.rectangle([MX, 120, MX+74, 126], fill=ACCENT)

# title wrap
def wrap(text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

size = 70
while size > 40:
    ft = ImageFont.truetype(BOLD, size)
    lines = wrap(TITLE, ft, W*0.74)
    lh = size * 1.16
    if len(lines) * lh <= 360 and len(lines) <= 4:
        break
    size -= 4

y = 180
for ln in lines:
    d.text((MX, y), ln, font=ft, fill=(244,247,250))
    y += int(size * 1.16)

# footer url
furl = ImageFont.truetype(SEMI, 28)
d.text((MX, H-70), "greypc.net", font=furl, fill=ACCENT)

base.save(OUT, "PNG")
print("wrote", OUT, base.size)
