# agent_week_report.py
# ============================================
# 优化版：用户反馈周报生成（LangGraph + DeepSeek）
# 修复了 PDF 中文乱码问题，增加错误处理和配置项
# ============================================

import os
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pymongo import MongoClient
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, SystemMessage

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from reportlab.lib import colors


# ============================================
# 1. 基础配置 & 日志
# ============================================

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("weekly_report.log", encoding="utf-8")
    ]
)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "SentinelEye")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")

OUTPUT_DIR = "./weekly_reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)

COL_FEEDBACKS = "feedbacks"
COL_AI_ANALYSIS = "ai_analysis"

# 字体配置
FONT_CONFIGS = {
    "windows": {
        "simsun": "C:/Windows/Fonts/simsun.ttc",
        "simhei": "C:/Windows/Fonts/simhei.ttf",
        "simkai": "C:/Windows/Fonts/simkai.ttf",
        "microsoft_yahei": "C:/Windows/Fonts/msyh.ttc"
    },
    "linux": {
        "simsun": "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "noto_sans_cjk": "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"
    },
    "mac": {
        "pingfang": "/System/Library/Fonts/PingFang.ttc",
        "stheitisc": "/System/Library/Fonts/STHeiti Medium.ttc"
    }
}


# ============================================
# 2. 字体管理
# ============================================

class FontManager:
    """字体管理器，解决中文显示问题"""
    
    @staticmethod
    def detect_platform():
        """检测操作系统平台"""
        if sys.platform.startswith('win'):
            return "windows"
        elif sys.platform.startswith('linux'):
            return "linux"
        elif sys.platform.startswith('darwin'):
            return "mac"
        else:
            return "unknown"
    
    @staticmethod
    def register_chinese_fonts():
        """注册中文字体"""
        platform = FontManager.detect_platform()
        registered_fonts = []
        
        # 尝试多种字体路径
        font_paths = []
        
        # 1. 检查配置中的字体路径
        if platform in FONT_CONFIGS:
            for font_name, font_path in FONT_CONFIGS[platform].items():
                if os.path.exists(font_path):
                    font_paths.append((font_name, font_path))
        
        # 2. 检查当前目录下的字体文件
        local_fonts = ["SimSun.ttf", "simsun.ttc", "msyh.ttf", "msyh.ttc"]
        for font_file in local_fonts:
            if os.path.exists(font_file):
                font_paths.append(("local_" + os.path.splitext(font_file)[0], font_file))
        
        # 3. 尝试注册找到的字体
        for font_name, font_path in font_paths:
            try:
                if font_path.endswith('.ttc'):
                    # TTC 文件需要指定字体索引
                    pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=0))
                else:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                registered_fonts.append(font_name)
                logging.info(f"成功注册字体: {font_name} ({font_path})")
                
                # 设置默认中文字体
                pdfmetrics.registerFontFamily(
                    font_name,
                    normal=font_name,
                    bold=font_name,
                    italic=font_name,
                    boldItalic=font_name
                )
                
            except Exception as e:
                logging.warning(f"注册字体 {font_path} 失败: {e}")
        
        if not registered_fonts:
            # 如果没找到任何中文字体，尝试使用内置的东亚字体
            try:
                pdfmetrics.registerFont(TTFont("ChineseFont", "Helvetica"))
                logging.warning("使用默认字体，中文可能显示为方块")
                return "ChineseFont"
            except:
                logging.error("无法注册任何字体")
                return "Helvetica"
        
        return registered_fonts[0]


# ============================================
# 3. LLM 初始化
# ============================================

llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0.0,
    max_tokens=2048,
    timeout=120,
    base_url=DEEPSEEK_BASE_URL,
    api_key=DEEPSEEK_API_KEY
)


def call_llm(prompt: str) -> str:
    """调用 LLM 生成内容"""
    try:
        logging.info("调用 LLM 生成内容...")
        messages = [
            SystemMessage(content="你是资深安全产品测试工程师，为测开和安全运营团队生成内部技术周报。语言严谨、技术化。"),
            HumanMessage(content=prompt)
        ]
        result = llm.invoke(messages).content
        logging.info("LLM 调用完成")
        return result
    except Exception as e:
        logging.error(f"LLM 调用失败: {e}")
        return f"LLM 调用失败: {str(e)}"


