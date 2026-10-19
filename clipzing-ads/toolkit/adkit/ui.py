"""adkit.ui: Clipzing's UI language, drawn in code (Pillow, supersampled for crisp edges).

Material rules (the product's "Studio Cinematic" system, and the owner's taste):
  - solid surfaces in the bg / bg-elevated / bg-overlay steps, never frosted white glass
  - 1 px hairline borders (white at 8 %), a faint lit top edge, soft deep shadows
  - one accent: purple; buttons are chunky with a darker lip under them
  - no bright gradient + glow + colour-swap combos, no neon
Every function draws into a Pillow RGBA image in full-size pixel units; Layer handles supersampling.
"""
import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from . import brand
from .brand import C, font

import functools

from . import core

def _default_ss():
    return 2 if core.SCALE >= 0.99 else 1   # previews skip supersampling

def cached(maxsize=24):
    """Cache a layer-building function on its (quantised) arguments: UI is drawn once, not per motion-blur sample.
    Quantise continuous inputs yourself, e.g. build(round(p, 2)), so nearby sub-frames share a layer.
    MEMORY: a full-frame layer is ~8 MB (9:16 RGBA) and every render worker keeps its own cache. Keep maxsize small
    (8–32) for layers that change every frame; large caches × 8 workers swapped a 17 GB Mac to death (Got You)."""
    return functools.lru_cache(maxsize=maxsize)

class Layer:
    """A transparent drawing surface of w×h full-size pixels, supersampled. .rgba() → numpy uint8 (h, w, 4)."""
    def __init__(self, w, h, ss=None):
        ss = ss or _default_ss()
        self.w, self.h, self.ss = int(w), int(h), ss
        self.im = Image.new('RGBA', (self.w * ss, self.h * ss), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def S(self, *v):
        return [x * self.ss for x in v] if len(v) > 1 else v[0] * self.ss

    def rgba(self):
        return np.asarray(self.im.resize((self.w, self.h), Image.LANCZOS)).copy()

    def paste(self, src, x, y, opacity=1.0):
        """Paste an RGBA numpy/PIL image at full-size (x, y)."""
        im = src if isinstance(src, Image.Image) else Image.fromarray(src)
        im = im.convert('RGBA')
        if self.ss != 1: im = im.resize((max(1, im.width * self.ss), max(1, im.height * self.ss)), Image.LANCZOS)
        if opacity < 1: im.putalpha(im.getchannel('A').point(lambda a: int(a * opacity)))
        self.im.alpha_composite(im, (int(x * self.ss), int(y * self.ss)))

    # ── primitives ──────────────────────────────────────────────────────────
    def rrect(self, box, r, fill=None, outline=None, width=1):
        x0, y0, x1, y1 = box
        self.d.rounded_rectangle(self.S(x0, y0, x1, y1), radius=r * self.ss, fill=fill, outline=outline, width=max(1, int(width * self.ss)))

    def shadow(self, box, r, blur=28, offset=(0, 14), opacity=0.55, color=(0, 0, 0)):
        """A soft drop shadow under a rounded box."""
        x0, y0, x1, y1 = box
        pad = blur * 3
        sh = Image.new('L', (int((x1 - x0 + pad * 2) * self.ss), int((y1 - y0 + pad * 2) * self.ss)), 0)
        ImageDraw.Draw(sh).rounded_rectangle([pad * self.ss, pad * self.ss, (pad + x1 - x0) * self.ss, (pad + y1 - y0) * self.ss], r * self.ss, fill=int(255 * opacity))
        sh = sh.filter(ImageFilter.GaussianBlur(blur * self.ss / 2))
        col = Image.new('RGBA', sh.size, color + (0,)); col.putalpha(sh)
        self.im.alpha_composite(col, (int((x0 - pad + offset[0]) * self.ss), int((y0 - pad + offset[1]) * self.ss)))

    def gradient_rrect(self, box, r, top, bottom, alpha=255):
        """A rounded box filled with a vertical gradient (top → bottom colours)."""
        x0, y0, x1, y1 = [int(v * self.ss) for v in box]
        w, h = max(1, x1 - x0), max(1, y1 - y0)
        g = np.linspace(0, 1, h)[:, None]
        arr = np.zeros((h, w, 4), np.uint8)
        for i in range(3): arr[..., i] = (top[i] + (bottom[i] - top[i]) * g).astype(np.uint8)
        arr[..., 3] = alpha
        m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r * self.ss, fill=255)
        tile = Image.fromarray(arr); tile.putalpha(ImageChops.multiply(tile.getchannel('A'), m))
        self.im.alpha_composite(tile, (x0, y0))

