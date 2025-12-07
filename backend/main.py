# main.py
from fastapi import FastAPI, HTTPException
from services.feedback_service import load_feedback_list
from services.keyword_service import load_keywords, save_keywords
from models.feedback import Feedback
from models.keyword import Keyword
from models.dashboard import DashboardStats, DashboardSummary
from services.dashboard_service import DashboardService, get_dashboard_stats_from_json
from fastapi.middleware.cors import CORSMiddleware
from services.dashboard_service import DashboardService
from models.dashboard import DashboardStats
import uvicorn
from typing import Optional
from datetime import datetime

# 创建FastAPI应用实例
app = FastAPI(
    title="SentinelEye Backend API",
    description="监控反馈系统后端API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite 默认端口
        "http://localhost:3000",  # 可能的其他前端端口
    ],
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

@app.get("/")
async def root():
    """根路径，返回API基本信息"""
    return {
        "message": "欢迎使用SentinelEye API",
        "version": "1.0.0",
        "endpoints": {
            "仪表盘": "/dashboard/stats",
            "最近反馈": "/feedback/recent",
            "反馈详情": "/feedback/{id}"
        }
    }

# 仪表盘统计API
@app.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_statistics(limit: Optional[int] = None):
    """
    获取仪表盘统计数据

    Args:
        limit: 限制数据条数（可选）

    Returns:
        DashboardStats: 仪表盘统计数据
    """
    try:
        from services.dashboard_service import get_dashboard_stats_from_json

        print(f"开始获取仪表盘数据，limit={limit}")
        stats = get_dashboard_stats_from_json(limit)

        print(f"成功获取统计数据")
        return stats

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"获取仪表盘数据失败: {str(e)}")
        print(f"详细错误: {error_details}")
        raise HTTPException(status_code=500, detail=f"获取仪表盘数据失败: {str(e)}")


@app.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(limit: int = 10, recent_limit: int = 5):
    """
    获取仪表盘摘要信息

    Args:
        limit: 统计使用的数据条数
        recent_limit: 最近反馈显示数量

    Returns:
        DashboardSummary: 仪表盘摘要信息
    """
    try:
        # 加载反馈数据
        feedbacks = load_feedback_list(limit)

        # 创建仪表盘服务实例
        dashboard_service = DashboardService(feedbacks)

        # 获取统计数据
        stats = dashboard_service.get_dashboard_stats()

        # 获取最近反馈
        recent_feedbacks = load_feedback_list(recent_limit)

        # 构建分类统计
        from models.dashboard import CategoryStat
        category_items = []
        for category, count in stats.category_stats.items():
            percentage = (count / stats.total_feedbacks * 100) if stats.total_feedbacks > 0 else 0
            category_items.append(CategoryStat(
                category=category,
                count=count,
                percentage=round(percentage, 2)
            ))

        # 构建标签统计
        tag_items = []
        for tag, count in stats.tag_stats.items():
            percentage = (count / stats.total_feedbacks * 100) if stats.total_feedbacks > 0 else 0
            tag_items.append(CategoryStat(
                category=tag,
                count=count,
                percentage=round(percentage, 2)
            ))

        return DashboardSummary(
            stats=stats,
            recent_feedbacks=recent_feedbacks,
            top_categories=sorted(category_items, key=lambda x: x.count, reverse=True)[:5],
            top_tags=sorted(tag_items, key=lambda x: x.count, reverse=True)[:5]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表盘摘要失败: {str(e)}")


@app.get("/feedback/recent")
async def get_recent_feedbacks(limit: int = 5):
    """
    获取最近的反馈

    Args:
        limit: 返回的数据条数

    Returns:
        List[Feedback]: 最近的反馈列表
    """
    try:
        feedbacks = load_feedback_list(limit)
        return feedbacks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取反馈数据失败: {str(e)}")


@app.get("/feedback/all")
async def get_all_feedbacks():
    """
    获取所有反馈数据

    Returns:
        List[Feedback]: 所有反馈列表
    """
    try:
        # 加载所有数据
        from services.feedback_service import DATA_FILE
        import json
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        feedbacks = [Feedback(**item) for item in data]
        return feedbacks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取反馈数据失败: {str(e)}")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "SentinelEye Backend"
    }

