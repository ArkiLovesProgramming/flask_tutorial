# Flask Tutorial Project

A tutorial project for learning Flask and related technologies, including Celery distributed task queue, Redis broker, and Connexion/Swagger API documentation.

## Features

- **Application Factory Pattern** — Clean, scalable Flask architecture
- **Celery Integration** — Asynchronous task processing with Redis broker
- **Connexion + Swagger** — OpenAPI 3.0 specification with interactive API documentation
- **Environment-based Config** — Separate configs for dev/prod/testing
- **Flask-SQLAlchemy** — Database models with Alembic migrations
- **Flask-Caching** — Built-in caching support

## Quick Start

### Prerequisites

- Python 3.10+
- Redis server (or Docker)
- Docker & Docker Compose (for Docker deployment)

### Setup

1. **Create virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate  # Windows
   source .venv/bin/activate  # macOS/Linux
   ```

2. **Install Poetry inside the project venv (keeps everything self-contained):**
   ```bash
   pip install poetry
   ```

3. **Tell Poetry to reuse the existing `.venv` interpreter:**
   ```bash
   poetry env use .venv\Scripts\python.exe      # Windows
   poetry env use .venv/bin/python              # macOS/Linux
   ```

4. **Install dependencies via Poetry:**
   ```bash
   poetry install
   ```

5. **Configure environment variables:**
   ```bash
   # Copy the example .env file
   cp .env.example .env
   
   # Edit .env file and set SECRET_KEY (required)
   # Generate a secure key: python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

6. **Start Redis:**
   ```bash
   # Using Docker (recommended)
   docker run -d --name redis-local -p 6379:6379 redis:7
   ```

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

### Running the Application

**Development Mode:**

```bash
# Terminal 1: Flask application
python wsgi.py

# Terminal 2: Celery worker
celery -A app.celery_app worker --loglevel=info --pool=solo  # Windows
celery -A app.celery_app worker --loglevel=info  # macOS/Linux
```

**Production Mode:**

```bash
# Using uvicorn
uvicorn wsgi:app --host 0.0.0.0 --port 5000 --workers 4

# Using gunicorn with uvicorn workers
gunicorn wsgi:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000
```

## Docker Deployment

### Using Docker Compose (Recommended)

**快速启动所有服务（Flask + Celery + Redis）：**

```bash
# 1. 复制环境变量文件（可选）
cp .env.example .env
# 编辑 .env 文件设置你的配置

# 2. 构建并启动所有服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down

# 5. 停止并删除数据卷（清理数据）
docker-compose down -v
```

**启动特定服务：**

```bash
# 只启动 Redis
docker-compose up -d redis

# 启动 Flask 和 Redis（不启动 Celery worker）
docker-compose up -d redis web

# 启动 Celery Beat（定时任务，需要额外指定 profile）
docker-compose --profile beat up -d celery-beat
```

**查看服务状态：**

```bash
docker-compose ps
```

**执行数据库迁移：**

```bash
# 在 web 容器中执行
docker-compose exec web alembic upgrade head
```

### Using Docker Only

**构建镜像：**

```bash
docker build -t flask-celery-poc:latest .
```

**运行容器：**

```bash
# 1. 启动 Redis（如果还没有）
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 2. 运行 Flask 应用
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

# 3. 运行 Celery Worker
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

**Windows PowerShell 示例：**

```powershell
# 运行 Flask 应用
docker run -d `
  --name flask-app `
  -p 5000:5000 `
  --link redis:redis `
  -e FLASK_ENV=production `
  -e SECRET_KEY=your-secret-key `
  -e DATABASE_URL=sqlite:///instance/db/production.db `
  -e CELERY_BROKER_URL=redis://redis:6379/0 `
  -e CELERY_RESULT_BACKEND=redis://redis:6379/1 `
  -v ${PWD}/instance:/app/instance `
  flask-celery-poc:latest
```

### Docker 服务说明