def text_w(s, f, tracking=0.0):
    return f.getlength(s) + tracking * f.size * max(0, len(s) - 1)

def fit_size(s, max_w, size, weight='bold', family='jakarta', min_size=12):
    """The largest font size ≤ `size` at which `s` fits in max_w."""
    while size > min_size and font(size, weight, family).getlength(s) > max_w: size -= 2
    return size

def _text_ss(layer, xy, s, size, weight='bold', family='jakarta', fill=C['fg'], anchor='la', tracking=0.0):
    """Layer.type((x, y), 'text', size, weight, family, fill, anchor, tracking): text at full-size coords with
    the brand font, supersampled. `tracking` in em (display type wants about -0.02)."""
    f = font(size * layer.ss, weight, family)
    x, y = xy[0] * layer.ss, xy[1] * layer.ss
    if not tracking:
        layer.d.text((x, y), s, font=f, fill=fill, anchor=anchor); return
    widths = [f.getlength(ch) for ch in s]
    total = sum(widths) + tracking * f.size * (len(s) - 1)
    x0 = x - total / 2 if anchor[0] == 'm' else x - total if anchor[0] == 'r' else x
    for ch, w in zip(s, widths):
        layer.d.text((x0, y), ch, font=f, fill=fill, anchor='l' + anchor[1]); x0 += w + tracking * f.size
Layer.type = _text_ss

# ── components ──────────────────────────────────────────────────────────────
def surface(L, box, r=28, fill=C['bg_elevated'], lit=True, shadow=True, alpha=255, hairline=True):
    """A solid card: shadow, fill, 1 px hairline, a faint lit top edge."""
    x0, y0, x1, y1 = box
    if shadow: L.shadow(box, r, blur=30, offset=(0, 18), opacity=0.6)
    L.rrect(box, r, fill=fill + (alpha,))
    if hairline: L.rrect(box, r, outline=(255, 255, 255, int(20 * alpha / 255)), width=1)
    if lit:  # a lit top edge: a thin bright arc that fades toward the sides
        m = Image.new('L', L.im.size, 0)
        ImageDraw.Draw(m).rounded_rectangle(L.S(x0, y0, x1, y1), r * L.ss, outline=255, width=max(1, int(1.2 * L.ss)))
        cut = Image.new('L', L.im.size, 0)
        ImageDraw.Draw(cut).rectangle(L.S(x0, y0, x1, y0 + r * 0.9), fill=255)
        m = ImageChops.multiply(m, cut)
        grad = np.zeros((L.im.size[1], L.im.size[0]), np.float32)
        xs = (np.arange(L.im.size[0]) / L.ss - x0) / max(1, x1 - x0)
        grad[:] = np.clip(1 - np.abs(xs - 0.5) * 2, 0, 1) ** 1.5
        m = Image.fromarray((np.asarray(m, np.float32) * grad * 0.33 * alpha / 255).astype(np.uint8))
        lit_l = Image.new('RGBA', L.im.size, (255, 255, 255, 0)); lit_l.putalpha(m)
        L.im.alpha_composite(lit_l)

