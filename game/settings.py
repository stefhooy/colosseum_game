#We import os to build file paths
import os
import sys

# Base path:
# - normal Python run -> current project folder
# - PyInstaller bundle -> temporary/internal bundle folder
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#Screen resolution of the game window (width and height)
SCREEN_W, SCREEN_H = 1920, 1080
#Frames per second target, how fast we will update and draw the game.
FPS = 60

#Assets of the game (images, fonts and saved scores)
#folder where I stored every visual elements for the game
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BACKGROUND_FILE = "background.png" #main gameplay background (the Colosseum), also defines world size
FIRST_SCREEN_FILE = "first_screen.jpg" #splash/intro screen shown before the menu
MENU_BG_FILE = "menu_background.png" #image for the first page of the game (menu)
SCOREBOARD_BG_FILE = "scoreboard_background.png" #image for the scoreboard
#The player sprites (3 images, idle, running right, running left)
CHAR_STILL_FILE = "player_idle.png"
CHAR_RUN_RIGHT_FILE = "player_run_right.png"
CHAR_RUN_LEFT_FILE = "player_run_left.png"
#Custom arcade font
ARCADE_FONT_FILE = "arcade_font.ttf"
#Where the scoreboard is saved into a json file
SCORES_FILE = os.path.join(ASSETS_DIR, "scores.json")

#Player physics and visuals
#Size of the hitbox of the character (collision rectangle)
PLAYER_W, PLAYER_H = 32, 48
#Target height of the character by scaling the PNGs to this height
SPRITE_TARGET_H = 100
#Small offset so that the character's feet can line up nicely with the collision rectangle
FEET_OFFSET_Y = 10

#Default platform size when you start building platforms in editor mode (E)
DEFAULT_PLAT_W = 160
DEFAULT_PLAT_H = 16
#Size of the goal collision area. Even though the goal is drawn visually (photo/flash effect),
#the collision detection is handled using pygame.Rect
GOAL_W, GOAL_H = 40, 60
#Platform colors (stone style, placeholder until real Colosseum art lands)
PLATFORM_FILL = (140, 90, 45)
PLATFORM_OUTLINE = (0, 0, 0)
#Radius used to draw the glowing goal ring (for visual effect)
GOAL_RING_R = 14
#Window title is displayed at the top of the pygame window
WINDOW_TITLE = "COLOSSEUM CURFEW"

#Game states here in order to help us switch screens
#Going from menu -> name_input -> map_preview -> game -> scoreboard
STATE_SPLASH = "splash"
STATE_MENU = "menu"
STATE_NAME = "name"
STATE_MAP_PREVIEW = "map_preview"
STATE_SCOREBOARD = "scoreboard"
STATE_GAME = "game"
