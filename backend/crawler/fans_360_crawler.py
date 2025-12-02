# -*- coding: utf-8 -*-
import json
import re
import time
from dataclasses import dataclass, asdict
from typing import List, Optional
from urllib.parse import urljoin

import requests
from lxml import etree
from tqdm import tqdm

# ------------------------------
# 配置
# ------------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/142.0.0.0 Safari/537.36"
    )
}
BASE_FORUM = "https://bbs.360.cn/forum.php?mod=forumdisplay&fid=140&page={}"
SITE_DOMAIN = "https://bbs.360.cn/"

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


# ------------------------------
# 网络工具
# ------------------------------
def safe_get_text(url: str, retries: int = 3, timeout: int = 10) -> Optional[str]:
    """带重试的简单 GET（返回 text），空 url 会直接返回 None"""
    if not url:
        return None
    for i in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            if resp.status_code == 200:
                return resp.text
            # 非200也短暂等待再试
            time.sleep(0.5)
        except Exception as e:
            # 轻量打印，用于调试
            # print(f"[WARN] 请求异常 ({i+1}/{retries}): {e}")
            time.sleep(0.5)
    return None


def fetch_tree(url: str) -> Optional[etree._Element]:
    txt = safe_get_text(url)
    if txt:
        return etree.HTML(txt)
    return None


# ------------------------------
# 辅助解析函数
# ------------------------------
def get_tbody_list(tree: etree._Element):
    """获取帖子 tbody 列表，兼容 separatorline"""
    sep = tree.xpath("//tbody[@id='separatorline']")
    if sep:
        return tree.xpath("//tbody[@id='separatorline']/following-sibling::tbody")
    return tree.xpath("//tbody")


def extract_main_content(tree: etree._Element):
    """从详情页提取楼主文本和图片（更容错）"""
    try:
        main = tree.xpath('(//td[contains(@class, "t_f")])[1]')
        if not main:
            return "", []
        main = main[0]
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
            # 排除看起来像文件名但没有中文的
            if '.' in s and not re.search(r'[\u4e00-\u9fff]', s):
                continue
            parts.append(s)
        content = "\n".join(parts)

        imgs = []
        for img in main.xpath('.//img'):
            zoom = img.get('zoomfile')
            src = zoom or img.get('src')
            if not src:
                continue
            if src.endswith('.gif'):
                continue
            # 完整化相对 url
            src = urljoin(SITE_DOMAIN, src)
            imgs.append(src)
        return content, imgs
    except Exception:
        return "", []


def find_detail_href_from_tbody(tbody) -> Optional[str]:
    """
    更稳健地从 tbody 中找到详情页链接：
    - 优先选择 href 中包含 'thread-' 或 'viewthread.php' 的 a 标签
    - 如果找不到，则返回第一个 href（并做相对地址拼接）
    """
    # 在 div[2] 下找所有 a 标签
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

    # 回退到第一个可用 href
    if hrefs:
        return urljoin(SITE_DOMAIN, hrefs[0])
    return None


def safe_int(value):
    """从字符串里提取整数，失败返回 0"""
    if not value:
        return 0
    # 去掉逗号、空白
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
def parse_tbody(tbody) -> PostItem:
    # 初始化空字段
    post_id = tbody.get("id") or ""
    category_el = tbody.xpath('./tr/th/div[2]/a[1]/span/text()')
    has_category = bool(category_el)

    if has_category:
        title_el = tbody.xpath('./tr/th/div[2]/a[2]/text()')
        category = category_el[0].strip()
    else:
        title_el = tbody.xpath('./tr/th/div[2]/a[1]/text()')
        category = ""

    title = title_el[0].strip() if title_el else ""

    username = ''.join(tbody.xpath('./tr/th/div[2]/div/span[1]/a/text()')).strip()
    created_at = ''.join(tbody.xpath('./tr/th/div[2]/div/span[3]/text()')).strip()

    # 状态与附件
    alt_list = tbody.xpath('./tr/th/div[2]/img/@alt')
    has_attachment = "attach_img" in alt_list
    status = next((x for x in alt_list if x != "attach_img"), "")

    view_count = ''.join(tbody.xpath('./tr/th/div[2]/div/a[2]/text()')).strip()
    reply_count = ''.join(tbody.xpath('./tr/th/div[2]/div/a[1]/text()')).strip()

    # 细化解析 url（更稳健）
    url = find_detail_href_from_tbody(tbody) or ""

    # 请求详情页提取正文和图片
    content = ""
    images: List[str] = []
    if url:
        html = safe_get_text(url)
        if html:
            detail_tree = etree.HTML(html)
            content, images = extract_main_content(detail_tree)
        else:
            # 如果请求失败，可以尝试短暂休眠再试一次
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


# ------------------------------
# 主爬取流程（带 tqdm）
# ------------------------------
def crawl_forum(start_page: int = 1, end_page: int = 3) -> List[PostItem]:
    results: List[PostItem] = []
    pages = range(start_page, end_page + 1)
    for p in tqdm(pages, desc="Pages"):
        forum_url = BASE_FORUM.format(p)
        tree = fetch_tree(forum_url)
        if tree is None:
            tqdm.write(f"[WARN] 页面获取失败: {forum_url}")
            continue

        tbodys = get_tbody_list(tree)
        if not tbodys:
            tqdm.write(f"[WARN] 未在页面找到帖子列表: {forum_url}")
            continue

        for tbody in tqdm(tbodys, desc=f"Page {p} posts", leave=False):
            try:
                item = parse_tbody(tbody)
                results.append(item)
            except Exception as e:
                tqdm.write(f"[ERROR] 解析单条失败: {e}")
            time.sleep(0.15)  # 轻微延时，减缓请求压力

    return results


# ------------------------------
# 保存 JSON
# ------------------------------
def save_json(items: List[PostItem], filename: str = "result.json"):
    arr = [asdict(i) for i in items]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(arr, f, ensure_ascii=False, indent=2)
    print(f"[OK] 保存到 {filename}")


# ------------------------------
# 主程序
# ------------------------------
if __name__ == "__main__":
    start = 1
    end = 2  # 根据需要改为更多页
    posts = crawl_forum(start, end)
    save_json(posts, "../data/360_forum.json")