# 关键字 CRUD API
@app.get("/keywords")
def get_keywords():
    return load_keywords()

# 添加
@app.post("/keywords")
def add_keyword(item: Keyword):
    keywords = load_keywords()
    print(type(keywords))
    if item.keyword in keywords:
        raise HTTPException(status_code=400, detail="关键词已存在")

    keywords.append(item.keyword)
    save_keywords(keywords)
    return {"message": "添加成功", "keywords": keywords}

# ---- 删除关键词 ----
@app.delete("/keywords/{keyword}")
def delete_keyword(keyword: str):
    keywords = load_keywords()

    if keyword not in keywords:
        raise HTTPException(status_code=404, detail="关键词不存在")

    keywords.remove(keyword)
    save_keywords(keywords)
    return {"message": "删除成功", "keywords": keywords}

# ---- 修改关键词 ----
@app.put("/keywords")
def update_keyword(old: str, new: str):
    keywords = load_keywords()

    if old not in keywords:
        raise HTTPException(status_code=404, detail="原关键词不存在")

    if new in keywords:
        raise HTTPException(status_code=400, detail="目标关键词已存在")

    index = keywords.index(old)
    keywords[index] = new
    save_keywords(keywords)
    return {"message": "更新成功", "keywords": keywords}


@app.get("/dashboard/chart-data")
async def get_chart_data(days: int = 7, keyword_days: int = 3):
    """获取图表数据

    Args:
        days: 统计天数，默认为7天（用于饼图和趋势图）
        keyword_days: 关键词触发统计天数，默认为3天
    """
    try:
        from services.dashboard_service import DashboardService
        from services.feedback_service import load_all_feedbacks
        from datetime import datetime, date, timedelta

        # 获取所有反馈数据
        all_feedbacks = load_all_feedbacks()

        # 获取近N天的反馈数据（用于饼图和趋势图）
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        # 筛选近N天的数据
        recent_feedbacks = []
        for feedback in all_feedbacks:
            try:
                # 解析反馈日期
                created_date = datetime.strptime(feedback.created_at.split()[0], "%Y-%m-%d").date()
                # 调整年份逻辑
                if created_date.year > today.year:
                    if created_date.month == 12:
                        created_date = created_date.replace(year=today.year - 1)
                    else:
                        created_date = created_date.replace(year=today.year)

                if start_date <= created_date <= today:
                    recent_feedbacks.append(feedback)
            except:
                continue

        print(f"近{days}天的反馈数据：{len(recent_feedbacks)}条")

        # 创建近N天的仪表盘服务实例
        recent_dashboard_service = DashboardService(recent_feedbacks)

        # 获取统计数据
        stats = recent_dashboard_service.get_dashboard_stats()

        # 获取近N天的分类统计
        category_stats = recent_dashboard_service._get_category_stats()
        category_data = []
        for category, count in category_stats.items():
            category_data.append({
                "name": category,
                "value": count
            })

        # 取前8个分类
        category_data = sorted(category_data, key=lambda x: x["value"], reverse=True)[:8]

        # 获取近N天的趋势数据
        trend_data = {
            "dates": stats.recent_trend.dates[-days:] if len(
                stats.recent_trend.dates) > days else stats.recent_trend.dates,
            "feedbacks": stats.recent_trend.feedbacks[-days:] if len(
                stats.recent_trend.feedbacks) > days else stats.recent_trend.feedbacks,
        }

        # ============ 新增：获取近3天关键词触发数据 ============
        # 筛选近keyword_days天的数据
        keyword_start_date = today - timedelta(days=keyword_days - 1)
        recent_keyword_feedbacks = []

        for feedback in all_feedbacks:
            try:
                created_date = datetime.strptime(feedback.created_at.split()[0], "%Y-%m-%d").date()
                # 调整年份逻辑
                if created_date.year > today.year:
                    if created_date.month == 12:
                        created_date = created_date.replace(year=today.year - 1)
                    else:
                        created_date = created_date.replace(year=today.year)

                if keyword_start_date <= created_date <= today:
                    recent_keyword_feedbacks.append(feedback)
            except:
                continue

        print(f"近{keyword_days}天的关键词触发数据：{len(recent_keyword_feedbacks)}条")

        # 获取关键词触发数据
        keyword_triggers = get_keyword_triggers(recent_keyword_feedbacks, keyword_days)

        return {
            "category_data": category_data,
            "trend_data": trend_data,
            "keyword_triggers": keyword_triggers,  # 确保有这个字段
            "total_feedbacks": len(recent_feedbacks),
            "days": days,
            "keyword_days": keyword_days
        }

    except Exception as e:
        import traceback
        print(f"获取图表数据失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取图表数据失败: {str(e)}")


