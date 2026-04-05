# AI冥思记忆系统 v2.0 - Docker容器化配置
# 基于Python 3.11，支持GPU加速

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgomp1 \
    libopenblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements_meditation_enhanced.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements_meditation_enhanced.txt

# 复制应用程序代码
COPY . .

# 创建数据目录
RUN mkdir -p /data/models /data/state /data/results

# 设置数据卷
VOLUME ["/data/models", "/data/state", "/data/results"]

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# 设置默认命令
CMD ["python", "meditation_engine_with_gnn_fixed.py", "--help"]

# 暴露端口（如果需要Web界面）
EXPOSE 8080

# 标签信息
LABEL maintainer="Garylauchina <garylauchina@icloud.com>" \
      version="v2.0" \
      description="AI冥思记忆系统 - 向量+图结构混合记忆管理系统" \
      license="MIT"
