"""The Link: a Clipzing ad, built with the clipzing-ads skill (adkit).

"Today, your podcast gets shorter. Paste one link. It finds the moments worth posting, frames the speaker, and
times every word. Ranked. Captioned. Ready. Clipzing."

Word slams on the spoken frame; a 16:9 podcast frame squeezes into a 9:16 clip (the hook IS the product); one link
travels through the product; the real caption engine times the narrator's words; the real "Generated Clips"
screen; the light gathers into Zing. One continuous camera. See brief/PROMPT.md.
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
from adkit.core import (D, H, PORTRAIT, W, Camera, Plane, clamp, composite_plane, composite_sprite,  # noqa: E402
                        draw_line, eback, ein, einout, eout, lerp, new_frame, pose_mix, prog, shake_at, stage, v3)
from adkit.timeline import Cues, Words                                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
END = 17.5
VO_OFF = -0.28                                   # the take's leading breath is trimmed: "Today" lands at 0.21 s
WORDS = Words(os.path.join(HERE, 'voice', 'words.json'), VO_OFF)
w = WORDS.t

T = {
    'today': w('today'), 'your': w('your'), 'podcast': w('podcast'), 'gets': w('gets'),
    'shorter': w('gets') + 0.33,                 # the real onset of "shorter" (0.1 s before Whisper's stamp)
    'paste': w('paste'), 'link': w('link'), 'it': w('it'), 'moments': w('moments'), 'posting': w('posting'),
    'frames': w('frames'), 'speaker': w('speaker'), 'and': w('and'), 'every': w('every'), 'word': w('word'),
    'ranked': w('ranked'), 'captioned': w('captioned'), 'ready': w('ready'), 'clipzing': w('clipzing'),
}
T['whipB'] = T['paste'] - 0.3                    # whip into the panel, landing on "Paste"
T['press'] = WORDS.end('link') + 0.12
T['whipC'] = T['it'] - 0.32
T['dive'] = T['frames'] - 0.2                    # the camera dives into the best moment
T['phone'] = T['and'] - 0.3                      # the reframed window becomes a phone
T['whipF'] = T['ranked'] - 0.32
T['breath'] = T['clipzing'] - 0.42
T['land'] = T['clipzing'] - 0.02                 # Zing lands ON the word (a frame early)
T['fanfare'] = WORDS.end('clipzing') + 0.25
T['endcard'] = 15.4

# ── stations (planes in one world) ──────────────────────────────────────────
A = Plane(v3(0, 0, 0))                                            # the hook: slams + the podcast frame
B = Plane(v3(0, -2600, -1400), pitch=-8)                           # "Generate clips" panel
Cst = Plane(v3(2900, -2900, -3800), yaw=-18)                      # the episode: waveform + moments
Fst = Plane(v3(-2600, -2400, -6200), yaw=14)                      # the real "Generated Clips" screen

def focus_of(cam): return float(cam.to_cam(cam.target[None])[0, 2])

# ── S1: the podcast frame that gets shorter ─────────────────────────────────
CARD_W = 1000 if PORTRAIT else 1080
CARD_H = CARD_W * 9 / 16
CARD_CY = H * (0.48 if PORTRAIT else 0.53)       # 9:16: everything stays inside the TikTok / Shorts safe area
ZING_X = 0.33                                   # Zing's x in the wide shot (fraction of its width)

def squeeze(t):
    return einout(prog(t, T['shorter'] - 0.02, T['shorter'] + 0.55))

@ui.cached(512)
def podcast_card(fi, q100, arrive100):
    """The wide podcast recording on S1; q = 0 full 16:9 → 1 a 9:16 window around Zing (the rest falls away)."""
    q, arrive = q100 / 100, arrive100 / 100
    L = ui.Layer(W, H)
    x0c, y0c = (W - CARD_W) / 2, CARD_CY - CARD_H / 2
    frame = brand.footage('wide', fi / 30, CARD_W, CARD_H)
    win_w = lerp(CARD_W, CARD_H * 9 / 16, q)
    cx = lerp(CARD_W / 2, CARD_W * ZING_X, q)
    wx0 = clamp(cx - win_w / 2, 0, CARD_W - win_w)
    dim = (frame.astype(np.float32) * (1 - 0.9 * q)).astype(np.uint8)
    rgba = np.dstack([dim, np.full(dim.shape[:2], int(255 * (1 - 0.85 * q)), np.uint8)])
    rgba[:, int(wx0):int(wx0 + win_w), :3] = frame[:, int(wx0):int(wx0 + win_w)]
    rgba[:, int(wx0):int(wx0 + win_w), 3] = 255
    L.shadow((x0c, y0c, x0c + CARD_W, y0c + CARD_H), 22, blur=40, opacity=0.6 * arrive)
    L.paste(rgba, x0c, y0c, opacity=arrive)
    L.rrect((x0c + wx0, y0c, x0c + wx0 + win_w, y0c + CARD_H), 18 * q + 4, outline=C['accent'] + (int(255 * min(1, q * 3) * arrive),), width=4)
    return L.rgba()

# ── S2: the Generate clips panel ────────────────────────────────────────────
LINK = 'youtube.com/watch?v=LongTable112'
def typed_n(t): return int(len(LINK) * clamp(prog(t, T['paste'] + 0.02, T['link'] + 0.12)))

@ui.cached(128)
def panel_layer(n, press100, caret):
    press = press100 / 100
    L = ui.Layer(W, H)
    k = 1.3 if PORTRAIT else 1.0                 # the phone needs bigger UI than the desktop
    pw = W * (0.92 if PORTRAIT else 0.62)
    ph = 520 * k
    x0, y0 = (W - pw) / 2, (H - ph) / 2 - (40 if PORTRAIT else 0)
    ui.surface(L, (x0, y0, x0 + pw, y0 + ph), r=32)
    wm = brand.wordmark()
    wmh = int(54 * k); wmw = wm.shape[1] * wmh / wm.shape[0]
    L.paste(cv2.resize(wm, (int(wmw), wmh), interpolation=cv2.INTER_AREA), x0 + 40, y0 + 38 * k)
    L.type((x0 + 40, y0 + 130 * k), 'Generate clips', int(60 * k), 'extrabold', fill=C['fg'], tracking=-0.02)
    L.type((x0 + 40, y0 + 205 * k), 'Paste a YouTube link or upload a video', int(30 * k), 'medium', fill=C['fg_muted'])
    iy = y0 + 270 * k; ih = 104 * k
    L.rrect((x0 + 36, iy, x0 + pw - 36, iy + ih), 22, fill=C['bg_sunken'] + (255,))
    L.rrect((x0 + 36, iy, x0 + pw - 36, iy + ih), 22, outline=C['accent'] + (200,) if n else (255, 255, 255, 40), width=2 if n else 1)
    ui.glyph(L, 'link', x0 + 36 + 50 * k, iy + ih / 2, 40 * k, C['fg_muted'] if not n else C['lilac'])
    s = LINK[:n] if n else 'https://youtube.com/…'
    size = ui.fit_size(LINK, pw - 72 - 110 * k, int(34 * k), 'semibold')
    tx = x0 + 36 + 92 * k
    L.type((tx, iy + ih / 2), s, size, 'semibold', fill=C['fg'] if n else C['fg_subtle'], anchor='lm')
    if caret and n < len(LINK):
        cx = tx + brand.font(size, 'semibold').getlength(s) + 4
        L.rrect((cx, iy + ih * 0.28, cx + 4, iy + ih * 0.72), 2, fill=C['lilac'] + (255,))
    by = iy + ih + 46 * k
    ui.button(L, (x0 + 36, by, x0 + pw - 36, by + 100 * k), 'Generate clips', press=press, size=int(40 * k), icon='plus')
    return L.rgba(), (x0 + pw / 2, by + 50 * k)

# ── S3: the episode, its moments, the scores ────────────────────────────────
MOMENTS = [  # (score, footage, frame, title) in the order they sit in the episode
    (88, 'closeup_onair', 40, 'Guest roasts my mic setup'),
    (94, 'wide', 10, 'Why consistency beats talent'),
    (79, 'closeup_laugh', 20, 'Reacting to my first episode'),
    (91, 'closeup_serious', 30, 'The 3am editing confession'),
]
RANK = sorted(range(4), key=lambda i: -MOMENTS[i][0])                # slot of each moment after sorting
WAVE_N = 140
WAVE = [0.2 + 0.8 * (core.hash01(i * 3.7) ** 1.6) * (0.55 + 0.45 * math.sin(i * 0.21) ** 2) for i in range(WAVE_N)]
SEG = [(0.08, 0.17), (0.31, 0.40), (0.55, 0.63), (0.78, 0.88)]      # where the 4 moments sit on the waveform
WAVE_Y = H * (0.2 if PORTRAIT else 0.22)

def slots():
    """Card boxes (x, y, w, h) for the 4 slots (layer coords)."""
    if PORTRAIT:
        cw, ch = 470, 560
        xs = [W / 2 - cw - 14, W / 2 + 14]
        return [(xs[k % 2], H * 0.36 + (k // 2) * (ch + 28), cw, ch) for k in range(4)]
    cw, ch = 400, 470
    x0 = W / 2 - 2 * cw - 1.5 * 28
    return [(x0 + k * (cw + 28), H * 0.42, cw, ch) for k in range(4)]

@ui.cached(512)
def episode_layer(scan100, lift100, ring100, sort100):
    scan, lift, ring, sort_ = scan100 / 100, lift100 / 100, ring100 / 100, sort100 / 100
    L = ui.Layer(W, H)
    wx0, wx1, wy = W * 0.06, W * 0.94, WAVE_Y
    L.type((wx0, wy - (150 if PORTRAIT else 130)), 'The Long Table · Ep. 112', 44 if PORTRAIT else 40, 'bold', fill=C['fg'])
    L.type((wx1, wy - (150 if PORTRAIT else 130)), '1:54:07', 40 if PORTRAIT else 36, 'semibold', fill=C['fg_muted'], anchor='ra')
    bw = (wx1 - wx0) / WAVE_N
    for i, a in enumerate(WAVE):
        u = i / WAVE_N
        lit = u < scan
        inseg = lift > 0 and any(s0 <= u < s1 for s0, s1 in SEG)
        col = C['accent'] if inseg else (C['lilac'] if lit else (58, 60, 82))
        h = max(6, 150 * a)
        L.rrect((wx0 + i * bw, wy - h / 2, wx0 + i * bw + bw * 0.62, wy + h / 2), bw * 0.31, fill=col + (255 if (lit or inseg) else 200,))
    if 0 < scan < 1:
        sx = wx0 + (wx1 - wx0) * scan
        L.rrect((sx - 3, wy - 110, sx + 3, wy + 110), 3, fill=(255, 255, 255, 230))
    S = slots()
    for i, (score, foot, fi, title) in enumerate(MOMENTS):
        p = eback(clamp((lift - i * 0.12) / 0.6))
        if p <= 0: continue
        sx0, sy0, cw, ch = S[i]
        tx0, ty0, _, _ = S[RANK.index(i)]
        s = einout(sort_)
        lane = (-1 if RANK.index(i) < i else 1 if RANK.index(i) > i else 0)   # risers arc over, fallers dip under
        x = lerp(sx0, tx0, s); y = lerp(sy0, ty0, s) + math.sin(math.pi * s) * 90 * lane
        x += math.sin(math.pi * s) * 40 * lane
        segx = wx0 + (wx1 - wx0) * (SEG[i][0] + SEG[i][1]) / 2
        x = lerp(segx - cw / 2, x, min(1, p)); y = lerp(wy - ch / 2, y, min(1, p))
        sc = lerp(0.25, 1.0, min(1.05, p))
        bx0, by0 = x + cw * (1 - sc) / 2, y + ch * (1 - sc) / 2
        bw_, bh_ = cw * sc, ch * sc
        ui.surface(L, (bx0, by0, bx0 + bw_, by0 + bh_), r=26 * sc, alpha=int(255 * min(1, p * 1.4)))
        th = bw_ - 28 * sc; thh = th * 9 / 16
        img = brand.footage(foot, fi / 30, max(8, th), max(8, thh))
        L.paste(img, bx0 + 14 * sc, by0 + 14 * sc, opacity=min(1, p * 1.4))
        if p > 0.6:
            r = 52 * sc
            ui.score_badge(L, bx0 + 14 * sc + r + 6, by0 + 14 * sc + thh + r + 16, score, r=r, p=eout(clamp((ring - i * 0.08) / 0.6)))
            L.type((bx0 + 14 * sc + 2 * r + 28, by0 + 14 * sc + thh + r + 16), 'Score', int(30 * sc), 'semibold', fill=C['fg_muted'], anchor='lm')
            ws_ = title.split(); half = (len(ws_) + 1) // 2
            for j, line in enumerate((' '.join(ws_[:half]), ' '.join(ws_[half:]))):
                L.type((bx0 + 20 * sc, by0 + 14 * sc + thh + 2 * r + 46 * sc + j * 40 * sc), line, int(32 * sc), 'bold', fill=C['fg'])
    return L.rgba()

def best_card_box():
    """The best moment's thumbnail after sorting (layer coords): the dive target."""
    sx0, sy0, cw, ch = slots()[0]
    th = cw - 28
    return (sx0 + 14, sy0 + 14, sx0 + 14 + th, sy0 + 14 + th * 9 / 16)

