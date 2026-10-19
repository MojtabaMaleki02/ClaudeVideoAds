# ClaudeVideoAds: the `clipzing-ads` skill for Claude Code

A Claude Code skill that makes premium advertising videos for **Clipzing** entirely in code. It covers TikTok,
YouTube Shorts and Reels verticals (9:16), horizontal films (16:9), and long-form product tours. No AI video
generation and no stock montages: a Python 2.5D renderer with a real perspective camera, Clipzing's own brand and
UI, a voice-over that drives the picture, original music and sound made in code, a measured mix, and frame-by-frame QA.

## What's inside
```
clipzing-ads/
  SKILL.md                 the operating manual Claude follows (workflow, non-negotiables, toolkit reference)
  reference/               craft.md · brand.md · product-facts.md · concepts.md (9 concepts) · formats.md ·
                           needs.md (what to ask for) · lessons.md (real post results) · examples/ (worked films)
  templates/               film_short.py (9:16 + 16:9) · film_long.py (chaptered tours) · mix.py · brief.md
  scripts/new_ad.py        start a project: brief, film, mix, folders, commands
  toolkit/adkit/           the renderer: core (camera, planes, compositing, the line of light, grade) · brand ·
                           ui (Clipzing's UI kit) · fx (slams, swarm, shards, sweeps) · timeline (word timings, cues) ·
                           audio (music in code, ~30 SFX, the sonic logo, mix, master, measurement) · voice · qa
  toolkit/render.py        stills · preview · parallel full renders · encode
  toolkit/capture/         renders Clipzing's own assets through its real code (needs the Clipzing frontend repo):
                           Zing poses from his rig, his podcast footage, the wordmark, the REAL caption engine,
                           and real dashboard screens with fictional data (screens/)
  assets/                  brand marks + OFL fonts (Plus Jakarta Sans, Inter, Instrument Serif, JetBrains Mono, …)
  library/                 pre-rendered: 37 Zing poses, 7 footage scenes, 22 app screens (desktop + mobile)
```

## Install
```bash
git clone https://github.com/MojtabaMaleki02/ClaudeVideoAds.git
cp -r ClaudeVideoAds/clipzing-ads ~/.claude/skills/          # or <project>/.claude/skills/
```
Check the install: `python3 ~/.claude/skills/clipzing-ads/toolkit/selftest.py` (should print ALL PASS).

Then ask Claude Code: *"Make a 20-second TikTok ad for Clipzing about autopilot"*, or *"/clipzing-ads a 90-second
product tour"*.

## Requirements
- Python 3.10+ with `numpy`, `Pillow`, `opencv-python`, `scipy`, `faster-whisper`; `ffmpeg` on the PATH.
- A voice: `OPENAI_API_KEY` (gpt-4o-mini-tts), or better `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID`.
- Optional: an SFX library folder (`SFX_LIBRARY=/path`). Otherwise every sound is synthesized.
- Optional, for new captures: Node 18+ and the Clipzing frontend repo (`CLIPZING_FE=/path/to/shortn-fe`) with
  its `node_modules` (esbuild, tailwindcss, playwright-core) and Google Chrome.
- Set `ADKIT=/path/to/clipzing-ads/toolkit` if the skill doesn't live at `~/shorten/.claude/skills/clipzing-ads`.

## Rules the skill enforces
Every claim must be true (reference/product-facts.md, `qa.claims_lint`). Only Clipzing's own brand, never another
brand's characters, fonts, sounds or trademarks. No real people unless their rights are cleared; no celebrities.
The hook lands in 0.3 s, the brand appears within 2 s, the camera is one continuous move, and every word on screen
arrives with the voice. Master at −14 LUFS / ≤ −1.25 dBTP, music ≥ 12 dB under every word, and the final mix must
read to Whisper exactly like the dry voice.

## Notes
- The brand assets (Zing, the wordmark, the screens) belong to Clipzing. The fonts are under the SIL Open Font
  License (see `assets/fonts`).
- Two worked examples: *The Path* (the first film) and *The Link* (`reference/examples/the-link/film.py`, the
  reference implementation).
