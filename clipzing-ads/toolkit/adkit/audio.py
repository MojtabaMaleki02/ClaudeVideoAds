"""adkit.audio: original music made in code, a sound for every picture event, Clipzing's sonic logo, and a mix that
is MEASURED (you can't hear it, so measure it): loudness, true peak, the voice margin on every word, the voice on a
phone-speaker simulation, and a Whisper read of the final mix compared with the dry voice.

Targets (house standard): voice ≈ −16 LUFS (stem), music ≥ 12 dB (aim 15) under every spoken word,
master −14 LUFS integrated, true peak ≤ −1.25 dBTP. Impacts land a frame early and mostly low end; hero cues sit
just AFTER a word, never on it; ducking is applied AFTER reverb (or tails fill the dip).
"""
import glob
import json
import math
import os
import re
import subprocess

import numpy as np
import scipy.io.wavfile as wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
_rng = np.random.default_rng(3)

def tt(d): return np.arange(max(1, int(SR * d))) / SR
def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def lp(x, f): return sosfilt(butter(2, min(f, SR / 2 - 100), 'low', fs=SR, output='sos'), x)
def hp(x, f): return sosfilt(butter(2, f, 'high', fs=SR, output='sos'), x)
def bp(x, a, b): return sosfilt(butter(2, [a, min(b, SR / 2 - 100)], 'band', fs=SR, output='sos'), x)
def noise(n): return _rng.standard_normal(n)
def adsr(n, a, d, s, r):
    k = np.arange(n) / SR
    e = np.where(k < a, k / max(a, 1e-6), np.where(k < a + d, 1 + (s - 1) * (k - a) / max(d, 1e-6), s))
    nr = min(int(r * SR), n)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e
def fm(f, t): return np.sin(2 * np.pi * np.cumsum(np.broadcast_to(f, t.shape)) / SR)

class Bus:
    """A stereo buffer you place sounds into: bus.place(x, t, gain, pan)."""
    def __init__(self, seconds):
        self.n = int(SR * seconds); self.buf = np.zeros((self.n, 2))
    def place(self, x, t, g=1.0, pan=0.0):
        i = int(round(t * SR))
        if x is None or len(x) == 0: return
        if x.ndim == 1:
            L, R = x * math.sqrt(0.5 * (1 - pan)), x * math.sqrt(0.5 * (1 + pan))
            x = np.stack([L, R], 1)
        if i < 0: x = x[-i:]; i = 0
        if i >= self.n: return
        x = x[: self.n - i] * g
        self.buf[i:i + len(x)] += x

# ── instruments ─────────────────────────────────────────────────────────────
def marimba(m, g=0.3, d=0.9):
    t = tt(d); f = hz(m)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 7) + 0.35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 26) + 0.12 * np.sin(2 * np.pi * f * 10 * t) * np.exp(-t * 60)
    return x * (1 - np.exp(-t * 900)) * g
def mallet(m, g=0.2, d=0.6):
    t = tt(d); f = hz(m)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 18)) * np.exp(-t * 9) * (1 - np.exp(-t * 1200)) * g
def felt(ms, g=0.12, d=2.4):
    """Felt piano chord (soft, warm)."""
    t = tt(d); x = np.zeros(len(t))
    for m in ms:
        f = hz(m)
        x += sum(np.sin(2 * np.pi * f * h * t + h) * np.exp(-t * (1.1 + 0.9 * h)) / h ** 1.4 for h in range(1, 6))
    return lp(x, 2600) * (1 - np.exp(-t * 60)) * g / max(1, len(ms))
def pluck(m, g=0.2, d=0.5, bright=3500):
    """A clean synth pluck (keynote-minimal)."""
    t = tt(d); f = hz(m)
    saw = 2 * ((f * t) % 1) - 1
    return lp(saw, bright) * np.exp(-t * 10) * (1 - np.exp(-t * 2000)) * g
def bell(m, g=0.2, d=1.6):
    t = tt(d); f = hz(m)
    return sum(np.sin(2 * np.pi * f * r * t) * np.exp(-t * dk) * a for r, dk, a in ((1, 2.2, 1), (2.76, 4, .4), (5.4, 7, .2), (8.9, 11, .1))) * (1 - np.exp(-t * 3000)) * g
