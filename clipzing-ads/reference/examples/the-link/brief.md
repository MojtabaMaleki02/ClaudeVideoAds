# The Link: brief

## The ask
- Goal: show, in one look, what Clipzing does for a podcaster. Made with the clipzing-ads skill as its first real run.
- Audience: podcasters and YouTubers on TikTok / YouTube Shorts.
- Format: 9:16 1080×1920 60 fps, ≈ 15.5 s + 2 s end card; a 16:9 re-layout.

## Concept: "Word Slam → The Link" (concepts.md #2)
Words slam on the frame they're spoken. Then ONE link travels through the product: pasted → the episode's
waveform is scanned → moments lift out and sort by score → the camera dives into the best moment → a 9:16 window
finds the speaker → the product's REAL captions time every word → the real "Generated Clips" screen → the light
gathers into Zing.
The visual pun is the hook: on "your podcast gets SHORTER." a 16:9 podcast frame literally squeezes into a 9:16
clip around the speaker, which is the product's core move (auto reframe) shown in the first 2.5 s.

Directions considered:
1. The Link (this): the clearest "what it does"; new moves vs The Path (word slams, a squeeze, typing, sorting, a swarm). **Chosen.**
2. Found (raid structure): emotional, but promises an audience. Risky as a claim; better as a follow-up.
3. Two Hours In (before/after): strong for podcasters, but it spends 5 s on the "before" pain. Next test.

## Script (one flowing read; claims_lint clean)
"Today, your podcast gets shorter. Paste one link. It finds the moments worth posting, frames the speaker, and
times every word. Ranked. Captioned. Ready. Clipzing."
Facts: detection + 0–100 score ranking (features.ts: viral-clip-detection), auto reframe (auto-reframe),
word-level animated captions (animated-captions). No platform, price or count claims.

## Voice
OpenAI gpt-4o-mini-tts (no ElevenLabs key; see needs.md). 3 voices × 2 takes (coral, nova, sage). coral_1 is the
only word-perfect take on Whisper and has the widest pitch range (147–272 Hz). VO offset −0.28 s, so "Today" lands at 0.21 s.

## Beat sheet (locked to the take; seconds)
| | s | Picture | Sound |
|---|---|---|---|
| S1 | 0.00–3.30 | Word slams: TODAY, (0.21) · YOUR PODCAST (1.12) with a wide podcast frame slamming in · GETS (1.76) · SHORTER. (2.09, biggest): the 16:9 frame squeezes into a 9:16 window that glides to Zing. Small wordmark at the top from 0.35 s | suck + impact per slam, a sub boom on SHORTER |
| S2 | 3.20–5.00 | Whip down to the "Generate clips" panel; the link types letter by letter from "Paste" (3.47); the button is pressed after "link." | whoosh, key ticks, click + thump; the groove DROPS on "Paste" |
| S3 | 5.00–7.30 | The line runs into the episode's waveform; a scan light sweeps; on "moments" four moments lift out as cards; on "posting" their score rings fill; the cards sort best-first | zip, pops per card, ticks per ring, a whoosh per sort |
| S4 | 7.20–8.50 | The camera dives into the best card: the 16:9 moment fills the frame; on "speaker" a 9:16 window glides to Zing, the rest dims | whoosh-down, a soft lock |
| S5 | 8.50–10.40 | The window becomes a phone; the REAL caption engine (Pepper, Clipzing purple) times "and times every word." | taps |
| S6 | 10.40–12.95 | Whip to the real "Generated Clips (9)" screen; slams: Ranked. / Captioned. / Ready.; a light sweep; a ✓ on Ready | impacts, `clip_ready` after "Ready." |
| S7 | 12.95–15.4 | Breath: the screen falls away into light; the swarm gathers into Zing, who lands ON "Clipzing" (13.32); the wordmark text below | reversed swell, `logo_sting`, `published` |
| End | 15.4–17.5 | clipzing.com | the last chord rings |

## Look
Stage #05060E with drifting purple glows; Plus Jakarta Sans ExtraBold slams; one accent #975AFD; DOF, adaptive
motion blur, grain; the wordmark after the grade.

## Music / SFX
`keynote` 112.5 BPM, F# minor: tense pads + sub under the slams, the groove drops on "Paste", a lift from
"Ranked", a breath at 12.95, the hit on "Clipzing". Every visible move has a cue (film.cues()).

## Assets
Zing poses (library), wide + closeup footage (library), the real job screen (library/screens, mobile + desktop),
real captions (capture/src/captions.tsx, template "pepper").

## Needs (fallbacks used)
ElevenLabs key (→ OpenAI TTS); SFX library (→ synthesized); demo account (→ screens with fictional data).
