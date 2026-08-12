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
11. **Win ("photo captured") and lose ("caught") screens** — win is now a dedicated full-screen `STATE_WIN` (`screens.run_win_screen`) using `final_background.png`, reached the instant the win condition finalizes in `_run_game_frame` (replaces the old small overlay box entirely). Lose stays as the existing in-place "THE COP CAUGHT YOU!" overlay — same black-box/red-border visual language as before; no dedicated background art exists for it yet, so a full screen wasn't warranted. ✅ done
12. **Per-difficulty leaderboard (local JSON)** — `add_score(name, time, difficulty)` tags each entry and trims each difficulty's bucket to its own top 10 independently (a Hard run can't bump an Easy run off the list). Scoreboard screen (`run_scoreboard`) is now tabbed — 1/2/3 switches between EASY/MEDIUM/HARD without leaving the screen, opens on whichever difficulty was just played (`self.difficulty` passed in from `GameApp`). ✅ done
13. **Final art/audio pass + verify both build targets** — jump-pose sprites wired in as a 4th animation state (player + cop, shown while airborne); font/music already landed. Desktop build (PyInstaller) fully verified: builds clean, launches, runs stably with all assets bundled. Web build (pygbag) verified end-to-end for packaging — found and fixed two real bugs along the way (see "Web build gotchas" below); final HTML/JS wrapper generation needs a real internet connection to pygbag's CDN, which the dev sandbox this was built in doesn't have, so that last step should be re-run on a normal machine (should now succeed cleanly). ✅ done
14. **Online leaderboard via Supabase** — a shared `scores` table (schema + RLS policies in "Supabase leaderboard" below) now backs the scoreboard alongside the local one: winning a run fires a best-effort background sync to Supabase (`scores.add_score_online`) right after the unconditional local save, and the scoreboard screen fetches from Supabase with an instant local-data fallback (`scores.load_scores_online_by_difficulty`), so the game is never blocked by or dependent on the network. Desktop path fully verified end-to-end against the live project (real submit + real fetch + fail-soft-when-unreachable, all tested). Web path is implemented using pygbag's own internal Fetch-API-bridge technique but **not yet verified in a real browser** — needs testing once you have an actual pygbag web build running (see Step 13's note on finishing that build on your own machine). ✅ done (desktop) / ⏳ web path needs real-browser verification

---

## New systems (detail)

### Cop AI chaser
- Own `pygame.Rect`, vx/vy, gravity, jump, idle/run-left/run-right/jump sprites, same two-pass move-and-collide as `Player`.
- No precomputed path — always steers toward the player's (reaction-delayed) x, jumps when the player is above and it's grounded.
- **Stuck fallback — platform-breaking, not teleporting** (replaced the original "cheat hop" mechanic entirely after player feedback that a position-teleport felt overpowered, even after an earlier rebalance pass toned its speed/height down). If stuck without real upward progress longer than its per-difficulty *patience*, the cop now destroys the nearest player-built platform (`Cop._break_nearest_platform`) instead — the floor (`platforms[0]`) can never be targeted. This is a genuine last resort, not a routine catch-up tool: patience is long (see below), real jumps are always attempted first, and breaking one platform resets the stuck timer so the cop gets a fresh full-patience shot at climbing normally before it would ever consider breaking another. A brief red flash + crack mark (`GameApp.break_effects`, `PLATFORM_BREAK_COLOR/DURATION`) shows where the platform used to be, so it reads as a visible, fair event instead of a platform silently vanishing.
- Difficulty tuning (relative to player's `speed=260`, `jump_strength=650`, `gravity=1400`):
  - **Easy**: 180 px/s, 0.6s reaction delay, 220px starting gap, 6.0s patience before breaking a platform.
  - **Medium**: 260 px/s, 0.3s reaction delay, 140px starting gap, 4.0s patience.
  - **Hard**: 310 px/s, 0.1s reaction delay, 80px starting gap, 2.5s patience.
  - (Patience raised substantially across the board once the mechanic became "rare last resort" rather than "routine catch-up" — these numbers mean minutes can pass without the cop ever needing to break anything, as long as real jumps keep making progress.)
- Lose: `cop.rect.colliderect(player.rect)` → `STATE_GAMEOVER`.

### Ground-probe fix (sprite flicker, post-launch player feedback)
Player and cop both showed a "glitch/frenzy" flicker between idle and jump poses even while standing completely still. Root cause was latent since Step 1 (inherited from the reference game), just invisible until jump-pose sprites started reading `on_ground` every frame: gravity accumulates each frame, but the vertical move rounds to `int()` pixels, so on frames where the accumulated fall rounds to 0px the entity doesn't move — and pygame's `colliderect` treats two rects that are merely touching (no overlap) as NOT colliding, so `on_ground` flickers false for a frame even though nothing actually left the ground. Fixed in both `Player.move_and_collide` and `Cop.move_and_collide` with a standard "ground probe": if `on_ground` is still false after the normal collision pass and `vy >= 0`, check a copy of the rect nudged 2px down against the platform list — catches "resting exactly on top" without needing a fresh pixel of real overlap, and without actually moving the entity.

### Music timing (post-launch player feedback, revised twice)
First moved from "starts the instant you leave the splash screen" to "starts when the run actually begins" (map-preview → `STATE_GAME` transition) — then the user clarified they actually wanted it even earlier: playing immediately on launch, before any interaction at all. `play_music()` is now called directly in `GameApp.__init__`, right after `init_audio()`. On desktop this just works, no restriction. On web, browsers enforce a hard "needs a real user gesture" autoplay policy no code can bypass — `audio.py`'s web path already fails that quietly (`_web_play`'s `.catch(...)`), so the call is harmless there too, it just won't produce sound until the player's first click/keypress in that build specifically.

