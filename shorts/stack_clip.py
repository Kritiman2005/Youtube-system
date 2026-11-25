"""Stacked 'reaction' layout for the neon._coast_reels account (facecam on top, gameplay below, hook text on the seam).

Built from an ALREADY RENDERED clip (data/out/<creator>/<id>.mp4, 1080x1920 with the original centred at y=656..1264),
so it works even after the raw downloads are deleted.

  python -m shorts.stack_clip <clip_id> [--text "Hook text"] [--emoji 👀] [--cam x:y:w:h] [--game-cx N]
Output: data/out_reels/<creator>/<clip_id>.mp4  (1080x1920, <9.5 MB)
--cam is in ORIGINAL-region pixels (1080x608 frame) and overrides face detection.
"""
import argparse, json, subprocess, sys, re
from pathlib import Path
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
VY, VH = 656, 608            # where the original sits inside the rendered clip
TOP, BOT = 840, 1080         # panel heights
ap = argparse.ArgumentParser()
ap.add_argument("clip"); ap.add_argument("--text", default=""); ap.add_argument("--emoji", default="👀")
ap.add_argument("--cam", default=""); ap.add_argument("--game-cx", type=float, default=None)
ap.add_argument("--region", default="", help="override original region y:h inside the rendered clip")
a = ap.parse_args()

led = json.loads((ROOT / "data/ledger.json").read_text())
clip = next(c for c in led["clips"] if c["id"] == a.clip)
src = ROOT / "data/out" / clip["creator"] / f'{a.clip}.mp4'
out = ROOT / "data/out_reels" / clip["creator"] / f'{a.clip}.mp4'
out.parent.mkdir(parents=True, exist_ok=True)
if a.region:
    VY, VH = [int(v) for v in a.region.split(":")]
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)]))

# ---- find the facecam: Haar faces on several frames of the original region
def frames():
    for k in range(1, 7):
        t = dur * k / 7
        p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1", "-f", "image2pipe", "-vcodec", "bmp", "-"],
                           capture_output=True, stdin=subprocess.DEVNULL).stdout
        im = cv2.imdecode(np.frombuffer(p, np.uint8), 1)
        if im is not None:
            yield im[VY:VY + VH, 0:1080]

cam = None
if a.cam:
    cam = [int(v) for v in a.cam.split(":")]
else:
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    hits = []
    for im in frames():
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        for (x, y, w, h) in casc.detectMultiScale(g, 1.1, 6, minSize=(36, 36)):
            hits.append((x, y, w, h))
    if hits:
        arr = np.array(hits)
        # most common location: cluster by centre, take the biggest cluster median
        cx = arr[:, 0] + arr[:, 2] / 2; cy = arr[:, 1] + arr[:, 3] / 2
        best = max(range(len(arr)), key=lambda i: sum(abs(cx - cx[i]) < 60 and abs(cy - cy[i]) < 60 for _ in [0]) if False else int(((abs(cx - cx[i]) < 60) & (abs(cy - cy[i]) < 60)).sum()))
        m = (abs(cx - cx[best]) < 60) & (abs(cy - cy[best]) < 60)
        fx, fy, fw, fh = np.median(arr[m], axis=0)
        # crop: face centred, 9:7-ish aspect (1080:840), width 3.4x face width (min 220 px)
        cw = max(220, fw * 3.4); ch = cw * TOP / 1080
        ccx = fx + fw / 2; ccy = fy + fh / 2 + fh * 0.15
        x0 = min(max(0, ccx - cw / 2), 1080 - cw); y0 = min(max(0, ccy - ch / 2), VH - ch)
        cam = [int(x0), int(y0), int(cw), int(ch)]
        print("face", [int(v) for v in (fx, fy, fw, fh)], "from", len(hits), "hits ->cam", cam)
if not cam:
    print("NO FACE FOUND - pass --cam x:y:w:h", file=sys.stderr); sys.exit(2)
cx_, cy_, cw_, ch_ = cam
# keep the crop aspect = 1080:TOP
ch_ = int(cw_ * TOP / 1080)
if cy_ + ch_ > VH: cy_ = max(0, VH - ch_)
if ch_ > VH: ch_ = VH; cw_ = int(ch_ * 1080 / TOP)

# game panel: scale region to BOT tall, crop 1080 wide around game centre
gw = int(VH and 1080 * BOT / VH)
gcx = a.game_cx if a.game_cx is not None else 0.5
gx = int(min(max(0, gcx * gw - 540), gw - 1080))

# ---- hook text overlay (white bold, black stroke, emoji) on the seam
text = a.text or clip["title_on_screen"].title().replace("Gta 6", "GTA 6")
W = 1080
ov = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 78, index=1)  # Bold
words, lines, cur = text.split(), [], ""
for w in words:
    t = (cur + " " + w).strip()
    if d.textlength(t, font=font) > W - 200 and cur: lines.append(cur); cur = w
    else: cur = t
lines.append(cur)
lines[-1] += "  "                       # room for emoji
y = 130 - 45 * len(lines)
for i, ln in enumerate(lines):
    tw = d.textlength(ln, font=font)
    x = (W - tw) / 2 - (45 if i == len(lines) - 1 else 0)
    d.text((x, y + i * 90), ln, font=font, fill="white", stroke_width=6, stroke_fill="black")
    if i == len(lines) - 1 and a.emoji:
        ef = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", 160)
        e = Image.new("RGBA", (200, 200), (0, 0, 0, 0)); ImageDraw.Draw(e).text((0, 0), a.emoji, font=ef, embedded_color=True)
        e = e.resize((84, 84)); ov.alpha_composite(e, (int(x + tw + 6), y + i * 90 + 4))
ovp = ROOT / "data/out/_work" / f"{a.clip}.stack_text.png"; ovp.parent.mkdir(exist_ok=True); ov.save(ovp)

BR = int(min(2400, 8.8 * 8192 / max(1.0, dur) - 128))
vf = (f"[0:v]crop=1080:{VH}:0:{VY},split[a][b];"
      f"[a]crop={cw_}:{ch_}:{cx_}:{cy_},scale=1080:{TOP}:flags=lanczos[top];"
      f"[b]scale={gw}:{BOT}:flags=lanczos,crop=1080:{BOT}:{gx}:0[bot];"
      f"[top][bot]vstack[s];[s][1:v]overlay=0:{TOP - 130}[v]")
subprocess.run(["ffmpeg", "-y", "-i", str(src), "-i", str(ovp), "-filter_complex", vf, "-map", "[v]", "-map", "0:a?",
                "-c:v", "libx264", "-crf", "22", "-maxrate", f"{BR}k", "-bufsize", f"{2*BR}k", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", "-c:a", "aac", "-r", "30", str(out)], check=True, stdin=subprocess.DEVNULL,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(out, round(out.stat().st_size / 1e6, 2), "MB")
