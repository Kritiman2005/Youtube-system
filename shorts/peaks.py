"""Tool: list loudest moments in a video.  python -m shorts.peaks FILE [N] [MIN_GAP_SEC]"""
import sys, subprocess, numpy as np
f, n, gap = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 15, int(sys.argv[3]) if len(sys.argv) > 3 else 40
raw = subprocess.run(["ffmpeg","-v","quiet","-i",f,"-ac","1","-ar","16000","-f","s16le","-"],capture_output=True,check=True).stdout
a = np.frombuffer(raw, dtype=np.int16).astype(np.float32); sec = len(a)//16000
rms = np.sqrt((a[:sec*16000].reshape(sec,16000)**2).mean(axis=1))
sc = np.convolve(rms, np.ones(5)/5, mode="same"); out = []
for t in np.argsort(sc)[::-1]:
    if all(abs(t-p) > gap for p in out): out.append(int(t))
    if len(out) == n: break
for t in sorted(out): print(f"t={t}s ({t//60}:{t%60:02}) loudness={sc[t]:.0f}")