# S4/S5: the best moment, a plane exactly over its thumbnail (so the dive is one seamless zoom)
_bx0, _by0, _bx1, _by1 = best_card_box()
_TH_W = _bx1 - _bx0
Dst = Plane(Cst.world((_bx0 + _bx1) / 2, (_by0 + _by1) / 2) + Cst.n * 2, yaw=-18, size=(_TH_W, _TH_W * H / W))
D_DIST = D * _TH_W / W                          # at this distance the thumbnail fills the frame width

def reframe(t): return einout(prog(t, T['speaker'] - 0.25, T['speaker'] + 0.45))
def phone_p(t): return einout(prog(t, T['phone'], T['phone'] + 0.5))
CAP_DIR = os.path.join(HERE, 'assets', 'captions_raw', 'caption_job')
CAPS = sorted(f for f in os.listdir(CAP_DIR) if f.endswith('.png'))
CAP_T0 = WORDS.t('and') - 0.12                   # the caption job was rendered from this film time (assets/caption_job.json)

@ui.cached(256)
def moment_layer(fi, rf100, ph100):
    """The best moment filling the frame (16:9), a 9:16 window that finds Zing, then the window becomes a phone.
    W×H layer on Dst; at D_DIST it maps 1:1 onto the screen. Returns (rgba, screen box)."""
    rf, ph = rf100 / 100, ph100 / 100
    L = ui.Layer(W, H)
    vw, vh = W, W * 9 / 16
    vy0 = (H - vh) / 2
    full = brand.footage('wide', fi / 30, vw, vh)
    win_h = vh; win_w = win_h * 9 / 16
    cx = lerp(vw / 2, vw * ZING_X, rf)
    wx0 = clamp(cx - win_w / 2, 0, vw - win_w)
    dim = float(lerp(1.0, 0.22, rf) * (1 - ph))
    if dim > 0.01:
        L.paste((full.astype(np.float32) * dim).astype(np.uint8), 0, vy0)
    scr_h = lerp(win_h, H * (0.78 if PORTRAIT else 0.86), ph); scr_w = scr_h * 9 / 16
    scx = lerp(wx0 + win_w / 2, W / 2, ph); scy = lerp(vy0 + vh / 2, H / 2, ph)
    crop = full[:, int(wx0):int(wx0 + win_w)]
    crop = cv2.resize(crop, (max(2, int(scr_w)), max(2, int(scr_h))), interpolation=cv2.INTER_CUBIC)
    sx0, sy0 = scx - scr_w / 2, scy - scr_h / 2
    if ph > 0.01:
        bz = 22 * ph
        L.shadow((sx0 - bz, sy0 - bz, sx0 + scr_w + bz, sy0 + scr_h + bz), 60, blur=50, offset=(0, 30), opacity=0.7 * ph)
        L.gradient_rrect((sx0 - bz, sy0 - bz, sx0 + scr_w + bz, sy0 + scr_h + bz), 60 * ph + 4, (58, 56, 72), (22, 22, 30), alpha=int(255 * ph))
    rr = int(48 * ph + 4)
    m = np.zeros(crop.shape[:2], np.uint8)
    cv2.rectangle(m, (rr, 0), (crop.shape[1] - rr, crop.shape[0]), 255, -1)
    cv2.rectangle(m, (0, rr), (crop.shape[1], crop.shape[0] - rr), 255, -1)
    for ccx, ccy in ((rr, rr), (crop.shape[1] - rr, rr), (rr, crop.shape[0] - rr), (crop.shape[1] - rr, crop.shape[0] - rr)):
        cv2.circle(m, (ccx, ccy), rr, 255, -1, cv2.LINE_AA)
    L.paste(np.dstack([crop, m]), sx0, sy0)
    if ph < 0.99:
        L.rrect((sx0, sy0, sx0 + scr_w, sy0 + scr_h), rr, outline=C['accent'] + (int(255 * min(1, rf * 2) * (1 - ph)),), width=4)
    return L.rgba(), (sx0, sy0, scr_w, scr_h)

