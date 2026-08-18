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

#Zoom factor for the gameplay camera (Step 9). Gameplay is rendered onto an
#off-screen "virtual" surface of size (SCREEN_W*CAMERA_ZOOM, SCREEN_H*CAMERA_ZOOM),
#then smoothscaled to fill the real window. CAMERA_ZOOM > 1.0 shows MORE of
#the world at once (zoomed out, things appear smaller); CAMERA_ZOOM < 1.0
#shows LESS of the world (zoomed in, things appear bigger) — since that's
#cropping INTO the existing screen-sized background rather than needing
#anything beyond its edges, it works fine even though background.png is
#exactly screen-sized (unlike zooming out, which would need a taller
#background to avoid revealing empty space past its edges).
#0.6 = the camera shows a 60%-sized window of the world, scaled back up
#~1.67x — sprites/platforms read bigger, and the camera now has real room
#to scroll/follow the player instead of the whole field being visible at
#once. Tune this single number to taste.
CAMERA_ZOOM = 0.6
#Note: a mouse-driven camera lookahead was tried here (nudging the camera
#toward wherever the mouse points, to help aim beyond the current view
#while standing still) but was reverted at the user's request — they wanted
#the camera fully decoupled from the mouse and predictable: it only ever
#follows the player. Building is limited to whatever's currently visible.

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
ARCADE_FONT_FILE = "Nabla-Regular.ttf"
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
#Brief red flash + crack marks shown where the cop just destroyed a
#player-built platform (its last-resort fallback when stuck too long — see
#cop.py's _break_nearest_platform), so it reads as a visible, fair event
#instead of a platform just silently vanishing
PLATFORM_BREAK_COLOR = (255, 60, 60)
PLATFORM_BREAK_DURATION = 0.4
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
STATE_WARNING = "warning"
STATE_CONTROLS = "controls"
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
#Flat grace period (seconds) at the start of EVERY run, all difficulties,
#where the cop just stands still — on top of the spatial start gap above,
#not instead of it. Gives the player a fair, consistent moment to get moving
#before the chase begins, regardless of which difficulty tuning applies.
COP_HEADSTART_SECONDS = 1.0
#How long (seconds) the cop tries a normal jump before it builds its OWN
#platform to climb — its main way of keeping pace once the player starts
#building. This is the routine behavior, not a rare fallback: it should
#trigger often enough that the cop feels like a real competing builder, not
#just a follower. Hard barely waits; Easy gives the player real breathing
#room before the cop starts constructing.
COP_BUILD_PATIENCE_BY_DIFFICULTY = {
    DIFFICULTY_EASY: 2.0,
    DIFFICULTY_MEDIUM: 1.2,
    DIFFICULTY_HARD: 0.5,
}
#How long (seconds) the cop keeps trying (real jumps + building its own
#platforms) before resorting to its actual last resort: destroying the
#nearest player-built platform (see cop.py's _break_nearest_platform). Much
#longer than the build patience above — building should resolve most stuck
#situations on its own, so breaking should be rare, not routine.
COP_BREAK_PATIENCE_BY_DIFFICULTY = {
    DIFFICULTY_EASY: 6.0,
    DIFFICULTY_MEDIUM: 4.0,
    DIFFICULTY_HARD: 2.5,
}
#How long (seconds) the cop takes to actually finish building a platform
#once it decides to — separate from build PATIENCE above (which is how long
#it waits before deciding to build at all). The cop is frozen in place for
#this whole duration, so it's a real, visible "the cop is slower/faster at
#building" difference, not just a number — Hard barely pauses, Easy stands
#there constructing for over a second, giving the player a window.
COP_BUILD_DURATION_BY_DIFFICULTY = {
    DIFFICULTY_EASY: 1.2,
    DIFFICULTY_MEDIUM: 0.7,
    DIFFICULTY_HARD: 0.3,
}
#Size of the platform the cop builds for itself — a bit smaller than the
#player's own default (DEFAULT_PLAT_W/H), so its stepping stones read as
#hastily-built rather than as polished as the player's construction.
COP_BUILD_PLAT_W = 130
COP_BUILD_PLAT_H = 16
#How high above its current position the cop's self-built platform appears —
#capped so it's reachable by the cop's own normal jump afterward (a real
#player jump covers ~151px at jump_strength=650/gravity=1400; this stays
#comfortably under that so the cop can actually reach what it just built).
COP_BUILD_RISE = 120
#Safety cap so a pathological stall can't repeat forever — fails soft
MAX_COP_BUILDS = 300
#Tint for the cop's own self-built platforms — matches the cop's
#established red identity (MINIMAP_COP_COLOR), so it's visually obvious
#these are the COP's platforms, not the player's. Deliberately a duller,
#more brick-toned red than PLATFORM_BREAK_COLOR's brighter flash, so a
#permanent cop-built platform doesn't get visually confused with the
#brief "just broke something" flash effect.
COP_PLATFORM_FILL = (150, 55, 45)
COP_PLATFORM_OUTLINE = (70, 20, 15)

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
SUPABASE_REQUEST_TIMEOUT = 511