from __future__ import annotations
#import math for the sine function to have smooth animations
import math
import pygame
#Type hint for (x,y) position
from typing import Tuple
#radius used for the inner goal ring
from .settings import (
    GOAL_RING_R,
    MINIMAP_W, MINIMAP_H, MINIMAP_MARGIN, MINIMAP_DOT_R,
    MINIMAP_BG_COLOR, MINIMAP_BORDER_COLOR,
    MINIMAP_PLAYER_COLOR, MINIMAP_COP_COLOR, MINIMAP_GOAL_COLOR,
)
from .utils import clamp

def draw_goal_glow(screen: pygame.Surface, pos: Tuple[int, int]) -> None:
    """
    Draws a pulsing glow around the goal circle using a circle(purely for fun visuals)
    The glow effect is created using a sine wave over time, which makes the outer radius pulse smoothly.
    The inner ring represents the actual visual goal marker.
    """
    x, y = pos
    #animating continuously
    t = pygame.time.get_ticks() / 1000.0

    #Create a smooth pulsing value using sine, math.sin gives values between -1 and 1
    #We shift it to stay between 0 and 1
    pulse = 0.5 + 0.5 * math.sin(t * 3.0)
    #Outer radius grows and shrinks based on pulse value
    outer_r = int(34 + pulse * 10)
    #Inner ring radius
    inner_r = GOAL_RING_R

    #Create a transparent surface for the glow effect, SRCALPHA allows per-pixel transparency
    glow_surf = pygame.Surface((outer_r * 2 + 2, outer_r * 2 + 2), pygame.SRCALPHA)
    #Center coordinates for drawing circles on the glow surface.
    cx, cy = outer_r + 1, outer_r + 1

    #Draw multiple semi-transparent circles to stimule glowing effect (green colour)
    for r, a in [(outer_r, 30), (outer_r - 6, 55), (outer_r - 12, 80)]:
        if r > 0:
            pygame.draw.circle(glow_surf, (0, 255, 120, a), (cx, cy), r)

    #Blit (draw) the glow surface onto the main screen
    screen.blit(glow_surf, (x - cx, y - cy))
    #Draw the visible goal ring on top
    pygame.draw.circle(screen, (0, 255, 0), (x, y), inner_r, 3)
    #Small center dot for visual detail
    pygame.draw.circle(screen, (200, 255, 220), (x, y), 3)

def draw_minimap(
    screen: pygame.Surface,
    virtual_w: int,
    world_h: int,
    player_y: float,
    cop_y: float,
    goal_y: float,
) -> None:
    """
    Draws a slim vertical progress bar in the top-right corner showing how
    high up the player and cop currently are, plus where the goal sits.
    This game is climbed vertically, so height IS the progress — the bar
    only tracks y, not x.
    """
    bar_x = virtual_w - MINIMAP_MARGIN - MINIMAP_W
    bar_y = MINIMAP_MARGIN
    bar_rect = pygame.Rect(bar_x, bar_y, MINIMAP_W, MINIMAP_H)

    #Semi-transparent backing so the bar stays readable over any part of the background
    backing = pygame.Surface((MINIMAP_W, MINIMAP_H), pygame.SRCALPHA)
    backing.fill(MINIMAP_BG_COLOR)
    screen.blit(backing, (bar_x, bar_y))
    pygame.draw.rect(screen, MINIMAP_BORDER_COLOR, bar_rect, 2)

    #Maps a world y-coordinate onto a y position along the bar (top = world top)
    def y_to_bar(world_y: float) -> int:
        frac = clamp(world_y / world_h, 0.0, 1.0)
        return bar_y + int(frac * MINIMAP_H)

    cx = bar_x + MINIMAP_W // 2

    #Goal marker drawn as a small diamond so it reads differently from the round dots
    gy = y_to_bar(goal_y)
    pygame.draw.polygon(
        screen, MINIMAP_GOAL_COLOR,
        [(cx - 8, gy), (cx, gy - 6), (cx + 8, gy), (cx, gy + 6)],
    )

    #Cop drawn before the player so the player's dot stays on top if they overlap
    cy = y_to_bar(cop_y)
    pygame.draw.circle(screen, MINIMAP_COP_COLOR, (cx, cy), MINIMAP_DOT_R)

    py = y_to_bar(player_y)
    pygame.draw.circle(screen, MINIMAP_PLAYER_COLOR, (cx, py), MINIMAP_DOT_R)
