from __future__ import annotations
import asyncio
import os
import pygame
from typing import Optional, Tuple

#Import the things we need for the screens of our game
from .settings import (
    ASSETS_DIR,
    FIRST_SCREEN_FILE,
    MENU_BG_FILE,
    SCOREBOARD_BG_FILE,
    FINAL_BG_FILE,
    FPS,
    SCREEN_W, SCREEN_H,
    STATE_SPLASH,
    STATE_MENU,
    STATE_NAME,
    STATE_WARNING,
    STATE_CONTROLS,
    STATE_SCOREBOARD,
    STATE_GAME,
    DIFFICULTY_EASY,
    DIFFICULTY_MEDIUM,
    DIFFICULTY_HARD,
)
from .utils import safe_load_image, get_font, draw_center_text, format_time
from .scores import load_scores_by_difficulty, load_scores_online_by_difficulty
from .effects import draw_goal_glow

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
        draw_center_text(screen, font_title, "CURSUS COLOSSEI", TITLE_Y)
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
async def run_scoreboard(
    screen: pygame.Surface,
    clock: pygame.time.Clock,
    initial_difficulty: str = DIFFICULTY_MEDIUM,
) -> str:
    """
    Shows the top 10 best times for one difficulty at a time (each difficulty
    keeps its own separate top 10 — see scores.add_score). Starts on
    initial_difficulty (normally whichever difficulty was just played) and
    lets the player switch tabs with 1/2/3. Returns to the menu on ENTER or ESC.

    Scores shown are the shared Supabase leaderboard when reachable, with an
    instant local fallback (scores.json) so the screen is never blank while
    waiting on the network, and still fully works offline. See
    scores.load_scores_online_by_difficulty for the online side.
    """
    #Load scoreboard background (fallback works if ever missing)
    sb_bg = safe_load_image(os.path.join(ASSETS_DIR, SCOREBOARD_BG_FILE), convert_alpha=False)
    font_title = get_font(90)
    font_tabs = get_font(38)
    font_body = get_font(44)
    font_sync = get_font(26)

    #Which difficulty tab is currently shown
    current = initial_difficulty
    #(key, difficulty value, tab label)
    tabs = [
        (pygame.K_1, DIFFICULTY_EASY, "1-EASY"),
        (pygame.K_2, DIFFICULTY_MEDIUM, "2-MEDIUM"),
        (pygame.K_3, DIFFICULTY_HARD, "3-HARD"),
    ]

    #Seed instantly from the local file (no network wait), then kick off a
    #background fetch of the shared online leaderboard for this tab
    displayed_scores = load_scores_by_difficulty(current)
    syncing = True
    fetch_task = asyncio.ensure_future(load_scores_online_by_difficulty(current))

    while True:
        _ = clock.tick(FPS) / 1000.0
        #Input handling logic with ESC/Enter to leave, 1/2/3 to switch tabs
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    return STATE_MENU
                for key, value, _label in tabs:
                    if event.key == key and value != current:
                        current = value
                        #Switching tabs re-seeds from local instantly and
                        #restarts the background fetch for the new tab
                        displayed_scores = load_scores_by_difficulty(current)
                        syncing = True
                        fetch_task = asyncio.ensure_future(load_scores_online_by_difficulty(current))

        #Once the background fetch for the CURRENT tab finishes, swap in the
        #online result — unless it failed (None), in which case we just keep
        #showing the local data we already seeded above
        if fetch_task is not None and fetch_task.done():
            online_scores = fetch_task.result()
            if online_scores is not None:
                displayed_scores = online_scores
            syncing = False
            fetch_task = None

        #Drawing of the scoreboard and top 10 best scores for the current tab
        if sb_bg:
            screen.blit(sb_bg, (0, 0))
        else:
            screen.fill((10, 10, 25))

        draw_center_text(screen, font_title, "SCOREBOARD", 90)
        #Tab bar — the active difficulty is highlighted in yellow, others stay white
        tab_gap = 260
        tabs_start_x = SCREEN_W // 2 - tab_gap
        for i, (_key, value, label) in enumerate(tabs):
            color = (255, 255, 0) if value == current else (255, 255, 255)
            surf = font_tabs.render(label, True, color)
            x = tabs_start_x + i * tab_gap - surf.get_width() // 2
            screen.blit(surf, (x, 190))

        if not displayed_scores:
            #First time, if ever this difficulty's board is empty
            draw_center_text(screen, font_body, "NO SCORES YET. BE THE FIRST.", 300)
        else:
            #When there are scores to show for this difficulty
            start_y = 270
            line_h = 52
            for i, s in enumerate(displayed_scores[:10], start=1):
                line = f"{i:02d}. {s['name']}  {format_time(s['time'])}"
                draw_center_text(screen, font_body, line, start_y + (i - 1) * line_h)

        #Small, unobtrusive hint while the online leaderboard is still loading —
        #doesn't block anything, the local scores above are already visible
        if syncing:
            draw_center_text(screen, font_sync, "syncing online leaderboard...", 920, (180, 180, 180))
        draw_center_text(screen, font_body, "1/2/3 SWITCH DIFFICULTY  |  ENTER OR ESC TO RETURN", 970, (255, 255, 0))
        pygame.display.flip()
        await asyncio.sleep(0)  #yield to browser each frame