def button(L, box, label, kind='primary', press=0.0, size=34, icon=None):
    """A chunky button with a darker lip. press 0..1 sinks it into its lip (a tap)."""
    x0, y0, x1, y1 = box
    lip = max(4, (y1 - y0) * 0.12)
    dy = lip * 0.8 * press
    if kind == 'primary':
        top, mid, lipc, fg = C['purple'], C['violet'], C['lip'], (255, 255, 255)
    elif kind == 'success':
        top, mid, lipc, fg = (0x2B, 0xD9, 0x8F), C['success'], (0x00, 0x8A, 0x57), (255, 255, 255)
    else:
        top, mid, lipc, fg = C['bg_overlay'], C['bg_overlay'], C['bg_sunken'], C['fg']
    r = (y1 - y0) / 2 if (y1 - y0) < 90 else 26
    L.shadow((x0, y0 + lip, x1, y1 + lip), r, blur=22, offset=(0, 10), opacity=0.5 * (1 - press * 0.5))
    L.rrect((x0, y0 + lip, x1, y1 + lip), r, fill=lipc + (255,))
    L.gradient_rrect((x0, y0 + dy, x1, y1 + dy), r, top, mid)
    if kind != 'primary' and kind != 'success':
        L.rrect((x0, y0 + dy, x1, y1 + dy), r, outline=(255, 255, 255, 30), width=1)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 + dy
    if icon:
        tw = font(size, 'bold').getlength(label)
        glyph(L, icon, cx - tw / 2 - size * 0.55, cy, size * 0.8, fg)
        L.type((cx + size * 0.35, cy), label, size, 'bold', fill=fg, anchor='mm')
    else:
        L.type((cx, cy), label, size, 'bold', fill=fg, anchor='mm')

def pill(L, cx, cy, label, size=26, fill=C['bg_overlay'], fg=C['fg'], weight='semibold', pad=(22, 12), outline=True, alpha=255):
    """A rounded pill centred at (cx, cy). Returns its box."""
    tw = font(size, weight).getlength(label)
    w, h = tw + pad[0] * 2, size + pad[1] * 2
    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    L.rrect(box, h / 2, fill=fill + (alpha,))
    if outline: L.rrect(box, h / 2, outline=(255, 255, 255, int(28 * alpha / 255)), width=1)
    L.type((cx, cy), label, size, weight, fill=fg + (alpha,) if len(fg) == 3 else fg, anchor='mm')
    return box

def progress(L, box, p, color=C['accent'], track=C['bg_overlay'], glow=True):
    x0, y0, x1, y1 = box
    r = (y1 - y0) / 2
    L.rrect(box, r, fill=track + (255,))
    if p > 0.001:
        xe = x0 + max(y1 - y0, (x1 - x0) * min(1, p))
        if glow: L.shadow((x0, y0, xe, y1), r, blur=10, offset=(0, 0), opacity=0.55, color=color)
        L.gradient_rrect((x0, y0, xe, y1), r, tuple(min(255, c + 40) for c in color), color)

def ring(L, cx, cy, r, p, width=12, color=C['accent'], track=C['bg_overlay']):
    """A progress ring (score rings, approvals). p in 0..1, starts at 12 o'clock."""
    if r <= max(1.0, width / 2): return          # too small to draw (mid pop-in)
    b = L.S(cx - r, cy - r, cx + r, cy + r)
    L.d.arc(b, 0, 360, fill=track + (255,), width=int(width * L.ss))
    if p > 0.001:
        L.d.arc(b, -90, -90 + 360 * min(1, p), fill=color + (255,), width=int(width * L.ss))

def score_color(score):
    return C['score_high'] if score >= 80 else C['score_mid'] if score >= 60 else C['score_low']

def score_badge(L, cx, cy, score, r=46, p=1.0, label=True):
    """The virality score as the product shows it: a ring in its band colour with the number inside."""
    if r < 10: return                            # mid pop-in: nothing legible yet
    col = score_color(score)
    L.d.ellipse(L.S(cx - r, cy - r, cx + r, cy + r), fill=C['bg_sunken'] + (230,))
    ring(L, cx, cy, r - 5, p * score / 100, width=max(5, r * 0.16), color=col, track=(40, 44, 58))
    if label: L.type((cx, cy + 1), str(int(round(score * p))), int(r * 0.78), 'extrabold', fill=(255, 255, 255), anchor='mm')

