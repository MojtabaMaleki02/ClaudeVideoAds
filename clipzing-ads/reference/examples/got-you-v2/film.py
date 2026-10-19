"""Got You v2: a Clipzing promo in the brand's physical language, built with the clipzing-ads skill (adkit).

"Stuck at two hundred followers? I got you. Drop in one long video, and Clipzing slices it into shorts, best moments
first. Captions that hit every single word. The speaker, always in frame. Podcast, stream, or gameplay. B-roll,
exactly where it fits. Then your whole week, lined up. Never miss a day. Clipzing. Long videos in. Shorts out."

Chunky, glossy, EXTRUDED objects in a dark world (core.composite_extruded), one continuous camera, and the purple
line of light threading every station: a jammed follower counter → Zing → a long video slab dropped and sliced
into shorts → each word in a different real caption style → a viewfinder that locks onto the speaker (podcast,
stream, gameplay) → a B-roll card that drops in on the matching word → a desk calendar for the whole week with
Clipzing's streak → Zing lands, "Long videos in. Shorts out."
"""
import json
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
from adkit.core import (D, H, PORTRAIT, W, Camera, Plane, clamp, composite_extruded, composite_plane,  # noqa: E402
                        composite_sprite, draw_line, eback, ein, einout, eout, lerp, new_frame, pose_mix, prog,
                        shake_at, stage, v3)
from adkit.timeline import Cues, Words                                    # noqa: E402
import game                                                                # noqa: E402
import objects as O                                                        # noqa: E402

END = 21.0
VO_OFF = 0.0
WORDS = Words(os.path.join(HERE, 'voice', 'words.json'), VO_OFF)
P = PORTRAIT
def pf(a, b): return a if P else b
def w_(word, n=1): return WORDS.t(word, n)

T = {k: (w_(*v) if isinstance(v, tuple) else w_(v)) for k, v in {
    'stuck': 'stuck', 'followers': 'followers', 'i': 'i', 'got': 'got', 'you': 'you', 'drop': 'drop', 'long': ('long', 1),
    'clipzing1': ('clipzing', 1), 'slices': 'slices', 'shorts': ('shorts', 1), 'best': 'best', 'first': 'first',
    'captions': 'captions', 'word': 'word', 'speaker': 'speaker', 'always': 'always', 'frame': 'frame',
    'podcast': 'podcast', 'stream': 'stream', 'gameplay': 'gameplay', 'broll': 'b-roll', 'exactly': 'exactly', 'fits': 'fits',
    'then': 'then', 'whole': 'whole', 'week': 'week', 'never': 'never', 'day': 'day', 'clipzing2': ('clipzing', 2),
    'long2': ('long', 2), 'shorts2': ('shorts', 2)}.items()}
T['land'] = T['clipzing2'] - 0.02
T['endcard'] = 19.2
SIDE = (70, 26, 160)          # the brand's deep-violet lip (extrusion side)

# ── world: stations along one flight ────────────────────────────────────────
CNT = Plane(v3(0, 0, 0), yaw=-24, pitch=-12, size=(920, 560))            # S1 the follower counter
SLAB_W, SLAB_H = pf(980, 1180), pf(980, 1180) * 9 / 16
SLAB_C = v3(2300, -150, -2800)
SLAB_YAW = 20
CAP = v3(2300, -150, -4300)                                              # S3 the captions (inside the best card)
FRM = Plane(v3(-2200, 250, -6200), yaw=-22, pitch=-6, size=(pf(980, 1180), pf(980, 1180) * 9 / 16))   # S4 viewfinder monitor
BRL_C = v3(1900, -250, -8600)                                            # S5 B-roll cards
CAL = Plane(v3(-1700, -100, -11000), yaw=20, pitch=-14, size=(pf(940, 1500), pf(1180, 820)))           # S6 calendar

def off_axis(center, yaw_cam, pitch_cam, dist, look=v3(0, 0, 0)):
    """A camera pose looking at `center` from a direction rotated (yaw_cam, pitch_cam) off +z: objects show their depth."""
    y, p = math.radians(yaw_cam), math.radians(pitch_cam)
    d = v3(math.sin(y) * math.cos(p), math.sin(p), math.cos(y) * math.cos(p))
    tgt = center + look
    return tgt + d * dist, tgt

# ── S1: the jammed counter ──────────────────────────────────────────────────
CELL_X0 = (920 - 3 * 230 - 2 * 34) / 2
def counter_roll(t):
    """The last digit tries to roll to 201 and jams back, three times."""
    r = 0.0
    for t0 in (T['stuck'] + 0.1, T['followers'] - 0.25, T['followers'] + 0.25):
        r = max(r, 0.42 * math.sin(math.pi * clamp(prog(t, t0, t0 + 0.32))))
    return r
def jam_shake(t):
    s = 0.0
    for t0 in (T['stuck'] + 0.1, T['followers'] - 0.25, T['followers'] + 0.25):
        k = t - (t0 + 0.2)
        if 0 < k < 0.3: s += math.sin(k * 80) * 10 * (1 - k / 0.3)
    return s

def draw_counter(frame, cam, t, foc, opacity=1.0):
    sh = jam_shake(t)
    pl = Plane(CNT.c + CNT.r * sh, yaw=-24, pitch=-12, size=CNT.size if hasattr(CNT, 'size') else (920, 560))
    contact(frame, cam, pl, 0.6 * opacity)
    composite_extruded(frame, cam, pl, O.counter_plate(), depth=150, steps=14, side=SIDE, focus=foc, opacity=opacity)
    for i, dd in enumerate((2, 0, 0)):
        roll = counter_roll(t) if i == 2 else 0.0
        dp = Plane(pl.world(CELL_X0 + i * 264 + 115, 220) + pl.n * 26, yaw=-24, pitch=-12, size=(230, 300))
        composite_extruded(frame, cam, dp, O.digit(dd, int(roll * 100)), depth=34, steps=8, side=(150, 120, 230), focus=foc, opacity=opacity)
CNT.size = (920, 560)

# ── S2: the slab (one long video), dropped and sliced into shorts ───────────
def slab_plane(t):
    drop = eback(prog(t, T['drop'] - 0.05, T['drop'] + 0.42), 1.2)
    y = lerp(1700, 0, drop)
    return Plane(SLAB_C + v3(0, y, 0), yaw=SLAB_YAW, pitch=-6, size=(SLAB_W, SLAB_H))
