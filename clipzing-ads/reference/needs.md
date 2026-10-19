# What a flawless video needs, and what to ask the owner for

Check this list at the start of every ad. For each missing item, use the fallback and **say so in the delivery
notes**. Ask for the items marked ASK in one message at intake (not one at a time), with the reason.

| Need | Status (2026-10-19) | Why it matters | Fallback |
|---|---|---|---|
| **Premium voice: ElevenLabs API key + a chosen voice ID** (`ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`) | **ASK**, missing | The biggest single quality jump. TTS from OpenAI is good but recognisably synthetic | OpenAI `gpt-4o-mini-tts` (key in `shortn-be/.env`), 3 voices × 2 takes auditioned |
| **A human voice** (a voice actor, or the owner's own read; the owner can't appear on camera, but a voice is fine) | **ASK** | Human reads hold attention better; founder voice builds trust | TTS |
| **An SFX library** (folder path → `SFX_LIBRARY`) | **ASK**, missing | Recorded whooshes, hits and UI clicks sound richer than synthesis | `adkit.audio.SFX` (≈ 30 synthesized kinds), measured and mixed |
| Real app screens | have: 22 screens (11 desktop @2×, 11 mobile @3×) of the real UI with fictional data in `library/screens`, re-shootable with `capture/screens` | The product itself is the proof | `adkit.ui` rebuilt UI |
| **A demo Clipzing account with realistic content** (a podcast the owner has rights to, processed into clips) | **ASK** (optional upgrade) | Real results from a real show beat a fictional one | The fictional "The Long Table" screens above |
| **Clerk dev keys** in `shortn-fe/.env.local` (to sign in to a local build for screen captures) | have | `capture/screens` signs a test user in with a testing token | Rebuilt UI |
| **Footage with rights** (the owner's own podcast/video, or consenting creators with a signed OK) | **ASK** | Real people on the phones read as real results | Zing's own podcast scenes (`library/footage`). Never celebrities, never stock people implying endorsement |
| **Brand decisions**: tagline(s), CTA wording, show prices or not, a promo code | **ASK** once per campaign | Consistency across ads | No price; CTA = "clipzing.com"; tagline from the concept |
| **Real numbers** (users, clips made, hours saved) with a source | **ASK** if the script wants one | Claims must be provable | No numbers; illustrative UI numbers only, as story |
| **Results of the last post**: TikTok Studio retention curve, 3-second hold, average watch, completion, traffic source, follows, profile visits, link clicks; PostHog sign-ups with a referrer | **ASK** after every post | The only way to learn what works (lessons.md) | Views and likes alone (weak signal) |
| **Music** | have (made in code) | TikTok business accounts may only use the Commercial Music Library; original music avoids muting | — |
| Platform icons | have (code-drawn, simplified) | Show only platforms Clipzing really supports | — |
| Fonts | have (Plus Jakarta Sans and co., OFL, bundled) | — | — |
| DaVinci Resolve (optional) | ask only if the owner wants an editable project | Hand-off to an editor | Stems + cues.json + frames |
| Render time | 8-core Mac: about 15 min per format for 20 s at 60 fps | Plan long-form at 30 fps or overnight | Preview at half size first |
| GPU | not needed | — | — |

## How to ask (template)
> To make this one as good as it can be, I'm missing a few things. Everything has a fallback, so I'll start now
> and use whatever you send:
> 1. ElevenLabs API key + a voice ID you like (≈ N credits for this script). Otherwise I'll use OpenAI voices.
> 2. A path to your SFX library, if you have one. Otherwise I'll synthesize the sounds.
> 3. A demo account / podcast with rights for real screens. Otherwise I'll use captured screens with fictional data.
> 4. Your last post's TikTok Studio numbers (3-second hold, average watch, traffic source).

Never ask for passwords. Keys go in the environment or `.env`, never in chat logs, briefs or the repo.
