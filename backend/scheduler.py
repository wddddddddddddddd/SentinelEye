from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import logging
from datetime import datetime

from backend.crawler.fans_feedback import crawl_incremental_once  # 👈 你的爬虫函数

# ======================
# 日志
# ======================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ======================
# Scheduler 初始化
# ======================
executors = {
    "default": ThreadPoolExecutor(max_workers=5)
}

scheduler = BlockingScheduler(
    executors=executors,
    timezone="Asia/Shanghai"
)

# ======================
# 事件监听（可选但强烈推荐）
# ======================
def job_listener(event):
    if event.exception:
        logging.error(f"任务异常: {event.job_id}")
    else:
        logging.info(f"任务完成: {event.job_id}")

scheduler.add_listener(
    job_listener,
    EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
)

# ======================
# Job 定义
# ======================
def crawl_job():
    logging.info("开始执行增量爬虫")
    crawl_incremental_once()
    logging.info("增量爬虫执行完成")

# 每小时执行一次
scheduler.add_job(
    crawl_job,
    trigger="interval",
    minutes=40,
    id="incremental_crawler",
    replace_existing=True,
    max_instances=1,     # 防止重入
    coalesce=True        # 堆积时合并
)

# ======================
# 启动
# ======================
if __name__ == "__main__":
    logging.info("SentinelEye 调度器启动")
    crawl_job()  # 启动立刻跑一次
    scheduler.start()
