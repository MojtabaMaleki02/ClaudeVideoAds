"""Got You: a Clipzing promo with a story, built with the clipzing-ads skill (adkit).

A creator is stuck at 200 followers while their next followers scroll short videos. Zing: "Don't worry. I got you."
Then the product, one feature per beat: a long video's link → short clips of the best moments → captions in real
Clipzing styles → smart reframing (podcast, stream, gameplay) → B-roll → a week on the calendar (YouTube Shorts
scheduled, TikTok drafts, Instagram Reels-ready) → "Clipzing. Long videos in. Shorts out."
One continuous camera through nine stations. See brief/PROMPT.md.
"""
import math
import os
import sys

import cv2
import numpy as np

TOOLKIT = os.environ.get('ADKIT', os.path.expanduser('~/shorten/.claude/skills/clipzing-ads/toolkit'))
sys.path.insert(0, TOOLKIT)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from adkit import brand, core, fx, ui                                     # noqa: E402
from adkit.brand import C, LINE                                           # noqa: E402
from adkit.core import (D, H, PORTRAIT, W, Camera, Plane, clamp, composite_plane, composite_sprite,  # noqa: E402
                        eback, ein, einout, eout, lerp, new_frame, pose_mix, prog, shake_at, stage, v3)
from adkit.timeline import Cues, Words                                    # noqa: E402
import game                                                                # noqa: E402

END = 38.0
VO_OFF = 0.05
WORDS = Words(os.path.join(HERE, 'voice', 'words.json'), VO_OFF)
w = WORDS.t
P = PORTRAIT
def pf(a, b): return a if P else b

T = {k: w(*v) if isinstance(v, tuple) else w(v) for k, v in {
    'did': 'did', 'next': 'next', 'scrolling': 'scrolling', 'right': 'right', 'stuck': 'stuck', 'two': 'two', 'with': 'with',
    'grow': 'grow', 'dont': "don't", 'i': 'i', 'got': 'got', 'paste': 'paste', 'link': 'link', 'clipzing1': ('clipzing', 1),
    'long': ('long', 1), 'short2': ('short', 2), 'clips': ('clips', 1), 'best': 'best', 'captions': 'captions', 'in1': ('in', 1),
    'timed': 'timed', 'podcast': 'podcast', 'stream': 'stream', 'gameplay': 'gameplay', 'keeps': 'keeps', 'frame': 'frame',
    'add': 'add', 'broll': 'b-roll', 'then': 'then', 'schedule': 'schedule', 'never': 'never', 'day': 'day',
    'clipzing2': ('clipzing', 2), 'long2': ('long', 2), 'shorts': 'shorts'}.items()}
T['press'] = WORDS.end('link') + 0.15
T['land'] = T['clipzing2'] - 0.02
T['endcard'] = 35.8
WH = {  # whips: (start, duration, roll)
    'profile': (T['stuck'] - 0.42, 0.42, 6), 'panel': (T['paste'] - 0.42, 0.42, -7), 'strip': (T['clipzing1'] + 0.15, 0.45, 7),
    'caps': (T['captions'] - 0.42, 0.42, -6), 'ref': (T['podcast'] - 0.42, 0.42, 7), 'broll': (T['add'] - 0.38, 0.38, -6),
    'sched': (T['then'] - 0.05, 0.42, 7), 'end': (T['clipzing2'] - 0.5, 0.45, 0)}

# ── stations ────────────────────────────────────────────────────────────────
WALL = Plane(v3(0, 0, 0))
PROF = Plane(v3(0, -300, -2400))
PANEL = Plane(v3(1900, -2500, -4300), yaw=-14)
STRIP = Plane(v3(-1700, -2700, -5900), yaw=12)
CAPS = Plane(v3(1700, -1900, -7600), yaw=-12)
REF = Plane(v3(-1800, -1700, -9400), yaw=10)
BROLL = Plane(v3(1600, -2300, -11200), yaw=-12)
SCHED = Plane(v3(-1500, -2100, -13000), yaw=10)
FOCUS = lambda cam: float(cam.to_cam(cam.target[None])[0, 2])

ICONS = {n: core.load_rgba(os.path.join(HERE, 'assets', 'icons', f'{n}.png')) for n in ('youtube', 'youtubeshorts', 'tiktok', 'instagram')}
def icon(n, size): return cv2.resize(ICONS[n], (int(size), int(size)), interpolation=cv2.INTER_AREA)

# ── S1: the feed (your next followers, scrolling) ───────────────────────────
POOL = [('footage', 'closeup', 10), ('footage', 'coffee', 0), ('game', None, 1.3), ('footage', 'closeup_laugh', 40), ('footage', 'rocket', 0),
        ('footage', 'closeup_onair', 70), ('game', None, 3.7), ('footage', 'closeup_serious', 20), ('footage', 'wide', 30)]
COLS = pf(3, 6)
CW = pf(330, 290); CH = CW * 16 / 9; GAP = pf(18, 16)

@ui.cached(64)
def card_img(i):
    kind, name, a = POOL[i % len(POOL)]
    if kind == 'game':
        g = game.frame(a + i * 0.7, 1280, 720)
        x0 = int(1280 * game.ship_x(a) - 720 * 9 / 32)
        src = g[:, max(0, min(1280 - 405, x0)): max(0, min(1280 - 405, x0)) + 405]
        img = cv2.resize(src, (int(CW), int(CH)), interpolation=cv2.INTER_AREA)
    else:
        img = brand.footage(name, a / 30 + i * 0.3, CW, CH)
    L = ui.Layer(int(CW), int(CH), ss=1)
    m = np.zeros(img.shape[:2], np.uint8); cv2.rectangle(m, (0, 0), (img.shape[1], img.shape[0]), 255, -1)
    L.paste(np.dstack([img, m]), 0, 0)
    L.gradient_rrect((0, CH * 0.7, CW, CH), 0, (0, 0, 0), (0, 0, 0), alpha=110)
    L.rrect((16, CH - 26, CW - 16, CH - 20), 3, fill=(255, 255, 255, 90))
    L.rrect((16, CH - 26, 16 + (CW - 32) * (0.2 + 0.6 * core.hash01(i)), CH - 20), 3, fill=(255, 255, 255, 230))
    rgba = L.rgba()
    mk = np.zeros(rgba.shape[:2], np.uint8)
    cv2.rectangle(mk, (0, 0), (rgba.shape[1] - 1, rgba.shape[0] - 1), 255, -1)
    r = 26
    mk[:r, :r] = 0; mk[:r, -r:] = 0; mk[-r:, :r] = 0; mk[-r:, -r:] = 0
    for cx, cy in ((r, r), (rgba.shape[1] - r, r), (r, rgba.shape[0] - r), (rgba.shape[1] - r, rgba.shape[0] - r)):
        cv2.circle(mk, (cx, cy), r, 255, -1, cv2.LINE_AA)
    rgba[..., 3] = np.minimum(rgba[..., 3], mk)
    return rgba

