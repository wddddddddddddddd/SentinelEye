import os
import json
import base64
import requests
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import SystemMessage, HumanMessage
from pymongo import MongoClient
from bson import ObjectId

# =========================
# 1. 环境变量
# =========================

load_dotenv(override=True)

if not os.getenv("DASHSCOPE_API_KEY"):
    raise RuntimeError("未设置 DASHSCOPE_API_KEY")

# MongoDB 配置
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "SentinelEye")

# =========================
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

# =========================
# 3. 模型初始化
# =========================

model = ChatTongyi(
    model="qwen3-vl-flash",
    temperature=0.2,
    max_tokens=1024
)

# =========================
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

# =========================
# 5. 核心分析函数
# =========================

def analyze_post_by_id(post_id: str) -> Dict[str, Any]:
    """
    根据post_id分析帖子
    
    Args:
        post_id: 帖子ID，可以是论坛的post_id或feedback的_id
        
    Returns:
        AI分析结果
    """
    db = get_db_connection()
    
    try:
        # 1. 从数据库获取帖子数据
        # 先尝试用feedback的_id查找
        if ObjectId.is_valid(post_id):
            post = db.feedbacks.find_one({"_id": ObjectId(post_id)})
        else:
            # 用post_id查找
            post = db.feedbacks.find_one({"post_id": post_id})
        
        if not post:
            raise ValueError(f"未找到帖子: {post_id}")
        
        print(f"✅ 找到帖子: {post.get('title', '无标题')}")
        
        # 2. 构建输入文本
        forum_text = f"""
【标题】
{post.get("title", "")}

【正文】
{post.get("content", "")}

【分类】{post.get("category", "")}
【状态】{post.get("status", "")}
【发帖人】{post.get("username", "")}
"""
        
        # 3. 处理图片
        image_urls = post.get("images", [])
        image_base64 = ""
        
        if image_urls:
            image_base64 = image_url_to_base64(image_urls[0])
            if not image_base64:
                print("⚠️ 图片下载失败，将仅使用文本分析")
        
        # 4. 调用AI模型
        messages = build_messages(image_base64, forum_text)
        response = model.invoke(messages)
        
        # 5. 解析AI响应
        text_output = ""
        if isinstance(response.content, list):
            for item in response.content:
                if "text" in item:
                    text_output += item["text"]
        else:
            text_output = str(response.content)
        
        # 提取JSON
        try:
            # 尝试找到JSON部分
            start_idx = text_output.find('{')
            end_idx = text_output.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = text_output[start_idx:end_idx]
                ai_result = json.loads(json_str)
            else:
                raise ValueError("未找到有效的JSON输出")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败，原始输出:\n{text_output}")
            raise ValueError(f"AI输出格式错误: {e}")
        
        # 6. 创建AI分析文档
        analysis_doc = {
            "post_id": post.get("post_id"),  # 论坛帖子ID
            "feedback_id": str(post["_id"]),  # feedback的_id
            "title": post.get("title", ""),
            "ai_result": ai_result,
            "model_used": "qwen3-vl-flash",
            "analyzed_at": datetime.utcnow(),
            "has_image": bool(image_urls),
            "image_count": len(image_urls)
        }
        
        # 7. 保存到AI分析集合
        ai_collection = db.ai_analysis
        result = ai_collection.insert_one(analysis_doc)
        analysis_doc["_id"] = str(result.inserted_id)
        
        # 8. 更新原feedback，标记为已分析
        db.feedbacks.update_one(
            {"_id": post["_id"]},
            {"$set": {"ai_analyzed": True, "analysis_id": str(result.inserted_id)}}
        )
        
        print(f"✅ AI分析完成并保存，分析ID: {result.inserted_id}")
        
        return analysis_doc
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        raise

# =========================
# 6. 辅助函数
# =========================

def get_analysis_by_post_id(post_id: str) -> Dict[str, Any]:
    """根据post_id获取AI分析结果"""
    db = get_db_connection()
    
    analysis = db.ai_analysis.find_one({"post_id": post_id})
    
    if analysis:
        # 转换为可JSON序列化的格式
        analysis["_id"] = str(analysis["_id"])
        if "feedback_id" in analysis:
            analysis["feedback_id"] = str(analysis["feedback_id"])
    
    return analysis

def check_if_analyzed(post_id: str) -> bool:
    """检查帖子是否已被分析"""
    db = get_db_connection()
    
    if ObjectId.is_valid(post_id):
        feedback = db.feedbacks.find_one({"_id": ObjectId(post_id)})
    else:
        feedback = db.feedbacks.find_one({"post_id": post_id})
    
    return feedback.get("ai_analyzed", False) if feedback else False

# =========================
# 7. 测试
# =========================

if __name__ == "__main__":
    # 测试用论坛post_id
    test_post_id = "normalthread_16174804"
    
    # 或者用feedback的_id
    # test_post_id = "694bfe8d98f0cb12c5146587"
    
    try:
        print(f"开始分析帖子: {test_post_id}")
        
        # 先检查是否已分析
        if check_if_analyzed(test_post_id):
            print("⚠️ 该帖子已被分析过")
            # 可以强制重新分析，或者直接获取结果
            analysis = get_analysis_by_post_id(test_post_id)
            if analysis:
                print("\n已有分析结果:")
                print(json.dumps(analysis, indent=2, ensure_ascii=False, default=str))
        else:
            # 进行AI分析
            result = analyze_post_by_id(test_post_id)
            
            print("\n✅ AI分析结果:")
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")