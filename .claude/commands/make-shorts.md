---
description: Serial Instagram-only pipeline - one clip at a time (clip -> render -> post), then the next creator
argument-hint: [creator names, default = all in config]
---
Instagram only (YouTube is paused). First read the ledger: `python -m shorts.ledger summary` and `python -m shorts.ledger sources` - it is the single record of what has been made, which windows are used, what is posted. Do not use old json files.
Run ONE clip at a time, fully finished before the next: for each creator in $ARGUMENTS (default: the creators in config.yaml with GTA 6 material), do
1. shorts-scout (only if no usable source with unused windows exists in the ledger) -> data/sources.json
2. shorts-clipper for that ONE source -> data/moments.json (one moment; wait for it to really finish; if it returns [] skip this creator)
3. shorts-renderer for that moment -> data/rendered.json, registers the clip in the ledger
4. Review the rendered frames yourself, then shorts-instagram to post it (the user has authorised unreviewed posting for these runs) and confirm the ledger shows it posted
Then move to the next creator. If a step fails, skip that creator, log it with `python -m shorts.ledger event`, and continue. At the end report the summary from the ledger.
