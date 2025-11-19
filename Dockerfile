# 多阶段构建 Dockerfile
# 阶段1: 构建阶段
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /build

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
# 注意：删除了 requirements.txt，因为它是 Poetry 项目
COPY pyproject.toml poetry.lock* ./

# 安装 Poetry 并配置为不在容器内创建虚拟环境
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false

# 使用 Poetry 安装依赖
# --no-root: 不安装当前项目本身
# --no-dev: 不安装开发依赖（如 pytest）
RUN poetry install --no-root --only main

# 阶段2: 运行阶段
FROM python:3.11-slim

# 安装 curl 用于健康检查
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/instance/db && \
    chown -R appuser:appuser /app

# 从构建阶段复制已安装的包
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY --chown=appuser:appuser . .

# 复制并设置启动脚本权限
COPY --chown=appuser:appuser docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# 切换到非 root 用户
USER appuser

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    PYTHONPATH=/app

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/ping || exit 1

# 设置入口点
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# 默认命令（可以通过 docker-compose 或命令行覆盖）
CMD ["python", "wsgi.py"]
