import os
import json
import base64
import requests
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

from pymongo import MongoClient
from bson import ObjectId
from backend.celery_app import celery  # 确保导入你的 celery 实例

# =========================
# 1. 配置与初始化
# =========================
load_dotenv(override=True)

# 在你的 celery 配置文件中添加/修改
celery.conf.update(
    broker_connection_retry_on_startup=True, # 启动时自动重连
    redis_max_connections=20,                # 限制最大连接数，防止撑爆 Redis
    broker_transport_options={
        'visibility_timeout': 3600,          # 任务超时时间
        'socket_timeout': 30,                # 强制 socket 超时，防止挂死
        'retry_on_timeout': True
    }
)

# 优先检查 360 API KEY
if not os.getenv("API_KEY_360"):
    raise RuntimeError("未设置 360_API_KEY，无法进行 AI 分析")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "SentinelEye")

SYSTEM_PROMPT = """你是【360 客户端稳定性与蓝屏分析 AI】。
你的任务是分析用户反馈，并将其精准分类。

⚠️ 核心识别逻辑：
1. **BUG (故障)**：用户描述了程序崩溃、蓝屏、黑屏、功能不可用、报错代码等异常行为。
2. **SUGGESTION (建议)**：用户希望增加新功能、改变交互逻辑、或者对现有功能的改进想法。
3. **COMPLAINT (吐槽)**：无实质内容的情绪化表达（如“垃圾软件”）。

⚠️ 可信度 (reliability_score) 评估标准：
- 1.0: 有详细步骤 + 错误代码/截图 + 电脑配置信息。
- 0.7: 描述清晰但缺少截图或配置。
- 0.3: 描述模糊，仅说“坏了”、“打不开”。

⚠️ 强制输出 JSON 格式：
{
  "feedback_type": "BUG / SUGGESTION / COMPLAINT",
  "scene": "发生场景(如: 安装、游戏运行中、关机)",
  "issue_category": "分类(如: 蓝屏, 驱动冲突, UI交互, 功能缺失)",
  "risk_level": "low / medium / high",
  "reliability_score": 0.0,
  "key_evidence": ["提到的报错码", "截图中的关键文字"],
  "analysis": "简明扼要的故障原因或建议动机分析",
  "suggestions": ["给开发者的修复方向", "给用户的临时规避方案"],
  "need_followup": true/false
}

⚠️ 规则：只要涉及蓝屏/死机/数据丢失，risk_level 必须为 high，need_followup 必须为 true。
"""

# =========================
# 2. 工具函数 (内部调用)
# =========================
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]


def image_url_to_base64(url: str) -> str:
    try:
        resp = requests.get(url, timeout=15) # 爬虫环境下稍微放宽超时
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode("utf-8")
    except Exception as e:
        print(f"⚠️ 图片下载失败: {url}, 错误: {e}")
        return ""

def call_360_llm(messages):
    """直接调用 360 智脑 API，绕过 Langchain 兼容性问题"""
    url = "https://api.360.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('API_KEY_360')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-5.2", # 确认你的模型编码无误
        "messages": messages,
        "temperature": 1,
        "max_completion_tokens":2048,
        "stream": False
    }
    
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"360 API 调用失败 [{resp.status_code}]: {resp.text}")
    
    data = resp.json()
    choice = data["choices"][0]
    
    # 兼容性处理：如果 finish_reason 为空，某些逻辑可能会挂掉
    # 虽然这里直接取 content，但养成检查习惯更好
    content = choice.get("message", {}).get("content", "")
    
    if not content:
        raise ValueError("AI 返回内容为空，可能触发了敏感词过滤或接口异常")
        
    return content

def build_messages(image_base64: str, forum_text: str):
    """构造 OpenAI 格式的多模态输入"""
    user_content = []
    if image_base64:
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
        })
    user_content.append({"type": "text", "text": forum_text})

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]

# =========================
# 3. Celery 核心异步任务
# =========================

@celery.task(bind=True, max_retries=3, default_retry_delay=60, ignore_result=True)
def async_analyze_feedback(self, feedback_id: str):
    """
    异步执行 AI 分析（生产环境调用）
    """
    
    try:
        # 1. 获取数据
        obj_id = ObjectId(feedback_id)
        post = db.feedbacks.find_one({"_id": obj_id})
        
        if not post:
            return {"status": "error", "reason": f"未找到 ID 为 {feedback_id} 的文档"}
        
        # 重复性检查
        if post.get("ai_analyzed", False):
            return {"status": "skipped", "reason": "already_analyzed"}

        print(f"🚀 开始分析: {post.get('title', '无标题')} (ID: {feedback_id})")

        # 2. 构建 Prompt
        forum_text = f"【标题】\n{post.get('title', '')}\n\n【正文】\n{post.get('content', '')}\n\n【分类】{post.get('category', '')}"
        
        # 3. 处理图片
        image_base64 = ""
        image_urls = post.get("images", [])
        if image_urls:
            image_base64 = image_url_to_base64(image_urls[0])

        # 4. 调用 360 模型
        messages = build_messages(image_base64, forum_text)
        text_output = call_360_llm(messages)

        # 5. 解析结果 (健壮的 JSON 提取逻辑)
        start_idx = text_output.find('{')
        end_idx = text_output.rfind('}') + 1
        if start_idx == -1:
            raise ValueError(f"AI 回复未包含有效的 JSON: {text_output}")
        
        ai_result = json.loads(text_output[start_idx:end_idx])

        # 6. 保存分析结果
        analysis_doc = {
            "post_id": post.get("post_id"),
            "feedback_id": feedback_id,
            "title": post.get("title", ""),
            "ai_result": ai_result,
            "model_used": "360-gpt-5.2",
            "analyzed_at": datetime.utcnow(),
            "has_image": bool(image_base64),
            "alarm_sent": False
        }
        
        # 存入新集合 ai_analysis
        result = db.ai_analysis.insert_one(analysis_doc)
        
        # 回写原集合 feedbacks
        db.feedbacks.update_one(
            {"_id": obj_id},
            {"$set": {"ai_analyzed": True, "analysis_id": str(result.inserted_id)}}
        )

        print(f"✅ 分析成功并入库: {feedback_id}")
        return {"status": "success", "analysis_id": str(result.inserted_id)}

    except Exception as exc:
        print(f"❌ 异步分析失败: {exc}")
        # 触发 Celery 重试机制
        raise self.retry(exc=exc)
