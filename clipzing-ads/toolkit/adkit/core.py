"""adkit.core: the 2.5D renderer.

A real pinhole camera flies through a world of flat "stations" (planes). Each station has a home pose that maps it
1:1 onto the screen, so a layer drawn at screen size reads pixel-sharp when the camera rests on it. Layers are drawn
in Pillow, warped with OpenCV, composited premultiplied in float32. One continuous camera, no hard cuts needed.

Configuration comes from the environment so parallel render workers agree:
  FMT=9x16|16x9|1x1   SCALE=0.5 (previews)   FPS=60|30   END=<seconds>
"""
import math
import os

import cv2
import numpy as np
from PIL import Image

FMT = os.environ.get('FMT', '9x16')
PORTRAIT = FMT == '9x16'
SQUARE = FMT == '1x1'
SCALE = float(os.environ.get('SCALE', '1'))
FPS = int(os.environ.get('FPS', '60'))
END = float(os.environ.get('END', '20'))
W, H = (1080, 1920) if PORTRAIT else (1080, 1080) if SQUARE else (1920, 1080)
RW, RH = int(round(W * SCALE)), int(round(H * SCALE))   # render size (previews render smaller)
D = 1600.0                                              # home distance: f = D maps a station 1:1

# ── maths ───────────────────────────────────────────────────────────────────
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b):
    """0 before a, 1 after b, linear between. The basic building block of every timing."""
    return clamp((t - a) / (b - a)) if b != a else float(t >= b)
def lerp(a, b, p): return a + (b - a) * p
def eout(p): return 1 - (1 - p) ** 3
def ein(p): return p ** 3
def einout(p): return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2
def eexpo(p): return 1.0 if p >= 1 else 1 - 2 ** (-10 * p)
def eback(p, s=1.7):
    """Ease out with a small overshoot: for things that land."""
    if p <= 0: return 0.0
    if p >= 1: return 1.0
    return 1 + (s + 1) * (p - 1) ** 3 + s * (p - 1) ** 2
def spring(t, k=18.0, d=5.0):
    """Damped spring 0 → 1 (overshoots), t in seconds since release."""
    if t <= 0: return 0.0
    return 1 - math.exp(-d * t) * math.cos(k * t)
def pulse(t, at, dur=0.25):
    """A 0 → 1 → 0 bump centred on a hit: for glows, scale kicks, shakes."""
    p = prog(t, at, at + dur)
    return math.sin(math.pi * p) if 0 < p < 1 else 0.0
def smooth_noise(t, seed=0, freq=1.0):
    """Cheap smooth 1D noise in [-1, 1] (sum of incommensurate sines): drift, handheld breathing."""
    s = seed * 12.9898
    return (math.sin(t * freq * 1.31 + s) * 0.5 + math.sin(t * freq * 2.17 + s * 1.7) * 0.3 + math.sin(t * freq * 3.73 + s * 2.3) * 0.2)
def v3(x, y, z): return np.array([x, y, z], dtype=np.float64)
def norm(v): return v / (np.linalg.norm(v) + 1e-12)
def hash01(n):
    x = math.sin(n * 127.1 + 311.7) * 43758.5453
    return x - math.floor(x)

# ── the camera ──────────────────────────────────────────────────────────────
class Camera:
    """eye → target, optional roll (degrees) and a screen-space shake (pixels at full size)."""
    def __init__(self, eye, target, roll=0.0, f=D, shake=(0.0, 0.0)):
        self.eye, self.target, self.f, self.shake = np.asarray(eye, float), np.asarray(target, float), f, shake
        fw = norm(self.target - self.eye)
        rt = norm(np.cross(fw, [0, 1, 0]))
        up = np.cross(rt, fw)
        c, s = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        self.fw, self.rt, self.up = fw, rt * c + up * s, up * c - rt * s

    def to_cam(self, pts):
        d = np.atleast_2d(pts) - self.eye
        return np.stack([d @ self.rt, d @ self.up, d @ self.fw], axis=1)

    def project(self, pts):
        """World points → render-pixel xy (N×2) and camera depth (N)."""
        c = self.to_cam(pts)
        z = np.maximum(c[:, 2], 1e-3)
        k = self.f * SCALE / z
        x = RW / 2 + c[:, 0] * k + self.shake[0] * SCALE
        y = RH / 2 - c[:, 1] * k + self.shake[1] * SCALE
        return np.stack([x, y], axis=1), c[:, 2]

