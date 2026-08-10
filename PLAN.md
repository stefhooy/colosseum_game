# Colosseum Curfew — Build Plan

Working title: **Colosseum Curfew**. A 2D vertical platformer built with Python + Pygame, reusing the architecture and mechanics of *Tower of IE: The Wizard Climb* (reference game).

**Premise:** It's September, the last month of summer. You're a tourist/photographer in Rome who wants one last epic photo from the very top of the Colosseum before heading back to work. Climbing it is off-limits — a police officer spots you and chases you up the structure. Caught = lose. Reach the top and take the photo = win.

This is worked through as an ordered sequence of steps on the `dev` branch. **One step at a time** — implement, test, confirm, then move to the next. `web` branch is reserved for the Pygbag/WebAssembly build track once we get there.

---

## Steps

1. **Read the reference repo** — `settings.py`, `utils.py`, `scores.py`, `effects.py`, `audio.py`, `camera.py`, `platform.py`, `player.py`, `screens.py`, `app.py`, `main.py`, README, `pyproject.toml`, `pygbag.ini`. Confirm conventions before writing new code. ✅ done
2. **Scaffold the new project** — mirror the `game/` package layout (`settings.py`, `utils.py`, `camera.py`, `platform.py`, `player.py`, `cop.py`, `effects.py`, `audio.py`, `scores.py`, `screens.py`, `app.py`) + `main.py` + `pyproject.toml` + `pygbag.ini` + empty `assets/` with a README noting expected files.
3. **Port the skeleton** — `camera.py`, `utils.py`, `platform.py`, `player.py`, `audio.py`, `scores.py` with only theme-appropriate renames (state constants, window title, asset filenames, world-size-from-background behavior). No new features yet — just get it running with placeholder assets.
4. **Author the fixed Colosseum level** — `level.py` (or level data file) replacing the "start with just a floor" approach. Keep editor mode as a hidden dev-only tool for authoring/tuning the layout.
5. **Pre-game map preview screen** — shows the full Colosseum background scaled to fit, spawn + goal marked, "memorize your route" prompt.
6. **Difficulty-select screen** — Easy / Medium / Hard, wired into `GameApp`.
7. **Cop entity + AI chase logic** — mirrors `Player`'s rect/physics/collision, AI-driven along precomputed waypoints, tuned per difficulty.
8. **Wire the cop into `app.py`** — per-frame update/draw, add `STATE_GAMEOVER` "caught" flow alongside the existing win flow.
9. **Zoomed-out "grandiose" camera** — off-screen virtual-resolution surface + `smoothscale`, confirm all draw calls still align.
10. **Top-right minimap HUD** — vertical progress bar with player/cop/goal markers.
11. **Win ("photo captured") and lose ("caught") overlays** — matching the visual language of the existing win-box overlay.
12. **Per-difficulty leaderboard (local JSON)** — each score stores `difficulty`, ranked/truncated to top-10 within its own bucket; scoreboard screen shows all three (stacked or tabbed, clearly labeled, switchable without leaving the screen).
13. **Final art/audio pass + verify both build targets** — desktop (`python main.py` / PyInstaller) and web (`python -m pygbag --build main.py`), following the reference repo's itch.io packaging steps.
14. **Online leaderboard via Supabase** — added after the game is fully working locally. Migrates/extends the step-12 leaderboard to a live Supabase-backed scoreboard. User is new to Supabase, so this step introduces concepts as they come up (project setup, schema, Python client) rather than all at once.

---

## New systems (detail)

### Cop AI chaser
- Own `pygame.Rect`, vx/vy, gravity, jump, idle/run-left/run-right sprites, same two-pass move-and-collide as `Player`.
- Precompute an ordered "climb path" of waypoints up the tower once at level-load time (since the level is fixed). AI steers toward the player's x when at similar height, otherwise toward the next waypoint above; jumps when a waypoint requires it.
- Difficulty tuning (relative to player's `speed=260`, `jump_strength=650`, `gravity=1400`):
  - **Easy**: ~180 px/s, ~0.6s reaction delay, head-start gap behind player.
  - **Medium**: ~250–260 px/s, ~0.3s reaction delay, normal starting gap.
  - **Hard**: ~300–320 px/s, ~0.1s reaction delay, smaller starting gap.
- Lose: `cop.rect.colliderect(player.rect)` → `STATE_GAMEOVER`.

### Zoomed-out camera + minimap
- Render the whole scene to a virtual-resolution surface `(SCREEN_W/zoom, SCREEN_H/zoom)`, then `smoothscale` up once per frame. Existing `draw()` methods stay unchanged.
- Top-right vertical bar HUD: player (blue dot), cop (red dot), goal (gold marker), scaled to `world_h`.

### Fixed level
- Colosseum tiers/arches authored as fixed `Platform` objects (`level.py` or small JSON/level-data file). Editor mode (`E`) kept as a hidden dev tool for authoring, but the shipped game always loads the fixed level.

### Scoring — per-difficulty leaderboard
- Each entry: `{"name": str, "time": float, "difficulty": "easy"|"medium"|"hard"}`.
- `add_score(player_name, time_seconds, difficulty)` ranks/truncates to top-10 within that difficulty only.
- Scoreboard screen shows all three lists (stacked columns or tabs/pages switchable with left/right or 1/2/3), difficulty clearly labeled.

---

## Assets needed (new — do not reuse the wizard-tower art)
- Colosseum background (late-summer/dusk lighting) — defines world size.
- Player sprite set (tourist/photographer): idle, run-left, run-right.
- Cop sprite set: idle, run-left, run-right.
- Optional: camera/flash icon for the goal marker, siren-light accents for the cop's minimap marker.
- Menu/scoreboard/splash background art in the Rome theme.
- Music: Rome-evocative loop, siren stinger (caught), camera-shutter SFX (win). Same dual-backend `audio.py` pattern as the reference (native `HTMLAudioElement` on web via `sys.platform == "emscripten"`, `pygame.mixer` on desktop).
