"""
screens.py

Each screen (splash, menu, name_input, scoreboard, and later map preview
and difficulty select) is an async function that owns its own while-loop,
event handling, draw, and await asyncio.sleep(0) per frame — required for
Pygbag to yield control back to the browser event loop.

Placeholder for now — base screens ported from the reference project
(Tower of IE) in Step 3, map preview added in Step 5, difficulty select in
Step 6, per-difficulty scoreboard view in Step 12.
"""
