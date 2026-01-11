from datetime import datetime, timedelta
import random
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from backend.services.feedback_service import get_feedbacks_before_date, get_feedbacks_in_date_range, get_analyzed_feedbacks_in_date_range
from collections import Counter, defaultdict
import re
from backend.services.keyword_service import load_keywords
# 预定义颜色列表（可以扩展）
PREDEFINED_COLORS = [
    "#10b981",  # emerald
    "#f59e0b",  # amber
    "#3b82f6",  # blue
    "#8b5cf6",  # violet
    "#ef4444",  # red
    "#06b6d4",  # cyan
    "#f97316",  # orange
    "#84cc16",  # lime
]


def get_current_week_range(date_str=None, date_format="%Y.%m.%d", output_format="%Y.%m.%d"):
    """
    获取指定日期所在周的日期范围

    参数:
        date_str: 指定日期字符串，如果为None则使用当前日期
        date_format: 输入日期的格式
        output_format: 输出日期的格式

    返回:
        字符串: "起始日期~结束日期"
    """
    # 获取目标日期
    if date_str:
        target_date = datetime.strptime(date_str, date_format)
    else:
        target_date = datetime.now()

    # 计算本周的周一（周一是第一天）
    week_start = target_date - timedelta(days=target_date.weekday())
    # 计算本周的周日
    week_end = week_start + timedelta(days=6)

    # 格式化输出
    start_str = week_start.strftime(output_format)
    end_str = week_end.strftime(output_format)

    week_datetime_info = {
        'week_start_date': start_str,
        'week_end_date': end_str
    }
    return week_datetime_info

def str_to_date(date_str):
    """
    将字符串转换为Python的date类型
    
    参数:
    date_str (str): 日期字符串，格式应为YYYY-MM-DD
    
    返回:
    datetime.date: 转换后的date对象
    """
    try:
        # 将字符串解析为datetime对象，然后转换为date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        return date_obj
    except ValueError as e:
        raise ValueError(f"日期格式错误: {date_str}。请使用YYYY-MM-DD格式。") from e

class DateRange(BaseModel):
    start_date: str
    end_date: str


def generate_overview(start_date: str, end_date: str) -> Dict[str, Any]:
    """生成概览统计数据"""

    start_date = str_to_date(start_date)
    end_date = str_to_date(end_date)
    last_start_date = start_date - timedelta(days=7)
    last_end_date = end_date - timedelta(days=7)
    this_week_feedbacks = get_feedbacks_in_date_range(start_date, end_date)
    # print(this_week_feedbacks)
    last_week_feedbacks = get_feedbacks_in_date_range(last_start_date, last_end_date)

    this_week_total_feedback = len(this_week_feedbacks)
    this_week_pending_feedback = len([f for f in this_week_feedbacks if f.get('status') not in ['已解决', '确认解决', '已答复']])
    this_week_resolved_feedback = len([f for f in this_week_feedbacks if f.get('status') in ['已解决', '确认解决', '已答复']])

    last_week_total_feedback = len(last_week_feedbacks)
    last_week_pending_feedback = len([f for f in last_week_feedbacks if f.get('status') not in ['已解决', '确认解决', '已答复']])
    last_week_resolved_feedback = len([f for f in last_week_feedbacks if f.get('status') in ['已解决', '确认解决', '已答复']])

    feedback_growth = round((this_week_total_feedback - last_week_total_feedback / last_week_total_feedback * 100), 2) if last_week_total_feedback > 0 else 0.0

    pending_change = this_week_pending_feedback - last_week_pending_feedback
    resolution_rate = round((this_week_resolved_feedback - last_week_resolved_feedback / last_week_resolved_feedback * 100), 2) if last_week_resolved_feedback > 0 else 0.0

    this_week_ai_check = len(get_analyzed_feedbacks_in_date_range(start_date, end_date))
    ai_check_week_percentage = round((this_week_ai_check / this_week_total_feedback  * 100), 2) if this_week_total_feedback > 0 else 0.0

    return {
        "total_feedback": this_week_total_feedback,
        "resolved_feedback": this_week_resolved_feedback,
        "pending_feedback": this_week_pending_feedback,
        "this_week_ai_check": this_week_ai_check,
        "feedback_growth": feedback_growth,
        "pending_change": pending_change,
        "resolution_rate": resolution_rate,
        "ai_check_week_percentage": ai_check_week_percentage,
        # "average_response_time": f"{random.randint(1, 6)}小时",
        # "user_satisfaction": f"{random.randint(80, 98)}%"
    }

