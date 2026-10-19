"""adkit.qa: check it before anyone sees it.

  motion_audit(frames_dir, fps)      missing frames, near-black runs, hard cuts, one-frame pops, static stretches,
                                     and the fastest moments (look at those frames by eye for stepped blur copies)
  safe_zones(png, out)               TikTok / Shorts UI zones drawn over a 9:16 still (text must stay clear of them)
  claims_lint(paths)                 every on-screen / spoken string against what Clipzing can truthfully claim
  strip(frames_dir, i, out)          5 consecutive frames side by side (inspect a transition)
"""
import json
import os
import re

import cv2
import numpy as np

def _small(path, w=240):
    im = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    h = int(im.shape[0] * w / im.shape[1])
    return cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32)

def motion_audit(frames_dir, fps, expect=None, out_json=None):
    fs = sorted(f for f in os.listdir(frames_dir) if re.match(r'\d+\.png$', f))
    rep = {'frames': len(fs)}
    if expect is not None and len(fs) != expect:
        idx = {int(f[:-4]) for f in fs}
        rep['missing'] = [i for i in range(expect) if i not in idx][:50]
    ims = [_small(os.path.join(frames_dir, f)) for f in fs]
    diffs = np.array([np.abs(ims[i] - ims[i - 1]).mean() for i in range(1, len(ims))])
    means = np.array([im.mean() for im in ims])
    # near-black runs (> 0.3 s reads as "the video ended")
    dark = means < 6
    runs, s = [], None
    for i, d in enumerate(dark):
        if d and s is None: s = i
        if (not d or i == len(dark) - 1) and s is not None:
            e = i if not d else i + 1
            if (e - s) / fps > 0.3 and s > 2: runs.append((s, e))
            s = None
    rep['black_runs'] = runs
    local = np.convolve(diffs, np.ones(9) / 9, 'same')
    ratio = diffs / np.maximum(local, 0.5)
    rep['hard_cuts'] = [int(i) + 1 for i in np.where((diffs > 18) & (ratio > 3))[0]]
    # one-frame pop: frame i differs from both neighbours, while its neighbours agree with each other
    pops = []
    for i in range(1, len(ims) - 1):
        a, b = diffs[i - 1], diffs[i]
        if a > 6 and b > 6:
            skip = np.abs(ims[i + 1] - ims[i - 1]).mean()
            if skip < 0.35 * min(a, b): pops.append(i)
    rep['one_frame_pops'] = pops
    # static stretches (> 1 s without visible change; holds should still breathe)
    stat, s = [], None
    for i, d in enumerate(diffs):
        if d < 0.15 and s is None: s = i
        if (d >= 0.15 or i == len(diffs) - 1) and s is not None:
            if (i - s) / fps > 1.0: stat.append((s, i, round((i - s) / fps, 2)))
            s = None
    rep['static_stretches'] = stat
    top = np.argsort(-diffs)[:10]
    rep['fastest_frames_check_by_eye'] = sorted(int(i) + 1 for i in top)
    rep['pass'] = not (rep.get('missing') or runs or rep['hard_cuts'] or pops)
    if out_json: json.dump(rep, open(out_json, 'w'), indent=1)
    return rep

def strip(frames_dir, center, out, n=5, w=360):
    ims = []
    for i in range(center - n // 2, center + n // 2 + 1):
        p = os.path.join(frames_dir, f'{i:05d}.png')
        if os.path.exists(p):
            im = cv2.imread(p); h = int(im.shape[0] * w / im.shape[1]); ims.append(cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA))
    if ims: cv2.imwrite(out, np.hstack(ims))
    return out

# 9:16 UI zones at 1080×1920 (measured from the apps; leave them clear of text and faces)
ZONES = {
    'tiktok': [('right rail: like / comment / share', (930, 760, 1080, 1560)), ('caption + username', (0, 1500, 900, 1920)),
               ('top tabs', (0, 0, 1080, 210))],
    'shorts': [('right rail', (940, 900, 1080, 1620)), ('title + channel', (0, 1520, 920, 1920)), ('top bar', (0, 0, 1080, 160))],
}
def safe_zones(png, out, platforms=('tiktok', 'shorts')):
    im = cv2.imread(png); H, W = im.shape[:2]; k = W / 1080
    over = im.copy()
    cols = {'tiktok': (85, 44, 254), 'shorts': (51, 0, 255)}
    for p in platforms:
        for _, (x0, y0, x1, y1) in ZONES[p]:
            cv2.rectangle(over, (int(x0 * k), int(y0 * k)), (int(x1 * k), int(y1 * k)), cols[p], -1)
    cv2.imwrite(out, cv2.addWeighted(over, 0.28, im, 0.72, 0))
    return out

# ── claims ──────────────────────────────────────────────────────────────────
FORBIDDEN = [
    (r'\blinked\s*in\b', 'Clipzing does not post to LinkedIn.'),
    (r'\b(post|publish|schedul)\w*\b[^.\n]{0,40}\b(instagram|reels)\b', 'Instagram/Reels: export format only; Clipzing cannot post there.'),
    (r'\bfacebook\b|\bx\.com\b|\btwitter\b|\bsnapchat\b|\bpinterest\b', 'Not a supported platform.'),
    (r'\bfree\s*trial\b|\btry (it )?(for )?free\b|\bfree plan\b', 'There is no free trial and no free plan.'),
    (r'\bmoney[- ]back\b|\bguarantee', 'The money-back guarantee was withdrawn; say "Cancel anytime".'),
    (r'\bauto[- ]?post\w*\b[^.\n]{0,30}\btiktok\b|\bpublish\w*\b[^.\n]{0,20}\bto tiktok\b', 'TikTok gets DRAFTS; Clipzing never publishes to TikTok.'),
    (r'\bschedul\w*\b[^.\n]{0,30}\btiktok\b', 'TikTok drafts cannot be scheduled for later.'),
    (r'\b(guarantee|predict)\w*\b[^.\n]{0,30}\b(views|viral)\b|\bgo viral\b', 'The score ranks clips; it does not predict views.'),
    (r'\bunlimited (videos|clips|shorts)\b', 'Plans meter shorts and processing minutes per month.'),
    (r'\b[3-9]\s*(hour|hr)s?\b[^.\n]{0,20}\bvideo', 'Videos are up to 2 hours.'),
    (r'\bwatermark\b', 'Check wording: Clipzing adds NO watermark on paid plans.'),
    (r'\bstored forever\b|\bforever\b[^.\n]{0,20}\bclips\b', 'Clips are kept 24 / 48 / 72 hours by plan.'),
]
def claims_lint(paths_or_text):
    """Scan scripts / film code / briefs for claims Clipzing can't make. Returns [(file, line, text, why)]."""
    hits = []
    items = paths_or_text if isinstance(paths_or_text, (list, tuple)) else [paths_or_text]
    for it in items:
        txt, name = (open(it).read(), it) if os.path.exists(str(it)) else (str(it), '<text>')
        for n, line in enumerate(txt.splitlines(), 1):
            if re.search(r'claims_lint|FORBIDDEN', line): continue
            for pat, why in FORBIDDEN:
                if re.search(pat, line, re.I): hits.append((name, n, line.strip()[:120], why))
    return hits
