from __future__ import annotations
import os
import pygame
from typing import List, Tuple
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
    COP_SPEED_BY_DIFFICULTY,
    COP_REACTION_DELAY_BY_DIFFICULTY,
    COP_START_GAP_BY_DIFFICULTY,
    COP_PATIENCE_BY_DIFFICULTY,
)

#How close (vertically, in px) the cop needs to be to the player's height
#before it steers straight at the player's x instead of following waypoints
CHASE_HEIGHT_THRESHOLD = 80
#How close (vertically, in px) the cop needs to be to a waypoint's height —
#while actually standing on solid ground — before it counts as "reached"
#and the AI advances its target to the next one up the path
WAYPOINT_REACHED_TOLERANCE = 12
#Dead zone so the cop doesn't jitter left/right once lined up with its target
STEER_DEADZONE = 6

#--- "Cheat" hop (see Cop._start_hop / Cop._advance_hop) ---
#Early versions of this tried to make the cop spawn a platform and then
#reach it via normal jump physics (velocity + gravity + collision). That
#turned out to be fragile in a bunch of subtle ways — a few pixels of
#rounding at 60fps repeatedly turned "should land on top" into "clips the
#edge instead," and every fix for one case surfaced another. So instead the
#cheat hop drives the cop's position directly over a short fixed duration —
#no velocity, no gravity, no collision math to get wrong. It reads as "the
#cop cheats," which fits the theme anyway (a dirty cop cutting corners to
#catch you), and it can never fail to land.
HOP_DURATION = 0.35
#A small platform is still placed under the landing spot so the cop has
#normal solid ground the instant the hop ends, even if that spot doesn't
#line up exactly with a real platform's edges.
HOP_PAD_W, HOP_PAD_H = 80, 16
#Safety cap so a pathological stall (e.g. a badly misbehaving future level)
#can't grow this list forever — fails soft rather than leaking memory
MAX_CHEAT_HOPS = 40


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
    decides its movement each frame: follow the level's precomputed
    waypoint path upward, or steer straight at the player once close enough
    in height for a real chase.

    Unlike the player, the cop can cheat: if a normal jump toward the next
    waypoint doesn't pan out within its patience window, it performs a
    guaranteed "cheat hop" straight to that waypoint (see _start_hop),
    ensuring it's never permanently stuck on the fixed layout.
    """
    def __init__(self, x: int, y: int, difficulty: str, waypoints: List[Tuple[int, int]]):
        #cop collision rectangle used for physics and collisions (same size as the player)
        self.rect = pygame.Rect(x, y, PLAYER_W, PLAYER_H)
        #Physics variables — gravity/jump are identical to the player's so the
        #cop can always make the same jumps on the same fixed level
        self.vx = 0.0
        self.vy = 0.0
        self.gravity = 1400.0
        self.jump_strength = 650.0
        #Difficulty tuning — the only numbers that differ between Easy/Medium/Hard
        self.speed = COP_SPEED_BY_DIFFICULTY[difficulty]
        self.reaction_delay = COP_REACTION_DELAY_BY_DIFFICULTY[difficulty]
        self.patience = COP_PATIENCE_BY_DIFFICULTY[difficulty]
        self.on_ground = False
        self.facing_right = True

        #Ordered bottom-to-top path of (x, y) points up the fixed level (see
        #level.get_climb_waypoints). The AI works its way up this list.
        self.waypoints = waypoints
        self.waypoint_index = 0
        #Simulates reaction lag: the AI only "sees" a fresh player position
        #once every reaction_delay seconds, instead of instantly every frame
        self._reaction_timer = 0.0
        self._known_player_x = x
        #How long (seconds) the cop has been trying to reach the current
        #waypoint without advancing — drives the cheat-hop fallback
        self._stuck_timer = 0.0
        #The cop's current landing pad, if any — a list of at most 1
        self.created_platforms: List[Platform] = []
        #Lifetime count of cheat hops used this run, capped defensively so a
        #pathological stall can't repeat forever
        self._hops_used = 0

        #Cheat-hop state — while active, position is driven directly by
        #_advance_hop instead of normal steering/physics
        self._hop_active = False
        self._hop_start_x = 0.0
        self._hop_start_y = 0.0
        self._hop_target_x = 0.0
        self._hop_target_y = 0.0
        self._hop_elapsed = 0.0

        #Build the file paths for the cop's sprites
        still_path = os.path.join(ASSETS_DIR, COP_STILL_FILE)
        run_r_path = os.path.join(ASSETS_DIR, COP_RUN_RIGHT_FILE)
        run_l_path = os.path.join(ASSETS_DIR, COP_RUN_LEFT_FILE)
        #Load the images
        still = safe_load_image(still_path, convert_alpha=True)
        run_r = safe_load_image(run_r_path, convert_alpha=True)
        run_l = safe_load_image(run_l_path, convert_alpha=True)
        #if any cop sprites are missing then we stop the execution of the pygame
        if still is None or run_r is None or run_l is None:
            raise FileNotFoundError(
                "Missing cop sprites in assets."
                "Check COP_STILL_FILE, COP_RUN_RIGHT_FILE, COP_RUN_LEFT_FILE.")
        #Scale the sprites proportionally
        self.sprite_idle = scale_to_target_height(still, SPRITE_TARGET_H)
        self.sprite_run_r = scale_to_target_height(run_r, SPRITE_TARGET_H)
        self.sprite_run_l = scale_to_target_height(run_l, SPRITE_TARGET_H)

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
        self.patience = COP_PATIENCE_BY_DIFFICULTY[difficulty]
        self.waypoint_index = 0
        self._reaction_timer = 0.0
        self._known_player_x = x
        self._stuck_timer = 0.0
        self.created_platforms = []
        self._hops_used = 0
        self._hop_active = False
        self._hop_elapsed = 0.0

    #Decides which direction to move this frame: straight at the player's x
    #if the cop is at a similar height to them (a real chase), otherwise
    #toward the next waypoint above it on the fixed climb path. Does nothing
    #while a cheat hop is in progress — position is driven by _advance_hop.
    def ai_steer(self, dt: float, player_rect: pygame.Rect) -> None:
        if self._hop_active:
            return

        #Reaction delay: only refresh the cop's "known" player position every
        #reaction_delay seconds, instead of reacting instantly every frame
        self._reaction_timer += dt
        if self._reaction_timer >= self.reaction_delay:
            self._known_player_x = player_rect.centerx
            self._reaction_timer = 0.0

        #Only advance to the next waypoint once actually standing on solid
        #ground at or above its height. Checking height alone (without the
        #on_ground guard) would flip the target mid-jump — since consecutive
        #waypoints alternate lanes, that would pull the cop toward the
        #wrong lane before it even lands, making it miss the platform.
        prev_waypoint_index = self.waypoint_index
        while (
            self.on_ground
            and self.waypoint_index < len(self.waypoints) - 1
            and self.rect.centery <= self.waypoints[self.waypoint_index][1] + WAYPOINT_REACHED_TOLERANCE
        ):
            self.waypoint_index += 1

        #Track how long we've been trying to reach the same waypoint —
        #ai_try_jump uses this to decide when to stop attempting a normal
        #jump and cheat with a guaranteed hop instead
        if self.waypoint_index != prev_waypoint_index:
            self._stuck_timer = 0.0
        else:
            self._stuck_timer += dt

        same_height = abs(self.rect.centery - player_rect.centery) < CHASE_HEIGHT_THRESHOLD
        target_x = self._known_player_x if same_height else self.waypoints[self.waypoint_index][0]

        if target_x > self.rect.centerx + STEER_DEADZONE:
            self.vx = self.speed
            self.facing_right = True
        elif target_x < self.rect.centerx - STEER_DEADZONE:
            self.vx = -self.speed
            self.facing_right = False
        else:
            self.vx = 0.0

    #Jumps automatically when the next waypoint sits above the cop and it's
    #currently on solid ground — mirrors Player.try_jump, but the trigger is
    #"does the path require going up" instead of a key press. If we've been
    #stuck on this same waypoint longer than our patience allows, cheat with
    #a guaranteed hop straight to it instead of gambling on another jump.
    def ai_try_jump(self) -> None:
        if self._hop_active:
            return
        target_x, target_y = self.waypoints[self.waypoint_index]
        needs_to_climb = target_y < self.rect.top - WAYPOINT_REACHED_TOLERANCE
        if not (needs_to_climb and self.on_ground):
            return
        if self._stuck_timer >= self.patience and self._hops_used < MAX_CHEAT_HOPS:
            self._start_hop(target_x, target_y)
            return
        self.vy = -self.jump_strength
        self.on_ground = False

    #Begins a guaranteed cheat hop straight to the given target — position
    #is driven directly by _advance_hop over HOP_DURATION, bypassing normal
    #jump physics entirely so it can never fail to land.
    def _start_hop(self, target_x: float, target_y: float) -> None:
        self._hop_active = True
        self._hop_start_x, self._hop_start_y = float(self.rect.x), float(self.rect.y)
        self._hop_target_x = target_x - PLAYER_W / 2
        self._hop_target_y = target_y - PLAYER_H
        self._hop_elapsed = 0.0
        self.facing_right = target_x >= self.rect.centerx
        self.on_ground = False
        self.vx = 0.0
        self.vy = 0.0
        #Solid ground under the landing spot, in case it doesn't line up
        #exactly with a real platform's edges
        pad_x = int(target_x - HOP_PAD_W / 2)
        self.created_platforms = [Platform(pad_x, int(target_y), HOP_PAD_W, HOP_PAD_H)]
        self._hops_used += 1

    #Advances an in-progress cheat hop by dt, interpolating position toward
    #the target and finishing (grounded, ready for normal physics again)
    #once HOP_DURATION has elapsed.
    def _advance_hop(self, dt: float) -> None:
        self._hop_elapsed += dt
        t = min(1.0, self._hop_elapsed / HOP_DURATION)
        self.rect.x = int(self._hop_start_x + (self._hop_target_x - self._hop_start_x) * t)
        self.rect.y = int(self._hop_start_y + (self._hop_target_y - self._hop_start_y) * t)
        if t >= 1.0:
            self._hop_active = False
            self.on_ground = True
            self.vx = 0.0
            self.vy = 0.0

    #prevent the cop from mouving outside from the horizontal world bounds
    def clamp_to_world_x(self, world_w: int) -> None:
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > world_w:
            self.rect.right = world_w

    #Chooses which sprite to display depending on movement direction
    def _pick_sprite(self) -> pygame.Surface:
        if self._hop_active:
            return self.sprite_run_r if self.facing_right else self.sprite_run_l
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
    #identical two-pass approach to Player.move_and_collide, except the cop
    #also collides with its own landing pad, and skips physics entirely
    #while a cheat hop is driving its position directly.
    def move_and_collide(self, dt: float, platforms: List[Platform]) -> None:
        if self._hop_active:
            self._advance_hop(dt)
            return

        all_platforms = platforms + self.created_platforms

        self.vy += self.gravity * dt
        self.on_ground = False

        #Horizontal movement
        self.rect.x += int(self.vx * dt)
        for p in all_platforms:
            if self.rect.colliderect(p.rect):
                if self.vx > 0:
                    self.rect.right = p.rect.left
                elif self.vx < 0:
                    self.rect.left = p.rect.right

        #Vertical movement
        self.rect.y += int(self.vy * dt)
        for p in all_platforms:
            if self.rect.colliderect(p.rect):
                if self.vy > 0:
                    self.rect.bottom = p.rect.top
                    self.vy = 0.0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = p.rect.bottom
                    self.vy = 0.0
