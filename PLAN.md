# Cursus Colossei — Build Plan

**Cursus Colossei** ("Colosseum Run," Latin). A 2D vertical platformer built with Python + Pygame, reusing the architecture and mechanics of *Tower of IE: The Wizard Climb* (reference game).

**Premise:** It's September, the last month of summer. You're a tourist/photographer in Rome who wants one last epic photo from the very top of the Colosseum before heading back to work. Climbing it is off-limits — a police officer spots you and chases you up the structure. Caught = lose. Reach the top and take the photo = win.

This is worked through as an ordered sequence of steps on the `dev` branch. **One step at a time** — implement, test, confirm, then move to the next. `web` branch is reserved for the Pygbag/WebAssembly build track once we get there.

---

## Core mechanic (revised after Step 7)

The level is **not** a fixed, pre-authored layout. It starts with just a floor — the player builds their own platforms live, in real time, while running and being chased (no pause, no limit on placement), exactly like the reference game's dev editor except this is core gameplay here, not a hidden tool. The cop has no fixed path to follow either: it always heads toward wherever the player currently is, jumping normally when there's a platform to jump to, and performing a guaranteed "cheat hop" (position driven directly, not physics-based) when it's been stuck too long — see `cop.py`. Spawn and goal are still fixed points; only the climb between them is user-built.

---

## Steps

