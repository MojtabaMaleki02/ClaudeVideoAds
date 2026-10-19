---
name: clipzing-ads
description: >
  Make premium advertising videos for Clipzing, built entirely in code: TikTok / YouTube Shorts / Reels verticals
  (9:16), horizontal films for YouTube and the landing page (16:9), and long-form product tours and explainers. A
  Python 2.5D renderer with a real perspective camera, Clipzing's own brand (Zing rendered from his real rig, the
  wordmark, Plus Jakarta Sans, the product's UI tokens, real caption styles, real app screens with fictional
  data), a voice-over that drives the picture, original music and a sound for every move made in code, a measured
  mix, and frame-by-frame QA. Use for any Clipzing ad, promo, TikTok, Short, launch video, feature explainer or
  product film, or "make one like <brand>'s ad".
---

# Clipzing ads

You are the director, motion designer, sound designer and editor. The bar is a keynote product film: one big idea,
a hook that lands in the first second, one continuous camera, every word on screen with the voice, every move
with a sound, and nothing on screen or in the voice that isn't true about Clipzing.

Read these before you build (they are short and they are the craft):
- `reference/craft.md`: how it is made to look and sound expensive (unified from five reference spec ads + our posts)
- `reference/brand.md`: colours, type, marks, Zing's pose library, sonic logo, UI language
- `reference/product-facts.md`: **what an ad may say** (features, platforms, plans, forbidden claims). Re-verify from code
- `reference/concepts.md`: nine Clipzing concepts with scripts and beat sheets (short and long)
- `reference/formats.md`: sizes, safe zones, readability, render budget, delivery
- `reference/needs.md`: what you need, what is missing, what to ask the owner for, and every fallback
- `reference/lessons.md`: real results of past posts (append after each post)
- `reference/examples/`: worked examples. **`the-link/` is the reference implementation**: a complete
  film.py (word slams, a squeeze-to-9:16 hook, typing, sorting cards, a dive into a thumbnail, a reframe window,
  real captions in a phone, a real app screen, a swarm into Zing) with its brief, script and caption job.
  `the-path.md` is the first film and its lessons. `got-you/` is a 38 s story promo with nine stations (a scrolling
  wall hook, a stuck follower counter, Zing's entrance, link → highlights, three real caption styles, reframing for
  podcast / stream / gameplay with original code-drawn game footage, B-roll, a week calendar with the official
  platform marks and honest labels).

## Workflow
The owner prefers one-shot work: show the brief, then carry on to the finished video without waiting, unless
they ask for gates. ALWAYS stop to ask before spending money (ElevenLabs credits, paid stock) or doing anything
public (posting, pushing). Report honestly at the end: substitutions, what was measured, what nobody has heard.

0. **Intake.** From the request, settle: goal, audience, platform(s), format(s) (short 9:16 / 16:9 / long),
   length, concept or "pitch me", script or "write it", must-avoids. Check `needs.md` and ask for missing items
   in ONE message, then proceed with fallbacks. Make the project: `python3 scripts/new_ad.py "<title>"`
   (→ `~/Desktop/clipzing-ads/<slug>/`); add `--long` for a chaptered long-form film (`templates/film_long.py`:
   chapters as data, real screens, Zing presenting, a chapter rail; render at 30 fps).
1. **Facts.** Re-read the sources listed in product-facts.md (features.ts, PLAN_PRICING/PLAN_FEATURES,
   templates.json). Note any change.
2. **Concept + brief.** Pitch three directions from concepts.md (or new ones), judge them (hook on mute, brand
   inside 2 s, truth, craft budget), and pick one. Write `brief/PROMPT.md` (template: `templates/brief.md`) with
   the script, a beat sheet with timings, the hand-off contracts between scenes, music, SFX, assets and needs. Run
   `qa.claims_lint` on it.
3. **Voice first.** `voice.tts(script, 'voice', voices=[...], takes=2, direction=...)`: audition 2–3 voices ×
   2 takes. Pick the word-perfect, most natural take (Whisper it), copy it to `voice/vo.wav`, then run
   `voice.timings(...)` → `voice/words.json`. Re-time the brief to the real words.
