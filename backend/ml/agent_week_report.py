# agent_week_report.py
# ============================================
# 智能生成【用户反馈周报】Agent（简化版 + 持久化）
# ============================================

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, TypedDict, Optional
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId

from langgraph.graph import StateGraph, END
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, SystemMessage
from pathlib import Path
# ============================================
# 1. 配置
# ============================================

# 指向 backend/.env
BASE_DIR = Path(__file__).resolve().parent.parent  # 上一级目录
load_dotenv(BASE_DIR / ".env", override=True)

print(BASE_DIR / ".env")  # ✅ 打印验证路径
print("DEEPSEEK_API_KEY =", os.getenv("DEEPSEEK_API_KEY"))
# MongoDB配置
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "SentinelEye")
COL_FEEDBACKS = "feedbacks"
COL_AI_ANALYSIS = "ai_analysis"
COL_REPORTS = "weekly_reports"  # 新增报告存储集合

# DeepSeek配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# 2. 状态定义
# ============================================

class WeekReportState(TypedDict):
    start_date: datetime
    end_date: datetime
    report_type: str
    report_id: str  # 新增：报告ID
    feedbacks: List[Dict]
    merged_feedbacks: List[Dict]
    stats: Dict
    sentiment_analysis: Dict
    key_issues: str
    final_report_md: str
    pdf_path: Optional[str]
    execution_steps: List[Dict]  # 新增：执行步骤记录

# ============================================
# 3. MongoDB 报告存储类
# ============================================