def sub(m, g=0.35, d=2.4):
    t = tt(d); return np.sin(2 * np.pi * hz(m) * t) * adsr(len(t), 0.02, 0.3, 0.75, 0.25) * g
def pad(ms, d, g=0.07, cutoff=1800):
    t = tt(d); x = np.zeros(len(t))
    for m in ms:
        for det in (-0.07, 0.07):
            x += sum(np.sin(2 * np.pi * hz(m + det) * h * t) / h for h in range(1, 5))
    return lp(x, cutoff) * adsr(len(t), 0.4, 0.3, 0.8, 0.8) * g / max(1, len(ms))
def supersaw(ms, d, g=0.08, cutoff=5000):
    """Future-bass stab chord (detuned saws), short."""
    t = tt(d); x = np.zeros(len(t))
    for m in ms:
        for det in (-0.12, -0.05, 0, 0.05, 0.12):
            x += 2 * ((hz(m + det) * t + _rng.uniform()) % 1) - 1
    return lp(x, cutoff) * adsr(len(t), 0.005, 0.12, 0.55, 0.12) * g / max(1, len(ms) * 2.5)
def kick(g=0.6):
    t = tt(0.32); f = 48 + 110 * np.exp(-t * 32)
    return fm(f, t) * np.exp(-t * 9) * g
def clap(g=0.25):
    t = tt(0.22); x = bp(noise(len(t)), 900, 6000)
    e = np.exp(-t * 28) + 0.5 * np.exp(-np.maximum(0, t - 0.011) * 28) * (t > 0.011) + 0.4 * np.exp(-np.maximum(0, t - 0.022) * 28) * (t > 0.022)
    return x * e * g
def snare(g=0.25):
    t = tt(0.25); return (bp(noise(len(t)), 1200, 9000) * np.exp(-t * 22) + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.5) * g
def hat(g=0.06, open_=False):
    t = tt(0.25 if open_ else 0.06); return hp(noise(len(t)), 7000) * np.exp(-t * (14 if open_ else 70)) * g
def shaker(g=0.08):
    t = tt(0.09); return hp(noise(len(t)), 5000) * np.exp(-t * 55) * g
def lowhit(g=0.9, d=3.5):
    t = tt(d); f = 36 + 60 * np.exp(-t * 6)
    return (fm(f, t) * np.exp(-t * 0.9) + lp(noise(len(t)), 1500) * np.exp(-t * 20) * 0.4) * g
def riser(d=1.5, g=0.2):
    t = tt(d); f = 200 + 2400 * (t / d) ** 2
    return (fm(f, t) * 0.25 + bp(noise(len(t)), 800, 9000) * 0.75) * (t / d) ** 2.2 * g
def reverse_swell(d, g=0.25, chord=(62, 66, 69, 74)):
    t = tt(d); x = pad(list(chord), d, 1.0) + hp(noise(len(t)), 3000) * 0.15
    return x * (t / d) ** 2.5 * g

# ── SFX: one per kind of picture event ──────────────────────────────────────
def whoosh(d=0.4, g=0.2, up=True):
    t = tt(d); x = noise(len(t)); out = np.zeros(len(t)); seg = int(0.01 * SR)
    for i in range(0, len(t), seg):
        k = i / len(t); fc = (400 + 5000 * k ** 1.5) if up else (5400 - 5000 * k ** 0.7)
        out[i:i + seg] = bp(x[i:i + seg], max(80, fc * 0.6), min(20000, fc * 1.5))
    return out * np.sin(np.pi * t / d) ** 1.5 * g
def suck(d=0.35, g=0.2):
    """A reversed whoosh that pulls into a slam."""
    return whoosh(d, g, True)[::-1] * np.linspace(0.3, 1, int(SR * d)) ** 2
def zip_(d=0.3, g=0.12):
    t = tt(d); f = 900 + 3800 * (t / d)
    return (fm(f, t) * 0.3 + bp(noise(len(t)), 2000, 9000) * 0.7) * np.sin(np.pi * t / d) * g
def pop(f=900, g=0.18):
    t = tt(0.1); return np.sin(2 * np.pi * f * (1 + 1.6 * np.exp(-t * 55)) * t) * np.exp(-t * 40) * g
def tick(f=2600, g=0.12):
    t = tt(0.04); return np.sin(2 * np.pi * f * t) * np.exp(-t * 140) * g