def with_captions(lay, box, t):
    """The REAL caption frames, inside the phone screen."""
    sx0, sy0, sw, shh = box
    ci = min(len(CAPS) - 1, max(0, int((t - CAP_T0) * 60)))
    cap = core.load_rgba(os.path.join(CAP_DIR, CAPS[ci]))
    cap = cv2.resize(cap, (int(sw), int(shh)), interpolation=cv2.INTER_AREA)
    a = cap[..., 3:4].astype(np.float32) / 255
    y0, x0 = int(sy0), int(sx0)
    y1, x1 = min(lay.shape[0], y0 + cap.shape[0]), min(lay.shape[1], x0 + cap.shape[1])
    out = lay.copy()
    reg = out[y0:y1, x0:x1].astype(np.float32)
    a = a[: y1 - y0, : x1 - x0]
    reg[..., :3] = reg[..., :3] * (1 - a) + cap[: y1 - y0, : x1 - x0, :3] * a
    out[y0:y1, x0:x1] = reg.astype(np.uint8)
    return out

# ── S6: the real "Generated Clips" screen ───────────────────────────────────
@ui.cached(4)
def job_screen_layer():
    L = ui.Layer(W, H)
    if PORTRAIT:
        scr = brand.screen('mobile-job')
        pw = 780; phh = pw * scr.shape[0] / scr.shape[1] + 40
        phone, _ = ui.phone(int(pw), int(phh), scr)
        L.paste(phone, (W - pw) / 2, H * 0.33)
        return L.rgba()
    scr = brand.screen('desktop-job')
    bw_ = 1120; bh_ = bw_ * scr.shape[0] / scr.shape[1] + 56
    win, _ = ui.browser(int(bw_), int(bh_), scr, url='clipzing.com/dashboard/jobs')
    L.paste(win, 70, (H - bh_) / 2)
    return L.rgba()

