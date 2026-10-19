#!/usr/bin/env python3
"""Render a film. Run with the BE venv (numpy, Pillow, OpenCV, scipy) or any Python that has them.

  render.py FILM.py stills OUT  1.0 2.5 7.9     [--fmt 9x16] [--scale 0.5]   PNG stills + a contact sheet
  render.py FILM.py preview OUT.mp4             [--fmt 9x16]                 half size, 30 fps, with audio if present
  render.py FILM.py all FRAMES_DIR -j 8         [--fmt 9x16] [--fps 60]      every frame, in parallel workers
  render.py FILM.py frames FRAMES_DIR --from 0 --to 120 [--every N --offset k]   (what a worker runs)
  render.py FILM.py repair FRAMES_DIR -j 8      [--fmt …]                    re-render only missing / corrupt frames
  render.py encode FRAMES_DIR OUT.mp4 [--audio mix.wav] [--fps 60] [--upload]
  render.py sheet VIDEO OUT.jpg

The format, scale and fps are passed to the film through the environment (FMT, SCALE, FPS), so every worker agrees.
"""
import argparse
import importlib.util
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

def load_film(path):
    sys.path.insert(0, HERE)
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
    spec = importlib.util.spec_from_file_location('film', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('film'); ap.add_argument('mode', nargs='?', default='')
    ap.add_argument('out', nargs='?', default='')
    ap.add_argument('times', nargs='*')
    ap.add_argument('--fmt', default=os.environ.get('FMT', '9x16'))
    ap.add_argument('--scale', type=float, default=None)
    ap.add_argument('--fps', type=int, default=int(os.environ.get('FPS', '60')))
    ap.add_argument('-j', '--jobs', type=int, default=max(1, (os.cpu_count() or 2) - 0))
    ap.add_argument('--from', dest='a', type=int, default=0); ap.add_argument('--to', dest='b', type=int, default=None)
    ap.add_argument('--every', type=int, default=1); ap.add_argument('--offset', type=int, default=0)
    ap.add_argument('--audio', default=None); ap.add_argument('--upload', action='store_true')
    ap.add_argument('--only', default='', help='comma-separated frame numbers (frames mode)')
    args = ap.parse_args()

    if args.film == 'encode':
        sys.path.insert(0, HERE)
        os.environ['FPS'] = str(args.fps)
        from adkit import render as R
        R.encode(args.mode, args.out, audio=args.audio, fps=args.fps, upload=args.upload); print('encoded', args.out); return
    if args.film == 'sheet':
        sys.path.insert(0, HERE)
        from adkit import render as R
        R.contact_sheet(args.mode, args.out); print('sheet', args.out); return

    scale = args.scale if args.scale is not None else (0.5 if args.mode in ('stills', 'preview') else 1.0)
    fps = 30 if args.mode == 'preview' else args.fps
    os.environ.update(FMT=args.fmt, SCALE=str(scale), FPS=str(fps))

    if args.mode in ('all', 'repair'):
        os.makedirs(args.out, exist_ok=True)
        film = load_film(args.film)
        n = int(round(film.END * fps))
        import shutil
        free = shutil.disk_usage(args.out).free
        need = n * int(1080 * 1920 * scale * scale * 2.2) if args.mode == 'all' else 0   # ≈ PNG size at compress_level 1
        if need and free < need * 1.3:
            sys.exit(f'Not enough disk: {free / 1e9:.1f} GB free, about {need / 1e9:.1f} GB needed for {n} frames. Free space first '
                     f'(old frames folders can go once encoded).')
        if args.mode == 'repair':
            from PIL import Image
            todo = []
            for i in range(n):
                p = os.path.join(args.out, f'{i:05d}.png')
                try:
                    with Image.open(p) as im: im.load()
                except Exception:
                    todo.append(i)
            print(f'repair: {len(todo)} frames to render')
            if not todo: return
            chunks = [todo[k::args.jobs] for k in range(args.jobs)]
            procs = [subprocess.Popen([sys.executable, os.path.abspath(__file__), args.film, 'frames', args.out, '--fmt', args.fmt, '--scale', str(scale),
                                       '--fps', str(fps), '--only', ','.join(map(str, c))], env=dict(os.environ, OMP_NUM_THREADS='1')) for c in chunks if c]
            bad = [p for p in procs if p.wait() != 0]
            sys.exit(1 if bad else 0)
        t0 = time.time()
        procs = []
        for k in range(args.jobs):
            env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
            procs.append(subprocess.Popen([sys.executable, os.path.abspath(__file__), args.film, 'frames', args.out, '--fmt', args.fmt,
                                           '--scale', str(scale), '--fps', str(fps), '--from', '0', '--to', str(n),
                                           '--every', str(args.jobs), '--offset', str(k)], env=env))
        bad = [p for p in procs if p.wait() != 0]
        have = len([f for f in os.listdir(args.out) if f.endswith('.png')])
        print(f'{args.fmt}: {have}/{n} frames in {time.time() - t0:.0f} s' + (f' — {len(bad)} worker(s) FAILED' if bad else ''))
        sys.exit(1 if bad or have < n else 0)

    film = load_film(args.film)
    from adkit import render as R
    if args.mode == 'stills':
        os.makedirs(args.out, exist_ok=True)
        paths = []
        for s in args.times:
            t = float(s)
            p = os.path.join(args.out, f'{args.fmt}_{t:06.2f}.png')
            R.save(R.render_frame(film, t), p); paths.append(p)
            print('still', t, flush=True)
        R.stills_sheet(paths, os.path.join(args.out, f'sheet_{args.fmt}.jpg'), cols=4 if args.fmt != '9x16' else 6, width=480 if args.fmt != '9x16' else 270)
    elif args.mode == 'frames':
        os.makedirs(args.out, exist_ok=True)
        b = args.b if args.b is not None else int(round(film.END * fps))
        only = [int(x) for x in args.only.split(',') if x] if args.only else None
        for i in (only if only is not None else range(args.a, b)):
            if only is None and (i - args.a) % args.every != args.offset: continue
            p = os.path.join(args.out, f'{i:05d}.png')
            R.save(R.render_frame(film, i / fps), p)
    elif args.mode == 'preview':
        import tempfile
        d = tempfile.mkdtemp(prefix='adkit_prev_')
        n = int(round(film.END * fps))
        jobs = max(1, args.jobs)
        procs = [subprocess.Popen([sys.executable, os.path.abspath(__file__), args.film, 'frames', d, '--fmt', args.fmt, '--scale', str(scale),
                                   '--fps', str(fps), '--from', '0', '--to', str(n), '--every', str(jobs), '--offset', str(k)],
                                  env=dict(os.environ, OMP_NUM_THREADS='1')) for k in range(jobs)]
        for p in procs: p.wait()
        audio = args.audio or next((c for c in ('audio/final_audio.wav', 'final_audio.wav') if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(args.film)), c))), None)
        if audio and not os.path.isabs(audio): audio = os.path.join(os.path.dirname(os.path.abspath(args.film)), audio)
        R.encode(d, args.out, audio=audio, fps=fps, crf=20, preset='veryfast')
        print('preview', args.out)
    else:
        ap.error('mode must be stills | preview | all | frames | repair')

if __name__ == '__main__':
    main()
