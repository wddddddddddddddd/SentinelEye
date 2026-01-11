import time
import argparse
import requests
import re
from datetime import datetime, timedelta, UTC
from lxml import etree
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from backend.core.mongo_client import keywords_collection
import os


# ======================
# 基础配置
# ======================
HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0"
    )
}

BASE_URL = "https://bbs.360.cn/forum.php?mod=forumdisplay&fid=140&page={page}"

# ======================
# MongoDB 初始化
# ======================
# 从环境变量读取（有默认值，方便本地开发）
MONGO_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017/SentinelEye"
)
DB_NAME = os.getenv("DB_NAME", "SentinelEye")

# 初始化客户端
client = MongoClient(MONGO_URI)

db = client["SentinelEye"]
collection = db["feedbacks"]

collection.create_index([("post_id", ASCENDING)], unique=True)
collection.create_index("created_at")
collection.create_index("crawl_time")


# ======================
# 工具函数
# ======================

def parse_created_at(text: str) -> datetime | None:
    if not text:
        return None

    text = text.strip()
    now = datetime.now(UTC)

    # YYYY-MM-DD HH:MM
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)
    except ValueError:
        pass

    # YYYY-MM-DD
    try:
        return datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        pass

    # 支持其他格式：YYYY/MM/DD, YYYY.MM.DD
    try:
        text = text.replace("/", "-").replace(".", "-")
        return datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        pass

    # 今天
    if text == "今天":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 昨天
    if text == "昨天":
        return (now - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    # HH:MM → 今天
    if re.match(r"^\d{1,2}:\d{2}$", text):
        hour, minute = map(int, text.split(":"))
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    return None


def safe_int(text: str) -> int:
    try:
        return int(text)
    except Exception:
        return 0


# ======================
# HTTP 抓取
# ======================
def fetch_page(page: int) -> etree._Element:
    url = BASE_URL.format(page=page)
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return etree.HTML(resp.text)


def get_target_tbody_list(tree):
    separatorline = tree.xpath("//tbody[@id='separatorline']")
    if separatorline:
        return tree.xpath("//tbody[@id='separatorline']/following-sibling::tbody")
    return tree.xpath("//tbody")


# ======================
# 内容解析
# ======================
def extract_post_content(tree):
    main_content = tree.xpath('(//td[contains(@class, "t_f")])[1]')
    if not main_content:
        return "", []

    main = main_content[0]
    texts = main.xpath('.//text()')

    exclude_keywords = ['下载附件', '360社区', '上传', '本帖最后由', '编辑', 'B', 'KB', 'MB']
    content_parts = []

    for text in texts:
        t = text.strip()
        if (
                t
                and not any(k in t for k in exclude_keywords)
                and not re.match(r'^\(\d+\.?\d*\s*(KB|MB|B)\)$', t)
                and not ('.' in t and not re.search(r'[\u4e00-\u9fff]', t))
        ):
            content_parts.append(t)

    images = [
        img.get('zoomfile') or img.get('src')
        for img in main.xpath('.//img')
    ]

    return "\n".join(content_parts), images


def parse_post_list(tree):
    posts = []

    for tbody in get_target_tbody_list(tree):
        post_id = tbody.get("id")
        if not post_id:
            continue

        post = {
            "post_id": post_id,
            "title": "",
            "username": "",
            "category": "",
            "status": "",
            "has_attachment": False,
            "created_at": None,
            "view_count": 0,
            "reply_count": 0,
            "url": "",
            "content": "",
            "images": [],
            "crawl_time": datetime.now(UTC)  # 修复：使用 datetime.now(UTC)
        }

        category = tbody.xpath('./tr/th/div[2]/a[1]/span/text()')
        if category:
            post["category"] = category[0].strip()
            post["title"] = "".join(tbody.xpath('./tr/th/div[2]/a[2]/text()')).strip()
            post["url"] = "".join(tbody.xpath('./tr/th/div[2]/a[2]/@href')).strip()
        else:
            post["title"] = "".join(tbody.xpath('./tr/th/div[2]/a[1]/text()')).strip()
            post["url"] = "".join(tbody.xpath('./tr/th/div[2]/a[1]/@href')).strip()

        post["username"] = "".join(
            tbody.xpath('./tr/th/div[2]/div/span[1]/a/text()')
        ).strip()

        created_str = "".join(
            tbody.xpath('./tr/th/div[2]/div/span[3]/text()')
        ).strip()

        post["created_at"] = parse_created_at(created_str)

        post["reply_count"] = safe_int(
            "".join(tbody.xpath('./tr/th/div[2]/div/a[1]/text()'))
        )
        post["view_count"] = safe_int(
            "".join(tbody.xpath('./tr/th/div[2]/div/a[2]/text()'))
        )

        alt_texts = tbody.xpath('./tr/th/div[2]/img/@alt')
        post["status"] = next((x for x in alt_texts if x != "attach_img"), "")
        post["has_attachment"] = "attach_img" in alt_texts

        posts.append(post)

    return posts


def enrich_post(post: dict) -> dict:
    resp = requests.get(post["url"], headers=HEADERS, timeout=10)
    tree = etree.HTML(resp.text)
    post["content"], post["images"] = extract_post_content(tree)
    return post


def save_post(post: dict) -> bool:
    try:
        collection.insert_one(post)
        return True
    except DuplicateKeyError:
        return False


# ======================
# 爬虫模式
# ======================
def crawl_once(limit=3):
    page = 1
    count = 0

    while count < limit:
        tree = fetch_page(page)
        posts = parse_post_list(tree)

        for post in posts:
            post = enrich_post(post)
            save_post(post)
            print(f"[ONCE] {post['title']}")
            count += 1
            if count >= limit:
                return
        page += 1


def crawl_until_date(target_date: datetime):
    """回溯爬取，直到指定日期"""
    if target_date is None:
        print("错误：提供的日期格式无法识别")
        return

    page = 1
    print(f"开始回溯爬取，直到日期: {target_date.strftime('%Y-%m-%d')}")

    while True:
        tree = fetch_page(page)
        posts = parse_post_list(tree)

        if not posts:
            print("没有更多帖子")
            break

        for post in posts:
            # 如果帖子没有日期，跳过比较
            if post["created_at"] is None:
                print(f"警告：帖子 '{post['title']}' 没有日期信息，跳过")
                continue

            # 如果帖子日期早于目标日期，停止爬取
            if post["created_at"] < target_date:
                print(f"达到目标日期，停止爬取 (帖子日期: {post['created_at'].strftime('%Y-%m-%d')})")
                return

            # 爬取帖子内容
            try:
                post = enrich_post(post)
                saved = save_post(post)
                if saved:
                    print(f"[DATE] {post['title']} ({post['created_at'].strftime('%Y-%m-%d')})")
                else:
                    print(f"[SKIP] {post['title']} 已存在")
            except Exception as e:
                print(f"处理帖子失败: {post['title']}, 错误: {e}")

        page += 1
        time.sleep(1)  # 添加延迟避免被封


def crawl_incremental_once():
    """增量爬取：爬取最近3天的帖子，更新状态"""
    cutoff_date = datetime.now(UTC) - timedelta(days=3)
    print(f"增量爬取最近3天的帖子（从{cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}到现在）")

    page = 1
    new_post_count = 0
    updated_post_count = 0

    while True:
        try:
            tree = fetch_page(page)
            posts = parse_post_list(tree)

            if not posts:
                print("没有更多帖子")
                break

            # 检查本页帖子是否都早于3天
            earliest_date_in_page = min(
                (post["created_at"] for post in posts if post["created_at"] is not None),
                default=None
            )

            # 如果最早帖子日期早于3天，且所有帖子都早于3天，则停止
            if earliest_date_in_page and earliest_date_in_page < cutoff_date:
                all_old = all(
                    post["created_at"] and post["created_at"] < cutoff_date
                    for post in posts if post["created_at"] is not None
                )
                if all_old:
                    print(f"本页所有帖子都早于{cutoff_date.strftime('%Y-%m-%d')}，停止增量爬取")
                    break

            # 处理本页帖子
            for post in posts:
                # 如果帖子没有日期，跳过
                if post["created_at"] is None:
                    continue

                # 如果帖子早于3天，跳过
                if post["created_at"] < cutoff_date:
                    print(f"跳过3天前的帖子: {post['title']} ({post['created_at'].strftime('%Y-%m-%d')})")
                    continue

                # 检查帖子是否已存在
                existing_post = collection.find_one({"post_id": post["post_id"]})

                try:
                    # 获取帖子详情
                    enriched_post = enrich_post(post)
                    enriched_post["crawl_time"] = datetime.now(UTC)

                    if existing_post:
                        # 帖子已存在，检查状态是否有变化
                        old_status = existing_post.get("status", "")
                        new_status = enriched_post.get("status", "")

                        # 需要更新的字段
                        update_data = {
                            "crawl_time": enriched_post["crawl_time"],
                            "reply_count": enriched_post.get("reply_count", 0),
                            "view_count": enriched_post.get("view_count", 0),
                        }

                        # 如果状态变化了，更新状态
                        if old_status != new_status:
                            update_data["status"] = new_status
                            print(f"[UPDATE] 状态更新: {enriched_post['title']} - {old_status} → {new_status}")
                            updated_post_count += 1
                        else:
                            # 即使状态没变化，也更新其他信息
                            print(f"[UPDATE] 信息更新: {enriched_post['title']}")
                            updated_post_count += 1

                        # 执行更新
                        collection.update_one(
                            {"post_id": enriched_post["post_id"]},
                            {"$set": update_data}
                        )

                    else:
                        # 新帖子，插入数据库
                        result = collection.insert_one(enriched_post)
                        inserted_id = str(result.inserted_id)
                        print(f"[NEW] 新增帖子: {enriched_post['title']} (feedback_id={inserted_id})")
                        new_post_count += 1

                        # ======================
                        # 初步判断是否需要投递给大模型
                        # ======================
                        need_analyze = False
                        title = enriched_post.get("title", "").lower()
                        content = enriched_post.get("content", "").lower()

                        # --- 动态关键词触发 ---
                        keyword_docs = keywords_collection.find({}, {"keyword": 1, "_id": 0})
                        keywords = [doc["keyword"].lower() for doc in keyword_docs if doc.get("keyword")]
                        if keywords and any(k in title or k in content for k in keywords):
                                need_analyze = True
                                print(f"关键词命中触发分析: {inserted_id}")

                        # 有图片（尤其是可能截图）
                        # if enriched_post.get("images"):
                        #     need_analyze = True

                        # # 回复数或浏览数较高（表示关注度高）
                        # if enriched_post.get("reply_count", 0) >= 5 or enriched_post.get("view_count", 0) >= 100:
                        #     need_analyze = True

                        if need_analyze:
                            from backend.celery_app.tasks import async_analyze_feedback
                            async_analyze_feedback.delay(inserted_id)  # 异步投递
                            print(f"已投递异步AI分析任务: {inserted_id}")
                        else:
                            print(f"无需深度分析，跳过投递: {inserted_id}")

                except Exception as e:
                    print(f"处理帖子失败: {post['title']}, 错误: {e}")
                    continue

            print(f"已处理第{page}页")
            page += 1
            time.sleep(1)  # 请求间隔

        except Exception as e:
            print(f"获取第{page}页失败: {e}")
            break

    print(f"增量爬取完成！新增 {new_post_count} 个帖子，更新 {updated_post_count} 个帖子")


def crawl_forever(interval_seconds=3600):
    print(f"启动永久增量爬虫，检查间隔: {interval_seconds}秒")
    print(f"每次检查将爬取最近3天的帖子并更新状态")

    while True:
        try:
            print(f"\n[{datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}] 开始检查最近3天帖子...")
            crawl_incremental_once()
            print(f"[{datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}] 检查完成")
        except Exception as e:
            print(f"ERROR: {e}")

        print(f"等待 {interval_seconds} 秒后再次检查...")
        time.sleep(interval_seconds)

# ======================
# CLI
# ======================
def main():
    parser = argparse.ArgumentParser(
        description="360 论坛增量爬虫（支持单次 / 日期回溯 / 永久运行）"
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--once",
        action="store_true",
        help="单次运行，抓取最新帖子（默认 3 条）"
    )
    mode.add_argument(
        "--date",
        type=str,
        help="回溯爬取，直到指定日期（支持 2025/12/21 | 2025-12-21 | 2025.12.21）"
    )
    mode.add_argument(
        "--forever",
        action="store_true",
        help="永久运行的增量爬虫（默认每 1 小时执行一次）"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="--once 模式下抓取的最大帖子数量（默认 3）"
    )

    args = parser.parse_args()

    if args.once:
        crawl_once(limit=args.limit)
    elif args.date:
        # 验证日期格式
        target_date = parse_created_at(args.date)
        if target_date is None:
            print(f"错误：无法识别的日期格式 '{args.date}'")
            print("支持的格式: YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD, YYYY-MM-DD HH:MM")
            return
        crawl_until_date(target_date)
    elif args.forever:
        crawl_forever()


if __name__ == "__main__":
    main()