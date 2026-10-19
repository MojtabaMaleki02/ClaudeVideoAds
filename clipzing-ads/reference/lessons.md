# What our posts taught us (append after every post)

| # | Date | What | Result | Lesson |
|---|---|---|---|---|
| 1 | 2026-10-15 | Mascot hype ad: Zing flies in, hype announcer VO, 13 s | 800 views, 1.9 s average watch, 1.45 % completion, 0 likes | People swiped during the cartoon fly-in, before any proposition. Frame-1 hook readable on mute; entertain, don't sell; no hype announcer; one idea |
| 2 | 2026-10-15 | Skit (cat, night, editing pain), 11 s loop, TikTok-native text | ~200 views | The owner wanted more detail (camera angles, emotions, props) and called default text boxes "cheap". Never use TikTok-default text boxes; build typography |
| 3 | 2026-10-18 | Trend audio ("I can't stop") over grinding footage, the landing clips as the result, 24 s | 252 views, 2.83 s average watch, 1.5 % completion, 12 likes, 0 follows | The brand appeared only at 19 s, so nobody saw Clipzing. Front-load the brand into the first 3 s. Landing showcase clips are celebrities (never again). Pexels people can't imply endorsement |
| 4 | 2026-10-18 | "Nobody is coming to save you" trend narration montage + real captions | "did not do well, not at all" | Someone else's speech/trend audio risks muting on business accounts; montage of stock reads generic |
| 5 | 2026-10-19 | "The Path": code-built motion film, Zing, one line of light, TTS voice, code music, 21 s | The owner loved it ("I love everything about it") and posted it; results pending | The premium motion-design route (this skill). Mistake caught after delivery: "even LinkedIn" (not supported) |
| 6 | 2026-10-19 | "The Link": first film made WITH this skill (word slams, a squeeze-to-9:16 hook, the link's journey, real captions, a real app screen, a swarm into Zing), 15.5 s + end card | delivered, results pending | QA earned its keep: the safe-zone check moved the top lock-up, "SHORTER." and the supers out of TikTok's UI; Whisper caught the logo chord masking "Clipzing" (now `logo_hit` + `logo_chord`); the real captions were wider than the phone at first; the disk filled mid-render (render.py now checks space and has `repair`) |
| 7 | 2026-10-19 | "Got You": a 38 s story promo (stuck at 200 → Zing "I got you" → link to highlights, 3 real caption styles, reframing for podcast/stream/gameplay, B-roll, a week on the calendar with the official platform marks) | delivered, results pending | The first finals OOM-killed render workers (layer caches × 8 workers on a 17 GB Mac swapped the disk full) and the chain encoded a broken film; caches are now small, workers are RAM-capped, and finals stop on a frame-count mismatch. Hook slams must exit before the next one starts its rush |
| 8 | 2026-10-19 | Owner's review of "Got You": start at "Stuck at 200", faster voice; the timeline, captions, B-roll and calendar beats "horrible"; "the Duolingo-like one was better… shock me" | remade as Got You v2 | Rebuilt in the physical language (craft.md §1b): extruded objects, one line of light, show the result, fill the frame, feed pace (voice.tighten 3.2 w/s) |
| 9 | 2026-10-19 | Owner on the v2 draft: "all good, but the captions are so bad… oversized" | fixed | Captions at real size inside the clips; multiple styles via side-by-side cards / a flipping card |

## Standing rules from these
- The hook is a slam, readable on mute, within 0.3 s; the brand inside 2 s.
- Premium motion design beats trend edits and stock montages for this brand.
- Truth check every claim (platforms!) before rendering finals.
- After posting, always ask for the 3-second hold, average watch, completion and traffic source, and log them here.
- Change one variable per test (hook, length, voice, concept) so results teach something.
