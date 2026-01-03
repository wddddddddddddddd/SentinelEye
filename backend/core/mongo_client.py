# core/mongo_client.py
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# MongoDB 配置
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "SentinelEye"

# 初始化客户端
client = MongoClient(MONGO_URI)

# 获取数据库实例
db = client[DB_NAME]

# 获取反馈集合
feedbacks_collection = db.feedbacks
keywords_collection = db.keywords
ai_analysis_collection = db.ai_analysis

# 测试连接
try:
    client.admin.command('ping')
    print("✅ MongoDB 连接成功")
except ConnectionFailure:
    print("❌ MongoDB 连接失败")