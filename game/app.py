from __future__ import annotations
import asyncio
import os
import pygame
from typing import List, Optional
from .audio import init_audio, play_music

#Import the configuration/constants from settings.py
from .settings import (
    SCREEN_W, SCREEN_H, FPS, MAX_DT, ASSETS_DIR,
    BACKGROUND_FILE,
    DEFAULT_PLAT_W, DEFAULT_PLAT_H,
    STATE_SPLASH, STATE_MENU, STATE_NAME, STATE_DIFFICULTY, STATE_MAP_PREVIEW,
    STATE_SCOREBOARD, STATE_GAME, STATE_WIN,
    DIFFICULTY_MEDIUM,
    WINDOW_TITLE, CAMERA_ZOOM,
    PLATFORM_BREAK_COLOR, PLATFORM_BREAK_DURATION,
)
#Import the helper functions + game systems from other python modules
from .utils import safe_load_image, get_readable_font, format_time
from .scores import add_score, add_score_online
from .effects import draw_goal_glow, draw_minimap
from .camera import Camera
from .platform import Platform
from .player import Player
from .cop import Cop, get_spawn_position as get_cop_spawn_position
from .level import build_platforms, get_spawn, get_goal_rect
from .screens import (
    run_splash, run_menu, run_name_input, run_scoreboard,
    run_map_preview, run_difficulty_select, run_win_screen,
)


def load_background_world() -> pygame.Surface:
    """
    Loads the gameplay background image from the assets folder.
    This background image also defines the "world size" because we use its
    width and height to set the world boundaries for the camera and player.
    """
    path = os.path.join(ASSETS_DIR, BACKGROUND_FILE)
    img = safe_load_image(path, convert_alpha=False)
    #If the image is missing, we raise an error (the game cannot run without a world background)
    if img is None:
        raise FileNotFoundError(f"Background not found at: {path}")
    return img

