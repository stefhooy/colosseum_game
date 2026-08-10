"""
cop.py

The police officer chasing the player up the Colosseum. Structurally
mirrors Player (own rect, physics, two-pass move-and-collide, sprite set)
but is driven by an AI controller that follows a precomputed waypoint path
instead of keyboard input, tuned per difficulty (Easy/Medium/Hard).

New module — no reference-game equivalent. Built in Step 7.
"""
