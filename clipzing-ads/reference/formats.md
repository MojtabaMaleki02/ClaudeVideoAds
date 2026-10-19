# Formats

| Output | Size | fps | Length | Where |
|---|---|---|---|---|
| **Short, vertical** | 1080 × 1920 (9:16) | 60 | 15–25 s + 2 s end card (TikTok sweet spot ≤ 25 s) | TikTok, YouTube Shorts, Reels |
| **Film, horizontal** | 1920 × 1080 (16:9) | 60 | 15–30 s | YouTube, landing hero, X/LinkedIn organic by the owner |
| **Long, horizontal** | 1920 × 1080 | 30 or 60 | 45–120 s (tour / explainer) | YouTube, landing page, sales |
| **Long, vertical cut** | 1080 × 1920 | 60 | 30–45 s, chapters picked | Shorts |
| Square (optional) | 1080 × 1080 | 60 | as the short | feeds that prefer 1:1 |

`FMT=9x16 | 16x9 | 1x1` selects the layout. **A re-layout, never a crop**: each station decides its own geometry
with `if core.PORTRAIT:` (stack instead of side-by-side, bigger type, the phone fills more of the frame).

## 9:16 safe zones (1080 × 1920)
- TikTok: the right rail (x 930–1080, y 760–1560), the caption and username (y > 1500), the top tabs (y < 210).
- Shorts: the right rail (x 940–1080, y 900–1620), the title and channel (y > 1520), the top bar (y < 160).
- Keep supers, faces, the wordmark and key UI inside x 60–900, y 230–1480. This includes the small lock-up "bug" at the top
  (put it at y ≈ 230, not 120) and the last line of a slam stack (The Link's "SHORTER." first sat at y 1565). Check with
  `qa.safe_zones(still, out)` on every station's still. After moving anything to clear a zone, re-check that it doesn't
  cover Zing's face (the moved phone covered his eye once).

## Readability on a phone
- 9:16 supers ≥ 72 px; UI labels ≥ 34 px; nothing under 26 px. 16:9 supers ≥ 64 px.
- Hold text ≥ 0.6 s (≈ 0.3 s per word + 0.5 s).
- Contrast: white or lilac on the dark stage; never purple text on purple glow.

## Render budget (8 cores)
- Preview (half size, 30 fps): about 1–3 min for 20 s.
- Final 60 fps, full size: about 10–20 min per format for 20 s (motion-blurred frames cost ×N sub-samples).
- Long-form at 60 fps scales linearly (90 s ≈ 1–1.5 h per format). Use 30 fps for talky tours, 60 fps for showpieces.
- `render.py FILM all OUT -j 8` interleaves frames across workers; it can also run in the background.

## Delivery
- Master: H.264 CRF 15, yuv420p, AAC 320k, faststart (`render.py encode`).
- Upload copy: CRF 20, capped at 25 Mb/s (`--upload`). TikTok's limit is generous, but phones upload faster.
- Cover frame (JPG) from a moment where the brand and the idea are readable together.
- A POSTING kit: caption text (no false claims), 3–5 hashtags, the first comment, and the bio link with UTM
  (`?utm_source=tiktok&utm_medium=organic&utm_campaign=<slug>`).
