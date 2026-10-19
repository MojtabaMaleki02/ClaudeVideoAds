# Example: "The Path" (2026-10-19), the first code-built Clipzing film

The owner loved it ("I love everything about it") and posted it. Source: `~/Desktop/clipzing-the-path/source/`
(written before adkit existed: `engine.py` is adkit.core's ancestor, `film.py` the stations, `audio.py` the score).

**Device:** one purple line of light, many jobs (concepts.md #1). **Length:** 19.2 s + 2 s end card, 60 fps, 16:9 + 9:16.
**Voice:** OpenAI "coral", one flowing read. **Music:** `mallet_pop` 100 BPM D major.

| s | Station |
|---|---|
| 0.17 | Zing SLAMS at half the frame (slam pose, squash, shake, shards); the line reveals the wordmark |
| 1.7–2.9 | The line dives along an S-curve of chunky chapter nodes; presses GET CLIPS; a phone rises out of the node |
| 2.9–4.8 | Caption tiles snap in on "One clip at a time"; READY ✓, a score of 94, `clip_ready` |
| 4.8–7.2 | The line curls into a streak flame (the one anamorphic streak); the counter 1 → 365 in fixed cells |
| 7.2–9.3 | Drop: "Your top clips this week"; your row climbs #7 → #1 |
| 9.3–11.4 | A floating phone plays Zing's podcast; the line becomes the voice wave; comments and followers |
| 11.4–14.7 | The line splits into platform branches, each lit on its word |
| 14.7–16.5 | "One episode, / every platform." on the line as the baseline |
| 16.5–21.2 | A breath; Zing lands ON the hit; the wordmark; `published`; the end card |

## What it taught
- **A truth bug shipped:** the VO said "TikTok, Shorts, Reels… even LinkedIn". Clipzing cannot post to LinkedIn, and
  Reels is export-only. That's why product-facts.md and `qa.claims_lint` exist. Corrected line:
  "Shorts, TikTok, Reels… all from one upload. One episode, all your shorts."
- The landing showcase clips (celebrities) were used on the phones at first and were swapped for Zing's podcast in QA.
- A hero chime ON a spoken word masked it ("top" → "talk"): hero cues go after words.
- Ducking must come after reverb, or the tails fill the dip.
- Lines drawn inside every motion-blur sub-sample ghost; draw them once from the centre sample (`deferred`).