# ============================================
# 4. Graph State
# ============================================

class WeekReportState(Dict):
    start_date: datetime
    end_date: datetime
    feedbacks: List[Dict]
    merged_feedbacks: List[Dict]
    stats: Dict
    analysis_summary: str
    report_text: str
    pdf_path: str


# ============================================
# 5. Agent 定义
# ============================================

class DataAgent:
    def __init__(self):
        try:
            self.db = MongoClient(MONGO_URI)[DB_NAME]
            logging.info(f"成功连接 MongoDB: {DB_NAME}")
        except Exception as e:
            logging.error(f"连接 MongoDB 失败: {e}")
            raise

    def load_feedbacks(self, state: WeekReportState) -> WeekReportState:
        logging.info("【1】加载反馈数据...")
        try:
            state["feedbacks"] = list(self.db[COL_FEEDBACKS].find({
                "created_at": {
                    "$gte": state["start_date"],
                    "$lt": state["end_date"]
                }
            }))
            logging.info(f"加载完成，共 {len(state['feedbacks'])} 条")
            return state
        except Exception as e:
            logging.error(f"加载反馈数据失败: {e}")
            state["feedbacks"] = []
            return state

    def join_ai_analysis(self, state: WeekReportState) -> WeekReportState:
        logging.info("【2】合并 AI 分析结果...")
        if not state["feedbacks"]:
            state["merged_feedbacks"] = []
            return state

        try:
            ids = [f["_id"] for f in state["feedbacks"]]
            analysis_map = {
                a["feedback_id"]: a["ai_result"]
                for a in self.db[COL_AI_ANALYSIS].find({"feedback_id": {"$in": ids}})
            }

            merged = []
            for f in state["feedbacks"]:
                item = dict(f)
                if f["_id"] in analysis_map:
                    item["ai_analysis"] = analysis_map[f["_id"]]
                merged.append(item)

            state["merged_feedbacks"] = merged
            logging.info(f"合并完成，有分析 {len([i for i in merged if i.get('ai_analysis')])} 条")
            return state
        except Exception as e:
            logging.error(f"合并 AI 分析失败: {e}")
            state["merged_feedbacks"] = state["feedbacks"]
            return state


class AnalysisAgent:
    def aggregate_stats(self, state: WeekReportState) -> WeekReportState:
        logging.info("【3】聚合统计...")
        try:
            stats = {
                "total": len(state["merged_feedbacks"]),
                "by_category": {},
                "risk_level": {"high": 0, "medium": 0, "low": 0, "unknown": 0},
                "need_followup": 0
            }

            for f in state["merged_feedbacks"]:
                cat = f.get("category", "未知")
                stats["by_category"].setdefault(cat, 0)
                stats["by_category"][cat] += 1

                ai = f.get("ai_analysis")
                if ai:
                    lvl = ai.get("risk_level", "unknown").lower()
                    if lvl in stats["risk_level"]:
                        stats["risk_level"][lvl] += 1
                    if ai.get("need_followup"):
                        stats["need_followup"] += 1
                else:
                    stats["risk_level"]["unknown"] += 1

            state["stats"] = stats
            logging.info(f"统计完成：总数 {stats['total']}，高风险 {stats['risk_level']['high']}")
            return state
        except Exception as e:
            logging.error(f"聚合统计失败: {e}")
            state["stats"] = {}
            return state

    def summarize(self, state: WeekReportState) -> WeekReportState:
        logging.info("【4】生成关键问题分析...")
        
        if not state.get("stats") or state["stats"].get("total", 0) == 0:
            state["analysis_summary"] = "本周无用户反馈。产品运行稳定，建议加强主动监控（如日志审计、样本库更新）。"
            return state

        try:
            # 提取样例数据
            samples = []
            for f in state["merged_feedbacks"]:
                if f.get("ai_analysis"):
                    ai_data = f.get("ai_analysis", {})
                    samples.append({
                        "post_id": f.get("post_id", "未知"),
                        "title": f.get("title", "无标题")[:50],
                        "scene": ai_data.get("scene", "未分类"),
                        "risk_level": ai_data.get("risk_level", "unknown"),
                        "key_evidence": ai_data.get("key_evidence", [])[:3]
                    })
                    if len(samples) >= 8:
                        break

            period_start = state['start_date'].strftime('%Y年%m月%d日')
            period_end = (state['end_date'] - timedelta(days=1)).strftime('%Y年%m月%d日')

            prompt = f"""
报告周期：{period_start} - {period_end}
生成日期：{datetime.now().strftime('%Y年%m月%d日')}

统计数据：
{state["stats"]}

典型反馈样例（最多8条）：
{samples}

请用严谨技术语言总结（必须基于提供数据，不允许虚构）：
1. 本周高频问题类型（标注high/medium风险）
2. 高风险问题详情（列出post_id、核心证据、潜在影响、可复现性）
3. 下周优先行动项（标注测开验证 / 安全运营分析）

若无high风险，明确写"本周无high风险反馈"。
格式要求：使用清晰的段落和项目符号。
"""

            state["analysis_summary"] = call_llm(prompt)
            return state
        except Exception as e:
            logging.error(f"生成分析摘要失败: {e}")
            state["analysis_summary"] = "分析生成失败，请查看日志"
            return state


