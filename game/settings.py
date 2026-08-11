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
#Hard cap on dt (seconds) used for one physics step. Without this, a real
#frame hitch (asset loading, window drag, OS stall) produces one huge dt,
#which can move a fast-falling entity so far in a single step that it
#tunnels past a platform's collision check entirely — and if it then ends
#up vertically overlapping a wide platform like the floor, the horizontal
#collision pass misreads that platform as a side wall and teleports the
#entity to the world's edge. Capping dt keeps every step small and safe.
MAX_DT = 0.05

#Zoom-out factor for the gameplay camera (Step 9). Gameplay is rendered onto
#an off-screen "virtual" surface of size (SCREEN_W*CAMERA_ZOOM, SCREEN_H*CAMERA_ZOOM),
#then smoothscaled to fill the real window. CAMERA_ZOOM > 1.0 shows more of the
#world at once (zoomed out, "grandiose" framing); 1.0 means no zoom at all.
#Left at 1.0 for now because background.png is exactly screen-sized (no room
#to scroll yet) — zooming out would just reveal empty space past its edges.
#Bump this once a taller background lands; the render pipeline is ready for it.
CAMERA_ZOOM = 1.0

#Assets of the game (images, fonts and saved scores)
#folder where I stored every visual elements for the game
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
BACKGROUND_FILE = "background.png" #main gameplay background (the Colosseum), also defines world size
FIRST_SCREEN_FILE = "first_screen.png" #splash/intro screen shown before the menu
MENU_BG_FILE = "menu_background.png" #image for the first page of the game (menu)
SCOREBOARD_BG_FILE = "scoreboard_background.png" #image for the scoreboard
FINAL_BG_FILE = "final_background.png" #image for the dedicated "photo captured" win screen
#The player sprites (4 images: idle, running right, running left, jumping/airborne)
CHAR_STILL_FILE = "player_idle.png"
CHAR_RUN_RIGHT_FILE = "player_run_right.png"
CHAR_RUN_LEFT_FILE = "player_run_left.png"
CHAR_JUMP_RIGHT_FILE = "player_jump_right.png"
CHAR_JUMP_LEFT_FILE = "player_jump_left.png"
#The cop sprites (same 4-pose pattern as the player)
COP_STILL_FILE = "cop_idle.png"
COP_RUN_RIGHT_FILE = "cop_run_right.png"
COP_RUN_LEFT_FILE = "cop_run_left.png"
COP_JUMP_RIGHT_FILE = "cop_jump_right.png"
COP_JUMP_LEFT_FILE = "cop_jump_left.png"
#Custom arcade font
ARCADE_FONT_FILE = "Star Crush.ttf"
#Where the scoreboard is saved into a json file
SCORES_FILE = os.path.join(ASSETS_DIR, "scores.json")

#Player physics and visuals
#Size of the hitbox of the character (collision rectangle)
PLAYER_W, PLAYER_H = 32, 48
#Target height of the character by scaling the PNGs to this height
SPRITE_TARGET_H = 100
#Small offset so that the character's feet can line up nicely with the collision rectangle
FEET_OFFSET_Y = 10

#Default size of the next platform the player places (core climbing mechanic)
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

#Top-right minimap HUD (Step 10) — a slim vertical bar showing how close the
#player and cop are to the goal, since the level is climbed vertically.
#World y=0 (top) maps to the top of the bar, world_h (bottom/spawn) to the
#bottom of the bar. Purely a height/progress readout, not an x-position map.
MINIMAP_W = 18
MINIMAP_H = 320
MINIMAP_MARGIN = 20
MINIMAP_DOT_R = 7
MINIMAP_BG_COLOR = (0, 0, 0, 140)
MINIMAP_BORDER_COLOR = (255, 255, 255)
MINIMAP_PLAYER_COLOR = (60, 140, 255)
MINIMAP_COP_COLOR = (220, 60, 60)
MINIMAP_GOAL_COLOR = (255, 215, 0)
#Window title is displayed at the top of the pygame window
WINDOW_TITLE = "CURSUS COLOSSEI"

#Game states here in order to help us switch screens
#Going from menu -> name_input -> difficulty -> map_preview -> game -> scoreboard
STATE_SPLASH = "splash"
STATE_MENU = "menu"
STATE_NAME = "name"
STATE_DIFFICULTY = "difficulty"
STATE_MAP_PREVIEW = "map_preview"
STATE_SCOREBOARD = "scoreboard"
STATE_GAME = "game"
STATE_WIN = "win"

#Difficulty levels — chosen on the difficulty-select screen, stored on GameApp,
#and used to tune the Cop AI (Step 7) and to pick which leaderboard bucket a
#finished run gets saved to (Step 12).
DIFFICULTY_EASY = "easy"
DIFFICULTY_MEDIUM = "medium"
DIFFICULTY_HARD = "hard"

#Cop AI tuning per difficulty (see cop.py). Speed is relative to the player's
#own speed=260: Easy is slower (70%), Medium matches it, Hard is faster.
#Reaction delay is how long (seconds) the cop's AI waits before it "notices"
#a fresh player position — bigger delay = laggier, easier to shake off.
#Start gap is how far behind the player (in world x, along the floor) the
#cop spawns — bigger gap = more head start for the player.
COP_SPEED_BY_DIFFICULTY = {
    DIFFICULTY_EASY: 180.0,
    DIFFICULTY_MEDIUM: 260.0,
    DIFFICULTY_HARD: 310.0,
}
COP_REACTION_DELAY_BY_DIFFICULTY = {
    DIFFICULTY_EASY: 0.6,
    DIFFICULTY_MEDIUM: 0.3,
    DIFFICULTY_HARD: 0.1,
}
COP_START_GAP_BY_DIFFICULTY = {
    DIFFICULTY_EASY: 220,
    DIFFICULTY_MEDIUM: 140,
    DIFFICULTY_HARD: 80,
}
#How long (seconds) the cop keeps attempting a normal jump toward the player
#before giving up and "cheating" — a guaranteed hop toward them (see cop.py).
#Hard barely tries before cheating; Easy tries for a while first, giving the
#player more breathing room and making the cop feel like it's genuinely
#struggling.
COP_PATIENCE_BY_DIFFICULTY = {
    DIFFICULTY_EASY: 2.5,
    DIFFICULTY_MEDIUM: 1.2,
    DIFFICULTY_HARD: 0.3,
}

#Supabase settinigs added in the game (live dynamic database)
#The anon key below is the PUBLIC key — it's meant to be embedded in client
#code exactly like this (that's the whole point of it existing). Security
#comes from the Row Level Security policies on the `scores` table (read +
#insert only, no update/delete), not from hiding this value. The SEPARATE
#service_role/secret key must never appear here or anywhere in this project.
SUPABASE_URL = "https://ohktexvcncybtzyohsqy.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9oa3RleHZjbmN5YnR6eW9oc3F5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY0NjczMTAsImV4cCI6MjEwMjA0MzMxMH0.0stGZI9hoMQadDNgDU0vwDf7ItfWmjfD1kr3nUeoWks"
SUPABASE_SCORES_TABLE = "scores"
#How long (seconds) the desktop build waits for a Supabase response before
#giving up and falling back to the local scores.json leaderboard. The web
#build has no equivalent timeout knob — the browser's own Fetch API handles
#that.
SUPABASE_REQUEST_TIMEOUT = 5