#Runs the dedicated "photo captured" win screen (shown once instead of the small
#in-game overlay, now that real art exists for it)
async def run_win_screen(
    screen: pygame.Surface,
    clock: pygame.time.Clock,
    player_name: str,
    final_time_s: float,
) -> str:
    """
    Full-screen "PHOTO CAPTURED!" moment using final_background.png. Returns:
    - "quit" if the window is closed
    - "restart" if R is pressed (caller resets the run and clears platforms)
    - STATE_MENU if ESC is pressed
    - STATE_SCOREBOARD if S is pressed
    """
    final_bg = safe_load_image(os.path.join(ASSETS_DIR, FINAL_BG_FILE), convert_alpha=False)
    font_title = get_font(110)
    font_body = get_font(50)
    font_hint = get_font(36)

    while True:
        _ = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "restart"
                if event.key == pygame.K_ESCAPE:
                    return STATE_MENU
                if event.key == pygame.K_s:
                    return STATE_SCOREBOARD

        if final_bg:
            scaled = pygame.transform.smoothscale(final_bg, (SCREEN_W, SCREEN_H))
            screen.blit(scaled, (0, 0))
        else:
            screen.fill((10, 10, 25))

        draw_center_text(screen, font_title, "PHOTO CAPTURED!", 130, (255, 255, 255))
        draw_center_text(screen, font_body, f"{player_name} — {format_time(final_time_s)}", 280, (255, 255, 255))
        draw_center_text(screen, font_hint, "R RESTART  |  ESC MENU  |  S SCOREBOARD", SCREEN_H - 90, (255, 255, 0))

        pygame.display.flip()
        await asyncio.sleep(0)  #yield to browser each frame