- **web**: Flask 应用服务，运行在 5000 端口
- **celery-worker**: Celery 工作进程，处理异步任务
- **celery-beat**: Celery 定时任务调度器（可选，使用 `--profile beat` 启动）
- **redis**: Redis 服务，用作 Celery broker 和结果后端

### 本地开发 vs Docker

**本地开发：**
```bash
python wsgi.py  # 直接运行
```

**Docker 部署：**
```bash
docker-compose up -d  # 或 docker run ...
```

两种方式可以并存，互不影响。

## Testing

- Install dev dependencies (already handled if you ran `poetry install` with the default groups).
- Run pytest through Poetry to ensure it uses the managed virtualenv:

```bash
poetry run pytest
poetry run pytest --cov  # include coverage report
```

Tests live under `tests/` with fixtures in `tests/conftest.py` so you can add new modules per domain (`test_tasks.py`, `test_users.py`, etc.).

### Access Points

- **API**: http://localhost:5000/api
- **Swagger UI**: http://localhost:5000/api/ui
- **OpenAPI JSON**: http://localhost:5000/api/openapi.json

## API Endpoints

- `GET /api/ping` - Health check
- `GET /api/add/{x}/{y}` - Trigger async add task
- `GET /api/task?task_id={id}` - Check task status
- `POST /api/add_user` - Create user (JSON body or query params)
- `GET /api/user/{user_id}` - Get user data (cached)

## Environment Variables

The application uses `.env` file for configuration. Both `python wsgi.py` and `docker-compose` will automatically load environment variables from `.env` file.

**Setup:**

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file and set your configuration:**
   ```env
   # Required: Generate a secure secret key
   # You can generate one using: python -c "import secrets; print(secrets.token_urlsafe(32))"
   SECRET_KEY=your-secret-key-here
   
   # Optional: JWT secret (defaults to SECRET_KEY if not set)
   JWT_SECRET_KEY=
   
   # Database (SQLite for development, PostgreSQL for production)
   DATABASE_URL=sqlite:///instance/db/test.db
   
   # Redis configuration
   CELERY_BROKER_URL=redis://127.0.0.1:6379/0
   CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
   ```

**Important Notes:**
- `.env` file is already in `.gitignore` - it will not be committed to version control
- For production, set environment variables directly or use a secure secrets management system
- The application will fail to start if `SECRET_KEY` is not set
- Both `python wsgi.py` and `docker-compose up` will automatically load `.env` file

**Generate a secure SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Project Structure

```
flask_tutorial/
├── app/
│   ├── __init__.py              # Shared resources (db, cache)
│   ├── api/
│   │   └── v1/                  # Versioned controllers (health/tasks/users)
│   ├── config/                  # Environment-specific config modules
│   ├── models/                  # SQLAlchemy models
│   ├── services/                # Business logic layer
│   ├── celery_app.py            # Celery setup
│   └── connexion_app.py         # Connexion application factory
├── tests/
│   ├── conftest.py              # Pytest fixtures (app & client)
│   ├── test_health.py           # Health endpoint coverage
│   └── test_users.py            # User workflow coverage
├── openapi/
│   └── openapi.yaml             # OpenAPI 3.0 specification
├── migrations/                  # Alembic database migrations
├── wsgi.py                      # Application entry point
├── Dockerfile                   # Docker 镜像构建文件
├── docker-compose.yml           # Docker Compose 编排配置
├── docker-entrypoint.sh         # Docker 容器启动脚本
├── .dockerignore                # Docker 构建忽略文件
├── .env.example                 # 环境变量示例文件
├── pyproject.toml               # Poetry project + dependencies
├── poetry.lock                  # Locked dependency graph
└── requirements.txt             # Legacy pin file (optional reference)
```

## Technologies

- Flask 2.x
- Connexion 3.x (OpenAPI/Swagger)
- Celery 5.x
- Redis
- Flask-SQLAlchemy
- Flask-Caching
- Alembic

## License

MIT
