"""
audio.py

Dual audio backend: native HTMLAudioElement on web (sys.platform ==
"emscripten") to avoid Chrome/SDL stuttering, pygame.mixer on desktop.

Placeholder for now — ported from the reference project (Tower of IE) with
theme-appropriate renames in Step 3.
"""
