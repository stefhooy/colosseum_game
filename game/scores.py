#we import it to read and write scoreboard data in json format
import json
#we check if the files/folders exist
import os
#Type hints for better readability and structure
from typing import List, Dict

#import shared file path settings
from .settings import SCORES_FILE, ASSETS_DIR, DIFFICULTY_MEDIUM

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