def key_tick(g=0.08):
    t = tt(0.05); return (hp(noise(len(t)), 3000) * np.exp(-t * 160) + np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 200) * 0.4) * g
def click(g=0.3):
    t = tt(0.08); return (lp(noise(len(t)), 3500) * np.exp(-t * 90) + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 50) * 0.6) * g
def tap(g=0.22):
    t = tt(0.06); return (np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 90) + lp(noise(len(t)), 5000) * np.exp(-t * 200) * 0.4) * g
def tinkle(f, g=0.08):
    t = tt(0.5); return sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * (8 + 6 * k)) / k for k in (1, 2.7, 5.1)) * g
def glass(g=0.1):
    return mixadd(*(tinkle(f, g / 3) for f in (2400, 3100, 4100)))
def thump(g=0.6):
    t = tt(0.3); f = 70 + 90 * np.exp(-t * 30)
    return (fm(f, t) * np.exp(-t * 14) + lp(noise(len(t)), 900) * np.exp(-t * 35) * 0.5) * g
def impact(g=0.7):
    """A slam: sub boom + a short metallic crack (mostly low end, so the voice stays clear)."""
    t = tt(1.2); f = 40 + 70 * np.exp(-t * 18)
    boom = fm(f, t) * np.exp(-t * 3.2)
    crack = hp(noise(len(t)), 1800) * np.exp(-t * 35) * 0.35 + bp(noise(len(t)), 300, 1500) * np.exp(-t * 16) * 0.3
    return (boom + crack) * g
def crack(g=0.5):
    t = tt(0.25); return (hp(noise(len(t)), 1500) * np.exp(-t * 30) + bp(noise(len(t)), 200, 1200) * np.exp(-t * 18) * 0.6) * g
def fire(d, g=0.06):
    t = tt(d); x = lp(noise(len(t)), 900) * 0.6
    for _ in range(int(d * 26)):
        i = _rng.integers(0, max(1, len(t) - 600)); x[i:i + 600] += hp(noise(600), 2500) * np.exp(-np.arange(600) / 90) * _rng.uniform(0.3, 1)
    return x * adsr(len(t), 0.08, 0.1, 1, 0.3) * g
def flutter(d=0.8, g=0.1):
    t = tt(d); return bp(noise(len(t)), 600, 3000) * (0.5 + 0.5 * np.sin(2 * np.pi * 11 * t)) ** 2 * np.sin(np.pi * t / d) * g
def falling(d=0.3, g=0.12):
    t = tt(d); f = 1800 - 1300 * (t / d) ** 0.8
    return fm(f, t) * np.sin(np.pi * t / d) * g
def shimmer(d=0.6, g=0.06):
    t = tt(d); return sum(np.sin(2 * np.pi * hz(m) * t) for m in (86, 90, 93, 98)) / 4 * np.exp(-t * 4) * (1 - np.exp(-t * 200)) * g
def frost(d=0.5, g=0.08):
    t = tt(d); return hp(noise(len(t)), 6000) * (np.abs(np.sin(2 * np.pi * 37 * t)) ** 6) * np.exp(-t * 4) * g
def lock(g=0.35):
    """A heavy click + sub (something locking into place)."""
    return mixadd(click(g), np.concatenate([np.zeros(int(0.006 * SR)), sub(38, g * 0.6, 0.35)]))

def mixadd(*xs):
    """Sum mono sounds of different lengths."""
    n = max(len(x) for x in xs); out = np.zeros(n)
    for x in xs: out[:len(x)] += x
    return out
def air(d, g=0.04):
    t = tt(d); return bp(noise(len(t)), 300, 2500) * g

