#!/bin/bash
# splice re-rendered frames A..B into an encoded master: decode → replace → re-encode (CRF 15 → CRF 15)
set -e; cd "$(dirname "$0")"
PY=~/shorten/shortn-be/.venv/bin/python; R=~/shorten/.claude/skills/clipzing-ads/toolkit/render.py
A=$1; B=$2
for F in 9x16 16x9; do
  rm -rf out/dec_$F && mkdir -p out/dec_$F
  ffmpeg -hide_banner -loglevel error -i got-you-$F.mp4 -start_number 0 out/dec_$F/%05d.png
  n=$(ls out/dec_$F | wc -l | tr -d ' '); [ "$n" = "2280" ] || { echo "STOP: decoded $n frames"; exit 1; }
  for k in 0 1 2 3 4; do OMP_NUM_THREADS=1 $PY $R film.py frames out/dec_$F --fmt $F --from $A --to $B --every 5 --offset $k > /dev/null 2>&1 & done; wait
  $PY -c "
import sys,json; sys.path.insert(0,'$HOME/shorten/.claude/skills/clipzing-ads/toolkit')
from adkit import qa
r=qa.motion_audit('out/dec_$F',60,expect=2280); print('$F', json.dumps({k:r[k] for k in ('frames','black_runs','hard_cuts','one_frame_pops','pass')}))" 2>&1 | grep -v objc
  $PY $R encode out/dec_$F got-you-$F.new.mp4 --audio audio/final_audio.wav 2>&1 | grep -v objc
  mv got-you-$F.new.mp4 got-you-$F.mp4; rm -rf out/dec_$F
done
ffmpeg -hide_banner -loglevel error -y -i got-you-9x16.mp4 -c:v libx264 -preset slow -crf 20 -maxrate 25M -bufsize 50M -pix_fmt yuv420p -c:a copy -movflags +faststart got-you-9x16-upload.mp4
echo SPLICE DONE
