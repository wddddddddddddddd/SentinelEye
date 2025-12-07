"""
仪表盘相关数据模型
"""
from datetime import date
from typing import Dict, List, Optional
from pydantic import BaseModel


class TrendData(BaseModel):
    """趋势数据模型"""
    dates: List[str]
    feedbacks: List[int]  # 注意：这里是feedbacks，不是feedacks
    processed: List[int]
    urgent: List[int]


class KeywordTrigger(BaseModel):
    """关键词触发统计"""
    keyword: str
    count: int
    trend: str  # 'up', 'down', 'stable'


class DashboardStats(BaseModel):
    """仪表盘统计数据模型"""
    # 核心指标
    total_feedbacks: int = 0  # 总反馈数
    pending_feedbacks: int = 0  # 待处理反馈数
    processed_feedbacks: int = 0  # 已处理反馈数
    urgent_feedbacks: int = 0  # 紧急反馈数

    # 今日数据
    today_feedbacks: int = 0  # 今日新增反馈
    today_processed: int = 0  # 今日处理数量
    today_urgent: int = 0  # 今日紧急反馈
    today_pending: int = 0  # 今日待处理数（新增）

    # 与昨日对比
    yesterday_feedbacks: int = 0
    yesterday_processed: int = 0
    yesterday_urgent: int = 0
    yesterday_pending: int = 0  # 新增

    # 差额和增长率
    feedback_growth_rate: float = 0.0  # 反馈增长率（%）
    feedback_difference: int = 0  # 反馈差额（个）
    pending_difference: int = 0  # 待处理差额（个）
    urgent_difference: int = 0  # 紧急反馈差额（个）

    # 最近3天关键词触发
    recent_keyword_triggers: List[KeywordTrigger] = []

    # 最近7天趋势
    recent_trend: TrendData = TrendData(
        dates=[],
        feedbacks=[],  # 修正：feedbacks 不是 feedacks
        processed=[],
        urgent=[]
    )

    # 分类统计
    category_stats: Dict[str, int] = {}

    # 标签统计
    tag_stats: Dict[str, int] = {}


class CategoryStat(BaseModel):
    """分类统计模型"""
    category: str
    count: int
    percentage: float


class DashboardSummary(BaseModel):
    """仪表盘摘要模型"""
    stats: DashboardStats
    recent_feedbacks: List  # 最近反馈列表
    top_categories: List[CategoryStat]  # 主要分类
    top_tags: List[CategoryStat]  # 主要标签