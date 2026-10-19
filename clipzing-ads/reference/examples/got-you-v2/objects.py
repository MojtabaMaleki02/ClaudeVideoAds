"""Physical objects for Got You v2: chunky, glossy faces drawn in Clipzing's language; film.py extrudes them in 3D.
Each returns an RGBA face sized to the object (not the frame), so extrusion stays cheap."""
import math

import cv2
import numpy as np

from adkit import brand, fx, ui
from adkit.brand import C

def gloss(L, box, r, top=(70, 54, 120), bottom=(30, 22, 58), sheen=0.22):
    """A glossy rounded face: vertical gradient + a soft highlight band across the top third."""
    x0, y0, x1, y1 = box
    L.gradient_rrect(box, r, top, bottom)
    L.gradient_rrect((x0 + 6, y0 + 6, x1 - 6, y0 + (y1 - y0) * 0.42), max(4, r - 6), (255, 255, 255), (255, 255, 255), alpha=int(255 * sheen * 0.35))
    L.rrect(box, r, outline=(255, 255, 255, 46), width=2)

@ui.cached(8)
def counter_plate(w=920, h=560):
    """The follower counter's plate: three deep digit wells and the label."""
    L = ui.Layer(w, h)
    gloss(L, (0, 0, w, h), 70, top=(150, 104, 252), bottom=(104, 46, 220), sheen=0.5)
    cw, ch = 230, 300
    x0 = (w - 3 * cw - 2 * 34) / 2
    for i in range(3):
        x = x0 + i * (cw + 34)
        L.gradient_rrect((x, 70, x + cw, 70 + ch), 36, (10, 8, 22), (22, 18, 40))
        L.rrect((x, 70, x + cw, 70 + ch), 36, outline=(255, 255, 255, 26), width=2)
    L.type((w / 2, 70 + ch + 92), 'followers', 76, 'extrabold', fill=(255, 255, 255), anchor='mm', tracking=-0.01)
    return L.rgba()

@ui.cached(64)
def digit(d, roll100=0):
    """A digit tile that can roll toward the next digit (roll 0..1), clipped to its well."""
    cw, ch = 230, 300
    L = ui.Layer(cw, ch)
    f = brand.font(250 * L.ss, 'extrabold')
    off = roll100 / 100 * ch
    for k, dd in ((0, d % 10), (1, (d + 1) % 10)):
        y = (ch / 2 - off + k * ch) * L.ss
        L.d.text((cw / 2 * L.ss, y), str(dd), font=f, fill=(255, 255, 255, 255), anchor='mm')
    return L.rgba()

@ui.cached(8)
def slab_bezel(w, h, r=46):
    """A chunky screen bezel (face only; the picture is pasted in by the film)."""
    L = ui.Layer(w, h)
    gloss(L, (0, 0, w, h), r, top=(52, 46, 74), bottom=(18, 16, 28), sheen=0.14)
    return L.rgba()

def framed(picture, w, h, bezel=26, r=46):
    """A picture inside a chunky bezel: returns the face RGBA (w×h)."""
    face = slab_bezel(int(w), int(h), r).copy()
    pw, ph = int(w - 2 * bezel), int(h - 2 * bezel)
    pic = cv2.resize(picture, (pw, ph), interpolation=cv2.INTER_AREA) if picture.shape[1] != pw or picture.shape[0] != ph else picture
    m = np.zeros((ph, pw), np.uint8)
    rr = max(4, r - bezel)
    cv2.rectangle(m, (rr, 0), (pw - rr, ph), 255, -1); cv2.rectangle(m, (0, rr), (pw, ph - rr), 255, -1)
    for cx, cy in ((rr, rr), (pw - rr, rr), (rr, ph - rr), (pw - rr, ph - rr)): cv2.circle(m, (cx, cy), rr, 255, -1, cv2.LINE_AA)
    a = m[..., None].astype(np.float32) / 255
    reg = face[bezel:bezel + ph, bezel:bezel + pw].astype(np.float32)
    rgb = pic[..., :3].astype(np.float32)
    reg[..., :3] = reg[..., :3] * (1 - a) + rgb * a
    reg[..., 3:4] = np.maximum(reg[..., 3:4], a * 255)
    face[bezel:bezel + ph, bezel:bezel + pw] = reg.astype(np.uint8)
    # a glass sheen across the picture
    sheen = np.zeros_like(face[..., 0], np.float32)
    yy, xx = np.mgrid[0:face.shape[0], 0:face.shape[1]]
    band = np.clip(1 - np.abs((xx * 0.55 + yy) / (face.shape[0] * 1.2) - 0.3) / 0.12, 0, 1) * 0.07
    face[..., :3] = np.clip(face[..., :3] + (band[..., None] * 255), 0, 255).astype(np.uint8)
    return face

@ui.cached(16)
def pill(text, size=54, fill=None, fg=(255, 255, 255), pad=(44, 24)):
    f = brand.font(size, 'extrabold')
    tw = f.getlength(text)
    w, h = int(tw + pad[0] * 2), int(size + pad[1] * 2)
    L = ui.Layer(w, h)
    top = fill or C['purple']
    L.gradient_rrect((0, 0, w, h), h / 2, tuple(min(255, c + 30) for c in top), tuple(int(c * 0.8) for c in top))
    L.rrect((0, 0, w, h), h / 2, outline=(255, 255, 255, 60), width=2)
    L.type((w / 2, h / 2 + 2), text, size, 'extrabold', fill=fg, anchor='mm', tracking=0.02)
    return L.rgba()