SUPERS = [('Ranked.', 'ranked'), ('Captioned.', 'captioned'), ('Ready.', 'ready')]

# ── the camera: one continuous flight ───────────────────────────────────────
def camera_at(t):
    pose = pose_mix(A.home(D * 0.9), A.home(D * 1.0), einout(prog(t, 0.0, T['shorter'])))
    pose = pose_mix(pose, A.home(D * 0.94), einout(prog(t, T['shorter'], T['whipB'])))
    pose = pose_mix(pose, B.home(D * 1.0), einout(prog(t, T['whipB'], T['whipB'] + 0.42)))
    pose = pose_mix(pose, B.home(D * 0.93), prog(t, T['whipB'] + 0.42, T['whipC']))
    pose = pose_mix(pose, Cst.home(D * 1.06), einout(prog(t, T['whipC'], T['whipC'] + 0.45)))
    pose = pose_mix(pose, Cst.home(D * 1.0), prog(t, T['whipC'] + 0.45, T['dive']))
    pose = pose_mix(pose, Dst.home(D_DIST), einout(prog(t, T['dive'], T['dive'] + 0.5)))
    pose = pose_mix(pose, Dst.home(D_DIST * 0.97), prog(t, T['dive'] + 0.5, T['whipF']) * 0.7)
    pose = pose_mix(pose, Fst.home(D * 1.0), einout(prog(t, T['whipF'], T['whipF'] + 0.45)))
    pose = pose_mix(pose, Fst.home(D * 0.95), prog(t, T['whipF'] + 0.45, T['breath']))
    pose = pose_mix(pose, Fst.home(D * 1.6), ein(prog(t, T['breath'], T['land'] + 0.2)))
    whips = [(T['whipB'], 0.42, -7), (T['whipC'], 0.45, 8), (T['whipF'], 0.45, -8)]
    roll = sum(r * math.sin(math.pi * prog(t, a, a + d)) for a, d, r in whips)
    sh = [shake_at(t, T[k], amp) for k, amp in (('today', 22), ('podcast', 14), ('shorter', 30), ('ranked', 12), ('land', 20))]
    return Camera(pose[0], pose[1], roll=roll, shake=(sum(s[0] for s in sh), sum(s[1] for s in sh)))

