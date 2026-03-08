import os
from datetime import datetime, UTC
from dotenv import load_dotenv
from pymongo import MongoClient

from backend.crawler.fans_feedback import crawl_once  # 使用 crawl_once
from backend.celery_app.tasks import async_analyze_feedback
# from backend.core.mongo_client import keywords_collection  # 注释掉，不用动态加载

load_dotenv(override=True)

# ======================
# MongoDB 配置
# ======================
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "SentinelEye")

def get_db_connection():
    client = MongoClient(MONGODB_URI)
    return client[DB_NAME]

def init_historical_data(limit: int = 300):
    """
    初始化历史数据脚本（修改版：爬取最近 limit 条帖子）
    
    功能：
    1. 调用 crawl_once(limit) 爬取最近 limit 条帖子
    2. 关键词用硬编码 list（初始化时 collection 可能为空）
    3. 爬取完成后，筛选这批帖子中未分析的，投递异步 AI 任务
    """
    db = get_db_connection()
    collection = db.feedbacks
    
    # ======================
    # Step 1: 爬取最近 limit 条帖子
    # ======================
    print(f"[{datetime.now(UTC)}] 开始初始化：爬取最近 {limit} 条帖子（使用 crawl_once）")
    
    crawl_once(limit=limit)
    
    print(f"[{datetime.now(UTC)}] 爬取完成！总共处理 {limit} 条帖子，开始筛选并投递分析任务...")
    
    # ======================
    # Step 2: 硬编码关键词（初始化专用）
    # ======================
    keywords = [
        "蓝屏", "bsod", "崩溃", "卡死", "黑屏", "驱动", "死机", "闪退", "异常",
        "核晶防护", "蓝屏记录", "显卡", "驱动异常" 
    ]
    keywords = [k.lower() for k in keywords]
    print(f"使用硬编码关键词（共 {len(keywords)} 个）：{keywords[:10]}{'...' if len(keywords) > 10 else ''}")
    
    # ======================
    # Step 3: 查询最近爬取的帖子（按 crawl_time 降序，取最近 limit 条）
    # ======================
    recent_posts = collection.find().sort("crawl_time", -1).limit(limit)
    total_count = 0
    dispatched_count = 0
    
    for post in recent_posts:
        total_count += 1
        feedback_id = str(post["_id"])
        
        title_lower = post.get("title", "").lower()
        content_lower = post.get("content", "").lower()
        
        need_analyze = False
        reasons = []
        
        # 关键词触发
        if any(k in title_lower or k in content_lower for k in keywords) and post.get("images"):
            need_analyze = True
            reasons.append("关键词命中且有图片附件")
        
        # # 有图片触发
        # if post.get("images"):
        #     need_analyze = True
        #     reasons.append("有图片")
        
        # # 热度触发
        # if post.get("reply_count", 0) >= 5 or post.get("view_count", 0) >= 100:
        #     need_analyze = True
        #     reasons.append("热度高")
        
        # 只投递未分析过的
        if need_analyze and not post.get("ai_analyzed", False):
            async_analyze_feedback.delay(feedback_id)
            dispatched_count += 1
            print(f"[{dispatched_count}/{total_count}] 已投递: {post.get('title', '无标题')[:50]}... ({feedback_id}) 原因: {', '.join(reasons)}")
        else:
            print(f"[{total_count}] 跳过: {post.get('title', '无标题')[:50]}... ({feedback_id}) - 已分析或不符合条件")
    
    print(f"\n[{datetime.now(UTC)}] 初始化完成！")
    print(f"   处理了 {total_count} 条帖子")
    print(f"   成功投递 {dispatched_count} 个异步分析任务")
    print(f"   跳过 {total_count - dispatched_count} 个（已分析或无匹配）")
    print("   后续增量爬虫会自动接管新帖子～")

if __name__ == "__main__":
    # 可通过命令行参数改 limit，例如 python init_historical_data.py 500
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    init_historical_data(limit=limit)