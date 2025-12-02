# services/feedback_service.py
from pathlib import Path
import json
from typing import List
from datetime import datetime
from models.feedback import Feedback

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "360_forum.json"

def load_feedback_list(limit: int = 5) -> List[Feedback]:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 你 JSON 里的字段是 "created_at"
    data_sorted = sorted(
        data,
        key=lambda x: datetime.strptime(x["created_at"], "%Y-%m-%d %H:%M"),
        reverse=True
    )

    latest = data_sorted[:limit]
    return [Feedback(**item) for item in latest]