# ── slams (screen space, on the spoken frame) ───────────────────────────────
def slam_list():
    if PORTRAIT:
        return [('TODAY,', 'today', W / 2, H * 0.30, 190, 'your'),
                ('YOUR', 'your', W / 2, H * 0.185, 96, 'whipB'), ('PODCAST', 'podcast', W / 2, H * 0.255, 170, 'whipB'),
                ('GETS', 'gets', W / 2, H * 0.638, 104, 'whipB'), ('SHORTER.', 'shorter', W / 2, H * 0.735, 180, 'whipB')]
    return [('TODAY,', 'today', W / 2, H * 0.5, 260, 'your'),
            ('YOUR PODCAST', 'your', W / 2, H * 0.13, 120, 'whipB'),
            ('GETS', 'gets', W * 0.33, H * 0.9, 116, 'whipB'), ('SHORTER.', 'shorter', W * 0.6, H * 0.9, 140, 'whipB')]

def draw_slams(frame, t):
    for text, k, x, y, size, gone in slam_list():
        at = T[k] - 1 / 60
        if t < at - 0.2 or t > T[gone] + 0.25: continue
        out = prog(t, T[gone], T[gone] + 0.2)
        if out > 0:
            img = fx.type_rgba(text, size)
            composite_sprite(frame, img, x, y - 260 * ein(out), img.shape[0] * (1 + 0.3 * out), opacity=1 - out, blur=8 * out)
            continue
        fx.word_slam(frame, t, at, text, x, y, size)
        if k in ('today', 'shorter'):
            fx.shards(frame, t, at, x, y, n=22 if k == 'shorter' else 14, size=12)

