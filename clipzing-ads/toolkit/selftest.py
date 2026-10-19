#!/usr/bin/env python3
"""Check the install in about a minute: python3 toolkit/selftest.py

Renders a few stills of both templates (9:16 and 16:9, small), synthesizes every SFX, hero cue and music style,
masters a short mix, and lints a known-bad line. Prints PASS/FAIL per check.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
PY = sys.executable
ok = True

def check(name, fn):
    global ok
    try:
        fn(); print(f'PASS  {name}')
    except Exception as e:  # noqa: BLE001
        ok = False; print(f'FAIL  {name}: {str(e)[:300]}')

def tools():
    for t in ('ffmpeg', 'ffprobe'):
        assert shutil.which(t), f'{t} not on PATH'
    import cv2, numpy, PIL, scipy  # noqa: F401,E401

def library():
    for p in ('zing/idle', 'zing/slam', 'zing/land', 'zing/cheer', 'footage/closeup', 'footage/wide', 'screens'):
        assert os.path.isdir(os.path.join(SKILL, 'library', p)), f'library/{p} missing (see SKILL.md › Capture)'
    for p in ('wordmark.png', 'wordmark-white.png', 'icon.png'):
        assert os.path.exists(os.path.join(SKILL, 'assets', 'brand', p)), f'assets/brand/{p} missing'

def templates():
    d = tempfile.mkdtemp(prefix='adkit_selftest_')
    for tpl, times in (('film_short.py', ['0.3', '1.0', '4.6', '10.8']), ('film_long.py', ['1.4', '9.6', '42.5'])):
        shutil.copy(os.path.join(SKILL, 'templates', tpl), os.path.join(d, 'film.py'))
        for fmt in ('9x16', '16x9'):
            r = subprocess.run([PY, os.path.join(HERE, 'render.py'), os.path.join(d, 'film.py'), 'stills', os.path.join(d, f'{tpl}_{fmt}'), *times,
                                '--fmt', fmt, '--scale', '0.25'], capture_output=True, text=True, env=dict(os.environ, ADKIT=HERE))
            assert r.returncode == 0, f'{tpl} {fmt}: {r.stderr[-400:]}'
    print(f'      stills in {d}')

def sound():
    sys.path.insert(0, HERE)
    os.environ.setdefault('SCALE', '0.25')
    from adkit import audio
    for k, f in audio.SFX.items():
        x = f(0.6); assert x.ndim == 1 and len(x) > 10, k
    for k, f in audio.HERO.items(): f()
    for st in audio.STYLES: audio.score(6, style=st, drop=2, lift=3, breath=4.5, hit=5)
    from adkit.timeline import Cues
    d = tempfile.mkdtemp(prefix='adkit_mix_')
    music = audio.score(6, style='keynote', drop=1, hit=5)
    paths = audio.build_mix(6, None, None, 0, Cues().add(1, 'impact').add(2, 'whoosh'), music, hero_cues=[('clip_ready', 3)], outdir=d)
    m = audio.master(paths['mix_raw'], os.path.join(d, 'final.wav'))
    assert -15.5 < m['lufs'] < -12.5 and m['true_peak'] <= -1.0, m

def claims():
    sys.path.insert(0, HERE)
    from adkit.qa import claims_lint
    assert claims_lint('Posts to TikTok, Instagram and LinkedIn. Free trial!'), 'lint missed false claims'
    assert not claims_lint('Paste one link. Ranked. Captioned. Ready.'), 'lint flagged a true line'

for name, fn in (('tools', tools), ('library', library), ('templates render (both formats)', templates), ('sound', sound), ('claims lint', claims)):
    check(name, fn)
print('ALL PASS' if ok else 'SOME CHECKS FAILED')
sys.exit(0 if ok else 1)
