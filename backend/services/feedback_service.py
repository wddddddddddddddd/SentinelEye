# services/feedback_service.py
from typing import List, Optional
from datetime import datetime
from models.feedback import Feedback
from core.mongo_client import mongodb_client


def load_feedback_list(limit: Optional[int] = 5) -> List[Feedback]:
    """
    从 MongoDB 加载反馈数据

    Args:
        limit: 限制返回的数据条数，None 表示返回所有

    Returns:
        List[Feedback]: 反馈列表
    """
    try:
        cursor = mongodb_client.feedbacks.find(
            {},
            sort=[("created_at_timestamp", -1)]
        )
        if limit is not None:
            cursor = cursor.limit(limit)

        feedback_list = [Feedback(**item) for item in cursor]
        return feedback_list
    except Exception as e:
        # 出错时返回空列表
        from core.mongo_client import logger
        logger.error(f"[FeedbackService] 加载反馈失败: {e}")
        return []


def load_all_feedbacks() -> List[Feedback]:
    """加载所有反馈数据"""
    return load_feedback_list(None)