NSL = 5
CUT_T = [T['slices'] + 0.02 + k * 0.1 for k in range(NSL - 1)]
SPLIT = (T['shorts'] - 0.05, T['shorts'] + 0.5)
SCORES = [86, 91, 79, 94, 83]                     # per slice, left → right in the long video
MOM = ['closeup_onair', 'closeup_laugh', 'closeup_serious', 'closeup', 'closeup_onair']
CARD_H = SLAB_H * pf(1.6, 1.05)
CARD_W = CARD_H * 9 / 16
RANK = sorted(range(NSL), key=lambda k: -SCORES[k])            # best first
def fan_slot(k, best):
    """Where card k sits in the fan; after 'best moments first' the best is centre-front."""
    order = RANK if best > 0.5 else list(range(NSL))
    pos = [2, 1, 3, 0, 4][order.index(k)] if best > 0.5 else k     # best → slot 2 (centre)
    dx = (pos - 2)
    return v3(dx * (CARD_W * pf(0.56, 0.8)), -abs(dx) * 40, -abs(dx) * 150), -dx * 12

@ui.cached(12)
def slab_face(fi, cuts100):
    face = O.framed(brand.footage('wide', fi / 30, SLAB_W, SLAB_H), SLAB_W, SLAB_H, bezel=24, r=44)
    return face

@ui.cached(16)
def card_face(k, fi, morph100):
    """Slice k of the long video turning into its own vertical short."""
    m = morph100 / 100
    wv = lerp(SLAB_W / NSL, CARD_W, eout(m)); hv = lerp(SLAB_H, CARD_H, eout(m))
    src = brand.footage('wide', fi / 30, SLAB_W, SLAB_H)
    sl = src[:, int(k * SLAB_W / NSL): int((k + 1) * SLAB_W / NSL)]
    a = cv2.resize(sl, (int(wv), int(hv)), interpolation=cv2.INTER_AREA)
    b = brand.footage(MOM[k], fi / 30 + k * 0.6, wv, hv)
    pic = (a.astype(np.float32) * (1 - clamp(m * 1.6 - 0.3)) + b.astype(np.float32) * clamp(m * 1.6 - 0.3)).astype(np.uint8)
    return O.framed(pic, wv + 24, hv + 24, bezel=12, r=int(lerp(10, 34, m)))

def card_plane(k, t, fi):
    sp = einout(prog(t, *SPLIT))
    best = eout(prog(t, T['best'] - 0.05, T['best'] + 0.4))
    sl = slab_plane(t)
    start = sl.world((k + 0.5) * SLAB_W / NSL, SLAB_H / 2)
    off0, yaw0 = fan_slot(k, 0)
    off1, yaw1 = fan_slot(k, 1)
    off = off0 + (off1 - off0) * best
    yaw = yaw0 + (yaw1 - yaw0) * best
    cs = cap_spread(t)
    if cs > 0:
        slot = slot_of(k, 1); dx = slot - 2
        if P:    # 9:16: the centre card comes forward, big; the others step back
            off = off + (v3(0, 0, 330 if dx == 0 else -260) + v3(dx * 120, 0, 0)) * cs
            yaw = yaw + (cap_flip(t) if dx == 0 else 0) * cs
        else:    # 16:9: the three front cards spread side by side, nearly square to the camera
            tgt = v3(dx * CARD_W * 1.12, 0, -abs(dx) * 30)
            off = off + (tgt - off) * cs; yaw = yaw + (-dx * 6 - yaw) * cs
    lift = v3(0, 0, 160) if (best > 0.5 and k == RANK[0]) else v3(0, 0, 0)
    c = start + (SLAB_C + off + lift * best - start) * sp
    face = card_face(k, fi % 300, int(100 * sp))
    return Plane(c, yaw=SLAB_YAW * (1 - sp) + yaw * sp, pitch=-6 * (1 - sp), size=(face.shape[1], face.shape[0])), face

def best_card(t, fi):
    return card_plane(RANK[0], t, fi)

# ── S3: captions, one real style per word ───────────────────────────────────
CAPL = {}
for st in ('ivo', 'juno', 'kai'):
    job = json.load(open(os.path.join(HERE, 'assets', f'capline_{st}.json')))
    d = os.path.join(HERE, 'assets', 'captions', f'capline_{st}')
    CAPL[st] = (job['t0'], [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith('.png')])
CAP_SLOT_STYLE = {1: 'juno', 2: 'ivo', 3: 'kai'}       # fan slot → real Clipzing caption style
def cap_window(t): return T['captions'] - 0.15 < t < T['speaker'] + 0.4
def cap_spread(t): return einout(prog(t, T['captions'] - 0.4, T['captions'] + 0.05)) * (1 - einout(prog(t, T['speaker'] - 0.1, T['speaker'] + 0.3)))
FLIPS = None
def flip_times():
    return (w_('hit') - 0.04, w_('single') - 0.04)
def cap_flip(t):
    """9:16: the centre card flips (to its edge and back) as its caption style changes."""
    a = 0.0
    for ts in flip_times():
        q = prog(t, ts - 0.13, ts + 0.13)
        if 0 < q < 1: a = 80 * math.sin(math.pi * q)
    return a
def portrait_style(t):
    a, b = flip_times()
    return 'ivo' if t < a else 'juno' if t < b else 'kai'

def with_caption(face, style, t):
    """The real caption frame for this moment, inside a card's picture (normal caption size, lower third)."""
    t0, frames = CAPL[style]
    i = min(len(frames) - 1, max(0, int((t - t0) * 60)))
    cap = core.load_rgba(frames[i])
    bz = 12
    pw, ph = face.shape[1] - 2 * bz, face.shape[0] - 2 * bz
    cap = cv2.resize(cap, (pw, ph), interpolation=cv2.INTER_AREA)
    a = cap[..., 3:4].astype(np.float32) / 255
    out = face.copy()
    reg = out[bz:bz + ph, bz:bz + pw].astype(np.float32)
    reg[..., :3] = reg[..., :3] * (1 - a) + cap[..., :3] * a
    out[bz:bz + ph, bz:bz + pw] = reg.astype(np.uint8)
    return out

def slot_of(k, best):
    order = RANK if best > 0.5 else list(range(NSL))
    return [2, 1, 3, 0, 4][order.index(k)] if best > 0.5 else k

CAPW = []
for k in range(0):
    job = json.load(open(os.path.join(HERE, 'assets', f'capword_{k}.json')))
    d = os.path.join(HERE, 'assets', 'captions', f'capword_{k}')
    CAPW.append((job['template'].capitalize(), job['t0'], job['t0'] + job['duration'], [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith('.png')]))