def odometer(L, x, y, value, digits=None, cell=(96, 132), size=110, color=(255, 255, 255), cellfill=C['bg_overlay'], gap=12, roll=None):
    """Digits in FIXED cells that roll (never a number re-centring itself). value may be fractional while counting:
    each cell shows its digit rolling toward the next. One number, one function: drive every display of a count
    from the same value. Returns the total width."""
    v = max(0.0, float(value))
    n = digits or max(1, len(str(int(v))))
    cw, ch = cell
    for k in range(n):
        place = 10 ** (n - 1 - k)
        cx0 = x + k * (cw + gap)
        L.rrect((cx0, y, cx0 + cw, y + ch), 18, fill=cellfill + (255,))
        L.rrect((cx0, y, cx0 + cw, y + ch), 18, outline=(255, 255, 255, 24), width=1)
        d = (v / place) % 10
        lower = int(d)
        frac = (d - lower) if place == 1 or (v % place) > place - 1 else 0.0
        if roll is not None: frac = roll if k == n - 1 else frac
        # leading zeros stay empty
        if v < place and k < n - 1 and not (lower or frac):
            continue
        clip = Image.new('RGBA', (int(cw * L.ss), int(ch * L.ss)), (0, 0, 0, 0))
        dc = ImageDraw.Draw(clip)
        f = font(size * L.ss, 'extrabold')
        for j, dd in ((0, lower % 10), (1, (lower + 1) % 10)):
            yy = (ch / 2 - frac * ch + j * ch) * L.ss
            dc.text((cw / 2 * L.ss, yy), str(dd), font=f, fill=color + (255,), anchor='mm')
        L.im.alpha_composite(clip, (int(cx0 * L.ss), int(y * L.ss)))
    return n * cw + (n - 1) * gap

def waveform(L, box, amps, color=C['accent'], gap=0.35, alpha=255):
    """Rounded audio bars across box (amps 0..1)."""
    x0, y0, x1, y1 = box
    n = len(amps); bw = (x1 - x0) / n
    cy = (y0 + y1) / 2
    for i, a in enumerate(amps):
        h = max(bw * (1 - gap), (y1 - y0) * a)
        bx = x0 + i * bw
        L.rrect((bx, cy - h / 2, bx + bw * (1 - gap), cy + h / 2), bw * (1 - gap) / 2, fill=color + (alpha,))

def avatar(L, cx, cy, r, initials='', color=C['violet'], ring_color=None):
    L.d.ellipse(L.S(cx - r, cy - r, cx + r, cy + r), fill=color + (255,))
    if ring_color: L.d.ellipse(L.S(cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4), outline=ring_color + (255,), width=int(3 * L.ss))
    if initials: L.type((cx, cy + 1), initials, int(r * 0.85), 'bold', fill=(255, 255, 255), anchor='mm')

