import clip
import torch
from PIL import Image

# =========================
# 1. 模型初始化（只加载一次）
# =========================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL, PREPROCESS = clip.load("ViT-B/32", device=DEVICE)

PROMPT_GROUPS = {
    "bsod": [
        "a photo of a windows blue screen error",
        "a photo of a windows BSOD crash screen",
        "a system crash error screen on a computer"
    ],
    "black_screen": [
        "a photo of a computer black screen error",
        "a computer monitor showing nothing but black",
        "a powered on computer with a black screen"
    ],
    "dark_but_normal": [
        "a dark blue computer wallpaper",
        "a programming IDE with dark theme",
        "a dark themed desktop screen"
    ],
    "normal_desktop": [
        "a photo of a normal computer desktop",
        "a windows desktop with icons"
    ],
    "mobile": [
        "a mobile phone screenshot",
        "a smartphone screen photo"
    ]
}

# 展平 prompt
ALL_PROMPTS = []
PROMPT_TO_GROUP = []

for group, prompts in PROMPT_GROUPS.items():
    for p in prompts:
        ALL_PROMPTS.append(p)
        PROMPT_TO_GROUP.append(group)

TEXT_TOKENS = clip.tokenize(ALL_PROMPTS).to(DEVICE)

# =========================
# 2. 核心封装函数
# =========================
def clip_image_decision(image_path: str) -> dict:
    """
    输入：图片路径
    输出：
    {
      "group_scores": {...},
      "clip_final_decision": {
        "type": "...",
        "score": ...
      }
    }
    """

    # 1️⃣ 加载图片
    image = PREPROCESS(
        Image.open(image_path).convert("RGB")
    ).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        image_features = MODEL.encode_image(image)
        text_features = MODEL.encode_text(TEXT_TOKENS)

        # 归一化
        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)

        # 相似度
        similarity = (image_features @ text_features.T).squeeze(0)

    # 2️⃣ 聚合到 group 级别（max vote）
    group_scores = {}

    for idx, group in enumerate(PROMPT_TO_GROUP):
        score = float(similarity[idx])
        group_scores[group] = max(group_scores.get(group, score), score)

    # 3️⃣ 最终判断
    final_type = max(group_scores, key=group_scores.get)
    final_score = group_scores[final_type]

    return {
        "group_scores": group_scores,
        "clip_final_decision": {
            "type": final_type,
            "score": final_score
        }
    }


# =========================
# 3. 本地测试
# =========================
if __name__ == "__main__":
    result = clip_image_decision("./test_data/3.jpg")
    print(result)
