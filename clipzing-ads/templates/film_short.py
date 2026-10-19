"""<TITLE>: a Clipzing ad, built with the clipzing-ads skill (adkit).

A complete, runnable starter. Copy it into a project (scripts/new_ad.py does), then replace the stations with your
concept. It shows every pattern a film needs:
  - a timeline driven by the voice's words (falls back to fixed times until voice/words.json exists)
  - stations as planes with home poses, one continuous camera with eased flights and a hit shake
  - Zing from his own rig: a hook SLAM with squash and stretch, a blink, a hop, and the hero landing ON the hit
  - THE line of light, drawn by one function, revealing the wordmark (deferred: drawn once from the centre sample)
  - a product station rebuilt in Clipzing's UI language (cached layers), real footage on a phone, a score ring
  - type that lands with the word, the wordmark composited after the grade, an end card
  - a cue list that the mix builds every sound from
  - a 9:16 / 16:9 re-layout through core.PORTRAIT

Render:  python3 TOOLKIT/render.py film.py stills out/ 0.3 1.2 3 5 8 --fmt 9x16
"""
import math
import os
import sys

import cv2
import numpy as np

TOOLKIT = os.environ.get('ADKIT', os.path.expanduser('~/shorten/.claude/skills/clipzing-ads/toolkit'))
sys.path.insert(0, TOOLKIT)
from adkit import brand, core, fx, ui                                     # noqa: E402
from adkit.brand import C, LINE                                           # noqa: E402
from adkit.core import (D, H, PORTRAIT, W, Camera, Plane, clamp, composite_plane, composite_sprite, draw_line,  # noqa: E402
                        eback, einout, eout, lerp, new_frame, pose_mix, prog, shake_at, spring, stage, v3)
from adkit.timeline import Cues, Words                                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
END = 12.0                       # seconds, end card included
VO_OFF = 0.45                    # where the voice starts in the film
_wp = os.path.join(HERE, 'voice', 'words.json')
WORDS = Words(_wp, VO_OFF) if os.path.exists(_wp) else None
def at(word, n=1, fallback=0.0):
    """Start time of a spoken word (the picture locks to the voice); a fallback until the voice exists."""
    try:
        return WORDS.t(word, n) if WORDS else fallback
    except KeyError:
        return fallback

# ── the timeline (every hit is named here; the picture and the sound both read it) ──
T = {
    'slam': 0.17,                       # Zing slams (the hook lands within 0.3 s)
    'reveal': 0.55,                     # the line runs under the lock-up and reveals the wordmark
    'blink': 1.25, 'hop': 1.5,          # he blinks, then hops out
    'fly': 1.75,                        # the camera flies to the product station
    'tap': at('paste', 1, 2.9),         # the button is pressed on the word
    'ready': at('ready', 1, 4.3),       # the score ring completes (`clip_ready` chime just after the word)
    'type': at('one', 2, 6.2),          # the tagline lands with the voice
    'land': 8.6,                        # Zing lands ON the hit
    'endcard': 10.2,
}

# ── the world: stations are flat faces, each with a home pose that maps it 1:1 onto the screen ──
S1 = Plane(v3(0, 0, 0))                                         # the hook / lock-up
S2 = Plane(v3(1500, -260, -3600), yaw=-16, size=(W, H))         # the product station
F = Plane(v3(-200, 120, -7600), yaw=6, size=(W, H))             # type, hero, end card
WM = brand.wordmark()
WM_W = 820 if PORTRAIT else 980
WM_H = WM_W * WM.shape[0] / WM.shape[1]

