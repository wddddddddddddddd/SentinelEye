# crawler/fans_360_crawler.py
import re
import time
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple, Dict, Any
from urllib.parse import urljoin

import requests
from lxml import etree
from tqdm import tqdm

from config.settings import CRAWLER_CONFIG
from core.mongo_client import mongodb_client

# ------------------------------
# 配置
# ------------------------------
HEADERS = CRAWLER_CONFIG["headers"]
BASE_FORUM = CRAWLER_CONFIG["base_forum"]
SITE_DOMAIN = CRAWLER_CONFIG["site_domain"]
MAX_PAGES_PER_RUN = CRAWLER_CONFIG["max_pages_per_run"]
REQUEST_TIMEOUT = CRAWLER_CONFIG["request_timeout"]
RETRY_TIMES = CRAWLER_CONFIG["retry_times"]
DELAY_BETWEEN_POSTS = CRAWLER_CONFIG["delay_between_posts"]
DELAY_BETWEEN_PAGES = CRAWLER_CONFIG["delay_between_pages"]

logger = logging.getLogger(__name__)


# ------------------------------
# 数据类
# ------------------------------
@dataclass
class PostItem:
    post_id: str
    title: str
    username: str
    category: str
    status: str
    has_attachment: bool
    created_at: str
    view_count: int
    reply_count: int
    url: str
    content: str
    images: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，标准化时间格式"""
        import time
        from datetime import datetime

        # 标准化 created_at 格式
        created_at_original = self.created_at
        created_at_standard = self.created_at

        # 解析时间戳（用于排序）
        created_timestamp = 0

        try:
            # 标准化日期格式：2025-12-7 08:53 → 2025-12-07 08:53:00
            if created_at_original:
                # 分割日期和时间
                parts = created_at_original.strip().split()
                if len(parts) >= 1:
                    # 标准化日期部分
                    date_part = parts[0]
                    date_parts = date_part.split('-')
                    if len(date_parts) == 3:
                        year, month, day = date_parts
                        month = month.zfill(2)  # 12 → 12
                        day = day.zfill(2)  # 7 → 07
                        date_std = f"{year}-{month}-{day}"
                    else:
                        date_std = date_part

                    # 标准化时间部分
                    time_std = "00:00:00"
                    if len(parts) >= 2:
                        time_part = parts[1]
                        time_parts = time_part.split(':')
                        if len(time_parts) >= 2:
                            hour = time_parts[0].zfill(2)
                            minute = time_parts[1].zfill(2)
                            second = time_parts[2].zfill(2) if len(time_parts) >= 3 else "00"
                            time_std = f"{hour}:{minute}:{second}"

                    created_at_standard = f"{date_std} {time_std}"

                    # 转换为时间戳
                    try:
                        dt = datetime.strptime(created_at_standard, "%Y-%m-%d %H:%M:%S")
                        created_timestamp = int(dt.timestamp())
                    except:
                        # 如果解析失败，使用当前时间戳
                        created_timestamp = int(time.time())
        except Exception as e:
            logger.warning(f"标准化时间格式失败 {created_at_original}: {e}")
            created_timestamp = int(time.time())

        return {
            "post_id": self.post_id,
            "title": self.title,
            "username": self.username,
            "category": self.category,
            "status": self.status,
            "has_attachment": self.has_attachment,
            "created_at": created_at_standard,  # 标准化后的时间
            "created_at_original": created_at_original,  # 保留原始值
            "created_at_timestamp": created_timestamp,  # 时间戳（用于排序）
            "view_count": self.view_count,
            "reply_count": self.reply_count,
            "url": self.url,
            "content": self.content,
            "images": self.images,
            "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "crawl_timestamp": int(time.time())
        }


# ------------------------------
# 网络工具
# ------------------------------
def safe_get_text(url: str, retries: int = RETRY_TIMES, timeout: int = REQUEST_TIMEOUT) -> Optional[str]:
    """带重试的GET请求"""
    if not url:
        return None

    for i in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            if resp.status_code == 200:
                return resp.text
            logger.warning(f"请求失败 {url}: 状态码 {resp.status_code}")
            time.sleep(0.5)
        except Exception as e:
            logger.debug(f"请求异常 ({i + 1}/{retries}) {url}: {e}")
            time.sleep(0.5)

    logger.error(f"请求失败，已达最大重试次数: {url}")
    return None


def fetch_tree(url: str) -> Optional[etree._Element]:
    """获取页面并解析为HTML树"""
    txt = safe_get_text(url)
    if txt:
        return etree.HTML(txt)
    return None


# ------------------------------
# 辅助解析函数
# ------------------------------
def get_tbody_list(tree: etree._Element):
    """获取帖子tbody列表"""
    sep = tree.xpath("//tbody[@id='separatorline']")
    if sep:
        return tree.xpath("//tbody[@id='separatorline']/following-sibling::tbody")
    return tree.xpath("//tbody")


def extract_main_content(tree: etree._Element):
    """提取正文内容和图片"""
    try:
        main = tree.xpath('(//td[contains(@class, "t_f")])[1]')
        if not main:
            return "", []
        main = main[0]

        # 提取文本
        texts = main.xpath('.//text()')
        exclude_keywords = ['下载附件', '360社区', '上传', '本帖最后由', '编辑', 'KB', 'MB', 'B']
        parts = []

        for t in texts:
            s = t.strip()
            if not s:
                continue
            if any(k in s for k in exclude_keywords):
                continue
            if re.match(r'^\(\d+\.?\d*\s*(KB|MB|B)\)$', s):
                continue
            if '.' in s and not re.search(r'[\u4e00-\u9fff]', s):
                continue
            parts.append(s)

        content = "\n".join(parts)

        # 提取图片
        imgs = []
        for img in main.xpath('.//img'):
            zoom = img.get('zoomfile')
            src = zoom or img.get('src')
            if not src:
                continue
            if src.endswith('.gif'):
                continue
            src = urljoin(SITE_DOMAIN, src)
            imgs.append(src)

        return content, imgs
    except Exception as e:
        logger.error(f"提取正文失败: {e}")
        return "", []


def find_detail_href_from_tbody(tbody) -> Optional[str]:
    """从tbody中提取详情页链接"""
    a_list = tbody.xpath('./tr/th/div[2]//a[@href]')
    hrefs = []

    for a in a_list:
        h = a.get('href')
        if h:
            hrefs.append(h.strip())

    # 优先级匹配
    for h in hrefs:
        if 'thread-' in h or 'viewthread.php' in h:
            return urljoin(SITE_DOMAIN, h)

    # 回退
    if hrefs:
        return urljoin(SITE_DOMAIN, hrefs[0])

    return None


def safe_int(value) -> int:
    """安全转换整数"""
    if not value:
        return 0
    v = str(value).strip().replace(',', '')
    m = re.search(r'(\d+)', v)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return 0
    return 0


# ------------------------------
# 解析单条帖子
# ------------------------------
def parse_tbody(tbody) -> Optional[PostItem]:
    """解析单个tbody为PostItem"""
    try:
        # post_id
        post_id = tbody.get("id") or ""
        if not post_id:
            logger.warning("未找到post_id")
            return None

        # 分类和标题
        category_el = tbody.xpath('./tr/th/div[2]/a[1]/span/text()')
        has_category = bool(category_el)

        if has_category:
            title_el = tbody.xpath('./tr/th/div[2]/a[2]/text()')
            category = category_el[0].strip() if category_el else ""
        else:
            title_el = tbody.xpath('./tr/th/div[2]/a[1]/text()')
            category = ""

        title = title_el[0].strip() if title_el else ""

        # 用户信息
        username = ''.join(tbody.xpath('./tr/th/div[2]/div/span[1]/a/text()')).strip()
        created_at = ''.join(tbody.xpath('./tr/th/div[2]/div/span[3]/text()')).strip()

        # 状态和附件
        alt_list = tbody.xpath('./tr/th/div[2]/img/@alt')
        has_attachment = "attach_img" in alt_list
        status = next((x for x in alt_list if x != "attach_img"), "")

        # 统计信息
        view_count = ''.join(tbody.xpath('./tr/th/div[2]/div/a[2]/text()')).strip()
        reply_count = ''.join(tbody.xpath('./tr/th/div[2]/div/a[1]/text()')).strip()

        # 详情页链接
        url = find_detail_href_from_tbody(tbody) or ""

        # 提取正文和图片
        content = ""
        images = []
        if url:
            html = safe_get_text(url)
            if html:
                detail_tree = etree.HTML(html)
                content, images = extract_main_content(detail_tree)
            else:
                # 重试一次
                time.sleep(0.6)
                html = safe_get_text(url, retries=1)
                if html:
                    detail_tree = etree.HTML(html)
                    content, images = extract_main_content(detail_tree)

        return PostItem(
            post_id=post_id,
            title=title,
            username=username,
            category=category,
            status=status,
            has_attachment=has_attachment,
            created_at=created_at,
            view_count=safe_int(view_count),
            reply_count=safe_int(reply_count),
            url=url,
            content=content,
            images=images
        )

    except Exception as e:
        logger.error(f"解析帖子失败: {e}")
        return None


# ------------------------------
# 增量爬取核心逻辑（修复版）
# ------------------------------
def incremental_crawl(start_page: int = 1, max_pages: int = MAX_PAGES_PER_RUN) -> Tuple[int, int, int]:
    """
    增量爬取 - 遇到重复立即停止当前页面

    Returns:
        (成功插入数, 重复数, 爬取总数)
    """
    logger.info(f"开始增量爬取: 从第{start_page}页开始，最多{max_pages}页")

    success_count = 0
    duplicate_count = 0
    crawled_count = 0
    stop_crawling = False  # 控制是否停止整个爬取

    # 计算结束页
    end_page = start_page + max_pages - 1

    for page_num in tqdm(range(start_page, end_page + 1), desc="页面进度"):
        if stop_crawling:
            logger.info("已遇到重复数据，停止爬取")
            break

        forum_url = BASE_FORUM.format(page_num)
        logger.debug(f"正在爬取第{page_num}页: {forum_url}")

        # 获取页面
        tree = fetch_tree(forum_url)
        if tree is None:
            logger.warning(f"页面获取失败: {forum_url}")
            continue

        # 获取帖子列表
        tbodys = get_tbody_list(tree)
        if not tbodys:
            logger.warning(f"未找到帖子列表: {forum_url}")
            continue

        page_success = 0
        page_duplicate = 0

        # 处理当前页的每个帖子
        for tbody in tqdm(tbodys, desc=f"第{page_num}页帖子", leave=False):
            if stop_crawling:
                break

            # 解析帖子
            post_item = parse_tbody(tbody)
            if not post_item:
                continue

            crawled_count += 1

            # 检查是否已存在
            if mongodb_client.feedback_exists(post_item.post_id):
                logger.info(f"发现重复post_id: {post_item.post_id}，停止当前页面爬取")
                duplicate_count += 1
                stop_crawling = True  # 立即停止当前页面
                break  # 跳出当前页面的循环

            # 转换为字典并插入
            post_dict = post_item.to_dict()
            if mongodb_client.insert_feedback(post_dict):
                page_success += 1
                success_count += 1
            else:
                page_duplicate += 1
                duplicate_count += 1

            # 帖子间延时
            time.sleep(DELAY_BETWEEN_POSTS)

        logger.info(f"第{page_num}页完成: 插入{page_success}条，重复{page_duplicate}条")

        # 如果当前页没有成功插入任何新数据（可能都是重复的）
        if page_success == 0 and len(tbodys) > 0:
            logger.info(f"第{page_num}页没有新数据，可能已到最新位置")
            stop_crawling = True
            break

        # 页间延时
        if not stop_crawling:
            time.sleep(DELAY_BETWEEN_PAGES)

    total_count = success_count + duplicate_count
    logger.info(f"增量爬取完成: 成功{success_count}条，重复{duplicate_count}条，总共处理{total_count}条")

    # 验证数据库总数
    db_count = mongodb_client.count_feedbacks()
    logger.info(f"数据库当前共有{db_count}条记录")

    return success_count, duplicate_count, total_count


def crawl_specific_pages(start_page: int = 1, end_page: int = 3) -> Tuple[int, int, int]:
    """
    爬取指定页码范围（用于首次全量爬取）
    """
    logger.info(f"爬取指定页面: {start_page}到{end_page}页")

    success_count = 0
    duplicate_count = 0
    crawled_count = 0

    for page_num in tqdm(range(start_page, end_page + 1), desc="页面进度"):
        forum_url = BASE_FORUM.format(page_num)

        tree = fetch_tree(forum_url)
        if tree is None:
            logger.warning(f"页面获取失败: {forum_url}")
            continue

        tbodys = get_tbody_list(tree)
        if not tbodys:
            logger.warning(f"未找到帖子列表: {forum_url}")
            continue

        page_items = []
        for tbody in tbodys:
            post_item = parse_tbody(tbody)
            if post_item:
                page_items.append(post_item)
                crawled_count += 1
            time.sleep(DELAY_BETWEEN_POSTS)

        # 批量插入本页数据
        if page_items:
            page_dicts = [item.to_dict() for item in page_items]
            success, duplicate = mongodb_client.insert_many_feedbacks(page_dicts)
            success_count += success
            duplicate_count += duplicate
            logger.info(f"第{page_num}页: 插入{success}条，重复{duplicate}条")

        time.sleep(DELAY_BETWEEN_PAGES)

    logger.info(f"指定页面爬取完成: 成功{success_count}条，重复{duplicate_count}条")
    return success_count, duplicate_count, crawled_count


# ------------------------------
# 测试函数
# ------------------------------
def test_incremental_crawl():
    """测试增量爬取"""
    print("测试增量爬取...")

    # 先显示当前数据库状态
    count = mongodb_client.count_feedbacks()
    print(f"数据库当前有{count}条记录")

    # 获取最新一条记录
    latest = mongodb_client.get_latest_feedback()
    if latest:
        print(f"最新记录: {latest.get('post_id')} - {latest.get('title')}")

    # 运行增量爬取（只爬2页测试）
    success, duplicate, total = incremental_crawl(1, 2)

    print(f"测试结果: 成功{success}条，重复{duplicate}条，总共{total}条")


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 测试
    test_incremental_crawl()