def draw_caption_word(frame, t):
    for k, (name, a, b, frames) in enumerate(CAPW):
        if a <= t < min(b + (0.25 if k == len(CAPW) - 1 else 0.0), T['speaker'] - 0.1):   # gone before the whip
            i = min(len(frames) - 1, int((t - a) * 60))
            img = core.load_rgba(frames[i])
            bb = (0, 860, 1080, 1340)
            crop = img[bb[1]:bb[3]]
            # a soft scrim so every style reads over any picture
            yy = int(pf(H * 0.5, H * 0.5) * core.SCALE); hh = int(pf(330, 300) * core.SCALE)
            band = np.clip(1 - np.abs(np.arange(frame.shape[0]) - yy) / max(1, hh), 0, 1) ** 0.7 * 0.55
            frame *= (1 - band[:, None, None])
            sc = 1 + 0.05 * math.exp(-(t - a) * 18)          # a tiny punch on each word
            composite_sprite(frame, crop, W / 2, pf(H * 0.5, H * 0.5), crop.shape[0] * pf(1.25, 1.2) * sc)
            if a <= t < b:
                tag = O.pill(name, size=34, fill=(40, 30, 74), pad=(30, 14))
                composite_sprite(frame, tag, W / 2, pf(H * 0.62, H * 0.75), tag.shape[0], opacity=min(1, (t - a) / 0.06))
            return

# ── S4: the viewfinder ──────────────────────────────────────────────────────
FACECAM = brand.zing('gamer', 0.6)
MODES = [('PODCAST', 'podcast'), ('STREAM', 'stream'), ('GAMEPLAY', 'gameplay')]
def mode_at(t):
    m = 0
    for i, (_, k) in enumerate(MODES):
        if t >= T[k] - 0.12: m = i
    return m
def flip_angle(t):
    """The monitor spins to its edge and back as the content changes (no mirrored back face)."""
    a = 0.0
    for _, k in MODES[1:]:
        p = prog(t, T[k] - 0.24, T[k] + 0.06)
        if 0 < p < 1: a = 88 * math.sin(math.pi * p)
    return a

@ui.cached(24)
def monitor_face(fi, mode):
    sw, sh = int(FRM.w - 48), int(FRM.h - 48)
    if mode == 0: pic = brand.footage('wide', fi / 30, sw, sh)
    elif mode == 1: pic, _ = game.stream(fi / 30, sw, sh, FACECAM)
    else: pic = game.frame(fi / 30, sw, sh)
    return O.framed(pic, FRM.w, FRM.h, bezel=24, r=44)

def finder_boxes(t, mode):
    """The 9:16 window(s) in monitor-face pixels; they glide and lock."""
    sw, sh = FRM.w - 48, FRM.h - 48
    ww = sh * 9 / 16
    lock = eback(prog(t, T['always'] - 0.1, T['frame'] + 0.05))
    if mode == 0:
        cx = lerp(sw * 0.62, sw * 0.33, lock)
        return [(24 + cx - ww / 2, 24, 24 + cx + ww / 2, 24 + sh)]
    if mode == 1:
        fw, fh = sw * 0.28, sh * 0.36
        fx0, fy0 = sw * 0.025, sh - fh - sh * 0.04
        gx = clamp(sw * game.ship_x(t) - ww / 2, 0, sw - ww)
        return [(24 + fx0, 24 + fy0, 24 + fx0 + fw, 24 + fy0 + fh), (24 + gx, 24, 24 + gx + ww, 24 + sh * 0.6)]
    gx = clamp(sw * game.ship_x(t) - ww / 2, 0, sw - ww)
    return [(24 + gx, 24, 24 + gx + ww, 24 + sh)]

@ui.cached(24)
def result_face(fi, mode, lock100):
    """The 9:16 short the viewfinder produces (the stream's facecam stacks over the gameplay)."""
    ow, oh = 420, 746
    t = fi / 30
    if mode == 0:
        f = brand.footage('wide', t, 1280, 720)
        cx = lerp(1280 * 0.62, 1280 * 0.33, eback(lock100 / 100)); ww = 720 * 9 / 16
        x0 = int(clamp(cx - ww / 2, 0, 1280 - ww)); pic = cv2.resize(f[:, x0:x0 + int(ww)], (ow - 20, oh - 20), interpolation=cv2.INTER_AREA)
    elif mode == 1:
        f, (fx_, fy_, fw_, fh_) = game.stream(t, 1280, 720, FACECAM)
        top = cv2.resize(f[int(fy_):int(fy_ + fh_), int(fx_):int(fx_ + fw_)], (ow - 20, int((oh - 20) * 0.4)), interpolation=cv2.INTER_AREA)
        g = game.frame(t, 1280, 720); gx = int(clamp(1280 * game.ship_x(t) - 360, 0, 560))
        bot = cv2.resize(g[:, gx:gx + 720], (ow - 20, (oh - 20) - top.shape[0]), interpolation=cv2.INTER_AREA)
        pic = np.vstack([top, bot])
    else:
        g = game.frame(t, 1280, 720); ww = 720 * 9 / 16; gx = int(clamp(1280 * game.ship_x(t) - ww / 2, 0, 1280 - ww))
        pic = cv2.resize(g[:, gx:gx + int(ww)], (ow - 20, oh - 20), interpolation=cv2.INTER_AREA)
    return O.framed(pic, ow, oh, bezel=10, r=30)

# ── S5: B-roll exactly where it fits ────────────────────────────────────────
@ui.cached(24)
def talk_card(fi, hl100, swap100=0):
    """The short: the speaker; on 'B-roll' the picture wipes to the cutaway that matches the lit word, while the
    captions stay on top (that is what B-roll is)."""
    hl, sw = hl100 / 100, swap100 / 100
    cw, ch = int(CARD_W * 1.15), int(CARD_H * 1.15)
    pic = brand.footage('closeup_serious', fi / 30, cw - 24, ch - 24).copy()
    if sw > 0:
        cut = brand.footage('rocket', fi / 30, cw - 24, ch - 24)
        yy = int((ch - 24) * (1 - eout(sw)))
        pic[yy:] = cut[yy:]
        cv2.line(pic, (0, yy), (pic.shape[1], yy), (196, 160, 255), 6, cv2.LINE_AA) if 0 < sw < 1 else None
    face = O.framed(pic, cw, ch, bezel=12, r=34)
    L = ui.Layer(cw, ch)
    L.paste(face, 0, 0)
    # the speaker's caption line, with the word the B-roll matches lit up
    y = ch * 0.74
    words = [('then', False), ('we', False), ('LAUNCHED', True)]
    f = 52
    while f > 24 and sum(brand.font(f, 'extrabold').getlength(wd) for wd, _ in words) + 20 * 3 > cw * 0.84: f -= 2
    x = cw * 0.08
    for wd, key in words:
        tw = brand.font(f, 'extrabold').getlength(wd)
        if key and hl > 0:
            L.rrect((x - 10, y - f * 0.72, x + tw + 10, y + f * 0.5), 12, fill=C['purple'] + (int(255 * min(1, hl * 2)),))
        L.type((x, y), wd, f, 'extrabold', fill=(255, 255, 255), anchor='ls')
        x += tw + 20
    return L.rgba()