# ── layers (cached: UI is drawn once per state, not per motion-blur sub-frame) ──
@ui.cached()
def product_layer(state):
    """The product station: a phone playing Zing's podcast with a score ring and a primary button.
    `state` is quantised (0..100) so nearby sub-frames share one layer."""
    p = state / 100
    L = ui.Layer(W, H)
    ph_w = 560 if PORTRAIT else 470
    ph_h = ph_w * 2.05
    px, py = (W - ph_w) / 2, (H * 0.13 if PORTRAIT else (H - ph_h) / 2)
    if not PORTRAIT: px = W * 0.2
    screen = brand.footage('closeup', p * 3, ph_w * 0.93, ph_h * 0.955)
    phone, _ = ui.phone(int(ph_w), int(ph_h), screen)
    L.paste(phone, px, py)
    # score ring + label beside / under the phone
    cx, cy = (W / 2, py + ph_h + 120) if PORTRAIT else (W * 0.66, H * 0.42)
    ui.surface(L, (cx - 300, cy - 110, cx + 300, cy + 110), r=28)
    ui.score_badge(L, cx - 190, cy, 94, r=72, p=eout(clamp((p - 0.35) / 0.4)))
    L.type((cx - 90, cy - 34), 'Viral score', 34, 'semibold', fill=C['fg_muted'])
    L.type((cx - 90, cy + 8), 'Best moment found', 40, 'bold', fill=C['fg'])
    by = cy + (180 if PORTRAIT else 190)
    ui.button(L, (cx - 260, by, cx + 260, by + 96), 'Generate clips', press=clamp(1 - abs(p - 0.2) * 12), size=38, icon='plus')
    return L.rgba()

def product_state(t):
    return int(round(100 * clamp(prog(t, T['tap'] - 0.6, T['ready'] + 0.4))))

@ui.cached()
def type_layer(n_words):
    lines = ['One link.', 'All your shorts.'][:n_words]
    L = ui.Layer(W, H)
    size = 120 if PORTRAIT else 132
    for i, s in enumerate(lines):
        L.type((W / 2, H * 0.40 + i * size * 1.15), s, size, 'extrabold', fill=C['fg'], anchor='mm', tracking=-0.02)
    return L.rgba()

# ── the camera: one continuous flight ───────────────────────────────────────
def camera_at(t):
    # S1: slam pose close in, easing back to the lock-up home
    near = S1.home(D * 0.62)
    home1 = S1.home(D * 1.0)
    pose = pose_mix(near, home1, einout(prog(t, T['slam'] + 0.05, 1.05)))
    # fly to the product station (fast in the middle, eased at the ends), then a slow push
    p2 = S2.home(D * (1.0 if PORTRAIT else 1.02), 0, 40 if PORTRAIT else 0)
    pose = pose_mix(pose, p2, einout(prog(t, T['fly'], T['fly'] + 0.85)))
    pose = pose_mix(pose, S2.home(D * 0.94, 0, 40 if PORTRAIT else 0), prog(t, T['fly'] + 0.85, T['type'] - 0.5) * 0.6)
    # whip to the final face
    pose = pose_mix(pose, F.home(D), einout(prog(t, T['type'] - 0.45, T['type'] + 0.15)))
    pose = pose_mix(pose, F.home(D * 0.97), prog(t, T['type'] + 0.15, END) * 0.8)       # holds still breathe
    roll = 6 * math.sin(math.pi * prog(t, T['fly'], T['fly'] + 0.85)) - 5 * math.sin(math.pi * prog(t, T['type'] - 0.45, T['type'] + 0.15))
    sx, sy = shake_at(t, T['slam'], 26); lx, ly = shake_at(t, T['land'], 18)
    return Camera(pose[0], pose[1], roll=roll, shake=(sx + lx, sy + ly))

def probe(t):
    """Screen points that move on their own (Zing), so the adaptive motion blur sees them."""
    return [zing_xy(t)[:2]]

