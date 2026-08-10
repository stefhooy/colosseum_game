from __future__ import annotations
#import math for the sine function to have smooth animations
import math
import pygame
#Type hint for (x,y) position
from typing import Tuple
#radius used for the inner goal ring
from .settings import GOAL_RING_R

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
