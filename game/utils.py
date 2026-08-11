from __future__ import annotations
import os
import pygame
#Type hint for functions that may retrun None
from typing import Optional
#Import the assets
from .settings import ASSETS_DIR, ARCADE_FONT_FILE

#load images from disk and if it doesn't exist, the function will return none instead of crashing
def safe_load_image(path: str, convert_alpha: bool = True) -> Optional[pygame.Surface]:
    #file path doesn't exist, retunr None and prevent the game to crash
    if not os.path.exists(path):
        return None
    #load our images using pygaame
    img = pygame.image.load(path)
    #Convert the image format for better performance, convert_alpha() keeps transparency, convert() is      #faster but removes alpha.
    return img.convert_alpha() if convert_alpha else img.convert()

#Scales an image proportionally to a specific height, keeping an aspect ratio intact
def scale_to_target_height(img: pygame.Surface, target_h: int) -> pygame.Surface:
    #get the original size of our image
    w, h = img.get_size()
    #Avoid divisions by zero, return image to its original size
    if h == 0:
        return img
    #Compute our scaling factor
    scale = target_h / h
    #NEw width and height with the scaling factor
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    #Smooothscale gives us a better visual quality than just a basic scale
    return pygame.transform.smoothscale(img, (new_w, new_h))

#Restrict a value between a lower and upper bound, we will use it for other boundary control.
def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(v, hi))

#Convert the time value in seconds into this format MM:SS
#ExL 83.42 seconds will be 01:23:42
def format_time(t: float) -> str:
    minutes = int(t // 60)
    seconds = t - minutes * 60
    #f string formatiting with leading zeros and 2 decimal precision
    return f"{minutes:02d}:{seconds:05.2f}"

def get_font(size: int) -> pygame.font.Font:
    """
    Loads the stylized Star Crush TTF from assets, otherwise goes back to
    normal font. This is only for short, pure-word screen titles (e.g.
    "SCOREBOARD", "CURSUS COLOSSEI") — Star Crush is missing several ASCII
    glyphs (!,-._?), so it can't reliably render timers, hints, typed player
    names, or anything else with numbers/punctuation. Use get_readable_font
    for all of that instead.
    """
    #build the full path to our font file
    font_path = os.path.join(ASSETS_DIR, ARCADE_FONT_FILE)
    #if custom font exists, then use it
    if os.path.exists(font_path):
        return pygame.font.Font(font_path, size)
    #otherwise , default system font (prevent for the game to crash)
    return pygame.font.Font(None, size)

def get_readable_font(size: int) -> pygame.font.Font:
    """
    Pygame's built-in default font — full ASCII coverage, used for anything
    that needs to reliably render numbers/punctuation/arbitrary typed text:
    timers, HUD text, hints, score lines, and the win/caught titles (both
    contain "!", which Star Crush can't render at all).
    """
    return pygame.font.Font(None, size)

#Draws text centered horizontally on the screen at a given y position.
def draw_center_text(screen: pygame.Surface, font: pygame.font.Font, text: str, y: int, color=(0, 0, 0)) -> None:
    #renter text into a surface on top of the image/background
    surf = font.render(text, True, color)
    #horizontal center position
    x = (screen.get_width() - surf.get_width()) // 2
    #draw the text surfacte onto the screen
    screen.blit(surf, (x, y))
