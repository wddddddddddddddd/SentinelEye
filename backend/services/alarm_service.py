from typing import List, Dict
from backend.core.mongo_client import ai_analysis_collection

def get_pending_alarms(limit: int = 10) -> List[Dict]:
    """
    1. 在 ai_analysis 查找 alarm_sent != True 的记录
    2. 通过 lookup 关联 feedbacks 获取帖子基础信息
    """
    pipeline = [
        # STEP 1: 筛选未发送且已有结果的 AI 分析记录
        {
            "$match": {
                "alarm_sent": {"$ne": True},      # 过滤已发送
                "ai_result": {"$exists": True}    # 确保有分析结果
            }
        },
        # STEP 2: 关联 feedbacks 集合获取帖子详情
        {
            "$lookup": {
                "from": "feedbacks",             # 关联的集合名
                "localField": "post_id",         # ai_analysis 中的字段
                "foreignField": "post_id",       # feedbacks 中的字段
                "as": "post_details"             # 存入的临时数组名
            }
        },
        # STEP 3: 过滤掉那些在 feedbacks 中找不到原始帖子的记录（可选，增加健壮性）
        {
            "$match": {
                "post_details": { "$not": { "$size": 0 } }
            }
        },
        # STEP 4: 取出关联数组中的第一个对象
        {
            "$addFields": {
                "post": { "$arrayElemAt": ["$post_details", 0] }
            }
        },
        # STEP 5: 排序并限制条数
        { "$sort": { "analyzed_at": -1 } },
        { "$limit": limit }
    ]

    try:
        cursor = ai_analysis_collection.aggregate(pipeline)
        result = []

        for item in cursor:
            ai = item["ai_result"]
            post = item["post"]
            
            # 统一风险等级格式
            risk = str(ai.get("risk_level", "")).upper()
            if risk not in ["HIGH", "MEDIUM", "LOW"]:
                continue

            # 按照你之前的格式进行组装
            result.append({
                "post": {
                    "id": post.get("post_id"),
                    "title": post.get("title"),
                    "username": post.get("username"),
                    "category": post.get("category"),
                    "created_at": post.get("created_at"),
                    "content": post.get("content"),
                    "url": post.get("url"),
                    "images": post.get("images", [])
                },
                "ai_result": {
                    "trigger": ai.get("scene"),
                    "analysis": [ai.get("analysis")],
                    "evidence": ai.get("key_evidence"),
                    "suggestions": ai.get("suggestions")
                },
                "risk_level": risk
            })

        return result

    except Exception as e:
        print(f"[错误] 聚合查询待发送告警失败: {e}")
        return []

def mark_alarm_sent(post_id: str):
    """
    更新 ai_analysis 集合中的状态
    """
    try:
        ai_analysis_collection.update_one(
            {"post_id": post_id},
            {"$set": {"alarm_sent": True}}
        )
    except Exception as e:
        print(f"[错误] 更新告警状态失败: {e}")

def get_latest_alarm_manual() -> Dict:
    """
    获取最近的一条告警记录（无论是否已发送），用于手动触发
    """
    pipeline = [
        # 1. 确保有 AI 结果即可，不看 alarm_sent 状态
        {
            "$match": {
                "ai_result": {"$exists": True}
            }
        },
        # 2. 关联帖子详情
        {
            "$lookup": {
                "from": "feedbacks",
                "localField": "post_id",
                "foreignField": "post_id",
                "as": "post_details"
            }
        },
        # 3. 按分析时间倒序
        { "$sort": { "analyzed_at": -1 } },
        # 4. 只取最新的一条
        { "$limit": 1 },
        # 5. 展开
        {
            "$addFields": {
                "post": { "$arrayElemAt": ["$post_details", 0] }
            }
        }
    ]

    try:
        cursor = list(ai_analysis_collection.aggregate(pipeline))
        if not cursor:
            return None
        
        item = cursor[0]
        ai = item["ai_result"]
        post = item.get("post", {}) # 考虑到可能帖子被删，给个空字典

        # 统一格式化返回（复用之前的逻辑）
        return {
            "post": {
                "id": post.get("post_id"),
                "title": post.get("title"),
                "username": post.get("username"),
                "category": post.get("category"),
                "created_at": post.get("created_at"),
                "content": post.get("content"),
                "url": post.get("url"),
                "images": post.get("images", [])
            },
            "ai_result": {
                "trigger": ai.get("scene"),
                "analysis": [ai.get("analysis")],
                "evidence": ai.get("key_evidence"),
                "suggestions": ai.get("suggestions")
            },
            "risk_level": str(ai.get("risk_level", "")).upper()
        }
    except Exception as e:
        print(f"[错误] 获取手动告警数据失败: {e}")
        return None


def update_alarm_status(post_id: str, status: bool) -> bool:
    """
    手动修改指定 post_id 的告警发送状态
    """
    try:
        result = ai_analysis_collection.update_one(
            {"post_id": post_id},
            {"$set": {"alarm_sent": status}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"[错误] 修改状态失败: {e}")
        return False

def reset_all_alarms(limit: int = 10):
    """
    批量重置最近 N 条数据的告警状态为 False (调试专用)
    """
    try:
        # 先找到最近的 N 个 ID
        cursor = ai_analysis_collection.find().sort("analyzed_at", -1).limit(limit)
        ids = [doc["post_id"] for doc in cursor]
        
        # 批量更新
        ai_analysis_collection.update_many(
            {"post_id": {"$in": ids}},
            {"$set": {"alarm_sent": False}}
        )
        return len(ids)
    except Exception as e:
        print(f"[错误] 批量重置失败: {e}")
        return 0