class ReportWriterAgent:
    def __init__(self):
        self.chinese_font = FontManager.register_chinese_fonts()

    def write(self, state: WeekReportState) -> WeekReportState:
        logging.info("【5】生成最终周报文本...")
        
        try:
            period_start = state["start_date"].strftime('%Y年%m月%d日')
            period_end = (state["end_date"] - timedelta(days=1)).strftime('%Y年%m月%d日')
            generate_date = datetime.now().strftime('%Y年%m月%d日')

            # 构建格式化统计数据
            category_text = "\n".join([f"  - {k}: {v}" for k, v in state["stats"].get("by_category", {}).items()])
            risk_text = "\n".join([f"  - {k}: {v}" for k, v in state["stats"].get("risk_level", {}).items()])

            prompt = f"""
你为测开和安全运营团队生成内部技术周报。

报告周期：{period_start} - {period_end}
生成日期：{generate_date}

严格按以下结构输出Markdown，不允许添加未提供数据（如环比、CSAT）：

# 安全产品用户反馈技术周报（内部）

## 一、反馈概览
反馈总数：{state["stats"].get("total", 0)}

## 二、分类与风险统计
### 分类分布：
{category_text}

### 风险分布：
{risk_text}

### 需重点跟进：
{state["stats"].get("need_followup", 0)}

## 三、关键问题技术分析
{state["analysis_summary"]}

## 四、技术总结与行动计划
- 核心风险总结（重点说明high风险影响）
- 下周行动项（每项标注优先级和负责人方向：测开验证 / 安全运营分析）
- 若无反馈，说明产品稳定性良好并建议主动监控

输出要求：
1. 使用规范的Markdown格式
2. 语言技术化、简洁明了
3. 只输出周报正文
"""

            state["report_text"] = call_llm(prompt)
            
            # 如果 LLM 调用失败，生成基本报告
            if "失败" in state["report_text"]:
                state["report_text"] = self._generate_basic_report(state)
            
            logging.info("周报文本生成完成")
            return state
        except Exception as e:
            logging.error(f"生成周报文本失败: {e}")
            state["report_text"] = self._generate_basic_report(state)
            return state
    
    def _generate_basic_report(self, state: WeekReportState) -> str:
        """生成基本报告作为后备"""
        period_start = state["start_date"].strftime('%Y年%m月%d日')
        period_end = (state["end_date"] - timedelta(days=1)).strftime('%Y年%m月%d日')
        
        return f"""# 安全产品用户反馈技术周报（内部）

## 报告周期
{period_start} - {period_end}

## 反馈概览
反馈总数：{state["stats"].get("total", 0)}

## 分类与风险统计
分类分布：{state["stats"].get("by_category", {})}
风险分布：{state["stats"].get("risk_level", {})}
需重点跟进：{state["stats"].get("need_followup", 0)}

## 关键问题技术分析
{state.get("analysis_summary", "数据分析未完成")}

## 技术总结
根据本周数据分析，制定相应行动计划。
"""


