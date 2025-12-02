import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "keywords.json"

# 默认关键词
DEFAULT_KEYWORDS = ["蓝屏"]

def load_keywords():
    """
    读取关键词，如果文件不存在，则自动创建并初始化默认关键词
    """
    if not DATA_FILE.exists():
        # 如果 data 目录不存在，先创建
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        save_keywords(DEFAULT_KEYWORDS)
        return DEFAULT_KEYWORDS.copy()

    # 文件存在，读取数据
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            keywords = json.load(f)
        except json.JSONDecodeError:
            # 文件为空或损坏，重置默认关键词
            save_keywords(DEFAULT_KEYWORDS)
            return DEFAULT_KEYWORDS.copy()

    # 如果文件为空，也返回默认
    if not keywords:
        save_keywords(DEFAULT_KEYWORDS)
        return DEFAULT_KEYWORDS.copy()

    # 确保“蓝屏”一定存在
    if "蓝屏" not in keywords:
        keywords.insert(0, "蓝屏")
        save_keywords(keywords)

    return keywords


def save_keywords(keywords):
    """
    保存关键词到文件
    """
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(keywords, f, ensure_ascii=False, indent=4)
