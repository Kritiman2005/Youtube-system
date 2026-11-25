"""Tool: render one 9:16 short (blurred bg + original centered + burned captions).
python -m shorts.render_clip SRC START END OUT [--no-captions] [--model base]"""
import sys, subprocess, argparse
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("start", type=float); ap.add_argument("end", type=float)
ap.add_argument("out"); ap.add_argument("--bg", default="blur", help="blur | gradient | solid | image:PATH | video:PATH")
ap.add_argument("--c1", default="#1a0033"); ap.add_argument("--c2", default="#ff2d95"); ap.add_argument("--title", default="")
ap.add_argument("--no-banner", action="store_true")
ap.add_argument("--src-filter", default="", help="ffmpeg filter applied to the SOURCE video first, e.g. a shadow lift for dark footage: eq=gamma=2.0:brightness=0.08:contrast=1.1")
ap.add_argument("--mask", action="append", default=[], help="blur a region of the SOURCE video: x:y:w:h in source pixels (e.g. a chat panel); repeatable")
ap.add_argument("--bg-trim", type=int, default=10, help="px cropped off the bottom of an image background (removes baked-in labels)")
ap.add_argument("--fit", default="width", help="width (full width, letterboxed) | fill (crop to 9:16)"); ap.add_argument("--no-captions", action="store_true"); ap.add_argument("--model", default="base")
a = ap.parse_args()
if ":" in a.bg and a.bg.split(":",1)[0] in ("image","video"): k, v = a.bg.split(":",1); a.bg = f"{k}:{Path(v).resolve()}"
a.src = str(Path(a.src).resolve()); out = Path(a.out).resolve(); out.parent.mkdir(parents=True, exist_ok=True)
cut = out.with_suffix(".cut.mp4"); srt = out.with_suffix(".srt")
run = lambda c, **k: subprocess.run(c, check=True, capture_output=True, **k)
run(["ffmpeg","-y","-ss",str(a.start),"-to",str(a.end),"-i",a.src,"-c:v","libx264","-c:a","aac",str(cut)])
hexc = lambda c: "0x" + c.lstrip("#")
inputs = ["-i", str(cut)]
if a.bg == "gradient":
    rgb = lambda c: [int(c.lstrip("#")[k:k+2], 16) for k in (0, 2, 4)]
    (r1,g1,b1),(r2,g2,b2) = rgb(a.c1), rgb(a.c2)
    ge = lambda x,y: f"{x}+({y}-{x})*Y/H"
    inputs += ["-f","lavfi","-i",f"color=c=black:s=1080x1920,format=rgb24,geq=r='{ge(r1,r2)}':g='{ge(g1,g2)}':b='{ge(b1,b2)}'"]
    bgf = "[1:v]format=yuv420p[bg]"
elif a.bg == "solid":
    inputs += ["-f","lavfi","-i",f"color=c={hexc(a.c1)}:s=1080x1920"]; bgf = "[1:v]format=yuv420p[bg]"
elif a.bg.startswith("image:"):
    inputs += ["-loop","1","-i",a.bg[6:]]
    # blurred full-frame fill + sharp copy anchored at the bottom, feathered into the blur
    bgf = (f"[1:v]crop=iw:ih-{a.bg_trim}:0:0,split[a][b];"
           "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=45,eq=brightness=-0.18:saturation=1.15[blurbg];"
           "[b]scale=1080:-2:flags=lanczos,format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='255*min(1,Y/70)'[band];"
           "[blurbg][band]overlay=0:H-h[bg]")
elif a.bg.startswith("video:"):
    inputs += ["-stream_loop","-1","-i",a.bg[6:]]
    bgf = "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=-0.15:saturation=1.1[bg]"
else:
    bgf = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5,eq=brightness=-0.12[bg]"
fg = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" if a.fit == "fill" else ("scale=-2:1340" if a.fit == "inset" else "scale=1080:-2")
ROOT = Path(__file__).resolve().parent.parent; BANNER = ROOT / "assets/banner.png"; FONT = ROOT / "assets/fonts/Anton-Regular.ttf"
cur, mparts = "[0:v]", []
if a.src_filter:
    mparts.append(f"[0:v]{a.src_filter}[ef];"); cur = "[ef]"
for i, m in enumerate(a.mask):
    x, y, w, h = [int(v) for v in m.split(":")]
    mparts.append(f"{cur}split[a{i}][b{i}];[b{i}]crop={w}:{h}:{x}:{y},boxblur=30:6[m{i}];[a{i}][m{i}]overlay={x}:{y}[o{i}];"); cur = f"[o{i}]"
vf = f"{bgf};{''.join(mparts)}{cur}{fg}[fg];[bg][fg]overlay=(W-w)/2:{'500' if a.fit == 'inset' else '(H-h)/2'}:shortest=1[v0]"
if BANNER.exists() and not a.no_banner:
    inputs += ["-loop", "1", "-i", str(BANNER)]
    vf += f";[{inputs.count('-i') - 1}:v]format=rgba[bn];[v0][bn]overlay=(W-w)/2:90:shortest=1[v0]"
vf += ";[v0]null"  # next filters chain onto [v0]
if a.title:
    t = a.title.replace("\\","").replace(":","\\:").replace("'","")
    vf += f",drawtext=text='{t}':fontfile={FONT}:fontsize=84:fontcolor=white:borderw=6:bordercolor=0x14082a:x=(w-text_w)/2:y=360"
if not a.no_captions:
    from faster_whisper import WhisperModel
    segs, _ = WhisperModel(a.model, compute_type="int8").transcribe(str(cut))
    ts = lambda t: f"{int(t//3600):02}:{int(t%3600//60):02}:{int(t%60):02},{int(t%1*1000):03}"
    with open(srt, "w") as f:
        for i, s in enumerate(segs, 1): f.write(f"{i}\n{ts(s.start)} --> {ts(s.end)}\n{s.text.strip()}\n\n")
    if srt.stat().st_size: vf += f",subtitles={srt.name}:force_style='FontSize=14,Bold=1,Outline=3,Alignment=2,MarginV=45'"
BR = int(min(2400, 8.8 * 8192 / max(1.0, a.end - a.start) - 128))  # video kbps so the file stays under ~9.5 MB (upload tool cap ~10 MB)
run(["ffmpeg","-y"]+inputs+["-filter_complex",vf,"-shortest","-c:v","libx264","-crf","23","-maxrate",f"{BR}k","-bufsize",f"{2*BR}k","-movflags","+faststart","-c:a","aac","-r","30",str(out)], cwd=str(out.parent))
# tidy: intermediates go to data/out/_work (keeps creator folders clean); output stays under the ~9.5 MB upload cap via the bitrate cap above
import shutil
work = out.parent.parent / "_work"; work.mkdir(exist_ok=True)
for t in (cut, srt):
    if t.exists(): shutil.move(str(t), str(work / t.name))
print(out)
