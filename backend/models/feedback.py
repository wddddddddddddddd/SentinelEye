# models/feedback.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId


class FeedbackInDB(BaseModel):
    """MongoDB中存储的反馈文档结构"""
    post_id: str
    title: str
    username: str
    category: str = ""
    status: str = ""
    has_attachment: bool = False
    created_at: datetime  # 注意：这里是datetime，不是str！
    view_count: int = 0
    reply_count: int = 0
    url: str
    content: str = ""
    images: List[str] = []
    tags: List[str] = []
    crawl_time: Optional[datetime] = None
    
    class Config:
        # 允许使用别名
        allow_population_by_field_name = True
        # 处理ObjectId
        json_encoders = {ObjectId: str}