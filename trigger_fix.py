import os
from pymongo import MongoClient
from dotenv import load_dotenv
from backend.celery_app.tasks import async_analyze_feedback

# 加载环境变量
load_dotenv(override=True)

def trigger_reanalysis():
    try:
        # 核心修改：优先使用环境变量里的 URI
        # 容器内这个值通常是 mongodb://root:password@sentinel-mongo:27017/...
        uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("DB_NAME", "SentinelEye")
        
        if not uri:
            # 如果没拿到环境变量（比如在宿主机跑），才尝试手动拼
            user = os.getenv("MONGO_ROOT_USER", "root")
            password = os.getenv("MONGO_ROOT_PASSWORD", "")
            uri = f"mongodb://{user}:{password}@localhost:27017/{db_name}?authSource=admin"

        print(f"📡 正在连接数据库: {uri.split('@')[-1]}") # 打印脱敏后的地址
        client = MongoClient(uri)
        db = client[db_name]
        
        # 验证连接
        client.admin.command('ping')
        
        # 筛选未分析的数据
        query = {"ai_analyzed": {"$ne": True}}
        docs = list(db.feedbacks.find(query))
        total = len(docs)
        
        if total == 0:
            print("✨ 没有需要分析的数据。")
            return

        print(f"🔍 找到 {total} 条数据，准备推入队列...")

        for count, doc in enumerate(docs, 1):
            async_analyze_feedback.delay(str(doc["_id"]))
            # 更新状态防止重复推入
            db.feedbacks.update_one({"_id": doc["_id"]}, {"$set": {"ai_analyzed": False}})
            if count % 10 == 0:
                print(f"已投递 {count}/{total}...")

        print(f"✅ 成功投递 {total} 条任务！")

    except Exception as e:
        print(f"❌ 触发失败: {e}")

if __name__ == "__main__":
    trigger_reanalysis()