SFX = {
    'whoosh': lambda size=0.6: whoosh(0.25 + 0.3 * size, 0.08 + 0.16 * size, True),
    'whoosh_down': lambda size=0.6: whoosh(0.25 + 0.3 * size, 0.08 + 0.16 * size, False),
    'suck': lambda size=0.6: suck(0.3, 0.12 + 0.12 * size),
    'zip': lambda size=0.6: zip_(0.2 + 0.25 * size, 0.06 + 0.06 * size),
    'pop': lambda size=0.6: pop(1300 - 700 * size, 0.08 + 0.12 * size),
    'tick': lambda size=0.6: tick(2200 + 900 * (1 - size), 0.04 + 0.05 * size),
    'key': lambda size=0.6: key_tick(0.05 + 0.05 * size),
    'click': lambda size=0.6: click(0.15 + 0.25 * size),
    'tap': lambda size=0.6: tap(0.12 + 0.15 * size),
    'glass': lambda size=0.6: glass(0.06 + 0.08 * size),
    'thump': lambda size=0.6: thump(0.2 + 0.5 * size),
    'impact': lambda size=0.8: impact(0.4 + 0.5 * size),
    'crack': lambda size=0.6: crack(0.2 + 0.3 * size),
    'shimmer': lambda size=0.6: shimmer(0.4 + 0.4 * size, 0.03 + 0.04 * size),
    'flutter': lambda size=0.6: flutter(0.6 + 0.4 * size, 0.05 + 0.06 * size),
    'falling': lambda size=0.6: falling(0.3, 0.06 + 0.08 * size),
    'frost': lambda size=0.6: frost(0.5, 0.05 + 0.05 * size),
    'lock': lambda size=0.6: lock(0.2 + 0.25 * size),
    'riser': lambda size=0.6: riser(0.8 + 1.0 * size, 0.08 + 0.14 * size),
    'tinkle': lambda size=0.6: tinkle(2200 + 1600 * (1 - size), 0.04 + 0.05 * size),
    'fire': lambda size=0.6: fire(1.2 + size, 0.03 + 0.04 * size),
}

# ── Clipzing's sonic logo (composed for the brand; use these, never another app's sounds) ──
def clip_ready(g=0.4):
    """'Clip ready': two bright bell notes, up a fifth, with a sparkle. Plays when a clip is done / a goal is hit."""
    out = np.zeros(int(SR * 1.4))
    for m, t0 in ((86, 0.0), (93, 0.09)):
        t = tt(1.3); f = hz(m)
        x = (np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 6) + 0.25 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 10)) * np.exp(-t * 3.4)
        i = int(t0 * SR); out[i:i + len(x)] += (x * (1 - np.exp(-t * 1500)))[: len(out) - i]
    return out * g
def published(g=0.42):
    """'Published': a short bright arpeggio landing on a full D-major chord. The sonic button at the end."""
    out = np.zeros(int(SR * 2.2))
    for k, m in enumerate((74, 78, 81, 86)):
        x = marimba(m, 0.9, 0.7); y = mallet(m + 12, 0.4, 0.5); x[:len(y)] += y
        i = int(k * 0.085 * SR); out[i:i + len(x)] += x[: len(out) - i]
    ch = felt([62, 66, 69, 74, 78], 1.0, 1.8) + pad([62, 69, 74, 78], 1.8, 0.8)
    i = int(0.34 * SR); out[i:i + len(ch)] += ch[: len(out) - i] * 1.4
    return out * g
def logo_sting(g=0.8, chord=(50, 62, 66, 69, 74, 78)):
    """The hero landing: a full chord + low hit, ringing out (lands ON the logo / Zing landing)."""
    x = felt(list(chord), 0.22, 4.6); y = pad(list(chord[1:]), 4.4, 0.12); z = lowhit(0.85)
    n = max(len(x), len(y), len(z)); out = np.zeros(n)
    out[:len(x)] += x; out[:len(y)] += y; out[:len(z)] += z
    return out * g
def logo_hit(g=0.85):
    """The low half of the sting, sub only: lands ON a spoken brand name without masking it."""
    return lp(lowhit(1.0), 160) * g
def logo_chord(g=0.8, chord=(50, 62, 66, 69, 74, 78)):
    """The chord half of the sting: place it just AFTER the brand name is spoken."""
    return mixadd(felt(list(chord), 0.22, 4.6), pad(list(chord[1:]), 4.4, 0.12)) * g
HERO = {'clip_ready': clip_ready, 'published': published, 'logo_sting': logo_sting, 'logo_hit': logo_hit, 'logo_chord': logo_chord}