1. **Read the reference repo** — confirmed conventions before writing new code. ✅ done
2. **Scaffold the new project** — mirrored the `game/` package layout + `main.py` + `pyproject.toml` + `pygbag.ini` + `assets/`. ✅ done
3. **Port the skeleton** — `camera.py`, `utils.py`, `platform.py`, `player.py`, `audio.py`, `scores.py` ported with theme renames. ✅ done
4. ~~Author the fixed Colosseum level~~ — superseded; level is empty by design (see "Core mechanic" above). `level.py` now just defines the floor, spawn, and goal. ✅ done (revised)
5. **Pre-game map preview screen** — shows the background, spawn, and goal (no route to memorize anymore, since there's no fixed route). ✅ done
6. **Difficulty-select screen** — Easy / Medium / Hard, wired into `GameApp`. ✅ done
7. **Cop entity + AI chase logic** — mirrors `Player`'s rect/physics/collision; always chases the player directly, with a guaranteed cheat-hop fallback when stuck (no fixed layout to path along). ✅ done
8. **Wire the cop into `app.py`** — cop is now updated/drawn every frame, with a `self.caught` flag (mirroring `self.win`) that freezes both entities and shows a basic "THE COP CAUGHT YOU!" overlay; a full dedicated `STATE_GAMEOVER` screen comes in Step 11 along with the dedicated win screen. ✅ done
9. **Zoomed-out "grandiose" camera** — gameplay now renders onto an off-screen virtual surface (`game_surface`, sized `SCREEN * CAMERA_ZOOM`) which is smoothscaled to the real window every frame; all draw calls (background, platforms, player, cop, HUD, overlays) and mouse-to-world math go through it. `CAMERA_ZOOM` (settings.py) is left at `1.0` for now since `background.png` is exactly screen-sized — bumping it later reveals more world once a taller background exists. ✅ done
10. **Top-right minimap HUD** — a slim vertical bar (`effects.draw_minimap`) tracking height only (this is a vertical climb, so height IS progress): blue dot for the player, red for the cop, gold diamond for the goal, all mapped from world y onto the bar via `world_h`. ✅ done
11. **Win ("photo captured") and lose ("caught") screens** *(next up)* — a dedicated full-screen win moment (using `final_background.png`, decided once real art arrived — not just a small overlay box) plus a lose overlay matching the existing visual language.
12. **Per-difficulty leaderboard (local JSON)** — each score stores `difficulty`, ranked/truncated to top-10 within its own bucket; scoreboard screen shows all three (stacked or tabbed, clearly labeled, switchable without leaving the screen).
13. **Final art/audio pass + verify both build targets** — desktop (`python main.py` / PyInstaller) and web (`python -m pygbag --build main.py`), following the reference repo's itch.io packaging steps.
14. **Online leaderboard via Supabase** — added after the game is fully working locally. Migrates/extends the step-12 leaderboard to a live Supabase-backed scoreboard. User is new to Supabase, so this step introduces concepts as they come up (project setup, schema, Python client) rather than all at once.

---

## New systems (detail)

### Cop AI chaser
- Own `pygame.Rect`, vx/vy, gravity, jump, idle/run-left/run-right sprites, same two-pass move-and-collide as `Player`.
- No precomputed path — always steers toward the player's (reaction-delayed) x, jumps when the player is above and it's grounded.
- If stuck without real upward progress longer than its per-difficulty *patience*, performs a "cheat hop": position interpolated directly to a point toward the player (capped rise) over a fixed 0.35s, bypassing jump physics entirely so it can never fail to land. A small landing pad is placed under the hop's destination.
- Difficulty tuning (relative to player's `speed=260`, `jump_strength=650`, `gravity=1400`):
  - **Easy**: 180 px/s, 0.6s reaction delay, 220px starting gap, 2.5s patience before cheating.
  - **Medium**: 260 px/s, 0.3s reaction delay, 140px starting gap, 1.2s patience.
  - **Hard**: 310 px/s, 0.1s reaction delay, 80px starting gap, 0.3s patience.
- Lose: `cop.rect.colliderect(player.rect)` → `STATE_GAMEOVER`.

### Zoomed-out camera + minimap
- Gameplay renders to a virtual-resolution surface `(SCREEN_W*CAMERA_ZOOM, SCREEN_H*CAMERA_ZOOM)` (`GameApp.game_surface`), then `pygame.transform.smoothscale`s onto the real window once per frame in `_run_game_frame`. Existing `draw()` methods stay unchanged — they just get called with `game_surface` instead of `screen`.
- `Camera` is sized to the virtual surface, not the real window, so `camera.follow`/`clamp` math is entirely in virtual-surface space.
- Mouse position is scaled from real-window pixels to virtual-surface pixels (`GameApp._mouse_virtual_pos`) before any world-coordinate math, so platform placement still lines up with the cursor regardless of zoom.
- `CAMERA_ZOOM = 1.0` for now (settings.py) — see note below.
- Top-right vertical bar HUD (`effects.draw_minimap`, called from `GameApp._draw`): player (blue dot), cop (red dot), goal (gold diamond), each mapped from world y to a position along the bar via `world_h`. It only tracks height, not x — this is a vertical climb, so height is the whole notion of "progress."
- Note: current `background.png` is exactly screen-sized (1920x1080), so there's no vertical scroll room yet, and `CAMERA_ZOOM > 1.0` would reveal empty space past the background's edges — the render pipeline is ready, but the zoom itself is deferred until a taller background lands.

### Live platform-building (replaces the old "fixed level" idea)

- `level.py` only defines the floor, spawn, and a fixed goal position near the world's top.
- Placing/removing platforms (left click / right click, `[`/`]` width, numpad `-`/`+` height) is always active during gameplay — no toggle, no pause. This is the core climbing mechanic, not a hidden dev tool.
- Unlimited placement — no cooldown or cap. The cop's speed/pressure is the difficulty lever, not platform scarcity.

### Scoring — per-difficulty leaderboard

- Each entry: `{"name": str, "time": float, "difficulty": "easy"|"medium"|"hard"}`.
- `add_score(player_name, time_seconds, difficulty)` ranks/truncates to top-10 within that difficulty only.
- Scoreboard screen shows all three lists (stacked columns or tabs/pages switchable with left/right or 1/2/3), difficulty clearly labeled.

---

## Assets (in `assets/`, real art as of this step)

- `background.png`, `first_screen.png`, `menu_background.png`, `scoreboard_background.png`, `final_background.png` — see `assets/README.md` for what each is used for.
- Player sprite set (tourist/photographer): `player_idle.png`, `player_run_left/right.png`.
- Cop sprite set: `cop_idle.png`, `cop_run_left/right.png`.
- Still needed: `arcade_font.ttf`, `theme_music.ogg`, optional `siren.ogg` / `camera_shutter.ogg` SFX.
- Sitting unused for now (see `assets/README.md`): jump-pose sprites (deferred to Step 13 polish), a duplicate idle image.
