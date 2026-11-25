"""Tool: dominant vivid colors of an image/frame.  python -m shorts.palette FRAME.jpg  -> prints '#hex #hex avg_brightness'"""
import sys, subprocess, numpy as np, colorsys
raw = subprocess.run(["ffmpeg","-v","quiet","-i",sys.argv[1],"-vf","scale=48:48","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True,check=True).stdout
px = np.frombuffer(raw, dtype=np.uint8).reshape(-1,3)
q = (px//32)*32+16; vals, cnt = np.unique(q, axis=0, return_counts=True)
def score(v,c):
    h,s,l = colorsys.rgb_to_hsv(*(v/255)); return c*(0.2+s)*(0.3+l)
order = sorted(zip(vals,cnt), key=lambda x:-score(*x)); picks=[]
for v,c in order:
    if all(np.abs(v.astype(int)-p).sum()>120 for p in picks): picks.append(v.astype(int))
    if len(picks)==2: break
while len(picks)<2: picks.append(picks[0]//2)
print(" ".join("#%02x%02x%02x"%tuple(p) for p in picks), f"brightness={px.mean():.0f}")