@ui.cached(24)
def rocket_card(fi):
    cw, ch = int(CARD_W * 0.95), int(CARD_H * 0.95)
    face = O.framed(brand.footage('rocket', fi / 30, cw - 24, ch - 24), cw, ch, bezel=12, r=30)
    return face

# ── S6: the calendar ────────────────────────────────────────────────────────
DAYS = ('MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN')
COLS = pf(4, 7)
PLAT = ['youtubeshorts', 'tiktok', 'youtubeshorts', 'instagram', 'youtubeshorts', 'tiktok', 'youtubeshorts']
ICON = {n: core.load_rgba(os.path.join(HERE, 'assets', 'icons', f'{n}.png')) for n in set(PLAT)}
def day_t(i): return T['whole'] + 0.05 + i * (T['never'] - 0.15 - T['whole']) / 7

@ui.cached(16)
def day_card(i, fi):
    x0, y0, x1, y1 = O.day_cell_box(i, int(CAL.w), int(CAL.h), 7, COLS)
    cw = (x1 - x0) * 0.62; ch = cw * 16 / 9
    ch = min(ch, (y1 - y0) - 140); cw = ch * 9 / 16
    pic = brand.footage(MOM[i % 5], fi / 30 + i, cw - 16, ch - 16)
    face = O.framed(pic, cw, ch, bezel=8, r=18).copy()
    ic = cv2.resize(ICON[PLAT[i]], (int(cw * 0.42), int(cw * 0.42)), interpolation=cv2.INTER_AREA)
    L = ui.Layer(int(cw), int(ch + cw * 0.3))
    L.paste(face, 0, 0); L.paste(ic, cw - ic.shape[1] * 0.75, ch - ic.shape[0] * 0.55)
    return L.rgba()

@ui.cached(4)
def legend():
    items = [('youtubeshorts', 'Scheduled'), ('tiktok', 'To drafts'), ('instagram', 'Reels-ready')]   # the mark names the platform
    w = pf(1000, 1500); h = 120
    L = ui.Layer(w, h)
    for i, (ic, label) in enumerate(items):
        x = w * (i / 3) + 20
        L.paste(cv2.resize(ICON[ic] if ic in ICON else core.load_rgba(os.path.join(HERE, 'assets', 'icons', f'{ic}.png')), (72, 72), interpolation=cv2.INTER_AREA), x, 24)
        L.type((x + 90, 60), label, pf(36, 36), 'bold', fill=(230, 226, 248), anchor='lm')
    return L.rgba()

def contact(frame, cam, pl, strength=0.55, spread=1.0):
    """A soft contact shadow under an object, so it sits in the world instead of floating."""
    x, y, z = core.proj1(cam, pl.world(pl.w / 2, pl.h) - v3(0, 40, 0))
    x2, _, _ = core.proj1(cam, pl.world(pl.w, pl.h))
    x1, _, _ = core.proj1(cam, pl.world(0, pl.h))
    if z < 100: return
    rx = max(4, abs(x2 - x1) * 0.55 * spread); ry = max(3, rx * 0.12)
    hh, ww = frame.shape[:2]
    if rx > ww * 3 or not (-ww < x < 2 * ww) or not (-hh < y < 2 * hh): return     # the camera is on top of it: no shadow
    ry = min(ry, hh * 0.15)
    m = np.zeros(frame.shape[:2], np.float32)
    cv2.ellipse(m, (int(x), int(y + ry)), (int(rx), int(ry)), 0, 0, 360, strength, -1, cv2.LINE_AA)
    frame *= (1 - cv2.GaussianBlur(m, (0, 0), min(max(2.0, ry * 1.2), 40.0))[..., None])   # capped sigma: a huge kernel OOM-killed the check

# ── the camera: one continuous flight ───────────────────────────────────────
def camera_at(t):
    pose = off_axis(CNT.c, lerp(14, 4, prog(t, 0, T['i'])), lerp(10, 6, prog(t, 0, T['i'])), D * pf(1.0, 1.05) * lerp(0.92, 1.0, eout(prog(t, 0, T['i']))), v3(0, pf(0, 120) * prog(t, T['i'] - 0.4, T['i']), 0))
    # to the slab (it drops into frame), and in to the slicing
    s_pose = off_axis(SLAB_C, -8, 6, D * pf(0.95, 0.92), v3(0, -30, 0))
    pose = pose_mix(pose, s_pose, einout(prog(t, T['you'] + 0.02, T['drop'] + 0.15)))
    fan_pose = off_axis(SLAB_C + v3(0, 0, 80), -4, 4, D * pf(1.0, 0.95))
    pose = pose_mix(pose, fan_pose, einout(prog(t, T['shorts'] - 0.2, T['best'] + 0.3)))
    # into the best card: its picture fills the frame (the captions play on it)
    cap_pose = off_axis(SLAB_C + v3(0, pf(-10, -10), pf(330, 60)), -2, 3, D * pf(1.0, 1.0))
    pose = pose_mix(pose, cap_pose, einout(prog(t, T['captions'] - 0.35, T['captions'] + 0.1)))
    # whip to the viewfinder monitor
    f_pose = off_axis(FRM.c + v3(0, pf(-330, 0), 0), -16, 6, D * pf(1.18, 1.0))
    pose = pose_mix(pose, f_pose, einout(prog(t, T['speaker'] - 0.12, T['speaker'] + 0.3)))   # leave only after the last caption word
    pose = pose_mix(pose, off_axis(FRM.c + v3(pf(0, 300), pf(-330, 0), 0), -9, 4, D * pf(1.1, 1.12)), prog(t, T['speaker'] + 0.3, T['broll'] - 0.35) * 0.9)
    # to the B-roll cards
    b_pose = off_axis(BRL_C, 12, 4, D * (CARD_H * 1.15) / (pf(0.72, 0.84) * H))
    pose = pose_mix(pose, b_pose, einout(prog(t, T['broll'] - 0.35, T['broll'] + 0.05)))
    # to the calendar
    c_pose = off_axis(CAL.c, 14, 10, D * pf(1.02, 0.98), v3(0, pf(-120, 40), 0))
    pose = pose_mix(pose, c_pose, einout(prog(t, T['then'] - 0.3, T['then'] + 0.15)))
    pose = pose_mix(pose, off_axis(CAL.c, 8, 8, D * pf(0.98, 0.94), v3(0, pf(-120, 40), 0)), prog(t, T['then'] + 0.15, T['clipzing2'] - 0.45) * 0.9)
    # it falls away for the hero
    pose = pose_mix(pose, off_axis(CAL.c, 0, 30, D * 2.4), ein(prog(t, T['clipzing2'] - 0.45, T['land'] + 0.1)))
    whips = [(T['you'] + 0.02, 0.5, 6), (T['speaker'] - 0.12, 0.42, -7), (T['broll'] - 0.35, 0.4, 7), (T['then'] - 0.3, 0.45, -6)]
    roll = sum(r * math.sin(math.pi * prog(t, a, a + d)) for a, d, r in whips)
    sh = [shake_at(t, T[k], a) for k, a in (('i', 26), ('drop', 22), ('shorts', 10), ('land', 18))]
    return Camera(pose[0], pose[1], roll=roll, shake=(sum(x[0] for x in sh), sum(x[1] for x in sh)))

