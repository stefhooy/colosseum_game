from typing import Tuple
#This is used to restrict camera movement within world bounds
from .utils import clamp

class Camera:
    """
    The Camera class handles the transformation between world coordinates and screen coordinates.
    Instead of moving the player around the screen directly,we move the camera offsets and render objects relative to it.
    This allows the world to be larger than the visible window.
    """
    def __init__(self, screen_w: int, screen_h: int, world_w: int, world_h: int):
        #screen size (window)
        self.screen_w = screen_w
        self.screen_h = screen_h
        #world size (can be larger then the screen)
        self.world_w = world_w
        self.world_h = world_h
        #camera offsets (how much the world is shifted when drawn)
        self.offset_x = 0.0
        self.offset_y = 0.0

    def follow(self, target_x: float, target_y: float) -> None:
        """
        Makes the camera follow a target position (usually the player).
        The camera tries to center the target on screen,but it is clamped so it never scrolls outside the world boundaries.
        """
        #Desired camera position = center the target
        desired_x = target_x - self.screen_w / 2
        desired_y = target_y - self.screen_h / 2
        #Clamp ensures the camera never moves beyond world limits
        self.offset_x = clamp(desired_x, 0, self.world_w - self.screen_w)
        self.offset_y = clamp(desired_y, 0, self.world_h - self.screen_h)

    #Converts world coordinates into screen coordinates
    #Every object in the world is drawn using this transformation.
    def apply(self, world_x: float, world_y: float) -> Tuple[int, int]:
        return int(world_x - self.offset_x), int(world_y - self.offset_y)
