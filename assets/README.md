# Assets

This folder is empty for now — the game runs on placeholder fallback colors
until real art/audio lands (every asset loader fails soft: missing files
never crash the game, per `utils.safe_load_image`). Expected files, named
to match what `game/settings.py` will reference once ported in Step 3:

| File | Purpose |
|---|---|
| `background.png` | Main gameplay background (Colosseum). Its pixel size **defines the world size** for the camera and player bounds. |
| `first_screen.jpg` | Splash/intro screen shown before the menu. |
| `menu_background.png` | Menu screen background. |
| `scoreboard_background.png` | Scoreboard screen background. |
| `player_idle.png` | Tourist/photographer — idle sprite. |
| `player_run_right.png` | Tourist/photographer — running right. |
| `player_run_left.png` | Tourist/photographer — running left. |
| `cop_idle.png` | Police officer — idle sprite. |
| `cop_run_right.png` | Police officer — running right. |
| `cop_run_left.png` | Police officer — running left. |
| `arcade_font.ttf` | Custom TTF used for HUD/menu text (falls back to the default pygame font if missing). |
| `theme_music.ogg` | Looping background music (OGG for web/browser compatibility). |
| `siren.ogg` | Optional — short stinger played when the cop catches you. |
| `camera_shutter.ogg` | Optional — short stinger played when you take the winning photo. |
| `scores.json` | Auto-created/updated leaderboard (per-difficulty, from Step 12 onward). Not committed to git once populated with real runs. |

Sprites follow the same pattern as the reference game: 3 poses per
character (idle, run-left, run-right), scaled to a fixed height at load
time — no walk-cycle animation frames needed.
