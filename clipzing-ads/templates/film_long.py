"""<TITLE>: a long-form Clipzing film (product tour / explainer), built with the clipzing-ads skill (adkit).

16:9 first (YouTube, landing page), with a real 9:16 re-layout. 45–120 s. Render talky tours at 30 fps:
    python3 TOOLKIT/render.py film.py all out/frames_16x9 --fmt 16x9 --fps 30 -j 8

Structure: a hook → CHAPTERS (data below) → the end card. Every chapter is a station in one world, flown to with
one continuous camera: a real Clipzing screen (library/screens: a browser in 16:9, a phone in 9:16), a chapter
super that rises with the voice, Zing presenting beside it with a pose matched to the line, and a chapter rail
that shows where we are. When voice/words.json exists, each chapter starts on its first word (`start_word`).
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
                        eback, einout, eout, lerp, new_frame, pose_mix, prog, shake_at, stage, v3)
from adkit.timeline import Cues, Words                                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
VO_OFF = 0.4
_wp = os.path.join(HERE, 'voice', 'words.json')
WORDS = Words(_wp, VO_OFF) if os.path.exists(_wp) else None

# ── chapters: (super, kicker, screen, zing pose, start_word, fallback start s) ──
# Screens: library/screens/{desktop,mobile}-<name>.png. Lines must be true (reference/product-facts.md).
CHAPTERS = [
    ('Paste a link.', 'YouTube link or upload, up to two hours', 'videos', 'present_right', 'paste', 3.0),
    ('It finds the moments.', 'Scored 0–100, best first', 'job', 'determined', 'finds', 9.0),
    ('Edit by the words.', 'Only Export renders', 'editor', 'focused', 'edit', 15.0),
    ('Pick a look.', 'Animated captions, timed to every word', 'preferences', 'present_left', 'look', 21.0),
    ('One calendar.', 'YouTube published · TikTok to drafts', 'calendar', 'talk', 'calendar', 27.0),
    ('Autopilot.', 'New uploads become clips', 'autopilot', 'cheer', 'autopilot', 33.0),
]
HOOK_END = 2.6
CH_START = []
for _c in CHAPTERS:
    try:
        CH_START.append(WORDS.t(_c[4]) - 0.15 if WORDS else _c[5])
    except KeyError:
        CH_START.append(_c[5])
END_T = (CH_START[-1] + 6.0) if not WORDS else max(CH_START[-1] + 5.0, WORDS.span()[1] + 0.6)
LAND = END_T + 0.3
END = LAND + 3.2

# stations: a gentle arc through depth, alternating sides
def station(i):
    side = -1 if i % 2 else 1
    return Plane(v3(side * 600 * (1 if not PORTRAIT else 0.4), -300 * i, -2600 * (i + 1)), yaw=-10 * side)
ST = [station(i) for i in range(len(CHAPTERS))]
HOOK = Plane(v3(0, 300, 1200))

def ch_of(t):
    k = 0
    for i, s in enumerate(CH_START):
        if t >= s - 0.4: k = i
    return k

# ── layers ──────────────────────────────────────────────────────────────────
@ui.cached(32)
def chapter_layer(i):
    """A chapter station: the real screen in a device + room for the super and Zing (W×H)."""
    title, kicker, scr_name, pose, _, _ = CHAPTERS[i]
    L = ui.Layer(W, H)
    if PORTRAIT:
        scr = brand.screen(f'mobile-{scr_name}')
        pw = 600; phh = pw * scr.shape[0] / scr.shape[1] + 40
        dev, _ = ui.phone(int(pw), int(phh), scr)
        L.paste(dev, (W - pw) / 2 + 120, H * 0.36)
    else:
        scr = brand.screen(f'desktop-{scr_name}')
        bw = 1180; bh = bw * scr.shape[0] / scr.shape[1] + 56
        dev, _ = ui.browser(int(bw), int(bh), scr, url=f'clipzing.com/dashboard')
        L.paste(dev, W - bw - 70, (H - bh) / 2 + 40)
    return L.rgba()

@ui.cached(64)
def super_rgba(i, which):
    title, kicker = CHAPTERS[i][:2]
    room = W * 0.86 if PORTRAIT else 560          # the space beside the screen (16:9) / across the top (9:16)
    if which == 0: return fx.type_rgba(title, ui.fit_size(title, room, 96 if PORTRAIT else 80, 'extrabold'))
    return fx.type_rgba(kicker, ui.fit_size(kicker, room, 40 if PORTRAIT else 32, 'semibold'), weight='semibold', fill=C['lilac'], tracking=0)

def rail_layer(k, p):
    """The chapter rail: one segment per chapter, the current one filling (keynote progress)."""
    L = ui.Layer(W, 40, ss=1)
    n = len(CHAPTERS); x0, x1 = W * 0.2, W * 0.8; gap = 10
    sw = (x1 - x0 - gap * (n - 1)) / n
    for i in range(n):
        xa = x0 + i * (sw + gap)
        L.rrect((xa, 16, xa + sw, 24), 4, fill=(60, 62, 84, 255))
        f = 1.0 if i < k else (p if i == k else 0.0)
        if f > 0: L.rrect((xa, 16, xa + sw * f, 24), 4, fill=C['accent'] + (255,))
    return L.rgba()

# ── camera ──────────────────────────────────────────────────────────────────
def camera_at(t):
    pose = HOOK.home(D)
    pose = pose_mix(pose, HOOK.home(D * 0.92), prog(t, 0, HOOK_END))
    for i, s in enumerate(CH_START):
        pose = pose_mix(pose, ST[i].home(D * 1.02), einout(prog(t, s - 0.45, s + 0.1)))
        nxt = CH_START[i + 1] if i + 1 < len(CH_START) else END_T
        pose = pose_mix(pose, ST[i].home(D * 0.95), prog(t, s + 0.1, nxt - 0.45) * 0.8)    # holds breathe
    pose = pose_mix(pose, ST[-1].home(D * 2.2), einout(prog(t, END_T - 0.3, LAND)))
    roll = sum((4 if i % 2 else -4) * math.sin(math.pi * prog(t, s - 0.45, s + 0.1)) for i, s in enumerate(CH_START))
    sx, sy = shake_at(t, 0.2, 18)
    return Camera(pose[0], pose[1], roll=roll, shake=(sx, sy))

# ── scene ───────────────────────────────────────────────────────────────────
def scene(t):
    frame = new_frame()
    stage(frame, base=brand.STAGE_BASE, glows=(((0.5, 0.4), LINE, 0.1, 0.65), ((0.12, 0.88), C['zing_hem'], 0.06, 0.5)), t=t)
    cam = camera_at(t)
    foc = float(cam.to_cam(cam.target[None])[0, 2])
    deferred = []
    k = ch_of(t)
    for i in (k - 1, k, k + 1):
        if 0 <= i < len(CHAPTERS) and t > CH_START[i] - 1.0 and t < LAND:
            composite_plane(frame, cam, ST[i], chapter_layer(i), focus=foc)
    # hook: a word slam + the wordmark (replace with your own hook)
    if t < HOOK_END + 0.4:
        fx.word_slam(frame, t, 0.2, 'TWO HOURS IN.', W / 2, H * 0.40, 130 if PORTRAIT else 170)
        fx.word_slam(frame, t, 1.0, 'SHORTS OUT.', W / 2, H * (0.50 if PORTRAIT else 0.58), 130 if PORTRAIT else 170, fill=C['lilac'])
    # chapter supers rise with the voice; Zing presents
    if HOOK_END < t < END_T:
        s = CH_START[k]
        a = clamp(prog(t, s, s + 0.35)) * (1 - prog(t, (CH_START[k + 1] if k + 1 < len(CH_START) else END_T) - 0.5,
                                                  (CH_START[k + 1] if k + 1 < len(CH_START) else END_T) - 0.2))
        if a > 0:
            ttl, kick = super_rgba(k, 0), super_rgba(k, 1)
            rise = (1 - eout(prog(t, s, s + 0.35))) * 50
            if PORTRAIT:   # centred across the top
                composite_sprite(frame, ttl, W / 2, H * 0.17 + rise, ttl.shape[0], opacity=a)
                composite_sprite(frame, kick, W / 2, H * 0.17 + ttl.shape[0] * 0.75 + rise * 1.4, kick.shape[0], opacity=a * prog(t, s + 0.15, s + 0.5))
            else:          # left-aligned in the column beside the browser
                composite_sprite(frame, ttl, 60 + ttl.shape[1] / 2, H * 0.3 + rise, ttl.shape[0], opacity=a)
                composite_sprite(frame, kick, 60 + kick.shape[1] / 2 + 6, H * 0.3 + ttl.shape[0] * 0.72 + rise * 1.4, kick.shape[0], opacity=a * prog(t, s + 0.15, s + 0.5))
            pose = CHAPTERS[k][3]
            zh = H * (0.17 if PORTRAIT else 0.3)
            zx, zy = (W * 0.2, H * 0.62) if PORTRAIT else (W * 0.2, H * 0.68)
            pop = eback(prog(t, s + 0.1, s + 0.45))
            img = brand.zing(pose, t - s)
            bx = brand.zing_box(pose)
            composite_sprite(frame, img, zx, zy + zh / 2, zh * pop / (bx[3] - bx[1]), anchor=(0.5, bx[3]), opacity=a)
    if t >= END_T - 0.2:   # Zing lands, the end card
        p = prog(t, END_T - 0.2, LAND)
        zh = H * (0.24 if PORTRAIT else 0.36)
        y = lerp(-H * 0.3, H * 0.42, core.ein(p))
        q = max(0.0, t - LAND)
        sq = math.exp(-q * 8) * math.cos(q * 30) * 0.2 if t >= LAND else -0.1
        pose = 'land' if q < 0.5 else 'cheer'
        bx = brand.zing_box(pose)
        composite_sprite(frame, brand.zing(pose, q), W / 2, y + zh / 2, zh / (bx[3] - bx[1]), sx=1 + sq, sy=1 - sq, anchor=(0.5, bx[3]))
    return frame, deferred

def overlay(frame, t):
    if HOOK_END - 0.4 < t < END_T:   # the chapter rail and a small lock-up, after the grade
        k = ch_of(t)
        nxt = CH_START[k + 1] if k + 1 < len(CH_START) else END_T
        core.after_grade(frame, rail_layer(k, clamp(prog(t, CH_START[k], nxt))), 0, H - (90 if not PORTRAIT else 150),
                         opacity=prog(t, HOOK_END - 0.4, HOOK_END))
    if t < HOOK_END + 0.3 or t > LAND + 0.1:
        wm = brand.wordmark() if t < HOOK_END + 0.3 else brand.wordmark_text()
        h = 60 if t < HOOK_END + 0.3 else (90 if PORTRAIT else 100)
        img = cv2.resize(wm, (int(wm.shape[1] * h / wm.shape[0]), h), interpolation=cv2.INTER_AREA)
        y = H * 0.07 if t < HOOK_END + 0.3 else H * (0.42 + (0.24 if PORTRAIT else 0.36) / 2) + 50
        op = prog(t, 0.3, 0.6) * (1 - prog(t, HOOK_END, HOOK_END + 0.3)) if t < HOOK_END + 0.3 else prog(t, LAND + 0.1, LAND + 0.5)
        core.after_grade(frame, img, W / 2 - img.shape[1] / 2, y, opacity=op)
        if t > LAND + 1.0:
            L = ui.Layer(W, 90, ss=1)
            L.type((W / 2, 45), 'clipzing.com', 48, 'semibold', fill=C['lilac'], anchor='mm')
            core.after_grade(frame, L.rgba(), 0, y + h + 24, opacity=prog(t, LAND + 1.0, LAND + 1.4))

def probe(t): return [(W / 2, H * 0.42 + (1 - prog(t, END_T - 0.2, LAND)) * 600)] if END_T - 0.2 < t < LAND + 0.2 else [(0, 0)]

def cues():
    c = Cues()
    c.add(0.0, 'suck', size=0.5).add(0.19, 'impact', size=1.0).add(0.98, 'impact', size=0.8)
    for i, s in enumerate(CH_START):
        c.add(s - 0.45, 'whoosh', x=(1 if i % 2 else -1) * 0.5, size=0.8)
        c.add(s + 0.02, 'pop', size=0.5).add(s + 0.15, 'tick', size=0.3).add(s + 0.12, 'tap', size=0.3)
    c.add(END_T - 0.3, 'falling', size=0.6).add(LAND, 'thump', size=1.0)
    return c

def hero_cues():
    return [('logo_sting', LAND), ('published', LAND + 1.1)]

MUSIC = dict(style='keynote', drop=CH_START[0], lift=CH_START[len(CH_START) // 2], breath=END_T - 0.3, hit=LAND, sting=False)
