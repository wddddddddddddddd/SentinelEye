# SentinelEye - 智能用户反馈实时监控系统

一个专为你量身打造的 AI 测试助手  
7×24h 盯着公司用户社区，一旦出现「蓝屏」「死机」「游戏崩溃」「启动失败」「嗡嗡响」等你负责的问题，立刻企业微信@你，带原文+截图，让你在问题爆发前就复现它

GitHub: https://github.com/yourname/SentinelEye  
作者：一位再也不想每天手动刷论坛的测试开发

## 项目背景 & 痛点解决

- 每天手动翻几十页论坛找自己模块的问题，太累且容易漏
- 蓝屏、驱动、游戏兼容类问题往往要等用户骂到热榜才发现
- 领导问「这个月蓝屏反馈有多少？」要临时统计半天

SentinelEye 彻底解放你：
- 自动抓取 + 结构化存储所有反馈（含截图）
- 关键词 + 大模型语义理解 + 多模态视觉识别（识别蓝屏代码、错误弹窗）
- 命中即秒推企业微信/飞书/邮件
- 前端大屏 + 周/月 Top 问题 + 一键导出 PDF 周报

## 功能清单

| 功能                         | 状态         | 备注                                      |
|------------------------------|--------------|-------------------------------------------|
| 360社区自动抓取              | Done         | 支持分页、去重、防封                      |
| FastAPI + Swagger 文档       | Done         | http://localhost:8000/docs                |
| 关键词硬匹配告警             | Done         | 蓝屏/死机/游戏/嗡嗡响/启动不了等          |
| 企业微信实时通知（@人+卡片） | Done         | 支持附带原文+截图                         |
| 大模型语义理解               | In Progress  | Qwen-4L / DeepSeek / GPT-4o               |
| 多模态图片识别（蓝屏代码）   | In Progress  | Qwen-VL-Max / GPT-4o                      |
| Vue3 前端仪表盘              | In Progress  | NaiveUI + ECharts                         |
| 周/月问题统计 + PDF 周报     | In Progress  | WeasyPrint 自动生成                       |
| Agent 自动复现（未来）       | Planned      | Playwright 按用户描述操作复现             |


## 系统架构图

![SentinelEye 系统架构图](./docs/architecture.svg)

层级,技术选型,备注
爬虫,requests + lxml → Playwright（备选）
后端,FastAPI + Uvicorn + Pydantic2,自动文档、高性能
数据存储,本地 JSON → MongoDB / PostgreSQL,当前 JSON，随时可换
AI 能力,"Qwen-4L / DeepSeek（文本）
Qwen-VL-Max / GPT-4o（多模态）",免费额度够用，效果炸裂
向量检索,Chroma / Milvus（后续）,语义搜索历史相似问题
通知,企业微信 Webhook / 飞书 / 邮件,支持富文本+图片
前端,Vue3 + TypeScript + Pinia + NaiveUI,现代、漂亮、开箱即用
周报生成,WeasyPrint / Playwright,纯 Python 生成 PDF
定时任务,APScheduler,灵活易用
部署,Docker + Docker Compose,一键部署

## 项目架构图
SentinelEye/
├── backend/
│   ├── main.py                  # FastAPI 入口
│   ├── core/config.py
│   ├── models/feedback.py     # Pydantic 模型
│   ├── services/
│   │   ├── crawler.py           # 爬虫
│   │   ├── storage.py           # 数据读写
│   │   └── notifier.py          # 告警（开发中）
│   ├── api/v1/feedback.py       # 接口
│   └── data/
│       └── feedbacks.json
├── frontend/                    # Vue3 项目
├── .env
├── requirements.txt
└── README.md

# 快速开始
# 克隆项目
git clone https://github.com/yourname/SentinelEye.git
cd SentinelEye

# 安装依赖
pip install -r backend/requirements.txt

# 第一次抓取数据
python backend/services/crawler.py

# 启动服务
uvicorn backend.main:app --reload --port 8000

## 未来愿景（让领导尖叫的功能）

Agent 自动复现：识别到“启动失败”后自动启动虚拟机按用户描述操作复现
问题聚类：用 Embedding 把相似问题聚类，提前发现批量故障
情感分析：识别用户愤怒程度，自动在论坛礼貌回复「已收到，正在处理」
自动回复：机器人去论坛礼貌回复“已收到，正在紧急处理”