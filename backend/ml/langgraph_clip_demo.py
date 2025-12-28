import os
import base64
import requests
from typing import TypedDict, Optional

from langgraph.graph import StateGraph
from langchain_community.chat_models.tongyi import ChatTongyi
import os
from dotenv import load_dotenv

load_dotenv(override=True)
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")


# =====================================================
# 1. 输入数据（你的 MongoDB 帖子）
# =====================================================

POST = {
    "post_id": "normalthread_16174804",
    "title": "是谁经常关闭蓝屏记录呀？？这都好几次了，",
    "content": (
        "CF游戏正玩着就卡停在某个画面，\n"
        "资源管理器都调不出来，键盘鼠标亮屏幕无信号，\n"
        "重启后蓝屏记录没打开好几次了，是谁关的？？这是怎么回事？？"
    ),
    "images": [
        "https://p0.ssl.qhmsg.com/t11e3f4274fea347e72ead757dd.jpg"
    ]
}

# =====================================================
# 2. LangGraph State
# =====================================================

class FeedbackState(TypedDict):
    post: dict
    enter_vl: bool
    ai_result: Optional[str]
    status: str

# =====================================================
# 3. 图片 → base64（真实 VL 所需）
# =====================================================

def image_url_to_base64(url: str) -> str:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return base64.b64encode(resp.content).decode("utf-8")

# =====================================================
# 4. 决策节点（这里故意简单）
#    👉 后面你可以接 CLIP / 规则 / OCR
# =====================================================

KEYWORDS = ["蓝屏", "黑屏", "无信号", "死机", "卡死"]

def decide_node(state: FeedbackState) -> FeedbackState:
    text = state["post"]["title"] + state["post"]["content"]
    state["enter_vl"] = any(k in text for k in KEYWORDS)
    print(f"[DECIDE] 是否进入 VL: {state['enter_vl']}")
    return state

# =====================================================
# 5. 真 · Tongyi VL 节点
# =====================================================

def tongyi_vl_node(state: FeedbackState) -> FeedbackState:
    post = state["post"]

    base64_img = image_url_to_base64(post["images"][0])

    messages = [
        {
            "role": "system",
            "content": (
                "你是360安全产品的AI分析助手，"
                "擅长分析用户反馈中的系统蓝屏、黑屏、死机问题。"
                "请输出【问题判断 + 可能原因 + 处理建议】。"
            )
        },
        {
            "role": "user",
            "content": [
                {"image": f"data:image/jpeg;base64,{base64_img}"},
                {
                    "text": (
                        f"帖子标题：{post['title']}\n\n"
                        f"帖子内容：{post['content']}\n\n"
                        "请结合图片与文本，判断是否属于系统蓝屏/显示异常问题。"
                    )
                }
            ]
        }
    ]

    model = ChatTongyi(model="qwen3-vl-flash")
    resp = model.invoke(messages)

    state["ai_result"] = resp.content
    state["status"] = "done"

    print("[VL] 通义 VL 已返回结果")
    return state

# =====================================================
# 6. Skip 节点
# =====================================================

def skip_node(state: FeedbackState) -> FeedbackState:
    state["status"] = "skipped"
    return state

# =====================================================
# 7. 条件分支
# =====================================================

def route(state: FeedbackState) -> str:
    return "vl" if state["enter_vl"] else "skip"

# =====================================================
# 8. 构建 LangGraph
# =====================================================

def build_graph():
    g = StateGraph(FeedbackState)

    g.add_node("decide", decide_node)
    g.add_node("vl", tongyi_vl_node)
    g.add_node("skip", skip_node)

    g.set_entry_point("decide")

    g.add_conditional_edges(
        "decide",
        route,
        {"vl": "vl", "skip": "skip"}
    )

    g.set_finish_point("vl")
    g.set_finish_point("skip")

    return g.compile()

# =====================================================
# 9. 主函数
# =====================================================

if __name__ == "__main__":
    app = build_graph()

    result = app.invoke({
        "post": POST,
        "enter_vl": False,
        "ai_result": None,
        "status": "pending"
    })

    print("\n================= AI 最终输出 =================\n")
    print(result["ai_result"])
