import clip
import torch
from PIL import Image
from typing import Union, List

# =========================
# 1. 模型只加载一次
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

# 展平成 prompt 列表
ALL_PROMPTS = []
PROMPT_INDEX = []  # (group_name, prompt)

for group, prompts in PROMPT_GROUPS.items():
    for p in prompts:
        PROMPT_INDEX.append((group, p))
        ALL_PROMPTS.append(p)

TEXT_TOKENS = clip.tokenize(ALL_PROMPTS).to(DEVICE)

# =========================
# 2. 核心函数
# =========================
def clip_bsod_score(image_paths: Union[str, List[str]]):

    if isinstance(image_paths, str):
        image_paths = [image_paths]

    images = []
    valid_paths = []

    for path in image_paths:
        try:
            img = Image.open(path).convert("RGB")
            images.append(PREPROCESS(img))
            valid_paths.append(path)
        except Exception as e:
            print(f"[WARN] skip image {path}: {e}")

    if not images:
        return {}

    image_tensor = torch.stack(images).to(DEVICE)

    with torch.no_grad():
        image_features = MODEL.encode_image(image_tensor)
        text_features = MODEL.encode_text(TEXT_TOKENS)

        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)

        similarity = image_features @ text_features.T
        # shape: [num_images, num_prompts]

    results = {}

    for img_idx, path in enumerate(valid_paths):
        group_scores = {}

        # 1️⃣ 先聚合到 group 级别（多 prompt 投票）
        for i, (group, _) in enumerate(PROMPT_INDEX):
            score = float(similarity[img_idx][i])
            group_scores.setdefault(group, []).append(score)

        # 2️⃣ 每个 group 取 max（比 mean 稳定）
        final_group_scores = {
            group: max(scores)
            for group, scores in group_scores.items()
        }

        # 3️⃣ CLIP 的“最终判断”
        best_group = max(final_group_scores, key=final_group_scores.get)

        results[path] = {
            "group_scores": final_group_scores,
            "clip_final_decision": {
                "type": best_group,
                "score": final_group_scores[best_group]
            }
        }

    return results


# =========================
# 3. 测试
# =========================
if __name__ == "__main__":
    imgs = [
        "./test_data/1.jpg",
        "./test_data/2.jpg",
        "./test_data/3.jpg"
    ]

    res = clip_bsod_score(imgs)

    for img, info in res.items():
        print(f"\n[{img}]")
        for k, v in info["group_scores"].items():
            print(f"{k:18s} -> {v:.4f}")

        decision = info["clip_final_decision"]
        print(f">>> CLIP 最像：{decision['type']} ({decision['score']:.4f})")
