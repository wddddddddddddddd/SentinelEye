"""
仪表盘数据服务
"""
from datetime import datetime, date, timedelta
from backend.services.feedback_service import get_feedbacks_on_date
from backend.services.keyword_service import load_keywords


def get_keyword_triggers_stats(days=3):
    """
    统计近N天的关键词触发情况
    
    Args:
        days: 统计天数，默认3天
        
    Returns:
        list: 关键词触发统计列表
    """
    # 获取近N天的反馈数据
    keyword_stats = []
    
    # 获取近N天的所有反馈
    recent_feedbacks = get_recent_feedbacks(days)
    
    # 加载关键词列表
    keywords = load_keywords()
    print("关键词列表:", keywords)  # ['核晶防护', '游戏闪退', '蓝屏']
    
    # 统计每个关键词在近N天的触发次数
    for keyword_name in keywords:
        count = 0
        
        for feedback in recent_feedbacks:
            # 获取标题和内容
            title = feedback.get('title', '').lower()
            content = feedback.get('content', '').lower()
            keyword_lower = keyword_name.lower()
            
            # 检查标题或内容中是否包含关键词（不区分大小写）
            if keyword_lower in title or keyword_lower in content:
                count += 1
        
        # 判断趋势（这里简化处理，只返回有触发的关键词）
        trend = "stable"  # 默认稳定
        if count > 0:
            trend = "up"  # 有触发就标记为上升
        
        # 只返回有触发的关键词
        if count > 0:
            keyword_stats.append({
                "keyword": keyword_name,
                "count": count,
                "trend": trend
            })
    
    # 按触发次数降序排序
    keyword_stats.sort(key=lambda x: x['count'], reverse=True)
    
    return keyword_stats


def get_recent_feedbacks(days):
    """
    获取近N天的反馈数据
    
    Args:
        days: 天数
        
    Returns:
        list: 反馈数据列表
    """
    recent_feedbacks = []
    
    for i in range(days):
        target_date = date.today() - timedelta(days=i)
        day_feedbacks = get_feedbacks_on_date(target_date)
        recent_feedbacks.extend(day_feedbacks)
    
    return recent_feedbacks


def today_feedbacks_stats():
    """
    今日反馈 对比 昨天变化
    """
    # 获取日期
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # 获取对应日期的帖子信息
    today_feedbacks = get_feedbacks_on_date(today)
    yesterday_feedbacks = get_feedbacks_on_date(yesterday)
    
    # 统计帖子数量
    count_today_feedbacks = len(today_feedbacks)
    count_yesterday_feedbacks = len(yesterday_feedbacks)
    
    # 较昨日增减数量（可为负数）
    pending_difference = count_today_feedbacks - count_yesterday_feedbacks
    
    # 今日增长率（百分比，可为负数）
    # 处理除零错误（昨天没有反馈的情况）
    if count_yesterday_feedbacks > 0:
        feedback_growth_rate = (pending_difference / count_yesterday_feedbacks) * 100
    else:
        # 如果昨天没有反馈，今天有反馈则增长率为100%，否则为0%
        feedback_growth_rate = 100 if count_today_feedbacks > 0 else 0
    
    # 今日紧急反馈数量（根据您的数据结构，需要从content中分析）
    today_urgent = 0
    for feedback in today_feedbacks:
        content = feedback.get('content', '').lower()
        # 根据关键词判断是否为紧急反馈
        urgent_keywords = ['蓝屏', '死机', '崩溃', '劫持', '病毒', '紧急', '急', 'crash', 'error']
        if any(keyword in content for keyword in urgent_keywords):
            today_urgent += 1
    
    # 今日待处理问题数量（假设状态为'pending'或'未处理'的）
    today_pending = len([f for f in today_feedbacks if f.get('status') not in ['已解决', '确认解决', '已答复']])

    yesterday_pending = len([f for f in yesterday_feedbacks if f.get('status') not in ['已解决', '确认解决', '已答复']])
    
    # 统计近3天关键词触发情况
    recent_keyword_triggers = get_keyword_triggers_stats(days=3)
    
    # 输出结果
    result = {
        "today_feedbacks": count_today_feedbacks,
        "feedback_growth_rate": round(feedback_growth_rate, 2),
        "today_pending": today_pending,
        "yesterday_pending": yesterday_pending,
        "pending_difference": pending_difference,
        "today_urgent": today_urgent,
        "recent_keyword_triggers": recent_keyword_triggers
    }
    
    return result

def get_chart_data(days=7):
    """
    获取图表数据（近N天的分类分布和趋势）
    """
    recent_feedbacks = get_recent_feedbacks(days)
    
    # 1. 分类数据统计
    category_count = {}
    for feedback in recent_feedbacks:
        raw_category = feedback.get('category')
        category = raw_category if raw_category and raw_category.strip() else '未分类'
        category_count[category] = category_count.get(category, 0) + 1
    
    category_data = []
    for category, count in category_count.items():
        category_data.append({
            "name": category,
            "value": count
        })
    
    # 2. 趋势数据统计（每日反馈数）
    trend_data = {
        "dates": [],
        "feedbacks": []
    }
    
    # 生成最近N天的日期列表
    for i in range(days-1, -1, -1):
        target_date = date.today() - timedelta(days=i)
        day_feedbacks = get_feedbacks_on_date(target_date)
        
        trend_data["dates"].append(target_date.strftime("%m-%d"))
        trend_data["feedbacks"].append(len(day_feedbacks))
    
    # 3. 总反馈数
    total_feedbacks = len(recent_feedbacks)
    
    return {
        "total_feedbacks": total_feedbacks,
        "category_data": category_data,
        "trend_data": trend_data
    }


# 测试代码
if __name__ == "__main__":
    print(today_feedbacks_stats())