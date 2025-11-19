# Docker 部署指南

本文档提供使用 Docker 部署 Flask + Celery + Redis 应用的详细说明。

## 文件结构

```
Flask_Celery_POC/
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml      # Docker Compose 服务编排配置
├── docker-entrypoint.sh    # 容器启动入口脚本
├── .dockerignore           # Docker 构建时忽略的文件
└── .env.example            # 环境变量配置示例（可选）
```

## 快速开始

### 方式一：使用 Docker Compose（推荐）

**1. 启动所有服务：**
```bash
docker-compose up -d
```

**2. 查看服务状态：**
```bash
docker-compose ps
```

**3. 查看日志：**
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f web
docker-compose logs -f celery-worker
```

**4. 停止服务：**
```bash
docker-compose down
```

**5. 停止并清理数据：**
```bash
docker-compose down -v
```

### 方式二：使用 Docker 命令

**1. 构建镜像：**
```bash
docker build -t flask-celery-poc:latest .
```

**2. 启动 Redis：**
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

**3. 运行 Flask 应用：**
```bash
docker run -d \
  --name flask-app \
  -p 5000:5000 \
  --link redis:redis \
  -e FLASK_ENV=production \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=sqlite:///instance/db/production.db \
  -e CELERY_BROKER_URL=redis://redis:6379/0 \
  -e CELERY_RESULT_BACKEND=redis://redis:6379/1 \
  -v $(pwd)/instance:/app/instance \
  flask-celery-poc:latest
```

**4. 运行 Celery Worker：**
```bash
docker run -d \
  --name celery-worker \
  --link redis:redis \
  -e FLASK_ENV=production \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=sqlite:///instance/db/production.db \
  -e CELERY_BROKER_URL=redis://redis:6379/0 \
  -e CELERY_RESULT_BACKEND=redis://redis:6379/1 \
  -v $(pwd)/instance:/app/instance \
  flask-celery-poc:latest \
  celery -A app.celery_app worker --loglevel=info
```

## 服务说明

### web（Flask 应用）
- **端口**: 5000
- **功能**: 运行 Flask 应用，提供 API 服务
- **健康检查**: `/api/ping`
- **自动执行**: 数据库迁移（在 docker-compose.yml 中配置）

### celery-worker（Celery 工作进程）
- **功能**: 处理异步任务
- **并发数**: 4（可在 docker-compose.yml 中调整）
- **依赖**: Redis 和 web 服务

### celery-beat（Celery 定时任务）
- **功能**: 调度定时任务
- **启动方式**: `docker-compose --profile beat up -d celery-beat`
- **默认**: 不启动（使用 profile 控制）

### redis（Redis 服务）
- **端口**: 6379
- **功能**: Celery broker 和结果后端
- **数据持久化**: 使用 volume `redis_data`

## 环境变量

可以通过 `.env` 文件或环境变量配置：

```env
FLASK_ENV=production
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=sqlite:///instance/db/production.db
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

## 数据库迁移

**使用 Docker Compose：**
```bash
docker-compose exec web alembic upgrade head
```

**使用 Docker：**
```bash
docker exec flask-app alembic upgrade head
```

## 常用命令

### 进入容器
```bash
docker-compose exec web bash
docker-compose exec celery-worker bash
```

### 查看容器资源使用
```bash
docker stats
```

### 重启服务
```bash
docker-compose restart web
docker-compose restart celery-worker
```

### 重建镜像
```bash
docker-compose build --no-cache
docker-compose up -d
```

## 本地开发 vs Docker

**本地开发：**
```bash
python wsgi.py  # 直接运行
```

**Docker 部署：**
```bash
docker-compose up -d  # 或 docker run ...
```

两种方式可以并存，互不影响。

## 故障排查

### 1. 容器无法启动
```bash
# 查看日志
docker-compose logs web

# 检查容器状态
docker-compose ps
```

### 2. 数据库连接问题
- 确保 Redis 服务已启动并健康
- 检查环境变量 `CELERY_BROKER_URL` 和 `CELERY_RESULT_BACKEND`

### 3. 端口冲突
- 如果 5000 端口被占用，修改 `docker-compose.yml` 中的端口映射：
  ```yaml
  ports:
    - "5001:5000"  # 改为其他端口
  ```

### 4. 权限问题
- Dockerfile 使用非 root 用户运行，确保数据目录有正确权限

## 生产环境建议

1. **使用 PostgreSQL 替代 SQLite**：
   ```yaml
   DATABASE_URL=postgresql://user:password@postgres:5432/dbname
   ```

2. **设置强密码的 SECRET_KEY**

3. **使用环境变量文件**（不要提交 `.env` 到版本控制）

4. **配置日志收集**（如 ELK、Fluentd）

5. **使用反向代理**（如 Nginx）

6. **配置 HTTPS**

7. **设置资源限制**：
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1'
         memory: 1G
   ```