def focus_of(cam): return float(cam.to_cam(cam.target[None])[0, 2])

# ── the line of light (one function, many jobs) ─────────────────────────────
def line_jobs(t, cam):
    jobs = []
    if T['you'] - 0.05 < t < T['drop'] + 0.6:        # from Zing to where the slab will land
        a = CNT.world(460, 0) + v3(0, 120, 0); b = SLAB_C + v3(0, SLAB_H / 2 + 80, 0)
        mid = (a + b) / 2 + v3(0, 900, 300)
        pts = np.array([core.catmull([a, mid, b], s) for s in np.linspace(0, 1, 50)])
        up = eout(prog(t, T['you'] - 0.05, T['drop']))
        jobs.append(dict(pts=pts, upto=up, start=max(0, up - 0.5), width=12))
    sl = slab_plane(t)
    for k, tc in enumerate(CUT_T):                     # the cuts: down through the slab
        if tc - 0.02 < t < SPLIT[0] + 0.15:
            x = (k + 1) * SLAB_W / NSL
            pts = sl.worlds([(x, -60 + v * (SLAB_H + 120) / 30) for v in range(31)]) + sl.n * 30
            jobs.append(dict(pts=pts, upto=eout(prog(t, tc, tc + 0.12)), width=10, op=1 - prog(t, SPLIT[0], SPLIT[0] + 0.15)))
    if T['broll'] - 0.1 < t < T['fits'] + 0.4:         # from the spoken word to its B-roll
        tc_ = talk_plane(t)
        a = tc_.world(tc_.w * 0.52, tc_.h * 0.72) + tc_.n * 20
        b = tc_.world(tc_.w * 0.62, tc_.h * 0.3) + tc_.n * 20
        mid = (a + b) / 2 + v3(260, 120, 160)
        pts = np.array([core.catmull([a, mid, b], s) for s in np.linspace(0, 1, 40)])
        jobs.append(dict(pts=pts, upto=eout(prog(t, T['exactly'] - 0.2, T['exactly'] + 0.2)), width=9, op=1 - prog(t, T['fits'] + 0.1, T['fits'] + 0.4)))
    if False:    # (removed: a line zig-zagging across the days read as noise)
        cells = [O.day_cell_box(i, int(CAL.w), int(CAL.h), 7, COLS) for i in range(7)]
        pts = CAL.worlds([((c[0] + c[2]) / 2, c[3] - 20) for c in cells]) + CAL.n * 30
        dense = np.array([core.catmull(list(pts), s) for s in np.linspace(0, 1, 90)])
        jobs.append(dict(pts=dense, upto=eout(prog(t, T['whole'], T['never'] - 0.1)), width=10, op=1 - prog(t, T['clipzing2'] - 0.6, T['clipzing2'] - 0.3)))
    return jobs

def talk_plane(t):
    return Plane(BRL_C, yaw=14, pitch=-4, size=(int(CARD_W * 1.15), int(CARD_H * 1.15)))
def rocket_plane(t):
    p = eback(prog(t, T['broll'] + 0.05, T['broll'] + 0.45))
    c = BRL_C + v3(CARD_W * 0.45 + (1 - p) * 900, 40 + (1 - p) * 500, 160)
    return Plane(c, yaw=14 - 40 * (1 - p), pitch=-4, size=(int(CARD_W * 0.95), int(CARD_H * 0.95)))

