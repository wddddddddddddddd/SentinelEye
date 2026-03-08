import requests
import json
from dotenv import load_dotenv
import os
# ========================
# 配置区（请填写真实信息）
# ========================
load_dotenv(override=True)
WEBHOOK_BASE = "https://alarm.im.qihoo.net/message/custom/send"
APPID = os.getenv("TUITUI_APPID", "")
SECRET = os.getenv("TUITUI_SECRET", "")
GROUP_ID = "7653013246190247"   # 推推群组 ID
ROBOT_NAME = "用户反馈监控助手"
print(APPID)
# ========================
# 风险级别配置
# ========================
RISK_CONFIG = {
    "HIGH": {
        "emoji": "🚨",
        "color": "#d9534f",
        "bg_color": "#fef2f2",
        "border_color": "#fee2e2",
        "title_prefix": "【高危预警】",
        "summary_prefix": "⚠️ 高危",
        "badge_style": "background: #d9534f; color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold;"
    },
    "MEDIUM": {
        "emoji": "⚠️",
        "color": "#f0ad4e",
        "bg_color": "#fff3e0",
        "border_color": "#ffe0b2",
        "title_prefix": "【中危提醒】",
        "summary_prefix": "🔎 中危",
        "badge_style": "background: #f0ad4e; color: white; padding: 4px 12px; border-radius: 20px; font-weight: bold;"
    }
}

