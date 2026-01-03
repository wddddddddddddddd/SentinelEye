# backend/services/ai_analysis_service.py

from typing import List, Optional
from bson import ObjectId

from backend.core.mongo_client import ai_analysis_collection


def convert_to_dict(doc: dict) -> dict:
    """
    把 MongoDB 文档转成前端友好的 dict
    主要处理 _id 转为字符串
    """
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


def get_all_ai_analyses(limit: Optional[int] = None) -> List[dict]:
    """
    【调试专用】获取所有 AI 分析记录，按分析时间倒序
    完全模仿你 feedback 的写法，稳如老狗
    """
    try:
        # 基础查询 + 排序
        cursor = ai_analysis_collection.find({"ai_result": {"$exists": True}}) \
                                      .sort("analyzed_at", -1)

        # 如果有限制条数，手动切片
        if limit:
            cursor = cursor.limit(limit)

        analyses = []
        for doc in cursor:  # 同步遍历，绝对不会报 await list 的错
            analyses.append(convert_to_dict(doc))

        return analyses

    except Exception as e:
        print(f"[错误] 获取全部AI分析失败: {e}")
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