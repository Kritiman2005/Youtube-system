"""Tool: generate the consistent channel banner overlay -> assets/banner.png (1080x230, transparent).
python -m shorts.make_banner ["TAGLINE"]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops
A = Path(__file__).resolve().parent.parent / "assets"
tag = sys.argv[1] if len(sys.argv) > 1 else "Daily Clips"
W, H = 1080, 230
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
# soft dark strip so it reads on any background
strip = Image.new("RGBA", (W, H), (10, 4, 24, 150)); img.alpha_composite(strip)
big = ImageFont.truetype(str(A / "fonts/Anton-Regular.ttf"), 125)
script = ImageFont.truetype(str(A / "fonts/Yellowtail-Regular.ttf"), 64)
def gradient_text(txt, font, c1, c2, xy):
    mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).text(xy, txt, font=font, fill=255)
    grad = Image.new("RGBA", (W, H))
    for y in range(H):
        t = y / H; grad.paste(tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)) + (255,), (0, y, W, y + 1))
    return Image.composite(grad, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask), mask
bw = big.getbbox("GTA 6")[2]; x = (W - bw) // 2
# outline + glow
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(shadow)
d.text((x, 6), "GTA 6", font=big, fill=(255, 45, 149, 255), stroke_width=10, stroke_fill=(255, 45, 149, 255))
img.alpha_composite(shadow)
d = ImageDraw.Draw(img); d.text((x, 6), "GTA 6", font=big, fill=(20, 8, 42, 255), stroke_width=7, stroke_fill=(20, 8, 42, 255))
txt, _ = gradient_text("GTA 6", big, (255, 214, 102), (255, 60, 140), (x, 6)); img.alpha_composite(txt)
tw = script.getbbox(tag)[2]
d.text(((W - tw) // 2, 148), tag, font=script, fill=(110, 240, 255, 255), stroke_width=3, stroke_fill=(20, 8, 42, 255))
img.save(A / "banner.png"); print(A / "banner.png")
