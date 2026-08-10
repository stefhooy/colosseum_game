from __future__ import annotations
import asyncio
import os
import pygame
from typing import List, Optional, Tuple

#Import the things we need for the screens of our game
from .settings import (
    ASSETS_DIR,
    FIRST_SCREEN_FILE,
    MENU_BG_FILE,
    SCOREBOARD_BG_FILE,
    FPS,
    SCREEN_W, SCREEN_H,
    STATE_SPLASH,
    STATE_MENU,
    STATE_NAME,
    STATE_SCOREBOARD,
    STATE_GAME,
    DIFFICULTY_EASY,
    DIFFICULTY_MEDIUM,
    DIFFICULTY_HARD,
)
from .utils import safe_load_image, get_font, draw_center_text, format_time
from .scores import load_scores
from .effects import draw_goal_glow
from .platform import Platform

async def run_splash(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """
    Shows first_screen.jpg fullscreen. Any key or click advances to the menu.
    """
    img = safe_load_image(os.path.join(ASSETS_DIR, FIRST_SCREEN_FILE), convert_alpha=False)
    font = get_font(36)

    while True:
        _ = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return STATE_MENU

        if img:
            scaled = pygame.transform.smoothscale(img, (SCREEN_W, SCREEN_H))
            screen.blit(scaled, (0, 0))
        else:
            screen.fill((10, 10, 25))

        draw_center_text(screen, font, "PRESS ANY KEY TO CONTINUE", SCREEN_H - 80, (255, 255, 255))
        pygame.display.flip()
        await asyncio.sleep(0)


#Run the main menu screen
async def run_menu(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """
    This function stays in a while loop until the player chooses an option:
    - ENTER -> go to name input
    - S -> go to scoreboard
    - ESC or window close -> quit the game
    """
    #Laod menu background image (if missing, the menu still works
    menu_bg = safe_load_image(os.path.join(ASSETS_DIR, MENU_BG_FILE), convert_alpha=False)
    #Font used for title and instructions
    font_title = get_font(96)
    font_body = get_font(40)
    #Y positions for the layout to align the text easier
    TITLE_Y = 120
    LINE1_Y = 260
    LINE2_Y = 310
    OPT1_Y = 470
    OPT2_Y = 530
    OPT3_Y = 590

    while True:
        #Tick controls FPS for this menu loop (dt not really needed here, but keeps consistency)
        _ = clock.tick(FPS) / 1000.0
        #Input menu handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return STATE_NAME
                    #S to go to scoreboard
                if event.key == pygame.K_s:
                    return STATE_SCOREBOARD
                    #Esc to go back to splash screen
                if event.key == pygame.K_ESCAPE:
                    return STATE_SPLASH
        #Drawing the blit, title + descriptions
        if menu_bg:
            screen.blit(menu_bg, (0, 0))
        else:
            #Fallback measure if image is missing (just a dark bg will appear)
            screen.fill((10, 10, 25))
        #Title of the game! and brief description of the game for new incomers of the game
        draw_center_text(screen, font_title, "COLOSSEUM CURFEW", TITLE_Y)
        draw_center_text(screen, font_body, "It's your last night in Rome. Climb the Colosseum for one epic photo.", LINE1_Y,)
        draw_center_text(screen, font_body, "A cop is on your tail — reach the top before curfew catches you!", LINE2_Y,)
        #Show the menu options
        draw_center_text(screen, font_body, "PRESS ENTER TO START", OPT1_Y, (255, 255, 255))
        draw_center_text(screen, font_body, "PRESS S FOR SCOREBOARD", OPT2_Y, (255, 255, 255))
        draw_center_text(screen, font_body, "PRESS ESC TO QUIT", OPT3_Y, (255, 255, 255))

        pygame.display.flip()
        await asyncio.sleep(0)  #yield to browser each frame

#This will run the name input screen and returns:
async def run_name_input(screen: pygame.Surface, clock: pygame.time.Clock) -> Optional[str]:
    """
    - A valid player name string when ENTER is pressed
    - None if the player cancels with ESC or closes the window
    """
    menu_bg = safe_load_image(os.path.join(ASSETS_DIR, MENU_BG_FILE), convert_alpha=False)
    font_title = get_font(72)
    font_body = get_font(44)
    #Player name is built character by character from keyboard input
    name = ""

    while True:
        _ = clock.tick(FPS) / 1000.0
        #Building the name string
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                #ESC cancels name input and return to menu
                if event.key == pygame.K_ESCAPE:
                    return None
                #Enter confirms the name
                if event.key == pygame.K_RETURN:
                    cleaned = name.strip()
                    if cleaned:
                        return cleaned
                #Backspace will the delet the last character
                if event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    #This event.unicode stores the actual typed character (not the key code)
                    #We only accept printable characters and limit length to 16
                    if event.unicode and len(event.unicode) == 1:
                        if event.unicode.isprintable() and len(name) < 16:
                            name += event.unicode
        #Drawing here
        if menu_bg:
            screen.blit(menu_bg, (0, 0))
        else:
            screen.fill((10, 10, 25))
        draw_center_text(screen, font_title, "ENTER YOUR NAME", 200, (0, 0, 0))
        draw_center_text(screen, font_body, "TYPE THEN PRESS ENTER", 290, (0, 0, 0))
        #Draw the input box
        box_w, box_h = 700, 80
        box_x = (SCREEN_W - box_w) // 2
        box_y = 420
        pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(box_x, box_y, box_w, box_h))
        pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(box_x, box_y, box_w, box_h), 2)
        #Draw the current name inside the input box
        name_surf = font_body.render(name, True, (255, 255, 255))
        screen.blit(name_surf, (box_x + 18, box_y + 18))
        #Instructionn to go back
        draw_center_text(screen, font_body, "ESC TO GO BACK", 540, (255, 255, 255))
        pygame.display.flip()
        await asyncio.sleep(0)  #yield to browser each frame

