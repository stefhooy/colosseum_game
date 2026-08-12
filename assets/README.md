# Assets

Art is in. Every asset loader still fails soft (missing files never crash
the game, per `utils.safe_load_image`) — this list is what's actually
wired up and what's still needed.

| File | Purpose |
|---|---|
| `background.png` | Main gameplay background (Colosseum courtyard). Its pixel size **defines the world size**. Currently 1920x1080 — exactly screen-sized; `CAMERA_ZOOM < 1.0` (Step "camera zoom") crops into it rather than needing anything taller. |
| `first_screen.png` | Splash/intro screen shown before the menu ("CURSUS COLOSSEI" title art). |
| `menu_background.png` | Menu screen background. |
| `scoreboard_background.png` | Scoreboard screen background. |
| `final_background.png` | Background for the dedicated win ("photo captured") screen (`STATE_WIN` / `run_win_screen`, Step 11). |
| `player_idle.png` | Tourist/photographer — idle sprite, transparent background. |
| `player_run_right.png` | Tourist/photographer — running right, transparent background. |
| `player_run_left.png` | Tourist/photographer — running left, transparent background. |
| `cop_idle.png` | Police officer — idle sprite, transparent background. |
| `cop_run_right.png` | Police officer — running right, transparent background. |
| `cop_run_left.png` | Police officer — running left, transparent background. |
| `player_jump_right.png` / `player_jump_left.png` | Tourist/photographer — airborne pose (jumping or falling), transparent background, shown whenever `not on_ground`. Renamed from `jumping right/left.png` during Step 13's web-build verification — pygbag can't handle spaces in real asset filenames. |
| `cop_jump_right.png` / `cop_jump_left.png` | Police officer — airborne pose, transparent background, also shown mid cheat-hop (reads as a leap toward the player). Renamed from `Cop Jumping right/left.png`, same reason as above. |
| `Nabla-Regular.ttf` | Custom TTF (`ARCADE_FONT_FILE` in settings.py), used for every piece of text in the game. **This is a processed copy, not the font as-downloaded** — see the "Not wired up" note below and PLAN.md's "Two-font system" section for the full story of why. |
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
- `Star Crush.ttf` / `Star Crush.otf` — the previous display font, fully replaced by Nabla. Kept in case Nabla ever needs to be reverted.
- `SAMBA TEMPERADO 2015.mp3` — the source file `theme_music.ogg` was converted from. Kept as the original; not loaded by the game directly (pygame/browsers want ogg, not mp3).
- `1001fonts-star-crush-eula.txt` — license terms for the (now-unused) Star Crush font. Kept for attribution/licensing reference.
- `Nabla-Regular-original-color-font.ttf` — **the font exactly as downloaded**, a color/variable font (COLR/CPAL/SVG tables, for its signature layered-shadow look). This is NOT the file the game loads. pygame's text renderer (SDL_ttf) can only render plain monochrome outline glyphs — it fails on almost every character against this original file, even after instancing it down to a static (non-variable) font. The actual `assets/Nabla-Regular.ttf` the game uses is a processed copy of this file: instanced to its default axis values, then had the COLR/CPAL/SVG tables stripped out via `fonttools`, leaving just the plain glyf outlines underneath (which turned out to be complete, legible shapes on their own — Nabla's color "depth" layers are recolored copies of this same base outline). If Nabla's source font ever gets updated, redo this same processing on the new file rather than dropping it straight into `assets/`.

Sprites follow the reference game's pattern, extended with a 4th pose: idle,
run-left, run-right, and jump/airborne, scaled to a fixed height at load time.