#Main application class that owns the whole game system.
class GameApp:
    """
    This class keps track of:
    - pygame initialization + window creation
    - game state (menu, name input, scoreboard, gameplay)
    - main loop and per-frame updates
    - drawing everything on screen
    """
    def __init__(self) -> None:
        # pre_init must run before pygame.init() so the mixer is configured
        # with 44100 Hz before the WASM audio context is created.
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(WINDOW_TITLE)
        #Gameplay is rendered onto this off-screen "virtual" surface, then
        #smoothscaled up to fill the real window (Step 9). At CAMERA_ZOOM=1.0
        #the two are the same size, so this is currently a no-op scale — the
        #pipeline is ready for whenever CAMERA_ZOOM > 1.0 is used to zoom out.
        self.virtual_w = int(SCREEN_W * CAMERA_ZOOM)
        self.virtual_h = int(SCREEN_H * CAMERA_ZOOM)
        self.game_surface = pygame.Surface((self.virtual_w, self.virtual_h))
        init_audio()
        # Music is started later, after the first user interaction (splash screen),
        # to satisfy Chrome's autoplay policy and prevent glitchy/blocked audio.
        #Used to control FPS and compute delta time (dt)
        self.clock = pygame.time.Clock()
        #Fonts used during the game (HUD + editor overlay)
        self.font_hud = get_readable_font(42)
        self.font_editor = get_readable_font(32)
        #Load background and define the world size based on the image dimensions
        self.background = load_background_world()
        self.world_w, self.world_h = self.background.get_width(), self.background.get_height()
        #Camera converts world coordinates -> virtual-surface coordinates (important
        #for scrolling). It's sized to the virtual surface, not the real window,
        #so "screen" here means the camera's own render target pre-smoothscale.
        self.camera = Camera(self.virtual_w, self.virtual_h, self.world_w, self.world_h)
        #Spawn position where the player starts
        self.spawn_x, self.spawn_y = get_spawn(self.world_w, self.world_h)
        #Level data: starts as just the floor — climbing this game means
        #building your own platforms live as you go (core mechanic, not a
        #hidden dev tool), so there's nothing else to pre-author here
        self.platforms: List[Platform] = build_platforms(self.world_w, self.world_h)
        #Goal collision area (goal is drawn as a glow, but collision is a Rect)
        self.goal_rect = get_goal_rect(self.world_w, self.world_h)
        #Size of the next platform the player places (adjustable with [ ]/-+)
        self.plat_w = DEFAULT_PLAT_W
        self.plat_h = DEFAULT_PLAT_H
        #Global game state
        self.state = STATE_SPLASH
        self.player_name = "Unknown"
        #Difficulty chosen on the difficulty-select screen; tunes the Cop AI (Step 7)
        #and picks the leaderboard bucket a finished run is saved to (Step 12)
        self.difficulty = DIFFICULTY_MEDIUM
        self.win = False
        #True once the cop catches the player — a separate flag from win,
        #since a run can only end one way or the other
        self.caught = False
        #Timing variables
        self.run_start_ms: Optional[int] = None
        self.final_time_s: Optional[float] = None
        #Create the Player object
        self.player = Player(self.spawn_x, self.spawn_y)
        #Create the Cop object, spawned behind the player by a difficulty-dependent gap
        cop_x, cop_y = get_cop_spawn_position((self.spawn_x, self.spawn_y), self.difficulty)
        self.cop = Cop(cop_x, cop_y, self.difficulty)
        #Brief visual flashes marking where the cop just destroyed a platform
        #(its last-resort fallback) — each entry is [world Rect, seconds left]
        self.break_effects: List[List] = []

    def reset_run(self, clear_platforms: bool) -> None:
        """
        Resets the current run (timer + player + cop position).
        If clear_platforms is True, it also clears every platform the player
        has built this run, back down to just the floor.
        """
        self.win = False
        self.caught = False
        self.run_start_ms = pygame.time.get_ticks()
        self.final_time_s = None
        self.player.reset(self.spawn_x, self.spawn_y)
        #Cop position/tuning are reapplied here too, since the difficulty may
        #have changed since the last run (fresh difficulty-select choice)
        cop_x, cop_y = get_cop_spawn_position((self.spawn_x, self.spawn_y), self.difficulty)
        self.cop.reset(cop_x, cop_y, self.difficulty)
        self.break_effects = []
        if clear_platforms:
            self.platforms = build_platforms(self.world_w, self.world_h)

    def _mouse_virtual_pos(self) -> tuple[int, int]:
        """
        Mouse position from pygame is in real-window pixels, but gameplay is
        drawn on the (possibly differently-sized) virtual surface. Scale the
        raw mouse position into virtual-surface space before feeding it to
        the camera, so platform placement lines up with the cursor.
        """
        mx, my = pygame.mouse.get_pos()
        return int(mx * CAMERA_ZOOM), int(my * CAMERA_ZOOM)

    async def run(self) -> None:
        """
        Main application loop (async for Pygbag/browser compatibility).
        This loop does not run gameplay directly. Instead, it delegates to the correct
        screen/state (menu, name input, scoreboard, gameplay).
        """
        music_started = False
        while True:
            #Splash screen state
            if self.state == STATE_SPLASH:
                next_state = await run_splash(self.screen, self.clock)
                if next_state == "quit":
                    break
                self.state = next_state
                # Start music on the first user interaction (satisfies Chrome autoplay policy)
                if not music_started:
                    play_music()
                    music_started = True
            #Menu state
            elif self.state == STATE_MENU:
                next_state = await run_menu(self.screen, self.clock)
                if next_state == "quit":
                    break
                self.state = next_state
            #Name input state
            elif self.state == STATE_NAME:
                name = await run_name_input(self.screen, self.clock)
                if name is None:
                    self.state = STATE_MENU
                else:
                    self.player_name = name
                    self.state = STATE_DIFFICULTY
            #Difficulty-select state — Easy/Medium/Hard, tunes the Cop AI (Step 7)
            #and the leaderboard bucket a finished run gets saved to (Step 12)
            elif self.state == STATE_DIFFICULTY:
                difficulty = await run_difficulty_select(self.screen, self.clock)
                if difficulty == "quit":
                    break
                if difficulty is None:
                    self.state = STATE_MENU
                else:
                    self.difficulty = difficulty
                    self.state = STATE_MAP_PREVIEW
            #Map preview state — shown before the run timer starts, so the player
            #knows their spawn and goal before the cop starts chasing
            elif self.state == STATE_MAP_PREVIEW:
                next_state = await run_map_preview(
                    self.screen, self.clock, self.background,
                    (self.spawn_x, self.spawn_y), self.goal_rect,
                )
                if next_state == "quit":
                    break
                if next_state == STATE_GAME:
                    #Timer/run only actually starts once the player leaves the map preview
                    self.reset_run(clear_platforms=True)
                self.state = next_state
            #Scoreboard state
            elif self.state == STATE_SCOREBOARD:
                next_state = await run_scoreboard(self.screen, self.clock, self.difficulty)
                if next_state == "quit":
                    break
                self.state = next_state
            #Win state — dedicated full-screen "photo captured" moment (Step 11),
            #reached once a run's win condition finalizes in _run_game_frame()
            elif self.state == STATE_WIN:
                next_state = await run_win_screen(
                    self.screen, self.clock, self.player_name, self.final_time_s or 0.0,
                )
                if next_state == "quit":
                    break
                if next_state == "restart":
                    self.reset_run(clear_platforms=True)
                    self.state = STATE_GAME
                else:
                    self.state = next_state
            #GAMEPLAY state — runs one frame then yields to the browser
            elif self.state == STATE_GAME:
                self._run_game_frame()
                await asyncio.sleep(0)
        #If we escape this loop, pygame will quit
        pygame.quit()
    #runs one frame of gameplay
    def _run_game_frame(self) -> None:
        """
        - handle events
        - update player physics
        - update camera
        - draw everything
        """
        #dt = delta time (seconds per frame). This keeps movement stable across FPS changes.
        #Capped at MAX_DT so a real frame hitch can't cause a single huge
        #physics step (see settings.py for why that's dangerous here).
        dt = min(self.clock.tick(FPS) / 1000.0, MAX_DT)
        #If timer hasn't started yet, start it now
        if self.run_start_ms is None:
            self.run_start_ms = pygame.time.get_ticks()
        #Keyboard + mouse event handling
        for event in pygame.event.get():
            #close window
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            #keyboard presses
            if event.type == pygame.KEYDOWN:
                #Clicking R will restart the platforms
                if event.key == pygame.K_r:
                    self.reset_run(clear_platforms=True)
                #Clicking ESC will go back to menu page
                if event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU
                #Building platforms is always available (not a toggle) —
                #it IS the core way you climb here. [ ] adjusts width,
                #-/+ on the numpad adjusts height of the NEXT platform placed
                if event.key == pygame.K_LEFTBRACKET:
                    self.plat_w = max(40, self.plat_w - 20)
                if event.key == pygame.K_RIGHTBRACKET:
                    self.plat_w = min(600, self.plat_w + 20)
                if event.key == pygame.K_KP_MINUS:
                    self.plat_h = max(8, self.plat_h - 4)
                if event.key == pygame.K_KP_PLUS:
                    self.plat_h = min(80, self.plat_h + 4)
            #Mouse clicks place/remove platforms — live, while still running
            #and being chased, no pause
            if event.type == pygame.MOUSEBUTTONDOWN:
                #convert our mouse position (screen -> virtual surface -> world) using camera offsets
                mx, my = self._mouse_virtual_pos()
                wx = mx + self.camera.offset_x
                wy = my + self.camera.offset_y
                #Left click will add a platform centered on the mouse
                if event.button == 1:
                    x = int(wx - self.plat_w / 2)
                    y = int(wy - self.plat_h / 2)
                    self.platforms.append(Platform(x, y, self.plat_w, self.plat_h))
                #Right click will remove the nearest platform (but never remove the base floor)
                if event.button == 3 and len(self.platforms) > 1:
                    def dist2(p: Platform):
                        cx, cy = p.rect.center
                        return (cx - wx) ** 2 + (cy - wy) ** 2
                    nearest = min(self.platforms[1:], key=dist2)
                    self.platforms.remove(nearest)
        #GAmeplay updates
        keys = pygame.key.get_pressed()
        #Update the physics if the run hasn't ended yet (win or caught)
        if not self.win and not self.caught:
            self.player.handle_input(keys)
            self.player.try_jump(keys)
            self.player.move_and_collide(dt, self.platforms)
            self.player.clamp_to_world_x(self.world_w)

            self.cop.ai_steer(dt, self.player.rect)
            self.cop.ai_try_jump(self.player.rect, self.platforms)
            #If the cop just used its last-resort fallback and destroyed a
            #platform, spawn a brief visual flash where it used to be
            if self.cop.last_broken_platform_rect is not None:
                self.break_effects.append([self.cop.last_broken_platform_rect, PLATFORM_BREAK_DURATION])
            self.cop.move_and_collide(dt, self.platforms)
            self.cop.clamp_to_world_x(self.world_w)

            #Age out break-effect flashes, dropping any that have fully faded
            for effect in self.break_effects:
                effect[1] -= dt
            self.break_effects = [e for e in self.break_effects if e[1] > 0]

            #Win condition takes priority if both happen to trigger the same
            #frame — benefit of the doubt to the player
            if self.player.rect.colliderect(self.goal_rect):
                self.win = True
                self.player.vx = 0.0
                self.player.vy = 0.0
                #Save final time and then add it to the scoreboard (once)
                if self.run_start_ms is not None and self.final_time_s is None:
                    elapsed_ms = pygame.time.get_ticks() - self.run_start_ms
                    self.final_time_s = elapsed_ms / 1000.0
                    #Local save always happens first and is never affected by
                    #network conditions — the run's result is never lost.
                    add_score(self.player_name, self.final_time_s, self.difficulty)
                    #Best-effort sync to the shared Supabase leaderboard, fired
                    #off in the background so a slow/dead connection can never
                    #stall the moment of winning (see scores.add_score_online)
                    asyncio.ensure_future(
                        add_score_online(self.player_name, self.final_time_s, self.difficulty)
                    )
                #Hand off to the dedicated win screen (Step 11) instead of
                #lingering in gameplay with a small overlay
                self.state = STATE_WIN
            #Lose condition: the cop caught the player
            elif self.cop.rect.colliderect(self.player.rect):
                self.caught = True
                self.player.vx = 0.0
                self.player.vy = 0.0
                #Freeze the HUD timer here too — no score is saved on a loss,
                #but final_time_s is what stops the timer from still ticking
                if self.run_start_ms is not None and self.final_time_s is None:
                    elapsed_ms = pygame.time.get_ticks() - self.run_start_ms
                    self.final_time_s = elapsed_ms / 1000.0
        else:
            #Once the run is finished, freeze the player movement
            self.player.vx = 0.0
            self.player.vy = 0.0
        #this is to prevent infinte falling or player disappearing or camera following the player
        #endlessly downward
        if self.player.rect.top > self.world_h + 400:
            self.reset_run(clear_platforms=False)
        #camera follows player center (world -> virtual-surface handled by camera.apply)
        self.camera.follow(self.player.rect.centerx, self.player.rect.centery)
        #draw everything for this frame onto the virtual surface
        self._draw()
        #Scale the virtual surface up to the real window and present it.
        #At CAMERA_ZOOM=1.0 this is a same-size scale (visually a no-op);
        #it's the seam where a future CAMERA_ZOOM > 1.0 does the actual zoom-out.
        pygame.transform.smoothscale(self.game_surface, (SCREEN_W, SCREEN_H), self.screen)
        #If the player got caught, grant "S" shortcut to check out the scores.
        #(A win no longer lingers in STATE_GAME — it hands off to STATE_WIN
        #above, which has its own S-to-scoreboard handling in run_win_screen.)
        if self.caught:
            if pygame.key.get_pressed()[pygame.K_s]:
                self.state = STATE_SCOREBOARD

        pygame.display.flip()

    def _draw(self) -> None:
        """
        Draws the background, goal, platforms, player, HUD, and overlays onto
        the virtual surface (self.game_surface), which gets smoothscaled to
        the real window afterward in _run_game_frame. This method does NOT
        update physics, it only renders visuals.
        """
        surface = self.game_surface
        #Draw world background using camera offsets (creates a scrolling effect)
        surface.blit(self.background, (-self.camera.offset_x, -self.camera.offset_y))
        #Draw a spawn circle marker
        sx, sy = self.camera.apply(self.spawn_x, self.spawn_y)
        pygame.draw.circle(surface, (255, 165, 0), (sx, sy), 6)
        #Draw goal glow effect (visual circle) at the goal's center
        gx, gy = self.camera.apply(self.goal_rect.centerx, self.goal_rect.centery)
        draw_goal_glow(surface, (gx, gy))

        #Ghost/preview of the next platform's size at the mouse position —
        #always shown, since placing platforms is the core way you climb
        mx, my = self._mouse_virtual_pos()
        wx = mx + self.camera.offset_x
        wy = my + self.camera.offset_y

        ghost_x = int(wx - self.plat_w / 2)
        ghost_y = int(wy - self.plat_h / 2)
        gx2, gy2 = self.camera.apply(ghost_x, ghost_y)
        ghost_rect = pygame.Rect(gx2, gy2, self.plat_w, self.plat_h)

        ghost_r = max(2, self.plat_h // 2)
        pygame.draw.rect(surface, (150, 200, 255), ghost_rect, 2, border_radius=ghost_r)
        #control hint, always visible during gameplay
        hud = self.font_editor.render(
            "[ ] width | -/+ height | LMB add | RMB remove | R restart",
            True,
            (0, 0, 0),)
        surface.blit(hud, (20, 20))
        #Draw platforms
        for p in self.platforms:
            p.draw(surface, self.camera)
        #Draw any in-progress "platform just broken by the cop" flashes —
        #a fading red rect with a crack mark where it used to be, so the
        #cop's last-resort fallback reads as a visible, fair event
        for rect, remaining in self.break_effects:
            alpha = max(0, min(255, int(255 * (remaining / PLATFORM_BREAK_DURATION))))
            bx, by = self.camera.apply(rect.x, rect.y)
            flash = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            flash.fill((*PLATFORM_BREAK_COLOR, alpha))
            pygame.draw.line(flash, (255, 255, 255, alpha), (0, 0), (rect.w, rect.h), 3)
            pygame.draw.line(flash, (255, 255, 255, alpha), (rect.w, 0), (0, rect.h), 3)
            surface.blit(flash, (bx, by))
        #Draw the player and the cop chasing them
        self.player.draw(surface, self.camera)
        self.cop.draw(surface, self.camera)

        #HUD : player name + timer
        if self.run_start_ms is not None and self.final_time_s is None:
            elapsed_s = (pygame.time.get_ticks() - self.run_start_ms) / 1000.0
            timer_text = format_time(elapsed_s)
        elif self.final_time_s is not None:
            timer_text = format_time(self.final_time_s)
        else:
            timer_text = "00:00.00"

        hud_name = self.font_hud.render(f"PLAYER: {self.player_name}", True, (0, 0, 0))
        hud_time = self.font_hud.render(f"TIME: {timer_text}", True, (0, 0, 0))
        surface.blit(hud_name, (20, 70))
        surface.blit(hud_time, (20, 120))

        #Minimap HUD (top-right): shows player/cop height relative to the goal
        draw_minimap(
            surface, self.virtual_w, self.world_h,
            self.player.rect.centery, self.cop.rect.centery, self.goal_rect.centery,
        )

        #Caught overlay — the win side of this got promoted to a dedicated
        #full-screen moment (run_win_screen, Step 11) since real art landed
        #for it, but the plan keeps this one as an in-place overlay: there's
        #no dedicated "caught" background art, so this stays the lose-state
        #visual language (black box, red accent border).
        if self.caught:
            big = get_readable_font(84)
            small = get_readable_font(44)

            msg1 = big.render("THE COP CAUGHT YOU!", True, (255, 255, 255))
            msg2 = small.render(f"CAUGHT AFTER: {format_time(self.final_time_s or 0.0)}", True, (255, 255, 255))
            msg3 = small.render("R RESTART (CLEARS PLATFORMS) | ESC MENU | S SCOREBOARD", True, (255, 255, 255))
            box_w = max(msg1.get_width(), msg2.get_width(), msg3.get_width()) + 80
            box_h = msg1.get_height() + msg2.get_height() + msg3.get_height() + 80
            box_x = (self.virtual_w - box_w) // 2
            box_y = (self.virtual_h - box_h) // 2
            pygame.draw.rect(surface, (0, 0, 0), pygame.Rect(box_x, box_y, box_w, box_h))
            pygame.draw.rect(surface, (200, 50, 50), pygame.Rect(box_x, box_y, box_w, box_h), 2)
            surface.blit(msg1, (box_x + 40, box_y + 25))
            surface.blit(msg2, (box_x + 40, box_y + 25 + msg1.get_height() + 15))
            surface.blit(msg3, (box_x + 40, box_y + 25 + msg1.get_height() + msg2.get_height() + 30))
