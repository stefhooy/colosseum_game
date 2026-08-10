"""
level.py

Fixed, hand-authored Colosseum level layout: an ordered, ascending set of
platforms (standing in for the Colosseum's tiers/arches) that the player
climbs to reach the goal at the top.

Unlike the reference game (which starts with just a floor and lets the
player build the whole level live through editor mode), this game needs a
known, stable layout — the Cop AI needs a fixed structure to path over, and
the map-preview/minimap screens need fixed points to display. Editor mode
(E, in-game) is kept around as a dev tool for eyeballing/tuning positions
once real art exists; whatever looks right in editor mode gets hand-copied
back into the constants below.

Positions are stored relative to world_w/world_h (offsets from the floor,
offsets from the horizontal center) instead of raw pixel coordinates, so
the layout still lines up correctly if the final background image ends up
a different size than the placeholder. The step sizes are physics-tuned —
and importantly, tuned against the *slowest* entity that has to make these
jumps, which is the Easy-difficulty Cop at 180px/s, not the player at
260px/s (see cop.py). Whatever the slowest mover can clear, everyone faster
can clear too:

  - Max jump apex height is v^2/(2g) ~= 151px, so STEP_UP must stay well
    under that.
  - For a jump that rises STEP_UP pixels, you only start falling (and can
    land) after already going above STEP_UP and coming back down to it —
    that "time back at height STEP_UP" bounds how long there is to also
    move sideways. At STEP_UP=70 that's ~0.80s of hang time, i.e. ~145px of
    horizontal budget at the Easy cop's 180px/s. Consecutive platforms are
    LANE_HALF_WIDTH*2 = 110px apart horizontally — a comfortable ~24%
    margin under that budget.
"""
from __future__ import annotations
from typing import List, Tuple
import pygame

from .platform import Platform
from .settings import GOAL_W, GOAL_H

#Floor height in pixels, matches the reference game's base floor platform
FLOOR_H = 40

#--- Physics-tuned climb parameters (see module docstring for the math) ---
STEP_UP = 70             #vertical rise between consecutive platforms (px)
LANE_HALF_WIDTH = 55     #each platform sits this far left/right of world center (px)
TIER_COUNT = 15          #how many platforms make up the climb
TIER_W, TIER_H = 200, 20  #size of each climbing platform (Colosseum tier/arch)
GOAL_GAP = 140           #extra gap above the topmost platform before the goal (px)
TOP_MARGIN = 150         #breathing room above the goal, for camera framing (px)

#Minimum world height needed for the whole climb + goal + top margin to fit.
#If background.png ends up shorter than this, the level still builds (fails
#soft, same philosophy as the rest of the codebase) but may look cramped.
MIN_WORLD_H = FLOOR_H + TIER_COUNT * STEP_UP + GOAL_GAP + TOP_MARGIN


def build_platforms(world_w: int, world_h: int) -> List[Platform]:
    """
    Builds the fixed list of Platform objects for the current world size.
    Always starts with a full-width floor at the bottom (so the player has
    solid ground to spawn on), then adds TIER_COUNT platforms zigzagging
    up and alternating left/right of the world's horizontal center.
    """
    if world_h < MIN_WORLD_H:
        print(
            f"[level] warning: world_h ({world_h}) is shorter than the "
            f"recommended minimum ({MIN_WORLD_H}) for this layout to fit "
            f"comfortably - the climb may look cramped or clipped."
        )

    floor_top = world_h - FLOOR_H
    center_x = world_w // 2

    platforms: List[Platform] = [Platform(0, floor_top, world_w, FLOOR_H)]

    for i in range(1, TIER_COUNT + 1):
        #alternate left/right of center, starting on the left
        dx = -LANE_HALF_WIDTH if i % 2 == 1 else LANE_HALF_WIDTH
        x = center_x + dx - TIER_W // 2
        y = floor_top - i * STEP_UP
        platforms.append(Platform(x, y, TIER_W, TIER_H))

    return platforms


def get_spawn(world_w: int, world_h: int) -> Tuple[int, int]:
    """
    Spawn point sits on the floor, near the left edge.
    """
    return 80, world_h - 140


def get_goal_rect(world_w: int, world_h: int) -> pygame.Rect:
    """
    Goal sits GOAL_GAP pixels above the topmost climbing platform, roughly
    centered over it — one final jump away from the last tier.
    """
    floor_top = world_h - FLOOR_H
    center_x = world_w // 2
    top_dx = -LANE_HALF_WIDTH if TIER_COUNT % 2 == 1 else LANE_HALF_WIDTH
    top_rise = TIER_COUNT * STEP_UP

    goal_x = center_x + top_dx - GOAL_W // 2
    goal_y = floor_top - top_rise - GOAL_GAP - GOAL_H
    return pygame.Rect(goal_x, goal_y, GOAL_W, GOAL_H)


def get_climb_waypoints(world_w: int, world_h: int) -> List[Tuple[int, int]]:
    """
    Ordered bottom-to-top list of (x, y) points up the fixed level: the
    floor, then the landing spot of every climbing platform, then the goal.
    The Cop AI (cop.py) follows this path upward when it isn't close enough
    to the player to chase them directly.

    The first waypoint uses the floor platform's actual top surface (not
    get_spawn()'s y) — spawn is deliberately a little above the floor so the
    player visibly drops in, but a waypoint has to match where an entity
    actually comes to rest, or the "have I reached this waypoint" check
    could never become true.
    """
    platforms = build_platforms(world_w, world_h)
    goal = get_goal_rect(world_w, world_h)
    spawn_x, _ = get_spawn(world_w, world_h)
    floor = platforms[0]

    waypoints: List[Tuple[int, int]] = [(spawn_x, floor.rect.top)]
    for p in platforms[1:]:  #skip the floor, it's already waypoint 0
        waypoints.append((p.rect.centerx, p.rect.top))
    waypoints.append((goal.centerx, goal.top))
    return waypoints
