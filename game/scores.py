#we import it to read and write scoreboard data in json format
import json
#we check if the files/folders exist
import os
#used to run the network call in the background so it never freezes gameplay
import asyncio
#used to make the actual HTTP request to Supabase on desktop
import urllib.request
import sys
#Type hints for better readability and structure
from typing import List, Dict, Optional

#import shared file path settings
from .settings import (
    SCORES_FILE, ASSETS_DIR, DIFFICULTY_MEDIUM,
    SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SCORES_TABLE, SUPABASE_REQUEST_TIMEOUT,
)

#True when running inside the browser via Pygbag/WebAssembly — same check
#audio.py already uses, since the browser can't make raw HTTP/socket
#connections the way desktop Python can
_is_web = sys.platform == "emscripten"

def load_scores() -> List[Dict]:
    """
    Here we will load the scoreboard data into the JSON file.
    if the file doesn't exist or is invalid, we will retun an empty list.
    """
    #If the scores file doesn't exist, return an empty list
    if not os.path.exists(SCORES_FILE):
        return []
    try:
        #If it exist we will open the file and load it
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        #Make sure the data is actually a list before returning
        return data if isinstance(data, list) else []
    except Exception:
        #if ever something goes wrong (corrupted file or invalid json)
        #we will return an empty list instead of having a crash in the game
        return []

def save_scores(scores: List[Dict]) -> None:
    """
    Saving the current scoreboard list into the jSON file.
    In browser builds, file writes may not persist but will not crash the game.
    """
    try:
        #make sure the folder assets exists
        os.makedirs(ASSETS_DIR, exist_ok=True)
        #Writing the list of scores with indentation for readability
        with open(SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(scores, f, indent=2)
    except Exception:
        #In browser/WASM environments, file writes may fail silently
        pass

def add_score(player_name: str, time_seconds: float, difficulty: str = DIFFICULTY_MEDIUM) -> None:
    """
    Adding the score entry (tagged with its difficulty) + sorting it by fastest
    time. Each difficulty keeps its own top 10 — a Hard run never bumps an
    Easy run off the list and vice versa.
    """
    #load every existing score (all difficulties, one shared JSON file)
    scores = load_scores()
    #add the new score as a dictionnary, tagged with which difficulty it was run on
    scores.append({"name": player_name, "time": float(time_seconds), "difficulty": difficulty})
    #Group scores by difficulty so each bucket gets trimmed to its own top 10,
    #instead of one difficulty's scores crowding out another's
    by_difficulty: Dict[str, List[Dict]] = {}
    for s in scores:
        by_difficulty.setdefault(s.get("difficulty", DIFFICULTY_MEDIUM), []).append(s)
    trimmed: List[Dict] = []
    for entries in by_difficulty.values():
        #Sorting the scores in ascending order, having the fastest scores first shown
        entries.sort(key=lambda x: x["time"])
        trimmed.extend(entries[:10])
    #saving the recombined scores back into the JSON file
    save_scores(trimmed)

def load_scores_by_difficulty(difficulty: str) -> List[Dict]:
    """
    Returns just the scores for one difficulty, fastest time first. Used by
    the scoreboard screen so it can show one bucket at a time.
    """
    scores = [s for s in load_scores() if s.get("difficulty") == difficulty]
    scores.sort(key=lambda x: x["time"])
    return scores

#--- Online (Supabase) leaderboard ---
#Everything below talks to Supabase's REST API so players share ONE
#leaderboard instead of everyone having their own local scores.json. The
#local functions above are untouched and still run unconditionally — think
#of Supabase as an added, best-effort layer on top, not a replacement:
#if the network is unreachable or Supabase isn't configured, the game keeps
#working exactly as it did before this feature existed.

def _supabase_headers(for_write: bool = False) -> Dict[str, str]:
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    }
    if for_write:
        headers["Content-Type"] = "application/json"
        #return=minimal: we don't need the inserted row echoed back, just success/failure
        headers["Prefer"] = "return=minimal"
    return headers

def _supabase_select_url(difficulty: str, limit: int) -> str:
    #PostgREST query syntax: select which columns, filter by difficulty,
    #sort fastest-first, cap to `limit` rows — the server does the sorting
    #and trimming, not us
    return (
        f"{SUPABASE_URL}/rest/v1/{SUPABASE_SCORES_TABLE}"
        f"?select=name,time,difficulty&difficulty=eq.{difficulty}&order=time.asc&limit={limit}"
    )

