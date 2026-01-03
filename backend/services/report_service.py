# services/report_service.py
import os
from datetime import datetime
from typing import Dict, Any, Optional

from backend.ml.agent_week_report import (
    generate_week_report_with_storage, 
    ReportStorage
)

class ReportService:
    """报告服务类"""
    
    def __init__(self):
        self.storage = ReportStorage()
    
    async def create_report(self, start_date: str, end_date: str, report_type: str = "weekly") -> Dict[str, Any]:
        """创建报告并返回报告ID"""
        try:
            # 创建报告记录
            mongo_id = self.storage.create_report(start_date, end_date, report_type)
            
            return {
                "success": True,
                "report_id": mongo_id,
                "message": "报告生成任务已启动",
                "data": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "report_type": report_type
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"创建报告失败: {str(e)}"
            }
    
    async def get_report_status(self, report_id: str) -> Dict[str, Any]:
        """获取报告状态"""
        try:
            report = self.storage.get_report(report_id)
            if not report:
                return {
                    "success": False,
                    "error": "报告不存在"
                }
            
            return {
                "success": True,
                "data": {
                    "id": report_id,
                    "status": report.get("status"),
                    "steps": report.get("steps", []),
                    "start_date": report.get("start_date"),
                    "end_date": report.get("end_date"),
                    "report_type": report.get("report_type"),
                    "stats": report.get("stats", {}),
                    "has_pdf": report.get("pdf_stored", False),
                    "generated_at": report.get("generated_at"),
                    "error_message": report.get("error_message")
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"获取状态失败: {str(e)}"
            }
    
    async def get_report_content(self, report_id: str) -> Dict[str, Any]:
        """获取报告内容"""
        try:
            report = self.storage.get_report(report_id)
            if not report:
                return {
                    "success": False,
                    "error": "报告不存在"
                }
            
            if report.get("status") != "completed":
                return {
                    "success": False,
                    "error": "报告尚未完成生成"
                }
            
            return {
                "success": True,
                "data": {
                    "markdown": report.get("markdown_content", ""),
                    "key_issues": report.get("key_issues", ""),
                    "sentiment_analysis": report.get("sentiment_analysis", {}),
                    "stats": report.get("stats", {})
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"获取内容失败: {str(e)}"
            }
    
    async def list_reports(self, limit: int = 10) -> Dict[str, Any]:
        """获取报告列表"""
        try:
            reports = self.storage.list_reports(limit)
            return {
                "success": True,
                "data": reports
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"获取列表失败: {str(e)}"
            }
    
    def run_report_generation(self, report_id: str, start_date: str, end_date: str, report_type: str = "weekly"):
        """运行报告生成（用于后台任务）"""
        try:
            result = generate_week_report_with_storage(
                start_date=start_date,
                end_date=end_date,
                report_type=report_type,
                save_pdf=True,
                mongo_id=report_id
            )
            return result
        except Exception as e:
            print(f"报告生成失败: {str(e)}")
            raise

# 创建全局实例
report_service = ReportService()