# ── the scene ───────────────────────────────────────────────────────────────
def scene(t):
    frame = new_frame()
    stage(frame, base=brand.STAGE_BASE, glows=(((0.5, 0.45 + 0.04 * math.sin(t * 0.5)), LINE, 0.13, 0.62), ((0.12, 0.9), C['zing_hem'], 0.06, 0.5),
                                                ((0.9, 0.1), C['violet'], 0.05, 0.4)), t=t)
    cam = camera_at(t); foc = focus_of(cam)
    fi = int(t * 30)
    deferred = []
    # S1 counter
    if t < T['drop'] + 0.4:
        draw_counter(frame, cam, t, foc, opacity=1 - prog(t, T['drop'] - 0.1, T['drop'] + 0.3))
    # S2 slab → cards
    if T['you'] < t < T['speaker'] + 0.4:      # the best card stays in the world and slides out with the whip
        if t < SPLIT[0] + 0.02:
            contact(frame, cam, slab_plane(t), 0.6 * eout(prog(t, T['drop'], T['drop'] + 0.4)))
            composite_extruded(frame, cam, slab_plane(t), slab_face(fi % 300, 0), depth=90, steps=12, side=SIDE, focus=foc)
        else:
            planes = [card_plane(k, t, fi) for k in range(NSL)]
            order = sorted(range(NSL), key=lambda k: -float(cam.to_cam(planes[k][0].c[None])[0, 2]))   # far → near
            for k in order:
                pl, face = planes[k]
                slot = slot_of(k, 1)
                front = slot in CAP_SLOT_STYLE
                op = 1.0 if front else 1 - prog(t, T['captions'] - 0.35, T['captions'] - 0.05)
                style = (portrait_style(t) if slot == 2 else None) if P else CAP_SLOT_STYLE.get(slot)
                if P and slot != 2: front = False
                if cap_window(t) and front: face = with_caption(face, style, t)
                composite_extruded(frame, cam, pl, face, depth=40, steps=8, side=SIDE, focus=foc, opacity=op)
                if cap_window(t) and front:   # the style's name under its card
                    lab = O.pill(style.capitalize(), size=40, fill=C['purple'] if slot == 2 else (44, 34, 80), pad=(30, 16))
                    x, y, z = core.proj1(cam, pl.world(pl.w / 2, pl.h + 50))
                    if z > 100:
                        s_ = core.screen_scale(cam, pl.c) / core.SCALE
                        composite_sprite(frame, lab, x / core.SCALE, y / core.SCALE, lab.shape[0] * s_ * 1.3 * eback(prog(t, T['captions'] - 0.1, T['captions'] + 0.2)))
                    continue
                if t > T['best'] + 0.1:   # score chips on the cards
                    sc = SCORES[k]
                    chip = O.pill(f'{sc}', size=44 if k == RANK[0] else 34, fill=C['flame_hi'] if k == RANK[0] else (40, 32, 70),
                                  fg=(60, 30, 0) if k == RANK[0] else (255, 255, 255), pad=(26, 14))
                    x, y, z = core.proj1(cam, pl.world(pl.w / 2, -30) + pl.n * 10)
                    if z > 100:
                        s_ = core.screen_scale(cam, pl.c) / core.SCALE
                        composite_sprite(frame, chip, x / core.SCALE, y / core.SCALE, chip.shape[0] * s_ * eback(prog(t, T['best'] + 0.1, T['best'] + 0.35)) * 1.4,
                                         opacity=op)
                if k == RANK[0] and t > T['best'] + 0.2 and not cap_window(t):
                    tag = O.pill('BEST MOMENT', size=34, fill=C['purple'], pad=(26, 14))
                    x, y, z = core.proj1(cam, pl.world(pl.w / 2, pl.h + 40))
                    if z > 100:
                        s_ = core.screen_scale(cam, pl.c) / core.SCALE
                        composite_sprite(frame, tag, x / core.SCALE, y / core.SCALE, tag.shape[0] * s_ * 1.3 * eback(prog(t, T['best'] + 0.2, T['best'] + 0.45)), opacity=op * (1 - prog(t, T['captions'] - 0.4, T['captions'] - 0.2)))
    # S3 captions over the best card's picture
    pass  # (captions now play inside the three front cards, at real size)
    # S4 viewfinder
    if T['speaker'] - 0.25 < t < T['broll'] + 0.1:
        m = mode_at(t)
        pl = Plane(FRM.c, yaw=-22 + flip_angle(t), pitch=-6, size=(FRM.w, FRM.h))
        contact(frame, cam, pl)
        composite_extruded(frame, cam, pl, monitor_face(fi % 300, m), depth=110, steps=12, side=(40, 34, 64), focus=foc)
        if abs(flip_angle(t)) < 30:
            br = O.bracket_layer(FRM.w, FRM.h, finder_boxes(t, m), thick=16)
            composite_plane(frame, cam, core.plane_shift(pl, 18), br, focus=foc, opacity=prog(t, T['speaker'] - 0.1, T['speaker'] + 0.15))
        # the live result: what the 9:16 window captures, as a vertical short beside / under the monitor
        out = result_face(fi % 300, m, int(100 * prog(t, T['always'] - 0.1, T['frame'] + 0.05)))
        rp = Plane(FRM.c + pf(v3(0, -FRM.h / 2 - 380, 120), v3(FRM.w / 2 + 250, -20, 120)), yaw=-14, pitch=-6, size=(out.shape[1], out.shape[0]))
        if t > T['always'] - 0.15:
            pop = eback(prog(t, T['always'] - 0.15, T['always'] + 0.2))
            rp2 = Plane(rp.c, yaw=-14, pitch=-6, size=(out.shape[1] * pop, out.shape[0] * pop))
            composite_extruded(frame, cam, rp2, out, depth=40, steps=8, side=SIDE, focus=foc)
        lab = O.pill(MODES[m][0], size=46, fill=C['purple'])
        x, y, z = core.proj1(cam, pl.world(pl.w / 2, -70))
        if z > 100 and t > T['podcast'] - 0.15:
            s_ = core.screen_scale(cam, pl.c) / core.SCALE
            pop = eback(prog(t, T[MODES[m][1]] - 0.12, T[MODES[m][1]] + 0.15))
            composite_sprite(frame, lab, x / core.SCALE, y / core.SCALE, lab.shape[0] * s_ * 1.3 * pop)
    # S5 B-roll
    if T['broll'] - 0.5 < t < T['then'] + 0.1:
        hl = prog(t, T['broll'] - 0.05, T['broll'] + 0.2)
        sw = prog(t, T['exactly'] - 0.05, T['exactly'] + 0.4)
        tp = talk_plane(t)
        contact(frame, cam, tp)
        composite_extruded(frame, cam, tp, talk_card(fi % 300, int(hl * 100), int(sw * 100)), depth=50, steps=9, side=SIDE, focus=foc)
        if t > T['exactly'] - 0.05:
            tag = O.pill('B-ROLL', size=44, fill=C['purple'])
            x, y, z = core.proj1(cam, tp.world(tp.w * 0.5, -46))
            if z > 100:
                s_ = core.screen_scale(cam, tp.c) / core.SCALE
                composite_sprite(frame, tag, x / core.SCALE, y / core.SCALE, tag.shape[0] * s_ * 1.4 * eback(prog(t, T['exactly'] - 0.05, T['exactly'] + 0.2)))
    # S6 calendar
    if T['then'] - 0.5 < t < T['land'] + 0.2:
        op = 1 - prog(t, T['clipzing2'] - 0.35, T['land'] - 0.05)
        contact(frame, cam, CAL, 0.6)
        composite_extruded(frame, cam, CAL, O.calendar_body(int(CAL.w), int(CAL.h), DAYS, COLS), depth=120, steps=12, side=(30, 26, 54), focus=foc, opacity=op)
        for i in range(7):
            p = eback(prog(t, day_t(i), day_t(i) + 0.3))
            if p <= 0: continue
            x0, y0, x1, y1 = O.day_cell_box(i, int(CAL.w), int(CAL.h), 7, COLS)
            dc = day_card(i, fi % 300)
            # the short stands up out of its day, leaning back
            pl = Plane(CAL.world((x0 + x1) / 2, y0 + 80 + dc.shape[0] / 2) + CAL.n * (30 + 60 * min(1, p)), yaw=20, pitch=-14 + 14 * (1 - min(1, p)),
                       size=(dc.shape[1], dc.shape[0]))
            composite_extruded(frame, cam, pl, dc, depth=18, steps=5, side=SIDE, focus=foc, opacity=op * min(1, p * 1.5))
        if t > T['never'] - 0.05:   # Clipzing's streak, not a row of green checks
            sb = O.streak_badge()
            p = eback(prog(t, T['never'] - 0.05, T['never'] + 0.3))
            pl = Plane(CAL.world(CAL.w * pf(0.42, 0.5), -90) + CAL.n * 60, yaw=20, pitch=-14, size=(sb.shape[1] * p * pf(0.82, 1), sb.shape[0] * p * pf(0.82, 1)))
            if p > 0.02: composite_extruded(frame, cam, pl, sb, depth=36, steps=8, side=(170, 90, 10), focus=foc, opacity=op)
        if t > T['week'] - 0.1:   # the honest legend, readable (screen space, inside the safe area)
            lg = legend()
            a_ = op * prog(t, T['week'] - 0.1, T['week'] + 0.15)
            composite_sprite(frame, lg, W / 2, pf(H * 0.745, H * 0.93), lg.shape[0] * pf(0.95, 0.8), opacity=a_)
    # the line of light
    for j in line_jobs(t, cam):
        deferred.append(lambda fr, cam=cam, j=j: draw_line(fr, cam, j['pts'], upto=j['upto'], start=j.get('start', 0), color=LINE, width=j['width'], opacity=j.get('op', 1)))
    # Zing: the slam on "I", and the hero landing
    draw_zing(frame, cam, t)
    if T['i'] <= t < T['i'] + 0.6:
        x, y, z = core.proj1(cam, CNT.world(460, 0) + v3(0, 60, 0))
        fx.shards(frame, t, T['i'], x / core.SCALE, y / core.SCALE, n=26, size=13)
    if T['slices'] < t < SPLIT[0] + 0.3:     # sparks at each cut
        sl = slab_plane(t)
        for k, tc in enumerate(CUT_T):
            x, y, z = core.proj1(cam, sl.world((k + 1) * SLAB_W / NSL, SLAB_H * eout(prog(t, tc, tc + 0.12))))
            fx.shards(frame, t, tc, x / core.SCALE, y / core.SCALE, n=8, size=8, speed=900, life=0.35, seed=20 + k)
    return frame, deferred

