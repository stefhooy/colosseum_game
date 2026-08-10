#we import it to read and write scoreboard data in json format
import json
#we check if the files/folders exist
import os
#Type hints for better readability and structure
from typing import List, Dict

#import shared file path settings
from .settings import SCORES_FILE, ASSETS_DIR

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

def add_score(player_name: str, time_seconds: float) -> None:
    """
    Adding the score entries + sorting it by fastest time.
    Only show the top 10 best results
    """
    #load the existing scores
    scores = load_scores()
    #add new score as a dictionnary
    scores.append({"name": player_name, "time": float(time_seconds)})
    #Sorting the scores in asceding having the fastest scores first shown
    scores.sort(key=lambda x: x["time"])
    #keep the top 10 best
    scores = scores[:10]
    #saving the scores back in the JSON file
    save_scores(scores)