#Runs the difficulty-select screen (shown after name input, before the map preview)
async def run_difficulty_select(screen: pygame.Surface, clock: pygame.time.Clock) -> Optional[str]:
    """
    Lets the player pick Easy/Medium/Hard with the 1/2/3 keys — this choice
    tunes the Cop AI (Step 7) and picks which leaderboard bucket the run
    gets saved to (Step 12). Returns:
    - "quit" if the window is closed
    - None if the player cancels with ESC (caller sends them back to the menu)
    - DIFFICULTY_EASY / DIFFICULTY_MEDIUM / DIFFICULTY_HARD once chosen
    """
    menu_bg = safe_load_image(os.path.join(ASSETS_DIR, MENU_BG_FILE), convert_alpha=False)
    font_title = get_font(80)
    font_option = get_font(46)
    font_desc = get_font(30)

    #Each option: (key, difficulty value, label, short description)
    options = [
        (pygame.K_1, DIFFICULTY_EASY, "1 - EASY", "A head start, and a slower, forgiving cop."),
        (pygame.K_2, DIFFICULTY_MEDIUM, "2 - MEDIUM", "Balanced pace — the cop matches your speed."),
        (pygame.K_3, DIFFICULTY_HARD, "3 - HARD", "Fast reflexes required — the cop is right behind you."),
    ]

    while True:
        _ = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                for key, value, _label, _desc in options:
                    if event.key == key:
                        return value

        if menu_bg:
            screen.blit(menu_bg, (0, 0))
        else:
            screen.fill((10, 10, 25))

        draw_center_text(screen, font_title, "SELECT DIFFICULTY", 140, (255, 255, 255))

        start_y = 380
        gap_y = 130
        for i, (_key, _value, label, desc) in enumerate(options):
            y = start_y + i * gap_y
            draw_center_text(screen, font_option, label, y, (255, 255, 255))
            draw_center_text(screen, font_desc, desc, y + 55, (200, 200, 200))

        draw_center_text(screen, font_desc, "ESC TO GO BACK", SCREEN_H - 60, (200, 200, 200))
        pygame.display.flip()
        await asyncio.sleep(0)  #yield to browser each frame

