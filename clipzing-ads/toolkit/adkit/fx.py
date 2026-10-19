"""adkit.fx: light, particles and type moves. Everything is deterministic in t (any frame can be rendered alone).

Allowed "wows" (one per scene, each resolving into a crisp frame held ≥ 0.4 s):
  strands rushing past (a hook), shards on a slam, a swarm that becomes a shape (the logo, Zing, a number),
  a light sweep across a surface, one anamorphic streak per film, a word slam on the spoken word.
Never: strobe montages, flares to white, RGB-split glitch, ring pulses, tumbling objects, dolly zoom.
"""
import math

import cv2
import numpy as np
from PIL import Image

from . import core
from .brand import font

# ── strands: lines of light rushing past the lens (the hook's approach) ─────
def strands(frame, cam, t, t0, t1, n=60, color=(0x97, 0x5A, 0xFD), spread=900, depth=6000, length=900, seed=3, width=3.0, opacity=1.0):
    """Light strands flying from depth toward the lens between t0 and t1 (world space, around the camera axis)."""
    p = core.prog(t, t0, t1)
    if p <= 0 or p >= 1 or opacity <= 0: return
    rng = np.random.default_rng(seed)
    base = cam.eye + cam.fw * 200
    for i in range(n):
        ang = rng.uniform(0, 2 * math.pi); rad = rng.uniform(0.25, 1) * spread
        off = rng.uniform(0, 1)
        z = (1 - ((p * 1.6 + off) % 1)) * depth
        x, y = math.cos(ang) * rad, math.sin(ang) * rad
        a = base + cam.rt * x + cam.up * y + cam.fw * z
        b = a + cam.fw * length
        fade = math.sin(math.pi * p) * opacity * (0.4 + 0.6 * rng.uniform())
        core.draw_line(frame, cam, np.array([b, a]), color=color, width=width, glow=0.6, head=False, opacity=fade)

# ── shards: a burst on a slam ───────────────────────────────────────────────
def shards(frame, t, at, cx, cy, n=26, color=(0xC4, 0xB5, 0xFD), speed=1500, life=0.55, size=14, seed=5):
    """Small bright fragments thrown out from (cx, cy) (full-size screen px) at time `at`, slowing and fading."""
    dt = t - at
    if dt < 0 or dt > life: return
    rng = np.random.default_rng(seed)
    k = core.SCALE
    for i in range(n):
        ang = rng.uniform(0, 2 * math.pi); sp = speed * rng.uniform(0.35, 1)
        d = sp * (1 - math.exp(-dt * 5)) / 5
        x = cx + math.cos(ang) * d; y = cy + math.sin(ang) * d + 260 * dt * dt
        a = (1 - dt / life) ** 1.5
        s = size * rng.uniform(0.5, 1.2) * (1 - dt / life * 0.5)
        rot = ang + dt * rng.uniform(-8, 8)
        pts = np.array([[math.cos(rot + q) * s * (1.6 if q == 0 else 0.7), math.sin(rot + q) * s * (1.6 if q == 0 else 0.7)] for q in (0, 2.2, 4.1)])
        poly = np.int32((pts + [x, y]) * k * 8)
        m = np.zeros(frame.shape[:2], np.float32)
        cv2.fillPoly(m, [poly], a, cv2.LINE_AA, shift=3)
        frame += m[..., None] * (np.array(color, np.float32) / 255)      # additive light: never a dark fleck over a bright subject

# ── the swarm: particles that become a shape ────────────────────────────────
def sample_mask(rgba, n, seed=1):
    """n points inside the opaque part of an RGBA image, in its pixel coords (for a swarm to land into)."""
    a = rgba[..., 3] > 128
    ys, xs = np.nonzero(a)
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(xs), size=min(n, len(xs)), replace=len(xs) < n)
    return np.stack([xs[idx], ys[idx]], axis=1).astype(np.float32)

def swarm(frame, t, t_form, targets_xy, origin_xy=None, n=None, color=(0xC4, 0xB5, 0xFD), dur=0.9, size=2.4, seed=9, scatter=700, opacity=1.0):
    """Particles fly from a scattered cloud (or from origin_xy) into targets (full-size screen px), landing at t_form.
    After landing they hold still: hand over to the real mark (cross-fade it in on the landing frame)."""
    tg = np.asarray(targets_xy, np.float32)
    n = n or len(tg)
    rng = np.random.default_rng(seed)
    start = (np.asarray(origin_xy, np.float32)[None] + rng.normal(0, scatter * 0.15, (n, 2))) if origin_xy is not None else \
        tg.mean(0)[None] + rng.normal(0, scatter, (n, 2))
    delay = rng.uniform(0, 0.35, n)
    p = np.clip((t - (t_form - dur) - delay * dur * 0.4) / (dur * (1 - 0.14)), 0, 1)
    e = 1 - (1 - p) ** 4
    curl = np.sin(p * math.pi)[:, None] * rng.normal(0, scatter * 0.25, (n, 2))
    xy = start + (tg[:n] - start) * e[:, None] + curl
    k = core.SCALE
    col = np.array(color, np.float32) / 255
    layer = np.zeros((core.RH, core.RW), np.float32)
    ok = (xy[:, 0] > 0) & (xy[:, 0] < core.W) & (xy[:, 1] > 0) & (xy[:, 1] < core.H)
    xi = np.int32(xy[ok] * k)
    np.add.at(layer, (np.clip(xi[:, 1], 0, core.RH - 1), np.clip(xi[:, 0], 0, core.RW - 1)), 1.0)
    layer = cv2.GaussianBlur(layer, (0, 0), max(0.6, size * k * 0.5))
    layer = np.clip(layer * 3.0, 0, 1.5)
    frame += layer[..., None] * col * opacity