class PdfExportAgent:
    def __init__(self):
        self.chinese_font = FontManager.register_chinese_fonts()
    
    def export(self, state: WeekReportState) -> WeekReportState:
        logging.info("【6】生成 PDF...")
        
        try:
            period_start = state["start_date"].strftime('%Y年%m月%d日')
            period_end = (state["end_date"] - timedelta(days=1)).strftime('%Y年%m月%d日')
            generate_date = datetime.now().strftime('%Y年%m月%d日')
            
            period_file = f"{state['start_date'].strftime('%Y%m%d')}_{(state['end_date'] - timedelta(days=1)).strftime('%Y%m%d')}"
            filename = f"weekly_report_{period_file}.pdf"
            path = os.path.join(OUTPUT_DIR, filename)

            # 创建 PDF 文档
            doc = SimpleDocTemplate(
                path, 
                pagesize=A4, 
                leftMargin=2*cm, 
                rightMargin=2*cm, 
                topMargin=2*cm, 
                bottomMargin=2*cm,
                title=f"安全产品周报 {period_file}"
            )
            
            # 定义样式
            styles = self._create_styles()
            story = self._build_story(state, styles, period_start, period_end, generate_date)
            
            # 构建文档
            doc.build(story)
            
            state["pdf_path"] = os.path.abspath(path)
            logging.info(f"PDF 生成完成：{state['pdf_path']}")
            
            return state
        except Exception as e:
            logging.error(f"PDF 生成失败: {e}")
            state["pdf_path"] = ""
            return state
    
    def _create_styles(self):
        """创建 PDF 样式"""
        styles = getSampleStyleSheet()
        
        # 主标题样式
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=self.chinese_font,
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=24,
            textColor=colors.HexColor('#1a365d')
        )
        
        # 副标题样式
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontName=self.chinese_font,
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=18,
            textColor=colors.HexColor('#4a5568')
        )
        
        # 章节标题样式
        heading1_style = ParagraphStyle(
            'CustomHeading1',
            parent=styles['Heading2'],
            fontName=self.chinese_font,
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#2d3748')
        )
        
        heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading3'],
            fontName=self.chinese_font,
            fontSize=14,
            spaceBefore=16,
            spaceAfter=10,
            textColor=colors.HexColor('#4a5568')
        )
        
        # 正文样式
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=self.chinese_font,
            fontSize=11,
            leading=16,
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        # 列表项样式
        bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=styles['Normal'],
            fontName=self.chinese_font,
            fontSize=11,
            leading=16,
            leftIndent=20,
            spaceAfter=4,
            bulletIndent=10
        )
        
        return {
            'title': title_style,
            'subtitle': subtitle_style,
            'heading1': heading1_style,
            'heading2': heading2_style,
            'normal': normal_style,
            'bullet': bullet_style
        }
    
    def _build_story(self, state, styles, period_start, period_end, generate_date):
        """构建 PDF 内容"""
        story = []
        
        # 标题
        story.append(Paragraph("安全产品用户反馈技术周报（内部）", styles['title']))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f"报告周期：{period_start} - {period_end}", styles['subtitle']))
        story.append(Paragraph(f"生成日期：{generate_date}", styles['subtitle']))
        story.append(Spacer(1, 1*cm))
        
        # 添加分隔线
        story.append(self._create_horizontal_rule())
        story.append(Spacer(1, 0.5*cm))
        
        # 解析 Markdown 内容
        if state["report_text"]:
            self._parse_markdown_to_pdf(state["report_text"], story, styles)
        else:
            story.append(Paragraph("无报告内容", styles['normal']))
        
        return story
    
    def _create_horizontal_rule(self):
        """创建水平分隔线"""
        from reportlab.platypus import HRFlowable
        return HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#e2e8f0'),
            spaceBefore=6,
            spaceAfter=6
        )
    
    def _parse_markdown_to_pdf(self, markdown_text: str, story: List, styles: Dict):
        """将 Markdown 转换为 PDF 元素"""
        lines = markdown_text.strip().split('\n')
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                story.append(Spacer(1, 0.3*cm))
                continue
            
            # 处理标题
            if stripped.startswith('# '):
                story.append(Paragraph(stripped[2:], styles['heading1']))
            elif stripped.startswith('## '):
                story.append(Paragraph(stripped[3:], styles['heading2']))
            elif stripped.startswith('### '):
                story.append(Paragraph(stripped[4:], styles['heading2']))
            # 处理列表项
            elif stripped.startswith('- ') or stripped.startswith('* ') or stripped.startswith('+ '):
                # 移除列表标记，保留内容
                content = stripped[2:].strip()
                story.append(Paragraph(f"• {content}", styles['bullet']))
            elif stripped.startswith('1. ') or stripped.strip()[0].isdigit():
                # 处理有序列表
                content = stripped[stripped.find('.')+1:].strip()
                story.append(Paragraph(f"• {content}", styles['bullet']))
            # 处理普通段落
            else:
                story.append(Paragraph(stripped, styles['normal']))
    
    def _create_table(self, data, col_widths=None):
        """创建表格（备用）"""
        from reportlab.platypus import Table, TableStyle
        
        table_data = []
        for row in data:
            table_row = []
            for cell in row:
                table_row.append(Paragraph(cell, ParagraphStyle(
                    'TableText',
                    fontName=self.chinese_font,
                    fontSize=10,
                    leading=12
                )))
            table_data.append(table_row)
        
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('FONTNAME', (0,0), (-1,-1), self.chinese_font),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        
        return table


