#!/bin/bash
# finals: per format → render all frames → repair → motion audit → encode → upload copy → delete frames (disk)
cd "$(dirname "$0")"
PY=~/shorten/shortn-be/.venv/bin/python; R=~/shorten/.claude/skills/clipzing-ads/toolkit/render.py
set -o pipefail
for F in 9x16 16x9; do
  $PY $R film.py check --fmt $F 2>&1 | grep -v objc || { echo "STOP: $F pre-flight check failed"; exit 1; }
  $PY $R film.py repair out/frames_$F --fmt $F -j 5 2>&1 | grep -v objc | tail -1      # renders only what is missing
  $PY $R film.py repair out/frames_$F --fmt $F -j 3 2>&1 | grep -v objc | tail -1
  n=$(ls out/frames_$F | wc -l | tr -d ' '); if [ "$n" != "1260" ]; then echo "STOP: $F has $n/1260 frames"; exit 1; fi
  $PY -c "
import sys,json; sys.path.insert(0,'$HOME/shorten/.claude/skills/clipzing-ads/toolkit')
from adkit import qa
r=qa.motion_audit('out/frames_$F',60,expect=1260,out_json='qa/motion_$F.json'); print('$F audit', json.dumps({k:r[k] for k in ('frames','black_runs','hard_cuts','one_frame_pops','static_stretches','fastest_frames_check_by_eye','pass')}))
for i in r['fastest_frames_check_by_eye'][:3]: qa.strip('out/frames_$F', i, f'qa/strip_{\"$F\"}_{i}.jpg', n=5, w=300)
" 2>&1 | grep -v objc
  $PY $R encode out/frames_$F got-you-v2-$F.mp4 --audio audio/final_audio.wav 2>&1 | grep -v objc
  rm -rf out/frames_$F
done
[ -f got-you-v2-9x16.mp4 ] && ffmpeg -hide_banner -loglevel error -y -i got-you-v2-9x16.mp4 -c:v libx264 -preset slow -crf 20 -maxrate 25M -bufsize 50M -pix_fmt yuv420p -c:a copy -movflags +faststart got-you-v2-9x16-upload.mp4
ffmpeg -hide_banner -loglevel error -y -ss 0.9 -i got-you-v2-9x16.mp4 -frames:v 1 -q:v 2 cover-9x16.jpg
echo FINALS DONE