# ── an owner-supplied SFX library (preferred when present) ─────────────────
class Library:
    """Index of the owner's SFX folder (env SFX_LIBRARY). Picks a file per cue kind by filename keywords,
    deterministically, trims and fades it. Falls back to the synthesized SFX when nothing matches."""
    KEYS = {'whoosh': ['whoosh', 'swoosh', 'swish'], 'whoosh_down': ['whoosh', 'swoosh'], 'suck': ['reverse', 'suck', 'rev'],
            'pop': ['pop', 'bubble'], 'tick': ['tick'], 'key': ['key', 'type', 'typing'], 'click': ['click', 'ui'],
            'tap': ['tap', 'touch'], 'glass': ['glass', 'ding'], 'thump': ['thump', 'hit', 'punch'], 'impact': ['impact', 'boom', 'slam', 'hit'],
            'riser': ['riser', 'rise'], 'shimmer': ['shimmer', 'sparkle', 'magic'], 'lock': ['lock', 'latch'], 'zip': ['zip', 'swipe']}
    def __init__(self, root=None):
        self.root = root or os.environ.get('SFX_LIBRARY')
        self.files = []
        if self.root and os.path.isdir(self.root):
            for ext in ('wav', 'aif', 'aiff', 'mp3', 'flac'):
                self.files += glob.glob(os.path.join(self.root, '**', f'*.{ext}'), recursive=True)
        self._cache = {}
    def pick(self, kind, seed=0):
        keys = self.KEYS.get(kind)
        if not keys or not self.files: return None
        cands = sorted(f for f in self.files if any(k in os.path.basename(f).lower() for k in keys))
        if not cands: return None
        f = cands[seed % len(cands)]
        if f not in self._cache: self._cache[f] = read_audio(f)
        x = self._cache[f]
        return x[: int(SR * 2.5)]

def read_audio(path):
    """Any audio file → mono float64 at SR (via ffmpeg)."""
    raw = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)

# ── music ───────────────────────────────────────────────────────────────────
STYLES = {
    # bright, modern, premium, never kiddy (The Path)
    'mallet_pop': dict(bpm=100, root=62, mode='major'),
    # punchy future bass / house, every hit on the grid (RAID)
    'future_bass': dict(bpm=144, root=66, mode='minor'),
    # Apple-keynote minimal electronic pop (Just Ask / Thinking gets faster)
    'keynote': dict(bpm=112.5, root=66, mode='minor'),
    # dark, cinematic, serious narration (grind / motivation)
    'cinematic': dict(bpm=80, root=57, mode='minor'),
}
def chords(root, mode):
    if mode == 'major':   # I maj7 · V · vi · IV maj7
        return [([root, root + 4, root + 7, root + 11], root - 24), ([root - 5, root - 1, root + 2, root + 7], root - 29),
                ([root - 3, root, root + 4, root + 7], root - 27), ([root - 7, root - 3, root, root + 4], root - 31)]
    # i · VI · III · VII  (resolving lift)
    return [([root, root + 3, root + 7, root + 10], root - 24), ([root - 4, root, root + 3, root + 7], root - 28),
            ([root + 3, root + 7, root + 10, root + 14], root - 21), ([root - 2, root + 2, root + 5, root + 9], root - 26)]

