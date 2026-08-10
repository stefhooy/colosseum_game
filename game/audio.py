import os
import sys
import pygame

from .settings import ASSETS_DIR

MUSIC_FILE = "theme_music.ogg"

AUDIO_ENABLED = False
_bg_sound: "pygame.mixer.Sound | None" = None

# True when running inside the browser via Pygbag/WebAssembly
_is_web = sys.platform == "emscripten"


def init_audio() -> None:
    """
    On web: skip pygame mixer entirely — Chrome's SDL audio (ScriptProcessorNode)
    causes stuttering/glitches. We use the browser's native Audio API instead.
    On desktop: initialise pygame mixer normally.
    """
    global AUDIO_ENABLED

    if _is_web:
        AUDIO_ENABLED = True
        return

    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        AUDIO_ENABLED = True
    except pygame.error as e:
        print(f"[Audio disabled] Could not initialize mixer: {e}")
        AUDIO_ENABLED = False


def play_music(loop: bool = True) -> None:
    """
    Loads and plays background music.
    Web: uses the browser's HTMLAudioElement (no SDL involved).
    Desktop: uses pygame.mixer.Sound (pre-loaded into memory, no streaming).
    """
    global _bg_sound

    if not AUDIO_ENABLED:
        return

    if _is_web:
        _web_play(loop)
        return

    path = os.path.join(ASSETS_DIR, MUSIC_FILE)
    if os.path.exists(path):
        try:
            _bg_sound = pygame.mixer.Sound(path)
            _bg_sound.set_volume(0.5)
            _bg_sound.play(-1 if loop else 0)
        except pygame.error as e:
            print(f"[Audio disabled] Could not play music: {e}")


def _web_play(loop: bool) -> None:
    """
    Plays music via the browser's native Audio API.
    The OGG file must be served as a plain HTTP file alongside index.html —
    it cannot be inside the .apk bundle when accessed from JavaScript.
    """
    try:
        from platform import window
        loop_str = "true" if loop else "false"
        window.eval(
            f"(function(){{"
            f"  if(window._bgMusic){{window._bgMusic.pause();}}"
            f"  var a=new Audio('{MUSIC_FILE}');"
            f"  a.loop={loop_str};"
            f"  a.volume=0.5;"
            f"  window._bgMusic=a;"
            f"  a.play().catch(function(e){{console.warn('audio:',e);}});"
            f"}})();"
        )
    except Exception as e:
        print(f"[Web audio] {e}")


def stop_music() -> None:
    """
    Stops currently playing music.
    """
    if not AUDIO_ENABLED:
        return

    if _is_web:
        try:
            from platform import window
            window.eval(
                "if(window._bgMusic){window._bgMusic.pause();"
                "window._bgMusic.currentTime=0;}"
            )
        except Exception as e:
            print(f"[Web audio] {e}")
        return

    if _bg_sound is not None:
        _bg_sound.fadeout(300)
