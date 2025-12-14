# 测试脚本 mtest_order.py
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os


client = MongoClient('mongodb://localhost:27017/')
mongodb_client = client["sentineleye_db"]
# 方法1：按_id排序（物理顺序）
print("=== 按_id排序（物理存储顺序）===")
docs = list(mongodb_client.feedbacks.find().sort("_id", 1).limit(5))
for i, doc in enumerate(docs):
    print(f"{i+1}. ID:{doc['_id']} | 发帖:{doc.get('created_at')} | {doc.get('title')}")

print("\n=== 按created_at排序（业务逻辑顺序）===")
# 方法2：按created_at排序（业务顺序）
docs = list(mongodb_client.feedbacks.find().sort("created_at", -1).limit(5))
for i, doc in enumerate(docs):
    print(f"{i+1}. 发帖:{doc.get('created_at')} | {doc.get('title')}")

print("\n=== 验证数据完整性 ===")
# 统计
total = mongodb_client.feedbacks.count_documents({})
print(f"总记录数: {total}")

# 检查是否有重复
pipeline = [
    {"$group": {"_id": "$post_id", "count": {"$sum": 1}}},
    {"$match": {"count": {"$gt": 1}}}
]
duplicates = list(mongodb_client.feedbacks.aggregate(pipeline))
print(f"重复的post_id数量: {len(duplicates)}")