# ========================
# 构建推推 page.content HTML（优化版）
# ========================
def build_page_content(post, ai_result, risk_level, robot_name="{{tuitui_robot_name}}"):
    cfg = RISK_CONFIG[risk_level]
    
    # 构建带样式的列表项
    def build_styled_list(items, icon="•"):
        return ''.join(f'<li style="margin-bottom: 8px; line-height: 1.6;"><span style="color: {cfg["color"]}; font-weight: bold; margin-right: 8px;">{icon}</span>{x}</li>' for x in items)

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        .container {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            background: #f8fafc;
            padding: 20px;
            border-radius: 16px;
        }}
        .card {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border: 1px solid #eef2f6;
        }}
        .risk-badge {{
            {cfg['badge_style']}
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #eef2f6;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            background: #f8fafc;
            padding: 16px;
            border-radius: 12px;
            margin: 16px 0;
        }}
        .info-item {{
            display: flex;
            flex-direction: column;
        }}
        .info-label {{
            font-size: 13px;
            color: #64748b;
            margin-bottom: 4px;
        }}
        .info-value {{
            font-size: 15px;
            font-weight: 500;
            color: #1e293b;
        }}
        .content-box {{
            background: #f8fafc;
            border-radius: 12px;
            padding: 16px;
            margin: 16px 0;
            border-left: 4px solid {cfg['color']};
            font-size: 15px;
            line-height: 1.8;
            color: #334155;
        }}
        .evidence-box {{
            background: {cfg['bg_color']};
            border: 1px solid {cfg['border_color']};
            border-radius: 12px;
            padding: 16px;
            margin: 16px 0;
        }}
        .suggestion-item {{
            background: #f0f9ff;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
            border-left: 3px solid #0284c7;
        }}
        .url-link {{
            display: inline-block;
            background: #eef2f6;
            color: #2563eb;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 500;
            margin-top: 8px;
            transition: background 0.2s;
        }}
        .url-link:hover {{
            background: #e2e8f0;
        }}
        .footer {{
            text-align: center;
            font-size: 12px;
            color: #94a3b8;
            padding: 20px 0 10px 0;
            border-top: 1px dashed #e2e8f0;
            margin-top: 20px;
        }}
        .stats {{
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            margin-top: 8px;
        }}
        .stat-item {{
            background: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 13px;
            border: 1px solid #e2e8f0;
        }}
        .quote-mark {{
            font-size: 24px;
            color: {cfg['color']}40;
            margin-right: 8px;
            vertical-align: middle;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 风险标识卡 -->
        <div class="card" style="border-top: 4px solid {cfg['color']};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <div>
                    <span class="risk-badge">{cfg['emoji']} {risk_level} RISK</span>
                </div>
                <div style="color: #64748b; font-size: 14px;">
                    #{post.get('id', 'N/A')}
                </div>
            </div>
            
            <h1 style="font-size: 24px; margin: 0 0 16px 0; color: #1e293b; line-height: 1.4;">
                {cfg['title_prefix']} {post['title']}
            </h1>
            
            <!-- 用户信息网格 -->
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">👤 用户</span>
                    <span class="info-value">{post['username']}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">📌 版块</span>
                    <span class="info-value">{post['category']}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">📊 状态</span>
                    <span class="info-value" style="color: #10b981;">{post['status']}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">⏰ 发布时间</span>
                    <span class="info-value">{post['created_at']}</span>
                </div>
            </div>
            
            <!-- 阅读统计 -->
            <div class="stats">
                <span class="stat-item">👁️ 浏览 {post['view_count']}</span>
                <span class="stat-item">💬 回复 {post['reply_count']}</span>
            </div>
        </div>
        
        <!-- 原帖内容卡片 -->
        <div class="card">
            <div class="section-title">
                <span style="font-size: 24px;">📄</span> 用户原始反馈
            </div>
            
            <div class="content-box">
                <span class="quote-mark">"</span>
                {post['content'].replace(chr(10), '<br/>')}
            </div>
            
            <a href="{post['url']}" class="url-link" target="_blank">
                🔗 查看原帖详情 →
            </a>
        </div>
        
        <!-- 触发原因卡片 -->
        <div class="card" style="background: {cfg['bg_color']}; border: 1px solid {cfg['border_color']};">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 32px;">⚡</span>
                <div>
                    <div style="font-size: 14px; color: #64748b; margin-bottom: 4px;">触发原因</div>
                    <div style="font-size: 18px; font-weight: 600; color: {cfg['color']};">{ai_result['trigger']}</div>
                </div>
            </div>
        </div>
        
        <!-- AI 评估卡片 -->
        <div class="card">
            <div class="section-title">
                <span style="font-size: 24px;">🤖</span> AI 风险评估
            </div>
            
            <!-- 综合判断 -->
            <div style="margin-bottom: 24px;">
                <h3 style="font-size: 16px; color: #334155; margin: 0 0 12px 0; display: flex; align-items: center;">
                    <span style="background: #eef2f6; padding: 4px 8px; border-radius: 6px; font-size: 14px; margin-right: 8px;">📊</span>
                    综合判断
                </h3>
                <ul style="list-style: none; padding: 0; margin: 0;">
                    {build_styled_list(ai_result['analysis'], "•")}
                </ul>
            </div>
            
            <!-- 关键证据 -->
            <div class="evidence-box">
                <h3 style="font-size: 16px; color: #334155; margin: 0 0 12px 0; display: flex; align-items: center;">
                    <span style="background: {cfg['color']}20; color: {cfg['color']}; padding: 4px 8px; border-radius: 6px; font-size: 14px; margin-right: 8px;">🔍</span>
                    关键证据
                </h3>
                <ul style="list-style: none; padding: 0; margin: 0;">
                    {build_styled_list(ai_result['evidence'], "✓")}
                </ul>
            </div>
            
            <!-- 处理建议 -->
            <div style="margin-top: 24px;">
                <h3 style="font-size: 16px; color: #334155; margin: 0 0 12px 0; display: flex; align-items: center;">
                    <span style="background: #0284c7; color: white; padding: 4px 8px; border-radius: 6px; font-size: 14px; margin-right: 8px;">💡</span>
                    处理建议
                </h3>
                <div>
                    {''.join(f'<div class="suggestion-item">✨ {x}</div>' for x in ai_result['suggestions'])}
                </div>
            </div>
        </div>
        
        <!-- 页脚 -->
        <div class="footer">
            <span style="background: #eef2f6; padding: 4px 12px; border-radius: 20px;">🤖 {robot_name}</span>
            <div style="margin-top: 12px;">
                本条内容由 AI 自动生成，仅用于内部风险预警与技术辅助分析，不作为定责依据
            </div>
        </div>
    </div>
</body>
</html>
"""
    return html.strip()

# ========================
# 发送 Page 消息
# ========================
def send_page_message(page_data, risk_level="HIGH"):
    url = f"{WEBHOOK_BASE}?appid={APPID}&secret={SECRET}"
    payload = {
        "togroups": [GROUP_ID],
        "msgtype": "page",
        "page": page_data
    }

    resp = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload, ensure_ascii=False)
    )
    return resp.status_code, resp.text

# ========================
# 示例数据（你做自动化时从 DB 填）
# ========================
post_example = {
    "title": "设置完好，蓝屏无日志，蓝屏视频发给360-leo产品答疑了",
    "username": "奥特曼是敌人",
    "category": "问题反馈",
    "status": "已答复",
    "created_at": "2025-12-20 00:49",
    "view_count": 882,
    "reply_count": 2,
    "content": "设置完好，蓝屏无日志，\n蓝屏视频发给360-leo产品答疑了（2298129324）",
    "url": "https://bbs.360.cn/thread-16175330-1-1.html",
    "id": "16175330"  # 添加ID用于显示
}

ai_result_example = {
    "trigger": "无蓝屏日志 + 蓝屏视频佐证 + 涉及底层异常",
    "analysis": [
        "系统发生蓝屏但未生成 Minidump，可能涉及内核态或驱动加载早期阶段",
        "问题定位和复现成本较高，需要深入分析系统底层状态",
        "用户已提供视频证据，排除误报可能"
    ],
    "evidence": [
        "用户明确反馈“蓝屏无日志”，系统未记录崩溃转储文件",
        "蓝屏过程以视频形式完整呈现，非截图误判",
        "问题已升级至产品技术答疑处理（2298129324）",
        "涉及底层异常，可能与驱动或系统服务相关"
    ],
    "suggestions": [
        "确认系统分页文件和转储配置是否正确设置",
        "关注近期内核级驱动变更或系统更新",
        "联系用户获取系统配置和近期操作记录",
        "必要时跟进用户系统环境，远程协助分析"
    ]
}

# ========================
# 组织 page 数据
# ========================
risk_level = "HIGH"  # HIGH / MEDIUM
html_content = build_page_content(post_example, ai_result_example, risk_level)

# 优化标题和摘要
title_suffix = "蓝屏无日志｜疑似内核级异常"
if risk_level == "HIGH":
    title_suffix = "🚨 高危｜" + title_suffix
else:
    title_suffix = "⚠️ 中危｜" + title_suffix

page_data = {
    "title": title_suffix,
    "summary": f"{RISK_CONFIG[risk_level]['summary_prefix']} 用户反馈蓝屏但系统未生成崩溃日志，{ai_result_example['trigger']}",
    "image": "https://p0.ssl.qhmsg.com/t11e3f4274fb5ed658e3fc6c88b.png",
    "content": html_content
}

# ========================
# 发送并打印
# ========================
code, res = send_page_message(page_data, risk_level)
print("HTTP 状态码:", code)
print("返回内容:", res)