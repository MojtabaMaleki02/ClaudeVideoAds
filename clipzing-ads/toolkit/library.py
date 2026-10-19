#!/usr/bin/env python3
"""Turn raw captures (capture/shoot.mjs output) into the library the films read.

  library.py zing    RAW_DIR   [--max 900]    → library/zing/<pose>/NNNN.webp + meta.json (fps, loop, body_box)
  library.py footage RAW_DIR   [--max 720]    → library/footage/<scene>/NNNN.jpg
  library.py brand   RAW_DIR                  → assets/brand/{wordmark,wordmark-white,icon}.png (tight-cropped)
  library.py captions RAW_DIR OUT_DIR         → OUT_DIR/<job>/NNNN.png (kept PNG: exact, per project)
"""
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
LIB = os.environ.get('CLIPZING_ADS_LIBRARY', os.path.join(SKILL, 'library'))

def frames(d): return sorted(f for f in os.listdir(d) if f.endswith('.png'))

def body_box(paths):
    """Union of the opaque area over a pose's frames, as fractions of the canvas."""
    box = None
    for p in paths[:: max(1, len(paths) // 12)]:
        a = np.asarray(Image.open(p).getchannel('A')) > 24
        ys, xs = np.nonzero(a)
        if not len(xs): continue
        b = (xs.min(), ys.min(), xs.max(), ys.max())
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    h, w = np.asarray(Image.open(paths[0])).shape[:2]
    return [round(box[0] / w, 4), round(box[1] / h, 4), round(box[2] / w, 4), round(box[3] / h, 4)] if box else [0, 0, 1, 1]

def zing(raw, mx=720):
    for name in sorted(os.listdir(raw)):
        src = os.path.join(raw, name)
        if not os.path.isdir(src) or not frames(src): continue
        meta = json.load(open(os.path.join(src, 'meta.json'))) if os.path.exists(os.path.join(src, 'meta.json')) else {}
        if meta.get('entry', 'zing') != 'zing': continue
        dst = os.path.join(LIB, 'zing', name); shutil.rmtree(dst, ignore_errors=True); os.makedirs(dst)
        fs = [os.path.join(src, f) for f in frames(src)]
        for i, p in enumerate(fs):
            im = Image.open(p).convert('RGBA')
            if im.width > mx: im = im.resize((mx, mx * im.height // im.width), Image.LANCZOS)
            im.save(os.path.join(dst, f'{i:04d}.webp'), 'WEBP', quality=86, method=5)
        json.dump({'fps': meta.get('fps', 30), 'frames': len(fs), 'loop': len(fs) > 1, 'body_box': body_box(fs)}, open(os.path.join(dst, 'meta.json'), 'w'))
        print('zing', name, len(fs))

def footage(raw, mx=720):
    for name in sorted(os.listdir(raw)):
        src = os.path.join(raw, name)
        if not os.path.isdir(src): continue
        meta = json.load(open(os.path.join(src, 'meta.json'))) if os.path.exists(os.path.join(src, 'meta.json')) else {}
        if meta.get('entry') != 'footage': continue
        dst = os.path.join(LIB, 'footage', name); shutil.rmtree(dst, ignore_errors=True); os.makedirs(dst)
        for i, f in enumerate(frames(src)):
            im = Image.open(os.path.join(src, f)).convert('RGB')
            if im.width > mx: im = im.resize((mx, mx * im.height // im.width), Image.LANCZOS)
            im.save(os.path.join(dst, f'{i:04d}.jpg'), quality=90)
        print('footage', name)

def brand(raw):
    out = os.path.join(SKILL, 'assets', 'brand'); os.makedirs(out, exist_ok=True)
    for name in ('wordmark', 'wordmark-white', 'icon'):
        p = os.path.join(raw, name, '0000.png')
        if not os.path.exists(p): continue
        im = Image.open(p).convert('RGBA'); im = im.crop(im.getbbox())
        im.save(os.path.join(out, f'{name}.png')); print('brand', name, im.size)

def captions(raw, out):
    for name in sorted(os.listdir(raw)):
        src = os.path.join(raw, name)
        if os.path.isdir(src) and frames(src):
            dst = os.path.join(out, name); shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst); print('captions', name)

if __name__ == '__main__':
    kind, raw = sys.argv[1], sys.argv[2]
    mx = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else None
    {'zing': lambda: zing(raw, mx or 720), 'footage': lambda: footage(raw, mx or 720), 'brand': lambda: brand(raw),
     'captions': lambda: captions(raw, sys.argv[3])}[kind]()