#Desktop-only: these two do the actual blocking network call. They're called
#through loop.run_in_executor (see add_score_online/load_scores_online_by_difficulty
#below) so the blocking wait happens on a background thread, not the game loop.
def _desktop_post_score(player_name: str, time_seconds: float, difficulty: str) -> bool:
    body = json.dumps({
        "name": player_name,
        "time": float(time_seconds),
        "difficulty": difficulty,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/{SUPABASE_SCORES_TABLE}",
        data=body,
        method="POST",
        headers=_supabase_headers(for_write=True),
    )
    try:
        with urllib.request.urlopen(req, timeout=SUPABASE_REQUEST_TIMEOUT) as resp:
            return 200 <= resp.status < 300
    except Exception as e:
        #No internet, Supabase down, misconfigured key... none of these
        #should ever crash the game — the local scores.json save already
        #happened regardless, so the run's result is never lost
        print(f"[Supabase] Could not submit score online: {e}")
        return False

def _desktop_get_scores(difficulty: str, limit: int) -> Optional[List[Dict]]:
    req = urllib.request.Request(
        _supabase_select_url(difficulty, limit),
        method="GET",
        headers=_supabase_headers(),
    )
    try:
        with urllib.request.urlopen(req, timeout=SUPABASE_REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data if isinstance(data, list) else None
    except Exception as e:
        print(f"[Supabase] Could not load scores online: {e}")
        return None

#Web-only: the browser can't open raw sockets, so urllib doesn't work here.
#Instead we hand a small JS snippet to the browser's own Fetch API (same
#window.eval technique audio.py already uses for web playback) and await
#its result via pygbag's `platform.jsiter` bridge. This mirrors the pattern
#pygbag itself ships internally for exactly this situation.
_WEB_FETCH_JS = """
window.SupabaseFetch = {}
window.SupabaseFetch.GET = function* GET(url, apikey) {
    var request = new Request(url, {
        method: 'GET',
        headers: {'apikey': apikey, 'Authorization': 'Bearer ' + apikey}
    });
    var content = 'undefined';
    fetch(request)
        .then(resp => resp.text())
        .then((resp) => { content = resp; })
        .catch(err => { console.log('Supabase GET error:', err); content = '[]'; });
    while (content == 'undefined') { yield; }
    yield content;
}
window.SupabaseFetch.POST = function* POST(url, apikey, data) {
    var request = new Request(url, {
        method: 'POST',
        headers: {
            'apikey': apikey,
            'Authorization': 'Bearer ' + apikey,
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        },
        body: data
    });
    var content = 'undefined';
    fetch(request)
        .then(resp => { content = resp.ok ? 'ok' : 'error'; })
        .catch(err => { console.log('Supabase POST error:', err); content = 'error'; });
    while (content == 'undefined') { yield; }
    yield content;
}
"""
_web_fetch_ready = False

def _ensure_web_fetch_ready() -> None:
    #Only needs to hand the JS snippet to the browser once per run, not on
    #every single request
    global _web_fetch_ready
    if _web_fetch_ready:
        return
    from platform import window
    window.eval(_WEB_FETCH_JS)
    _web_fetch_ready = True

async def _web_post_score(player_name: str, time_seconds: float, difficulty: str) -> bool:
    from platform import window, jsiter
    _ensure_web_fetch_ready()
    body = json.dumps({"name": player_name, "time": float(time_seconds), "difficulty": difficulty})
    try:
        result = await jsiter(window.SupabaseFetch.POST(
            f"{SUPABASE_URL}/rest/v1/{SUPABASE_SCORES_TABLE}", SUPABASE_ANON_KEY, body,
        ))
        return result == "ok"
    except Exception as e:
        print(f"[Supabase] Could not submit score online: {e}")
        return False

async def _web_get_scores(difficulty: str, limit: int) -> Optional[List[Dict]]:
    from platform import window, jsiter
    _ensure_web_fetch_ready()
    try:
        result = await jsiter(window.SupabaseFetch.GET(_supabase_select_url(difficulty, limit), SUPABASE_ANON_KEY))
        data = json.loads(result)
        return data if isinstance(data, list) else None
    except Exception as e:
        print(f"[Supabase] Could not load scores online: {e}")
        return None

#--- Public entry points used by app.py / screens.py ---

async def add_score_online(player_name: str, time_seconds: float, difficulty: str) -> bool:
    """
    Best-effort submit to the shared Supabase leaderboard. Meant to be
    fired off as a background task (see app.py) right alongside the
    unconditional local add_score() call above — never awaited in a way
    that could stall gameplay, and never raises.
    """
    if _is_web:
        return await _web_post_score(player_name, time_seconds, difficulty)
    #urllib is blocking, so run it on a worker thread rather than freezing
    #the whole async event loop (and therefore the game) while it waits
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _desktop_post_score, player_name, time_seconds, difficulty)

async def load_scores_online_by_difficulty(difficulty: str, limit: int = 10) -> Optional[List[Dict]]:
    """
    Best-effort fetch of one difficulty's leaderboard from Supabase. Returns
    None (never an empty list) on failure specifically so the scoreboard
    screen can tell "genuinely no scores yet" apart from "couldn't reach
    Supabase" and fall back to the local leaderboard in the second case.
    """
    if _is_web:
        return await _web_get_scores(difficulty, limit)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _desktop_get_scores, difficulty, limit)
