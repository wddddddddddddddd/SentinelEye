import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

# 加载环境变量（确保能连 MongoDB）
load_dotenv(override=True)

# MongoDB 配置（和你项目里保持一致）
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "SentinelEye")

# 导入 Celery 任务
from backend.celery_app.tasks import async_analyze_feedback

def get_db_connection():
    client = MongoClient(MONGODB_URI)
    return client[DB_NAME]

def test_async_analyze(feedback_id: str = None):
    """
    测试投递异步分析任务
    """
    db = get_db_connection()
    
    # 如果没传 feedback_id，就自动找一个还没分析过的
    if not feedback_id:
        post = db.feedbacks.find_one({"ai_analyzed": {"$ne": True}})
        if not post:
            print("❌ 数据库里没有未分析的帖子，请手动指定 feedback_id")
            return
        feedback_id = str(post["_id"])
        print(f"自动找到未分析的帖子: {post.get('title', '无标题')} (id: {feedback_id})")
    else:
        # 验证 ID 存在
        if not ObjectId.is_valid(feedback_id):
            print("❌ 无效的 ObjectId")
            return
        post = db.feedbacks.find_one({"_id": ObjectId(feedback_id)})
        if not post:
            print("❌ 未找到该 feedback_id")
            return
        print(f"找到帖子: {post.get('title', '无标题')}")

    # 检查是否已经分析过（任务里也有这层保护，但提前提示更好）
    if post.get("ai_analyzed", False):
        print("⚠️ 该帖子已经分析过（ai_analyzed=True），任务会自动跳过")
    
    # 投递异步任务
    print(f"正在投递异步分析任务到 Celery 队列...")
    result = async_analyze_feedback.delay(feedback_id)

    print(f"任务已投递，task_id: {result.id}")
    print(f"当前状态: {result.status}")  # 通常先是 PENDING

    # 可选：轮询等待结果（测试时用，生产别这么干）
    import time
    while not result.ready():
        print(f"等待中... 当前状态: {result.status}")
        time.sleep(2)

    print(f"最终状态: {result.status}")  # SUCCESS / FAILURE
    if result.successful():
        print("任务成功！结果:", result.get())
    elif result.failed():
        print("任务失败！错误:", result.traceback)

if __name__ == "__main__":
    # ===== 方式1：自动找一个未分析的帖子投递 =====
    # test_async_analyze()
    
    # ===== 方式2：手动指定 feedback_id（用你提供的样例）=====
    test_async_analyze("694bfe9e98f0cb12c51465ac")
    
    # 已分析过的，会被跳过
    # test_async_analyze("694bfead98f0cb12c51465cc")