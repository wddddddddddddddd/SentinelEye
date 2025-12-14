# core/mongo_client.py
import logging
from typing import Optional, List, Dict, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError, OperationFailure
from config.settings import MONGODB_URI, MONGODB_DB_NAME, MONGODB_FEEDBACKS_COLLECTION

logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB客户端（单例模式）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化连接"""
        try:
            self.client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            # 测试连接
            self.client.admin.command('ping')
            logger.info(f"[MongoDB] 成功连接到 {MONGODB_URI}")

            # 设置数据库
            self.db = self.client[MONGODB_DB_NAME]
            self.feedbacks = self.db[MONGODB_FEEDBACKS_COLLECTION]

            # 确保索引存在
            self._ensure_indexes()

        except ConnectionFailure as e:
            logger.error(f"[MongoDB] 连接失败: {e}")
            raise

    def _ensure_indexes(self):
        """确保必要的索引存在"""
        try:
            # 获取现有索引
            existing_indexes = list(self.feedbacks.list_indexes())
            index_names = [idx["name"] for idx in existing_indexes]

            # 创建post_id唯一索引
            if "post_id_1" not in index_names:
                self.feedbacks.create_index(
                    [("post_id", ASCENDING)],
                    unique=True,
                    name="post_id_unique_idx"
                )
                logger.info("[MongoDB] 创建post_id唯一索引")

            # 创建created_at索引（用于排序）
            if "created_at_-1" not in index_names:
                self.feedbacks.create_index(
                    [("created_at", DESCENDING)],
                    name="created_at_idx",
                    background=True
                )
                logger.info("[MongoDB] 创建created_at索引")

            # 新增：创建时间戳索引（用于正确排序）
            if "created_at_timestamp_-1" not in index_names:
                self.feedbacks.create_index(
                    [("created_at_timestamp", DESCENDING)],
                    name="created_at_timestamp_idx",
                    background=True
                )
                logger.info("[MongoDB] 创建created_at_timestamp索引")

        except OperationFailure as e:
            logger.error(f"[MongoDB] 索引创建失败: {e}")

    def insert_feedback(self, feedback: Dict[str, Any]) -> bool:
        """插入单条反馈，返回是否成功"""
        try:
            result = self.feedbacks.insert_one(feedback)
            logger.debug(f"[MongoDB] 插入成功: {feedback.get('post_id')}")
            return result.inserted_id is not None
        except DuplicateKeyError:
            logger.debug(f"[MongoDB] 数据已存在: {feedback.get('post_id')}")
            return False
        except Exception as e:
            logger.error(f"[MongoDB] 插入失败 {feedback.get('post_id')}: {e}")
            return False

    def insert_many_feedbacks(self, feedbacks: List[Dict[str, Any]]) -> tuple:
        """批量插入，返回(成功数, 重复数)"""
        if not feedbacks:
            return 0, 0

        success = 0
        duplicate = 0

        for feedback in feedbacks:
            if self.insert_feedback(feedback):
                success += 1
            else:
                duplicate += 1

        return success, duplicate

    def feedback_exists(self, post_id: str) -> bool:
        """检查post_id是否已存在"""
        try:
            return self.feedbacks.find_one({"post_id": post_id}) is not None
        except Exception as e:
            logger.error(f"[MongoDB] 查询失败 {post_id}: {e}")
            return False

    def get_latest_feedback(self) -> Optional[Dict[str, Any]]:
        """获取最新的反馈（按created_at_timestamp排序）"""
        try:
            # 优先按时间戳排序
            return self.feedbacks.find_one(
                sort=[("created_at_timestamp", DESCENDING)]
            )
        except Exception as e:
            logger.error(f"[MongoDB] 获取最新数据失败: {e}")
            # 回退到按字符串排序
            try:
                return self.feedbacks.find_one(
                    sort=[("created_at", DESCENDING)]
                )
            except:
                return None

    def count_feedbacks(self) -> int:
        """统计反馈总数"""
        try:
            return self.feedbacks.count_documents({})
        except Exception as e:
            logger.error(f"[MongoDB] 统计失败: {e}")
            return 0

    def close(self):
        """关闭连接"""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("[MongoDB] 连接已关闭")


# 全局实例
mongodb_client = MongoDBClient()