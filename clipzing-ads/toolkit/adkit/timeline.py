"""adkit.timeline: voice first, picture second. Word timestamps drive every slam, tile, tick and cut; picture events
drive every sound cue (one list, read by both the renderer and the mix, so a hit can never drift off its frame)."""
import json
import re
from dataclasses import dataclass, field

class Words:
    """Word timings of the chosen voice take (from voice.timings → words.json), shifted by the VO offset in the film.

    w = Words('voice/words.json', offset=0.45)
    w.t('clip')          start of the first "clip"
    w.t('one', 3)        start of the 3rd "one" (case-insensitive, punctuation ignored; counts every occurrence)
    w.end('clipzing')    end of that word
    w.after('top', 0.15) a hero cue's safe time: just after the word, never on it
    """
    def __init__(self, path, offset=0.0):
        raw = json.load(open(path))
        raw = raw['words'] if isinstance(raw, dict) else raw
        self.offset = offset
        self.list = [{'w': x.get('w', x.get('word', '')), 'start': float(x['start']) + offset, 'end': float(x['end']) + offset} for x in raw]

    @staticmethod
    def _norm(s): return re.sub(r"[^a-z0-9']", '', s.lower())

    def find(self, word, n=1):
        k = 0
        for x in self.list:
            if self._norm(x['w']) == self._norm(word):
                k += 1
                if k == n: return x
        raise KeyError(f'"{word}" #{n} is not in the take: {[x["w"] for x in self.list]}')

    def t(self, word, n=1): return self.find(word, n)['start']
    def end(self, word, n=1): return self.find(word, n)['end']
    def after(self, word, n=1, gap=0.15): return self.end(word, n) + gap
    def span(self): return (self.list[0]['start'], self.list[-1]['end'])
    def text(self): return ' '.join(x['w'] for x in self.list)

    def phrases(self, gap=0.28):
        """Split into phrases at the take's own pauses (cut only at pauses, never inside a line)."""
        out, cur = [], []
        for i, x in enumerate(self.list):
            if cur and x['start'] - cur[-1]['end'] > gap:
                out.append(cur); cur = []
            cur.append(x)
        if cur: out.append(cur)
        return [{'start': p[0]['start'], 'end': p[-1]['end'], 'text': ' '.join(x['w'] for x in p), 'words': p} for p in out]

    def mask(self, sr, n, pre=0.04, post=0.08):
        """A 0/1 sample mask that is 1 while any word is spoken (for ducking under every word)."""
        import numpy as np
        m = np.zeros(n, np.float32)
        for x in self.list:
            m[max(0, int((x['start'] - pre) * sr)): min(n, int((x['end'] + post) * sr))] = 1
        return m

@dataclass
class Cue:
    """A picture event that must have a sound. kind names a sound in adkit.audio.SFX (or a hero cue);
    x is the screen position (-1 left … 1 right, for panning), size 0..1 (for gain), gain is extra trim."""
    t: float
    kind: str
    x: float = 0.0
    size: float = 0.6
    gain: float = 1.0
    note: str = ''
    params: dict = field(default_factory=dict)

class Cues(list):
    def add(self, t, kind, x=0.0, size=0.6, gain=1.0, note='', **params):
        self.append(Cue(t, kind, x, size, gain, note, params)); return self
    def json(self):
        return [c.__dict__ for c in sorted(self, key=lambda c: c.t)]

class Grid:
    """A musical grid: put every hit on it. g = Grid(bpm=100, first_downbeat=drop_t - 3 * bar)."""
    def __init__(self, bpm, first_downbeat=0.0, beats_per_bar=4):
        self.bpm, self.t0, self.bpb = bpm, first_downbeat, beats_per_bar
        self.beat = 60.0 / bpm
        self.bar = self.beat * beats_per_bar
    def at(self, bar, beat=0.0): return self.t0 + bar * self.bar + beat * self.beat
    def snap(self, t, div=1):
        step = self.beat / div
        return self.t0 + round((t - self.t0) / step) * step
    def bar_of(self, t): return int((t - self.t0) // self.bar)

def seconds_to_frame(t, fps): return int(round(t * fps))
