import requests
from lxml import etree
import re


headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0"}

url = "https://bbs.360.cn/forum.php?mod=forumdisplay&fid=140&page=1"

response = requests.get(url=url, headers=headers).text

tree = etree.HTML(response)


def get_target_tbody_list(tree):
    separatorline = tree.xpath("//tbody[@id='separatorline']")

    if separatorline:
        tbody_list = tree.xpath("//tbody[@id='separatorline']/following-sibling::tbody")
    else:
        tbody_list = tree.xpath("//tbody")
    return tbody_list


def extract_post_content(tree):
    """简化版内容提取，不依赖ID"""
    # 查找帖子主要内容区域
    # 通常是在class包含"t_f"或"postmessage"的元素中
    """改进版内容提取，只提取楼主的主内容"""

    # 方法1：优先查找楼主的帖子内容（通常是第一个包含t_f的td）
    main_content = tree.xpath('(//td[contains(@class, "t_f")])[1]')

    if not main_content:
        return "", []

    main_content_element = main_content[0]

    # 提取文本内容，但排除图片相关的描述文字
    content_elements = main_content_element.xpath('.//text()')
    content_parts = []

    # 要排除的关键词
    exclude_keywords = ['下载附件', '360社区', '上传', '本帖最后由', '编辑', 'B', 'KB', 'MB']

    for text in content_elements:
        cleaned_text = text.strip()
        if (cleaned_text and
                cleaned_text not in ['', ' '] and
                not any(keyword in cleaned_text for keyword in exclude_keywords) and
                # 排除纯数字和单位（文件大小）
                not re.match(r'^\(\d+\.?\d*\s*(KB|MB|B)\)$', cleaned_text) and
                # 排除纯文件名（不含中文）
                not ('.' in cleaned_text and not re.search(r'[\u4e00-\u9fff]', cleaned_text))):
            content_parts.append(cleaned_text)

    content = '\n'.join(content_parts)

    # 提取图片（只从楼主内容中提取）
    img_elements = main_content_element.xpath('.//img')
    img_list = []

    for img in img_elements:
        zoomfile = img.get('zoomfile')
        if zoomfile:
            img_list.append(zoomfile)
        else:
            src = img.get('src')
            if src and not src.endswith('.gif'):
                img_list.append(src)

    return content, img_list


tbody_list = get_target_tbody_list(tree)

print(len(tbody_list))

feedback = {
    "post_id": "119557379",
    "title": "",
    "username": "",
    "category": "",  # 分类前缀，如："问题反馈"、"人工服务"
    "status": "",
    "has_attachment": False,
    "created_at": "",
    "view_count": 0,
    "reply_count": 0,
    "url": "",
    "content": "",
    "images": [],           # 放图片链接就行
}

for tbody in tbody_list:
    # post_id
    feedback["post_id"] = tbody.get("id")

    # 获取title文本
    title_elements = tbody.xpath('./tr/th/div[2]/a[2]/text()')
    feedback["title"] = title_elements[0].strip() if title_elements else ""

    # 获取username文本
    username_elements = tbody.xpath('./tr/th/div[2]/div/span[1]/a/text()')
    feedback["username"] = username_elements[0].strip() if username_elements else ""

    # 先判断是否有分类标签
    category_elements = tbody.xpath('./tr/th/div[2]/a[1]/span/text()')
    has_category = bool(category_elements)

    if has_category:
        # 有分类的情况：分类在a[1]，标题在a[2]
        feedback["category"] = category_elements[0].strip()
        title_elements = tbody.xpath('./tr/th/div[2]/a[2]/text()')
        feedback["title"] = title_elements[0].strip() if title_elements else ""
    else:
        # 没有分类的情况：标题在a[1]
        feedback["category"] = ""
        title_elements = tbody.xpath('./tr/th/div[2]/a[1]/text()')
        feedback["title"] = title_elements[0].strip() if title_elements else ""

    # 提取所有img的alt属性
    alt_texts = tbody.xpath('./tr/th/div[2]/img/@alt')

    # 状态：过滤掉附件标记，取第一个状态
    feedback["status"] = next((text for text in alt_texts if text != "attach_img"), "")

    # 是否有附件：直接检查是否存在
    feedback["has_attachment"] = "attach_img" in alt_texts

    # created_at
    created_at_elements = tbody.xpath('./tr/th/div[2]/div/span[3]/text()')
    feedback["created_at"] = created_at_elements[0].strip() if created_at_elements else ""

    # view_count
    view_count_elements = tbody.xpath('./tr/th/div[2]/div/a[2]/text()')
    feedback["view_count"] = view_count_elements[0].strip() if view_count_elements else ""

    # reply_count
    reply_count_elements = tbody.xpath('./tr/th/div[2]/div/a[1]/text()')
    feedback["reply_count"] = reply_count_elements[0].strip() if reply_count_elements else ""

    # url
    url_elements = tbody.xpath('./tr/th/div[2]/a[2]/@href')
    feedback["url"] = url_elements[0].strip() if url_elements else ""

    detail_resp = requests.get(url=feedback["url"], headers=headers).text
    detail_tree = etree.HTML(detail_resp)
    content, img_list = extract_post_content(detail_tree)
    feedback["content"] = content
    feedback["images"] = img_list


    print(feedback)  # 查看结果