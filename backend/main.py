# main.py
from fastapi import FastAPI, HTTPException
from services.feedback_service import load_feedback_list
from services.keyword_service import load_keywords, save_keywords
from models.feedback import Feedback
from models.keyword import Keyword
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SentinelEye API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite 默认端口
        "http://localhost:3000",  # 可能的其他前端端口
    ],
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)
@app.get("/feedback/recent", response_model=list[Feedback])
def get_recent_feedback(limit: int = 5):
    """
    获取最近的反馈（默认 5 条）
    """
    return load_feedback_list(limit)


# 关键字 CRUD API
@app.get("/keywords")
def get_keywords():
    return load_keywords()

# 添加
@app.post("/keywords")
def add_keyword(item: Keyword):
    keywords = load_keywords()
    print(type(keywords))
    if item.keyword in keywords:
        raise HTTPException(status_code=400, detail="关键词已存在")

    keywords.append(item.keyword)
    save_keywords(keywords)
    return {"message": "添加成功", "keywords": keywords}

# ---- 删除关键词 ----
@app.delete("/keywords/{keyword}")
def delete_keyword(keyword: str):
    keywords = load_keywords()

    if keyword not in keywords:
        raise HTTPException(status_code=404, detail="关键词不存在")

    keywords.remove(keyword)
    save_keywords(keywords)
    return {"message": "删除成功", "keywords": keywords}

# ---- 修改关键词 ----
@app.put("/keywords")
def update_keyword(old: str, new: str):
    keywords = load_keywords()

    if old not in keywords:
        raise HTTPException(status_code=404, detail="原关键词不存在")

    if new in keywords:
        raise HTTPException(status_code=400, detail="目标关键词已存在")

    index = keywords.index(old)
    keywords[index] = new
    save_keywords(keywords)
    return {"message": "更新成功", "keywords": keywords}