def draw_zing(frame, cam, t):
    if T['i'] - 0.25 < t < T['drop']:          # the slam onto the counter
        x, y, z = core.proj1(cam, CNT.world(460, 0) + v3(0, 30, 0))
        s = core.screen_scale(cam, CNT.c) / core.SCALE
        k = t - T['i']
        zh = 330 * s
        if k < 0:
            p = prog(t, T['i'] - 0.25, T['i'])
            composite_sprite(frame, brand.zing('slam', 0), x / core.SCALE, y / core.SCALE - zh * 0.5 - (1 - p) * 700, zh * 1.6 * (0.3 + 0.7 * p), blur=(1 - p) * 10)
        else:
            sq = math.exp(-k * 9) * math.cos(k * 34) * 0.25
            pose = 'slam' if k < 0.12 else 'wink'
            bx = brand.zing_box(pose)
            op = 1 - prog(t, T['drop'] - 0.25, T['drop'] - 0.05)
            composite_sprite(frame, brand.zing(pose, k), x / core.SCALE, y / core.SCALE, zh / (bx[3] - bx[1]), sx=1 + sq, sy=1 - sq, anchor=(0.5, bx[3]), opacity=op)
    if t >= T['land'] - 0.35:                  # the hero landing
        p = prog(t, T['land'] - 0.35, T['land'])
        k = max(0.0, t - T['land'])
        sq = math.exp(-k * 8) * math.cos(k * 30) * 0.24 if t >= T['land'] else -0.12
        pose = 'land' if k < 0.5 else 'cheer'
        bx = brand.zing_box(pose)
        zh = H * pf(0.22, 0.34); zc = (W / 2, H * pf(0.33, 0.33))
        y = lerp(-H * 0.25, zc[1], ein(p))
        if t >= T['land'] - 0.08:
            s = core.SCALE; shm = np.zeros(frame.shape[:2], np.float32)
            cv2.ellipse(shm, (int(zc[0] * s), int((zc[1] + zh / 2 + 6) * s)), (max(1, int(zh * 0.42 * s)), max(1, int(zh * 0.06 * s))), 0, 0, 360, 0.55, -1, cv2.LINE_AA)
            frame *= (1 - cv2.GaussianBlur(shm, (0, 0), max(1.0, 10 * s))[..., None])
        composite_sprite(frame, brand.zing(pose, k), zc[0], y + zh / 2, zh / (bx[3] - bx[1]), sx=1 + sq, sy=1 - sq, anchor=(0.5, bx[3]))

def probe(t):
    out = []
    if abs(t - T['i']) < 0.3: out.append((W / 2, H * 0.4 - (1 - prog(t, T['i'] - 0.25, T['i'])) * 700))
    if T['land'] - 0.4 < t < T['land'] + 0.3: out.append((W / 2, H * 0.33 - (1 - prog(t, T['land'] - 0.35, T['land'])) * 800))
    return out or [(0, 0)]

