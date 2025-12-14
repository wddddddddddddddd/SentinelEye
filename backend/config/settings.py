# config/settings.py
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 环境变量
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "sentineleye_db")
MONGODB_FEEDBACKS_COLLECTION = "feedbacks"

# 爬虫配置
CRAWLER_CONFIG = {
    "base_forum": "https://bbs.360.cn/forum.php?mod=forumdisplay&fid=140&orderby=dateline&filter=author&orderby=dateline&page={}",
    "site_domain": "https://bbs.360.cn/",
    "headers": {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/142.0.0.0 Safari/537.36"
        )
    },
    "max_pages_per_run": 30,  # 每次最多爬30页
    "request_timeout": 10,
    "retry_times": 3,
    "delay_between_posts": 0.15,  # 帖子间延时
    "delay_between_pages": 1,     # 页间延时
}