# services/feedback_service.py
from typing import List, Optional
from datetime import datetime, date, timedelta
# 修改为从 pymongo 导入
from bson import ObjectId

from backend.core.mongo_client import feedbacks_collection
from backend.models.feedback import FeedbackInDB
from backend.schemas.feedback import FeedbackResponse


def _format_datetime(dt: datetime) -> str:
    """格式化datetime为字符串"""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return ""


def convert_to_response(feedback_data: dict) -> FeedbackResponse:
    """
    将MongoDB文档转换为API响应格式
    
    Args:
        feedback_data: MongoDB查询结果
        
    Returns:
        API响应格式的数据
    """
    # 将MongoDB的_id转换为字符串id
    feedback_dict = dict(feedback_data)
    
    # 处理时间格式
    created_at_str = _format_datetime(feedback_dict.get('created_at'))
    crawl_time_str = _format_datetime(feedback_dict.get('crawl_time'))
    
    return FeedbackResponse(
        id=str(feedback_dict.get('_id', '')),
        post_id=feedback_dict.get('post_id', ''),
        title=feedback_dict.get('title', ''),
        username=feedback_dict.get('username', ''),
        category=feedback_dict.get('category', ''),
        status=feedback_dict.get('status', ''),
        has_attachment=feedback_dict.get('has_attachment', False),
        created_at=created_at_str,
        view_count=feedback_dict.get('view_count', 0),
        reply_count=feedback_dict.get('reply_count', 0),
        url=feedback_dict.get('url', ''),
        content=feedback_dict.get('content', ''),
        images=feedback_dict.get('images', []),
        tags=feedback_dict.get('tags', []),
        crawl_time=crawl_time_str
    )


def get_recent_feedbacks(limit: int = 5) -> List[FeedbackResponse]:
    """
    获取最近的反馈
    
    Args:
        limit: 返回条数，默认5条
        
    Returns:
        反馈列表
    """
    try:
        # 按created_at倒序排序，获取最新的
        cursor = feedbacks_collection.find().sort("created_at", -1).limit(limit)
        
        feedbacks = []
        for item in cursor:
            feedbacks.append(convert_to_response(item))
        
        return feedbacks
        
    except Exception as e:
        print(f"[错误] 获取最近反馈失败: {e}")
        return []


def get_all_feedbacks() -> List[FeedbackResponse]:
    """
    获取所有反馈
    
    Returns:
        所有反馈列表
    """
    try:
        cursor = feedbacks_collection.find().sort("created_at", -1)
        
        feedbacks = []
        for item in cursor:
            feedbacks.append(convert_to_response(item))
        
        return feedbacks
        
    except Exception as e:
        print(f"[错误] 获取所有反馈失败: {e}")
        return []


def get_feedback_by_id(feedback_id: str) -> Optional[FeedbackResponse]:
    """
    根据ID获取单个反馈
    
    Args:
        feedback_id: 反馈ID
        
    Returns:
        单个反馈详情，不存在返回None
    """
    try:
        # 验证ObjectId格式
        if not ObjectId.is_valid(feedback_id):
            return None
            
        item = feedbacks_collection.find_one({"_id": ObjectId(feedback_id)})
        
        if item:
            return convert_to_response(item)
        return None
        
    except Exception as e:
        print(f"[错误] 获取反馈详情失败: {e}")
        return None


def get_feedback_count() -> int:
    """
    获取反馈总数
    
    Returns:
        总数
    """
    try:
        return feedbacks_collection.count_documents({})
    except Exception as e:
        print(f"[错误] 获取反馈总数失败: {e}")
        return 0
    

