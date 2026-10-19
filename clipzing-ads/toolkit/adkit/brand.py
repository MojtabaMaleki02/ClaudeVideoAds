"""adkit.brand: Clipzing's look, as data. Colours come from the product's own tokens (shortn-fe/app/globals.css,
tailwind.config.js), the wordmark and Zing from the product's own art. Nothing here is "inspired by" another brand."""
import json
import os

import numpy as np
from PIL import ImageFont

from . import core

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(SKILL, 'assets')
LIBRARY = os.environ.get('CLIPZING_ADS_LIBRARY', os.path.join(SKILL, 'library'))
FONTS = os.path.join(ASSETS, 'fonts')

def hx(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))

# ── palette ─────────────────────────────────────────────────────────────────
# Product UI ("Studio Cinematic" tokens, OKLCH converted to sRGB)
C = {
    'bg': hx('#060813'), 'bg_elevated': hx('#0D111D'), 'bg_overlay': hx('#161A26'), 'bg_sunken': hx('#02030B'),
    'fg': hx('#FAFAFA'), 'fg_muted': hx('#A4A4A4'), 'fg_subtle': hx('#717171'),
    'border': (255, 255, 255, 20), 'border_strong': (255, 255, 255, 36),
    'accent': hx('#975AFD'), 'accent_hover': hx('#8242E5'),      # purple-500 / purple-600 as the app renders them
    'success': hx('#00C57C'), 'warning': hx('#ECAA0B'), 'info': hx('#19AFFE'), 'danger': hx('#F94144'),
    # Brand (wordmark gradient, landing)
    'purple': hx('#A855F7'), 'purple_deep': hx('#9333EA'), 'violet': hx('#7C3AED'), 'lilac': hx('#C4B5FD'),
    'lip': hx('#5B21B6'), 'ink': hx('#2E1065'),
    'landing_deep': hx('#0F0F23'), 'landing_surface': hx('#1E1B4B'),
    # Zing's own body paint (components/mascot/art.ts)
    'zing_body': hx('#8B52CB'), 'zing_hem': hx('#6D3BC8'),
    # Streak / gamification
    'flame': hx('#FF9600'), 'flame_hi': hx('#FFC800'),
    # Virality score bands (score-low / mid / high tokens)
    'score_low': hx('#F94144'), 'score_mid': hx('#ECAA0B'), 'score_high': hx('#00C57C'),
}
STAGE_BASE = hx('#05060E')           # the film stage: a touch darker than the app so UI planes lift off it
LINE = C['accent']                   # the line of light
LINE_HI = C['lilac']

# Platforms Clipzing actually works with (see reference/product-facts.md before showing any other):
#   YouTube Shorts: scheduled and published.  TikTok: sent as a draft to the TikTok inbox.
#   Instagram Reels: correct export format only (no posting from Clipzing).
PLATFORM = {
    'youtube': {'name': 'YouTube Shorts', 'color': hx('#FF0033'), 'verb': 'published'},
    'tiktok': {'name': 'TikTok', 'color': hx('#FE2C55'), 'color2': hx('#25F4EE'), 'verb': 'sent to drafts'},
    'reels': {'name': 'Reels', 'color': hx('#E1306C'), 'color2': hx('#F77737'), 'verb': 'ready to post'},
}

# ── type ────────────────────────────────────────────────────────────────────
# Plus Jakarta Sans is the product's UI font (next/font in app/layout.tsx). Inter for dense UI numbers,
# Instrument Serif for the rare editorial accent, JetBrains Mono for code/API moments. All OFL, bundled.
FAMILIES = {
    'jakarta': ('PlusJakartaSans[wght].ttf', {'regular': 'Regular', 'medium': 'Medium', 'semibold': 'SemiBold', 'bold': 'Bold', 'extrabold': 'ExtraBold'}),
    'jakarta_italic': ('PlusJakartaSans-Italic[wght].ttf', {'regular': 'Italic', 'bold': 'Bold Italic', 'extrabold': 'ExtraBold Italic'}),
    'inter': ('Inter[opsz,wght].ttf', {'regular': 'Regular', 'medium': 'Medium', 'semibold': 'SemiBold', 'bold': 'Bold', 'extrabold': 'ExtraBold', 'black': 'Black'}),
    'serif': ('InstrumentSerif-Regular.ttf', {}),
    'serif_italic': ('InstrumentSerif-Italic.ttf', {}),
    'mono': ('JetBrainsMono[wght].ttf', {'regular': 'Regular', 'medium': 'Medium', 'bold': 'Bold'}),
    'anton': ('Anton-Regular.ttf', {}),          # caption-style display (as the product's caption presets use)
    'bebas': ('BebasNeue-Regular.ttf', {}),
    'montserrat': ('Montserrat[wght].ttf', {'bold': 'Bold', 'extrabold': 'ExtraBold', 'black': 'Black'}),
}
_fonts = {}
def font(size, weight='bold', family='jakarta'):
    """font(64) → Plus Jakarta Sans Bold 64 px. Weights: regular medium semibold bold extrabold (black on inter)."""
    k = (int(size), weight, family)
    if k not in _fonts:
        fn, weights = FAMILIES[family]
        f = ImageFont.truetype(os.path.join(FONTS, fn), max(1, int(size)))
        if weights:
            name = weights.get(weight) or weights.get('bold') or next(iter(weights.values()))
            try:
                f.set_variation_by_name(name)
            except Exception:
                pass
        _fonts[k] = f
    return _fonts[k]