# ── glyphs (simple, code-drawn; platform marks only for platforms Clipzing really supports) ──
def glyph(L, name, cx, cy, s, color=(255, 255, 255)):
    d = L.d
    S = L.ss
    col = color + (255,) if len(color) == 3 else color
    if name == 'play':
        d.polygon([((cx - s * .28) * S, (cy - s * .36) * S), ((cx + s * .38) * S, cy * S), ((cx - s * .28) * S, (cy + s * .36) * S)], fill=col)
    elif name == 'plus':
        w = s * 0.13
        d.rounded_rectangle(L.S(cx - s * .4, cy - w, cx + s * .4, cy + w), w * S, fill=col)
        d.rounded_rectangle(L.S(cx - w, cy - s * .4, cx + w, cy + s * .4), w * S, fill=col)
    elif name == 'check':
        d.line([((cx - s * .32) * S, cy * S), ((cx - s * .08) * S, (cy + s * .24) * S), ((cx + s * .36) * S, (cy - s * .26) * S)], fill=col, width=int(s * .16 * S), joint='curve')
    elif name == 'link':
        w = int(s * .12 * S)
        d.rounded_rectangle(L.S(cx - s * .46, cy - s * .2, cx + s * .06, cy + s * .2), s * .2 * S, outline=col, width=w)
        d.rounded_rectangle(L.S(cx - s * .06, cy - s * .2, cx + s * .46, cy + s * .2), s * .2 * S, outline=col, width=w)
    elif name == 'spark':  # four-point spark (AI / copilot)
        pts = []
        for k in range(8):
            a = math.pi / 4 * k - math.pi / 2
            rr = s * (.5 if k % 2 == 0 else .14)
            pts.append(((cx + math.cos(a) * rr) * S, (cy + math.sin(a) * rr) * S))
        d.polygon(pts, fill=col)
    elif name == 'calendar':
        w = int(s * .1 * S)
        d.rounded_rectangle(L.S(cx - s * .42, cy - s * .34, cx + s * .42, cy + s * .42), s * .1 * S, outline=col, width=w)
        d.line([((cx - s * .42) * S, (cy - s * .1) * S), ((cx + s * .42) * S, (cy - s * .1) * S)], fill=col, width=w)
    elif name == 'bolt':
        d.polygon([((cx + s * .1) * S, (cy - s * .5) * S), ((cx - s * .3) * S, (cy + s * .06) * S), ((cx - s * .02) * S, (cy + s * .06) * S),
                   ((cx - s * .1) * S, (cy + s * .5) * S), ((cx + s * .3) * S, (cy - s * .08) * S), ((cx + s * .02) * S, (cy - s * .08) * S)], fill=col)
    elif name == 'cc':  # captions
        w = int(s * .09 * S)
        d.rounded_rectangle(L.S(cx - s * .46, cy - s * .32, cx + s * .46, cy + s * .32), s * .12 * S, outline=col, width=w)
        for dx in (-.16, .16):
            d.arc(L.S(cx + s * dx - s * .12, cy - s * .12, cx + s * dx + s * .12, cy + s * .12), 40, 320, fill=col, width=w)
    elif name == 'youtube':  # YouTube Shorts: a red rounded tile with a white play
        d.rounded_rectangle(L.S(cx - s * .5, cy - s * .36, cx + s * .5, cy + s * .36), s * .14 * S, fill=brand.PLATFORM['youtube']['color'] + (255,))
        d.polygon([((cx - s * .12) * S, (cy - s * .17) * S), ((cx + s * .2) * S, cy * S), ((cx - s * .12) * S, (cy + s * .17) * S)], fill=(255, 255, 255, 255))
    elif name == 'tiktok':  # a note with the cyan/red offset
        for off, c2 in ((-s * .04, brand.PLATFORM['tiktok']['color2']), (s * .04, brand.PLATFORM['tiktok']['color']), (0, (255, 255, 255))):
            w = s * .1
            d.rounded_rectangle(L.S(cx - w / 2 + off, cy - s * .42 + off, cx + w / 2 + off, cy + s * .2 + off), w / 2 * S, fill=c2 + (255,))
            d.ellipse(L.S(cx - s * .3 + off, cy + s * .06 + off, cx + w / 2 + off, cy + s * .4 + off), fill=c2 + (255,))
            d.arc(L.S(cx + off, cy - s * .48 + off, cx + s * .36 + off, cy - s * .14 + off), 180, 270, fill=c2 + (255,), width=int(w * S))
    elif name == 'reels':
        L.gradient_rrect((cx - s * .46, cy - s * .46, cx + s * .46, cy + s * .46), s * .16, brand.PLATFORM['reels']['color2'], brand.PLATFORM['reels']['color'])
        d.rounded_rectangle(L.S(cx - s * .3, cy - s * .3, cx + s * .3, cy + s * .3), s * .1 * S, outline=(255, 255, 255, 255), width=int(s * .07 * S))
        d.polygon([((cx - s * .08) * S, (cy - s * .12) * S), ((cx + s * .14) * S, cy * S), ((cx - s * .08) * S, (cy + s * .12) * S)], fill=(255, 255, 255, 255))

