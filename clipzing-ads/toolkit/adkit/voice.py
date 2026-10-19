"""adkit.voice: the voice-over comes FIRST; the picture is timed to its words.

  takes = tts(script, 'voice/', voices=['coral', 'shimmer', 'nova'], takes=2, direction=...)   # audition
  words = timings('voice/coral_1.wav', 'voice/words.json', script)                            # lock

Providers, in order of preference:
  ElevenLabs   env ELEVENLABS_API_KEY (+ ELEVENLABS_VOICE_ID). The best quality; ESTIMATE CREDITS FIRST and ask.
  OpenAI       env OPENAI_API_KEY (gpt-4o-mini-tts, steerable with `instructions`). Good, cheap (~$0.015/min).
Keys are read from the environment or from the repo's .env files; they are never printed or written anywhere.
Write the script in full, clear sentences; numbers as words ("three point five"); respell names that TTS gets wrong
("Clip-zing") in the TTS input only, never on screen.
"""
import json
import os
import re
import subprocess
import urllib.request

import numpy as np

SPOKEN = {'Clipzing': 'Clip-zing'}   # respellings for the TTS input only

def _key(name, env_files=('~/shorten/shortn-be/.env', '~/shorten/.env', '.env')):
    if os.environ.get(name): return os.environ[name]
    for f in env_files:
        p = os.path.expanduser(f)
        if os.path.exists(p):
            for line in open(p):
                m = re.match(rf'\s*{name}\s*=\s*"?([^"\n]+)"?', line)
                if m: return m.group(1).strip()
    return None

def respell(script):
    for k, v in SPOKEN.items(): script = re.sub(rf'\b{k}\b', v, script)
    return script

def openai_tts(text, out_wav, voice='coral', instructions='', model='gpt-4o-mini-tts'):
    key = _key('OPENAI_API_KEY')
    if not key: raise RuntimeError('No OPENAI_API_KEY (env or .env). Ask the owner, or use ElevenLabs.')
    body = json.dumps({'model': model, 'voice': voice, 'input': text, 'instructions': instructions, 'response_format': 'wav'}).encode()
    req = urllib.request.Request('https://api.openai.com/v1/audio/speech', data=body,
                                 headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    import time
    for attempt in range(4):                 # the stream sometimes stalls: retry with backoff
        try:
            with urllib.request.urlopen(req, timeout=180) as r, open(out_wav + '.raw.wav', 'wb') as f: f.write(r.read())
            break
        except (TimeoutError, OSError) as e:
            if attempt == 3: raise
            time.sleep(5 * (attempt + 1))
    _rewrap(out_wav + '.raw.wav', out_wav)
    return out_wav

def _rewrap(src, dst):
    """Streamed WAVs carry a bogus length header (0xFFFFFFFF): rewrite through ffmpeg as clean 48 kHz mono."""
    subprocess.check_call(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', src, '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s16le', dst])
    os.remove(src)

def elevenlabs_tts(text, out_wav, voice_id=None, stability=0.4, similarity=0.8, style=0.35, model='eleven_multilingual_v2'):
    key = _key('ELEVENLABS_API_KEY'); voice_id = voice_id or _key('ELEVENLABS_VOICE_ID')
    if not key or not voice_id: raise RuntimeError('No ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID. Ask the owner (see reference/needs.md).')
    body = json.dumps({'text': text, 'model_id': model, 'voice_settings': {'stability': stability, 'similarity_boost': similarity, 'style': style}}).encode()
    req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=pcm_44100', data=body,
                                 headers={'xi-api-key': key, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r: pcm = r.read()
    raw = out_wav + '.pcm'; open(raw, 'wb').write(pcm)
    subprocess.check_call(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 's16le', '-ar', '44100', '-ac', '1', '-i', raw, out_wav]); os.remove(raw)
    return out_wav

def estimate_cost(script, provider='openai'):
    """Rough cost so you can ask before spending. ElevenLabs bills ~1 credit per character."""
    n = len(script)
    return {'characters': n, 'openai_usd': round(n / 1000 * 0.015 * 1.2, 3), 'elevenlabs_credits': n}

def tts(script, outdir, voices=('coral', 'shimmer', 'nova'), takes=2, direction='', provider=None):
    """Audition: every voice × takes. Returns the list of wav paths (name_take.wav)."""
    os.makedirs(outdir, exist_ok=True)
    provider = provider or ('elevenlabs' if _key('ELEVENLABS_API_KEY') and _key('ELEVENLABS_VOICE_ID') else 'openai')
    text = respell(script)
    out = []
    for v in voices if provider == 'openai' else [None]:
        for k in range(1, takes + 1):
            p = os.path.join(outdir, f'{v or "eleven"}_{k}.wav')
            if os.path.exists(p): out.append(p); continue
            (openai_tts(text, p, v, direction) if provider == 'openai' else elevenlabs_tts(text, p))
            out.append(p)
    json.dump({'provider': provider, 'script': script, 'tts_input': text, 'direction': direction}, open(os.path.join(outdir, 'request.json'), 'w'), indent=1)
    return out

def duration(path):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path]).decode())

