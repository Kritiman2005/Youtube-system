"""Single source of truth for everything we have made and posted: data/ledger.json.

Agents: READ this before choosing sources/windows, and WRITE to it after rendering/posting.
The ledger keeps working even if the video files / raw downloads are deleted.

  python -m shorts.ledger summary                 # one line per clip + status
  python -m shorts.ledger sources                 # every source video + windows already used
  python -m shorts.ledger used <source_id>        # windows/clips already used for a source (stream-time seconds)
  python -m shorts.ledger next <creator_folder>   # next free clip id, e.g. mythpat_04
  python -m shorts.ledger clip <clip_id>          # full record of one clip
  python -m shorts.ledger add-clip '<json>'       # register a new clip (after rendering)
  python -m shorts.ledger add-window '<json>'     # {"source_id","stream_start","stream_end","file","outcome","note"}
  python -m shorts.ledger set-post <clip_id> <instagram|youtube> <status> [url] [note]
  python -m shorts.ledger event "<text>"          # append a dated note (claims, limits, drafts...)
  python -m shorts.ledger index                   # regenerate data/out/INDEX.md from the ledger
All times in the ledger are STREAM time (seconds from the start of the source video), not file-relative.
"""
import json, sys, re, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "data" / "ledger.json"


def load():
    return json.loads(LEDGER.read_text())


def save(d):
    tmp = LEDGER.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=1, ensure_ascii=False))
    tmp.replace(LEDGER)


def fmt(t):
    t = int(t)
    return f"{t//3600}:{t%3600//60:02}:{t%60:02}"


def st(clip, plat):
    p = clip.get(plat) or {}
    return p.get("status", "-")


def cmd_summary(d):
    for c in d["clips"]:
        print(f'{c["id"]:<16} {c["source_id"]:<12} {fmt(c["source_start"])}-{fmt(c["source_end"])}  IG:{st(c,"instagram"):<9} YT:{st(c,"youtube"):<14} {c["title_on_screen"]}')
    print(f'\n{len(d["clips"])} clips | IG posted: {sum(1 for c in d["clips"] if st(c,"instagram")=="posted")} | '
          f'YT posted: {sum(1 for c in d["clips"] if st(c,"youtube")=="posted")}')


def cmd_sources(d):
    for sid, s in d["sources"].items():
        print(f'{sid}  {s["creator"]:<12} {s.get("duration_h","?")}h  {s["title"][:60]}')
        for w in s["windows"]:
            print(f'    {fmt(w["stream_start"])}-{fmt(w["stream_end"])}  {w["outcome"]}: {w.get("note","")[:100]}')
    print("\nUnused candidate sources:")
    for u in d.get("unused_candidates", []):
        print("  ", u)


def cmd_used(d, sid):
    s = d["sources"].get(sid)
    if not s:
        print(f"{sid}: not in ledger (fresh source)")
        return
    print(f'{sid} ({s["creator"]}) {s["title"]}')
    print("windows downloaded/looked at (stream time):")
    for w in s["windows"]:
        print(f'  {fmt(w["stream_start"])}-{fmt(w["stream_end"])}  {w["outcome"]}: {w.get("note","")}')
    print("clips already made from this source (do NOT reuse/overlap):")
    for c in d["clips"]:
        if c["source_id"] == sid:
            print(f'  {c["id"]}  {fmt(c["source_start"])}-{fmt(c["source_end"])}  {c["title_on_screen"]}')
    for r in d.get("rejected_moments", []):
        if r["source_id"] == sid:
            print(f'  REJECTED {fmt(r["source_start"])}-{fmt(r["source_end"])}: {r["reason"]}')


def cmd_next(d, creator):
    n = 1 + max([int(c["id"].rsplit("_", 1)[1]) for c in d["clips"] if c["creator"] == creator] or [0])
    print(f"{creator}_{n:02d}")


def cmd_index(d):
    rows = ["# Clip index (generated from data/ledger.json - edit the ledger, not this file)\n",
            "| clip | source (stream time) | title | Instagram | YouTube |", "|---|---|---|---|---|"]
    for c in d["clips"]:
        ig, yt = c.get("instagram") or {}, c.get("youtube") or {}
        rows.append(f'| {c["creator"]}/{c["id"]}.mp4 | {c["source_id"]} {fmt(c["source_start"])}-{fmt(c["source_end"])} | {c["title_on_screen"]} | '
                    f'{ig.get("status","-")} {ig.get("url","")} | {yt.get("status","-")} {yt.get("url","")} {yt.get("note","")} |')
    (ROOT / "data/out/INDEX.md").write_text("\n".join(rows) + "\n")
    print("wrote data/out/INDEX.md")


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    d = load()
    c = a[0]
    if c == "summary": cmd_summary(d)
    elif c == "sources": cmd_sources(d)
    elif c == "used": cmd_used(d, a[1])
    elif c == "next": cmd_next(d, a[1])
    elif c == "index": cmd_index(d)
    elif c == "clip":
        print(json.dumps(next(x for x in d["clips"] if x["id"] == a[1]), indent=1, ensure_ascii=False))
    elif c == "add-clip":
        new = json.loads(a[1])
        assert not any(x["id"] == new["id"] for x in d["clips"]), "clip id already exists"
        new.setdefault("created", datetime.datetime.now().isoformat(timespec="minutes"))
        d["clips"].append(new); save(d); print("added", new["id"])
    elif c == "add-window":
        w = json.loads(a[1]); sid = w.pop("source_id")
        d["sources"].setdefault(sid, {"creator": w.pop("creator", "?"), "title": w.pop("title", sid), "url": f"https://www.youtube.com/watch?v={sid}", "windows": []})
        d["sources"][sid]["windows"].append(w); save(d); print("window added to", sid)
    elif c == "set-post":
        clip = next(x for x in d["clips"] if x["id"] == a[1])
        rec = clip.setdefault(a[2], {})
        rec["status"] = a[3]
        if len(a) > 4 and a[4]: rec["url"] = a[4]
        if len(a) > 5: rec["note"] = a[5]
        rec["updated"] = datetime.datetime.now().isoformat(timespec="minutes")
        save(d); print("updated", a[1], a[2], a[3])
    elif c == "event":
        d["events"].append({"time": datetime.datetime.now().isoformat(timespec="minutes"), "text": a[1]}); save(d); print("event added")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
