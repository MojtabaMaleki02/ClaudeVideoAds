# Craft: how a Clipzing ad is made to look and sound expensive

This unifies five code-built spec ads (a language-app "The Path", a streaming-app "See What's Next", an AI-model
"Thinking Gets Faster", a fintech "Just Ask" and a live-streaming "RAID"), their author's standing rules, and what
our own posts taught us. Their **techniques** are reused here; their brands, characters and sounds are not. Each
example below is translated into Clipzing terms.

## 1. The idea: one device, many jobs
The strongest films have ONE visual device that carries the whole story and gets a new job in every scene:
- *One line of light* (purple) reveals the wordmark, strings the chapter nodes of an episode, fills the progress bar,
  becomes the voice wave, splits into the platforms, and underlines the tagline. (Clipzing's "The Path".)
- *A swarm of light* is the audience. It erupts, scatters, finds one small creator, and lands as Zing. (RAID's swarm.)
- *One prompt's journey*: a link goes in, moments come out, captions land, the calendar fills. (Gemini's
  prompt journey, with a YouTube link instead of a prompt.)
- *A brand world, then "and now…"*: the product you know, then the new feature arriving inside it, three quick
  real examples, a drop on the logo. (The fintech launch structure, for launching copilot, agents or autopilot.)
Pick one device per film. Write it in one sentence in the brief: "One ___, many jobs."

## 2. The hook (the first second decides everything)
- **Readable and in motion within 0.3 s, on mute.** Frame 1 already says something.
- **One big slam on the first beat**, not a montage: Zing rushes from depth and slams at ~0.17 s at about half the
  frame (twice his logo size), with squash, stretch and a decaying shake. Or a WORD SLAM: each word rushes out of
  depth and lands full-width on the frame the voice says it ("ONE / VIDEO. / THIRTY / SHORTS.").
- **The brand inside the first 2 s.** Our post #3 showed the brand at 19 s and nobody saw it. The wordmark
  reveal under the slam fixes that.
- After the slam, the camera settles onto a lock-up and the line reveals "Clipzing" (pixel-exact).

## 3. The camera
- **One continuous camera. No hard cuts.** Every scene hands over through a camera move, a rack focus, a shape
  morph or a match-cut. Our renderer is built for this: stations are flat faces in a 3D world, each with a home
  pose that maps 1:1 onto the screen (`Plane.home`), and the camera flies between them.
- **Never static.** About one major move per second; nothing frozen for more than ~20 frames. Holds still breathe
  (a slow push of 2–4 %, drifting glow).
- **One "wow" per scene, resolving into a crisp frame held ≥ 0.4 s** so it can be read.
- Smooth eased motion and C1 camera paths (`catmull`, `einout`); whips are fast in the middle and eased at the ends.
- Roll ≤ 8° on whips. A shake only on hits (`shake_at`), decaying in ~0.3 s.
- **A stage beats a journey.** RAID's first draft flew six seconds through a city; a keynote stage where things pop
  on the beat read faster. Don't fly far when popping things in place says it in one look.

## 4. Transitions are match-cuts
- A white-out irises into the first card; three viewer lights become the "3" of a counter; the type dissolves into
  the particles that form the logo; the logo collapses into the end-card line.
- **Seams are contracts.** When one scene hands its light to the next, both sides draw the same thing on the same
  frame: the same point, size and colour. Write the hand-off frames into the brief.

## 5. Type
- Plus Jakarta Sans (the product's font): ExtraBold for slams and supers, Bold for UI, tracking −0.02 em on display.
- **Every word on screen arrives with, or a hair before, the spoken word.** Never after it.
- Keynote supers (clean, short, at the top or centre) or masked rises. **Never karaoke captions** in a motion
  film. Real Clipzing captions appear only as the PRODUCT (inside a phone, showing what Clipzing makes).
- Text holds long enough to read: about 0.3 s per word plus 0.5 s, never less than 0.6 s.
- No text that slides to re-centre itself (lay out the final line first, then reveal it).
- A stack of slams: each one leaves BEFORE the next starts its rush (≈ 0.4 s before the next word), or the words pile up.
- Over busy footage (a wall of clips), put a soft dark scrim behind type and behind the top lock-up.
- Platform marks: the official shapes (simple-icons, CC0, as on Clipzing's site) as app tiles in each brand's colours,
  ALWAYS with what Clipzing truly does there ("Shorts · published", "TikTok · to drafts", "Reels · export").
- Phone readability at 9:16 (1080 × 1920): supers ≥ 72 px, UI labels ≥ 34 px, nothing under 26 px.

## 6. Product UI
- Rebuilt in code in Clipzing's UI language (`adkit.ui`), or real captured screens (`library/screens`) on a plane.
  Use fictional data: creator names, clip titles, numbers.
- **Bigger than you think.** The streaming-app film's first version was "clean but not exciting". The fix was a
  bigger phone and UI, larger type, a darker stage with no flat colour bands, brighter heroes and a camera that
  always moves.
- A UI action = a cursor or a finger tap, a press-scale into its lip, a click sound, the result. Real flows only
  (the real way a feature opens).
- **One number, one function.** A count shown in three places (counter, card, pill) reads the same value every frame.
  Digits roll in fixed cells (`ui.odometer`) and never jitter or re-centre.

## 7. Character (Zing)
- Zing is animated only by his own parts, from his own rig (`library/zing/<pose>`). Never redrawn, recoloured or
  distorted, except squash and stretch on impacts.
- A character needs a surface: a contact shadow at the real contact point, or he "floats" (owner's note on ad #2).
- Match his face to the line. **No cute reactions over serious narration**: use `determined` or `focused` there.
  `cheer` and `joy` are for payoffs.
- He lands ON the hit (the music's low hit and his squash on the same frame).

## 8. Light, depth, finish
- Near-black stage (`brand.STAGE_BASE`) with one or two soft drifting purple glows, **never neon**, and no flat
  colour bands.
- Depth of field by distance (`focus=`), real motion blur (adaptive sub-frames; no stepped copies), light grain,
  gentle bloom. Heroes brighter than everything else.
- **Logos after the grade**: compose the wordmark in `overlay()` so no grain, bloom or vignette touches it. It must be
  pixel-exact at rest. Only move, scale, fade, blur or mask it, with no glow over it.
- One anamorphic streak per film at most.
- **Never**: strobe montages, flares to white, RGB-split glitch, ring pulses, tumbling objects, dolly zoom,
  karaoke captions, one-frame pops, text sliding to re-centre, stepped motion-blur copies, near-black for more than
  0.3 s (reads as "the video ended").

## 9. Voice
- **Voice first, picture second.** Record, pick, time the words, then lock the picture to them.
- **One flowing read** that fills the film, cut only at its own pauses. Short lines spread across the picture
  sound robotic.
- A voice that fits: Clipzing is a creator's tool, so use a bright, warm, young creator voice that is premium and
  never salesy. Audition 2–3 voices on the same script.
- Natural speed, never sped up. Numbers as words ("two hours"). Respell for TTS only ("Clip-zing").
- Full, clear sentences: every word must be understood on a phone speaker.

## 10. Music and sound
- **Original music made in code**, arranged around the voice. It starts on the hook, drops on a key word, lifts on a
  reveal, takes a breath (or a TRUE dead stop) before the hero hit, and the last chord rings under the end card.
- **Dense, satisfying sound design, tied to the picture**: a whoosh into every move, a hit on every landing, a
  click on every UI action, a tick on every typed letter or counter step, glass on gems and stars. Export the
  picture's events (`Cues`) and build every sound from that list, panned by x and gained by size.
- Clipzing's **sonic logo**: `clip_ready` (a clip is done, a goal is hit) and `published` (the button at the end),
  plus `logo_sting` on the hero landing. The music dips under them.
- Hero cues sit just after a word, never on it. A chime on "top" turned it into "talk".
- **The brand name is the clearest word in the ad.** When the logo lands ON "Clipzing", split the sting:
  `logo_hit` (sub only) on the word, `logo_chord` just after it. A full chord on the name turned "Clip-sing" into
  "Clip-sync" for Whisper (The Link, 2026-10-19).
- Impacts land a frame early, mostly low end, with their tails ducked under the words.
- **Measure what you can't hear** (`audio.report`): master −14 LUFS / ≤ −1.25 dBTP, music ≥ 12 dB (aim 15) under
  every word on full range AND on a phone-speaker simulation, every hit on its frame, and Whisper reading the
  final mix exactly like the dry voice.

## 11. Process discipline
- Brief with frame-exact timings → voice → assets → engine/scenes → **PREVIEW v1** (stills + contact sheet + a
  half-size preview MP4) → **art-direction critique** (is it exciting? bigger, darker, brighter heroes, always
  moving?) → **frame-by-frame motion audit** (`qa.motion_audit`, then look at the fastest frames and every seam with
  `qa.strip`) → one fix round → the other aspect ratio as a REAL re-layout (not a crop) → finals.
- Build scene packages in parallel only when the seams are written as contracts.
- New animations each time: don't recycle the previous ad's moves. Keep the device and invent the moves.

## 12. Short-form truths from our own posts (see lessons.md)
- Entertainment first. The product is the punchline, never an announcer's hard sell.
- A frame-1 hook readable on mute. One idea per video.
- The brand inside 3 s. Ask for the 3-second hold, the average watch time and the traffic source, not just views.
- No celebrities, no third-party footage, no stock people implying endorsement.
- When asked for a "trend" edit (someone else's audio): captions at the bottom, normal size, word by word, in the
  real Clipzing caption styles the owner names; dark theme; cuts on word onsets (±1 frame); only spoken words as text.
