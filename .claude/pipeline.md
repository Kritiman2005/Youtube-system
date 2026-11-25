# Instagram clip pipeline (shared procedure for /insta and /insta-creator)

Goal: make and post ONE good GTA 6 Reel at a time for each creator in scope, Instagram only (account neon._coast). YouTube is paused. Everything is recorded in the ledger.

## Standing rules (decided by the user)
- Posting is authorised for these runs without a review stop, BUT you (the main session) must look at the rendered frames yourself before every post.
- Ordinary swearing is fine. NEVER use a moment with slurs (voice, game NPC dialogue, subtitles, on-screen chat/donation text). Blur chat panels with `render_clip --mask x:y:w:h`.
- No cutscene/trailer/menu/map/black-screen footage. Live gameplay with the creator's own voice/reaction carrying it. 12-40 s, clean cut points.
- Instagram only. Do NOT upload to YouTube. Do NOT submit anything on Content Rewards, connect accounts, or touch Whop - just tell the user when a Reel for a campaign creator is posted (the campaign wants the link within 30 minutes) so they can submit it.
- Campaign creators (lacy, clix, yourrage, kai_cenat, asianjeff, dylan_page): backgrounds with NO GTA VI logo (never key-art-collage.jpg / logo-crab-festival-beach.png), blur any stream/brand logo in the footage, caption must name the creator + the campaign hashtag (see `ledger['campaigns']`), creator must be on screen/main focus. Skip bendadonnn (Puffco) and brettliftsxp unless the user names them.
- Never reuse a source window: ALWAYS check the ledger first.
- Disk is tight: after a clip is posted delete that source's raw download and any probe files (`data/raw/<id>_*.mp4`, `data/probe/*`) unless the next clip for the same source needs it. Keep final clips in data/out.

## Two Instagram accounts (from 2026-11-22)
- Main account `neon._coast` (blurred/image background look, what the steps below produce) AND second account `neon._coast_reels` (stacked layout: facecam on top, gameplay below, hook text on the seam).
- After the main post, make the stacked version: `python3 -m shorts.stack_clip <clip_id> [--cam x:y:w:h] [--text "..."]` -> `data/out_reels/<creator>/<id>.mp4` (cam box is in the original-region 1080x608 frame; auto face-detect often misses - look at the frame and pass --cam; check a frame before posting). Post it on `neon._coast_reels` with the SAME caption, then `ledger set-post <id> instagram_reels posted <url>`.
- The two accounts are two Chrome tabs; use the tab that shows the right profile ('Edit Profile'). NEVER log in, type passwords, or click Instagram's 'Confirm you're human' / suspended-account Continue step - stop and tell the user. neon._coast_reels hit that check after 10 uploads in ~2 hours: keep to a few Reels per account per run and leave gaps.

## Procedure for ONE creator (finish it completely before the next)
0. Read state: `python -m shorts.ledger summary`, `python -m shorts.ledger sources`, and for the creator `python -m shorts.ledger used <source_id>` for each of their sources. Read config.yaml (creator channel URLs) and, for campaign creators, `ledger['campaigns'][<creator_folder>]` (hashtag/name rules).
1. Choose a source: a finished (not live/upcoming) GTA 6 stream replay with unused material (the ledger lists used windows; a source can be reused with a NEW non-overlapping window). If none, run the `shorts-scout` agent restricted to that creator and have it write data/sources.json (it must not touch the ledger). Check `ledger['unused_candidates']`. If the creator has no usable source, skip and log an event.
2. Find the window (long streams are mostly cutscenes/menus/idle):
   - Use the `shorts-clipper` agent in PHASE A ONLY: it probes ~6 spread-out 100-s snippets (foreground, retry once on HTTP 403) and writes data/probe_report.json with a recommended 25-min window + a backup. Tell it not to download a big window, not to create moments.json, not to touch the ledger, to do everything in the foreground, and to delete its probe files. For short sources (< 2 h) or when you already know the window you may skip the probe.
3. Download the window YOURSELF in the background (agents stall when they hand back mid-download):
   `nohup yt-dlp -f "bv*[height<=720]+ba/b" --merge-output-format mp4 --download-sections "*START-END" --remote-components ejs:github -o data/raw/<id>_<x>.mp4 "<url>" > data/raw/<id>_<x>.log 2>&1 &`
   then wait with a background command (run_in_background) that loops `while pgrep -f "yt-dlp.*<id>" >/dev/null; do sleep 20; done` and prints done/FAILED; you get notified. On HTTP 403 retry once. Never start two downloads at once.
4. Pick the moment: run the `shorts-clipper` agent on the FINISHED file (tell it the file is ready, not to download anything and not to start background processes, to run `ledger used`/`ledger next`, write data/moments.json with ONE moment incl. stream_start/stream_end, and to register the window with `ledger add-window`). Rules above apply (slur check word by word, read chat/overlay text at the cut points). If it returns [] skip the creator (log `ledger event` with the reason). If the clipper stalls or its report is lost, do the analysis yourself (peaks via `python -m shorts.peaks`, contact sheet of frames at the top peaks, whisper on candidates).
5. Render: `shorts-renderer` agent on the moment (it registers the clip in the ledger, output `data/out/<creator>/<creator>_NN.mp4`). Tell it: the creator's campaign rules if any, to mask chat/logos with `--mask`, captions only if accurate, title <=24 chars, <9.5 MB (upload tool cap ~10 MB), `--fit inset` for vertical (360x640-style) sources.
6. YOU review the output: ffprobe (1080x1920, duration, size) and a contact sheet of 4-5 frames; check title not clipped, background contrasts, nothing readable that is profane/slur-like, logos masked for campaign creators. If it is bad, fix (re-render) or skip - do not post junk.
7. Post with the `shorts-instagram` agent (one Reel): give it the clip id, file path and the EXACT caption (hook + emoji, newline, `Original: <Creator> <source url>`, newline, hashtags `#GTA6 #<Creator> #gaming #reels`, plus the campaign hashtag/name for campaign creators). Remind it to choose 'Post' (not 'Live video') at the Create menu. It records the Reel with `ledger set-post <clip_id> instagram posted <url>`.
8. Verify: `python -m shorts.ledger summary` shows the clip posted. Clean up disk (delete raw/probe files for that source). Tell the user the Reel link (and, for campaign creators, the 30-minute submission reminder).
9. If any step fails: log `python -m shorts.ledger event "<what and why>"`, skip that creator, continue with the next.

## Final report
Run `python -m shorts.ledger summary` and give the user: posted Reels (links), skipped creators + reasons, anything they need to do. Be honest about weak clips.
