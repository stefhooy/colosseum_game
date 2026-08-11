from __future__ import annotations
import os
import pygame
from typing import List
#Used for the collision detection
from .platform import Platform
#USed for the world gameplay (screen transformation)
from .camera import Camera
from .utils import safe_load_image, scale_to_target_height
from .settings import (
    ASSETS_DIR,
    PLAYER_W, PLAYER_H,
    SPRITE_TARGET_H,
    FEET_OFFSET_Y,
    CHAR_STILL_FILE,
    CHAR_RUN_RIGHT_FILE,
    CHAR_RUN_LEFT_FILE,
    CHAR_JUMP_RIGHT_FILE,
    CHAR_JUMP_LEFT_FILE,
)

#This class is the player that we will control
class Player:
    """
    The Player class handles:
    - Movement (left/right)
    - Jumping physics
    - Gravity
    - Collision detection with platforms
    - Sprite selection and rendering
    """
    def __init__(self, x: int, y: int):
        #player collision rectangle used for physics and collisions
        self.rect = pygame.Rect(x, y, PLAYER_W, PLAYER_H)
        #Physics variables
        self.vx = 0.0 #horizontal
        self.vy = 0.0 #vertical
        self.speed = 260.0
        self.jump_strength = 650.0
        self.gravity = 1400.0
        self.on_ground = False #Prevent double jumping
        #Direction tracking
        self.facing_right = True
        #Build the file paths for our character we created
        still_path = os.path.join(ASSETS_DIR, CHAR_STILL_FILE)
        run_r_path = os.path.join(ASSETS_DIR, CHAR_RUN_RIGHT_FILE)
        run_l_path = os.path.join(ASSETS_DIR, CHAR_RUN_LEFT_FILE)
        jump_r_path = os.path.join(ASSETS_DIR, CHAR_JUMP_RIGHT_FILE)
        jump_l_path = os.path.join(ASSETS_DIR, CHAR_JUMP_LEFT_FILE)
        #Load the images
        still = safe_load_image(still_path, convert_alpha=True)
        run_r = safe_load_image(run_r_path, convert_alpha=True)
        run_l = safe_load_image(run_l_path, convert_alpha=True)
        jump_r = safe_load_image(jump_r_path, convert_alpha=True)
        jump_l = safe_load_image(jump_l_path, convert_alpha=True)
        #if any character sprites are missing then we stop the execution of the pygame
        if still is None or run_r is None or run_l is None:
            raise FileNotFoundError(
                "Missing character sprites in assets."
                "Check CHAR_STILL_FILE, CHAR_RUN_RIGHT_FILE, CHAR_RUN_LEFT_FILE.")
        #Scale the sprites proportionally
        self.sprite_idle = scale_to_target_height(still, SPRITE_TARGET_H)
        self.sprite_run_r = scale_to_target_height(run_r, SPRITE_TARGET_H)
        self.sprite_run_l = scale_to_target_height(run_l, SPRITE_TARGET_H)
        #Jump pose falls back to the run sprite if it's ever missing (unlike
        #the 3 base poses, this one won't crash the game — it's an added-on
        #4th pose, not something the game was originally built to require)
        self.sprite_jump_r = scale_to_target_height(jump_r, SPRITE_TARGET_H) if jump_r else self.sprite_run_r
        self.sprite_jump_l = scale_to_target_height(jump_l, SPRITE_TARGET_H) if jump_l else self.sprite_run_l

    #Resets the player position and physics values, we use this when we want to restart the run/climb
    def reset(self, x: int, y: int) -> None:
        self.rect.topleft = (x, y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing_right = True

    #Handles horizonatl mouvement inputs
    #WAD mouvement, up left right keys or SPACE
    def handle_input(self, keys) -> None:
        self.vx = 0.0
        #Left key or A
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vx = -self.speed
            self.facing_right = False
        #Right key or D
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vx = self.speed
            self.facing_right = True

    #Allowing jumping with SPACE, W and up
    #+ prevent double jumping
    def try_jump(self, keys) -> None:
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.vy = -self.jump_strength
            self.on_ground = False

    #prevent the player from mouving outside from the horizontal world bounds and fall
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

    #Draws the player sprite using the camera transformation
    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        sprite = self._pick_sprite()
        #Convert world position into a screen position
        sx, sy = camera.apply(self.rect.x, self.rect.y)
        #Akign sprite so its feet will match with the collision rectangle
        sprite_rect = sprite.get_rect()
        sprite_rect.midbottom = (sx + self.rect.w // 2, sy + self.rect.h + FEET_OFFSET_Y)
        screen.blit(sprite, sprite_rect)

    #Applies gravity, updates position, and handles collision detection separately for X and Y axes.
    def move_and_collide(self, dt: float, platforms: List[Platform]) -> None:
        #apply gravity to the vertical velocity
        self.vy += self.gravity * dt
        self.on_ground = False

        #Horizontal movement
        self.rect.x += int(self.vx * dt)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                #Moving right, hit platform from left
                if self.vx > 0:
                    self.rect.right = p.rect.left
                elif self.vx < 0:
                    #Moving left, hit plafrom from the right
                    self.rect.left = p.rect.right

        #Vertical mouvement
        self.rect.y += int(self.vy * dt)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vy > 0:
                    #Falling down and landing on a platform (top of it)
                    self.rect.bottom = p.rect.top
                    self.vy = 0.0
                    self.on_ground = True
                elif self.vy < 0:
                    #jumping and you hit the bottom of the platform
                    self.rect.top = p.rect.bottom
                    self.vy = 0.0

        #Ground probe: colliderect only counts real overlap, not two rects
        #just touching at an edge — so a player resting exactly on a
        #platform's top can flicker "not grounded" on any frame where
        #gravity's accumulated fall rounds to 0px (int() truncation) and
        #therefore never re-touches the platform that frame. Nudging a
        #copy of the rect down a couple pixels catches that case without
        #actually moving the player, so on_ground reads stable while at rest.
        if not self.on_ground and self.vy >= 0:
            probe = self.rect.move(0, 2)
            for p in platforms:
                if probe.colliderect(p.rect):
                    self.on_ground = True
                    break
