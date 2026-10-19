# Clipzing: what an ad may say

Every spoken word and every string on screen must be true today. These facts were read from the code on
2026-10-19. **Re-verify before every ad.** Files and plans change, so read them again:

| Fact | Source of truth |
|---|---|
| What each feature does, plan availability, what it does NOT do | `shortn-fe/lib/seo/features.ts` |
| Prices | `shortn-be/clipzing/settings/base.py` → `PLAN_PRICING` (`price_monthly`, `price_yearly`) |
| Quotas (shorts, minutes, accounts, channels, retention) | same file → `PLAN_FEATURES` (note: the Creator plan's key is `pro`) |
| Caption templates that exist | `shortn-fe/public/caption-engine/templates.json` (38 on 2026-10-19) |
| Support email, guarantee wording | `shortn-fe/lib/constants.ts` (`SUPPORT_EMAIL`), memory: no guarantee, "Cancel anytime" |

Run `python3 -c "import sys; sys.path.insert(0,'toolkit'); from adkit.qa import claims_lint; print(claims_lint(['brief/PROMPT.md','film.py']))"`
on the brief and the film before rendering finals.

## The product in one line
Clipzing turns a long video (a YouTube link or an uploaded file, up to 2 hours) into vertical 9:16 short clips:
it finds the moments that stand on their own, scores and ranks them, reframes to vertical around the speaker,
adds word-by-word animated captions, and helps you post them.

## Features: true lines and the picture that proves them

| Feature | Say (true) | Show | Never say |
|---|---|---|---|
| **Clip detection** | "It finds the moments worth posting." "Each clip gets a score from 0 to 100." "Best first." | A long waveform/transcript; moments lift out; score rings (0–100) sort best-first | "predicts views", "guaranteed viral". The score ranks clips against each other; it is not a forecast. |
| **Input** | "Paste a YouTube link, or upload a file." "Up to two hours." | A link pasted into the input, a file dropped | Longer than 2 h; other sources (Twitch, Zoom links…) |
| **Auto reframe** | "It keeps the speaker in frame." "Framed for podcasts, lessons, streams and sport." | A 16:9 frame with a 9:16 window gliding with the speaker | Bringing an off-camera speaker into frame |
| **Animated captions** | "Captions timed to every word." "30+ languages." "Pick a look." | The REAL caption engine (capture/src/captions.tsx) on the ad's own words | Exact style counts (the code has 38 templates while features.ts says 10 / 15; avoid counts or ask the owner) |
| **Hook voiceover** (Creator, Agency) | "A spoken hook for clips that start slow." "Six voices." | A clip's first second with a voice wave over it | That it's the creator's own voice (it is synthetic) |
| **AI B-roll** (Creator, Agency) | "Stock footage where it helps, never over the hook." | Cutaways sliding in on a timeline | "Shows your product/location" (stock is generic) |
| **Clip editor** | "Edit by the words." "Only Export renders." | Transcript beside the video; select text, the clip follows | A general video editor |
| **Scheduling** | "One calendar." "YouTube Shorts: scheduled and published." "TikTok: sent to your drafts." | Clips dropping onto calendar days; YouTube "Published", TikTok "Sent to drafts" | Publishing or scheduling to TikTok; posting to Instagram, LinkedIn, X, Facebook |
| **Autopilot** (Creator 1 channel, Agency 5) | "New upload, new clips, without opening the app." "Review mode holds every clip for your OK." | A channel's new upload flowing into clips and a calendar | That it works backwards on old uploads (it is forward only) |
| **Brand kit** (Creator 1, Agency unlimited) | "Your logo, fonts and colours on every clip." | Captions restyling into brand colours | "Clipzing watermark": there is none on paid plans |
| **AI copilot** (all plans, 100 msgs/day) | "Ask in plain language." "It asks before anything that publishes, spends or deletes." Real example asks: "Give these three clips punchier titles." "Add B-roll where he talks about the factory." "Schedule my five best clips across next week." | A chat bubble → the clips changing; an approval card | That it acts without approval |
| **AI agents / MCP** | "Use Clipzing from Claude, ChatGPT or Cursor." "Browser approval, no API key to paste." | An assistant chat driving Clipzing | That Starter agents can render/publish (read and edit only) |

## Platforms (the most common mistake)
- **YouTube Shorts**: scheduled and published by Clipzing. ✔
- **TikTok**: clips are **sent to the TikTok inbox as drafts**. You finish and post in the app. Drafts can't be scheduled for later, and they arrive within 10–25 minutes. ✔ "Send to TikTok" / "straight to your TikTok drafts". ✘ "Posts to TikTok"
- **Instagram Reels**: **export format only**. ✔ "Reels-ready" / "made for Reels". ✘ "Posts to Instagram"
- **LinkedIn, X, Facebook, Snapchat, Pinterest**: not supported. Don't show or say them. (The Path, 2026-10-19, said "even LinkedIn"; that was wrong and was flagged to the owner.)

## Plans (2026-10-19)
| Plan | Monthly | Yearly (= 2 months free) | Shorts / month | Processing min | Clips / video | Accounts | Autopilot | Brand kit | B-roll, hook VO | Clips kept |
|---|---|---|---|---|---|---|---|---|---|---|
| Starter | $14.99 | $149.90 | 40 | 240 | up to 5 | 1 (5 scheduled posts/mo) | – | – | – | 24 h |
| Creator | $38.99 | $389.90 | 500 | 1,500 | no per-video limit | 3 | 1 channel | 1 | ✔ | 48 h |
| Agency | $89.99 | $899.90 | 1,000 | 3,000 | no per-video limit | 10 | 5 channels | unlimited | ✔ | 72 h |

- **No free trial and no free plan.** Never say "free", "try free", or "start free".
- **No money-back guarantee.** Say "Cancel anytime".
- Annual billing: "2 months free".
- Prices in ads date quickly. Prefer no price; if you show one, read the source on the day.
- Copy rule from the plans file: state allowances in **processing minutes**, hours only as "~" approximations. Never a flat "25 hours of footage".

## Numbers that may appear on screen
- Illustrative UI numbers (followers, views, chart rows, streak days) are fine as part of a **story**, never as a
  claim about results. Keep them plausible, never attribute them to a real account, and don't caption them as a
  promise ("you WILL get 12k followers" ✘).
- Real numbers (users, clips made, hours saved) only if the owner provides them with their source.

## People, names, footage
- Fictional creator names and channel names only (e.g. "rivvo", "nova", "@yourchannel"). No real person, brand
  or show in thumbnails, titles or comments.
- The landing showcase clips (`public/clips/showcase-v2-*`) show REAL celebrities: **never in an ad.**
- Phone "footage" = Zing's own podcast (library/footage) or footage the owner has the rights to.
- Pexels/Unsplash people may not be shown as if they endorse or use Clipzing (their licence forbids it).