### Zoomed-out camera + minimap
- Gameplay renders to a virtual-resolution surface `(SCREEN_W*CAMERA_ZOOM, SCREEN_H*CAMERA_ZOOM)` (`GameApp.game_surface`), then `pygame.transform.smoothscale`s onto the real window once per frame in `_run_game_frame`. Existing `draw()` methods stay unchanged — they just get called with `game_surface` instead of `screen`.
- `Camera` is sized to the virtual surface, not the real window, so `camera.follow`/`clamp` math is entirely in virtual-surface space.
- Mouse position is scaled from real-window pixels to virtual-surface pixels (`GameApp._mouse_virtual_pos`) before any world-coordinate math, so platform placement still lines up with the cursor regardless of zoom.
- `CAMERA_ZOOM = 0.6` (settings.py) — zoomed IN, not out: the virtual surface is smaller than the world (which is exactly screen-sized), so the camera now has real room to scroll/follow the player for the first time, and sprites/platforms read bigger. (Zooming OUT, `CAMERA_ZOOM > 1.0`, would still need a taller background to avoid revealing empty space past its edges — that part of the original plan still holds; zooming in doesn't have that problem since it only crops into the existing background, never beyond it.)
- Top-right vertical bar HUD (`effects.draw_minimap`, called from `GameApp._draw`): player (blue dot), cop (red dot), goal (gold diamond), each mapped from world y to a position along the bar via `world_h`. It only tracks height, not x — this is a vertical climb, so height is the whole notion of "progress." Now that the camera is actually zoomed in (you can't see the whole field at once anymore), this is doing real work instead of being mostly redundant.
- **Fixed: couldn't build while moving/jumping.** Confirmed via debug output from the user's real machine: every successfully-logged click showed `player.vx=0.0` (never while genuinely moving), and attempts made while actually holding a movement key produced no event at all — not a lag/stall (frame `dt` stayed normal), the discrete `MOUSEBUTTONDOWN` event simply never arrived in that state, even though continuous key-state polling for movement was completely unaffected. Root cause is presumably an SDL/Windows-level event-delivery quirk specific to that input combination, not reproducible in headless testing. Fix: mouse clicks are now detected via continuous state polling (`pygame.mouse.get_pressed()`, edge-detected against the previous frame's state in `GameApp._prev_mouse_buttons`) instead of the `MOUSEBUTTONDOWN` event — mirroring the same continuous-polling approach movement already reliably used. Sidesteps the event-delivery issue entirely rather than chasing its exact SDL-level cause.
- **Mouse lookahead — tried, then reverted.** Once the camera stopped showing the whole field, standing still to aim a platform meant you couldn't see past the current view (camera only followed player position). A mouse-driven lookahead was added (nudging the camera toward wherever the mouse pointed) to address that, but the user asked for it to be reverted — they wanted the camera fully decoupled from the mouse and predictable, purely player-driven, even though that brings back the "can't see past the current view while idle" tradeoff. `camera.follow(self.player.rect.centerx, self.player.rect.centery)` — no mouse term at all.

### Two-font system (readability fix, post-Step-13)

`Star Crush.ttf` is missing 6 ASCII glyphs: `! , - . _ ?` — confirmed by checking every printable character against the font directly. That's a real problem since `.` is in every timer/score, `-` is in hints and tab labels, and `!` is in both win/lose titles ("PHOTO CAPTURED!", "THE COP CAUGHT YOU!"). Fix: `utils.get_readable_font(size)` (pygame's built-in default font, full glyph coverage) now handles everything except a small set of short, pure-word screen titles that stay on `utils.get_font(size)` (Star Crush): `"CURSUS COLOSSEI"`, `"ENTER YOUR NAME"`, `"SELECT DIFFICULTY"`, `"SCOREBOARD"`, `"SCOUT THE COLOSSEUM"`. Everything else — HUD text, hints, controls, the typed player name, score lines, and even the win/caught titles despite being "titles" (they contain `!`) — uses `get_readable_font`, since a broken glyph in the two biggest moments in the game would be worse than losing the decorative font there.

### Live platform-building (replaces the old "fixed level" idea)

- `level.py` only defines the floor, spawn, and a fixed goal position near the world's top.
- Placing/removing platforms (left click / right click, `[`/`]` width, numpad `-`/`+` height) is always active during gameplay — no toggle, no pause. This is the core climbing mechanic, not a hidden dev tool.
- Unlimited placement — no cooldown or cap. The cop's speed/pressure is the difficulty lever, not platform scarcity.

### Scoring — per-difficulty leaderboard

- Each entry: `{"name": str, "time": float, "difficulty": "easy"|"medium"|"hard"}`, all stored together in one `scores.json`.
- `add_score(player_name, time_seconds, difficulty)` groups all scores by difficulty and trims each group to its own top 10 independently, then saves the recombined list.
- `load_scores_by_difficulty(difficulty)` returns just one bucket, fastest first — what the scoreboard screen actually reads from.
- Scoreboard screen (`run_scoreboard`) is tabbed: 1/2/3 switches EASY/MEDIUM/HARD live, active tab highlighted in yellow, no need to leave the screen. Opens on `initial_difficulty` (the difficulty just played, passed in from `GameApp.difficulty`) rather than always defaulting to one tab.

### Supabase leaderboard (Step 14)

The local per-difficulty leaderboard above is untouched and still the reliable baseline — Supabase is an added, best-effort online layer on top of it, not a replacement. If the network is down or Supabase is misconfigured, the game keeps working exactly as it did before this step.

- **Table**: `scores` (`id`, `name`, `time`, `difficulty`, `created_at`), Row Level Security enabled with two policies — anyone can `select` and `insert`, nobody can `update`/`delete` through the API. Table-level `grant select, insert ... to anon` was also needed (RLS policies alone aren't enough — the SQL Editor doesn't auto-grant the way the Table Editor UI does).
- **Credentials**: `SUPABASE_URL` / `SUPABASE_ANON_KEY` live directly in `settings.py` as plain constants, same as every other config value in this project — not a `.env` file. The anon key is *meant* to be public (that's what the RLS policies are for); a `.env` also wouldn't actually protect a statically-hosted itch.io web build anyway, since whatever's baked in at `pygbag --build` time is what ships.
- **`scores.py` additions**: `add_score_online(name, time, difficulty)` and `load_scores_online_by_difficulty(difficulty, limit=10)`, both `async`. Branches on `sys.platform == "emscripten"` exactly like `audio.py` already does:
  - **Desktop**: plain stdlib `urllib.request` calls to Supabase's PostgREST REST API, run via `loop.run_in_executor(None, ...)` so the blocking network call happens on a worker thread instead of stalling the game loop.
  - **Web**: browser sockets don't exist, so this uses the same `platform.window.eval(...)` JS-injection technique `audio.py` already relies on for web playback — a small JS snippet exposes `window.SupabaseFetch.GET/POST` (using the browser's native Fetch API with the right headers), awaited from Python via pygbag's `platform.jsiter(...)` bridge. This mirrors a pattern pygbag ships internally for the same purpose.
  - Both directions fail soft: `add_score_online` returns `False`, `load_scores_online_by_difficulty` returns `None` (not `[]`, so "no scores yet" can be told apart from "couldn't reach Supabase") — never raises.
- **Win integration** (`app.py`): after the unconditional local `add_score(...)` call, `asyncio.ensure_future(add_score_online(...))` fires the online sync in the background — the win screen appears instantly regardless of network speed.
- **Scoreboard integration** (`screens.py`): `run_scoreboard` seeds instantly from local data (no network wait), kicks off a background fetch (`asyncio.ensure_future`), and swaps in the online result once it resolves — showing a small "syncing online leaderboard..." hint in the meantime. Switching tabs (1/2/3) re-seeds from local and restarts the fetch for the new tab.
- **Verification status**: desktop path fully tested end-to-end against the live Supabase project (real submit, real fetch, confirmed fail-soft when unreachable, confirmed the win frame stays fast/non-blocking). Web path is implemented but **not yet verified in an actual browser** — the dev environment this was built in can't run one; test it once you have a real pygbag web build running (see Step 13).

### Jump-pose sprites (Step 13)

- 4th animation pose for both `Player` and `Cop`: `player_jump_left/right.png`, `cop_jump_left/right.png`. Shown whenever `not on_ground` (covers both rising and falling — there's only one pose per direction, no separate fall pose). For the cop, an in-progress cheat hop also shows the jump pose, since a hop reads visually as a leap toward the player.
- Falls back to the run sprite if the jump image is ever missing (unlike the 3 base poses, which still hard-fail the whole game if missing) — an added-on pose isn't something the game was originally built to require.

### Web build gotchas (found verifying Step 13, worth remembering)

- **pygbag validates every file under `assets/`, not just what the code loads.** A leftover source mp3 (kept around after converting to `theme_music.ogg`) made the whole build fail with "unsupported format," even though nothing in the game ever loads it.
- **pygbag's `pygbag.ini` parser hard-rejects any `ignorefiles`/`ignoredirs` entry containing a space** — so a space-containing filename can't be excluded by listing it directly; it has to live in an excluded *directory* instead.
- **Real asset filenames with spaces also break the actual packer**, not just the ignore-list parser — this is what "renaming assets" should have already covered, but the jump-pose sprites were added later (Step 13) and still had their original spaced names (`jumping left.png`, `Cop Jumping left.png`, etc.) until this step renamed them to match the project's existing snake_case convention.
- **Fix applied:** renamed the 4 jump sprites to snake_case (load-bearing, code needed the new names); moved the remaining unused/source files that still have spaces in their names (`SAMBA TEMPERADO 2015.mp3`, `Star Crush.otf`, `standing still right.png`, `1001fonts-star-crush-eula.txt`) into a new `assets/unused/` subfolder, excluded wholesale via `pygbag.ini`'s `ignoredirs`.

---

## Assets (in `assets/`, real art as of this step)

- `background.png`, `first_screen.png`, `menu_background.png`, `scoreboard_background.png`, `final_background.png` — see `assets/README.md` for what each is used for.
- Player sprite set (tourist/photographer): `player_idle.png`, `player_run_left/right.png`, `player_jump_left/right.png`.
- Cop sprite set: `cop_idle.png`, `cop_run_left/right.png`, `cop_jump_left/right.png`.
- Font (`Star Crush.ttf`) and background music (`theme_music.ogg`, converted from mp3 at 44100 Hz) are in. Optional `siren.ogg` / `camera_shutter.ogg` stingers were considered and explicitly skipped — user decided not to add them, so Step 13 doesn't need to wait on any more audio assets.
- `assets/unused/` holds files that exist for reference but aren't loaded by the game and (in the mp3's case) would actively break the web build if left in `assets/` directly — see `assets/README.md`.
- Sitting unused for now (see `assets/README.md`): jump-pose sprites (deferred to Step 13 polish), a duplicate idle image.
