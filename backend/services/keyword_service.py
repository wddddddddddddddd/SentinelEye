# services/keyword_service.py
from typing import List
from datetime import datetime
from core.mongo_client import mongodb_client
from models.keyword import Keyword
from pymongo.errors import DuplicateKeyError
from pymongo import ASCENDING

# 确保索引唯一
mongodb_client.db.keywords.create_index([("keyword", ASCENDING)], unique=True)


def load_keywords() -> List[str]:
    """从 MongoDB 加载所有关键词"""
    cursor = mongodb_client.db.keywords.find({}, {"_id": 0, "keyword": 1}).sort("keyword", ASCENDING)
    keywords = [doc["keyword"] for doc in cursor]
    # 确保“蓝屏”一定存在
    if "蓝屏" not in keywords:
        add_keyword("蓝屏")
        keywords.insert(0, "蓝屏")
    return keywords


def add_keyword(keyword: str) -> bool:
    """添加关键词，返回是否成功"""
    try:
        mongodb_client.db.keywords.insert_one({
            "keyword": keyword,
            "created_at": datetime.utcnow()
        })
        return True
    except DuplicateKeyError:
        return False


def delete_keyword(keyword: str) -> bool:
    """删除关键词"""
    result = mongodb_client.db.keywords.delete_one({"keyword": keyword})
    return result.deleted_count > 0


def update_keyword(old: str, new: str) -> bool:
    """更新关键词"""
    if add_keyword(new):
        # 新关键词添加成功，再删除旧的
        delete_keyword(old)
        return True
    else:
        # 新关键词已存在，更新失败
        return False