def get_keyword_triggers(feedbacks, days=3):
    """获取关键词触发统计数据"""
    try:
        # 加载关键词文件
        import json
        from pathlib import Path

        base_dir = Path(__file__).resolve().parent
        keywords_file = base_dir / "data" / "keywords.json"

        # 加载关键词
        with open(keywords_file, "r", encoding="utf-8") as f:
            keywords_data = json.load(f)

        keywords = keywords_data.get("keywords", [])
        print(f"加载了 {len(keywords)} 个关键词")

        # 统计每个关键词的出现次数
        keyword_counts = {}

        for feedback in feedbacks:
            title_lower = feedback.title.lower()
            content_lower = feedback.content.lower() if hasattr(feedback, 'content') and feedback.content else ""
            text_to_check = f"{title_lower} {content_lower}"

            for keyword in keywords:
                if keyword in text_to_check:
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        # 按出现次数排序，取前10个
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # 转换为前端需要的格式
        result = []
        for keyword, count in sorted_keywords:
            # 简单判断趋势（可以根据历史数据更精确判断）
            if count > 5:
                trend = "up"  # 上升
            elif count > 2:
                trend = "stable"  # 稳定
            else:
                trend = "down"  # 下降

            result.append({
                "keyword": keyword,
                "count": count,
                "trend": trend
            })

        print(f"关键词触发统计：{len(result)} 个关键词有触发")
        return result

    except Exception as e:
        print(f"获取关键词触发数据失败: {e}")
        return []