# ── Zing and the swarm (S7) ─────────────────────────────────────────────────
ZING_H = H * (0.24 if PORTRAIT else 0.40)
ZC = (W / 2, H * (0.42 if PORTRAIT else 0.40))
_land = brand.zing('land')
_box = brand.zing_box('land')
def _targets():
    a = _land
    s = ZING_H / ((_box[3] - _box[1]) * a.shape[0])
    pts = fx.sample_mask(a, 2600, seed=4)
    return np.stack([ZC[0] + (pts[:, 0] - a.shape[1] * 0.5) * s, ZC[1] + (pts[:, 1] - a.shape[0] * (_box[1] + _box[3]) / 2) * s], 1)
TARGETS = _targets()

def draw_hero(frame, t):
    if t < T['breath'] - 0.1: return
    if t < T['land']:
        fx.swarm(frame, t, T['land'], TARGETS, origin_xy=(W / 2, H * 0.6), color=C['lilac'], dur=T['land'] - T['breath'] + 0.05,
                 scatter=900 if PORTRAIT else 1200)
        return
    k = t - T['land']
    sq = math.exp(-k * 8) * math.cos(k * 30) * 0.2
    pose = 'land' if k < 0.55 else 'cheer'
    img = brand.zing(pose, k)
    bx = brand.zing_box(pose)
    s = core.SCALE
    foot = ZC[1] + ZING_H / 2
    sh = np.zeros(frame.shape[:2], np.float32)
    cv2.ellipse(sh, (int(ZC[0] * s), int((foot + 8) * s)), (max(1, int(ZING_H * 0.42 * s)), max(1, int(ZING_H * 0.06 * s))), 0, 0, 360, 0.5, -1, cv2.LINE_AA)
    frame *= (1 - cv2.GaussianBlur(sh, (0, 0), max(1.0, 10 * s))[..., None])
    composite_sprite(frame, img, ZC[0], foot, ZING_H / (bx[3] - bx[1]), sx=1 + sq, sy=1 - sq, anchor=(0.5, bx[3]))
    if k < 0.25:
        fx.swarm(frame, t, T['land'], TARGETS, color=C['lilac'], opacity=1 - k / 0.25)