# ── Zing ────────────────────────────────────────────────────────────────────
def zing_xy(t):
    """Screen centre (full-size px), height, squash (sx, sy) and pose of Zing at t."""
    hook_h = H * (0.36 if PORTRAIT else 0.5)
    if t < T['hop'] + 0.6:
        if t < T['slam']:           # rushing from depth
            p = prog(t, 0, T['slam'])
            return W / 2, H * 0.45, hook_h * (0.15 + 0.85 * core.ein(p)), 0.85, 1.25, 'slam'
        k = t - T['slam']
        sq = math.exp(-k * 9) * math.cos(k * 34) * 0.22                       # squash and stretch after the impact
        settle = einout(prog(t, T['slam'] + 0.1, 1.05))
        cx = lerp(W / 2, W / 2 - WM_W / 2 + WM_W * brand.WORDMARK_META['icon_frac'] / 2, settle)
        cy = lerp(H * 0.45, H / 2, settle)
        h = lerp(hook_h, WM_H * 1.18, settle)
        pose = 'slam' if t < T['slam'] + 0.45 else 'idle'
        if t >= T['hop']:          # hop out
            p = prog(t, T['hop'], T['hop'] + 0.55)
            cy -= math.sin(math.pi * min(1, p * 1.2)) * 260 - 900 * max(0, p - 0.5) ** 2
            cx += 500 * p
            pose = 'hop'
        return cx, cy, h, 1 + sq, 1 - sq, pose
    if t >= T['land'] - 0.35:      # the hero landing
        p = prog(t, T['land'] - 0.35, T['land'])
        cy = lerp(-H * 0.2, H * 0.43, core.ein(p))
        k = max(0.0, t - T['land'])
        sq = math.exp(-k * 8) * math.cos(k * 30) * 0.25 if t >= T['land'] else -0.12
        return W / 2, cy, H * (0.26 if PORTRAIT else 0.36), 1 + sq, 1 - sq, ('land' if t < T['land'] + 0.6 else 'cheer')
    return -9999, -9999, 0, 1, 1, None

def draw_zing(frame, t):
    cx, cy, h, sx, sy, pose = zing_xy(t)
    if not pose or h < 4: return
    if pose == 'idle' and 0 <= (t - T['blink']) * 60 < 8:                  # a blink from his own eyelids
        k = (t - T['blink']) * 60
        pose = 'blink2' if 2 <= k < 6 else 'blink1'
    img = brand.zing(pose, t)
    blur = 14 * (1 - prog(t, 0, T['slam'])) if t < T['slam'] else 0
    # contact shadow on the landing (he never floats)
    if t >= T['land'] - 0.12 and pose in ('land', 'cheer'):
        k = core.SCALE
        shadow = np.zeros(frame.shape[:2], np.float32)
        r = h * 0.36 * (0.6 + 0.4 * clamp(prog(t, T['land'] - 0.12, T['land'])))
        cv2.ellipse(shadow, (int(cx * k), int((cy + h * 0.45) * k)), (max(1, int(r * k)), max(1, int(h * 0.05 * k))), 0, 0, 360, 0.55, -1, cv2.LINE_AA)
        shadow = cv2.GaussianBlur(shadow, (0, 0), max(1.0, 9 * k))
        frame *= (1 - shadow[..., None])
    composite_sprite(frame, img, cx, cy + h * 0.5, h / 0.62, sx=sx, sy=sy, anchor=(0.5, brand.zing_box(pose if pose in brand.zing_poses() else 'idle')[3]), blur=blur)

@ui.cached(64)
def lockup_layer(reveal):
    """The S1 lock-up: the wordmark's letters, revealed left to right (reveal 0..200) behind the line's head.
    The icon part stays empty: Zing himself stands there."""
    wm = cv2.resize(WM, (int(WM_W), int(WM_H)), interpolation=cv2.INTER_AREA)
    wm[:, int(wm.shape[1] * reveal / 200):, 3] = 0
    wm[:, : int(wm.shape[1] * brand.WORDMARK_META['icon_frac']), 3] = 0
    layer = np.zeros((H, W, 4), np.uint8)
    x0, y0 = int(W / 2 - WM_W / 2), int(H / 2 - WM_H / 2)
    layer[y0:y0 + wm.shape[0], x0:x0 + wm.shape[1]] = wm
    return layer

# ── the scene ───────────────────────────────────────────────────────────────
def lockup_line(y_off=0.0):
    """THE line's path under the S1 lock-up (world points)."""
    y = S1.h / 2 + WM_H / 2 + 34 + y_off
    return S1.worlds([(S1.w / 2 - WM_W / 2 + u * WM_W, y) for u in [i / 30 for i in range(31)]])

