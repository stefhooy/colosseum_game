from __future__ import annotations
import os
import pygame
from typing import List, Optional, Tuple
#Used for the collision detection
from .platform import Platform
#Used for the world gameplay (screen transformation)
from .camera import Camera
from .utils import safe_load_image, scale_to_target_height
from .settings import (
    ASSETS_DIR,
    PLAYER_W, PLAYER_H,
    SPRITE_TARGET_H,
    FEET_OFFSET_Y,
    COP_STILL_FILE,
    COP_RUN_RIGHT_FILE,
    COP_RUN_LEFT_FILE,
    COP_JUMP_RIGHT_FILE,
    COP_JUMP_LEFT_FILE,
    COP_SPEED_BY_DIFFICULTY,
    COP_REACTION_DELAY_BY_DIFFICULTY,
    COP_START_GAP_BY_DIFFICULTY,
    COP_HEADSTART_SECONDS,
    COP_BUILD_PATIENCE_BY_DIFFICULTY,
    COP_BREAK_PATIENCE_BY_DIFFICULTY,
    COP_BUILD_DURATION_BY_DIFFICULTY,
    COP_BUILD_PLAT_W, COP_BUILD_PLAT_H, COP_BUILD_RISE, MAX_COP_BUILDS,
)

#How far (in px) the player needs to be above the cop before it's worth
#trying to climb toward them at all
CLIMB_TOLERANCE = 12
#Dead zone so the cop doesn't jitter left/right once lined up with the player
STEER_DEADZONE = 6
#Minimum upward progress (px) that counts as "not stuck" — the cop tracks
#the best (smallest) centery it's reached; anything less than this much
#improvement resets nothing, and the stuck timer keeps climbing
PROGRESS_EPSILON = 20

#--- Nearest-reachable-platform preference ---
#Before building a new platform, the cop should prefer using one that's
#already there (the player's own, or one of its own from earlier) if it's
#genuinely within jump range — "follow your platforms or build his own,
#depending on the distance." Reach estimates come from real jump physics
#(jump_strength=650, gravity=1400): the full arc covers ~151px of rise, and
#at the SLOWEST cop speed (Easy, 180px/s) covers ~167px horizontally during
#the ~0.93s flight. Using the slowest speed keeps these safely reachable
#regardless of which difficulty is actually running.
JUMP_REACH_DX = 150
JUMP_REACH_DY = 145

#--- Stuck fallbacks: building (routine), breaking (rare last resort) ---
#Since the level has no fixed layout (the player builds their own platforms
#live), the cop can't rely on a precomputed path the way an early version of
#this AI did. Instead it always just heads toward wherever the player
#currently is, jumping normally when that's reachable.
#
#Two fallbacks kick in the longer the cop goes without real upward progress:
#1. BUILD (routine, see _build_platform_toward_player) — the cop places its
#   own stepping-stone platform, just like the player does. This is the
#   main way the cop keeps pace once the player starts building, matching
#   the request that the cop compete on the same terms rather than just
#   following — it's meant to happen regularly, not rarely.
#2. BREAK (rare last resort, see _break_nearest_platform) — if even
#   building doesn't get the cop unstuck for a long stretch, it destroys
#   the nearest player-built platform instead. An earlier version of this
#   AI used a "cheat hop" (teleporting toward the player) for this; player
#   feedback was that it felt overpowered even after toning the timing
#   down, so it was replaced with breaking, which is at least visible and
#   fair rather than magic. The floor itself (platforms[0]) can never be
#   broken, and this tier is now even rarer since building resolves most
#   stuck situations on its own.
#Safety caps so a pathological stall can't repeat forever — fail soft
MAX_PLATFORM_BREAKS = 100


def get_spawn_position(player_spawn: Tuple[int, int], difficulty: str) -> Tuple[int, int]:
    """
    The cop spawns on the same floor as the player, offset behind them by a
    difficulty-dependent head-start gap (bigger gap = easier for the player).
    """
    gap = COP_START_GAP_BY_DIFFICULTY[difficulty]
    x = max(0, player_spawn[0] - gap)
    return x, player_spawn[1]


