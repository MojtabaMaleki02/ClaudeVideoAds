"""Sound for the film: original music (arranged on the film's own moments), every cue from film.cues(),
Clipzing's sonic logo from film.hero_cues(), the voice, a measured mix and a −14 LUFS master.

  python3 mix.py            → audio/final_audio.wav + stems + audio_qa.json (prints the QA)
"""
import os
import sys

TOOLKIT = os.environ.get('ADKIT', os.path.expanduser('~/shorten/.claude/skills/clipzing-ads/toolkit'))
sys.path.insert(0, TOOLKIT)
os.environ.setdefault('SCALE', '0.25')            # importing the film does not need full-size anything
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import film                                        # noqa: E402
from adkit import audio                            # noqa: E402

OUT = os.path.join(HERE, 'audio')
VO = os.path.join(HERE, 'voice', 'vo.wav')         # the chosen take (copy it here as vo.wav)

music = audio.score(film.END, **getattr(film, 'MUSIC', {}))
paths = audio.build_mix(film.END, film.WORDS, VO if os.path.exists(VO) else None, film.VO_OFF, film.cues(), music,
                        hero_cues=film.hero_cues() if hasattr(film, 'hero_cues') else (), outdir=OUT,
                        silence=getattr(film, 'SILENCE', None))
stats = audio.master(paths['mix_raw'], os.path.join(OUT, 'final_audio.wav'))
if film.WORDS:
    audio.report(OUT, film.WORDS, stats, check_whisper='--no-whisper' not in sys.argv, dry_vo=VO)
else:
    print('master', stats, '(no voice yet: word margins skipped)')
print('cues:', len(film.cues()))
