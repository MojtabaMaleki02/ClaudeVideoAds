#!/usr/bin/env python3
"""Start a new Clipzing ad project.

  python3 new_ad.py "Two Hours In" [--dir ~/Desktop/clipzing-ads] [--fmt 9x16] [--long]

Creates <dir>/<slug>/ with: brief/PROMPT.md (from the template), film.py and mix.py (from the templates),
voice/, audio/, assets/, out/, and a README with the commands for every phase.
"""
import argparse
import os
import re
import shutil

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('title'); ap.add_argument('--dir', default='~/Desktop/clipzing-ads')
    ap.add_argument('--fmt', default='9x16')
    ap.add_argument('--long', action='store_true', help='a chaptered long-form film (16:9 first) instead of a short')
    a = ap.parse_args()
    slug = re.sub(r'[^a-z0-9]+', '-', a.title.lower()).strip('-')
    root = os.path.join(os.path.expanduser(a.dir), slug)
    if os.path.exists(root): raise SystemExit(f'{root} exists. Pick another title or remove it.')
    for d in ('brief', 'voice', 'audio', 'assets', 'out', 'qa'): os.makedirs(os.path.join(root, d))
    brief = open(os.path.join(SKILL, 'templates', 'brief.md')).read().replace('<TITLE>', a.title)
    open(os.path.join(root, 'brief', 'PROMPT.md'), 'w').write(brief)
    film = open(os.path.join(SKILL, 'templates', 'film_long.py' if a.long else 'film_short.py')).read().replace('<TITLE>', a.title)
    if a.long and a.fmt == '9x16': a.fmt = '16x9'
    film = film.replace("os.path.expanduser('~/shorten/.claude/skills/clipzing-ads/toolkit')", repr(os.path.join(SKILL, 'toolkit')))
    open(os.path.join(root, 'film.py'), 'w').write(film)
    mix = open(os.path.join(SKILL, 'templates', 'mix.py')).read()
    mix = mix.replace("os.path.expanduser('~/shorten/.claude/skills/clipzing-ads/toolkit')", repr(os.path.join(SKILL, 'toolkit')))
    open(os.path.join(root, 'mix.py'), 'w').write(mix)
    tk = os.path.join(SKILL, 'toolkit')
    py = '~/shorten/shortn-be/.venv/bin/python'
    open(os.path.join(root, 'README.md'), 'w').write(f"""# {a.title}

Phase commands (run from this folder; {py} has numpy, Pillow, OpenCV, scipy, faster-whisper):

    # voice: audition, then lock the timings of the chosen take
    {py} -c "import sys; sys.path.insert(0,'{tk}'); from adkit import voice; voice.tts(open('brief/script.txt').read(), 'voice', direction=open('brief/voice_direction.txt').read())"
    cp voice/<chosen>.wav voice/vo.wav
    {py} -c "import sys; sys.path.insert(0,'{tk}'); from adkit import voice; voice.timings('voice/vo.wav', 'voice/words.json', open('brief/script.txt').read())"

    # picture: stills → preview → finals
    {py} {tk}/render.py film.py stills out/stills 0.2 1.0 3.0 6.0 9.0 11.5 --fmt {a.fmt}
    {py} {tk}/render.py film.py preview out/preview_{a.fmt}.mp4 --fmt {a.fmt}
    {py} mix.py
    {py} {tk}/render.py film.py all out/frames_9x16 --fmt 9x16 -j 8
    {py} {tk}/render.py film.py all out/frames_16x9 --fmt 16x9 -j 8
    {py} {tk}/render.py encode out/frames_9x16 out/{slug}-9x16.mp4 --audio audio/final_audio.wav
    {py} -c "import sys; sys.path.insert(0,'{tk}'); from adkit import qa; print(qa.motion_audit('out/frames_9x16', 60))"
""")
    print(root)

if __name__ == '__main__':
    main()