# ── light sweep across a surface ────────────────────────────────────────────
def sweep_layer(rgba, p, width=0.18, strength=0.5, angle=20):
    """A soft band of light crossing an RGBA layer (only where it is opaque). p 0 → 1 moves it across."""
    h, w = rgba.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = math.radians(angle)
    u = (xx * math.cos(a) + yy * math.sin(a)) / (w * math.cos(a) + h * abs(math.sin(a)))
    c = -width + (1 + 2 * width) * p
    band = np.clip(1 - np.abs(u - c) / width, 0, 1) ** 2 * strength
    out = rgba.astype(np.float32).copy()
    m = out[..., 3:4] / 255
    out[..., :3] = np.clip(out[..., :3] + band[..., None] * 255 * m, 0, 255)
    return out.astype(np.uint8)

# ── the one anamorphic streak ───────────────────────────────────────────────
def anamorphic(frame, t, at, cx, cy, color=(255, 200, 120), length=1.2, life=0.45, strength=0.9):
    """A horizontal lens streak at (cx, cy) (full-size px) on one hero moment. Use once per film."""
    dt = t - at
    if dt < 0 or dt > life: return
    a = math.sin(math.pi * dt / life) * strength
    w = int(core.RW * length * (0.6 + 0.4 * dt / life)); h = max(2, int(10 * core.SCALE))
    m = np.zeros((core.RH, core.RW), np.float32)
    cv2.ellipse(m, (int(cx * core.SCALE), int(cy * core.SCALE)), (w // 2, h), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 6 * core.SCALE + 1)
    frame += m[..., None] * (np.array(color, np.float32) / 255) * a

# ── bokeh dust ──────────────────────────────────────────────────────────────
def dust(frame, t, n=40, color=(0x97, 0x5A, 0xFD), seed=11, opacity=0.5):
    """Slow out-of-focus motes drifting in the stage (depth without objects)."""
    rng = np.random.default_rng(seed)
    k = core.SCALE
    for i in range(n):
        x = (rng.uniform() * core.W + t * rng.uniform(-14, 14)) % core.W
        y = (rng.uniform() * core.H + t * rng.uniform(-22, -6)) % core.H
        r = rng.uniform(3, 14)
        a = opacity * rng.uniform(0.15, 0.6) * (0.6 + 0.4 * math.sin(t * rng.uniform(0.4, 1.2) + i))
        cv2.circle(frame, (int(x * k), int(y * k)), max(1, int(r * k)), tuple(float(c) / 255 * a * 0.35 for c in color), -1, cv2.LINE_AA)

# ── type ────────────────────────────────────────────────────────────────────
def type_rgba(text, size, weight='extrabold', family='jakarta', fill=(255, 255, 255), tracking=-0.02, pad=None, ss=2):
    """Render a line of type to a tight RGBA image (supersampled). Tracking in em."""
    f = font(size * ss, weight, family)
    widths = [f.getlength(c) for c in text]
    tw = sum(widths) + tracking * f.size * (len(text) - 1)
    asc, desc = f.getmetrics()
    pad = pad if pad is not None else int(size * 0.25)
    im = Image.new('RGBA', (int(tw + pad * 2 * ss), int(asc + desc + pad * 2 * ss)), (0, 0, 0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(im); x = pad * ss
    for c, w in zip(text, widths):
        d.text((x, pad * ss), c, font=f, fill=fill + (255,) if len(fill) == 3 else fill)
        x += w + tracking * f.size
    im = im.resize((max(1, im.width // ss), max(1, im.height // ss)), Image.LANCZOS)
    return np.asarray(im).copy()

def word_slam(frame, t, at, text, cx, cy, size, rush=0.18, settle=0.35, **kw):
    """A word rushing out of depth and slamming full-size ON the spoken word (land it a frame early).
    Returns the screen-space scale it is drawn at (for a matching shake/shards)."""
    if t < at - rush: return 0.0
    img = type_rgba(text, size, **kw)
    if t < at:   # approach: tiny and far → full, accelerating, blurred by its own speed
        p = core.prog(t, at - rush, at)
        s = 0.08 + 0.92 * core.ein(p)
        core.composite_sprite(frame, img, cx, cy, img.shape[0] * s, opacity=min(1, p * 2.5), blur=(1 - p) * 10)
        return s
    k = 1 + 0.06 * math.exp(-(t - at) * 14) * math.cos((t - at) * 40)   # a tiny elastic settle
    core.composite_sprite(frame, img, cx, cy, img.shape[0] * k)
    return k

def rise_mask(frame, t, at, text, x, y, size, dur=0.35, anchor='center', **kw):
    """Type rising into view through an invisible line (masked rise), keynote-super style."""
    if t < at: return
    img = type_rgba(text, size, **kw)
    h, w = img.shape[:2]
    p = core.eout(core.prog(t, at, at + dur))
    off = int(round((1 - p) * h))          # shifted down inside its own box; what falls below the box is clipped
    vis = np.zeros_like(img)
    if off < h: vis[off:] = img[:h - off]
    ox = x - w / 2 if anchor == 'center' else x
    core.composite_screen(frame, vis, ox, y - h / 2)