def proj1(cam, p):
    """One world point → (x, y) in render pixels and its camera depth."""
    xy, z = cam.project(np.asarray(p, float)[None])
    return float(xy[0, 0]), float(xy[0, 1]), float(z[0])

def screen_scale(cam, p):
    """How many render pixels one world unit covers at point p (1.0 × SCALE at a station's home pose)."""
    return cam.f * SCALE / max(1e-3, float(cam.to_cam(np.asarray(p, float)[None])[0, 2]))

def pose_mix(a, b, p):
    """Blend two (eye, target) poses."""
    return (lerp(np.asarray(a[0], float), np.asarray(b[0], float), p), lerp(np.asarray(a[1], float), np.asarray(b[1], float), p))

def catmull(points, s):
    """C1 spline through 3D points, s in [0, 1] over the whole path (camera flights that never kink)."""
    P = [np.asarray(p, float) for p in points]
    if len(P) == 1: return P[0]
    n = len(P) - 1
    x = clamp(s) * n
    i = min(int(x), n - 1); u = x - i
    p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, n)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)

def shake_at(t, at, amp=24.0, decay=9.0, freq=42.0):
    """Decaying camera shake after a hit at `at` (screen pixels). Use sparingly: hits only."""
    if t < at: return (0.0, 0.0)
    e = math.exp(-(t - at) * decay)
    return (amp * e * math.sin((t - at) * freq), amp * 0.6 * e * math.cos((t - at) * freq * 1.3))

# ── planes (stations) ───────────────────────────────────────────────────────
class Plane:
    """A flat face in the world. Layer pixel (u, v) with origin top-left, v down."""
    def __init__(self, center, yaw=0.0, pitch=0.0, size=None):
        self.c = np.asarray(center, float)
        cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        self.r = norm(v3(cy, 0, -sy))
        self.u = norm(v3(sy * sp, cp, cy * sp))
        self.n = norm(np.cross(self.r, self.u))
        self.w, self.h = size or (W, H)

    def world(self, u, v):
        return self.c + self.r * (u - self.w / 2) + self.u * (self.h / 2 - v)

    def worlds(self, uv):
        uv = np.asarray(uv, float)
        return self.c + np.outer(uv[:, 0] - self.w / 2, self.r) + np.outer(self.h / 2 - uv[:, 1], self.u)

    def home(self, dist=D, du=0.0, dv=0.0):
        """The pose that maps this plane 1:1 onto the screen (optionally aimed at a layer offset)."""
        tgt = self.world(self.w / 2 + du, self.h / 2 + dv)
        return tgt + self.n * dist, tgt

    def framing(self, box, fill=0.86):
        """A pose that frames the layer-rect box=(u0, v0, u1, v1) so it fills `fill` of the screen."""
        u0, v0, u1, v1 = box
        bw, bh = (u1 - u0), (v1 - v0)
        k = min(W * fill / bw, H * fill / bh)
        return self.home(D / k, (u0 + u1) / 2 - self.w / 2, (v0 + v1) / 2 - self.h / 2)

# ── compositing ─────────────────────────────────────────────────────────────
def new_frame():
    return np.zeros((RH, RW, 3), np.float32)

def to_premul(rgba_u8):
    a = rgba_u8[..., 3:4].astype(np.float32) / 255.0
    return np.concatenate([rgba_u8[..., :3].astype(np.float32) / 255.0 * a, a], axis=2)