def score(end, style='mallet_pop', drop=None, lift=None, breath=None, hit=None, stop=None, bpm=None, root=None, mode=None, intensity=1.0, sting=True):
    """Original music for a film of `end` seconds, arranged around its moments:
      drop    the groove (kick / claps / hats) starts here; the bar grid is aligned so the drop is a downbeat
      lift    a lift (higher line, open pad) from here
      breath  near silence + a reversed swell into `hit`
      stop    a TRUE dead stop (digital silence) until hit (RAID)
      hit     the hero landing: full chord + low hit, ringing under the end card
      sting   False when the film places `logo_sting` itself as a hero cue (so it isn't ducked under a word)
    Returns a stereo float array (len = end × SR)."""
    st = dict(STYLES[style]); st.update({k: v for k, v in dict(bpm=bpm, root=root, mode=mode).items() if v is not None})
    beat = 60.0 / st['bpm']; bar = beat * 4
    prog_ = chords(st['root'], st['mode'])
    bus = Bus(end)
    anchor = drop if drop is not None else 0.0
    t0 = anchor - math.ceil(anchor / bar) * bar if anchor else 0.0
    quiet_from = min([x for x in (breath, stop) if x is not None], default=hit if hit is not None else end)
    k = 0; tb = t0
    while tb < quiet_from:
        ch, rootn = prog_[k % 4]
        lifted = lift is not None and tb >= lift - 0.3
        grooved = drop is not None and tb >= drop - 0.01
        if tb + bar > 0:
            if style == 'mallet_pop':
                bus.place(felt(ch, 0.11, bar + 0.4), tb); bus.place(sub(rootn, 0.3, bar), tb)
                arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[0] + 24, ch[2] + 12]
                for j in range(8):
                    tk = tb + j * beat / 2
                    if 0 <= tk < quiet_from:
                        bus.place(marimba(arp[j] + (12 if lifted and j % 4 == 3 else 0), 0.17 if j % 2 == 0 else 0.11), tk, 1, (j % 3 - 1) * 0.3)
            elif style == 'future_bass':
                bus.place(sub(rootn, 0.32, bar), tb)
                for j in (0, 3, 6, 10, 12, 14):   # syncopated 16th stabs
                    tk = tb + j * beat / 4
                    if tk < quiet_from and (grooved or j in (0, 6)): bus.place(supersaw([m + 12 for m in ch], beat / 2, 0.09), tk, 1, (j % 2 - 0.5) * 0.4)
            elif style == 'keynote':
                bus.place(pad(ch, bar + 0.3, 0.05, 2200), tb); bus.place(sub(rootn, 0.26, bar), tb)
                for j in range(8):
                    tk = tb + j * beat / 2
                    if tk < quiet_from: bus.place(pluck(ch[j % 4] + 12 + (12 if lifted and j % 4 == 2 else 0), 0.12 if j % 2 == 0 else 0.07), tk, 1, (j % 2 - 0.5) * 0.5)
            else:  # cinematic
                bus.place(pad(ch, bar + 0.6, 0.08, 1400), tb); bus.place(sub(rootn, 0.28, bar), tb)
                bus.place(felt([ch[0] + 12, ch[2] + 12], 0.09, bar), tb + beat * 2)
            if grooved:
                for j in range(4):
                    tk = tb + j * beat
                    if tk >= quiet_from: continue
                    bus.place(kick(0.55 * intensity), tk)
                    if j % 2 == 1: bus.place((clap if style != 'cinematic' else snare)(0.2 * intensity), tk, 1, 0.15)
                    for h in range(4 if style != 'cinematic' else 2):
                        th = tk + h * beat / (4 if style != 'cinematic' else 2)
                        if th < quiet_from: bus.place((shaker if style == 'mallet_pop' else hat)(0.06 if h % 2 else 0.085), th, 1, 0.4)
            if lifted:
                for j in range(4):
                    tk = tb + j * beat + beat / 2
                    if tk < quiet_from: bus.place((mallet if style == 'mallet_pop' else pluck)(ch[(j + 1) % 4] + 24, 0.07), tk, 1, -0.3)
                bus.place(pad(ch, bar, 0.045), tb)
        k += 1; tb += bar
    if breath is not None and hit is not None:
        bus.place(reverse_swell(hit - breath + 0.02, 0.33), breath)
    if stop is not None and hit is not None:
        bus.buf[int(stop * SR): int(hit * SR)] = 0.0      # true digital silence (re-cleared after reverb in mix)
    if hit is not None:
        if sting: bus.place(logo_sting(0.9), hit)
        for j, m in enumerate((74, 78, 81, 86, 81, 78)):
            tj = hit + 2.2 + j * beat / 2
            if tj < end - 0.3: bus.place(marimba(m, 0.06), tj, 1, (j % 3 - 1) * 0.4)
    return bus.buf

# ── the mix ─────────────────────────────────────────────────────────────────
def reverb(x, secs=1.8, wet=0.16, seed=5):
    rng = np.random.default_rng(seed)
    t = tt(secs); ir = lp(rng.standard_normal(len(t)) * np.exp(-t * 3.6), 6000); ir /= np.sqrt((ir ** 2).sum()) * 4
    return x + np.stack([fftconvolve(x[:, c], ir)[: len(x)] for c in range(2)], 1) * wet

def env_follow(x, att=0.002, rel=0.35):
    a = np.abs(x); out = np.zeros_like(a); v = 0.0
    ga, gr = math.exp(-1 / (att * SR)), math.exp(-1 / (rel * SR)); step = 16
    for i in range(0, len(a), step):
        m = a[i:i + step].max()
        v = m + (v - m) * (ga ** step if m > v else gr ** step); out[i:i + step] = v
    return out