# ── the scene ───────────────────────────────────────────────────────────────
def scene(t):
    frame = new_frame()
    stage(frame, base=brand.STAGE_BASE, glows=(((0.5, 0.42 + 0.06 * math.sin(t * 0.4)), LINE, 0.12, 0.65),
                                                ((0.15, 0.9), C['zing_hem'], 0.07, 0.5), ((0.88, 0.12), C['violet'], 0.05, 0.4)), t=t)
    cam = camera_at(t)
    foc = focus_of(cam)
    deferred = []
    fi = int(t * 30)
    if t < T['whipB'] + 0.5:                                                    # S1
        arrive = clamp(prog(t, T['podcast'] - 0.12, T['podcast'] + 0.08))
        if arrive > 0:
            composite_plane(frame, cam, A, podcast_card(fi % 300, int(squeeze(t) * 100), int(eback(arrive) * 100)), focus=foc)
    if T['whipB'] - 0.3 < t < T['whipC'] + 0.6:                                 # S2
        press = clamp(1 - abs(t - T['press'] - 0.06) / 0.12)
        lay, btn = panel_layer(typed_n(t), int(press * 100), int(t * 3) % 2 == 0)
        composite_plane(frame, cam, B, lay, focus=foc)
        if t > T['press']:   # the button's light leaves as the line, into the episode
            p0, p1 = B.world(*btn), Cst.world(W * 0.06, WAVE_Y)
            mid = (p0 + p1) / 2 + v3(0, 900, 300)
            pts = np.array([core.catmull([p0, mid, p1], s) for s in np.linspace(0, 1, 40)])
            up = eout(prog(t, T['press'], T['whipC'] + 0.4))
            deferred.append(lambda fr, cam=cam, pts=pts, up=up: draw_line(fr, cam, pts, upto=up, start=max(0, up - 0.45), color=LINE, width=10))
    if T['whipC'] - 0.3 < t < T['dive'] + 0.55:                                 # S3
        scan = prog(t, T['it'] - 0.05, T['moments'] + 0.1)
        lift = prog(t, T['moments'] - 0.05, T['moments'] + 0.6)
        ring = prog(t, T['posting'] - 0.1, T['posting'] + 0.6)
        srt = prog(t, T['posting'] + 0.45, T['frames'] - 0.25)
        op = 1 - prog(t, T['dive'] + 0.3, T['dive'] + 0.5)
        composite_plane(frame, cam, Cst, episode_layer(int(scan * 100), int(lift * 100), int(ring * 100), int(srt * 100)), focus=foc, opacity=op)
    if T['dive'] + 0.15 < t < T['whipF'] + 0.5:                                 # S4 + S5
        lay, box = moment_layer(fi % 300, int(reframe(t) * 100), int(phone_p(t) * 100))
        if t >= CAP_T0 and phone_p(t) > 0.98: lay = with_captions(lay, box, t)
        composite_plane(frame, cam, Dst, lay, opacity=prog(t, T['dive'] + 0.15, T['dive'] + 0.45), focus=foc)
    if T['whipF'] - 0.25 < t < T['land'] + 0.3:                                 # S6
        lay = job_screen_layer()
        if T['ranked'] - 0.05 < t < T['ranked'] + 0.6:
            lay = fx.sweep_layer(lay, prog(t, T['ranked'] - 0.05, T['ranked'] + 0.6), width=0.14, strength=0.35)
        composite_plane(frame, cam, Fst, lay, opacity=1 - prog(t, T['breath'], T['land'] - 0.05), focus=foc)
    draw_slams(frame, t)
    if T['ranked'] - 0.2 < t < T['breath'] + 0.2:
        o = 1 - prog(t, T['breath'] - 0.15, T['breath'] + 0.2)
        for i, (txt, k) in enumerate(SUPERS):
            at = T[k] - 1 / 60
            if t < at - 0.2: continue
            if PORTRAIT: x, y, size = W / 2, H * (0.145 + i * 0.07), 108
            else: x, y, size = W * 0.835, H * (0.3 + i * 0.16), 112
            if t < at + 0.3: fx.word_slam(frame, t, at, txt, x, y, size)
            else:
                img = fx.type_rgba(txt, size)
                composite_sprite(frame, img, x, y, img.shape[0], opacity=o)
        if t > T['ready'] + 0.05:
            p = eback(prog(t, T['ready'] + 0.05, T['ready'] + 0.35))
            L = ui.Layer(160, 160)
            L.d.ellipse(L.S(10, 10, 150, 150), fill=C['success'] + (255,))
            ui.glyph(L, 'check', 80, 82, 90, (255, 255, 255))
            cx, cy = (W / 2 + 220, H * 0.285) if PORTRAIT else (W * 0.835 + 190, H * 0.62)
            composite_sprite(frame, L.rgba(), cx, cy, 110 * p, opacity=min(1, p) * o)
    draw_hero(frame, t)
    return frame, deferred

def probe(t):
    out = [(x, y + (1 - core.ein(prog(t, T[k] - 0.2, T[k]))) * 300) for _, k, x, y, _, _ in slam_list() if abs(t - T[k]) < 0.25]
    if T['breath'] < t < T['land'] + 0.3: out.append((ZC[0], ZC[1] - 400 * (1 - prog(t, T['breath'], T['land']))))
    return out or [(0, 0)]

