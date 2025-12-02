from pydantic import BaseModel
from typing import List, Optional


class Feedback(BaseModel):
    post_id: str  # tbody的id，如 "normalthread_16174124"
    title: str  # 帖子标题
    username: str  # 发帖人用户名
    category: str = ""  # 分类，如 "人工服务"、"问题反馈"
    status: str = ""  # 状态，如 "新人帖"、"处理中"
    has_attachment: bool = False  # 是否有附件图片
    created_at: str  # 创建时间，如 "2025-11-30 15:55"
    view_count: int = 0  # 查看数
    reply_count: int = 0  # 回复数
    url: str  # 帖子链接
    content: str = ""  # 帖子内容
    images: List[str] = []  # 图片链接列表

    # 可选字段，根据你的需要添加
    tags: List[str] = []  # 标签（如果需要的话）
    is_notified: bool = False  # 是否已通知（如果需要的话）

    # 数据验证
    @classmethod
    def validate_numbers(cls, v):
        """确保数字字段是整数"""
        if isinstance(v, str):
            try:
                return int(v)
            except (ValueError, TypeError):
                return 0
        return v or 0