# Assets

Art is in. Every asset loader still fails soft (missing files never crash
the game, per `utils.safe_load_image`) — this list is what's actually
wired up and what's still needed.

| File | Purpose |
|---|---|
| `background.png` | Main gameplay background (Colosseum courtyard). Its pixel size **defines the world size**. Currently 1920x1080 — exactly screen-sized, so the camera can't scroll; swap in a taller shot later if a bigger world is wanted. |
| `first_screen.png` | Splash/intro screen shown before the menu ("CURSUS COLOSSEI" title art). |
| `menu_background.png` | Menu screen background. |
| `scoreboard_background.png` | Scoreboard screen background. |
| `final_background.png` | Background for the dedicated win ("photo captured") screen — not wired up yet, planned for Step 11. |
| `player_idle.png` | Tourist/photographer — idle sprite. |
| `player_run_right.png` | Tourist/photographer — running right. |
| `player_run_left.png` | Tourist/photographer — running left. |
| `cop_idle.png` | Police officer — idle sprite. |
| `cop_run_right.png` | Police officer — running right. |
| `cop_run_left.png` | Police officer — running left. |
| `arcade_font.ttf` | Custom TTF used for HUD/menu text — still not provided, falls back to the default pygame font. |
| `theme_music.ogg` | Looping background music (OGG for web/browser compatibility) — not provided yet. |
| `siren.ogg` | Optional — short stinger played when the cop catches you. |
| `camera_shutter.ogg` | Optional — short stinger played when you take the winning photo. |
| `scores.json` | Auto-created/updated leaderboard (per-difficulty, from Step 12 onward). |

## Not wired up yet (sitting in this folder unused)

- `jumping left.png`, `jumping right.png`, `Cop Jumping left.png`, `Cop Jumping right.png` — a 4th "jumping" pose for both characters. The code currently only ever shows idle/run-left/run-right; adding a jump pose is deferred to the Step 13 art/polish pass so it doesn't expand scope mid-step.
- `standing still right.png` — a near-duplicate of `player_idle.png` (both front-facing, no real left/right difference). Left in place but unused; `player_idle.png` is the one actually loaded.

Sprites follow the reference game's pattern: 3 poses per character (idle,
run-left, run-right), scaled to a fixed height at load time.
