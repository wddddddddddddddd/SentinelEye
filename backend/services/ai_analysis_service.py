# backend/services/ai_analysis_service.py

from typing import List, Optional
from bson import ObjectId

from backend.core.mongo_client import ai_analysis_collection
from datetime import datetime, date, timedelta

def convert_to_dict(doc: dict) -> dict:
    """
    把 MongoDB 文档转成前端友好的 dict
    主要处理 _id 转为字符串
    """
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc

def get_all_ai_analyses(skip: int = 0, limit: int = 10) -> List[dict]:
    """
    获取所有 AI 分析记录（支持分页）
    """

    try:
        cursor = (
            ai_analysis_collection
            .find({"ai_result": {"$exists": True}})
            .sort("analyzed_at", -1)
            .skip(skip)
            .limit(limit)
        )

        analyses = []

        for doc in cursor:
            analyses.append(convert_to_dict(doc))

        return analyses

    except Exception as e:
        print(f"[错误] 获取AI分析分页失败: {e}")
        return []


def get_ai_analysis_by_post_id(post_id: str) -> Optional[dict]:
    """
    根据 post_id 查询单条 AI 分析（你最常用的）
    """
    try:
        doc = ai_analysis_collection.find_one({"post_id": post_id})
        return convert_to_dict(doc)
    except Exception as e:
        print(f"[错误] 根据post_id查询AI分析失败: {e}")
        return None