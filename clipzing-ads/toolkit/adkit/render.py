"""adkit.render: turning a film module into frames.

A FILM is a Python module that defines:
  END                     length in seconds (end card included)
  scene(t) -> (frame, deferred)
                          draw the world at time t into a new float frame; return callables in `deferred` for things
                          that must be drawn ONCE from the centre motion-blur sample (lines of light, crisp type)
                          each deferred item is f(frame) → None
  camera_at(t) -> Camera  (optional) used by the motion probe
  probe(t) -> list[(x,y)] (optional) extra screen points (full-size px) that move, so sprites/UI get blur too
  overlay(frame, t)       (optional) drawn AFTER the grade: logos, end-card marks (pixel-exact, no grain)
  GRADE = dict(...)       (optional) kwargs for core.grade
"""
import math
import os
import subprocess

import numpy as np
from PIL import Image

from . import core

def _probe_px(film, t, dt):
    """How far (render px) things move across one frame: camera probe + the film's own moving points."""
    best = 0.0
    if hasattr(film, 'camera_at'):
        a, b = film.camera_at(t - dt / 2), film.camera_at(t + dt / 2)
        ref = a.target
        pts = np.array([ref + a.rt * x + a.up * y for x in (-900, 0, 900) for y in (-500, 0, 500)])
        pa, za = a.project(pts); pb, zb = b.project(pts)
        ok = (za > 60) & (zb > 60)
        if ok.any(): best = float(np.max(np.linalg.norm(pa[ok] - pb[ok], axis=1)))
        best = max(best, abs(a.shake[0] - b.shake[0]) * core.SCALE, abs(a.shake[1] - b.shake[1]) * core.SCALE)
    if hasattr(film, 'probe'):
        pa, pb = film.probe(t - dt / 2), film.probe(t + dt / 2)
        for (x0, y0), (x1, y1) in zip(pa, pb):
            best = max(best, math.hypot(x1 - x0, y1 - y0) * core.SCALE)
    return best

def samples_for(film, t, max_samples=24, px_per_sample=5.0):
    """Adaptive motion blur: enough sub-frames that no step between copies exceeds ~5 px (no stepped ghosts)."""
    if getattr(film, 'NO_BLUR', False): return 1
    px = _probe_px(film, t, 1.0 / core.FPS) * getattr(film, 'SHUTTER', 0.5)
    n = int(math.ceil(px / px_per_sample))
    if n <= 1: return 1
    n = min(max_samples, n)
    return n + (1 - n % 2)   # odd, so one sample sits on t exactly

def render_frame(film, t):
    """One finished frame (uint8 RGB) at time t."""
    n = samples_for(film, t)
    shutter = getattr(film, 'SHUTTER', 0.5) / core.FPS
    if n == 1:
        frame, deferred = film.scene(t)
    else:
        acc = None
        deferred = []
        for i in range(n):
            ts = t + (i / (n - 1) - 0.5) * shutter
            fr, df = film.scene(ts)
            if i == n // 2: deferred = df
            acc = fr if acc is None else acc + fr
        frame = acc / n
    for f in deferred or []: f(frame)
    core.grade(frame, t, **getattr(film, 'GRADE', {}))
    if hasattr(film, 'overlay'): film.overlay(frame, t)
    return core.to_u8(frame)

def save(arr, path, level=1):
    Image.fromarray(arr).save(path, compress_level=level)

# ── video helpers ───────────────────────────────────────────────────────────
def encode(frames_dir, out, audio=None, fps=None, crf=15, preset='slow', upload=False):
    """Frames %05d.png (+ audio) → H.264 MP4, yuv420p, faststart. upload=True: CRF 20 capped at 25 Mb/s (TikTok size)."""
    fps = fps or core.FPS
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-framerate', str(fps), '-i', os.path.join(frames_dir, '%05d.png')]
    if audio: cmd += ['-i', audio]
    cmd += ['-c:v', 'libx264', '-preset', preset, '-crf', str(20 if upload else crf), '-pix_fmt', 'yuv420p', '-profile:v', 'high',
            '-g', str(fps * 2), '-bf', '2']
    if upload: cmd += ['-maxrate', '25M', '-bufsize', '50M']
    else: cmd += ['-tune', 'animation']
    if audio: cmd += ['-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-shortest']
    cmd += ['-movflags', '+faststart', out]
    subprocess.check_call(cmd)
    return out

def contact_sheet(video, out, cols=6, every=0.7, width=320):
    subprocess.check_call(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', video, '-vf',
                           f'fps={1 / every},scale={width}:-1,tile={cols}x{max(1, 30 // cols)}:padding=4', '-frames:v', '1', out])
    return out

def stills_sheet(paths, out, cols=4, width=480):
    ims = [Image.open(p).convert('RGB') for p in paths]
    if not ims: return
    w = width; h = int(ims[0].height * w / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * w + (cols + 1) * 6, rows * h + (rows + 1) * 6), (60, 60, 64))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((w, h), Image.LANCZOS), (6 + (i % cols) * (w + 6), 6 + (i // cols) * (h + 6)))
    sheet.save(out, quality=90)
    return out
