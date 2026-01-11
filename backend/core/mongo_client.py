# core/mongo_client.py
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# 从环境变量读取（有默认值，方便本地开发）
MONGO_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://localhost:27017/SentinelEye"
)
DB_NAME = os.getenv("DB_NAME", "SentinelEye")

# 初始化客户端
client = MongoClient(MONGO_URI)

# 获取数据库实例
db = client[DB_NAME]

# 集合
feedbacks_collection = db.feedbacks
keywords_collection = db.keywords
ai_analysis_collection = db.ai_analysis

# 测试连接（启动时验证）
try:
    client.admin.command("ping")
    print("✅ MongoDB 连接成功")
except ConnectionFailure as e:
    print(f"❌ MongoDB 连接失败: {e}")
