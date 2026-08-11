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
| `final_background.png` | Background for the dedicated win ("photo captured") screen (`STATE_WIN` / `run_win_screen`, Step 11). |
| `player_idle.png` | Tourist/photographer — idle sprite. |
| `player_run_right.png` | Tourist/photographer — running right. |
| `player_run_left.png` | Tourist/photographer — running left. |
| `cop_idle.png` | Police officer — idle sprite. |
| `cop_run_right.png` | Police officer — running right. |
| `cop_run_left.png` | Police officer — running left. |
| `player_jump_right.png` / `player_jump_left.png` | Tourist/photographer — airborne pose (jumping or falling), shown whenever `not on_ground`. Renamed from `jumping right/left.png` during Step 13's web-build verification — pygbag can't handle spaces in real asset filenames. |
| `cop_jump_right.png` / `cop_jump_left.png` | Police officer — airborne pose, also shown mid cheat-hop (reads as a leap toward the player). Renamed from `Cop Jumping right/left.png`, same reason as above. |
| `Star Crush.ttf` | Custom TTF used for HUD/menu/title text (`ARCADE_FONT_FILE` in settings.py). |
| `theme_music.ogg` | Looping background music. Converted from the source mp3 with `ffmpeg -ar 44100 -ac 2 -c:a libvorbis`, explicitly pinned to 44100 Hz stereo to match `pygame.mixer.pre_init(44100, ...)` in app.py — a mismatched sample rate is what caused the previous game's Firefox/Chrome playback issue, so this is deliberate, not a default. |
| `siren.ogg` | Optional stinger for the cop catching you — user decided not to add this. |
| `camera_shutter.ogg` | Optional stinger for the winning photo — user decided not to add this. |
| `scores.json` | Auto-created/updated leaderboard (per-difficulty, from Step 12 onward). |

## Not wired up (`assets/unused/`, not loaded by the game)

These live in a subfolder, not `assets/` directly — the source mp3 has spaces
in its filename and an unsupported format, both of which would break the
`pygbag` web build if pygbag ever scanned them (it validates every file
under `assets/`, not just what the game code loads). `assets/unused/` is
excluded wholesale via `pygbag.ini`'s `ignoredirs`.

- `standing still right.png` — a near-duplicate of `player_idle.png` (both front-facing, no real left/right difference). `player_idle.png` is the one actually loaded.
- `Star Crush.otf` — an OTF sibling of the TTF that's actually loaded. Only one font format is needed.
- `SAMBA TEMPERADO 2015.mp3` — the source file `theme_music.ogg` was converted from. Kept as the original; not loaded by the game directly (pygame/browsers want ogg, not mp3).
- `1001fonts-star-crush-eula.txt` — license terms for the Star Crush font. Not an asset the game loads, just keep it around for attribution/licensing reference.

Sprites follow the reference game's pattern, extended with a 4th pose: idle,
run-left, run-right, and jump/airborne, scaled to a fixed height at load time.
