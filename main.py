"""
Main entry point for Colosseum Curfew.

This file is intentionally minimal. Its only responsibility
is to start the application. All game logic is handled
inside the GameApp class (defined in game/app.py).

asyncio.run() is required for Pygbag (browser/WebAssembly builds).
"""
import asyncio
import traceback
import pygame  # required so Pygbag preloads the pygame WASM extension
from game.app import GameApp

async def main() -> None:
    """
    Creates an instance of the GameApp class
    and starts the main async execution loop.
    """
    try:
        print("Starting GameApp...")
        await GameApp().run()
    except Exception as e:
        print("FATAL ERROR:", e)
        traceback.print_exc()

asyncio.run(main())
