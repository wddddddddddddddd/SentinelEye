FROM python:3.11-slim

# 1. 换国内 apt 源并安装 WeasyPrint 所需的系统依赖
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && \
    apt-get install -y \
    git \
    build-essential \
    python3-dev \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    # --- 修正后的包名 ---
    libgdk-pixbuf-2.0-0 \
    libgobject-2.0-0 \
    # --- 额外建议：支持 PDF 中文显示 (如果不装，中文会乱码) ---
    fonts-wqy-zenhei \
    # ------------------
    && rm -rf /var/lib/apt/lists/*

# 2. 设置工作目录为 /app
WORKDIR /app

# 3. 清华 pip 源配置
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 复制后端代码
COPY . ./backend/

# 6. 设置 PYTHONPATH
ENV PYTHONPATH=/app

# 默认启动命令
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
