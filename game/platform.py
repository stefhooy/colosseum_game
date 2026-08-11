from __future__ import annotations
import pygame
#Used to convert world coordinates to screen coordinates
from .camera import Camera
#Colors defined globally in settings
from .settings import PLATFORM_FILL, PLATFORM_OUTLINE

#this class will represent a static surface that the player can stand on
class Platform:
    """
    Each platform owns a pygame.Rect which is used both for:
    - Collision detection
    - Positioning in the world
    """
    def __init__(self, x: int, y: int, w: int, h: int = 12):
        #The platform is defined by a rectangle in world coordinates.
        #Default height is 12 if not specified.
        self.rect = pygame.Rect(x, y, w, h)

    #Draws the platform on screen using camera transformation
    def draw(self, screen: pygame.Surface, camera: Camera, fill_color=None, outline_color=None) -> None:
        """
        The platform exists in world space,
        so we use camera.apply() to convert it into screen space.
        fill_color/outline_color let a caller override the default stone
        look — used to tint the cop's own cheat-hop landing pads a
        different color so they read as "the cop built this", not the
        player's own platforms.
        """
        #Convert world position -> screen position
        x, y = camera.apply(self.rect.x, self.rect.y)
        #Border radius makes the platform slightly rounded instead of sharp corners
        radius = max(2, self.rect.h // 2)
        #This will draw the inside filled rectangle (mainly body of the platform)
        pygame.draw.rect(
            screen,
            fill_color or PLATFORM_FILL,
            pygame.Rect(x, y, self.rect.w, self.rect.h),
            border_radius=radius,
        )
        #This will draw the outline of the platform
        pygame.draw.rect(
            screen,
            outline_color or PLATFORM_OUTLINE,
            pygame.Rect(x, y, self.rect.w, self.rect.h),
            2,
            border_radius=radius,
        )