def generate_type_distribution(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """生成反馈类型分布"""

    start_date_dt = str_to_date(start_date)
    end_date_dt = str_to_date(end_date)
    this_week_feedbacks = get_feedbacks_in_date_range(start_date_dt, end_date_dt)  # 建议改用这个更清晰的函数
    
    categories = []
    for fb in this_week_feedbacks:
        cat = fb.get("category", "").strip()  # 去掉前后空格
        if not cat:  # 如果为空字符串或None
            cat = "未知"
        categories.append(cat)
    
    counter = Counter(categories)
    
    distribution = []
    for i, (category, count) in enumerate(counter.most_common()):
        color = PREDEFINED_COLORS[i % len(PREDEFINED_COLORS)]
        distribution.append({
            "name": category,
            "value": count,
            "color": color
        })
    
    return distribution

def generate_trend(start_date: str, end_date: str) -> Dict[str, Any]:
    """生成周趋势数据：Top3 类型在日期范围内的每日数量"""
    
    # 解析日期
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    # 获取日期范围内的所有反馈（包含结束日）
    feedbacks = get_feedbacks_in_date_range(start_dt, end_dt, include_end_day=True)
    
    # 清理 category：空字符串或 None 转为 "未知"
    def normalize_category(cat: str) -> str:
        return cat.strip() if cat and str(cat).strip() else "未知"
    
    # 统计总数量，找出 Top3
    category_counter = Counter(normalize_category(fb.get("category", "")) for fb in feedbacks)
    top3_categories = [item[0] for item in category_counter.most_common(3)]
    
    # 如果不足3个，用 "未知" 补齐（可选，这里直接取实际有的）
    # top3_categories = top3_categories[:3]  # 自然最多3个
    
    # 生成日期序列（最多7天）
    dates = []
    current = start_dt
    while current <= end_dt and len(dates) < 7:
        dates.append(current.strftime("%m-%d"))
        current += timedelta(days=1)
    
    # 按天按类别统计数量
    daily_stats = defaultdict(lambda: defaultdict(int))
    for fb in feedbacks:
        created = fb["created_at"]
        if isinstance(created, dict):  # 如果是 {"$date": ...} 格式，需要处理（建议提前转好）
            continue  # 或用 parser 解析，这里假设已经是 datetime
        day = created.date()
        if start_dt <= day <= end_dt:
            cat = normalize_category(fb.get("category", ""))
            daily_stats[day.strftime("%m-%d")][cat] += 1
    
    # 构建 series
    series = []
    predefined_colors = ["#10b981", "#f59e0b", "#3b82f6"]  # 绿色、橙色、蓝色
    for i, cat in enumerate(top3_categories):
        data = [daily_stats[date].get(cat, 0) for date in dates]
        series.append({
            "name": cat,
            "data": data,
            "color": predefined_colors[i % len(predefined_colors)]
        })
    
    return {
        "dates": dates,
        "series": series
    }

def generate_category_analysis(start_date: str | None = None, end_date: str | None = None) -> List[Dict[str, Any]]:
    """生成分类分析数据：取数量前8的类型（不足则全部）"""
    
    if start_date and end_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        feedbacks = get_feedbacks_in_date_range(start_dt, end_dt, include_end_day=True)
    else:
        # 如果不传日期，就默认周
        default_week_dt = get_current_week_range()
        start_dt = datetime.strptime(default_week_dt['week_start_date'], "%Y.%m.%d").date()
        end_dt = datetime.strptime(default_week_dt['week_end_date'], "%Y.%m.%d").date()
        feedbacks = get_feedbacks_in_date_range(start_dt, end_dt, include_end_day=True)

    
    def normalize_category(cat: Any) -> str:
        return str(cat).strip() if cat and str(cat).strip() else "未知"
    
    counter = Counter(normalize_category(fb.get("category", "")) for fb in feedbacks)
    
    # 取前8
    top_categories = counter.most_common(8)
    
    # 预定义颜色循环（可以扩展更多）
    colors = [
        "#10b981", "#f59e0b", "#3b82f6", "#8b5cf6", "#ef4444",
        "#06b6d4", "#ec4899", "#84cc16", "#f97316"
    ]
    
    result = []
    for i, (category, count) in enumerate(top_categories):
        result.append({
            "name": category if category != "未知" else "未分类",  # 可选美化
            "value": count,
            "color": colors[i % len(colors)]
        })
    
    return result

def generate_keyword_analysis(start_date: str, end_date: str) -> Dict[str, Any]:
    """生成关键词分析数据：高频前8个关键词（不足则全部） + Top4趋势"""
    
    # 解析日期
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    # 获取本周帖子
    feedbacks = get_feedbacks_in_date_range(start_dt, end_dt, include_end_day=True)
    
    # 加载关键词库
    all_keywords = load_keywords()
    if not all_keywords:
        all_keywords = ["蓝屏", "崩溃", "错误", "无法启动", "闪退", "卡顿", "数据丢失", "系统错误"]
    
    print(f"[DEBUG] 关键词库加载: {len(all_keywords)} 个 → {all_keywords}")
    print(f"[DEBUG] 本周帖子数量: {len(feedbacks)} 条")
    
    # 生成日期序列（最多7天）
    dates = []
    current = start_dt
    while current <= end_dt and len(dates) < 7:
        dates.append(current.strftime("%m-%d"))
        current += timedelta(days=1)
    
    # 统计：总出现次数 + 每日出现次数
    total_counter = Counter()                    # 关键词 → 总次数
    daily_counter = defaultdict(lambda: defaultdict(int))  # 日期 → 关键词 → 次数
    
    for fb in feedbacks:
        title = (fb.get("title") or "").strip()
        content = (fb.get("content") or "").strip()
        text = (title + " " + content).lower()  # 统一转小写
        
        if not text:
            continue
        
        # 处理 created_at 各种可能格式
        created = fb.get("created_at")
        if isinstance(created, str):
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except:
                continue
        elif isinstance(created, dict) and "$date" in created:
            try:
                created_dt = datetime.fromisoformat(created["$date"].replace("Z", "+00:00"))
            except:
                continue
        elif isinstance(created, datetime):
            created_dt = created
        else:
            continue
        
        post_day_str = created_dt.date().strftime("%m-%d")
        if post_day_str not in dates:
            continue
        
        # 匹配关键词（子串计数，不区分大小写）
        for kw in all_keywords:
            kw_lower = kw.lower()
            count = text.count(kw_lower)
            if count > 0:
                total_counter[kw] += count
                daily_counter[post_day_str][kw] += count
    
    print(f"[DEBUG] 本周关键词匹配统计: {dict(total_counter)}")
    
    # ========== 高频关键词：前8个（不足8个就显示全部）==========
    top_keywords_list = total_counter.most_common(8)  # 最多取8个
    # 如果少于8个，most_common(8) 会返回全部，不需要额外处理
    
    top_keywords = []
    colors = ["#ef4444", "#f59e0b", "#8b5cf6", "#10b981", "#3b82f6", "#ec4899", "#f97316", "#22c55e"]
    for i, (kw, count) in enumerate(top_keywords_list):
        top_keywords.append({
            "keyword": kw,
            "count": count,
            "color": colors[i % len(colors)]
        })
    
    # 如果一个都没匹配到，至少返回空数组（前端不会报错）
    if not top_keywords:
        print("[DEBUG] 本周无任何关键词匹配")
    
    # ========== 趋势图：Top4 关键词 ==========
    top4_keywords = [item[0] for item in total_counter.most_common(4)]
    
    # 如果一个都没匹配，兜底显示“蓝屏”（避免趋势图为空报错）
    if not top4_keywords:
        top4_keywords = ["蓝屏"]
    
    keyword_trend = {
        "dates": dates,
        "keywords": top4_keywords,
        "data": {}
    }
    
    for kw in top4_keywords:
        keyword_trend["data"][kw] = [daily_counter[date].get(kw, 0) for date in dates]
    
    print(f"[DEBUG] 趋势图关键词: {top4_keywords}")
    
    return {
        "top_keywords": top_keywords,      # 前8个或全部
        "keyword_trend": keyword_trend      # Top4（或兜底蓝屏）的每日数据
    }

# 使用示例
print(get_current_week_range())  # 默认使用今天
print(get_current_week_range("2025.12.14"))  # 指定日期