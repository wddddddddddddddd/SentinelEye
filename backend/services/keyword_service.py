# services/keyword_service.py
from typing import List
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from pymongo import ASCENDING

from core.mongo_client import keywords_collection


def init_indexes():
    """初始化索引（启动时调用一次即可）"""
    keywords_collection.create_index(
        [("keyword", ASCENDING)],
        unique=True
    )


def load_keywords() -> List[str]:
    """加载所有关键词"""
    cursor = keywords_collection.find(
        {},
        {"_id": 0, "keyword": 1}
    ).sort("keyword", ASCENDING)

    keywords = [doc["keyword"] for doc in cursor]

    # 确保“蓝屏”一定存在
    if "蓝屏" not in keywords:
        add_keyword("蓝屏")
        keywords.insert(0, "蓝屏")

    return keywords


def add_keyword(keyword: str) -> bool:
    """添加关键词"""
    try:
        keywords_collection.insert_one({
            "keyword": keyword,
            "created_at": datetime.utcnow()
        })
        return True
    except DuplicateKeyError:
        return False


def delete_keyword(keyword: str) -> bool:
    """删除关键词"""
    result = keywords_collection.delete_one({"keyword": keyword})
    return result.deleted_count > 0


def update_keyword(old: str, new: str) -> bool:
    """更新关键词"""
    if old == new:
        return True

    # 新关键词已存在，直接失败
    if keywords_collection.find_one({"keyword": new}):
        return False

    result = keywords_collection.update_one(
        {"keyword": old},
        {"$set": {"keyword": new}}
    )

    return result.matched_count > 0
