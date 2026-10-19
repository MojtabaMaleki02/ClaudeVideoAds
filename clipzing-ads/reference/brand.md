# Clipzing brand for motion

Everything here comes from the product itself: the CSS tokens, the font loaded in `app/layout.tsx`, the navbar
lock-up, Zing's rig, the caption engine. `adkit.brand` holds it as data. If the product changes, update `brand.py`.

## Colour
| Role | Token | Hex | Use |
|---|---|---|---|
| Film stage | `STAGE_BASE` | #05060E | every background; a touch darker than the app so UI planes lift off it |
| App background | `bg` | #060813 | inside phone/browser screens |
| Elevated surface | `bg_elevated` | #0D111D | cards, panels |
| Overlay surface | `bg_overlay` | #161A26 | inputs, pills, cells |
| Text | `fg` / `fg_muted` / `fg_subtle` | #FAFAFA / #A4A4A4 / #717171 | |
| **Accent (the line, buttons)** | `accent` | #975AFD | THE colour. One accent per film. |
| Wordmark gradient | `purple` → `purple_deep` | #A855F7 → #9333EA | the lock-up only |
| Highlights / lips | `lilac` / `lip` | #C4B5FD / #5B21B6 | button tops / the darker lip under chunky buttons |
| Zing body | `zing_body` / `zing_hem` | #8B52CB / #6D3BC8 | matching glows to the character |
| Status | `success` / `warning` / `danger` / `info` | #00C57C / #ECAA0B / #F94144 / #19AFFE | score bands (≥ 80 / 60–79 / < 60), "Published", errors |
| Streak | `flame` / `flame_hi` | #FF9600 / #FFC800 | streaks and gamification only |
| Platforms | `PLATFORM[...]` | YouTube #FF0033, TikTok #FE2C55 + #25F4EE, Reels #E1306C → #F77737 | only on their own glyphs and states |

Rules: dark theme always. Glows are dim (0.06–0.14 strength) and drift. No bright gradient + glow + colour-swap
combos (the owner calls that "generic"). Use deeper purple, lit edges and crisp hairlines.

## Type
- **Plus Jakarta Sans** (`font(size, weight)`; weights regular … extrabold) for every Clipzing string. The UI
  uses 400–700. ExtraBold (800) is for display slams only.
- Inter (`family='inter'`) for dense numbers; JetBrains Mono (`'mono'`) for API/agent moments; Instrument Serif
  (`'serif'`) for a rare editorial accent. Anton / Bebas / Montserrat exist because caption presets use them, and
  they appear only inside captions.
- Display tracking −0.02 em. Sentence case. Supers end with a full stop when they are a statement ("Every word,
  timed.").
- All bundled fonts are OFL (`assets/fonts`). SF Pro is not used: it isn't ours, and it can't be shared.

## Marks
- `wordmark()`: Zing's icon plus "Clipzing" in Plus Jakarta Sans 700 with the #A855F7 → #9333EA gradient, exactly as
  the navbar draws it (captured from `logo-sidebar.svg`). `wordmark_white()` is for busy or coloured backgrounds.
  `icon()` is the face alone.
- Only move, scale, fade, blur or mask a mark. Never recolour, rotate, stretch or outline it, or put a glow on it at rest.
- Compose marks **after the grade** (`overlay()` / `core.after_grade`) so they stay pixel-exact.
- Keep clear space equal to the icon's height around the lock-up. The end card is the wordmark plus
  "clipzing.com" in `lilac`.

## Zing
Zing is Clipzing's character: a purple ghost with a flowing hem, big eyes and floating arms, built as a layered
SVG rig in `shortn-fe/components/mascot`. Ads use him from his **own rig**, rendered by `capture/shoot.mjs zing`
into `library/zing/<pose>/` (30 fps loops on the rig's 4.2 s beat, transparent).

| Pose | When |
|---|---|
| `idle`, `talk`, `nod`, `look_*` | presenting, listening |
| `present_right` / `present_left` | introducing a UI element beside him |
| `slam` (1 frame), `land`, `hop`, `cheer`, `celebrate`, `joy` | the hook slam, the hero landing, payoffs |
| `determined`, `determined_talk`, `focused`, `typing`, `scan`, `think` | work, serious lines, the product doing its job |
| `tense`, `sleepy`, `sad`, `ashamed`, `rage`, `poker` | the "before" (the pain without Clipzing), used sparingly |
| `podcast`, `podcast_listen`, `gamer`, `boss` | with the product's own props (headset, studio mic, controller, shades) |
| `blink1`, `blink2` | hand-placed blinks (`blink1` → `blink2` → `blink1` over 8 frames) |

Rules:
- Never redraw, recolour, mirror his face, or add parts. New expressions are new pose DATA in
  `capture/src/zing.tsx` (brows, lids, pupils, mouth, arm reach, act), rendered from the rig.
- Squash and stretch on impact only (sx, sy in `composite_sprite`).
- Give him a contact shadow or a surface. He must not float in a void unless he is flying.
- Size: hook slam ≈ half the frame height; presenter ≈ 30–40 % of the frame height; corner cameo ≈ 15 %.
- He's a ghost and a mascot, not a person: never put him in a celebrity's role or likeness.

## Sonic identity
- `clip_ready`: two bright bell notes, up a fifth, with a sparkle. Plays when a clip is ready or a goal is hit.
- `published`: a bright rising arpeggio landing on a full D-major chord. The sonic button at the end.
- `logo_sting`: a full chord + low hit when Zing or the logo lands, ringing under the end card. When the landing
  happens ON the spoken brand name, use `logo_hit` (sub only) on the word and `logo_chord` right after it.
- The house key is D major (D minor for serious films), so the stings sit inside the score.

## Product UI language (for rebuilt screens)
Solid surfaces (`bg_elevated` / `bg_overlay`), 1 px hairlines (white at 8 %), a faint lit top edge, deep soft
shadows, 26–28 px radii on cards and full pills on chips. Primary buttons are purple with a darker lip (chunky).
Score rings are coloured by band. The dashboard's real labels are "Generate clips", "My Clips", "Videos", "Calendar",
"Autopilot", "Accounts", "Brand Kit", "Preferences", "Achievements" and "Shorts this month". Use them verbatim when
you rebuild a screen.

## Voice of the copy
Plain, specific, creator-to-creator. Short sentences. Verbs over adjectives ("finds", "frames", "sends"). The product
is the punchline, never shouted. No hype words ("revolutionary", "insane"), no fake urgency, no claims we can't
prove (see product-facts.md).