class ReportStorage:
    """报告存储管理类"""
    
    def __init__(self, mongo_uri: str = None, db_name: str = None):
        self.mongo_uri = mongo_uri or MONGO_URI
        self.db_name = db_name or DB_NAME
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.db_name]
        self.reports_collection = self.db[COL_REPORTS]
    
    def create_report(self, start_date: str, end_date: str, report_type: str = "weekly") -> str:
        """创建报告记录"""
        report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        report_doc = {
            "report_id": report_id,
            "start_date": start_date,
            "end_date": end_date,
            "report_type": report_type,
            "status": "pending",  # pending, processing, completed, failed
            "steps": [],
            "stats": {},
            "generated_at": datetime.now(),
            "metadata": {
                "model_used": "deepseek-chat",
                "created_at": datetime.now()
            }
        }
        
        result = self.reports_collection.insert_one(report_doc)
        return str(result.inserted_id)
    
    def update_step(self, mongo_id: str, step_name: str, status: str, details: str = ""):
        """更新步骤状态"""
        step_data = {
            "name": step_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now()
        }
        
        self.reports_collection.update_one(
            {"_id": ObjectId(mongo_id)},
            {
                "$push": {"steps": step_data},
                "$set": {"status": "processing"}
            }
        )
    
    def complete_report(self, mongo_id: str, report_data: Dict[str, Any]):
        """完成报告"""
        update_data = {
            "status": "completed",
            "stats": report_data.get("stats", {}),
            "sentiment_analysis": report_data.get("sentiment_analysis", {}),
            "key_issues": report_data.get("key_issues", ""),
            "markdown_content": report_data.get("final_report_md", ""),
            "pdf_path": report_data.get("pdf_path", ""),
            "pdf_stored": bool(report_data.get("pdf_path")),
            "completed_at": datetime.now(),
            "execution_time": (datetime.now() - report_data.get("start_time", datetime.now())).total_seconds()
        }
        
        self.reports_collection.update_one(
            {"_id": ObjectId(mongo_id)},
            {"$set": update_data}
        )
    
    def fail_report(self, mongo_id: str, error_message: str):
        """标记报告失败"""
        self.reports_collection.update_one(
            {"_id": ObjectId(mongo_id)},
            {
                "$set": {
                    "status": "failed",
                    "error_message": error_message,
                    "failed_at": datetime.now()
                }
            }
        )
    
    def get_report(self, mongo_id: str) -> Dict[str, Any]:
        """获取报告详情"""
        report = self.reports_collection.find_one({"_id": ObjectId(mongo_id)})
        if not report:
            return None
        
        # 转换为可序列化的字典
        result = dict(report)
        result["_id"] = str(result["_id"])
        return result
    
    def get_report_by_report_id(self, report_id: str) -> Dict[str, Any]:
        """根据report_id获取报告"""
        report = self.reports_collection.find_one({"report_id": report_id})
        if not report:
            return None
        
        result = dict(report)
        result["_id"] = str(result["_id"])
        return result
    
    def list_reports(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取报告列表"""
        reports = list(self.reports_collection.find(
            {},
            {"markdown_content": 0, "key_issues": 0}  # 不返回大字段
        ).sort("generated_at", -1).limit(limit))
        
        simplified = []
        for report in reports:
            simplified.append({
                "id": str(report["_id"]),
                "report_id": report.get("report_id"),
                "start_date": report.get("start_date"),
                "end_date": report.get("end_date"),
                "report_type": report.get("report_type"),
                "status": report.get("status"),
                "stats": report.get("stats", {}),
                "generated_at": report.get("generated_at"),
                "has_pdf": report.get("pdf_stored", False),
                "steps": report.get("steps", [])
            })
        
        return simplified

# 全局存储实例
storage = ReportStorage()

# ============================================
# 4. LLM工具
# ============================================
_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatDeepSeek(
            model="deepseek-chat",
            temperature=0.0,
            max_tokens=2048,
            timeout=180,
            base_url=DEEPSEEK_BASE_URL,
            api_key=DEEPSEEK_API_KEY
        )
    return _llm

def call_llm(prompt: str, system_prompt: str = None) -> str:
    """调用DeepSeek模型"""
    if system_prompt is None:
        system_prompt = "你是360安全产品技术分析专家，擅长总结用户反馈与风险分析。"
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]
    
    try:
        _llm = get_llm()
        result = _llm.invoke(messages)
        return result.content
    except Exception as e:
        logger.error(f"LLM调用失败: {str(e)}")
        raise

# ============================================
# 5. 数据库工具
# ============================================

def get_db():
    """获取数据库连接"""
    return MongoClient(MONGO_URI)[DB_NAME]

# ============================================
# 6. LangGraph节点（带步骤追踪）
# ============================================

def load_feedbacks(state: WeekReportState) -> WeekReportState:
    """加载反馈数据"""
    # 记录步骤开始
    if state.get("report_id"):
        storage.update_step(
            state["report_id"], 
            "load_feedbacks", 
            "processing", 
            f"时间范围: {state['start_date'].date()} 到 {state['end_date'].date()}"
        )
    
    logger.info(f"加载反馈数据: {state['start_date']} 到 {state['end_date']}")
    
    db = get_db()
    feedbacks = list(db[COL_FEEDBACKS].find({
        "created_at": {
            "$gte": state["start_date"],
            "$lt": state["end_date"]
        }
    }))
    
    state["feedbacks"] = feedbacks
    logger.info(f"加载完成: {len(feedbacks)} 条反馈")
    
    # 记录步骤完成
    if state.get("report_id"):
        storage.update_step(
            state["report_id"], 
            "load_feedbacks", 
            "completed", 
            f"成功加载 {len(feedbacks)} 条反馈"
        )
    
    return state

def join_ai_analysis(state: WeekReportState) -> WeekReportState:
    """合并AI分析"""
    # 记录步骤开始
    if state.get("report_id"):
        storage.update_step(
            state["report_id"], 
            "join_ai_analysis", 
            "processing"
        )
    
    if not state["feedbacks"]:
        state["merged_feedbacks"] = []
        
        if state.get("report_id"):
            storage.update_step(
                state["report_id"], 
                "join_ai_analysis", 
                "completed", 
                "无反馈数据可处理"
            )
        
        return state
    
    db = get_db()
    feedback_ids = [str(f["_id"]) for f in state["feedbacks"]]
    
    # 查询AI分析
    analysis_map = {}
    for analysis in db[COL_AI_ANALYSIS].find({"feedback_id": {"$in": feedback_ids}}):
        analysis_map[analysis["feedback_id"]] = analysis
    
    # 合并数据
    merged = []
    ai_count = 0
    for feedback in state["feedbacks"]:
        feedback_id = str(feedback["_id"])
        merged_item = dict(feedback)
        
        if feedback_id in analysis_map:
            merged_item["ai_analysis"] = analysis_map[feedback_id].get("ai_result", {})
            ai_count += 1
        else:
            merged_item["ai_analysis"] = None
        
        merged.append(merged_item)
    
    state["merged_feedbacks"] = merged
    
    # 记录步骤完成
    if state.get("report_id"):
        storage.update_step(
            state["report_id"], 
            "join_ai_analysis", 
            "completed", 
            f"合并完成: {len(merged)} 条数据, {ai_count} 条AI分析"
        )
    
    logger.info(f"合并完成: {len(merged)} 条数据")
    return state

def aggregate_stats(state: WeekReportState) -> WeekReportState:
    """聚合统计和情感分析"""
    # 记录步骤开始
    if state.get("report_id"):
        storage.update_step(
            state["report_id"], 
            "aggregate_stats", 
            "processing"
        )
    
    merged = state.get("merged_feedbacks", [])
    
    if not merged:
        state["stats"] = {}
        state["sentiment_analysis"] = {}
        
        if state.get("report_id"):
            storage.update_step(
                state["report_id"], 
                "aggregate_stats", 
                "completed", 
                "无数据可统计"
            )
        
        return state
    
    # 基础统计
    stats = {
        "total": len(merged),
        "by_category": {},
        "by_status": {},
        "risk_level": {"high": 0, "medium": 0, "low": 0, "unknown": 0},
        "need_followup": 0,
        "has_attachment": 0,
        "ai_analyzed": 0
    }
    
    # 情感分析样本
    feedback_contents = []
    
    for feedback in merged:
        # 分类统计
        category = feedback.get("category", "未知")
        stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
        
        # 状态统计
        status = feedback.get("status", "未知")
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        # 附件统计
        if feedback.get("has_attachment"):
            stats["has_attachment"] += 1
        
        # AI分析统计
        ai_analysis = feedback.get("ai_analysis")
        if ai_analysis:
            stats["ai_analyzed"] += 1
            
            # 风险等级
            risk_level = ai_analysis.get("risk_level", "unknown")
            if risk_level in stats["risk_level"]:
                stats["risk_level"][risk_level] += 1
            else:
                stats["risk_level"]["unknown"] += 1
            
            # 跟进需求
            if ai_analysis.get("need_followup"):
                stats["need_followup"] += 1
        
        # 收集情感分析样本
        if content := feedback.get("content"):
            feedback_contents.append(content[:300])
    
    state["stats"] = stats
    
    # 情感分析
    sentiment_analysis = {"sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0}}
    
    if feedback_contents:
        try:
            sentiment_prompt = f"分析用户反馈情感倾向，返回JSON格式: {feedback_contents[:5]}"
            sentiment_result = call_llm(
                sentiment_prompt,
                "你是情感分析专家，请分析以下文本的情感倾向，只返回JSON格式结果"
            )
            
            # 简单解析JSON
            import re
            if json_match := re.search(r'\{.*\}', sentiment_result, re.DOTALL):
                parsed = json.loads(json_match.group())
                sentiment_analysis.update(parsed)
        except Exception as e:
            logger.warning(f"情感分析失败: {str(e)}")
    
    state["sentiment_analysis"] = sentiment_analysis
    
    # 记录步骤完成
    if state.get("report_id"):
        storage.update_step(
            state["report_id"], 
            "aggregate_stats", 
            "completed", 
            f"统计完成: {stats['total']}条数据，{stats['ai_analyzed']}条AI分析"
        )
    
    logger.info(f"统计完成: {stats['total']}条数据，{stats['ai_analyzed']}条AI分析")
    return state

def analyze_key_issues(state: WeekReportState) -> WeekReportState:
    """分析关键问题"""
    # 记录步骤开始
    if state.get("report_id"):
        storage.update_step(
            state["report_id"], 
            "analyze_key_issues", 
            "processing"
        )
    
    samples = []
    for feedback in state.get("merged_feedbacks", [])[:5]:
        sample = {
            "title": feedback.get("title"),
            "category": feedback.get("category"),
            "content": feedback.get("content", "")[:100]
        }
        if ai := feedback.get("ai_analysis"):
            sample.update({
                "risk_level": ai.get("risk_level"),
                "scene": ai.get("scene", "")[:50]
            })
        samples.append(sample)
    
    prompt = f"""
基于以下数据生成关键问题分析：

统计数据:
{json.dumps(state['stats'], ensure_ascii=False, indent=2)}

情感分析:
{json.dumps(state['sentiment_analysis'], ensure_ascii=False, indent=2)}

样本数据:
{json.dumps(samples, ensure_ascii=False, indent=2)}

请从【测试开发】和【安全运营】视角分析：
1. 主要问题类型和风险
2. 需要优先处理的问题
3. 改进建议

用简洁、专业的语言输出。
"""
    
    analysis = call_llm(prompt)
    state["key_issues"] = analysis
    
    # 记录步骤完成
    if state.get("report_id"):
        storage.update_step(
            state["report_id"], 
            "analyze_key_issues", 
            "completed"
        )
    
    logger.info("关键问题分析完成")
    return state

def generate_report(state: WeekReportState) -> WeekReportState:
    """生成最终报告"""
    # 记录步骤开始
    if state.get("report_id"):
        storage.update_step(
            state["report_id"], 
            "generate_report", 
            "processing"
        )
    
    # 准备数据
    start_str = state['start_date'].strftime('%Y-%m-%d')
    end_str = state['end_date'].strftime('%Y-%m-%d')
    
    prompt = f"""
# 安全产品用户反馈周报生成

## 基本信息
- 统计周期: {start_str} 到 {end_str}
- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 核心数据
{json.dumps(state['stats'], ensure_ascii=False, indent=2)}

## 情感分析
{json.dumps(state['sentiment_analysis'], ensure_ascii=False, indent=2)}

## 关键问题分析
{state['key_issues']}

## 要求
请生成一份结构清晰、专业的周报，包含：
1. 执行摘要（核心发现）
2. 详细数据分析
3. 风险等级评估
4. 改进建议
5. 下周重点

使用Markdown格式，语言简洁专业。
"""
    
    report = call_llm(prompt)
    state["final_report_md"] = report
    
    # 记录步骤完成
    if state.get("report_id"):
        storage.update_step(
            state["report_id"], 
            "generate_report", 
            "completed"
        )
    
    logger.info("周报生成完成")
    return state

# ============================================
# 7. PDF生成（修正版）
# ============================================

def save_as_pdf(markdown_content: str, filename: str = None) -> str:
    """保存为PDF文件，返回可访问的相对路径 (/static/xxx.pdf)"""
    try:
        from markdown import markdown
        from weasyprint import HTML
        from pathlib import Path

        # 获取 backend/static 目录（项目根/backend/static）
        BASE_DIR = Path(__file__).resolve().parent.parent  # backend
        static_dir = BASE_DIR / "static"
        os.makedirs(static_dir, exist_ok=True)

        # 默认文件名
        if not filename:
            filename = f"周报_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # 完整文件路径
        filepath = static_dir / filename

        # 转换 Markdown 为 HTML
        html_content = markdown(markdown_content, extensions=['tables', 'fenced_code'])

        # 添加样式
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
                h2 {{ color: #34495e; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; }}
                th {{ background-color: #f2f2f2; }}
                .footer {{ margin-top: 40px; color: #7f8c8d; font-size: 12px; text-align: center; }}
            </style>
        </head>
        <body>
            {html_content}
            <div class="footer">
                生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 机密文件
            </div>
        </body>
        </html>
        """

        # 生成 PDF
        HTML(string=styled_html).write_pdf(str(filepath))  # WeasyPrint 需要 str 类型路径
        logger.info(f"PDF保存成功: {filepath}")

        # 返回前端访问路径（相对 /static/）
        return f"/static/{filename}"

    except Exception as e:
        logger.error(f"PDF生成失败: {str(e)}")
        raise

def generate_and_save_pdf(state: WeekReportState) -> WeekReportState:
    """生成PDF文件"""
    # 记录步骤开始
    if state.get("report_id"):
        storage.update_step(
            state["report_id"], 
            "save_pdf", 
            "processing"
        )
    
    pdf_path = save_as_pdf(state["final_report_md"])
    state["pdf_path"] = pdf_path
    
    # 记录步骤完成
    if state.get("report_id"):
        storage.update_step(
            state["report_id"], 
            "save_pdf", 
            "completed", 
            f"PDF保存到: {pdf_path}" if pdf_path else "PDF生成跳过"
        )
    
    return state

# ============================================
# 8. 构建工作流（添加PDF生成节点）
# ============================================

def build_workflow():
    """构建LangGraph工作流"""
    workflow = StateGraph(WeekReportState)
    
    # 添加节点
    workflow.add_node("load_feedbacks", load_feedbacks)
    workflow.add_node("join_ai_analysis", join_ai_analysis)
    workflow.add_node("aggregate_stats", aggregate_stats)
    workflow.add_node("analyze_key_issues", analyze_key_issues)
    workflow.add_node("generate_report", generate_report)
    workflow.add_node("generate_pdf", generate_and_save_pdf)
    
    # 设置流程
    workflow.set_entry_point("load_feedbacks")
    workflow.add_edge("load_feedbacks", "join_ai_analysis")
    workflow.add_edge("join_ai_analysis", "aggregate_stats")
    workflow.add_edge("aggregate_stats", "analyze_key_issues")
    workflow.add_edge("analyze_key_issues", "generate_report")
    workflow.add_edge("generate_report", "generate_pdf")
    workflow.add_edge("generate_pdf", END)
    
    return workflow.compile()

# ============================================
# 9. 主函数（带持久化）
# ============================================

def generate_week_report_with_storage(
    start_date=None, 
    end_date=None, 
    days=7, 
    report_type="weekly",
    save_pdf=True,
    mongo_id: str = None  # MongoDB中的报告ID
):
    """
    生成周报主函数（带持久化）
    
    Args:
        start_date: 开始日期 (datetime或YYYY-MM-DD字符串)
        end_date: 结束日期 (datetime或YYYY-MM-DD字符串)
        days: 如果不指定日期，统计最近几天
        report_type: 报告类型 (weekly, monthly, custom)
        save_pdf: 是否保存PDF
        mongo_id: MongoDB报告ID，用于更新状态
    """
    start_time = datetime.now()
    print("🚀 开始生成周报")
    print("-" * 50)
    
    # 解析日期参数
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 设置默认日期
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=days)
    
    # 确保时间顺序
    if start_date >= end_date:
        error_msg = "开始日期必须早于结束日期"
        print(f"❌ 错误: {error_msg}")
        
        if mongo_id:
            storage.fail_report(mongo_id, error_msg)
        
        return None
    
    # 显示时间范围
    print(f"📅 统计范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    print(f"📊 报告类型: {report_type}")
    print(f"📊 生成PDF: {'是' if save_pdf else '否'}")
    print()
    
    try:
        # 初始化状态
        initial_state = WeekReportState(
            start_date=start_date,
            end_date=end_date,
            report_type=report_type,
            report_id=mongo_id,  # 传入MongoDB ID用于步骤追踪
            feedbacks=[],
            merged_feedbacks=[],
            stats={},
            sentiment_analysis={},
            key_issues="",
            final_report_md="",
            pdf_path=None,
            execution_steps=[]
        )
        
        # 构建并执行工作流
        app = build_workflow()
        result = app.invoke(initial_state)
        
        # 如果不生成PDF，跳过PDF步骤
        if not save_pdf:
            result["pdf_path"] = None
        
        # 显示结果
        print("\n" + "="*60)
        print("📄 周报内容:")
        print("="*60)
        print(result["final_report_md"][:500] + "...")  # 只显示前500字符
        print("="*60)
        
        # 保存PDF
        # if save_pdf and result["final_report_md"]:
        #     print("\n💾 正在保存PDF...")
        #     pdf_path = save_as_pdf(result["final_report_md"])
        #     if pdf_path:
        #         result["pdf_path"] = pdf_path
        #         print(f"✅ PDF已保存: {pdf_path}")
        
        # 添加执行时间
        result["start_time"] = start_time
        
        # 持久化完成状态
        if mongo_id:
            storage.complete_report(mongo_id, result)
        
        # 显示统计摘要
        print("\n📊 数据摘要:")
        print(f"   总反馈数: {result['stats'].get('total', 0)}")
        print(f"   高风险问题: {result['stats'].get('risk_level', {}).get('high', 0)}")
        print(f"   需要跟进: {result['stats'].get('need_followup', 0)}")
        print(f"   生成耗时: {(datetime.now() - start_time).total_seconds():.1f}秒")
        
        print("\n🎉 周报生成完成!")
        
        return result
        
    except Exception as e:
        error_msg = f"生成失败: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(f"周报生成失败: {str(e)}", exc_info=True)
        
        if mongo_id:
            storage.fail_report(mongo_id, error_msg)
        
        return None

# ============================================
# 10. 命令行接口
# ============================================

if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description='生成安全产品用户反馈周报',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python agent_week_report.py                        # 最近7天周报
  python agent_week_report.py --days 30              # 最近30天报告
  python agent_week_report.py --start 2025-12-01 --end 2025-12-31  # 指定日期范围
  python agent_week_report.py --type monthly         # 生成月报
  python agent_week_report.py --no-pdf               # 不生成PDF
        """
    )
    
    # 日期参数
    parser.add_argument('--start', type=str, help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=7, help='统计天数（默认7天）')
    parser.add_argument('--type', type=str, default='weekly', choices=['weekly', 'monthly', 'custom'], 
                       help='报告类型（默认weekly）')
    
    # 输出参数
    parser.add_argument('--no-pdf', action='store_true', help='不生成PDF文件')
    parser.add_argument('--no-storage', action='store_true', help='不使用持久化存储')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 处理日期逻辑
    start_date = None
    end_date = None
    
    if args.start:
        try:
            start_date = datetime.strptime(args.start, '%Y-%m-%d')
        except ValueError:
            print(f"❌ 错误: 开始日期格式错误 '{args.start}'，应为 YYYY-MM-DD")
            sys.exit(1)
    
    if args.end:
        try:
            end_date = datetime.strptime(args.end, '%Y-%m-%d')
        except ValueError:
            print(f"❌ 错误: 结束日期格式错误 '{args.end}'，应为 YYYY-MM-DD")
            sys.exit(1)
    
    # 创建持久化记录
    mongo_id = None
    if not args.no_storage:
        try:
            # 格式化为字符串用于存储
            start_str = start_date.strftime('%Y-%m-%d') if start_date else None
            end_str = end_date.strftime('%Y-%m-%d') if end_date else None
            
            if not start_str or not end_str:
                # 计算默认日期
                if not end_date:
                    end_date = datetime.utcnow()
                if not start_date:
                    start_date = end_date - timedelta(days=args.days)
                start_str = start_date.strftime('%Y-%m-%d')
                end_str = end_date.strftime('%Y-%m-%d')
            
            mongo_id = storage.create_report(start_str, end_str, args.type)
            print(f"📝 创建报告记录: {mongo_id}")
        except Exception as e:
            print(f"⚠️  持久化记录创建失败，继续生成报告: {str(e)}")
    
    # 生成周报
    result = generate_week_report_with_storage(
        start_date=start_date,
        end_date=end_date,
        days=args.days,
        report_type=args.type,
        save_pdf=not args.no_pdf,
        mongo_id=mongo_id
    )
    
    # 根据结果设置退出码
    sys.exit(0 if result else 1)