def scene(t):
    frame = new_frame()
    stage(frame, base=brand.STAGE_BASE, glows=(((0.5, 0.42), LINE, 0.11, 0.62), ((0.15, 0.85), C['zing_hem'], 0.06, 0.5)), t=t)
    cam = camera_at(t)
    deferred = []
    focus = float(cam.to_cam(cam.target[None])[0, 2])
    # S1: the lock-up, revealed by the line (a mask that follows the line's head)
    rv = prog(t, T['reveal'], T['reveal'] + 0.55)
    if rv > 0 and t < T['fly'] + 1:
        composite_plane(frame, cam, S1, lockup_layer(int(eout(rv) * 200)), focus=focus)
        deferred.append(lambda fr, cam=cam, rv=rv: draw_line(fr, cam, lockup_line(), upto=eout(rv), color=LINE, width=7))
    # S2: the product
    if T['fly'] - 0.2 < t < T['type'] + 0.3:
        composite_plane(frame, cam, S2, product_layer(product_state(t)), focus=focus)
    # F: type, then the hero
    if t > T['type'] - 0.5:
        n = 1 + int(t >= at('all', 1, T['type'] + 0.7))
        a = clamp(1 - prog(t, T['land'] - 0.3, T['land']))
        if a > 0: composite_plane(frame, cam, F, type_layer(n), opacity=a, focus=focus)
        y = F.h * 0.40 + (1 if n == 2 else 0) * 150 + 110
        deferred.append(lambda fr, cam=cam, a=a: draw_line(fr, cam, F.worlds([(F.w * 0.18 + i / 30 * F.w * 0.64, y) for i in range(31)]),
                                                          upto=eout(prog(t, T['type'] - 0.1, T['type'] + 0.5)), color=LINE, width=8, opacity=a))
    draw_zing(frame, t)
    if t >= T['slam']:
        fx.shards(frame, t, T['slam'], W / 2, H * 0.45)
    return frame, deferred

def overlay(frame, t):
    """After the grade: the wordmark at the hero moment and on the end card (pixel-exact, no grain on it)."""
    if t >= T['land'] + 0.15:
        p = eout(prog(t, T['land'] + 0.15, T['land'] + 0.6))
        up = eout(prog(t, T['endcard'], T['endcard'] + 0.5)) * 80
        # the text part of the lock-up: Zing himself is the icon above it (never two Zings on screen)
        text = brand.wordmark_text()
        w = WM_W * 0.62; h = w * text.shape[0] / text.shape[1]
        wm = cv2.resize(text, (int(w), int(h)), interpolation=cv2.INTER_AREA)
        core.after_grade(frame, wm, W / 2 - w / 2, H * (0.62 if PORTRAIT else 0.66) - up, opacity=p)
        if t >= T['endcard'] + 0.2:
            L = ui.Layer(W, 120, ss=1)
            L.type((W / 2, 60), 'clipzing.com', 56, 'semibold', fill=C['lilac'], anchor='mm')
            core.after_grade(frame, L.rgba(), 0, H * (0.62 if PORTRAIT else 0.66) + h + 30 - up, opacity=prog(t, T['endcard'] + 0.2, T['endcard'] + 0.6))

# ── sound: one cue per visible move (the mix builds every sound from this list) ──
def cues():
    c = Cues()
    c.add(0.0, 'whoosh', size=0.5).add(T['slam'] - 0.01, 'impact', size=1.0).add(T['slam'], 'glass', size=0.7)
    c.add(T['reveal'], 'zip', size=0.6).add(T['blink'], 'tick', size=0.2).add(T['hop'], 'pop', size=0.5)
    c.add(T['fly'], 'whoosh', x=0.6, size=0.8)
    c.add(T['tap'], 'click', size=0.8).add(T['tap'] + 0.02, 'thump', size=0.3)
    c.add(T['type'] - 0.45, 'whoosh_down', x=-0.4, size=0.8)
    c.add(T['land'] - 0.33, 'falling', size=0.6).add(T['land'], 'thump', size=1.0)
    c.add(T['endcard'], 'whoosh', size=0.3)
    return c

def hero_cues():
    """Clipzing's sonic logo: after words, never on them."""
    ready_end = WORDS.after('ready') if WORDS else T['ready'] + 0.2
    return [('clip_ready', ready_end), ('published', T['land'] + 1.1)]

MUSIC = dict(style='mallet_pop', drop=None, lift=T['fly'], breath=T['land'] - 0.35, hit=T['land'])