def scroll(t, col):
    """Flick-scrolling: a quick swipe every ~0.55 s (eased), offset per column."""
    s = 0.0
    k0 = int(t / 0.55)
    for k in range(k0 + 1):
        s += eout(clamp((t - k * 0.55 - col * 0.11) / 0.32)) * (CH + GAP)
    return s + t * 60

def wall_layer(t):
    L = np.zeros((H, W, 4), np.uint8)
    x0 = (W - (COLS * CW + (COLS - 1) * GAP)) / 2
    for c in range(COLS):
        off = scroll(t, c) * (1 + 0.15 * (c % 2))
        n0 = int(off // (CH + GAP)) - 1
        for k in range(n0, n0 + int(H / (CH + GAP)) + 3):
            y = k * (CH + GAP) - off + (c % 2) * CH * 0.4
            yy = H - y - CH                                     # scrolling up
            img = card_img((k * COLS + c * 5) % 64)
            x = int(x0 + c * (CW + GAP)); yi = int(yy)
            a, b = max(0, yi), min(H, yi + img.shape[0])
            if b <= a: continue
            sub = img[a - yi:b - yi]
            al = sub[..., 3:4].astype(np.float32) / 255
            reg = L[a:b, x:x + img.shape[1]].astype(np.float32)
            reg[..., :3] = reg[..., :3] * (1 - al) + sub[..., :3] * al
            reg[..., 3:4] = np.maximum(reg[..., 3:4], sub[..., 3:4])
            L[a:b, x:x + img.shape[1]] = reg.astype(np.uint8)
    return L

HOOK = [('DID YOU KNOW?', 'did'), ('YOUR NEXT FOLLOWERS', 'next'), ('ARE SCROLLING', 'scrolling'), ('RIGHT NOW.', 'right')]

# ── S2: stuck at 200 ────────────────────────────────────────────────────────
@ui.cached(8)
def profile_layer(v100, chart100):
    v, cp = v100 / 100, chart100 / 100
    L = ui.Layer(W, H)
    cw_ = pf(W * 0.86, W * 0.5); ch_ = pf(980, 700)
    x0, y0 = (W - cw_) / 2, pf(H * 0.3, H * 0.2)
    ui.surface(L, (x0, y0, x0 + cw_, y0 + ch_), r=36)
    ui.avatar(L, x0 + 100, y0 + 100, 56, 'LT', color=C['violet'])
    L.type((x0 + 180, y0 + 72), 'The Long Table', 46, 'bold')
    L.type((x0 + 180, y0 + 128), '@thelongtable', 32, 'medium', fill=C['fg_muted'])
    wdt = ui.odometer(L, x0 + 60, y0 + 220, v, digits=3, cell=(130, 176), size=140)
    L.type((x0 + 60 + wdt + 36, y0 + 330), 'followers', 46, 'semibold', fill=C['fg_muted'])
    # the growth chart: flat
    gx0, gx1, gy = x0 + 60, x0 + cw_ - 60, y0 + pf(640, 560)
    L.type((gx0, gy - pf(170, 150)), 'This month', 30, 'semibold', fill=C['fg_subtle'])
    L.type((gx1, gy - pf(170, 150)), '+0', 40, 'extrabold', fill=C['danger'], anchor='ra')
    pts = [(gx0 + (gx1 - gx0) * u, gy - 8 * math.sin(u * 17) * (1 - u) - 4) for u in np.linspace(0, cp, 60)]
    if len(pts) > 1:
        L.d.line([(x * L.ss, y * L.ss) for x, y in pts], fill=C['fg_muted'] + (255,), width=int(5 * L.ss), joint='curve')
    L.rrect((gx0, gy + 40, gx1, gy + 42), 1, fill=(255, 255, 255, 30))
    return L.rgba()

def follower_value(t):
    """200, trying to grow and falling back."""
    v = 200.0
    for t0 in (T['two'] + 0.4, T['with'] + 0.45, T['grow'] - 0.1):
        p = prog(t, t0, t0 + 0.55)
        v += 0.62 * math.sin(math.pi * p)
    return v

# ── S4: the link and the clips ──────────────────────────────────────────────
LINK = 'youtube.com/watch?v=LongTable112'
@ui.cached(8)
def panel_layer(n, press100, caret):
    press = press100 / 100
    k = pf(1.3, 1.0)
    L = ui.Layer(W, H)
    pw = pf(W * 0.92, W * 0.62); ph = 520 * k
    x0, y0 = (W - pw) / 2, (H - ph) / 2 - pf(40, 0)
    ui.surface(L, (x0, y0, x0 + pw, y0 + ph), r=32)
    wm = brand.wordmark(); wmh = int(54 * k)
    L.paste(cv2.resize(wm, (int(wm.shape[1] * wmh / wm.shape[0]), wmh), interpolation=cv2.INTER_AREA), x0 + 40, y0 + 38 * k)
    L.type((x0 + 40, y0 + 130 * k), 'Generate clips', int(60 * k), 'extrabold', tracking=-0.02)
    L.type((x0 + 40, y0 + 205 * k), 'Paste a YouTube link or upload a video', int(30 * k), 'medium', fill=C['fg_muted'])
    iy = y0 + 270 * k; ih = 104 * k
    L.rrect((x0 + 36, iy, x0 + pw - 36, iy + ih), 22, fill=C['bg_sunken'] + (255,))
    L.rrect((x0 + 36, iy, x0 + pw - 36, iy + ih), 22, outline=C['accent'] + (200,) if n else (255, 255, 255, 40), width=2 if n else 1)
    L.paste(icon('youtube', 52 * k), x0 + 36 + 22 * k, iy + ih / 2 - 26 * k)
    s = LINK[:n] if n else 'https://youtube.com/…'
    size = ui.fit_size(LINK, pw - 72 - 120 * k, int(34 * k), 'semibold')
    tx = x0 + 36 + 96 * k
    L.type((tx, iy + ih / 2), s, size, 'semibold', fill=C['fg'] if n else C['fg_subtle'], anchor='lm')
    if caret and n < len(LINK):
        cx = tx + brand.font(size, 'semibold').getlength(s) + 4
        L.rrect((cx, iy + ih * 0.28, cx + 4, iy + ih * 0.72), 2, fill=C['lilac'] + (255,))
    by = iy + ih + 46 * k
    ui.button(L, (x0 + 36, by, x0 + pw - 36, by + 100 * k), 'Generate clips', press=press, size=int(40 * k), icon='plus')
    return L.rgba()

def typed_n(t): return int(len(LINK) * clamp(prog(t, T['paste'] + 0.05, T['link'] + 0.2)))

SCORES = [94, 91, 88, 86, 83, 79]
SEGS = [(0.04, 0.12), (0.19, 0.26), (0.33, 0.41), (0.52, 0.60), (0.68, 0.75), (0.84, 0.92)]
CLIP_SRC = ['closeup', 'closeup_onair', 'closeup_laugh', 'closeup_serious', 'closeup', 'closeup_onair']
def strip_geom():
    sx0, sx1 = W * 0.05, W * 0.95
    sy = pf(H * 0.2, H * 0.22); sh = pf(150, 130)
    if P:
        cw_, ch_ = 280, 498
        slots = [(W / 2 + (k % 3 - 1) * (cw_ + 26) - cw_ / 2, H * 0.3 + (k // 3) * (ch_ + 110), cw_, ch_) for k in range(6)]
    else:
        cw_, ch_ = 262, 466
        slots = [(W / 2 + (k - 2.5) * (cw_ + 22) - cw_ / 2, H * 0.4, cw_, ch_) for k in range(6)]
    return sx0, sx1, sy, sh, slots

@ui.cached(8)
def strip_layer(draw100, cut100, rise100, score100):
    dr, cut, rise, sc = draw100 / 100, cut100 / 100, rise100 / 100, score100 / 100
    L = ui.Layer(W, H)
    sx0, sx1, sy, sh, slots = strip_geom()
    if dr <= 0: return L.rgba()
    L.type((sx0, sy - sh / 2 - 70), 'The Long Table · Ep. 112', pf(40, 36), 'bold')
    L.type((sx1, sy - sh / 2 - 70), '1:54:07', pf(36, 32), 'semibold', fill=C['fg_muted'], anchor='ra')
    n = 14; tw = (sx1 - sx0) / n
    xr = sx0 + (sx1 - sx0) * dr
    for i in range(n):
        x = sx0 + i * tw
        if x > xr: break
        u = (i + 0.5) / n
        inseg = any(a <= u <= b for a, b in SEGS)
        img = brand.footage('wide', i * 0.4, tw - 4, sh)
        a_ = 1.0 if not cut or inseg else 1 - 0.7 * cut
        L.paste(img, x + 2, sy - sh / 2, opacity=a_ * (1 - 0.6 * rise))
    L.rrect((sx0, sy - sh / 2, xr, sy + sh / 2), 14, outline=(255, 255, 255, 40), width=1)
    for k, (a, b) in enumerate(SEGS):
        if cut <= 0: break
        p = eout(clamp((cut - k * 0.08) / 0.5))
        L.rrect((sx0 + (sx1 - sx0) * a, sy - sh / 2 - 6, sx0 + (sx1 - sx0) * b, sy + sh / 2 + 6), 12, outline=C['accent'] + (int(255 * p),), width=5)
    for k, (a, b) in enumerate(SEGS):
        p = eback(clamp((rise - k * 0.07) / 0.6))
        if p <= 0: continue
        bx0, by0 = sx0 + (sx1 - sx0) * a, sy - sh / 2
        bw0, bh0 = (sx1 - sx0) * (b - a), sh
        tx, ty, cw_, ch_ = slots[k]
        x = lerp(bx0, tx, min(1, p)); y = lerp(by0, ty, min(1, p)); wv = lerp(bw0, cw_, min(1, p)); hv = lerp(bh0, ch_, min(1, p))
        L.shadow((x, y, x + wv, y + hv), 22, blur=24, opacity=0.6 * min(1, p))
        img = brand.footage(CLIP_SRC[k], k * 0.7, max(4, wv), max(4, hv))
        mk = np.zeros(img.shape[:2], np.uint8); rr = int(min(22, img.shape[1] / 4))
        cv2.rectangle(mk, (rr, 0), (img.shape[1] - rr, img.shape[0]), 255, -1); cv2.rectangle(mk, (0, rr), (img.shape[1], img.shape[0] - rr), 255, -1)
        for cx, cy in ((rr, rr), (img.shape[1] - rr, rr), (rr, img.shape[0] - rr), (img.shape[1] - rr, img.shape[0] - rr)):
            cv2.circle(mk, (cx, cy), rr, 255, -1, cv2.LINE_AA)
        L.paste(np.dstack([img, mk]), x, y)
        q = eback(clamp((sc - k * 0.08) / 0.5))
        if q > 0.05 and p > 0.9:
            ui.score_badge(L, x + wv - 50, y + hv + 52, SCORES[k], r=44 * min(1, q), p=min(1, q))
            L.type((x + 6, y + hv + 52), f'Clip {k + 1}', 30, 'bold', fill=C['fg'], anchor='lm')
    return L.rgba()

# ── S5: captions in real Clipzing styles ────────────────────────────────────
import json  # noqa: E402
CAPJOBS = []
for name in ('ivo', 'juno', 'kai'):
    job = json.load(open(os.path.join(HERE, 'assets', f'cap_{name}.json')))
    d = os.path.join(HERE, 'assets', 'captions', f'cap_{name}')
    CAPJOBS.append((name.capitalize(), job['t0'], job['t0'] + job['duration'], [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith('.png')]))
def phone_geom():
    pw = pf(640, 470); return (W / 2 - pw / 2 + pf(0, 180), pf(H * 0.27, H * 0.08), pw, pw * 2.05)

@ui.cached(8)
def caps_layer(fi, active, chip100):
    L = ui.Layer(W, H)
    px, py, pw, ph = phone_geom()
    scr = brand.footage('closeup_onair', fi / 30, pw * 0.93, ph * 0.955)
    phone, sb = ui.phone(int(pw), int(ph), scr)
    L.paste(phone, px, py)
    # style chips: the real template names, the active one lit
    names = [c[0] for c in CAPJOBS]
    if P: cx0, cy0 = W / 2, H * 0.17
    else: cx0, cy0 = W * 0.28, H * 0.42
    for i, n in enumerate(names):
        on = i == active
        if P: x, y = cx0 + (i - 1) * 280, cy0
        else: x, y = cx0, cy0 + (i - 1) * 130
        ui.pill(L, x, y, n, size=pf(48, 44), fill=C['accent'] if on else C['bg_overlay'], fg=(255, 255, 255) if on else C['fg_muted'], weight='bold', pad=(38, 20))
    L.type((cx0, cy0 - pf(110, 260)), 'Caption style', 34, 'semibold', fill=C['fg_subtle'], anchor='mm')
    return L.rgba(), (px + sb[0], py + sb[1], sb[2] - sb[0], sb[3] - sb[1])

def with_caption(lay, box, t):
    for name, a, b, frames in CAPJOBS:
        if a <= t < b + 0.02:
            i = min(len(frames) - 1, int((t - a) * 60))
            cap = core.load_rgba(frames[i])
            sx0, sy0, sw, shh = box
            cap = cv2.resize(cap, (int(sw), int(shh)), interpolation=cv2.INTER_AREA)
            al = cap[..., 3:4].astype(np.float32) / 255
            y0, x0 = int(sy0), int(sx0)
            out = lay.copy()
            reg = out[y0:y0 + cap.shape[0], x0:x0 + cap.shape[1]].astype(np.float32)
            reg[..., :3] = reg[..., :3] * (1 - al) + cap[..., :3] * al
            out[y0:y0 + cap.shape[0], x0:x0 + cap.shape[1]] = reg.astype(np.uint8)
            return out
    return lay

def active_style(t):
    k = 0
    for i, (_, a, _, _) in enumerate(CAPJOBS):
        if t >= a - 0.05: k = i
    return k

# ── S6: smart reframing (podcast, stream, gameplay) ─────────────────────────
FACECAM = brand.zing('gamer', 0.6)
MODES = [('Podcast', 'podcast'), ('Stream', 'stream'), ('Gameplay', 'gameplay')]
def mode_at(t):
    k = 0
    for i, (_, key) in enumerate(MODES):
        if t >= T[key] - 0.08: k = i
    return k

def source_frame(mode, t, sw, sh):
    """The 16:9 source for a mode, and the 9:16 window(s) in source pixels."""
    if mode == 0:
        f = brand.footage('wide', t, sw, sh)
        ww = sh * 9 / 16; x0 = clamp(sw * 0.33 - ww / 2, 0, sw - ww)
        return f, [(x0, 0, ww, sh)]
    if mode == 1:
        f, (fx, fy, fw, fh) = game.stream(t, int(sw), int(sh), FACECAM)
        gw = sh * 0.6 * 9 / 16 / 0.6 * 0.6
        gx = clamp(sw * game.ship_x(t) - sh * 0.5, 0, sw - sh)
        return f, [(fx, fy, fw, fh), (gx, 0, sh, sh * 0.62)]
    f = game.frame(t, int(sw), int(sh))
    ww = sh * 9 / 16; x0 = clamp(sw * game.ship_x(t) - ww / 2, 0, sw - ww)
    return f, [(x0, 0, ww, sh)]

def output_916(mode, t, ow, oh):
    """What the 9:16 short looks like for a mode: the crop, or the stream's stacked layout."""
    sw, sh = 1280, 720
    f, wins = source_frame(mode, t, sw, sh)
    if mode == 1:
        (fx, fy, fw, fh), (gx, gy, gw, gh) = wins
        top = cv2.resize(f[int(fy):int(fy + fh), int(fx):int(fx + fw)], (int(ow), int(oh * 0.4)), interpolation=cv2.INTER_AREA)
        g = game.frame(t, sw, sh)
        gx = int(clamp(sw * game.ship_x(t) - (oh * 0.6) * 0.0 - sh * 0.5, 0, sw - sh))
        bot = cv2.resize(g[:, gx:gx + sh], (int(ow), int(oh) - int(oh * 0.4)), interpolation=cv2.INTER_AREA)
        return np.vstack([top, bot])
    x0, y0, ww, hh = wins[0]
    return cv2.resize(f[int(y0):int(y0 + hh), int(x0):int(x0 + ww)], (int(ow), int(oh)), interpolation=cv2.INTER_AREA)

@ui.cached(8)
def ref_layer(fi, mode, out100):
    t = fi / 30
    outp = out100 / 100
    L = ui.Layer(W, H)
    sw = pf(W * 0.9, W * 0.5); sh = sw * 9 / 16
    sx, sy = (W - sw) / 2 if P else W * 0.05, pf(H * 0.15, H * 0.2)
    f, wins = source_frame(mode, t, 1280, 720)
    k = sw / 1280
    img = cv2.resize(f, (int(sw), int(sh)), interpolation=cv2.INTER_AREA)
    dim = (img.astype(np.float32) * 0.35).astype(np.uint8)
    for (x0, y0, ww, hh) in wins:
        a, b = int(x0 * k), int((x0 + ww) * k); c, d = int(y0 * k), int((y0 + hh) * k)
        dim[c:d, a:b] = img[c:d, a:b]
    L.shadow((sx, sy, sx + sw, sy + sh), 20, blur=30, opacity=0.6)
    L.paste(dim, sx, sy)
    for (x0, y0, ww, hh) in wins:
        L.rrect((sx + x0 * k, sy + y0 * k, sx + (x0 + ww) * k, sy + (y0 + hh) * k), 10, outline=C['accent'] + (255,), width=4)
    # the mode pills
    for i, (label, _) in enumerate(MODES):
        on = i == mode
        ui.pill(L, sx + sw / 2 + (i - 1) * pf(300, 250), sy - 70, label, size=pf(40, 34), fill=C['accent'] if on else C['bg_overlay'],
                fg=(255, 255, 255) if on else C['fg_muted'], weight='bold', pad=(30, 14))
    # the three 9:16 results
    if outp > 0:
        ow = pf(280, 230); oh = ow * 16 / 9
        for i in range(3):
            p = eback(clamp((outp - i * 0.12) / 0.6))
            if p <= 0: continue
            if P: ox, oy = W / 2 + (i - 1) * (ow + 40) - ow / 2, H * 0.55
            else: ox, oy = W * 0.565 + i * (ow + 34), H * 0.25
            ph_, _ = ui.phone(int(ow + 20), int(oh + 20), output_916(i, t, ow, oh), radius=36, bezel=10, notch=False)
            L.paste(ph_, ox, oy + (1 - min(1, p)) * 80, opacity=min(1, p))
            L.type((ox + (ow + 20) / 2, oy + oh + 60), MODES[i][0], 32, 'bold', fill=C['fg_muted'], anchor='mm')
    return L.rgba()

# ── S7: B-roll ──────────────────────────────────────────────────────────────
@ui.cached(8)
def broll_layer(fi, p100):
    t, p = fi / 30, p100 / 100
    L = ui.Layer(W, H)
    pw = pf(560, 420); ph = pw * 2.05
    px, py = W / 2 - pw / 2, pf(H * 0.17, H * 0.06)
    sw_, sh_ = int(pw * 0.93), int(ph * 0.955)
    base = brand.footage('closeup_serious', t, sw_, sh_)
    cut = brand.footage('coffee', t, sw_, sh_)
    xw = int(sw_ * eout(p))
    scr = base.copy()
    if xw > 0: scr[:, sw_ - xw:] = cut[:, sw_ - xw:]
    phone, sb = ui.phone(int(pw), int(ph), scr)
    L.paste(phone, px, py)
    if p > 0.3: ui.pill(L, px + pw / 2, py + ph * 0.12, 'B-roll', size=36, fill=C['accent'], fg=(255, 255, 255), weight='bold')
    # the timeline under the phone (side in 16:9)
    tx0, tx1 = (W * 0.1, W * 0.9) if P else (W * 0.66, W * 0.95)
    ty = py + ph + 60 if P else H * 0.42
    L.type((tx0, ty - 40), 'Timeline', 30, 'semibold', fill=C['fg_subtle'])
    for j, (lab, col) in enumerate((('A-roll', (70, 72, 98)), ('B-roll', C['accent']))):
        yy = ty + j * 70
        L.type((tx0, yy + 22), lab, 28, 'semibold', fill=C['fg_muted'], anchor='lm')
        bx0 = tx0 + 130
        L.rrect((bx0, yy, tx1, yy + 44), 10, fill=(40, 42, 58, 255))
        if j == 0: L.rrect((bx0, yy, tx1, yy + 44), 10, fill=col + (255,))
        elif p > 0: L.rrect((bx0 + (tx1 - bx0) * 0.45, yy, bx0 + (tx1 - bx0) * (0.45 + 0.3 * eout(p)), yy + 44), 10, fill=col + (255,))
    return L.rgba()

# ── S8: a week of shorts ────────────────────────────────────────────────────
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
PLAN = [('youtubeshorts', '6 pm'), ('tiktok', 'Draft'), ('youtubeshorts', '6 pm'), ('instagram', 'Reels'), ('youtubeshorts', '6 pm'),
        ('tiktok', 'Draft'), ('youtubeshorts', '6 pm')]
@ui.cached(8)
def sched_layer(fill100, streak100, legend100):
    fill, streak, legend = fill100 / 100, streak100 / 100, legend100 / 100
    L = ui.Layer(W, H)
    cw_ = pf(W * 0.94, W * 0.86); x0 = (W - cw_) / 2; y0 = pf(225, H * 0.06)
    ncol = pf(4, 7); colw = cw_ / ncol; cellh = pf(400, 380); rows = pf(2, 1)
    card_h = 160 + rows * cellh + pf(40, 50)
    ui.surface(L, (x0, y0, x0 + cw_, y0 + card_h + 110), r=32)
    L.type((x0 + 36, y0 + 34), 'Calendar · next week', pf(40, 36), 'bold')
    for i, dname in enumerate(DAYS):
        col, row = i % ncol, i // ncol
        cx = x0 + col * colw + (colw / 2 if P and row == 1 else 0)
        rowy = y0 + row * cellh
        L.type((cx + colw / 2, rowy + 120), dname, pf(32, 30), 'semibold', fill=C['fg_muted'], anchor='mm')
        cy = rowy + 150
        L.rrect((cx + 8, cy, cx + colw - 8, cy + cellh - 30), 18, fill=C['bg_overlay'] + (255,))
        p = eback(clamp((fill - i * 0.11) / 0.35))
        if p > 0:
            th_w = colw - 26; th_h = th_w * 16 / 9
            th_h = min(th_h, cellh - pf(170, 130))
            img = brand.footage(CLIP_SRC[i % 6], i * 0.5, th_w, th_h)
            L.paste(img, cx + 13, cy + 10 - (1 - min(1, p)) * 60, opacity=min(1, p))
            ic, lab = PLAN[i]
            s = pf(58, 44)
            L.paste(icon(ic, s), cx + colw / 2 - s / 2, cy + th_h + 22, opacity=min(1, p))
            L.type((cx + colw / 2, cy + th_h + 22 + s + 28), lab, pf(30, 24), 'semibold', fill=C['fg'], anchor='mm')
        # the streak row: never miss a day
        q = eback(clamp((streak - i * 0.1) / 0.3))
        sx_ = x0 + (i + 0.5) * cw_ / 7; sy = y0 + card_h + 50
        L.d.ellipse(L.S(sx_ - 28, sy - 28, sx_ + 28, sy + 28), fill=(C['success'] if q > 0.5 else (50, 52, 70)) + (255,))
        if q > 0.5: ui.glyph(L, 'check', sx_, sy + 1, 38, (255, 255, 255))
    # the legend: the official marks, each with what Clipzing really does there
    if legend > 0:
        items = [('youtubeshorts', 'YouTube Shorts', 'Scheduled & published'), ('tiktok', 'TikTok', 'Sent to your drafts'), ('instagram', 'Instagram', 'Reels-ready export')]
        ly = y0 + card_h + pf(130, 150)
        for i, (ic, name, what) in enumerate(items):
            p = eout(clamp((legend - i * 0.15) / 0.5))
            if P:   # three columns: the official mark over one honest line (clear of TikTok's caption zone)
                lx = 70 + (i + 0.5) * 830 / 3          # x 70–900: clear of the right rail
                L.paste(icon(ic, 80), lx - 40, ly, opacity=p)
                L.type((lx, ly + 106), ('Shorts · published', 'TikTok · to drafts', 'Reels · export')[i], 28, 'bold', fill=C['fg'] + (int(255 * p),), anchor='mm')
            else:
                lx, lyy = x0 + 30 + i * cw_ / 3, ly
                L.paste(icon(ic, 84), lx, lyy, opacity=p)
                L.type((lx + 108, lyy + 24), name, 34, 'bold', fill=C['fg'] + (int(255 * p),))
                L.type((lx + 108, lyy + 66), what, 28, 'medium', fill=C['fg_muted'] + (int(255 * p),))
    return L.rgba()

# ── the camera ──────────────────────────────────────────────────────────────
ORDER = [('profile', PROF), ('panel', PANEL), ('strip', STRIP), ('caps', CAPS), ('ref', REF), ('broll', BROLL), ('sched', SCHED)]
def camera_at(t):
    pose = pose_mix(WALL.home(D * 0.85, 0, 120), WALL.home(D * 1.0), einout(prog(t, 0, T['stuck'] - 0.5)))
    for i, (k, pl) in enumerate(ORDER):
        a, d, _ = WH[k]
        pose = pose_mix(pose, pl.home(D * 1.03), einout(prog(t, a, a + d)))
        nxt = WH[ORDER[i + 1][0]][0] if i + 1 < len(ORDER) else WH['end'][0]
        pose = pose_mix(pose, pl.home(D * 0.96), prog(t, a + d, nxt) * 0.8)
    pose = pose_mix(pose, SCHED.home(D * 1.7), ein(prog(t, WH['end'][0], T['land'])))
    roll = sum(r * math.sin(math.pi * prog(t, a, a + d)) for a, d, r in WH.values())
    sh = [shake_at(t, T[k], amp) for k, amp in (('did', 14), ('stuck', 16), ('i', 26), ('land', 20))]
    return Camera(pose[0], pose[1], roll=roll, shake=(sum(s[0] for s in sh), sum(s[1] for s in sh)))

def super_slam(frame, t, at, text, x, y, size, until, **kw):
    if t < at - 0.2 or t > until + 0.18: return
    out = prog(t, until, until + 0.16)
    if out > 0:
        img = fx.type_rgba(text, size, **kw)
        composite_sprite(frame, img, x, y - 120 * ein(out), img.shape[0], opacity=1 - out, blur=6 * out); return
    fx.word_slam(frame, t, at - 1 / 60, text, x, y, size, **kw)

def scrim(frame, y, h, a=0.55):
    """A soft dark band behind type over busy footage (readability)."""
    k = core.SCALE
    y0, y1 = int((y - h / 2) * k), int((y + h / 2) * k)
    band = np.zeros(frame.shape[0], np.float32)
    yy = np.arange(frame.shape[0])
    band = np.clip(1 - np.abs(yy - (y0 + y1) / 2) / max(1, (y1 - y0) / 2), 0, 1) ** 0.6 * a
    frame *= (1 - band[:, None, None])

# ── the scene ───────────────────────────────────────────────────────────────
ZING_H = H * pf(0.3, 0.46)
ZC = (W / 2, H * pf(0.47, 0.45))

def scene(t):
    frame = new_frame()
    stage(frame, base=brand.STAGE_BASE, glows=(((0.5, 0.4 + 0.05 * math.sin(t * 0.4)), LINE, 0.11, 0.65), ((0.12, 0.9), C['zing_hem'], 0.06, 0.5)), t=t)
    cam = camera_at(t); foc = FOCUS(cam)
    fi = int(t * 30)
    # S1
    if t < WH['profile'][0] + 0.5:
        composite_plane(frame, cam, WALL, wall_layer(t), focus=foc, opacity=1 - 0.5 * prog(t, T['right'] + 0.4, WH['profile'][0]))
        hy = pf(H * 0.47, H * 0.5)
        if t > T['did'] - 0.25: scrim(frame, hy, pf(330, 300), 0.6 * (1 - prog(t, WH['profile'][0], WH['profile'][0] + 0.3)))
        scrim(frame, pf(262, 68), pf(170, 130), 0.55 * prog(t, 0.2, 0.5) * (1 - prog(t, WH['profile'][0], WH['profile'][0] + 0.25)))   # behind the lock-up
        for i, (txt, k) in enumerate(HOOK):
            until = T[HOOK[i + 1][1]] - 0.42 if i + 1 < len(HOOK) else WH['profile'][0]   # gone before the next word starts its rush
            super_slam(frame, t, T[k], txt, W / 2, hy, ui.fit_size(txt, W * 0.88, pf(130, 150), 'extrabold'), until)
    # S2 + S3
    if WH['profile'][0] - 0.3 < t < WH['panel'][0] + 0.5:
        swipe = ein(prog(t, T['dont'] - 0.1, T['dont'] + 0.35))
        lay = profile_layer(int(follower_value(t) * 100), int(100 * eout(prog(t, T['stuck'], T['grow']))))
        if swipe > 0:
            lay = np.roll(lay, int(-swipe * H), axis=0); lay[int(H * (1 - swipe)):] = 0
        composite_plane(frame, cam, PROF, lay, focus=foc)
        super_slam(frame, t, T['stuck'], 'Stuck at 200?', W / 2, pf(H * 0.17, H * 0.1), pf(110, 96), T['dont'] - 0.1)
        super_slam(frame, t, T['dont'], "Don't worry.", W / 2, pf(H * 0.24, H * 0.2), pf(110, 110), T['i'] - 0.1, fill=C['lilac'])
        if t > T['i'] - 0.25:   # Zing slams in: "I got you."
            k = t - T['i']
            if k < 0:
                p = prog(t, T['i'] - 0.25, T['i'])
                composite_sprite(frame, brand.zing('slam', 0), ZC[0], ZC[1], ZING_H * 1.6 * (0.15 + 0.85 * ein(p)), blur=(1 - p) * 12)
            else:
                sq = math.exp(-k * 9) * math.cos(k * 34) * 0.22
                pose = 'slam' if k < 0.18 else 'wink'
                bx = brand.zing_box(pose)
                composite_sprite(frame, brand.zing(pose, k), ZC[0], ZC[1] + ZING_H / 2, ZING_H / (bx[3] - bx[1]), sx=1 + sq, sy=1 - sq, anchor=(0.5, bx[3]),
                                 opacity=1 - prog(t, WH['panel'][0], WH['panel'][0] + 0.25))
                fx.shards(frame, t, T['i'], ZC[0], ZC[1], n=24, size=12)
    # S4
    if WH['panel'][0] - 0.3 < t < WH['strip'][0] + 0.55:
        press = clamp(1 - abs(t - T['press'] - 0.06) / 0.12)
        composite_plane(frame, cam, PANEL, panel_layer(typed_n(t), int(press * 100), int(t * 3) % 2 == 0), focus=foc)
    if WH['strip'][0] - 0.3 < t < WH['caps'][0] + 0.55:
        composite_plane(frame, cam, STRIP, strip_layer(int(100 * prog(t, WH['strip'][0] + 0.2, T['long'] + 0.7)), int(100 * prog(t, T['short2'] - 0.25, T['short2'] + 0.35)),
                                                    int(100 * prog(t, T['short2'] + 0.2, T['clips'] + 0.75)), int(100 * prog(t, T['best'] - 0.05, T['best'] + 0.6))), focus=foc)
    # S5
    if WH['caps'][0] - 0.3 < t < WH['ref'][0] + 0.55:
        lay, box = caps_layer(fi % 300, active_style(t), 0)
        composite_plane(frame, cam, CAPS, with_caption(lay, box, t), focus=foc)
    # S6
    if WH['ref'][0] - 0.3 < t < WH['broll'][0] + 0.55:
        composite_plane(frame, cam, REF, ref_layer(fi, mode_at(t), int(100 * prog(t, T['keeps'] - 0.1, T['frame'] + 0.2))), focus=foc)
    # S7
    if WH['broll'][0] - 0.3 < t < WH['sched'][0] + 0.55:
        composite_plane(frame, cam, BROLL, broll_layer(fi % 300, int(100 * prog(t, T['broll'] - 0.05, T['broll'] + 0.45))), focus=foc)
    # S8
    if WH['sched'][0] - 0.3 < t < T['land'] + 0.2:
        lay = sched_layer(int(100 * prog(t, T['schedule'] - 0.1, WORDS.end('week') + 0.2)), int(100 * prog(t, T['never'] - 0.05, WORDS.end('day') + 0.1)),
                          int(100 * prog(t, WORDS.end('day') - 0.1, T['clipzing2'] - 0.45)))
        composite_plane(frame, cam, SCHED, lay, focus=foc, opacity=1 - prog(t, WH['end'][0], T['land'] - 0.05))
    # S9: Zing lands on "Clipzing"
    if t >= T['land'] - 0.35:
        p = prog(t, T['land'] - 0.35, T['land'])
        k = max(0.0, t - T['land'])
        sq = math.exp(-k * 8) * math.cos(k * 30) * 0.22 if t >= T['land'] else -0.12
        pose = 'land' if k < 0.55 else 'cheer'
        bx = brand.zing_box(pose)
        zh = H * pf(0.22, 0.32); zc = (W / 2, H * pf(0.31, 0.27))
        y = lerp(-H * 0.25, zc[1], ein(p))
        if t >= T['land'] - 0.1:
            s = core.SCALE; shm = np.zeros(frame.shape[:2], np.float32)
            cv2.ellipse(shm, (int(zc[0] * s), int((zc[1] + zh / 2 + 8) * s)), (max(1, int(zh * 0.42 * s)), max(1, int(zh * 0.06 * s))), 0, 0, 360, 0.5, -1, cv2.LINE_AA)
            frame *= (1 - cv2.GaussianBlur(shm, (0, 0), max(1.0, 10 * s))[..., None])
        composite_sprite(frame, brand.zing(pose, k), zc[0], y + zh / 2, zh / (bx[3] - bx[1]), sx=1 + sq, sy=1 - sq, anchor=(0.5, bx[3]))
        for i, (txt, key) in enumerate((('Long videos in.', 'long2'), ('Shorts out.', 'shorts'))):
            if t > T[key] - 0.2:
                yy = zc[1] + zh / 2 + pf(250, 200) + i * pf(110, 96) - eout(prog(t, T['endcard'], T['endcard'] + 0.5)) * 40
                if t < T[key] + 0.3: fx.word_slam(frame, t, T[key] - 1 / 60, txt, W / 2, yy, pf(96, 92), fill=C['lilac'] if i else C['fg'])
                else:
                    img = fx.type_rgba(txt, pf(96, 92), fill=C['lilac'] if i else C['fg'])
                    composite_sprite(frame, img, W / 2, yy, img.shape[0])
    return frame, []

def probe(t):
    out = []
    if abs(t - T['i']) < 0.3: out.append((ZC[0], ZC[1] + (1 - prog(t, T['i'] - 0.25, T['i'])) * 300))
    if T['land'] - 0.4 < t < T['land'] + 0.3: out.append((W / 2, H * 0.4 - (1 - prog(t, T['land'] - 0.35, T['land'])) * 800))
    return out or [(0, 0)]

WM = brand.wordmark(); WMT = brand.wordmark_text()
def overlay(frame, t):
    a = prog(t, 0.3, 0.55) * (1 - prog(t, WH['profile'][0], WH['profile'][0] + 0.25))   # the brand inside the first second
    if a > 0:
        h = pf(64, 56)
        wmi = cv2.resize(WM, (int(WM.shape[1] * h / WM.shape[0]), h), interpolation=cv2.INTER_AREA)
        core.after_grade(frame, wmi, W / 2 - wmi.shape[1] / 2, pf(230, 40), opacity=a)
    if T['got'] + 0.2 < t < WH['panel'][0] + 0.2:       # "I got you." — the wordmark under Zing
        h = pf(110, 120)
        img = cv2.resize(WMT, (int(WMT.shape[1] * h / WMT.shape[0]), h), interpolation=cv2.INTER_AREA)
        core.after_grade(frame, img, W / 2 - img.shape[1] / 2, ZC[1] + ZING_H / 2 + 50,
                         opacity=prog(t, T['got'] + 0.2, T['got'] + 0.5) * (1 - prog(t, WH['panel'][0] - 0.1, WH['panel'][0] + 0.2)))
    if t >= T['land'] + 0.12:
        p = eout(prog(t, T['land'] + 0.12, T['land'] + 0.5)); up = eout(prog(t, T['endcard'], T['endcard'] + 0.5)) * 40
        zh = H * pf(0.22, 0.32); zy = H * pf(0.31, 0.27)
        h = pf(120, 104)
        img = cv2.resize(WMT, (int(WMT.shape[1] * h / WMT.shape[0]), h), interpolation=cv2.INTER_AREA)
        y = zy + zh / 2 + 60 - up
        core.after_grade(frame, img, W / 2 - img.shape[1] / 2, y, opacity=p)
        if t >= T['endcard']:
            L = ui.Layer(W, 100, ss=1)
            L.type((W / 2, 50), 'clipzing.com', 52, 'semibold', fill=C['lilac'], anchor='mm')
            core.after_grade(frame, L.rgba(), 0, y + pf(400, 340), opacity=prog(t, T['endcard'] + 0.15, T['endcard'] + 0.5))

# ── sound ───────────────────────────────────────────────────────────────────
def cues():
    c = Cues()
    for i in range(int(T['right'] / 0.55) + 2):                 # a swipe per flick of the feed
        c.add(i * 0.55, 'whoosh', x=((i % 3) - 1) * 0.5, size=0.25)
    for txt, k in HOOK: c.add(T[k] - 0.2, 'suck', size=0.3).add(T[k] - 1 / 60, 'impact', size=0.55)
    c.add(WH['profile'][0], 'whoosh_down', size=0.8).add(T['stuck'] - 1 / 60, 'impact', size=0.6)
    for t0 in (T['two'] + 0.4, T['with'] + 0.45, T['grow'] - 0.1):
        c.add(t0 + 0.05, 'tick', size=0.5).add(t0 + 0.4, 'tick', size=0.3)
    c.add(T['dont'] - 0.05, 'whoosh', size=0.6).add(T['dont'], 'impact', size=0.45)
    c.add(T['i'] - 0.25, 'suck', size=0.6).add(T['i'] - 1 / 60, 'impact', size=1.0).add(T['i'], 'glass', size=0.7).add(T['got'] + 0.1, 'pop', size=0.5)
    c.add(WH['panel'][0], 'whoosh', size=0.8)
    n = len(LINK); a, b = T['paste'] + 0.05, T['link'] + 0.2
    for i in range(0, n, 2): c.add(a + (b - a) * i / n, 'key', size=0.45)
    c.add(T['press'], 'click', size=0.9).add(T['press'] + 0.01, 'thump', size=0.35)
    c.add(WH['strip'][0], 'whoosh_down', size=0.8).add(WH['strip'][0] + 0.25, 'zip', size=0.7)
    for k in range(6):
        c.add(T['short2'] - 0.2 + k * 0.05, 'crack', x=-0.7 + 0.28 * k, size=0.3)
        c.add(T['short2'] + 0.25 + k * 0.05, 'pop', x=-0.7 + 0.28 * k, size=0.5)
        c.add(T['best'] + k * 0.05, 'tick', x=-0.7 + 0.28 * k, size=0.3)
    c.add(T['best'] + 0.4, 'shimmer', size=0.5)
    c.add(WH['caps'][0], 'whoosh', x=0.4, size=0.8)
    for _, a_, _, _ in CAPJOBS: c.add(a_ - 0.02, 'tap', size=0.6).add(a_, 'pop', size=0.4)
    c.add(WH['ref'][0], 'whoosh_down', x=-0.4, size=0.8)
    for _, key in MODES: c.add(T[key] - 0.05, 'click', size=0.6).add(T[key], 'zip', size=0.35)
    for i in range(3): c.add(T['keeps'] + i * 0.12, 'pop', x=-0.5 + 0.5 * i, size=0.5)
    c.add(T['frame'], 'lock', size=0.5)
    c.add(WH['broll'][0], 'whoosh', size=0.7).add(T['broll'] - 0.02, 'zip', x=0.5, size=0.6).add(T['broll'] + 0.4, 'thump', size=0.3)
    c.add(WH['sched'][0], 'whoosh_down', size=0.8)
    for i in range(7): c.add(T['schedule'] - 0.1 + i * 0.12, 'pop', x=-0.8 + 0.27 * i, size=0.45)
    for i in range(7): c.add(T['never'] - 0.05 + i * 0.1, 'tick', x=-0.8 + 0.27 * i, size=0.4)
    c.add(WORDS.end('day'), 'shimmer', size=0.6)
    c.add(WH['end'][0], 'whoosh_down', size=0.5).add(T['land'] - 0.33, 'falling', size=0.6).add(T['land'], 'thump', size=1.0)
    c.add(T['long2'] - 0.18, 'suck', size=0.3).add(T['long2'] - 1 / 60, 'impact', size=0.45)
    c.add(T['shorts'] - 0.18, 'suck', size=0.3).add(T['shorts'] - 1 / 60, 'impact', size=0.5)
    c.add(T['endcard'], 'whoosh', size=0.3)
    return c

def hero_cues():
    return [('clip_ready', WORDS.after('moments', gap=0.15)), ('clip_ready', WORDS.after('day', gap=0.2)), ('logo_hit', T['land']),
            ('logo_chord', WORDS.end('clipzing', 2) + 0.04), ('published', WORDS.end('out') + 0.25)]

MUSIC = dict(style='mallet_pop', drop=T['paste'], lift=T['podcast'], breath=WH['end'][0], hit=T['land'], sting=False)