#This class is the police officer chasing the player
class Cop:
    """
    Structurally mirrors Player — same rect-based hitbox, gravity/jump
    physics, two-pass move-and-collide, and idle/run-left/run-right sprite
    selection — but instead of reading the keyboard, an AI controller
    decides its movement each frame: always head toward the player's
    (reaction-delayed) position, jumping when they're above and there's
    ground to jump to.

    Unlike the player, the cop has two stuck fallbacks layered on top of
    real jumps: if it's stuck without real upward progress for a while, it
    builds its own stepping-stone platform (see _build_platform_toward_player)
    — a routine, competing-builder behavior, not a rare trick. If even that
    doesn't resolve things for a much longer stretch, it falls back further
    to destroying the nearest player-built platform (see
    _break_nearest_platform) so it's never permanently stuck. Real jumps are
    always tried first.
    """
    def __init__(self, x: int, y: int, difficulty: str):
        #cop collision rectangle used for physics and collisions (same size as the player)
        self.rect = pygame.Rect(x, y, PLAYER_W, PLAYER_H)
        #Physics variables — gravity/jump are identical to the player's
        self.vx = 0.0
        self.vy = 0.0
        self.gravity = 1400.0
        self.jump_strength = 650.0
        #Difficulty tuning — the only numbers that differ between Easy/Medium/Hard
        self.speed = COP_SPEED_BY_DIFFICULTY[difficulty]
        self.reaction_delay = COP_REACTION_DELAY_BY_DIFFICULTY[difficulty]
        self.build_patience = COP_BUILD_PATIENCE_BY_DIFFICULTY[difficulty]
        self.break_patience = COP_BREAK_PATIENCE_BY_DIFFICULTY[difficulty]
        self.build_duration = COP_BUILD_DURATION_BY_DIFFICULTY[difficulty]
        self.on_ground = False
        self.facing_right = True

        #Flat grace period at the very start of every run (all difficulties)
        #where the cop just stands still — see COP_HEADSTART_SECONDS
        self._headstart_timer = COP_HEADSTART_SECONDS

        #Simulates reaction lag: the AI only "sees" a fresh player position
        #once every reaction_delay seconds, instead of instantly every frame
        self._reaction_timer = 0.0
        self._known_player_x = x
        #Tracks the best (smallest) centery reached, and how long it's been
        #stuck without meaningfully improving on that — drives both the
        #build and break fallbacks in ai_try_jump
        self._best_centery = float(self.rect.centery)
        self._stuck_timer = 0.0
        #Lifetime counts this run, capped defensively so a pathological
        #stall can't repeat forever
        self._platforms_built = 0
        self._platforms_broken = 0
        #While True, the cop is frozen in place actually constructing the
        #platform it decided to build — see _start_building/move_and_collide.
        #Takes build_duration seconds, tunable per difficulty (see
        #COP_BUILD_DURATION_BY_DIFFICULTY): a real, visible "how fast the
        #cop builds" difference, not just how soon it decides to.
        self._is_building = False
        self._building_timer = 0.0
        self._build_target_x = 0
        self._build_target_y = 0
        #Set to the rect of whatever platform was just destroyed, for one
        #frame only — GameApp reads this right after calling ai_try_jump to
        #spawn a visual "break" effect, then it's cleared again next call
        self.last_broken_platform_rect: Optional[pygame.Rect] = None

        #Build the file paths for the cop's sprites
        still_path = os.path.join(ASSETS_DIR, COP_STILL_FILE)
        run_r_path = os.path.join(ASSETS_DIR, COP_RUN_RIGHT_FILE)
        run_l_path = os.path.join(ASSETS_DIR, COP_RUN_LEFT_FILE)
        jump_r_path = os.path.join(ASSETS_DIR, COP_JUMP_RIGHT_FILE)
        jump_l_path = os.path.join(ASSETS_DIR, COP_JUMP_LEFT_FILE)
        #Load the images
        still = safe_load_image(still_path, convert_alpha=True)
        run_r = safe_load_image(run_r_path, convert_alpha=True)
        run_l = safe_load_image(run_l_path, convert_alpha=True)
        jump_r = safe_load_image(jump_r_path, convert_alpha=True)
        jump_l = safe_load_image(jump_l_path, convert_alpha=True)
        #if any cop sprites are missing then we stop the execution of the pygame
        if still is None or run_r is None or run_l is None:
            raise FileNotFoundError(
                "Missing cop sprites in assets."
                "Check COP_STILL_FILE, COP_RUN_RIGHT_FILE, COP_RUN_LEFT_FILE.")
        #Scale the sprites proportionally
        self.sprite_idle = scale_to_target_height(still, SPRITE_TARGET_H)
        self.sprite_run_r = scale_to_target_height(run_r, SPRITE_TARGET_H)
        self.sprite_run_l = scale_to_target_height(run_l, SPRITE_TARGET_H)
        #Jump pose falls back to the run sprite if it's ever missing, same
        #as Player — an added-on 4th pose, not a hard requirement
        self.sprite_jump_r = scale_to_target_height(jump_r, SPRITE_TARGET_H) if jump_r else self.sprite_run_r
        self.sprite_jump_l = scale_to_target_height(jump_l, SPRITE_TARGET_H) if jump_l else self.sprite_run_l

    #Resets position, physics, and AI state — also reapplies difficulty tuning,
    #since a restarted run may follow a fresh difficulty-select choice
    def reset(self, x: int, y: int, difficulty: str) -> None:
        self.rect.topleft = (x, y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing_right = True
        self.speed = COP_SPEED_BY_DIFFICULTY[difficulty]
        self.reaction_delay = COP_REACTION_DELAY_BY_DIFFICULTY[difficulty]
        self.build_patience = COP_BUILD_PATIENCE_BY_DIFFICULTY[difficulty]
        self.break_patience = COP_BREAK_PATIENCE_BY_DIFFICULTY[difficulty]
        self.build_duration = COP_BUILD_DURATION_BY_DIFFICULTY[difficulty]
        self._headstart_timer = COP_HEADSTART_SECONDS
        self._reaction_timer = 0.0
        self._known_player_x = x
        self._best_centery = float(self.rect.centery)
        self._stuck_timer = 0.0
        self._platforms_built = 0
        self._platforms_broken = 0
        self._is_building = False
        self._building_timer = 0.0
        self.last_broken_platform_rect = None

    #Decides which direction to move this frame: normally straight at the
    #player's (reaction-delayed) x, but prefers steering toward the nearest
    #reachable platform instead when one exists and climbing is needed — see
    #_find_nearest_reachable_platform. Does nothing during the opening
    #headstart or while frozen mid-build (see _is_building).
    def ai_steer(self, dt: float, player_rect: pygame.Rect, platforms: List[Platform]) -> None:
        if self._headstart_timer > 0:
            self._headstart_timer -= dt
            self.vx = 0.0
            return
        if self._is_building:
            return

        #Reaction delay: only refresh the cop's "known" player position every
        #reaction_delay seconds, instead of reacting instantly every frame
        self._reaction_timer += dt
        if self._reaction_timer >= self.reaction_delay:
            self._known_player_x = player_rect.centerx
            self._reaction_timer = 0.0

        #Track upward progress — ai_try_jump uses how long it's been since
        #real progress to decide when to give up on normal jumps and break
        #a blocking platform instead
        if self.rect.centery < self._best_centery - PROGRESS_EPSILON:
            self._best_centery = self.rect.centery
            self._stuck_timer = 0.0
        else:
            self._stuck_timer += dt

        #Prefer heading toward a platform that's already reachable — "follow
        #your platforms or build his own, depending on the distance" — real
        #jumps naturally succeed more often when aimed at an actual target
        #instead of just the player's raw x, which in turn means the cop
        #builds less often (it only gets stuck, and resorts to building,
        #when nothing usable is actually in reach)
        target_x = self._known_player_x
        needs_to_climb = player_rect.top < self.rect.top - CLIMB_TOLERANCE
        if needs_to_climb:
            nearest = self._find_nearest_reachable_platform(platforms)
            if nearest is not None:
                target_x = nearest.rect.centerx

        if target_x > self.rect.centerx + STEER_DEADZONE:
            self.vx = self.speed
            self.facing_right = True
        elif target_x < self.rect.centerx - STEER_DEADZONE:
            self.vx = -self.speed
            self.facing_right = False
        else:
            self.vx = 0.0

    #Finds the closest platform that's genuinely within normal jump range
    #(see JUMP_REACH_DX/DY) and above the cop by more than CLIMB_TOLERANCE —
    #the "optimization technique" behind preferring existing platforms over
    #building a new one. A simple nearest-neighbor scan; the platform lists
    #here are small (a handful to a few dozen), so no fancier structure is
    #worth the complexity.
    def _find_nearest_reachable_platform(self, platforms: List[Platform]) -> Optional[Platform]:
        best = None
        best_dist2 = None
        for p in platforms:
            dx = p.rect.centerx - self.rect.centerx
            dy = self.rect.centery - p.rect.centery  # positive = platform is above
            if dy <= CLIMB_TOLERANCE or dy > JUMP_REACH_DY or abs(dx) > JUMP_REACH_DX:
                continue
            dist2 = dx * dx + dy * dy
            if best is None or dist2 < best_dist2:
                best = p
                best_dist2 = dist2
        return best

    #Jumps when the player is above the cop and it's on solid ground —
    #mirrors Player.try_jump, but the trigger is "the player is above me"
    #instead of a key press. Two escalating fallbacks kick in the longer
    #the cop goes without real upward progress: first it starts building its
    #own stepping-stone platform (routine — see COP_BUILD_PATIENCE_BY_DIFFICULTY),
    #and only much later, if that's still not enough, it destroys the
    #nearest player-built platform instead (rare last resort — see
    #COP_BREAK_PATIENCE_BY_DIFFICULTY). Does nothing during the opening
    #headstart or while frozen mid-build.
    def ai_try_jump(self, player_rect: pygame.Rect, platforms: List[Platform]) -> None:
        #Cleared every call — only set for the one frame a break actually happens
        self.last_broken_platform_rect = None
        if self._headstart_timer > 0 or self._is_building:
            return
        needs_to_climb = player_rect.top < self.rect.top - CLIMB_TOLERANCE
        if not (needs_to_climb and self.on_ground):
            return
        if self._stuck_timer >= self.break_patience and self._platforms_broken < MAX_PLATFORM_BREAKS:
            self._break_nearest_platform(platforms)
            return
        if self._stuck_timer >= self.build_patience and self._platforms_built < MAX_COP_BUILDS:
            self._start_building()
            return
        self.vy = -self.jump_strength
        self.on_ground = False

    #Starts building a stepping-stone platform for itself, the same way the
    #player builds — a real, physics-based platform within normal jump
    #range, not a teleport. The cop freezes in place for build_duration
    #seconds (see COP_BUILD_DURATION_BY_DIFFICULTY — a real, visible "how
    #fast the cop builds" difference between difficulties) before the
    #platform actually appears; see move_and_collide for the completion.
    #Target position is computed now (biased toward the player's x, capped
    #by COP_BUILD_RISE so a following normal jump can reach it) so it stays
    #fixed for the whole build even if the player moves in the meantime.
    def _start_building(self) -> None:
        build_cx = self.rect.centerx + max(-80, min(80, self._known_player_x - self.rect.centerx))
        self._build_target_x = int(build_cx - COP_BUILD_PLAT_W / 2)
        self._build_target_y = int(self.rect.top - COP_BUILD_RISE)
        self._is_building = True
        self._building_timer = self.build_duration
        self.vx = 0.0
        self.vy = 0.0

    #Destroys the player-built platform nearest to the cop (never the floor,
    #platforms[0]) — the last-resort fallback for a gap real jumps can't
    #clear. Resets the stuck timer so it gets a full fresh shot at climbing
    #normally afterward, rather than potentially chain-breaking more
    #platforms the instant this one turns out not to have been enough.
    def _break_nearest_platform(self, platforms: List[Platform]) -> None:
        candidates = platforms[1:]
        if not candidates:
            return

        def dist2(p: Platform) -> float:
            cx, cy = p.rect.center
            return (cx - self.rect.centerx) ** 2 + (cy - self.rect.centery) ** 2

        nearest = min(candidates, key=dist2)
        self.last_broken_platform_rect = nearest.rect.copy()
        platforms.remove(nearest)
        self._platforms_broken += 1
        self._stuck_timer = 0.0

    #prevent the cop from mouving outside from the horizontal world bounds
    def clamp_to_world_x(self, world_w: int) -> None:
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > world_w:
            self.rect.right = world_w

    #Chooses which sprite to display depending on movement direction and
    #whether we're airborne (jumping or falling)
    def _pick_sprite(self) -> pygame.Surface:
        if not self.on_ground:
            return self.sprite_jump_r if self.facing_right else self.sprite_jump_l
        moving = abs(self.vx) > 1e-3
        if not moving:
            return self.sprite_idle
        if self.vx < -1e-3:
            return self.sprite_run_l
        if self.vx > 1e-3:
            return self.sprite_run_r
        return self.sprite_run_r if self.facing_right else self.sprite_run_l

    #Draws the cop sprite using the camera transformation
    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        sprite = self._pick_sprite()
        sx, sy = camera.apply(self.rect.x, self.rect.y)
        sprite_rect = sprite.get_rect()
        sprite_rect.midbottom = (sx + self.rect.w // 2, sy + self.rect.h + FEET_OFFSET_Y)
        screen.blit(sprite, sprite_rect)

    #Applies gravity, updates position, and handles collision detection —
    #identical two-pass approach to Player.move_and_collide (same shared
    #platform list the player builds onto and the cop can break). While
    #mid-build (see _start_building), skips physics entirely and just counts
    #down the timer, appending the actual platform once it completes.
    def move_and_collide(self, dt: float, platforms: List[Platform]) -> None:
        if self._is_building:
            self._building_timer -= dt
            if self._building_timer <= 0:
                platforms.append(Platform(
                    self._build_target_x, self._build_target_y,
                    COP_BUILD_PLAT_W, COP_BUILD_PLAT_H, built_by="cop",
                ))
                self._platforms_built += 1
                self._stuck_timer = 0.0
                self._is_building = False
            return

        self.vy += self.gravity * dt
        self.on_ground = False

        #Horizontal movement
        self.rect.x += int(self.vx * dt)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vx > 0:
                    self.rect.right = p.rect.left
                elif self.vx < 0:
                    self.rect.left = p.rect.right

        #Vertical movement
        self.rect.y += int(self.vy * dt)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vy > 0:
                    self.rect.bottom = p.rect.top
                    self.vy = 0.0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = p.rect.bottom
                    self.vy = 0.0

        #Ground probe — same fix as Player.move_and_collide: colliderect
        #alone flickers "not grounded" for a resting entity whenever a
        #frame's fall rounds to 0px, since touching edges don't count as
        #colliding. Nudge a probe rect down a couple pixels to catch that.
        if not self.on_ground and self.vy >= 0:
            probe = self.rect.move(0, 2)
            for p in platforms:
                if probe.colliderect(p.rect):
                    self.on_ground = True
                    break
