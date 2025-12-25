# schemas/feedback.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class FeedbackResponse(BaseModel):
    """API返回的反馈数据格式"""
    id: str
    post_id: str
    title: str
    username: str
    category: str
    status: str
    has_attachment: bool
    created_at: str  # 格式化成字符串返回给前端
    view_count: int
    reply_count: int
    url: str
    content: str
    images: List[str]
    tags: List[str]
    crawl_time: Optional[str] = None