def over(dst, src_premul, opacity=1.0):
    a = src_premul[..., 3:4] * opacity
    dst *= (1 - a)
    dst += src_premul[..., :3] * opacity

def add(dst, src_premul, opacity=1.0):
    """Additive light (glows, strands, flares)."""
    dst += src_premul[..., :3] * opacity

DOF_K = 9000.0
def dof_blur(cam, p, focus):
    """Blur radius (render px) of a point at p when the lens focuses at camera depth `focus`."""
    if focus is None: return 0.0
    z = float(cam.to_cam(np.asarray(p, float)[None])[0, 2])
    return abs(1 / max(z, 1) - 1 / focus) * DOF_K * SCALE

def composite_plane(frame, cam, plane, layer_rgba, opacity=1.0, blur=0.0, focus=None, mode='over'):
    """Warp a station's layer (RGBA uint8, plane-sized or any size mapped onto the plane) into the frame."""
    if opacity <= 0.003 or layer_rgba is None: return
    h, w = layer_rgba.shape[:2]
    corners = np.array([plane.world(0, 0), plane.world(plane.w, 0), plane.world(plane.w, plane.h), plane.world(0, plane.h)])
    cc = cam.to_cam(corners)
    if (cc[:, 2] < 50).any(): return                     # behind or too close to the lens
    dst, _ = cam.project(corners)
    if dst[:, 0].max() < -RW or dst[:, 0].min() > 2 * RW or dst[:, 1].max() < -RH or dst[:, 1].min() > 2 * RH: return
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    M = cv2.getPerspectiveTransform(src, dst.astype(np.float32))
    pm = to_premul(layer_rgba)
    # big minification aliases: pre-shrink the layer when it lands much smaller than it is
    span = max(np.ptp(dst[:, 0]), 1.0)
    if span < w * 0.5:
        k = max(span / w * 1.5, 0.05)
        pm = cv2.resize(pm, (max(2, int(w * k)), max(2, int(h * k))), interpolation=cv2.INTER_AREA)
        M = cv2.getPerspectiveTransform(np.float32([[0, 0], [pm.shape[1], 0], [pm.shape[1], pm.shape[0]], [0, pm.shape[0]]]), dst.astype(np.float32))
    warped = cv2.warpPerspective(pm, M, (RW, RH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    blur = max(blur, dof_blur(cam, plane.c, focus))
    if blur > 0.6: warped = cv2.GaussianBlur(warped, (0, 0), blur)
    (add if mode == 'add' else over)(frame, warped, opacity)

def composite_sprite(frame, img_rgba, cx, cy, height, sx=1.0, sy=1.0, rot=0.0, opacity=1.0, anchor=(0.5, 0.5), blur=0.0, mode='over'):
    """Place an RGBA sprite in screen space (full-size pixel coords). Squash/stretch via sx, sy about the anchor."""
    if opacity <= 0.003 or height < 2 or img_rgba is None: return
    h0, w0 = img_rgba.shape[:2]
    s = height * SCALE / h0
    pm = to_premul(img_rgba)
    if s < 0.5:  # pre-shrink so small sprites stay clean
        k = max(s * 1.5, 0.02)
        pm = cv2.resize(pm, (max(2, int(w0 * k)), max(2, int(h0 * k))), interpolation=cv2.INTER_AREA)
        s, h0, w0 = s / k, pm.shape[0], pm.shape[1]
    M = cv2.getRotationMatrix2D((w0 * anchor[0], h0 * anchor[1]), rot, 1.0)
    M = np.vstack([M, [0, 0, 1]])
    S = np.diag([s * sx, s * sy, 1.0])
    T = np.array([[1, 0, cx * SCALE - w0 * anchor[0] * s * sx], [0, 1, cy * SCALE - h0 * anchor[1] * s * sy], [0, 0, 1]])
    A = (T @ S @ M)[:2]
    warped = cv2.warpAffine(pm, A, (RW, RH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    if blur > 0.6: warped = cv2.GaussianBlur(warped, (0, 0), blur * SCALE)
    (add if mode == 'add' else over)(frame, warped, opacity)

def composite_screen(frame, layer_rgba, x=0, y=0, opacity=1.0, mode='over'):
    """Paste a screen-space RGBA layer (full-size coords) without any camera: supers, overlays, end cards."""
    if opacity <= 0.003: return
    lay = layer_rgba
    if SCALE != 1:
        lay = cv2.resize(lay, (max(1, int(lay.shape[1] * SCALE)), max(1, int(lay.shape[0] * SCALE))), interpolation=cv2.INTER_AREA)
    x, y = int(round(x * SCALE)), int(round(y * SCALE))
    h, w = lay.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(RW, x + w), min(RH, y + h)
    if x1 <= x0 or y1 <= y0: return
    pm = to_premul(lay[y0 - y:y1 - y, x0 - x:x1 - x])
    sub = frame[y0:y1, x0:x1]
    (add if mode == 'add' else over)(sub, pm, opacity)

# ── THE LINE: one shared function draws it, everywhere ──────────────────────
def draw_line(frame, cam, pts_world, upto=1.0, color=(0x97, 0x5A, 0xFD), width=12.0, glow=1.0, head=True,
              opacity=1.0, focus=None, start=0.0):
    """A line of light along a 3D polyline. `upto` = how much of its length is drawn (the head travels);
    `start` trims the tail (a comet). Perspective width, a dim additive glow, a hot core, a spark at the head.
    Draw it ONCE per frame from the centre motion-blur sample (see render_frame), never inside the sub-samples."""
    if opacity <= 0.003 or upto <= start: return None
    pts = np.asarray(pts_world, float)
    if len(pts) < 2: return None
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    a, b = L[-1] * clamp(start), L[-1] * clamp(upto)
    s = np.linspace(a, b, max(2, int(len(pts) * (b - a) / max(L[-1], 1e-9)) + 2))
    part = np.stack([np.interp(s, L, pts[:, i]) for i in range(3)], axis=1)
    xy, z = cam.project(part)
    keep = z > 40
    if keep.sum() < 2: return None
    xy, z = xy[keep], z[keep]
    px = width * cam.f * SCALE / float(np.median(z))
    col = np.array(color, np.float32) / 255
    gmask = np.zeros((RH // 2, RW // 2), np.uint8)
    cv2.polylines(gmask, [np.int32(xy / 2 * 8)], False, 255, max(1, int(px * 2.2 / 2)), cv2.LINE_AA, shift=3)
    g = cv2.GaussianBlur(gmask, (0, 0), max(2.0, px * 1.6 / 2)).astype(np.float32) / 255
    g = cv2.resize(g, (RW, RH), interpolation=cv2.INTER_LINEAR)
    cmask = np.zeros((RH, RW), np.uint8)
    cv2.polylines(cmask, [np.int32(xy * 8)], False, 255, max(1, int(px)), cv2.LINE_AA, shift=3)
    c = cmask.astype(np.float32) / 255
    if focus is not None:
        bl = abs(1 / float(np.median(z)) - 1 / focus) * DOF_K * SCALE
        if bl > 0.6: c = cv2.GaussianBlur(c, (0, 0), bl)
    hot = np.minimum(1, col * 0.55 + 0.55)
    frame += g[..., None] * col * 0.55 * glow * opacity
    al = c[..., None] * opacity
    frame *= (1 - al * 0.85)
    frame += al * (col * 0.35 + hot * 0.65)
    if head:
        hx, hy = xy[-1]
        r = max(3, px * 1.4)
        cv2.circle(frame, (int(hx), int(hy)), int(r * 2.2), tuple(float(v) * 0.35 * opacity for v in col), -1, cv2.LINE_AA)
        cv2.circle(frame, (int(hx), int(hy)), int(r), tuple(float(min(1, v * 0.4 + 0.8)) * opacity for v in col), -1, cv2.LINE_AA)
    return xy

# ── the stage and the grade ─────────────────────────────────────────────────
_cache = {}
def _grid():
    if 'grid' not in _cache:
        yy, xx = np.mgrid[0:RH, 0:RW].astype(np.float32)
        _cache['grid'] = (xx / max(RW, 1), yy / max(RH, 1))
    return _cache['grid']

def stage(frame, base=(0x06, 0x08, 0x13), glows=(((0.5, 0.42), (0x97, 0x5A, 0xFD), 0.11, 0.62),), t=0.0, drift=0.035):
    """The near-black brand stage with soft, drifting glows. glows = ((x, y), rgb, strength, radius) in 0..1 units.
    Never neon: strengths around 0.06-0.14 read as light in a dark room."""
    gx_, gy_ = _grid()
    out = np.empty((RH, RW, 3), np.float32)
    out[:] = np.array(base, np.float32) / 255
    asp = RW / RH
    for i, ((x, y), rgb, strength, rad) in enumerate(glows):
        x += smooth_noise(t, i + 1, 0.35) * drift
        y += smooth_noise(t, i + 7, 0.3) * drift
        r2 = (((gx_ - x) * asp) ** 2 + (gy_ - y) ** 2) / (rad * rad * max(asp, 1))
        g = np.clip(1 - r2, 0, 1) ** 2 * strength
        out += g[..., None] * (np.array(rgb, np.float32) / 255)
    frame[:] = out

def _grain(i):
    k = ('grain', i % 6)
    if k not in _cache:
        rng = np.random.default_rng(100 + i % 6)
        _cache[k] = rng.normal(0, 1, (RH, RW)).astype(np.float32)
    return _cache[k]

def _vignette(strength):
    k = ('vig', strength)
    if k not in _cache:
        gx_, gy_ = _grid()
        r = np.sqrt(((gx_ - 0.5) / 0.72) ** 2 + ((gy_ - 0.5) / 0.72) ** 2)
        _cache[k] = (1 - np.clip(r - 0.55, 0, 1) * strength)[..., None].astype(np.float32)
    return _cache[k]

def bloom(frame, threshold=0.75, strength=0.35, radius=18):
    """Soft bloom from the brightest parts (keep it subtle; heroes brighter, never flare to white)."""
    hi = np.clip(frame - threshold, 0, None)
    small = cv2.resize(hi, (RW // 4, RH // 4), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), max(1.0, radius * SCALE / 4))
    frame += cv2.resize(small, (RW, RH), interpolation=cv2.INTER_LINEAR) * strength

def grade(frame, t, vignette=0.5, grain=0.02, bloom_strength=0.25):
    """The finish: bloom, vignette, film grain. Logos and end-card marks are composited AFTER this (after_grade)."""
    if bloom_strength > 0: bloom(frame, strength=bloom_strength)
    frame *= _vignette(vignette)
    frame += _grain(int(t * FPS))[..., None] * grain
    np.clip(frame, 0, 1, out=frame)
    return frame

def after_grade(frame, layer_rgba, x, y, opacity=1.0):
    """Brand marks go on top of the grade: no grain, bloom or vignette on them, pixel-exact at rest."""
    composite_screen(frame, layer_rgba, x, y, opacity)
    np.clip(frame, 0, 1, out=frame)

def to_u8(frame):
    return (np.clip(frame, 0, 1) * 255 + 0.5).astype(np.uint8)

# ── assets ──────────────────────────────────────────────────────────────────
_img_cache = {}
def load_rgba(path, max_h=None):
    k = (path, max_h)
    if k not in _img_cache:
        im = Image.open(path).convert('RGBA')
        if max_h and im.height > max_h:
            im = im.resize((int(im.width * max_h / im.height), max_h), Image.LANCZOS)
        _img_cache[k] = np.asarray(im).copy()
        if len(_img_cache) > 64: _img_cache.clear()    # bounded: every render worker holds its own copy
    return _img_cache[k]

def pil_to_rgba(im):
    return np.asarray(im.convert('RGBA')).copy()
