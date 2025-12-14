# crawler/scheduler.py
import logging
import sys
import os
import signal
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.fans_360_crawler import incremental_crawl
from core.mongo_client import mongodb_client

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler_scheduler.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 全局变量
scheduler = None
is_running = True


def signal_handler(sig, frame):
    """处理终止信号"""
    global is_running
    logger.info(f"接收到信号 {sig}，正在停止...")
    is_running = False

    if scheduler:
        scheduler.shutdown(wait=False)

    mongodb_client.close()
    logger.info("调度器已停止")
    sys.exit(0)


def crawl_job():
    """爬虫任务"""
    logger.info("=" * 60)
    logger.info(f"开始执行爬虫任务: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 显示数据库当前状态
        count = mongodb_client.count_feedbacks()
        logger.info(f"任务前数据库记录数: {count}")

        # 执行增量爬取
        success, duplicate, total = incremental_crawl(start_page=1, max_pages=2)

        # 记录结果
        logger.info(f"爬取结果: 新增{success}条，重复{duplicate}条，处理{total}条")

        # 显示更新后的状态
        new_count = mongodb_client.count_feedbacks()
        logger.info(f"任务后数据库记录数: {new_count}")

        if success > 0:
            logger.info(f"本次新增记录: {success}条")
        else:
            logger.info("没有新增记录")

    except Exception as e:
        logger.error(f"爬虫任务执行失败: {e}", exc_info=True)

    logger.info(f"爬虫任务结束: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)


def start_scheduler():
    """启动定时调度器"""
    global scheduler

    logger.info("启动360论坛爬虫定时调度器")
    logger.info("按 Ctrl+C 停止")

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill命令

    try:
        # 测试MongoDB连接
        mongodb_client.client.admin.command('ping')
        logger.info("MongoDB连接正常")

        # 创建调度器
        scheduler = BlockingScheduler()

        # 添加定时任务 - 每30分钟执行一次（测试用）
        scheduler.add_job(
            crawl_job,
            trigger='interval',
            minutes=1,
            id='incremental_crawl',
            name='360论坛增量爬取',
            replace_existing=True,
            max_instances=1  # 确保只有一个实例运行
        )

        logger.info("定时任务已添加: 每30分钟执行一次")

        # 立即执行一次（可选）
        # logger.info("立即执行第一次爬取...")
        # crawl_job()

        # 启动调度器
        scheduler.start()

    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"调度器启动失败: {e}", exc_info=True)
    finally:
        if scheduler:
            scheduler.shutdown()
        mongodb_client.close()
        logger.info("程序已完全退出")


def run_once():
    """只运行一次爬取（测试用）"""
    logger.info("执行单次爬取任务...")
    crawl_job()


if __name__ == "__main__":
    # 根据参数决定运行模式
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_once()
    else:
        start_scheduler()