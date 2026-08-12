from __future__ import annotations
import pygame
#Used to convert world coordinates to screen coordinates
from .camera import Camera
#Colors defined globally in settings
from .settings import PLATFORM_FILL, PLATFORM_OUTLINE, COP_PLATFORM_FILL, COP_PLATFORM_OUTLINE

#this class will represent a static surface that the player can stand on
class Platform:
    """
    Each platform owns a pygame.Rect which is used both for:
    - Collision detection
    - Positioning in the world
    """
    def __init__(self, x: int, y: int, w: int, h: int = 12, built_by: str = "player"):
        #The platform is defined by a rectangle in world coordinates.
        #Default height is 12 if not specified.
        self.rect = pygame.Rect(x, y, w, h)
        #Who placed this platform — "player" (default, includes the floor)
        #or "cop" (the cop's own stepping stones, see cop.py). Purely
        #cosmetic: only affects which colors draw() uses below, so the cop
        #can build platforms that visually read as its own construction.
        self.built_by = built_by

    #Draws the platform on screen using camera transformation
    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        """
        The platform exists in world space,
        so we use camera.apply() to convert it into screen space.
        """
        #Convert world position -> screen position
        x, y = camera.apply(self.rect.x, self.rect.y)
        #Border radius makes the platform slightly rounded instead of sharp corners
        radius = max(2, self.rect.h // 2)
        fill_color = COP_PLATFORM_FILL if self.built_by == "cop" else PLATFORM_FILL
        outline_color = COP_PLATFORM_OUTLINE if self.built_by == "cop" else PLATFORM_OUTLINE
        #This will draw the inside filled rectangle (mainly body of the platform)
        pygame.draw.rect(
            screen,
            fill_color,
            pygame.Rect(x, y, self.rect.w, self.rect.h),
            border_radius=radius,
        )
        #This will draw the outline of the platform
        pygame.draw.rect(
            screen,
            outline_color,
            pygame.Rect(x, y, self.rect.w, self.rect.h),
            2,
            border_radius=radius,
        )
