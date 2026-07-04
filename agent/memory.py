import json
import os

MEMORY_FILE = "data/memory.json"

DEFAULT_MEMORY = {
    "risk_preference": "balanced",
    "last_race": None,
    "runs": 0
}


def load_memory() -> dict:
    """Load user preferences from disk."""
    os.makedirs("data", exist_ok=True)
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_MEMORY.copy()


def save_memory(preference: str, race_name: str = None) -> None:
    """Persist user preference to disk."""
    os.makedirs("data", exist_ok=True)
    memory = load_memory()
    memory["risk_preference"] = preference
    memory["runs"] = memory.get("runs", 0) + 1
    if race_name:
        memory["last_race"] = race_name
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)