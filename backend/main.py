from fastapi import FastAPI, HTTPException
import uvicorn
from typing import Optional, List

from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

## feedback 相关导入
from services.feedback_service import (
    get_recent_feedbacks,
    get_all_feedbacks,
    get_feedback_by_id,
    get_feedback_count
)
from schemas.feedback import FeedbackResponse

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
    