@app.get("/analytics/data")
async def get_analytics_data(days: int = 7):
    """获取数据分析页面所需的所有数据"""
    try:
        from services.dashboard_service import DashboardService
        from services.feedback_service import load_all_feedbacks
        from datetime import datetime, date, timedelta

        # 获取所有反馈数据
        all_feedbacks = load_all_feedbacks()

        # 获取近N天的反馈数据
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        # 筛选近N天的数据
        recent_feedbacks = []
        for feedback in all_feedbacks:
            try:
                created_date = datetime.strptime(feedback.created_at.split()[0], "%Y-%m-%d").date()
                # 调整年份逻辑
                if created_date.year > today.year:
                    if created_date.month == 12:
                        created_date = created_date.replace(year=today.year - 1)
                    else:
                        created_date = created_date.replace(year=today.year)

                if start_date <= created_date <= today:
                    recent_feedbacks.append(feedback)
            except:
                continue

        print(f"数据分析：近{days}天的反馈数据：{len(recent_feedbacks)}条")

        # 创建仪表盘服务实例
        dashboard_service = DashboardService(recent_feedbacks)

        # 获取统计数据
        stats = dashboard_service.get_dashboard_stats()

        # 1. 获取反馈类型分布数据（饼图）
        category_stats = dashboard_service._get_category_stats()
        category_data = []
        for category, count in category_stats.items():
            category_data.append({
                "name": category,
                "value": count
            })
        # 取前8个分类
        category_data = sorted(category_data, key=lambda x: x["value"], reverse=True)[:8]

        # 2. 获取趋势数据（折线图）
        trend_data = {
            "dates": stats.recent_trend.dates[-days:] if len(
                stats.recent_trend.dates) > days else stats.recent_trend.dates,
            "feedbacks": stats.recent_trend.feedbacks[-days:] if len(
                stats.recent_trend.feedbacks) > days else stats.recent_trend.feedbacks,
            "processed": stats.recent_trend.processed[-days:] if len(
                stats.recent_trend.processed) > days else stats.recent_trend.processed
        }

        # 3. 获取分类详细数据（横向条形图）
        module_data = []
        for category, count in category_stats.items():
            module_data.append({
                "name": category,
                "value": count
            })
        # 按值排序，取前10个
        module_data = sorted(module_data, key=lambda x: x["value"], reverse=True)[:10]

        # 4. 获取关键词触发数据
        keyword_triggers = get_keyword_analytics(recent_feedbacks, days=7)

        # 5. 获取统计概览数据
        total_count = len(recent_feedbacks)
        processed_count = dashboard_service._count_processed_feedbacks()
        pending_count = dashboard_service._count_pending_feedbacks()
        urgent_count = dashboard_service._count_urgent_feedbacks()

        # 计算增长率（与上周期对比）
        previous_start_date = start_date - timedelta(days=days)
        previous_end_date = start_date - timedelta(days=1)

        previous_feedbacks = []
        for feedback in all_feedbacks:
            try:
                created_date = datetime.strptime(feedback.created_at.split()[0], "%Y-%m-%d").date()
                if created_date.year > today.year:
                    if created_date.month == 12:
                        created_date = created_date.replace(year=today.year - 1)
                    else:
                        created_date = created_date.replace(year=today.year)

                if previous_start_date <= created_date <= previous_end_date:
                    previous_feedbacks.append(feedback)
            except:
                continue

        previous_count = len(previous_feedbacks)
        growth_rate = 0
        if previous_count > 0:
            growth_rate = round(((total_count - previous_count) / previous_count) * 100, 1)

        processing_rate = round((processed_count / total_count * 100), 1) if total_count > 0 else 0

        return {
            "summary": {
                "total_feedbacks": total_count,
                "processed_feedbacks": processed_count,
                "pending_feedbacks": pending_count,
                "urgent_feedbacks": urgent_count,
                "growth_rate": growth_rate,
                "processing_rate": processing_rate,
                "previous_count": previous_count
            },
            "category_data": category_data,
            "trend_data": trend_data,
            "module_data": module_data,
            "keyword_data": keyword_triggers,
            "total_feedbacks": total_count,
            "days": days
        }

    except Exception as e:
        import traceback
        print(f"获取数据分析数据失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取数据分析数据失败: {str(e)}")


def get_keyword_analytics(feedbacks, days=7):
    """获取关键词分析数据"""
    try:
        import json
        from pathlib import Path
        from collections import defaultdict

        base_dir = Path(__file__).resolve().parent
        keywords_file = base_dir / "data" / "keywords.json"

        # 加载关键词
        with open(keywords_file, "r", encoding="utf-8") as f:
            keywords_data = json.load(f)

        keywords = keywords_data.get("keywords", [])

        # 统计每个关键词的出现次数
        keyword_counts = defaultdict(int)

        for feedback in feedbacks:
            title_lower = feedback.title.lower()
            content_lower = feedback.content.lower() if hasattr(feedback, 'content') and feedback.content else ""
            text_to_check = f"{title_lower} {content_lower}"

            for keyword in keywords:
                if keyword in text_to_check:
                    keyword_counts[keyword] += 1

        # 按出现次数排序，取前8个
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:8]

        # 获取关键词趋势数据
        keyword_trends = {}
        top_keywords = [k for k, _ in sorted_keywords[:3]]

        # 这里可以扩展为按日期统计关键词趋势，现在先返回简单数据
        return {
            "top_keywords": [
                {"keyword": keyword, "count": count}
                for keyword, count in sorted_keywords
            ],
            "keyword_trends": {
                keyword: {
                    "trend_data": [max(1, count // 2), count, max(1, count // 3)],
                    "description": "高频关键词" if count > 5 else "中频关键词" if count > 2 else "低频关键词"
                }
                for keyword, count in sorted_keywords[:3]
            }
        }

    except Exception as e:
        print(f"获取关键词分析数据失败: {e}")
        return {
            "top_keywords": [],
            "keyword_trends": {}
        }

if __name__ == "__main__":
    # 启动服务
    uvicorn.run(app, port=8888)