FROM python:3.11-slim

# 1. 换国内 apt 源 (适配 Debian 12 Bookworm)
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && \
    apt-get install -y git build-essential && \
    rm -rf /var/lib/apt/lists/*

# 2. 设置工作目录为 /app (代码将存放在 /app/backend)
WORKDIR /app

# 3. 清华 pip 源配置
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 关键：将当前目录(backend文件夹内容)复制到容器的 /app/backend 目录下
# 这样你的 import backend.xxx 才能生效
COPY . ./backend/

# 6. 设置 PYTHONPATH，确保 Python 在 /app 下查找模块
ENV PYTHONPATH=/app

# 默认启动命令
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]