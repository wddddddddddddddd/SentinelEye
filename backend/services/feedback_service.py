# services/feedback_service.py
from pathlib import Path
import json
from typing import List
from datetime import datetime
from models.feedback import Feedback
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "360_forum.json"


def load_feedback_list(limit: Optional[int] = None) -> List[Feedback]:
    """
    加载反馈数据

    Args:
        limit: 限制返回的数据条数，None表示返回所有

    Returns:
        List[Feedback]: 反馈列表
    """
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 按时间排序
    data_sorted = sorted(
        data,
        key=lambda x: datetime.strptime(x["created_at"], "%Y-%m-%d %H:%M"),
        reverse=True
    )

    if limit is not None:
        latest = data_sorted[:limit]
    else:
        latest = data_sorted

    return [Feedback(**item) for item in latest]


def load_all_feedbacks() -> List[Feedback]:
    """加载所有反馈数据"""
    return load_feedback_list(None)