def load_voice(path, target_lufs=-16.0):
    """The chosen take, high-passed, gently compressed and normalised to target LUFS (mono float)."""
    out = os.path.splitext(path)[0] + '_norm.wav'
    subprocess.check_call(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', path, '-af',
                           f'highpass=f=80,acompressor=threshold=-20dB:ratio=2.5:attack=6:release=120:makeup=2,loudnorm=I={target_lufs}:TP=-2:LRA=7',
                           '-ar', str(SR), '-ac', '1', out])
    sr, v = wavfile.read(out)
    return v.astype(np.float64) / (32768 if v.dtype == np.int16 else 1)

def build_mix(end, words, vo_path, vo_offset, cues, music, hero_cues=(), outdir='audio', duck_db=-20.0, library=None, silence=None):
    """Mix voice + music + cue SFX + hero cues into stems and a raw mix in outdir. Returns stem paths.
    cues: adkit.timeline.Cues (kind, t, x, size, gain). hero_cues: [(name, t)] from HERO.
    silence: (a, b) a TRUE dead stop: music and sfx are zeroed there AFTER reverb (tails would fill it)."""
    os.makedirs(outdir, exist_ok=True)
    n = int(end * SR)
    voice = Bus(end)
    if vo_path: voice.place(load_voice(vo_path), vo_offset, 1.0)     # mono → centre (−3 dB/side keeps the stem at ≈ −16 LUFS)
    sfx = Bus(end); hero = Bus(end)
    lib = library or Library()
    for i, c in enumerate(sorted(cues, key=lambda c: c.t)):
        x = lib.pick(c.kind, seed=i) if lib.files else None
        if x is not None:
            x = x * (0.25 + 0.6 * c.size)
        elif c.kind in SFX:
            x = SFX[c.kind](c.size)
        else:
            raise KeyError(f'unknown cue kind {c.kind!r}; add it to adkit.audio.SFX')
        sfx.place(x, c.t, c.gain, max(-0.8, min(0.8, c.x * 0.7)))
    for name, t in hero_cues:
        hero.place(HERO[name](), t)
    # reverb FIRST, then duck: otherwise tails fill the dip under the words
    mus = reverb(music[:n] if len(music) >= n else np.pad(music, ((0, n - len(music)), (0, 0))), 2.2, 0.2)
    sfx_r = reverb(sfx.buf, 1.2, 0.1); hero_r = reverb(hero.buf, 1.8, 0.18)
    wm = words.mask(SR, n) if words is not None else np.zeros(n)
    k = int(0.03 * SR); wm = np.clip(np.convolve(wm, np.ones(k) / k, 'same'), 0, 1)
    he = env_follow(hero.buf[:, 0] + hero.buf[:, 1]); he = np.clip(he / (he.max() + 1e-9) * 6, 0, 1)
    depth = 1 - 10 ** (duck_db / 20)
    mus *= np.maximum(10 ** (duck_db / 20), 1 - depth * wm - 0.5 * he)[:, None]
    sfx_r *= (1 - 0.35 * wm - 0.3 * he)[:, None]
    hero_r *= (1 - 0.5 * wm)[:, None]          # hero cues dip 6 dB under a word too (a sting on the brand name masked it)
    if silence:
        a, b = int(silence[0] * SR), int(silence[1] * SR)
        mus[a:b] = 0; sfx_r[a:b] = 0
    fade = int(0.4 * SR); mus[-fade:] *= np.linspace(1, 0, fade)[:, None]
    stems = {'voice': voice.buf, 'music': mus * 0.9, 'sfx': sfx_r * 0.9, 'hero': hero_r}
    mix = sum(stems.values())
    peak = max(1.0, float(np.abs(mix).max()))
    paths = {}
    for name, buf in list(stems.items()) + [('mix_raw', mix)]:
        p = os.path.join(outdir, f'{name}.wav'); wavfile.write(p, SR, (buf / peak).astype(np.float32)); paths[name] = p
    json.dump([c.__dict__ for c in cues], open(os.path.join(outdir, 'cues.json'), 'w'), indent=1)
    return paths

def _loudnorm_json(path, extra=''):
    o = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    return json.loads(re.findall(r'\{[^{}]*\}', o)[-1])

