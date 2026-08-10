from __future__ import annotations
import asyncio
import os
import pygame
from typing import List, Optional
from .audio import init_audio, play_music

#Import the configuration/constants from settings.py
from .settings import (
    SCREEN_W, SCREEN_H, FPS, ASSETS_DIR,
    BACKGROUND_FILE,
    DEFAULT_PLAT_W, DEFAULT_PLAT_H,
    STATE_SPLASH, STATE_MENU, STATE_NAME, STATE_MAP_PREVIEW, STATE_SCOREBOARD, STATE_GAME,
    WINDOW_TITLE,
)
#Import the helper functions + game systems from other python modules
from .utils import safe_load_image, get_font, format_time
from .scores import add_score
from .effects import draw_goal_glow
from .camera import Camera
from .platform import Platform
from .player import Player
from .level import build_platforms, get_spawn, get_goal_rect
from .screens import run_splash, run_menu, run_name_input, run_scoreboard, run_map_preview


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
        init_audio()
        # Music is started later, after the first user interaction (splash screen),
        # to satisfy Chrome's autoplay policy and prevent glitchy/blocked audio.
        #Used to control FPS and compute delta time (dt)
        self.clock = pygame.time.Clock()
        #Fonts used during the game (HUD + editor overlay)
        self.font_hud = get_font(42)
        self.font_editor = get_font(32)
        #Load background and define the world size based on the image dimensions
        self.background = load_background_world()
        self.world_w, self.world_h = self.background.get_width(), self.background.get_height()
        #Camera converts world coordinates -> screen coordinates (important for scrolling)
        self.camera = Camera(SCREEN_W, SCREEN_H, self.world_w, self.world_h)
        #Spawn position where the player starts (fixed level, see level.py)
        self.spawn_x, self.spawn_y = get_spawn(self.world_w, self.world_h)
        #Level data: the fixed, hand-authored Colosseum platform layout
        self.platforms: List[Platform] = build_platforms(self.world_w, self.world_h)
        #Goal collision area (goal is drawn as a glow, but collision is a Rect)
        self.goal_rect = get_goal_rect(self.world_w, self.world_h)
        #Editor mode settings — hidden dev tool for tuning the fixed layout above,
        #gated behind DEV_TOOLS_ENABLED (see settings.py)
        self.editor_mode = False
        self.plat_w = DEFAULT_PLAT_W
        self.plat_h = DEFAULT_PLAT_H
        #Global game state
        self.state = STATE_SPLASH
        self.player_name = "Unknown"
        self.win = False
        #Timing variables
        self.run_start_ms: Optional[int] = None
        self.final_time_s: Optional[float] = None
        #Create the Player object
        self.player = Player(self.spawn_x, self.spawn_y)

    def reset_run(self, clear_platforms: bool) -> None:
        """
        Resets the current run (timer + player position).
        If clear_platforms is True, it also resets the level back to the fixed
        Colosseum layout — this discards any temporary edits made in the hidden
        editor dev tool, so tuning always starts from the shipped layout.
        """
        self.win = False
        self.run_start_ms = pygame.time.get_ticks()
        self.final_time_s = None
        self.player.reset(self.spawn_x, self.spawn_y)
        if clear_platforms:
            self.platforms = build_platforms(self.world_w, self.world_h)

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
                    self.state = STATE_MAP_PREVIEW
            #Map preview state — shown before the run timer starts, so the player
            #can plan their route up the fixed Colosseum layout
            elif self.state == STATE_MAP_PREVIEW:
                next_state = await run_map_preview(
                    self.screen, self.clock, self.background,
                    self.platforms, (self.spawn_x, self.spawn_y), self.goal_rect,
                )
                if next_state == "quit":
                    break
                if next_state == STATE_GAME:
                    #Timer/run only actually starts once the player leaves the map preview
                    self.reset_run(clear_platforms=True)
                self.state = next_state
            #Scoreboard state
            elif self.state == STATE_SCOREBOARD:
                next_state = await run_scoreboard(self.screen, self.clock)
                if next_state == "quit":
                    break
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
        dt = self.clock.tick(FPS) / 1000.0
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
                #Clicking E will go in builder/editor mode — used to tune the
                #fixed Colosseum layout in level.py by hand
                if event.key == pygame.K_e:
                    self.editor_mode = not self.editor_mode
                #When in builder/editor mode
                if self.editor_mode:
                    #Control the width of the platfrom with []
                    if event.key == pygame.K_LEFTBRACKET:
                        self.plat_w = max(40, self.plat_w - 20)
                    if event.key == pygame.K_RIGHTBRACKET:
                        self.plat_w = min(600, self.plat_w + 20)
                    #Control the height of the platform with - and + from the numeric keypad
                    if event.key == pygame.K_KP_MINUS:
                        self.plat_h = max(8, self.plat_h - 4)
                    if event.key == pygame.K_KP_PLUS:
                        self.plat_h = min(80, self.plat_h + 4)
            #Mouse clicks while in editor mode
            if event.type == pygame.MOUSEBUTTONDOWN and self.editor_mode:
                #convert our mouse position (screen) into world coordinates using camera offstes
                mx, my = pygame.mouse.get_pos()
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
        #Update the physics if we're not editing and haven't wont yet
        if not self.editor_mode and not self.win:
            self.player.handle_input(keys)
            self.player.try_jump(keys)
            self.player.move_and_collide(dt, self.platforms)
            self.player.clamp_to_world_x(self.world_w)
            #Win condition here, if only the player collides with the goal area
            if self.player.rect.colliderect(self.goal_rect):
                self.win = True
                self.player.vx = 0.0
                self.player.vy = 0.0
                #Save final time and then add it to the scoreboard (once)
                if self.run_start_ms is not None and self.final_time_s is None:
                    elapsed_ms = pygame.time.get_ticks() - self.run_start_ms
                    self.final_time_s = elapsed_ms / 1000.0
                    add_score(self.player_name, self.final_time_s)
        else:
            #If we're editing or the run is finished, we will freeze the player movement
            self.player.vx = 0.0
            self.player.vy = 0.0
        #this is to prevent infinte falling or player disappearing or camera following the player
        #endlessly downward
        if self.player.rect.top > self.world_h + 400:
            self.reset_run(clear_platforms=False)
        #camera follows player center (world -> screen handled by camera.apply)
        self.camera.follow(self.player.rect.centerx, self.player.rect.centery)
        #draw everything for this frame
        self._draw()
        #If player has won/finished the race, grant "S" shortcut to check out his scores and see with
        #the others how he did
        if self.win and self.final_time_s is not None:
            if pygame.key.get_pressed()[pygame.K_s]:
                self.state = STATE_SCOREBOARD

        pygame.display.flip()

    def _draw(self) -> None:
        """
        Draws the background, goal, platforms, player, HUD, and overlays.
        This method does NOT update physics, it only renders visuals.
        """
        #Draw world background using camera offsets (creates a scrolling effect)
        self.screen.blit(self.background, (-self.camera.offset_x, -self.camera.offset_y))
        #Draw a spawn circle marker
        sx, sy = self.camera.apply(self.spawn_x, self.spawn_y)
        pygame.draw.circle(self.screen, (255, 165, 0), (sx, sy), 6)
        #Draw goal glow effect (visual circle) at the goal's center
        gx, gy = self.camera.apply(self.goal_rect.centerx, self.goal_rect.centery)
        draw_goal_glow(self.screen, (gx, gy))

        #In editor mode, to help author the fixed level layout,
        #we will show a "ghost"/preview of the platform size at the mouse position
        if self.editor_mode:
            mx, my = pygame.mouse.get_pos()
            wx = mx + self.camera.offset_x
            wy = my + self.camera.offset_y

            ghost_x = int(wx - self.plat_w / 2)
            ghost_y = int(wy - self.plat_h / 2)
            gx2, gy2 = self.camera.apply(ghost_x, ghost_y)
            ghost_rect = pygame.Rect(gx2, gy2, self.plat_w, self.plat_h)

            ghost_r = max(2, self.plat_h // 2)
            pygame.draw.rect(self.screen, (150, 200, 255), ghost_rect, 2, border_radius=ghost_r)
            #display the possibilities in editor mode
            hud = self.font_editor.render(
                "EDITOR ON | [ ] width | -/+ height | LMB add | RMB remove | E toggle | R restart",
                True,
                (0, 0, 0),)
            self.screen.blit(hud, (20, 20))
        #Draw platforms
        for p in self.platforms:
            p.draw(self.screen, self.camera)
        #Draw the player
        self.player.draw(self.screen, self.camera)

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
        self.screen.blit(hud_name, (20, 70))
        self.screen.blit(hud_time, (20, 120))

        #Win overlay
        if self.win and self.final_time_s is not None:
            big = get_font(84)
            small = get_font(44)

            msg1 = big.render("PHOTO CAPTURED!", True, (255, 255, 255))
            msg2 = small.render(f"YOUR TIME: {format_time(self.final_time_s)}", True, (255, 255, 255))
            msg3 = small.render("R RESTART (CLEARS PLATFORMS) | ESC MENU | S SCOREBOARD", True, (255, 255, 255))
            #Create the winning message board with a centered back box behind the win message(msg1)
            box_w = max(msg1.get_width(), msg2.get_width(), msg3.get_width()) + 80
            box_h = msg1.get_height() + msg2.get_height() + msg3.get_height() + 80
            box_x = (SCREEN_W - box_w) // 2
            box_y = (SCREEN_H - box_h) // 2
            pygame.draw.rect(self.screen, (0, 0, 0), pygame.Rect(box_x, box_y, box_w, box_h))
            pygame.draw.rect(self.screen, (255, 255, 255), pygame.Rect(box_x, box_y, box_w, box_h), 2)
            #Draw the message inside the box
            self.screen.blit(msg1, (box_x + 40, box_y + 25))
            self.screen.blit(msg2, (box_x + 40, box_y + 25 + msg1.get_height() + 15))
            self.screen.blit(msg3, (box_x + 40, box_y + 25 + msg1.get_height() + msg2.get_height() + 30))
