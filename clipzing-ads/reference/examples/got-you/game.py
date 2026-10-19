"""Original game "footage" for the reframe beat: a neon space shooter drawn in code (no real game, no third-party IP),
and a stream layout of it with Zing on a facecam. Deterministic in t."""
import math
from functools import lru_cache

import cv2
import numpy as np

def ship_x(t):
    """The player's x (0..1) — the reframe follows it."""
    return 0.5 + 0.28 * math.sin(t * 1.3) + 0.08 * math.sin(t * 3.1)

@lru_cache(maxsize=4)
def _bg(w, h):
    y = np.linspace(0, 1, h)[:, None]
    top, bot = np.array([18, 6, 40], np.float32), np.array([60, 10, 70], np.float32)
    img = (top + (bot - top) * y[..., None] ** 1.4) * np.ones((1, w, 1), np.float32)
    # a striped sun
    cx, cy, r = w * 0.5, h * 0.52, h * 0.22
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    sun = (d < r) & ~(((yy - (cy - r * 0.1)) % (r * 0.16) < r * 0.05) & (yy > cy - r * 0.1))
    grad = np.clip((yy - (cy - r)) / (2 * r), 0, 1)[..., None]
    sun_col = np.array([255, 210, 90], np.float32) * (1 - grad) + np.array([255, 60, 150], np.float32) * grad
    img = np.where(sun[..., None], sun_col, img)
    return img.astype(np.float32)

def frame(t, w=1280, h=720):
    """One RGB uint8 frame of the game at time t."""
    img = _bg(w, h).copy()
    rng = np.random.default_rng(7)
    # stars (parallax)
    for i in range(90):
        x = (rng.uniform() * w + t * 20 * (1 + i % 3)) % w
        y = rng.uniform() * h * 0.5
        c = 140 + 100 * (i % 3) / 2
        cv2.circle(img, (int(x), int(y)), 1 + i % 2, (c, c, c * 1.1), -1, cv2.LINE_AA)
    # neon perspective grid on the floor
    hor = int(h * 0.62)
    img[hor:] *= 0.35
    for k in range(-12, 13):
        x0 = w / 2 + k * w * 0.02
        x1 = w / 2 + k * w * 0.16
        cv2.line(img, (int(x0), hor), (int(x1), h), (230, 60, 255), 2, cv2.LINE_AA)
    for j in range(10):
        p = ((j + (t * 1.5) % 1) / 10) ** 2
        y = int(hor + (h - hor) * p)
        cv2.line(img, (0, y), (w, y), (230, 60, 255), 2, cv2.LINE_AA)
    # enemies in a wave
    sx = ship_x(t) * w
    for i in range(7):
        ex = w * (0.12 + 0.12 * i) + math.sin(t * 2 + i) * 30
        ey = h * 0.18 + math.sin(t * 1.5 + i * 0.8) * 25 + 40 * (i % 2)
        hit = (t * 2.5 + i * 0.37) % 2.0 < 0.18
        if hit:
            for k in range(10):
                a = k * 0.63; r = 26 * (((t * 2.5 + i * 0.37) % 2.0) / 0.18)
                cv2.circle(img, (int(ex + math.cos(a) * r), int(ey + math.sin(a) * r)), 3, (255, 220, 120), -1, cv2.LINE_AA)
        else:
            pts = np.array([[ex, ey - 18], [ex + 16, ey], [ex, ey + 18], [ex - 16, ey]], np.int32)
            cv2.fillPoly(img, [pts], (255, 70, 170), cv2.LINE_AA)
            cv2.polylines(img, [pts], True, (255, 190, 230), 2, cv2.LINE_AA)
    # bullets
    for k in range(6):
        by = h * 0.82 - ((t * 900 + k * 120) % (h * 0.75))
        cv2.line(img, (int(sx), int(by)), (int(sx), int(by + 22)), (120, 255, 255), 3, cv2.LINE_AA)
    # the ship
    sy = h * 0.82
    ship = np.array([[sx, sy - 34], [sx + 28, sy + 20], [sx, sy + 8], [sx - 28, sy + 20]], np.int32)
    cv2.fillPoly(img, [ship], (60, 240, 255), cv2.LINE_AA)
    cv2.polylines(img, [ship], True, (220, 255, 255), 2, cv2.LINE_AA)
    cv2.circle(img, (int(sx), int(sy + 26)), 7, (255, 160, 60), -1, cv2.LINE_AA)
    # HUD
    score = 12000 + int(t * 137) % 900
    cv2.putText(img, f'SCORE {score:06d}', (int(w * 0.03), int(h * 0.07)), cv2.FONT_HERSHEY_SIMPLEX, h / 720, (120, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(img, 'LVL 7', (int(w * 0.86), int(h * 0.07)), cv2.FONT_HERSHEY_SIMPLEX, h / 720, (255, 120, 220), 2, cv2.LINE_AA)
    return np.clip(img, 0, 255).astype(np.uint8)

def stream(t, w, h, facecam_rgba):
    """The stream: the game full frame, a facecam (Zing in his gamer pose) bottom-left, a LIVE pill."""
    img = frame(t, w, h).copy()
    fw, fh = int(w * 0.28), int(h * 0.36)
    fx, fy = int(w * 0.025), int(h - fh - h * 0.04)
    cam = np.zeros((fh, fw, 3), np.float32)
    cam[:] = np.array([24, 18, 44], np.float32)
    z = cv2.resize(facecam_rgba, (int(fh * 1.25), int(fh * 1.25)), interpolation=cv2.INTER_AREA)
    zx, zy = (fw - z.shape[1]) // 2, int(fh * 0.02)
    a = z[..., 3:4].astype(np.float32) / 255
    ys, xs = slice(max(0, zy), min(fh, zy + z.shape[0])), slice(max(0, zx), min(fw, zx + z.shape[1]))
    zz = z[ys.start - zy: ys.stop - zy, xs.start - zx: xs.stop - zx]
    aa = a[ys.start - zy: ys.stop - zy, xs.start - zx: xs.stop - zx]
    cam[ys, xs] = cam[ys, xs] * (1 - aa) + zz[..., :3] * aa
    img[fy:fy + fh, fx:fx + fw] = cam.astype(np.uint8)
    cv2.rectangle(img, (fx, fy), (fx + fw, fy + fh), (120, 255, 160), 3, cv2.LINE_AA)
    cv2.rectangle(img, (int(w * 0.03), int(h * 0.11)), (int(w * 0.03) + int(h * 0.11), int(h * 0.16)), (235, 40, 60), -1)
    cv2.putText(img, 'LIVE', (int(w * 0.034), int(h * 0.148)), cv2.FONT_HERSHEY_SIMPLEX, h / 1300, (255, 255, 255), 2, cv2.LINE_AA)
    return img, (fx, fy, fw, fh)