# ── after the grade: the marks ──────────────────────────────────────────────
WM = brand.wordmark()
WM_TEXT = brand.wordmark_text()
def overlay(frame, t):
    a = prog(t, 0.35, 0.6) * (1 - prog(t, T['whipB'], T['whipB'] + 0.25))      # the brand inside the first second
    if a > 0:
        h = 64 if PORTRAIT else 56
        wmi = cv2.resize(WM, (int(WM.shape[1] * h / WM.shape[0]), h), interpolation=cv2.INTER_AREA)
        core.after_grade(frame, wmi, W / 2 - wmi.shape[1] / 2, H * (0.118 if PORTRAIT else 0.03), opacity=a)
    if t >= T['land'] + 0.12:
        p = eout(prog(t, T['land'] + 0.12, T['land'] + 0.5))
        up = eout(prog(t, T['endcard'], T['endcard'] + 0.5)) * 40
        tw = 520 if PORTRAIT else 560
        th = int(tw * WM_TEXT.shape[0] / WM_TEXT.shape[1])
        img = cv2.resize(WM_TEXT, (tw, th), interpolation=cv2.INTER_AREA)
        y = ZC[1] + ZING_H / 2 + 60 - up
        core.after_grade(frame, img, W / 2 - tw / 2, y, opacity=p)
        if t >= T['endcard']:
            L = ui.Layer(W, 100, ss=1)
            L.type((W / 2, 50), 'clipzing.com', 52, 'semibold', fill=C['lilac'], anchor='mm')
            core.after_grade(frame, L.rgba(), 0, y + th + 30, opacity=prog(t, T['endcard'] + 0.15, T['endcard'] + 0.5))

# ── sound: a cue for every visible move ─────────────────────────────────────
def cues():
    c = Cues()
    for text, k, x, y, size, _ in slam_list():
        big = k in ('today', 'shorter', 'podcast')
        c.add(T[k] - 0.25, 'suck', x=(x / W - 0.5) * 2, size=0.5 if big else 0.3)
        c.add(T[k] - 1 / 60, 'impact' if big else 'thump', x=(x / W - 0.5) * 2, size=1.0 if k == 'shorter' else 0.7 if big else 0.5)
    c.add(T['podcast'] - 0.12, 'whoosh', size=0.5)
    c.add(T['shorter'] + 0.05, 'zip', size=0.6).add(T['shorter'] + 0.5, 'lock', size=0.5)
    c.add(T['whipB'], 'whoosh_down', size=0.9)
    n = len(LINK); a, b = T['paste'] + 0.02, T['link'] + 0.12
    for i in range(0, n, 2): c.add(a + (b - a) * i / n, 'key', x=-0.2 + 0.4 * i / n, size=0.45)
    c.add(T['press'], 'click', size=0.9).add(T['press'] + 0.01, 'thump', size=0.35)
    c.add(T['press'] + 0.08, 'zip', x=0.4, size=0.8).add(T['whipC'], 'whoosh', x=0.5, size=0.9)
    c.add(T['it'] - 0.05, 'riser', size=0.25)
    for i in range(4):
        c.add(T['moments'] + i * 0.07, 'pop', x=-0.6 + 0.4 * i, size=0.6)
        for j in range(3): c.add(T['posting'] - 0.1 + i * 0.05 + j * 0.15, 'tick', x=-0.6 + 0.4 * i, size=0.3)
    c.add(T['posting'] + 0.5, 'whoosh', size=0.4).add(T['frames'] - 0.3, 'glass', size=0.4)
    c.add(T['dive'], 'whoosh_down', size=0.8).add(T['speaker'] - 0.2, 'zip', x=-0.3, size=0.4).add(T['speaker'] + 0.42, 'lock', size=0.35)
    c.add(T['phone'], 'whoosh', size=0.5)
    for k in ('and', 'every', 'word'): c.add(T[k] - 0.01, 'tap', size=0.35)
    c.add(T['whipF'], 'whoosh_down', x=-0.5, size=0.9)
    for k in ('ranked', 'captioned', 'ready'):
        c.add(T[k] - 0.2, 'suck', size=0.3).add(T[k] - 1 / 60, 'impact', size=0.55)
    c.add(T['ranked'], 'shimmer', size=0.5).add(T['ready'] + 0.06, 'pop', size=0.6)
    c.add(T['breath'] - 0.05, 'whoosh_down', size=0.5).add(T['breath'], 'shimmer', size=0.8)
    c.add(T['land'], 'thump', size=1.0).add(T['land'] + 0.6, 'flutter', size=0.5)
    c.add(T['endcard'], 'whoosh', size=0.3)
    return c

def hero_cues():
    # the sting is split around the brand name: the sub hit lands ON "Clipzing" with Zing, the chord blooms after it
    return [('clip_ready', WORDS.after('ready', gap=0.18)), ('logo_hit', T['land']), ('logo_chord', WORDS.end('clipzing') + 0.04),
            ('published', T['fanfare'] + 0.35)]

MUSIC = dict(style='keynote', drop=T['paste'], lift=T['ranked'], breath=T['breath'], hit=T['land'], sting=False)
