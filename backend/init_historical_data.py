import os
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv

from backend.crawler.fans_feedback import crawl_until_date, parse_created_at
from backend.celery_app.tasks import async_analyze_feedback
from pymongo import MongoClient

load_dotenv(override=True)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "SentinelEye")

def get_db_connection():
    client = MongoClient(MONGODB_URI)
    return client[DB_NAME]

def init_historical_data(days: int = 30):
    """
    初始化历史数据：回溯爬取过去 N 天帖子
    并对命中条件的帖子投递异步分析任务
    """
    target_date = datetime.now(UTC) - timedelta(days=days)
    print(f"开始初始化：爬取直到 {target_date.strftime('%Y-%m-%d')} 的历史帖子")

    # 调用回溯函数
    crawl_until_date(target_date)

    print("历史帖子爬取完成！")

    # 可选：爬完后，批量投递未分析的帖子（防止漏掉）
    db = get_db_connection()
    collection = db.feedbacks

    # 找这段时间内未分析的帖子
    cutoff_date = datetime.now(UTC) - timedelta(days=days)
    posts = collection.find({
        "created_at": {"$gte": cutoff_date},
        "ai_analyzed": {"$ne": True}
    })

    count = 0
    for post in posts:
        feedback_id = str(post["_id"])

        # 这里复用你的判断逻辑（关键词 + 图片 + 热度）
        need_analyze = False
        title = post.get("title", "").lower()
        content = post.get("content", "").lower()
        keywords = ["蓝屏", "bsod", "崩溃", "卡死", "黑屏", "驱动", "死机", "闪退", "异常"]

        if any(k in title or k in content for k in keywords):
            need_analyze = True
        if post.get("images"):
            need_analyze = True
        if post.get("reply_count", 0) >= 5 or post.get("view_count", 0) >= 100:
            need_analyze = True

        if need_analyze:
            async_analyze_feedback.delay(feedback_id)
            print(f"投递历史帖子分析: {post.get('title', '无标题')} ({feedback_id})")
            count += 1

    print(f"初始化完成！共投递 {count} 个历史帖子任务")

if __name__ == "__main__":
    # 默认爬30天，可传参数改
    init_historical_data(days=30)