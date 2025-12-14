import json
from pathlib import Path
from core.mongo_client import mongodb_client

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "keywords.json"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    keywords = json.load(f)

for k in keywords:
    try:
        mongodb_client.db.keywords.insert_one({"keyword": k})
    except Exception:
        pass  # 已存在就跳过

print("同步完成")
