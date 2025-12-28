import base64
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_models.tongyi import ChatTongyi
import os
from dotenv import load_dotenv

load_dotenv(override=True)
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")



def image_to_base64(image_path):
    """将图片转换为Base64编码字符串"""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string
    except FileNotFoundError:
        print(f"错误：找不到文件 {image_path}")
        print(f"当前工作目录：{os.getcwd()}")
        return None
    except Exception as e:
        print(f"读取图片时出错：{e}")
        return None

# 1. 将本地图片转换为Base64
image_path = "./test_data/1.jpg"  # 您的图片路径
base64_image = image_to_base64(image_path)

if base64_image is None:
    print("Base64转换失败，程序退出")
    exit(1)

# 2. 创建符合DashScope格式的消息列表
# 对于Base64格式，需要添加data:image/jpeg;base64,前缀
messages = [
    {"role": "system", "content": "你是一个专业的问答专家"},
    {
        "role": "user",
        "content": [
            # 使用Base64格式的图片数据
            {"image": f"data:image/jpeg;base64,{base64_image}"},
            {"text": "请描述图片"}
        ]
    }
]

# 3. 初始化模型
model = ChatTongyi(model="qwen3-vl-flash")

# 4. 调用模型

res = model.invoke(messages)

print(res.content)