#Runs the scoreboard screen
async def run_scoreboard(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """
    Shows the top 10 best times stored in the JSON file and will return to the menu when ENTER or ESC is pressed
    """
    #Load scoreboard background (fallback works if ever missing)
    sb_bg = safe_load_image(os.path.join(ASSETS_DIR, SCOREBOARD_BG_FILE), convert_alpha=False)
    font_title = get_font(90)
    font_body = get_font(44)

    while True:
        _ = clock.tick(FPS) / 1000.0
        #Input handling logic with ESC and Enter
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    return STATE_MENU
        #Drawing of the scoreboard and top 10 best scores
        if sb_bg:
            screen.blit(sb_bg, (0, 0))
        else:
            screen.fill((10, 10, 25))

        draw_center_text(screen, font_title, "SCOREBOARD", 90)
        #load the scores from JSON file
        scores = load_scores()
        if not scores:
            #First time, if ever the scoreboard is empty
            draw_center_text(screen, font_body, "NO SCORES YET. BE THE FIRST.", 240)
        else:
            #When the scores.json file is populated
            start_y = 220
            line_h = 52
            for i, s in enumerate(scores[:10], start=1):
                line = f"{i:02d}. {s['name']}  {format_time(s['time'])}"
                draw_center_text(screen, font_body, line, start_y + (i - 1) * line_h)
        draw_center_text(screen, font_body, "PRESS ENTER OR ESC TO RETURN", 950, (255, 255, 0))
        pygame.display.flip()
        await asyncio.sleep(0)  #yield to browser each frame


#Runs the pre-game map preview screen (shown after name input, before the run timer starts)
async def run_map_preview(
    screen: pygame.Surface,
    clock: pygame.time.Clock,
    background: pygame.Surface,
    platforms: List[Platform],
    spawn: Tuple[int, int],
    goal_rect: pygame.Rect,
) -> str:
    """
    Shows the whole Colosseum background shrunk to fit the screen, with the
    fixed platform layout, spawn point, and goal all marked, so the player
    can plan their climb before the cop starts chasing. Any key or click
    advances to gameplay; ESC goes back to the menu.
    """
    #The world is much taller than the screen, so we squash it down uniformly
    #with separate x/y scale factors and apply the same factors to every
    #marker below — that keeps everything lined up even though it's not a
    #1:1 aspect-ratio preview.
    world_w, world_h = background.get_size()
    scale_x = SCREEN_W / world_w
    scale_y = SCREEN_H / world_h
    preview_bg = pygame.transform.smoothscale(background, (SCREEN_W, SCREEN_H))

    def to_preview(wx: float, wy: float) -> tuple[int, int]:
        return int(wx * scale_x), int(wy * scale_y)

    font_title = get_font(64)
    font_body = get_font(38)

    while True:
        _ = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return STATE_MENU
                return STATE_GAME
            if event.type == pygame.MOUSEBUTTONDOWN:
                return STATE_GAME

        screen.blit(preview_bg, (0, 0))

        #Draw the fixed platform layout so the whole route is visible at a glance
        for p in platforms:
            px, py = to_preview(p.rect.x, p.rect.y)
            pw, ph = max(2, int(p.rect.w * scale_x)), max(2, int(p.rect.h * scale_y))
            pygame.draw.rect(screen, (255, 215, 0), pygame.Rect(px, py, pw, ph), 2)

        #Spawn marker (same orange dot style as the in-game spawn marker)
        pygame.draw.circle(screen, (255, 165, 0), to_preview(*spawn), 8)
        #Goal marker (reuses the same pulsing glow used in gameplay)
        draw_goal_glow(screen, to_preview(goal_rect.centerx, goal_rect.centery))

        draw_center_text(screen, font_title, "MEMORIZE YOUR ROUTE", 60, (255, 255, 255))
        draw_center_text(screen, font_body, "PRESS ANY KEY TO BEGIN THE CLIMB", SCREEN_H - 100, (255, 255, 255))
        draw_center_text(screen, font_body, "ESC TO GO BACK", SCREEN_H - 50, (200, 200, 200))

        pygame.display.flip()
        await asyncio.sleep(0)  #yield to browser each frame