# ============================================
# 6. 构建 LangGraph
# ============================================

def build_graph():
    data_agent = DataAgent()
    analysis_agent = AnalysisAgent()
    writer_agent = ReportWriterAgent()
    pdf_agent = PdfExportAgent()

    graph = StateGraph(WeekReportState)

    graph.add_node("load_data", data_agent.load_feedbacks)
    graph.add_node("join_ai", data_agent.join_ai_analysis)
    graph.add_node("stats", analysis_agent.aggregate_stats)
    graph.add_node("analysis", analysis_agent.summarize)
    graph.add_node("write", writer_agent.write)
    graph.add_node("pdf", pdf_agent.export)

    graph.set_entry_point("load_data")

    graph.add_edge("load_data", "join_ai")
    graph.add_edge("join_ai", "stats")
    graph.add_edge("stats", "analysis")
    graph.add_edge("analysis", "write")
    graph.add_edge("write", "pdf")
    graph.add_edge("pdf", END)

    return graph.compile()


# ============================================
# 7. 运行入口
# ============================================

def run_week_report(start: datetime, end: datetime) -> Dict:
    """运行周报生成"""
    try:
        app = build_graph()
        logging.info("=== 开始生成周报 ===")
        logging.info(f"时间范围: {start.strftime('%Y-%m-%d')} 至 {end.strftime('%Y-%m-%d')}")

        final_state = None
        for step in app.stream({"start_date": start, "end_date": end}, stream_mode="updates"):
            for node, update in step.items():
                logging.info(f"✓ 完成节点：{node}")
                if node == "pdf":
                    final_state = update

        if final_state is None:
            logging.error("周报生成失败，未获取到最终状态")
            raise ValueError("生成失败")
        
        return final_state
        
    except Exception as e:
        logging.error(f"周报生成过程异常: {e}")
        raise


def get_date_range(days_back: int = 7) -> tuple:
    """获取日期范围"""
    end = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days_back)
    return start, end


if __name__ == "__main__":
    try:
        # 获取上周数据（可调整天数）
        start, end = get_date_range(7)
        
        print(f"生成周报: {start.strftime('%Y-%m-%d')} 至 {end.strftime('%Y-%m-%d')}")
        print("-" * 50)
        
        result = run_week_report(start, end)
        
        print("\n" + "=" * 50)
        print("周报预览")
        print("=" * 50 + "\n")
        
        # 显示报告前500字符预览
        if result.get("report_text"):
            preview = result["report_text"][:500]
            print(preview)
            if len(result["report_text"]) > 500:
                print("\n... (完整内容详见PDF文件)")
        else:
            print("未生成报告内容")
        
        print("\n" + "=" * 50)
        
        if result.get("pdf_path"):
            print(f"✅ PDF 已生成: {result['pdf_path']}")
            
            # 检查文件大小
            if os.path.exists(result["pdf_path"]):
                size = os.path.getsize(result["pdf_path"]) / 1024
                print(f"📄 文件大小: {size:.1f} KB")
        else:
            print("❌ PDF 生成失败")
            
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        sys.exit(1)