import os
import json
import base64
import requests
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import SystemMessage, HumanMessage
from pymongo import MongoClient
from bson import ObjectId

from backend.celery_app import celery  # 导入 celery 实例

load_dotenv(override=True)

if not os.getenv("DASHSCOPE_API_KEY"):
    raise RuntimeError("未设置 DASHSCOPE_API_KEY")

# MongoDB 配置
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "SentinelEye")


# 2. System Prompt 优化
# =========================

SYSTEM_PROMPT = """你是【360 客户端稳定性与蓝屏分析 AI】。

你需要分析来自用户社区的【真实用户反馈】，结合【截图内容 + 文本描述】，判断是否存在：

- 蓝屏（BSOD）
- 游戏卡死 / 黑屏
- 显卡 / 驱动异常
- 系统关键日志被关闭
- 可能影响问题溯源的配置异常

⚠️ 强制输出规则：
1. 只能输出 JSON，不允许任何额外文本
2. risk_level 只能是：low / medium / high
3. confidence 是 0~1 之间的小数
4. 只要涉及蓝屏 / 卡死 / 崩溃 / 驱动：need_followup 必须为 true

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


# 3. 模型初始化
# =========================

model = ChatTongyi(
    model="qwen3-vl-flash",
    temperature=0.2,
    max_tokens=1024
)


# 4. 工具函数
# =========================

def get_db_connection():
    """获取数据库连接"""
    client = MongoClient(MONGODB_URI)
    return client[DB_NAME]

def image_url_to_base64(url: str) -> str:
    """下载图片并转为 base64"""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode("utf-8")
    except Exception as e:
        print(f"⚠️ 图片下载失败: {url}, 错误: {e}")
        return ""

def build_messages(image_base64: str, forum_text: str):
    """构造多模态输入"""
    content = []
    
    # 如果有图片，先添加图片
    if image_base64:
        content.append({"image": f"data:image/jpeg;base64,{image_base64}"})
    
    # 添加文本
    content.append({"text": forum_text})
    
    return [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=content)
    ]

# Celery 异步任务
# ======================
@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def async_analyze_feedback(self, feedback_id: str):
    """
    异步执行 AI 分析
    feedback_id: MongoDB feedbacks 集合的 _id（字符串形式）
    """
    db = get_db_connection()
    
    try:
        obj_id = ObjectId(feedback_id)
        post = db.feedbacks.find_one({"_id": obj_id})
        
        if not post:
            raise ValueError(f"未找到 feedback_id: {feedback_id}")
        
        # 检查是否已经分析过（防止重复投递）
        if post.get("ai_analyzed", False):
            print(f"已跳过已分析的帖子: {post.get('title', '无标题')}")
            return {"status": "skipped", "reason": "already_analyzed"}
        
        print(f"开始异步分析: {post.get('title', '无标题')} ({feedback_id})")
        
        # 构建输入文本（和你原来一样）
        forum_text = f"""
【标题】
{post.get("title", "")}

【正文】
{post.get("content", "")}

【分类】{post.get("category", "")}
【状态】{post.get("status", "")}
【发帖人】{post.get("username", "")}
"""
        
        # 处理图片（只取第一张，和你原来一致）
        image_base64 = ""
        image_urls = post.get("images", [])
        if image_urls:
            image_base64 = image_url_to_base64(image_urls[0])
        
        # 调用模型
        messages = build_messages(image_base64, forum_text)
        response = model.invoke(messages)
        
        # 解析输出（和你原来完全一致）
        text_output = ""
        if isinstance(response.content, list):
            for item in response.content:
                if "text" in item:
                    text_output += item["text"]
        else:
            text_output = str(response.content)
        
        start_idx = text_output.find('{')
        end_idx = text_output.rfind('}') + 1
        if start_idx == -1 or end_idx <= start_idx:
            raise ValueError("未找到有效JSON")
        
        json_str = text_output[start_idx:end_idx]
        ai_result = json.loads(json_str)
        
        # 保存分析结果
        analysis_doc = {
            "post_id": post.get("post_id"),
            "feedback_id": feedback_id,
            "title": post.get("title", ""),
            "ai_result": ai_result,
            "model_used": "qwen3-vl-flash",
            "analyzed_at": datetime.utcnow(),
            "has_image": bool(image_urls),
            "image_count": len(image_urls)
        }
        
        result = db.ai_analysis.insert_one(analysis_doc)
        
        # 标记原帖已分析
        db.feedbacks.update_one(
            {"_id": obj_id},
            {"$set": {"ai_analyzed": True, "analysis_id": str(result.inserted_id)}}
        )
        
        print(f"异步分析完成: {feedback_id}")
        return {"status": "success", "analysis_id": str(result.inserted_id)}
        
    except Exception as exc:
        print(f"异步分析失败（将重试）: {exc}")
        raise self.retry(exc=exc)