def get_feedbacks_before_date(
    target_date: date,
    include_target_day: bool = True
) -> List[dict]:
    """
    获取指定日期之前（包含当天）的所有帖子原始数据
    
    Args:
        target_date: 目标日期（datetime.date对象）
        include_target_day: 是否包含目标当天，默认为True
        
    Returns:
        MongoDB原始文档列表（字典格式），不经过Pydantic转换
    """
    try:
        # 计算时间范围
        if include_target_day:
            # 包含当天：小于等于目标日期的23:59:59
            end_date = datetime.combine(
                target_date + timedelta(days=1),  # 第二天
                datetime.min.time()
            )  # 第二天的00:00:00
            query = {"created_at": {"$lt": end_date}}
        else:
            # 不包含当天：小于目标日期的00:00:00
            start_date = datetime.combine(target_date, datetime.min.time())
            query = {"created_at": {"$lt": start_date}}
        
        print(f"[DEBUG] 查询日期之前的数据: target_date={target_date}, "
              f"include_target_day={include_target_day}, query={query}")
        
        # 获取原始数据（不转换为Response模型，用于数据分析）
        cursor = feedbacks_collection.find(query).sort("created_at", 1)
        
        result = []
        for item in cursor:
            # 转换为字典，处理ObjectId
            item_dict = dict(item)
            item_dict['_id'] = str(item_dict['_id'])
            result.append(item_dict)
        
        print(f"[DEBUG] 找到 {len(result)} 条记录")
        return result
        
    except Exception as e:
        print(f"[错误] 获取日期之前数据失败: {e}")
        return []


def get_feedbacks_on_date(target_date: date) -> List[dict]:
    """
    获取指定日期当天的所有帖子原始数据
    
    Args:
        target_date: 目标日期（datetime.date对象）
        
    Returns:
        当天帖子的原始文档列表
    """
    try:
        # 计算当天的开始和结束时间
        start_date = datetime.combine(target_date, datetime.min.time())
        end_date = datetime.combine(
            target_date + timedelta(days=1),
            datetime.min.time()
        )
        
        query = {
            "created_at": {
                "$gte": start_date,
                "$lt": end_date
            }
        }
        
        print(f"[DEBUG] 查询当天数据: target_date={target_date}, "
              f"range={start_date} to {end_date}")
        
        cursor = feedbacks_collection.find(query).sort("created_at", 1)
        
        result = []
        for item in cursor:
            item_dict = dict(item)
            item_dict['_id'] = str(item_dict['_id'])
            result.append(item_dict)
        
        print(f"[DEBUG] 找到 {len(result)} 条当天记录")
        return result
        
    except Exception as e:
        print(f"[错误] 获取当天数据失败: {e}")
        return []


def get_feedbacks_in_date_range(
    start_date: date,
    end_date: date,
    include_end_day: bool = True
) -> List[dict]:
    try:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        
        if include_end_day:
            # 包含结束当天：到 end_date + 1 的 00:00:00
            end_datetime = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        else:
            # 不包含结束当天
            end_datetime = datetime.combine(end_date, datetime.min.time())
        
        query = {
            "created_at": {
                "$gte": start_datetime,
                "$lt": end_datetime
            }
        }
        
        print(f"[DEBUG] 查询日期范围: {start_date} ~ {end_date} "
              f"(include_end={include_end_day}), query={query}")
        
        cursor = feedbacks_collection.find(query).sort("created_at", 1)
        
        result = []
        for item in cursor:
            item_dict = dict(item)
            item_dict['_id'] = str(item_dict['_id'])
            result.append(item_dict)
        
        print(f"[DEBUG] 找到 {len(result)} 条记录")
        return result
        
    except Exception as e:
        print(f"[错误] 获取日期范围数据失败: {e}")
        return []


def get_feedbacks_by_date_with_stats(target_date: date) -> dict:
    """
    获取指定日期的数据并包含统计信息（示例使用）
    
    Args:
        target_date: 目标日期
        
    Returns:
        包含数据和统计信息的字典
    """
    try:
        # 获取当天数据
        daily_data = get_feedbacks_on_date(target_date)
        
        # 获取日期之前的数据（不包含当天）
        before_data = get_feedbacks_before_date(
            target_date, 
            include_target_day=False
        )
        
        # 计算统计信息
        stats = {
            "date": target_date.isoformat(),
            "daily_count": len(daily_data),
            "total_before_count": len(before_data),
            "categories_daily": {},
            "categories_before": {}
        }
        
        # 按分类统计当天数据
        for item in daily_data:
            category = item.get('category', '未分类')
            stats["categories_daily"][category] = \
                stats["categories_daily"].get(category, 0) + 1
        
        # 按分类统计之前数据
        for item in before_data:
            category = item.get('category', '未分类')
            stats["categories_before"][category] = \
                stats["categories_before"].get(category, 0) + 1
        
        return {
            "date": target_date.isoformat(),
            "daily_data": daily_data,
            "stats": stats
        }
        
    except Exception as e:
        print(f"[错误] 获取日期统计失败: {e}")
        return {"error": str(e)}