# ── after the grade: supers and marks ───────────────────────────────────────
WM = brand.wordmark(); WMT = brand.wordmark_text()
def overlay(frame, t):
    # the hook, readable on mute: "Stuck at 200 followers?" (the counter says the rest)
    if t < T['i'] + 0.1:
        a = prog(t, T['stuck'] - 0.05, T['stuck'] + 0.08) * (1 - prog(t, T['i'] - 0.1, T['i'] + 0.05))
        img = fx.type_rgba('STUCK AT', pf(118, 120))
        core.after_grade(frame, img, W / 2 - img.shape[1] / 2, pf(H * 0.2, H * 0.08), opacity=a)
    if T['i'] - 0.05 < t < T['drop'] - 0.1:
        a = prog(t, T['you'], T['you'] + 0.12) * (1 - prog(t, T['drop'] - 0.3, T['drop'] - 0.1))
        img = fx.type_rgba('I got you.', pf(118, 120), fill=C['lilac'])
        core.after_grade(frame, img, W / 2 - img.shape[1] / 2, pf(H * 0.66, H * 0.8), opacity=a)
    # the lock-up from 0.3 s (the brand inside the first second)
    a = prog(t, 0.3, 0.55) * (1 - prog(t, T['drop'] - 0.2, T['drop']))
    if a > 0:
        h = pf(62, 54)
        wmi = cv2.resize(WM, (int(WM.shape[1] * h / WM.shape[0]), h), interpolation=cv2.INTER_AREA)
        core.after_grade(frame, wmi, W / 2 - wmi.shape[1] / 2, pf(232, 36), opacity=a)
    # supers that name each feature as it is said (keynote style, short)
    for txt, a0, a1 in (('Long video → shorts', T['drop'] + 0.3, SPLIT[0] + 0.1),):
        if a0 < t < a1 + 0.2:
            a = prog(t, a0, a0 + 0.2) * (1 - prog(t, a1, a1 + 0.2))
            img = fx.type_rgba(txt, pf(80, 78))
            core.after_grade(frame, img, W / 2 - img.shape[1] / 2, pf(H * 0.12, H * 0.05), opacity=a)
    # the hero: wordmark + the line-of-light reveal, then the two beats and the end card
    if t >= T['land'] + 0.1:
        zh = H * pf(0.22, 0.34); zc_y = H * 0.33
        h = pf(120, 110)
        img = cv2.resize(WMT, (int(WMT.shape[1] * h / WMT.shape[0]), h), interpolation=cv2.INTER_AREA)
        rv = eout(prog(t, T['land'] + 0.1, T['land'] + 0.45))
        img = img.copy(); img[:, int(img.shape[1] * rv):, 3] = 0
        up = eout(prog(t, T['endcard'], T['endcard'] + 0.5)) * 30
        y = zc_y + zh / 2 + 55 - up
        core.after_grade(frame, img, W / 2 - img.shape[1] / 2, y)
        for i, (txt, key) in enumerate((('Long videos in.', 'long2'), ('Shorts out.', 'shorts2'))):
            if t > T[key] - 0.05:
                im2 = fx.type_rgba(txt, pf(92, 86), fill=C['lilac'] if i else (255, 255, 255))
                p = eout(prog(t, T[key] - 0.05, T[key] + 0.15))
                core.after_grade(frame, im2, W / 2 - im2.shape[1] / 2, y + h + 50 + i * pf(110, 100) + (1 - p) * 30, opacity=p)
        if t >= T['endcard']:
            L = ui.Layer(W, 100, ss=1)
            L.type((W / 2, 50), 'clipzing.com', 50, 'semibold', fill=C['lilac'], anchor='mm')
            core.after_grade(frame, L.rgba(), 0, y + h + 50 + pf(250, 230), opacity=prog(t, T['endcard'] + 0.1, T['endcard'] + 0.45))

def deferred_wordmark_line(frame, t):
    pass

# ── sound ───────────────────────────────────────────────────────────────────
def cues():
    c = Cues()
    c.add(0.0, 'whoosh', size=0.4).add(T['stuck'] - 0.02, 'thump', size=0.5)
    for t0 in (T['stuck'] + 0.1, T['followers'] - 0.25, T['followers'] + 0.25):
        c.add(t0 + 0.02, 'tick', size=0.6).add(t0 + 0.2, 'crack', size=0.35)
    c.add(T['i'] - 0.25, 'suck', size=0.6).add(T['i'] - 1 / 60, 'impact', size=1.0).add(T['i'], 'glass', size=0.7).add(T['got'] + 0.08, 'pop', size=0.5)
    c.add(T['you'] + 0.02, 'whoosh', x=0.4, size=0.9).add(T['you'] + 0.1, 'zip', x=0.4, size=0.6)
    c.add(T['drop'] - 0.08, 'falling', size=0.6).add(T['drop'] + 0.3, 'impact', size=0.8)
    for k, tc in enumerate(CUT_T): c.add(tc, 'zip', x=-0.5 + 0.33 * k, size=0.5).add(tc + 0.05, 'crack', x=-0.5 + 0.33 * k, size=0.3)
    c.add(SPLIT[0], 'whoosh', size=0.6)
    for k in range(NSL): c.add(SPLIT[0] + 0.1 + k * 0.06, 'pop', x=-0.6 + 0.3 * k, size=0.5)
    c.add(T['best'] - 0.02, 'whoosh', size=0.4).add(T['best'] + 0.15, 'shimmer', size=0.5)
    c.add(T['captions'] - 0.35, 'whoosh', size=0.5)
    for wd in ('captions', 'that', 'hit', 'every', 'single', 'word'): c.add(w_(wd) - 0.01, 'tap', size=0.3)
    c.add(T['speaker'] - 0.12, 'whoosh_down', x=-0.5, size=0.9)
    c.add(T['always'] - 0.05, 'zip', size=0.4).add(T['frame'] + 0.04, 'lock', size=0.6)
    for _, k in MODES[1:]: c.add(T[k] - 0.24, 'whoosh', size=0.45).add(T[k] + 0.05, 'lock', size=0.45)
    for _, k in MODES: c.add(T[k] - 0.1, 'pop', size=0.4)
    c.add(T['broll'] - 0.35, 'whoosh', x=0.5, size=0.8).add(T['broll'] + 0.05, 'whoosh', x=0.6, size=0.5).add(T['broll'] + 0.4, 'thump', size=0.6)
    c.add(T['fits'], 'lock', size=0.5)
    c.add(T['then'] - 0.3, 'whoosh_down', size=0.8)
    for i in range(7): c.add(day_t(i), 'pop', x=-0.8 + 0.27 * i, size=0.5).add(day_t(i) + 0.02, 'tick', x=-0.8 + 0.27 * i, size=0.3)
    c.add(T['never'] - 0.05, 'impact', size=0.5).add(T['never'], 'fire', size=0.5).add(T['day'], 'shimmer', size=0.6)
    c.add(T['clipzing2'] - 0.45, 'whoosh_down', size=0.5).add(T['land'] - 0.33, 'falling', size=0.6).add(T['land'], 'thump', size=1.0)
    c.add(T['land'] + 0.12, 'zip', size=0.5)
    c.add(T['long2'] - 0.05, 'pop', size=0.4).add(T['shorts2'] - 0.05, 'pop', size=0.45).add(T['endcard'], 'whoosh', size=0.3)
    return c

def hero_cues():
    return [('clip_ready', WORDS.after('first', gap=0.12)), ('clip_ready', WORDS.after('day', gap=0.1)), ('logo_hit', T['land']),
            ('logo_chord', WORDS.end('clipzing', 2) + 0.04), ('published', WORDS.end('out') + 0.2)]

MUSIC = dict(style='mallet_pop', bpm=116, drop=T['drop'], lift=T['podcast'], breath=T['clipzing2'] - 0.45, hit=T['land'], sting=False)
