from fastapi import FastAPI
from services.feedback_service import load_feedback_list
from models.feedback import Feedback

app = FastAPI(title="SentinelEye Feedback API")

@app.get("/feedback/all", response_model=list[Feedback])
def get_all_feedback():
    """
    返回所有爬虫抓取的数据
    """
    feedback_list = load_feedback_list()
    return feedback_list