def master(raw, out, target=-14.0, tp=-1.5):
    """Oversampled limiter at −2 dBFS, then a two-pass LINEAR loudnorm (no pumping) to −14 LUFS / ≤ −1.25 dBTP."""
    lim = os.path.splitext(out)[0] + '_lim.wav'
    subprocess.check_call(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', raw, '-af',
                           'aresample=192000,alimiter=limit=0.8:attack=1:release=60:level=false,aresample=48000', '-c:a', 'pcm_f32le', lim])
    m = _loudnorm_json(lim)
    af = (f"loudnorm=I={target}:TP={tp}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.check_call(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', lim, '-af', af, '-ar', str(SR), '-c:a', 'pcm_s24le', out])
    os.remove(lim)
    return measure(out)

def measure(path):
    """EBU R128 integrated loudness, true peak (dBTP) and LRA, as the platforms measure them."""
    o = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    summ = o[o.rfind('Summary:'):]
    g = lambda k: float(re.search(rf'{k}:\s+(-?[\d.]+|-inf)', summ).group(1).replace('-inf', '-99'))
    return {'lufs': g('I'), 'true_peak': g('Peak'), 'lra': g('LRA')}

# ── measuring what you can't hear ───────────────────────────────────────────
def word_margins(voice_wav, music_wav, words, phone=False):
    """dB of voice over music on the voiced frames of every word. phone=True simulates a phone speaker
    (mono, 250 Hz – 7 kHz band) where low-end music disappears but mids compete."""
    _, v = wavfile.read(voice_wav); _, m = wavfile.read(music_wav)
    v = v.mean(1) if v.ndim > 1 else v; m = m.mean(1) if m.ndim > 1 else m
    if phone: v, m = bp(v, 250, 7000), bp(m, 250, 7000)
    else: v, m = hp(v, 60), hp(m, 60)
    f = int(0.02 * SR); out = []
    for x in words.list:
        a, b = int(x['start'] * SR), int(x['end'] * SR)
        fr = [(np.sqrt((v[i:i + f] ** 2).mean()), np.sqrt((m[i:i + f] ** 2).mean())) for i in range(a, max(a + 1, b - f), f)]
        if not fr: continue
        pk = max(r for r, _ in fr); act = [(r, q) for r, q in fr if r > pk * 0.3] or fr
        g = 20 * np.log10(np.mean([r for r, _ in act]) / (np.mean([q for _, q in act]) + 1e-9) + 1e-12)
        out.append((round(float(g), 1), x['w'], round(x['start'], 2)))
    return sorted(out)

def transcribe(path, model='base'):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device='cpu', compute_type='int8', cpu_threads=4)
    segs, _ = m.transcribe(path, language='en', vad_filter=True)
    return ' '.join(s.text.strip() for s in segs)

def intelligibility(dry_vo, final_mix):
    """Whisper reads the dry voice and the final mix; any word that changes is masked by something in the mix."""
    a, b = transcribe(dry_vo), transcribe(final_mix)
    na = re.findall(r"[a-z0-9']+", a.lower()); nb = re.findall(r"[a-z0-9']+", b.lower())
    import difflib
    diff = [(op, na[i1:i2], nb[j1:j2]) for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, na, nb).get_opcodes() if op != 'equal']
    return {'dry': a, 'mix': b, 'changed': diff}

def report(outdir, words, master_stats, check_whisper=True, dry_vo=None):
    """Print + save the audio QA: loudness, true peak, worst word margins (full range and phone speaker)."""
    full = word_margins(os.path.join(outdir, 'voice.wav'), os.path.join(outdir, 'music.wav'), words)
    phone = word_margins(os.path.join(outdir, 'voice.wav'), os.path.join(outdir, 'music.wav'), words, phone=True)
    rep = {'master': master_stats, 'worst_word_margins_db': full[:5], 'worst_phone_margins_db': phone[:5]}
    if check_whisper and dry_vo:
        rep['whisper'] = intelligibility(dry_vo, os.path.join(outdir, 'final_audio.wav'))
    ok = master_stats['lufs'] > -14.6 and master_stats['lufs'] < -13.4 and master_stats['true_peak'] <= -1.25 and (not full or full[0][0] >= 12)
    rep['pass'] = bool(ok and (not rep.get('whisper') or not rep['whisper']['changed']))
    json.dump(rep, open(os.path.join(outdir, 'audio_qa.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'whisper'}, indent=1))
    if rep.get('whisper'): print('whisper changed words:', rep['whisper']['changed'] or 'none')
    return rep
