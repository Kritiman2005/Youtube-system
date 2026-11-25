# GTA 6 clips -> Instagram (Neon Coast)
Single source of truth: `data/ledger.json` (every clip, source, used window, post link, lesson learned). Read it with
`python -m shorts.ledger summary | sources | used <source_id> | next <creator>`; agents update it via `add-clip` / `set-post` / `event`.
`data/out/INDEX.md` is generated from it. Old per-run json files are in `data/archive/` (history only).
Commands: `/insta` (every creator in config, one clip at a time) and `/insta-creator <name>` (one creator, e.g. `/insta-creator ishowspeed`); both follow `.claude/pipeline.md`. (`/make-shorts` is the older version.)
Run (old): `/make-shorts` - serial, one clip at a time: scout -> clipper -> renderer -> shorts-instagram (YouTube paused).
Agents live in `.claude/agents/`. Backgrounds: `assets/backgrounds/` (see CATALOGUE.md). Creators: `config.yaml`.