#Runs the pre-game map preview screen (shown after name input, before the run timer starts)
async def run_map_preview(
    screen: pygame.Surface,
    clock: pygame.time.Clock,
    background: pygame.Surface,
    spawn: Tuple[int, int],
    goal_rect: pygame.Rect,
) -> str:
    """
    Shows the whole Colosseum background shrunk to fit the screen, with the
    spawn point and goal marked, so the player knows where they're starting
    and what they're climbing to before the cop starts chasing. There's no
    fixed platform layout to show — the player builds their own as they
    climb. Any key or click advances to gameplay; ESC goes back to the menu.
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
                return STATE_WARNING
            if event.type == pygame.MOUSEBUTTONDOWN:
                return STATE_WARNING

        screen.blit(preview_bg, (0, 0))

        #Spawn marker (same orange dot style as the in-game spawn marker)
        pygame.draw.circle(screen, (255, 165, 0), to_preview(*spawn), 8)
        #Goal marker (reuses the same pulsing glow used in gameplay)
        draw_goal_glow(screen, to_preview(goal_rect.centerx, goal_rect.centery))

        draw_center_text(screen, font_title, "SCOUT THE COLOSSEUM", 60, (255, 255, 255))
        draw_center_text(screen, font_body, "PRESS ANY KEY TO CONTINUE", SCREEN_H - 100, (255, 255, 255))
        draw_center_text(screen, font_body, "ESC TO GO BACK", SCREEN_H - 50, (200, 200, 200))

        pygame.display.flip()
        await asyncio.sleep(0)  #yield to browser each frame

#Runs the "the cop spotted you" warning screen (shown after the map preview,
#before the controls screen and gameplay itself)
async def run_warning_screen(screen: pygame.Surface, clock: pygame.time.Clock, background: pygame.Surface) -> str:
    """
    A short narrative beat between scouting the map and actually starting
    the climb: a black message box announcing the chase is on. Any key or
    click advances to the controls screen; ESC goes back to the menu.
    """
    preview_bg = pygame.transform.smoothscale(background, (SCREEN_W, SCREEN_H))
    font_title = get_font(70)
    font_hint = get_font(36)

    while True:
        _ = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return STATE_MENU
                return STATE_CONTROLS
            if event.type == pygame.MOUSEBUTTONDOWN:
                return STATE_CONTROLS

        screen.blit(preview_bg, (0, 0))

        msg1 = font_title.render("THE COP SPOTTED YOU!", True, (255, 255, 255))
        msg2 = font_title.render("RUN TOWARDS THE TOP OF THE COLOSSEUM", True, (255, 255, 255))
        msg3 = font_title.render("BEFORE HE CATCHES YOU!", True, (255, 255, 255))
        box_w = max(msg1.get_width(), msg2.get_width(), msg3.get_width()) + 80
        box_h = msg1.get_height() + msg2.get_height() + msg3.get_height() + 70
        box_x = (SCREEN_W - box_w) // 2
        box_y = (SCREEN_H - box_h) // 2
        pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(box_x, box_y, box_w, box_h))
        pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(box_x, box_y, box_w, box_h), 2)
        screen.blit(msg1, (box_x + 40, box_y + 20))
        screen.blit(msg2, (box_x + 40, box_y + 20 + msg1.get_height() + 10))
        screen.blit(msg3, (box_x + 40, box_y + 20 + msg1.get_height() + msg2.get_height() + 20))

        draw_center_text(screen, font_hint, "PRESS ANY KEY TO CONTINUE", SCREEN_H - 70, (255, 255, 0))

        pygame.display.flip()
        await asyncio.sleep(0)  #yield to browser each frame

#Runs the controls-reminder screen (shown right before gameplay actually starts)
async def run_controls_screen(screen: pygame.Surface, clock: pygame.time.Clock, background: pygame.Surface) -> str:
    """
    Lists the core controls one last time before the run/timer starts. Any
    key or click starts the actual climb; ESC goes back to the menu.
    """
    preview_bg = pygame.transform.smoothscale(background, (SCREEN_W, SCREEN_H))
    font_title = get_font(70)
    font_body = get_font(42)
    font_luck = get_font(56)
    font_hint = get_font(36)

    controls = [
        "LEFT / RIGHT  —  MOVE",
        "UP / SPACE  —  JUMP",
        "LEFT CLICK  —  BUILD PLATFORM",
        "RIGHT CLICK  —  REMOVE PLATFORM",
    ]

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

        draw_center_text(screen, font_title, "CONTROLS", 110, (255, 255, 255))

        start_y = 260
        line_h = 60
        for i, line in enumerate(controls):
            draw_center_text(screen, font_body, line, start_y + i * line_h, (255, 255, 255))

        draw_center_text(screen, font_luck, "GOOD LUCK!", start_y + len(controls) * line_h + 50, (255, 215, 0))
        draw_center_text(screen, font_hint, "PRESS ANY KEY OR CLICK TO START", SCREEN_H - 70, (255, 255, 0))

        pygame.display.flip()
        await asyncio.sleep(0)  #yield to browser each frame