def bracket_layer(w, h, box_list, color=(196, 160, 255), thick=14, arm=0.22, glow=True):
    """Viewfinder corner brackets (chunky L shapes) for one or more boxes, on a transparent w×h layer."""
    L = ui.Layer(int(w), int(h), ss=1)
    for (x0, y0, x1, y1) in box_list:
        bw, bh = x1 - x0, y1 - y0
        a = min(bw, bh) * arm
        for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            L.d.rounded_rectangle([min(cx, cx + sx * a), min(cy, cy + sy * thick) - (thick if sy < 0 else 0) * 0, max(cx, cx + sx * a), max(cy, cy + sy * thick)], thick / 2, fill=color + (255,))
            L.d.rounded_rectangle([min(cx, cx + sx * thick), min(cy, cy + sy * a), max(cx, cx + sx * thick), max(cy, cy + sy * a)], thick / 2, fill=color + (255,))
    rgba = L.rgba()
    if glow:
        g = cv2.GaussianBlur(rgba[..., 3].astype(np.float32), (0, 0), 14)
        out = rgba.astype(np.float32)
        glow_a = np.clip(g * 0.6, 0, 255)
        out[..., :3] = np.where(rgba[..., 3:4] > 0, out[..., :3], np.array(color, np.float32))
        out[..., 3] = np.maximum(out[..., 3], glow_a)
        rgba = out.astype(np.uint8)
    return rgba

@ui.cached(8)
def calendar_body(w, h, days, cols):
    """A chunky desk calendar: a purple header with binding rings, then day wells in a grid."""
    L = ui.Layer(w, h)
    gloss(L, (0, 30, w, h), 56, top=(40, 34, 64), bottom=(16, 14, 28), sheen=0.12)
    L.gradient_rrect((0, 30, w, 210), 56, C['purple'], C['violet'])
    L.rrect((0, 150, w, 210), 0, fill=C['violet'] + (255,))
    L.type((60, 120), 'NEXT WEEK', 72, 'extrabold', fill=(255, 255, 255), tracking=0.04, anchor='lm')
    for i in range(6):   # binding rings
        x = w * (0.18 + i * 0.128)
        L.gradient_rrect((x - 14, 0, x + 14, 78), 14, (236, 232, 248), (150, 144, 170))
    rows = (len(days) + cols - 1) // cols
    gw = (w - 60) / cols; gh = (h - 250) / rows
    for i, d in enumerate(days):
        c, r = i % cols, i // cols
        cx = 30 + c * gw + (gw / 2 if (r == rows - 1 and len(days) % cols and cols > len(days) % cols) else 0) * (cols - len(days) % cols) / 1
        x0, y0 = 30 + c * gw + 10, 240 + r * gh + 10
        if r == rows - 1 and len(days) % cols:
            x0 += (cols - len(days) % cols) * gw / 2
        L.gradient_rrect((x0, y0, x0 + gw - 20, y0 + gh - 20), 30, (12, 10, 22), (24, 20, 40))
        L.type((x0 + (gw - 20) / 2, y0 + 44), d, 40, 'extrabold', fill=(190, 184, 220), anchor='mm', tracking=0.04)
    return L.rgba()

def day_cell_box(i, w, h, n, cols):
    rows = (n + cols - 1) // cols
    gw = (w - 60) / cols; gh = (h - 250) / rows
    c, r = i % cols, i // cols
    x0, y0 = 30 + c * gw + 10, 240 + r * gh + 10
    if r == rows - 1 and n % cols:
        x0 += (cols - n % cols) * gw / 2
    return x0, y0, x0 + gw - 20, y0 + gh - 20

@ui.cached(4)
def streak_badge():
    """Clipzing's streak: a gold flame and '7-day streak' on a chunky pill."""
    w, h = 760, 190
    L = ui.Layer(w, h)
    L.gradient_rrect((0, 0, w, h), h / 2, (255, 214, 102), (245, 150, 30))
    L.rrect((0, 0, w, h), h / 2, outline=(255, 255, 255, 110), width=3)
    # a flame glyph
    cx, cy, s = 110, h / 2 + 6, 100
    pts = []
    for k in range(60):
        a = k / 59 * 2 * math.pi
        rr = s * (0.5 + 0.08 * math.cos(3 * a))
        x = cx + math.sin(a) * rr * 0.62
        y = cy - math.cos(a) * rr * (1.0 if math.cos(a) > 0 else 0.62) * 0.9
        pts.append((x * L.ss, y * L.ss))
    L.d.polygon(pts, fill=(255, 255, 255, 255))
    L.d.polygon([(x * 0.55 + cx * 0.45 * L.ss, y * 0.55 + (cy + 18) * 0.45 * L.ss) for x, y in pts], fill=(255, 150, 40, 255))
    L.type((196, h / 2 + 2), '7-day streak', 72, 'extrabold', fill=(90, 40, 0), anchor='lm', tracking=-0.01)
    return L.rgba()
