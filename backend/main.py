from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
import uvicorn
from typing import Optional, List, Any, Dict
from pydantic import BaseModel
import random
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
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

## AI service导入
from backend.services.ai_analysis_service import get_ai_analysis_by_post_id, get_all_ai_analyses

## report导入
from backend.services.report_service import report_service
import os

# ============ 静态文件服务（用于PDF下载） ============
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from urllib.parse import quote

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
    lifespan=lifespan,
    openapi_url="/api/openapi.json", # 强制 openapi 定义也在 /api 下
    docs_url="/api/docs",           # 强制文档在 /api/docs
    redoc_url="/api/redoc",
)
# 确保静态文件目录存在
static_dir = "./static"
os.makedirs(static_dir, exist_ok=True)

# 获取项目根目录
BASE_DIR = Path(__file__).parent  # backend目录
PROJECT_ROOT = BASE_DIR.parent    # 项目根目录

# 静态文件目录 - 使用绝对路径
static_dir = os.path.join(PROJECT_ROOT, "backend", "static")
os.makedirs(static_dir, exist_ok=True)

print(f"静态文件目录: {static_dir}")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

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
    return generate_category_analysis(date_range.start_date, date_range.end_date)

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
        "category_analysis": generate_category_analysis(date_range.start_date, date_range.end_date),
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


## AI 分析获取接口
# @app.get("/api/ai-analysis/recent")
# async def recent_ai_analyses(
#     limit: int = Query(6, ge=1, le=20),
#     days: int = Query(7, ge=1, le=30)
# ):
#     analyses = await get_recent_ai_analyses(limit=limit, days=days)
#     return {"data": analyses}

# 【调试专用】新增返回全部的接口
@app.get("/api/ai-analysis/recent")
async def all_ai_analyses_recent(
    limit: Optional[int] = Query(None, ge=1, le=1000, description="不传表示返回全部")
):
    """
    调试用：返回所有 AI 分析记录
    """
    try:
        limit = 4
        analyses = get_all_ai_analyses(limit=limit)
        return analyses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取全部AI分析失败: {str(e)}")
    


