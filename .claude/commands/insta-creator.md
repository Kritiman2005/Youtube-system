---
description: Make and post one Instagram Reel for ONE specific creator (e.g. /insta-creator ishowspeed)
argument-hint: <creator name, e.g. ishowspeed | n3on | carryminati | kai cenat | lacy | asianjeff | mythpat | clix | yourrage | dylan page>
---
Read `.claude/pipeline.md` and follow it exactly, for ONLY this creator: $ARGUMENTS

Match the name (case/spacing-insensitive) to a creator folder in the ledger/config: ishowspeed, n3on, carryminati (also CarryisLive), kai_cenat, asianjeff, mythpat, lacy, clix, yourrage, dylan_page, brettliftsxp, bendadonnn, live_insaan, ujjwal, typical_gamer. If $ARGUMENTS is empty, ask the user which creator. If the name is NOT in config.yaml: find their official YouTube channel (verify with yt-dlp: name, subscribers, GTA 6 content), tell the user what you found, and add it to `config.yaml` `channels:` (a `# comment` with the name) before proceeding; if you cannot verify it, say so and stop. If the user named bendadonnn or brettliftsxp, warn about their campaign requirements first (Puffco product / Brett's tag+banner) and ask before posting.

Make exactly ONE new clip for this creator and finish it (clip -> render -> your own frame check -> Instagram post -> ledger updated). If the first source/window yields nothing clean, you may try ONE more window or source for this creator before giving up and logging why. Report the Reel link when done (plus the 30-minute Content Rewards submission reminder if the creator has a campaign).
