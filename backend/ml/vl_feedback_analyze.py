import os
import json
import base64
import requests
from dotenv import load_dotenv

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import SystemMessage, HumanMessage

# =========================
# 1. 环境变量
# =========================

load_dotenv(override=True)

if not os.getenv("DASHSCOPE_API_KEY"):
    raise RuntimeError("未设置 DASHSCOPE_API_KEY")

# =========================
# 2. System Prompt（为你的真实业务定制）
# =========================

SYSTEM_PROMPT = """
你是【360 客户端稳定性与蓝屏分析 AI】。

你需要分析来自用户社区的【真实用户反馈】，
结合【截图内容 + 文本描述】，判断是否存在：

- 蓝屏（BSOD）
- 游戏卡死 / 黑屏
- 显卡 / 驱动异常
- 系统关键日志被关闭
- 可能影响问题溯源的配置异常

⚠️ 强制输出规则：
1. 只能输出 JSON，不允许任何额外文本
2. risk_level 只能是：low / medium / high
3. confidence 是 0~1 之间的小数
4. 只要涉及蓝屏 / 卡死 / 崩溃 / 驱动：
   need_followup 必须为 true

JSON 结构如下（字段不可缺失）：
{
  "scene": "",
  "risk_type": "",
  "risk_level": "",
  "confidence": 0.0,
  "key_evidence": [],
  "analysis": "",
  "suggestions": [],
  "need_followup": false
}
"""

# =========================
# 3. 工具函数
# =========================

def image_url_to_base64(url: str) -> str:
    """下载图片并转为 base64"""
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return base64.b64encode(resp.content).decode("utf-8")


def build_messages(image_base64: str, forum_text: str):
    """构造多模态输入"""
    return [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=[
                {"image": f"data:image/jpeg;base64,{image_base64}"},
                {"text": forum_text}
            ]
        )
    ]

# =========================
# 4. 模型初始化
# =========================

model = ChatTongyi(
    model="qwen3-vl-flash",
    temperature=0.2,
    max_tokens=1024
)

# =========================
# 5. 核心分析函数（直接对接 MongoDB 数据）
# =========================

def analyze_forum_post(post: dict) -> dict:
    """
    输入：MongoDB 中的一条 forum post
    输出：结构化 AI 分析结果
    """

    # 拼接用户真实语境（非常重要）
    forum_text = f"""
【标题】
{post.get("title")}

【正文】
{post.get("content")}

【分类】{post.get("category")}
【状态】{post.get("status")}
"""

    # 默认只取第一张图（安全产品里这是常规做法）
    image_url = post.get("images", [None])[0]
    if not image_url:
        raise ValueError("该帖子标记为有附件，但未找到图片")

    image_base64 = image_url_to_base64(image_url)

    messages = build_messages(
        image_base64=image_base64,
        forum_text=forum_text
    )

    response = model.invoke(messages)

    # 通义返回 content 是 list
    raw_content = response.content
    text_output = ""

    if isinstance(raw_content, list):
        for item in raw_content:
            if "text" in item:
                text_output += item["text"]

    try:
        result = json.loads(text_output)
    except json.JSONDecodeError:
        raise ValueError(
            "模型输出不是合法 JSON\n"
            f"原始输出:\n{text_output}"
        )

    # 补充系统字段（方便你回写 MongoDB）
    result["post_id"] = post.get("post_id")
    result["model"] = "qwen3-vl-flash"
    result["source"] = "forum_multimodal_ai"

    return result

# =========================
# 6. 本地测试（用你给的真实数据）
# =========================

if __name__ == "__main__":
    forum_post = {
        "post_id": "normalthread_16174804",
        "title": "是谁经常关闭蓝屏记录呀？？这都好几次了，",
        "category": "问题反馈",
        "status": "已答复",
        "content": (
            "CF游戏正玩着就卡停在某个画面，\n"
            "资源管理器都调不出来，键盘鼠标亮屏幕无信号，\n"
            "重启后蓝屏记录没打开好几次了，是谁关的？？这是怎么回事？？"
        ),
        "images": [
            "https://p0.ssl.qhmsg.com/t11e3f4274fea347e72ead757dd.jpg"
        ]
    }

    analysis = analyze_forum_post(forum_post)

    print("===== AI 分析结果 =====")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