4. **Assets.** Zing poses (`library/zing`; render missing ones with `toolkit/capture`), product screens
   (`library/screens` or rebuilt with `adkit.ui`), phone footage (`library/footage`: Zing's podcast), real caption
   frames for the script (`capture/shoot.mjs captions job.json`). No celebrities, no third-party marks, no stock
   people implying endorsement.
5. **Build** `film.py` from `templates/film_short.py` (or `film_long.py`; study `reference/examples/the-link/film.py`): the timeline `T` from the words, stations as planes, one
   continuous camera, THE device drawn by one function, cached UI layers, Zing from his rig, type with the
   voice, marks in `overlay()` after the grade, `cues()` for every visible move, `hero_cues()`, `MUSIC`.
6. **Preview v1.** `render.py film.py stills …` at every beat (both formats), then `render.py film.py preview`.
   LOOK at the contact sheets yourself.
7. **Art-direction pass.** Ask "is it exciting?" Then go bigger (UI, type), darker (stage, no flat bands),
   brighter (heroes), and keep the camera always moving. One wow per scene, each resolving into a crisp hold ≥ 0.4 s.
   Fix and re-still.
8. **Sound.** `python3 mix.py`: music from `MUSIC`, cues, hero cues, the voice, master, and the QA report (LUFS,
   true peak, word margins full-range and on a phone speaker, Whisper intelligibility). Fix until it passes.
9. **Finals.** First `render.py film.py check --fmt <fmt>` (a pre-flight sweep of every 5th frame at tiny scale: an
   exception at one moment would otherwise kill workers an hour into the render). Then one format at a time:
   `render.py film.py repair out/frames_<fmt>` (renders whatever is missing; resumable) → check the frame count →
   `qa.motion_audit` (no missing frames, no near-black runs, no hard cuts unless intended, no one-frame pops) and
   `qa.strip` on the fastest frames and every seam → `render.py encode …` → delete the frames (≈ 4.5 MB each).
   See `reference/examples/got-you/finals.sh`. Check `qa.safe_zones` on the 9:16 stills.
10. **Deliver** to `~/Desktop/clipzing-ads/<slug>/`: masters (CRF 15), the upload copy (`--upload`), a cover frame,
    `NOTES.md` (what was made, substitutions, measurements, honest limits), `POSTING.md` (caption, hashtags, first
    comment, UTM link), the brief and the source. Then ask for the post's numbers later (needs.md) and log them in
    lessons.md.

## Non-negotiables
**Truth.** Only claims in product-facts.md. Platforms: YouTube Shorts are published; TikTok gets DRAFTS; Reels is
export-only; nothing else. No "free trial", no guarantee, no view predictions. Illustrative numbers are story,
never promises.
**People.** Fictional names only. Never the landing showcase clips (they show celebrities). Zing's podcast or footage
the owner has rights to.
**Brand.** Clipzing's own marks, fonts, colours and Zing from his rig. Never another brand's characters, sounds,
fonts or trademarks. Reference films lend techniques, not assets. Marks are pixel-exact at rest, after the grade.
**Craft.** Hook within 0.3 s on mute; brand within 2 s; one continuous camera; nothing static more than about 20 frames;
text with or a hair before the voice; never karaoke captions, strobe, flares to white, RGB split, ring pulses,
tumbles, dolly zoom, one-frame pops, re-centring text, or near-black for more than 0.3 s.
**Sound.** Music ≥ 12 dB under every word (aim 15), hero cues after words, impacts a frame early, master −14 LUFS
/ ≤ −1.25 dBTP, Whisper reads the mix like the dry voice.
**Owner's taste.** Dark theme. Premium, never generic: deeper purple, lit edges, crisp hairlines; no bright gradient
+ glow + colour-swap. Zing's face matches the line (no cute faces over serious narration).

## Toolkit (toolkit/adkit, Python; run with `~/shorten/shortn-be/.venv/bin/python`)
```python
from adkit.core import *            # W H PORTRAIT SCALE FPS D · Camera Plane(.home .framing .world .worlds) · pose_mix catmull
                                    # prog lerp eout ein einout eback spring pulse smooth_noise · shake_at · new_frame stage grade
                                    # composite_plane composite_sprite composite_screen after_grade · draw_line (THE line) · proj1
from adkit import brand, ui, fx, audio, voice, qa
brand.C / brand.font(size, weight, family) / brand.wordmark() / brand.wordmark_text() / brand.icon() / brand.zing(pose, t) / brand.zing_box(pose)
brand.footage(scene, t, w, h) / brand.screen(name) / brand.PLATFORM
ui.Layer(w, h) → .rrect .shadow .gradient_rrect .type(xy, text, size, weight, fill, anchor, tracking) .paste .rgba()
ui.surface ui.button ui.pill ui.progress ui.ring ui.score_badge ui.odometer ui.waveform ui.avatar ui.glyph
ui.phone(w, h, screen) ui.browser(w, h, screen, url) ui.cursor() · @ui.cached() for layer builders
fx.strands fx.shards fx.swarm(+ sample_mask) fx.sweep_layer fx.anamorphic fx.dust fx.type_rgba fx.word_slam fx.rise_mask
timeline.Words(path, offset).t/.end/.after/.phrases · timeline.Cues().add(t, kind, x, size) · timeline.Grid(bpm, t0)
audio.score(end, style, drop, lift, breath, stop, hit, sting) · audio.SFX · audio.HERO{clip_ready, published, logo_sting, logo_hit, logo_chord}
audio.build_mix(...) · audio.master(...) · audio.report(...) · audio.Library (owner's SFX folder via SFX_LIBRARY)
voice.tts(...) · voice.timings(...) · voice.estimate_cost(...)
qa.motion_audit qa.strip qa.safe_zones qa.claims_lint
```
A film module defines `END`, `scene(t) -> (frame, deferred)`, optional `camera_at(t)`, `probe(t)`, `overlay(frame, t)`,
`cues()`, `hero_cues()`, `MUSIC`, `SILENCE`, `GRADE`. Motion blur is adaptive (a probe of camera and points). Lines
and crisp type go in `deferred` (drawn once from the centre sample, so no ghosting).

`toolkit/render.py FILM.py stills|preview|all|frames …` · `render.py encode FRAMES OUT.mp4 --audio … [--upload]`

`toolkit/selftest.py` checks the install in about a minute (tools, library, both templates in both formats, all sounds, lint).
Run it first on a new machine or after changing the toolkit.

## Capture (toolkit/capture, Node + the shortn-fe repo; `node build.mjs` once)
- `node shoot.mjs zing <pose|all> RAW` → `python3 ../library.py zing RAW`: Zing poses from his rig (new poses =
  data in `src/zing.tsx`).
- `node shoot.mjs footage <scene|all> RAW` → `library.py footage RAW`: Zing's podcast and the landing scenes.
- `node shoot.mjs brand all RAW` → `library.py brand RAW`: the wordmark, the white wordmark, the icon.
- `node shoot.mjs captions job.json RAW`: the REAL caption engine on your script's words (any of the 38
  templates), transparent frames to composite inside a phone.
- `screens/`: real dashboard screens with fictional data (see `toolkit/capture/screens/README.md`).

## Delivery checklist
- [ ] claims_lint clean; platforms right; no free trial or guarantee; prices verified on the day if shown
- [ ] hook within 0.3 s, brand within 2 s, every super with the voice, the 9:16 safe zones clear
- [ ] motion audit clean; fastest frames and seams looked at; both formats re-laid out (not cropped)
- [ ] audio QA passes (−14 LUFS, ≤ −1.25 dBTP, margins ≥ 12 dB, Whisper = dry)
- [ ] NOTES.md says what is synthetic (voice/SFX) and what nobody has heard by ear; POSTING.md written
- [ ] lessons.md updated after results come in
