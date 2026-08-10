"""
level.py

Fixed points only: the floor, the spawn, and the goal. Unlike the reference
game's hidden dev-only editor, platform-building here is core, live
gameplay — the level intentionally starts empty (just a floor) and the
player (and the cop, via its cheat-hop — see cop.py) build their own path
upward as they go. There is no fixed climb layout to author or validate
jump-reachability against, so this module stays deliberately small.
"""
from __future__ import annotations
from typing import List, Tuple
import pygame

from .platform import Platform
from .settings import GOAL_W, GOAL_H

#Floor height in pixels, matches the reference game's base floor platform
FLOOR_H = 40
#How far below the world's top edge the goal sits, regardless of how the
#player builds their way up to it
GOAL_TOP_MARGIN = 150


def build_platforms(world_w: int, world_h: int) -> List[Platform]:
    """
    The level starts with just a full-width floor at the bottom — every
    other platform is built live during play, not pre-authored here.
    """
    return [Platform(0, world_h - FLOOR_H, world_w, FLOOR_H)]


def get_spawn(world_w: int, world_h: int) -> Tuple[int, int]:
    """
    Spawn point sits on the floor, near the left edge.
    """
    return 80, world_h - 140


def get_goal_rect(world_w: int, world_h: int) -> pygame.Rect:
    """
    Goal sits near the top of the world, horizontally centered — a fixed
    target the player has to build their own way up to.
    """
    goal_x = world_w // 2 - GOAL_W // 2
    goal_y = GOAL_TOP_MARGIN
    return pygame.Rect(goal_x, goal_y, GOAL_W, GOAL_H)