@app.get("/api/ai-analysis/all")
async def all_ai_analyses(
    skip: int = Query(0, ge=0, description="跳过的记录数(用于分页)"),
    limit: int = Query(10, ge=1, le=100, description="每次拉取的记录数")
):
    """
    分页获取所有 AI 分析记录，供前端懒加载使用
    """
    try:
        # 你需要确保你的底层数据库查询函数支持 skip 和 limit
        # 例如 MongoDB: collection.find().skip(skip).limit(limit)
        analyses = get_all_ai_analyses(skip=skip, limit=limit)
        
        # 建议统一返回结构
        return {
            "code": 200,
            "data": analyses,
            "msg": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取全部AI分析失败: {str(e)}")

# 根据 post_id 查询单条
@app.get("/api/ai-analysis/post/{post_id}")
async def ai_analysis_by_post_id(post_id: str):
    analysis = await get_ai_analysis_by_post_id(post_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="未找到该帖子的AI分析")
    return analysis


class ReportGenerateRequest(BaseModel):
    start_date: str
    end_date: str
    report_type: str = "weekly"


@app.post("/api/reports/generate", tags=["报告管理"])
async def generate_report(
    req: ReportGenerateRequest,
    background_tasks: BackgroundTasks
):
    # 验证日期格式
    try:
        datetime.strptime(req.start_date, '%Y-%m-%d')
        datetime.strptime(req.end_date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")

    result = await report_service.create_report(
        req.start_date,
        req.end_date,
        req.report_type
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    report_id = result["report_id"]

    background_tasks.add_task(
        report_service.run_report_generation,
        report_id,
        req.start_date,
        req.end_date,
        req.report_type
    )

    return {
        "success": True,
        "message": "报告生成任务已启动",
        "data": {
            "report_id": report_id,
            "status_url": f"/api/reports/{report_id}/status"
        }
    }

@app.get("/api/reports/{report_id}/status", tags=["报告管理"])
async def get_report_status(report_id: str):
    """获取报告生成状态"""
    result = await report_service.get_report_status(report_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@app.get("/api/reports/{report_id}/content", tags=["报告管理"])
async def get_report_content(report_id: str):
    """获取报告内容"""
    result = await report_service.get_report_content(report_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@app.get("/api/reports/{report_id}/download", tags=["报告管理"])
async def download_report(report_id: str):
    try:
        result = await report_service.get_report_status(report_id)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])

        report_data = result["data"]
        if report_data["status"] != "completed":
            raise HTTPException(status_code=400, detail="报告尚未完成")

        report_detail = report_service.storage.get_report(report_id)
        if not report_detail:
            raise HTTPException(status_code=404, detail="报告不存在")

        pdf_path = report_detail.get("pdf_path")
        if not pdf_path:
            raise HTTPException(status_code=404, detail="PDF文件不存在")

        # 统一从 static 目录取
        filename = os.path.basename(pdf_path)
        filepath = os.path.join(static_dir, filename)

        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"PDF文件不存在: {filename}")

        # ========= 修复点 =========
        download_name = f"报告_{report_id}.pdf"
        encoded_name = quote(download_name)

        return FileResponse(
            filepath,
            media_type="application/pdf",
            headers={
                # RFC 5987 写法，浏览器全支持
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print("下载失败:", repr(e))
        raise HTTPException(status_code=500, detail="下载失败")

@app.get("/api/reports/list", tags=["报告管理"])
async def list_reports(limit: int = 10):
    """获取报告列表"""
    result = await report_service.list_reports(limit)
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return {
        "success": True,
        "count": len(result["data"]),
        "data": result["data"]
    }

# 推推通知接口
from backend.services.alarm_service import get_pending_alarms, mark_alarm_sent, get_latest_alarm_manual, update_alarm_status, reset_all_alarms
from fastapi import Body, Header

@app.get("/api/alarm/pending")
async def pending_alarms(limit: int = 10):
    """
    获取待处理的告警列表 (聚合了 feedbacks 和 ai_analysis)
    """
    try:
        # 调用我们之前写的聚合查询逻辑
        data = get_pending_alarms(limit)
        
        return {
            "success": True,
            "count": len(data),
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警失败: {str(e)}")

@app.post("/api/alarm/mark_sent")
async def mark_as_sent(payload: dict = Body(...)):
    """
    标记告警已发送
    """
    post_id = payload.get("post_id")
    if not post_id:
        raise HTTPException(status_code=400, detail="缺少 post_id")
    
    try:
        mark_alarm_sent(post_id)
        return {
            "success": True,
            "message": f"Post {post_id} 状态已更新为已发送"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新状态失败: {str(e)}")
    
@app.post("/api/alarm/resend_latest")
async def resend_latest_alarm():
    """
    手动触发：获取最近一次告警数据并返回
    前端拿到这个数据后，可以调用发送逻辑（如发钉钉/飞书）
    """
    try:
        data = get_latest_alarm_manual()
        
        if not data:
            return {
                "success": False,
                "message": "数据库中暂无 AI 分析记录"
            }
            
        return {
            "success": True,
            "data": data,
            "message": "已成功获取最近一次告警详情"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发手动告警失败: {str(e)}")
    
@app.put("/api/alarm/reset_status/{post_id}")
async def reset_single_status(
    post_id: str, 
    status: bool = False, 
    x_debug_key: Optional[str] = Header(None) # FastAPI会自动把 x-debug-key 映射到这个变量
):
    """
    调试接口：手动修改某条数据的 alarm_sent 状态
    Postman 调用方式: PUT http://server/api/debug/reset_status/normalthread_123?status=false
    """
    if x_debug_key != "tuituitui123": # 只有 Postman 带有这个 Header 才能执行
        raise HTTPException(status_code=403, detail="Forbidden")
    success = update_alarm_status(post_id, status)
    if success:
        return {"success": True, "message": f"Post {post_id} status updated to {status}"}
    return {"success": False, "message": "Post ID not found or status unchanged"}

@app.post("/api/alarm/batch_reset")
async def batch_reset(limit: int = Body(...), x_debug_key: str = Header(None)):
    """
    调试接口：一键重置最近 N 条数据为“未发送”状态
    Postman 调用方式: POST http://server/api/debug/batch_reset  JSON: {"limit": 20}
    """
    if x_debug_key != "tuituitui123": # 只有 Postman 带有这个 Header 才能执行
        raise HTTPException(status_code=403, detail="Forbidden")
    count = reset_all_alarms(limit)
    return {
        "success": True, 
        "message": f"已重置最近 {count} 条数据的告警状态，Worker 将重新抓取它们。"
    }