def timings(wav, out_json, script=None, model='base'):
    """Word timings for a take: faster-whisper word stamps, words after a pause snapped to the speech-band onset,
    repeated hallucinated words on trailing silence dropped, spelling restored from the script when it aligns."""
    from faster_whisper import WhisperModel
    import scipy.io.wavfile as wf
    m = WhisperModel(model, device='cpu', compute_type='int8', cpu_threads=4)
    segs, _ = m.transcribe(wav, language='en', word_timestamps=True, vad_filter=False)
    words = [{'w': w.word.strip(), 'start': float(w.start), 'end': float(w.end)} for s in segs for w in s.words]
    # drop hallucinated repeats past the end of speech
    tmp = wav + '.16k.wav'
    subprocess.check_call(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', wav, '-ac', '1', '-ar', '16000', tmp])
    sr, x = wf.read(tmp); os.remove(tmp)
    x = x.astype(np.float32) / (32768 if x.dtype == np.int16 else 1)
    from scipy.signal import butter, sosfilt
    band = sosfilt(butter(4, [300, 3400], 'band', fs=sr, output='sos'), x)
    hop = int(0.005 * sr)
    env = np.sqrt(np.convolve(band ** 2, np.ones(hop * 4) / (hop * 4), 'same'))[::hop]
    thr = max(1e-4, np.percentile(env, 95) * 0.08)
    voiced = env > thr
    last = np.nonzero(voiced)[0]
    speech_end = (last[-1] * hop / sr + 0.1) if len(last) else 1e9
    words = [w for w in words if w['start'] < speech_end]
    # snap to real onsets in the speech band. Only the first word and words after a pause (Whisper's starts drift
    # there), each once, to the FIRST onset after ≥ 120 ms of silence inside its window. Never mid-word syllables.
    onsets = [i * hop / sr for i in range(1, len(voiced)) if voiced[i] and not voiced[max(0, i - 24):i].any()]
    if len(voiced) and voiced[0]: onsets.insert(0, 0.0)
    for i, w in enumerate(words):
        if i == 0: lo, hi = 0.0, w['end'] - 0.05
        elif w['start'] - words[i - 1]['end'] > 0.08: lo, hi = w['start'] - 0.25, w['start'] + 0.35
        else: continue
        cand = [o for o in onsets if lo <= o <= min(hi, w['end'] - 0.03) and (i == 0 or o > words[i - 1]['start'] + 0.05)]
        if cand:
            w['start'] = round(cand[0], 3)
            if i > 0 and words[i - 1]['end'] > w['start']: words[i - 1]['end'] = round(w['start'] - 0.01, 3)
    # Whisper splits brand words ("Clip" + "-sing."): merge fragments that start with a hyphen or apostrophe
    merged = []
    for w in words:
        if merged and re.match(r"^[-'’]", w['w']):
            merged[-1]['w'] += w['w'].lstrip('-'); merged[-1]['end'] = w['end']
        else:
            merged.append(w)
    words = merged
    if script:   # restore the script's spelling (brand names, digits Whisper wrote as numerals) by aligning the two
        import difflib
        sw = re.findall(r"[\w'’-]+[.,!?…]*", script)
        key = lambda x: re.sub(r"[^a-z0-9]", '', x.lower())
        ops = difflib.SequenceMatcher(None, [key(w['w']) for w in words], [key(x) for x in sw], autojunk=False).get_opcodes()
        out = []
        for op, i1, i2, j1, j2 in ops:
            if op == 'equal' or (op == 'replace' and i2 - i1 == j2 - j1):
                for w, x in zip(words[i1:i2], sw[j1:j2]): w['w'] = x; out.append(w)
            elif op == 'replace' and i2 - i1 == 1:            # one heard token = several script words ("200" → "two hundred")
                w = words[i1]; n = j2 - j1; dur = (w['end'] - w['start']) / n
                for k, x in enumerate(sw[j1:j2]):
                    out.append({'w': x, 'start': round(w['start'] + k * dur, 3), 'end': round(w['start'] + (k + 1) * dur, 3)})
            else:
                out.extend(words[i1:i2])
        words = out
    json.dump(words, open(out_json, 'w'), indent=1)
    return words

def tighten(wav, out, gap=0.09, sentence_gap=0.16, tempo=1.1, script=None):
    """Social pacing, done in the edit: every pause is cut to `gap` (`sentence_gap` after . ? !), then a pitch-preserving
    tempo boost. TTS ignores 'speak faster'; this doesn't. Returns the new duration."""
    import scipy.io.wavfile as wf
    tmp = out + '.48k.wav'
    subprocess.check_call(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', wav, '-ac', '1', '-ar', '48000', tmp])
    sr, x = wf.read(tmp); os.remove(tmp)
    x = x.astype(np.float32) / (32768 if x.dtype == np.int16 else 1)
    hop = int(0.005 * sr)
    from scipy.signal import butter, sosfilt
    band = sosfilt(butter(4, [150, 9000], 'band', fs=sr, output='sos'), x)   # up to 9 kHz: an 's' is speech, not silence
    env = np.sqrt(np.convolve(band ** 2, np.ones(hop * 4) / (hop * 4), 'same'))[::hop]
    thr = max(1e-4, np.percentile(env, 95) * 0.04)
    voiced = env > thr
    # silent runs longer than the target gap get shortened (keep 30 ms fades either side)
    pieces, i, n = [], 0, len(voiced)
    runs = []
    while i < n:
        if not voiced[i]:
            j = i
            while j < n and not voiced[j]: j += 1
            runs.append((i, j)); i = j
        else:
            i += 1
    # which pauses end a sentence: approximate from the script's punctuation order
    marks = re.findall(r'[.?!]|[,;:]', script or '')
    keep = np.ones(len(x), bool)
    k = 0
    for a, b in runs:
        dur = (b - a) * hop / sr
        if a == 0 or b >= n:                       # trim leading / trailing silence to 50 ms
            s0, s1 = a * hop, b * hop
            if a == 0: keep[: max(0, s1 - int(0.05 * sr))] = False
            else: keep[s0 + int(0.05 * sr):] = False
            continue
        if dur < 0.06: continue
        mark = marks[k] if k < len(marks) else ','
        k += 1
        target = sentence_gap if mark in '.?!' else gap
        if dur > target:
            c = (a * hop + b * hop) // 2; half = int(target * sr / 2)
            keep[a * hop + half: c] = False; keep[c: b * hop - half] = False
    y = x[keep]
    tmp2 = out + '.cut.wav'
    wf.write(tmp2, sr, (y * 32767).astype(np.int16))
    subprocess.check_call(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', tmp2, '-af', f'atempo={tempo}', '-ar', '48000', '-ac', '1', out])
    os.remove(tmp2)
    return duration(out)
