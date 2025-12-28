import time
import threading
from queue import Queue
from datetime import datetime

# =========================
# 1. 模拟 MongoDB collections
# =========================

POSTS_COLLECTION = []
AI_ANALYSIS_COLLECTION = []

# =========================
# 2. 模拟三条帖子入库
# =========================

def mock_insert_posts():
    posts = [
        {
            "post_id": "p1",
            "title": "今天电脑突然蓝屏了",
            "content": "玩游戏的时候直接黑屏重启",
            "images": ["bsod.jpg"],
            "ai_check": {"status": "pending"}
        },
        {
            "post_id": "p2",
            "title": "软件界面太丑了",
            "content": "建议 UI 再优化一下",
            "images": [],
            "ai_check": {"status": "pending"}
        },
        {
            "post_id": "p3",
            "title": "又是蓝屏日志没开",
            "content": "重启后发现蓝屏记录关闭",
            "images": ["360_fix.jpg"],
            "ai_check": {"status": "pending"}
        }
    ]

    POSTS_COLLECTION.extend(posts)
    print(f"📥 已入库帖子数量: {len(posts)}")


# =========================
# 3. 关键词命中规则
# =========================

BSOD_KEYWORDS = ["蓝屏", "BSOD", "黑屏", "死机", "卡死"]

def text_hit(post):
    text = post["title"] + post["content"]
    return any(k in text for k in BSOD_KEYWORDS)


# =========================
# 4. 模拟 CLIP 图片命中
# =========================

def clip_image_hit(post):
    """
    这里只是模拟：
    有图片名就认为命中
    """
    return bool(post.get("images"))


# =========================
# 5. AI 分析（mock Qwen-VL）
# =========================

def mock_qwen_vl_analysis(post):
    print(f"🤖 AI 分析中: {post['post_id']}")
    time.sleep(2)  # 模拟模型耗时

    return {
        "post_id": post["post_id"],
        "risk_type": "bsod_related",
        "risk_level": "high",
        "confidence": 0.9,
        "analysis": "检测到蓝屏/黑屏相关描述，可能存在系统稳定性问题",
        "created_at": datetime.utcnow().isoformat()
    }


# =========================
# 6. AI Worker（模拟 Celery Worker）
# =========================

def ai_worker(task_queue: Queue):
    while True:
        post = task_queue.get()
        if post is None:
            break

        post["ai_check"]["status"] = "processing"

        result = mock_qwen_vl_analysis(post)

        AI_ANALYSIS_COLLECTION.append(result)

        post["ai_check"]["status"] = "done"
        post["ai_check"]["last_check_at"] = datetime.utcnow().isoformat()

        task_queue.task_done()


# =========================
# 7. 主流程
# =========================

def run_pipeline():
    task_queue = Queue()

    # 启动 worker
    worker_thread = threading.Thread(
        target=ai_worker,
        args=(task_queue,),
        daemon=True
    )
    worker_thread.start()

    # 遍历帖子，决定是否丢给 AI
    for post in POSTS_COLLECTION:
        hit_text = text_hit(post)
        hit_image = clip_image_hit(post)

        if hit_text or hit_image:
            print(f"✅ 命中 AI Check: {post['post_id']}")
            task_queue.put(post)
        else:
            post["ai_check"]["status"] = "skipped"

    # 等待任务完成
    task_queue.join()
    task_queue.put(None)

    print("\n===== AI 分析结果 =====")
    for r in AI_ANALYSIS_COLLECTION:
        print(r)


# =========================
# 8. 入口
# =========================

if __name__ == "__main__":
    mock_insert_posts()
    run_pipeline()
