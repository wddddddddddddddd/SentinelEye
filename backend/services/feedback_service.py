import json
from pathlib import Path
from typing import List
from models.feedback import Feedback

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "360_forum.json"

def load_feedback_list() -> List[Feedback]:
    if not DATA_PATH.exists():
        return []

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    return [Feedback(**item) for item in raw_data]