# ── device frames ───────────────────────────────────────────────────────────
def phone(w, h, screen_rgba=None, radius=None, bezel=None, notch=True):
    """A generic modern phone (no maker's marks) of outer size w×h. Returns (rgba, screen_box)."""
    L = Layer(w, h)
    r = radius or w * 0.14
    bz = bezel or w * 0.035
    L.shadow((0, 0, w, h), r, blur=40, offset=(0, 28), opacity=0.7)
    L.gradient_rrect((0, 0, w, h), r, (58, 56, 72), (22, 22, 30))
    L.rrect((2, 2, w - 2, h - 2), r - 2, outline=(255, 255, 255, 40), width=1.2)
    sb = (bz, bz, w - bz, h - bz)
    L.rrect(sb, r - bz, fill=(4, 4, 8, 255))
    if screen_rgba is not None:
        scr = Image.fromarray(screen_rgba).convert('RGBA').resize((int((sb[2] - sb[0]) * L.ss), int((sb[3] - sb[1]) * L.ss)), Image.LANCZOS)
        m = Image.new('L', scr.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, scr.width - 1, scr.height - 1], (r - bz) * L.ss, fill=255)
        scr.putalpha(ImageChops.multiply(scr.getchannel('A'), m))
        L.im.alpha_composite(scr, (int(sb[0] * L.ss), int(sb[1] * L.ss)))
    if notch:
        nw, nh = w * 0.3, w * 0.075
        L.rrect((w / 2 - nw / 2, bz + w * 0.03, w / 2 + nw / 2, bz + w * 0.03 + nh), nh / 2, fill=(0, 0, 0, 255))
    return L.rgba(), sb

def browser(w, h, screen_rgba=None, url='clipzing.com/dashboard', radius=22):
    """A minimal dark browser window (no vendor marks) of outer size w×h. Returns (rgba, content_box)."""
    L = Layer(w, h)
    bar = 56
    L.shadow((0, 0, w, h), radius, blur=44, offset=(0, 30), opacity=0.7)
    L.rrect((0, 0, w, h), radius, fill=(18, 19, 28, 255))
    L.rrect((0, 0, w, h), radius, outline=(255, 255, 255, 34), width=1)
    for i, c in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))):
        L.d.ellipse(L.S(24 + i * 24, bar / 2 - 7, 38 + i * 24, bar / 2 + 7), fill=c + (255,))
    L.rrect((w * 0.3, 12, w * 0.7, bar - 12), (bar - 24) / 2, fill=(30, 32, 44, 255))
    L.type((w * 0.5, bar / 2), url, 20, 'medium', fill=C['fg_muted'], anchor='mm')
    cb = (0, bar, w, h)
    if screen_rgba is not None:
        scr = Image.fromarray(screen_rgba).convert('RGBA').resize((int(w * L.ss), int((h - bar) * L.ss)), Image.LANCZOS)
        m = Image.new('L', scr.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([0, -radius * L.ss, scr.width - 1, scr.height - 1], radius * L.ss, fill=255)
        scr.putalpha(ImageChops.multiply(scr.getchannel('A'), m))
        L.im.alpha_composite(scr, (0, int(bar * L.ss)))
    return L.rgba(), cb

def cursor(size=44, color=(255, 255, 255)):
    """A pointer arrow sprite (for UI demos), with its hot-spot at (0, 0)."""
    L = Layer(size, size * 1.4)
    s = size
    pts = [(2, 2), (2, s * 1.05), (s * .3, s * .8), (s * .5, s * 1.25), (s * .66, s * 1.18), (s * .46, s * .74), (s * .82, s * .74)]
    L.d.polygon([(x * L.ss + 3 * L.ss, y * L.ss + 4 * L.ss) for x, y in pts], fill=(0, 0, 0, 90))
    L.d.polygon([(x * L.ss, y * L.ss) for x, y in pts], fill=(10, 10, 14, 255))
    inner = [(x * 0.82 + s * 0.06, y * 0.82 + s * 0.1) for x, y in pts]
    L.d.polygon([(x * L.ss, y * L.ss) for x, y in inner], fill=color + (255,))
    return L.rgba()
