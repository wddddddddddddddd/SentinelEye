"""
仪表盘数据服务
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import json
from pathlib import Path

from models.dashboard import DashboardStats, TrendData, KeywordTrigger
from models.feedback import Feedback
# from services.feedback_service import load_feedback_list, DATA_FILE


class DashboardService:
    """仪表盘服务类"""

    def __init__(self, feedbacks: List[Feedback]):
        """
        初始化仪表盘服务

        Args:
            feedbacks: 反馈数据列表
        """
        self.feedbacks = feedbacks
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)

        # 加载关键词文件
        self.base_dir = Path(__file__).resolve().parent.parent
        self.keywords_file = self.base_dir / "data" / "keywords.json"
        self.urgent_keywords_file = self.base_dir / "data" / "urgent_keywords.json"

        # 加载关键词
        self.keywords = self._load_keywords()
        self.urgent_keywords = self._load_urgent_keywords()

    def _load_keywords(self) -> List[str]:
        """加载关键词"""
        try:
            with open(self.keywords_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception as e:
            print(f"加载关键词文件失败: {e}")
            return []

    def _load_urgent_keywords(self) -> List[str]:
        """加载紧急关键词"""
        try:
            with open(self.urgent_keywords_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("keywords", [])
        except Exception as e:
            print(f"加载紧急关键词文件失败: {e}")
            # 返回默认紧急关键词
            return ["紧急", "urgent", "马上", "立刻", "崩溃", "错误", "bug", "故障", "无法", "不能", "急"]

    def get_dashboard_stats(self) -> DashboardStats:
        """获取仪表盘统计数据"""
        if not self.feedbacks:
            return DashboardStats()

        # 按日期分组数据
        feedbacks_by_date = self._group_feedbacks_by_date()

        # 计算各种统计数据
        total_count = len(self.feedbacks)
        pending_count = self._count_pending_feedbacks()
        processed_count = self._count_processed_feedbacks()
        urgent_count = self._count_urgent_feedbacks()

        # 今日数据
        today_str = self.today.strftime("%Y-%m-%d")
        today_data = feedbacks_by_date.get(today_str, [])
        today_feedbacks = len(today_data)
        today_processed = self._count_processed_feedbacks(today_data)
        today_urgent = self._count_urgent_feedbacks(today_data)
        today_pending = self._count_pending_feedbacks(today_data)

        # 昨日数据
        yesterday_str = self.yesterday.strftime("%Y-%m-%d")
        yesterday_data = feedbacks_by_date.get(yesterday_str, [])
        yesterday_feedbacks = len(yesterday_data)
        yesterday_processed = self._count_processed_feedbacks(yesterday_data)
        yesterday_urgent = self._count_urgent_feedbacks(yesterday_data)
        yesterday_pending = self._count_pending_feedbacks(yesterday_data)

        # 计算增长率和差额
        feedback_growth_rate = self._calculate_growth_rate(today_feedbacks, yesterday_feedbacks)
        feedback_difference = today_feedbacks - yesterday_feedbacks
        pending_difference = today_pending - yesterday_pending
        urgent_difference = today_urgent - yesterday_urgent

        # 获取最近3天关键词触发
        recent_keyword_triggers = self._get_recent_keyword_triggers(3)

        # 获取趋势数据
        recent_trend = self._get_recent_trend(7)

        # 获取分类统计
        category_stats = self._get_category_stats()

        # 获取标签统计
        tag_stats = self._get_tag_stats()

        # 创建TrendData实例
        trend_data = TrendData(
            dates=recent_trend["dates"],
            feedbacks=recent_trend["feedbacks"],
            processed=recent_trend["processed"],
            urgent=recent_trend["urgent"]
        )

        return DashboardStats(
            total_feedbacks=total_count,
            pending_feedbacks=pending_count,
            processed_feedbacks=processed_count,
            urgent_feedbacks=urgent_count,

            today_feedbacks=today_feedbacks,
            today_processed=today_processed,
            today_urgent=today_urgent,
            today_pending=today_pending,

            yesterday_feedbacks=yesterday_feedbacks,
            yesterday_processed=yesterday_processed,
            yesterday_urgent=yesterday_urgent,
            yesterday_pending=yesterday_pending,

            feedback_growth_rate=feedback_growth_rate,
            feedback_difference=feedback_difference,
            pending_difference=pending_difference,
            urgent_difference=urgent_difference,

            recent_keyword_triggers=recent_keyword_triggers,
            recent_trend=trend_data,
            category_stats=category_stats,
            tag_stats=tag_stats
        )

    def _parse_feedback_date(self, feedback: Feedback) -> str:
        """解析反馈日期，返回YYYY-MM-DD格式，自动补零"""
        try:
            date_time_parts = feedback.created_at.split()
            if len(date_time_parts) < 1:
                return self.today.strftime("%Y-%m-%d")

            date_part = date_time_parts[0]
            date_components = date_part.split("-")
            if len(date_components) != 3:
                return self.today.strftime("%Y-%m-%d")

            year, month, day = date_components
            month = month.zfill(2)
            day = day.zfill(2)

            # 调整年份逻辑
            current_date = datetime.now()
            current_year = current_date.year

            try:
                data_year = int(year)
                data_month = int(month)
                data_day = int(day)

                # 如果数据年份明显大于当前年份，调整为今年或去年
                if data_year > current_year:
                    # 如果是12月，可能是去年的数据
                    if data_month == 12:
                        adjusted_year = current_year - 1
                    else:
                        adjusted_year = current_year

                    # 验证调整后的日期是否有效
                    try:
                        adjusted_date = datetime(adjusted_year, data_month, data_day)
                        # 如果调整后还是未来，使用今天
                        if adjusted_date > current_date:
                            return current_date.strftime("%Y-%m-%d")
                        return adjusted_date.strftime("%Y-%m-%d")
                    except ValueError:
                        return self.today.strftime("%Y-%m-%d")

                return f"{data_year}-{month}-{day}"

            except ValueError:
                return self.today.strftime("%Y-%m-%d")

        except Exception as e:
            return self.today.strftime("%Y-%m-%d")

    def _group_feedbacks_by_date(self) -> Dict[str, List[Feedback]]:
        """按日期分组反馈数据"""
        feedbacks_by_date = defaultdict(list)

        for feedback in self.feedbacks:
            feedback_date = self._parse_feedback_date(feedback)
            feedbacks_by_date[feedback_date].append(feedback)

        return feedbacks_by_date

    def _get_feedbacks_by_date_range(self, days: int = 3) -> Dict[str, List[Feedback]]:
        """获取最近N天的反馈数据"""
        feedbacks_by_date = self._group_feedbacks_by_date()
        result = {}

        for i in range(days):
            target_date = self.today - timedelta(days=i)
            date_str = target_date.strftime("%Y-%m-%d")
            if date_str in feedbacks_by_date:
                result[date_str] = feedbacks_by_date[date_str]

        return result

    def _count_pending_feedbacks(self, feedbacks: Optional[List[Feedback]] = None) -> int:
        """统计待处理反馈数量"""
        if feedbacks is None:
            feedbacks = self.feedbacks

        count = 0
        for feedback in feedbacks:
            if not hasattr(feedback, 'status') or not feedback.status:
                count += 1
            elif feedback.status.lower() in ["待处理", "未处理", "处理中", "pending", "open", "new"]:
                count += 1
            elif feedback.status == "已解决" and hasattr(feedback, 'reply_count') and feedback.reply_count == 0:
                # 标记为已解决但没有回复的，可能也需要关注
                count += 1

        return count

    def _count_processed_feedbacks(self, feedbacks: Optional[List[Feedback]] = None) -> int:
        """统计已处理反馈数量"""
        if feedbacks is None:
            feedbacks = self.feedbacks

        count = 0
        for feedback in feedbacks:
            if hasattr(feedback, 'status') and feedback.status:
                status_lower = feedback.status.lower()
                if any(word in status_lower for word in ["已处理", "处理完成", "resolved", "closed", "完成", "解决", "已解决"]):
                    count += 1
                elif hasattr(feedback, 'reply_count') and feedback.reply_count > 2:
                    count += 1

        return count

    def _count_urgent_feedbacks(self, feedbacks: Optional[List[Feedback]] = None) -> int:
        """统计紧急反馈数量（合并紧急关键词）"""
        if feedbacks is None:
            feedbacks = self.feedbacks

        count = 0
        # 合并所有紧急关键词
        all_urgent_keywords = set(self.urgent_keywords)

        for feedback in feedbacks:
            # 检查标题和内容中的紧急关键词
            title_lower = feedback.title.lower()
            content_lower = feedback.content.lower() if hasattr(feedback, 'content') and feedback.content else ""

            text_to_check = f"{title_lower} {content_lower}"

            # 检查是否包含紧急关键词
            for keyword in all_urgent_keywords:
                if keyword in text_to_check:
                    count += 1
                    break  # 找到一个关键词就计数，避免重复
                # 或者根据回复数/查看数判断（作为备选）
                elif hasattr(feedback, 'reply_count') and feedback.reply_count > 15:
                    count += 1
                elif hasattr(feedback, 'view_count') and feedback.view_count > 500:
                    count += 1
        return count

    def _calculate_growth_rate(self, current: int, previous: int) -> float:
        """计算增长率"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)

    def _get_recent_keyword_triggers(self, days: int = 3) -> List[KeywordTrigger]:
        """获取最近N天的关键词触发情况"""
        feedbacks_by_date = self._get_feedbacks_by_date_range(days)

        if not feedbacks_by_date or not self.keywords:
            return []

        # 统计每个关键词的出现次数
        keyword_counts = defaultdict(int)

        for date_str, feedbacks in feedbacks_by_date.items():
            for feedback in feedbacks:
                title_lower = feedback.title.lower()
                content_lower = feedback.content.lower() if hasattr(feedback, 'content') and feedback.content else ""
                text_to_check = f"{title_lower} {content_lower}"

                for keyword in self.keywords:
                    if keyword in text_to_check:
                        keyword_counts[keyword] += 1

        # 按出现次数排序，取前10个
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # 转换为KeywordTrigger对象
        triggers = []
        for keyword, count in sorted_keywords:
            # 简单判断趋势（可以根据历史数据更精确判断）
            trend = "up" if count > 2 else "stable" if count > 0 else "down"
            triggers.append(KeywordTrigger(keyword=keyword, count=count, trend=trend))

        return triggers

    def _get_recent_trend(self, days: int = 7) -> Dict[str, List]:
        """获取最近N天的趋势数据"""
        feedbacks_by_date = self._group_feedbacks_by_date()

        dates = []
        feedback_counts = []
        processed_counts = []
        urgent_counts = []

        # 生成最近N天的日期
        for i in range(days-1, -1, -1):
            current_date = self.today - timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            display_date = current_date.strftime("%m-%d")

            dates.append(display_date)

            daily_feedbacks = feedbacks_by_date.get(date_str, [])
            feedback_counts.append(len(daily_feedbacks))
            processed_counts.append(self._count_processed_feedbacks(daily_feedbacks))
            urgent_counts.append(self._count_urgent_feedbacks(daily_feedbacks))

        return {
            "dates": dates,
            "feedbacks": feedback_counts,
            "processed": processed_counts,
            "urgent": urgent_counts
        }

    def _get_category_stats(self) -> Dict[str, int]:
        """获取分类统计"""
        category_stats = defaultdict(int)

        for feedback in self.feedbacks:
            category = feedback.category if hasattr(feedback, 'category') and feedback.category else "未分类"
            category_stats[category] += 1

        sorted_stats = dict(sorted(category_stats.items(), key=lambda x: x[1], reverse=True))
        return sorted_stats

    def _get_tag_stats(self) -> Dict[str, int]:
        """获取标签统计"""
        tag_stats = defaultdict(int)

        for feedback in self.feedbacks:
            if hasattr(feedback, 'tags') and feedback.tags:
                for tag in feedback.tags:
                    tag_stats[tag] += 1

        return dict(tag_stats)


def get_dashboard_stats_from_json(limit: Optional[int] = None) -> DashboardStats:
    """
    从JSON文件获取仪表盘统计数据

    Args:
        limit: 限制加载的数据条数（可选）

    Returns:
        DashboardStats: 仪表盘统计数据
    """
    try:
        if limit:
            feedbacks = load_feedback_list(limit)
        else:
            # 加载所有数据
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            feedbacks = [Feedback(**item) for item in data]

        dashboard_service = DashboardService(feedbacks)
        return dashboard_service.get_dashboard_stats()

    except Exception as e:
        import traceback
        print(f"获取仪表盘数据失败: {str(e)}")
        traceback.print_exc()
        raise