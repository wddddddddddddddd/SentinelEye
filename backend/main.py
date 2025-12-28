from fastapi import FastAPI, HTTPException
import uvicorn
from typing import Optional, List, Any, Dict
from pydantic import BaseModel
import random
from datetime import datetime, date, timedelta
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
## feedback 相关导入
from backend.services.feedback_service import (
    get_recent_feedbacks,
    get_all_feedbacks,
    get_feedback_by_id,
    get_feedback_count
)
from backend.schemas.feedback import FeedbackResponse

## keyword 相关导入
from backend.schemas.keyword import KeywordCreate, KeywordUpdate
from backend.services import keyword_service

## Dashboard
import asyncio
from backend.services.dashboard_service import today_feedbacks_stats, get_chart_data

## Analytics相关导入
from backend.services.analytics_service import generate_overview, generate_type_distribution, generate_trend, generate_category_analysis, generate_keyword_analysis, DateRange

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    keyword_service.init_indexes()
    yield
    # 关闭时（这里暂时不需要做事）

# 创建FastAPI应用实例
app = FastAPI(
    title="SentinelEye Backend API",
    description="监控反馈系统后端API",
    version="1.0.0",
    lifespan=lifespan
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

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "SentinelEye Backend"
    }

## 用户反馈信息接口
@app.get("/api/feedback/recent", response_model=List[FeedbackResponse])
async def api_get_recent_feedbacks(limit: int = 5):
    """
    获取最近的反馈
    
    Args:
        limit: 返回条数，默认5条
        
    Returns:
        最近的反馈列表
    """
    try:
        return get_recent_feedbacks(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取反馈数据失败: {str(e)}")


@app.get("/api/feedback/all", response_model=List[FeedbackResponse])
async def api_get_all_feedbacks():
    """
    获取所有反馈
    
    Returns:
        所有反馈列表
    """
    try:
        return get_all_feedbacks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取反馈数据失败: {str(e)}")
    
## keyword CRUD
@app.get("/api/keywords")
def get_keywords():
    return keyword_service.load_keywords()


@app.post("/api/keywords")
def add_keyword(item: KeywordCreate):
    success = keyword_service.add_keyword(item.keyword)
    if not success:
        raise HTTPException(status_code=400, detail="关键词已存在")
    return {
        "message": "添加成功",
        "keywords": keyword_service.load_keywords()
    }


@app.delete("/api/keywords/{keyword}")
def delete_keyword(keyword: str):
    success = keyword_service.delete_keyword(keyword)
    if not success:
        raise HTTPException(status_code=404, detail="关键词不存在")
    return {
        "message": "删除成功",
        "keywords": keyword_service.load_keywords()
    }


@app.put("/api/keywords")
def update_keyword(item: KeywordUpdate):
    success = keyword_service.update_keyword(item.old, item.new)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="更新失败，目标关键词可能已存在或原关键词不存在"
        )
    return {
        "message": "更新成功",
        "keywords": keyword_service.load_keywords()
    }


## Dashboard Card
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """
    获取仪表盘统计卡片数据
    """
    try:
        stats = today_feedbacks_stats()
        
        # 直接构造响应，Pydantic 会自动验证和序列化
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表盘统计失败: {str(e)}")


@app.get("/api/dashboard/chart-data")
async def get_chart_data_api(days: int = 7):
    """
    获取图表数据（近 days 天的分类和趋势）
    """
    if days <= 0 or days > 30:
        raise HTTPException(status_code=400, detail="days 参数必须在 1-30 之间")
        
    try:
        chart_data = get_chart_data(days)
        
        return chart_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图表数据失败: {str(e)}")


## 数据分析页面
@app.post("/api/analytics/overview")
async def get_overview(date_range: DateRange):
    """获取概览统计数据"""
    return generate_overview(date_range.start_date, date_range.end_date)

@app.post("/api/analytics/type-distribution")
async def get_type_distribution(date_range: DateRange):
    """获取反馈类型分布"""
    return generate_type_distribution()

@app.post("/api/analytics/trend")
async def get_trend(date_range: DateRange):
    """获取反馈趋势"""
    return generate_trend(date_range.start_date, date_range.end_date)

@app.post("/api/analytics/category")
async def get_category_analysis(date_range: DateRange):
    """获取分类分析"""
    return generate_category_analysis()

@app.post("/api/analytics/keywords")
async def get_keyword_analysis(date_range: DateRange):
    """获取关键词分析"""
    return generate_keyword_analysis(date_range.start_date, date_range.end_date)

@app.post("/api/analytics/all")
async def get_all_analytics(date_range: DateRange):
    """获取所有分析数据（一次性获取）"""
    return {
        "overview": generate_overview(date_range.start_date, date_range.end_date),
        "type_distribution": generate_type_distribution(date_range.start_date, date_range.end_date),
        "trend": generate_trend(date_range.start_date, date_range.end_date),
        "category_analysis": generate_category_analysis(),
        "keyword_analysis": generate_keyword_analysis(date_range.start_date, date_range.end_date),
    }

@app.post("/api/analytics/generate-report")
async def generate_report(date_range: DateRange):
    """生成周报（模拟）"""
    import time
    time.sleep(1)  # 模拟生成时间
    
    return {
        "success": True,
        "message": "周报生成成功",
        "report_id": f"report_{int(time.time())}",
        "download_url": f"/api/reports/download/{date_range.start_date}_{date_range.end_date}.pdf",
        "date_range": {
            "start": date_range.start_date,
            "end": date_range.end_date
        },
        "generated_at": datetime.now().isoformat()
    }

@app.get("/api/reports/download/{report_id}")
async def download_report(report_id: str):
    """下载报告（模拟）"""
    # 实际项目中这里应该返回文件流
    return {
        "success": True,
        "message": "报告下载准备完成",
        "report_id": report_id,
        "direct_download_url": f"https://example.com/reports/{report_id}.pdf"
    }

# 数据对比API
@app.post("/api/analytics/compare")
async def compare_data(current_range: DateRange, compare_range: DateRange):
    """对比两个时间段的数据"""
    current_data = {
        "overview": generate_overview(current_range.start_date, current_range.end_date),
        "trend": generate_trend(current_range.start_date, current_range.end_date)
    }
    
    compare_data = {
        "overview": generate_overview(compare_range.start_date, compare_range.end_date),
        "trend": generate_trend(compare_range.start_date, compare_range.end_date)
    }
    
    # 计算增长率
    current_total = current_data["overview"]["total_feedback"]
    compare_total = compare_data["overview"]["total_feedback"]
    growth_rate = ((current_total - compare_total) / compare_total * 100) if compare_total > 0 else 0
    
    return {
        "current_period": current_data,
        "compare_period": compare_data,
        "comparison": {
            "total_feedback_growth": round(growth_rate, 2),
            "resolution_rate_change": round(
                current_data["overview"]["resolution_rate"] - compare_data["overview"]["resolution_rate"], 2
            ),
            "urgent_feedback_change": 
                current_data["overview"]["urgent_feedback"] - compare_data["overview"]["urgent_feedback"]
        }
    }