# ── marks ───────────────────────────────────────────────────────────────────
def asset(*p): return os.path.join(ASSETS, *p)
def lib(*p): return os.path.join(LIBRARY, *p)

def wordmark(max_h=None):
    """The horizontal lock-up (Zing icon + 'Clipzing' in Plus Jakarta Sans 700, #A855F7 → #9333EA), transparent.
    Brand rule: only move, scale, fade, blur or mask it. Never recolour, glow, distort or rotate it at rest."""
    return core.load_rgba(asset('brand', 'wordmark.png'), max_h)

def wordmark_white(max_h=None):
    """Single-colour white lock-up for busy or coloured backgrounds."""
    return core.load_rgba(asset('brand', 'wordmark-white.png'), max_h)

def wordmark_text(max_h=None, white=False):
    """Just the word "Clipzing" from the lock-up, tight-cropped: for when Zing himself stands above it
    (never two Zings on screen)."""
    k = ('wmtext', white, max_h)
    if k not in core._img_cache:
        wm = wordmark_white() if white else wordmark()
        t = wm[:, int(wm.shape[1] * WORDMARK_META['icon_frac']) + 6:]
        ys, xs = np.nonzero(t[..., 3] > 8)
        t = np.ascontiguousarray(t[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
        if max_h and t.shape[0] > max_h:
            import cv2
            t = cv2.resize(t, (int(t.shape[1] * max_h / t.shape[0]), max_h), interpolation=cv2.INTER_AREA)
        core._img_cache[k] = t
    return core._img_cache[k]

def icon(max_h=None):
    """Zing's face icon alone (the app icon / favicon art)."""
    return core.load_rgba(asset('brand', 'icon.png'), max_h)

WORDMARK_META = {'icon_frac': 350 / 957}    # the icon's share of the tight lock-up width (assets/brand/wordmark.png)

# ── Zing ────────────────────────────────────────────────────────────────────
_zmeta = {}
def zing_meta(name):
    if name not in _zmeta:
        p = lib('zing', name, 'meta.json')
        _zmeta[name] = json.load(open(p)) if os.path.exists(p) else {'fps': 30, 'frames': len(_zframes(name)), 'loop': True}
    return _zmeta[name]

def _zframes(name):
    d = lib('zing', name)
    if not os.path.isdir(d):
        raise FileNotFoundError(f'Zing pose "{name}" is not in the library ({d}). Render it with '
                                f'toolkit/capture (node capture/zing.mjs {name}) or pick one from zing_poses().')
    return sorted(f for f in os.listdir(d) if f.endswith(('.webp', '.png')))

def zing_poses():
    d = lib('zing')
    return sorted(x for x in os.listdir(d) if os.path.isdir(os.path.join(d, x))) if os.path.isdir(d) else []

def zing(name, t=0.0, max_h=720):
    """A frame of Zing from his own rig (library/zing/<name>/). Loops by default; meta.json can say loop=false."""
    fr = _zframes(name)
    m = zing_meta(name)
    i = int(max(0.0, t) * m.get('fps', 30) + 1e-6)
    i = i % len(fr) if m.get('loop', True) else min(i, len(fr) - 1)
    return core.load_rgba(lib('zing', name, fr[i]), max_h)

def zing_box(name):
    """Zing's body box inside the sprite canvas, as fractions (x0, y0, x1, y1): for contact shadows and anchors."""
    return tuple(zing_meta(name).get('body_box', (0.19, 0.18, 0.81, 0.80)))

def footage(name, t, w, h, fps=30):
    """A cover-cropped frame of Zing's own podcast footage (library/footage/<name>/), ping-ponged so it never jumps.
    The landing showcase clips show real celebrities: never use them in an ad."""
    import cv2
    d = lib('footage', name)
    fr = sorted(f for f in os.listdir(d) if f.endswith(('.jpg', '.webp', '.png')))
    n = len(fr)
    i = int(t * fps) % (2 * n - 2) if n > 1 else 0
    i = i if i < n else 2 * n - 2 - i
    k = ('foot', name, i, int(w), int(h))
    if k in core._img_cache: return core._img_cache[k]
    im = cv2.cvtColor(cv2.imread(os.path.join(d, fr[i]), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    s = max(w / im.shape[1], h / im.shape[0])
    im = cv2.resize(im, (int(im.shape[1] * s) + 1, int(im.shape[0] * s) + 1), interpolation=cv2.INTER_AREA)
    y0 = (im.shape[0] - int(h)) // 2; x0 = (im.shape[1] - int(w)) // 2
    out = np.ascontiguousarray(im[y0:y0 + int(h), x0:x0 + int(w)])
    core._img_cache[k] = out
    return out

def screen(name, max_w=None):
    """A captured product screen (library/screens/<name>.png), real UI with fictional data."""
    p = lib('screens', name if name.endswith('.png') else name + '.png')
    im = core.load_rgba(p)
    if max_w and im.shape[1] > max_w:
        import cv2
        im = cv2.resize(im, (max_w, int(im.shape[0] * max_w / im.shape[1])), interpolation=cv2.INTER_AREA)
    return im

def caption_frames(name):
    """Frames of a real Clipzing caption style rendered for this film's words (library/captions/<name>/)."""
    d = lib('captions', name)
    return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith('.png')]
