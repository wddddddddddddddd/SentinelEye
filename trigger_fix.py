import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv
from backend.celery_app.tasks import async_analyze_feedback

# 加载环境变量
load_dotenv(override=True)

# 定义核心关键词
CORE_KEYWORDS = [
    "蓝屏", "BSOD", "卡死", "崩溃", "驱动", "dump", "dmp", 
    "重启", "黑屏", "死机", "报错", "异常", "kernel", "屏"
]

def trigger_reanalysis():
    try:
        uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("DB_NAME", "SentinelEye")
        
        if not uri:
            user = os.getenv("MONGO_ROOT_USER", "root")
            password = os.getenv("MONGO_ROOT_PASSWORD", "")
            uri = f"mongodb://{user}:{password}@localhost:27017/{db_name}?authSource=admin"

        print(f"📡 正在连接数据库: {uri.split('@')[-1]}") 
        client = MongoClient(uri)
        db = client[db_name]
        
        # 1. 动态拼接正则模式："蓝屏|BSOD|卡死|..."
        regex_pattern = "|".join(CORE_KEYWORDS)
        
        # 2. 构建查询条件：未分析，且内容包含任意核心关键词 (忽略大小写)
        query = {
            "ai_analyzed": {"$ne": True},
            "content": {"$regex": regex_pattern, "$options": "i"} # ⚠️ 请确保 "content" 是你实际存文本的字段名
        }
        
        # 3. 核心修改：只取 10 条！
        docs = list(db.feedbacks.find(query).limit(10))
        total = len(docs)
        
        if total == 0:
            print("✨ 队列很空闲，没有找到包含高价值关键词且未分析的数据。")
            return

        print(f"🔍 截获 {total} 条高价值数据，准备推入 Celery 队列...")

        for count, doc in enumerate(docs, 1):
            async_analyze_feedback.delay(str(doc["_id"]))
            # 建议将状态改成 pending，防止你手抖点两次重复入队浪费 Token
            db.feedbacks.update_one({"_id": doc["_id"]}, {"$set": {"ai_analyzed": "pending"}})
            print(f"[{count}/10] 已投递 ID: {doc['_id']}")

        print(f"✅ 成功投递 {total} 条任务！脚本执行完毕。")

    except Exception as e:
        print(f"❌ 触发失败: {e}")

if __name__ == "__main__":
    trigger_reanalysis()