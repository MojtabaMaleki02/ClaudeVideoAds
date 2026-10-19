"""adkit: Clipzing's ad toolkit. A Python 2.5D renderer (numpy / Pillow / OpenCV) with a real perspective camera,
Clipzing's brand and UI kit, light/particle/type effects, word-timed timelines, original music + SFX in code,
a measured mix, and QA. See ../../SKILL.md.

    import adkit as K                       # after FMT / SCALE / FPS are in the environment (render.py does it)
    from adkit.core import *                # camera, planes, compositing, draw_line, easings
"""
from . import core, brand, ui, fx, timeline  # noqa: F401
