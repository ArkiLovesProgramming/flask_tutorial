# Flask Tutorial Project

A tutorial project for learning Flask and related technologies, including Celery distributed task queue, Redis broker, and Connexion/Swagger API documentation.

## Features

- **Application Factory Pattern** — Clean, scalable Flask architecture
- **Celery Integration** — Asynchronous task processing with Redis broker
- **Connexion + Swagger** — OpenAPI 3.0 specification with interactive API documentation
- **Environment-based Config** — Separate configurations for development, production, and testing
- **Flask-SQLAlchemy** — Database models with Alembic migrations
- **Flask-Caching** — Built-in caching support
- **JWT Authentication** — Secure API authentication
- **Docker Support** — Containerized deployment with Docker Compose

## Prerequisites

- Python 3.10+
- Redis server (or Docker)
- Docker & Docker Compose (optional, for containerized deployment)
- Poetry (for dependency management)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd flask_tutorial
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows
.venv\Scripts\Activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install Poetry

```bash
pip install poetry
```

### 4. Configure Poetry to Use Existing Virtual Environment

```bash
# Windows
poetry env use .venv\Scripts\python.exe
# macOS/Linux
poetry env use .venv/bin/python
```

### 5. Install Dependencies

```bash
poetry install
```

### 6. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` file and set required variables:

```env
# Required: Generate a secure secret key
# Generate one: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-secret-key-here

# Optional: JWT secret (defaults to SECRET_KEY if not set)
JWT_SECRET_KEY=

# Database (SQLite for development, PostgreSQL for production)
DATABASE_URL=sqlite:///instance/db/test.db

# Redis configuration
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/1
```

### 7. Start Redis

```bash
# Using Docker (recommended)
docker run -d --name redis-local -p 6379:6379 redis:7

# Or use a local Redis installation
```

### 8. Run Database Migrations

```bash
alembic upgrade head
```

## Running the Application

### Development Mode

Run the application in development mode:

```bash
# Terminal 1: Start Flask application
python wsgi.py

# Terminal 2: Start Celery worker
# Windows
celery -A app.celery_app worker --loglevel=info --pool=solo
# macOS/Linux
celery -A app.celery_app worker --loglevel=info
```

The application will be available at:
- **API**: http://localhost:5000/api
- **Swagger UI**: http://localhost:5000/api/ui
- **OpenAPI JSON**: http://localhost:5000/api/openapi.json

### Production Mode

```bash
# Using uvicorn
uvicorn wsgi:app --host 0.0.0.0 --port 5000 --workers 4

# Using gunicorn with uvicorn workers
gunicorn wsgi:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000
```

## Docker Deployment

### Using Docker Compose (Recommended)

**Start all services (Flask + Celery + Redis):**

```bash
# 1. Copy environment file (optional)
cp .env.example .env
# Edit .env file with your configuration

# 2. Build and start all services
docker-compose up -d

# 3. View logs
docker-compose logs -f

# 4. Stop services
docker-compose down

# 5. Stop and remove volumes (clean data)
docker-compose down -v
```

**Start specific services:**

```bash
# Start only Redis
docker-compose up -d redis

# Start Flask and Redis (without Celery worker)
docker-compose up -d redis web

# Start Celery Beat (scheduled tasks, requires profile)
docker-compose --profile beat up -d celery-beat
```

**Check service status:**

```bash
docker-compose ps
```

**Run database migrations:**

```bash
docker-compose exec web alembic upgrade head
```

### Using Docker Only

**Build the image:**

```bash
docker build -t flask-tutorial:latest .
```

**Run containers:**

```bash
# 1. Start Redis (if not already running)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 2. Run Flask application
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
  flask-tutorial:latest

# 3. Run Celery Worker
docker run -d \
  --name celery-worker \
  --link redis:redis \
  -e FLASK_ENV=production \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=sqlite:///instance/db/production.db \
  -e CELERY_BROKER_URL=redis://redis:6379/0 \
  -e CELERY_RESULT_BACKEND=redis://redis:6379/1 \
  -v $(pwd)/instance:/app/instance \
  flask-tutorial:latest \
  celery -A app.celery_app worker --loglevel=info
```

**Windows PowerShell example:**

```powershell
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
  flask-tutorial:latest
```

### Docker Services

- **web**: Flask application service, runs on port 5000
- **celery-worker**: Celery worker process for handling asynchronous tasks
- **celery-beat**: Celery scheduled task scheduler (optional, start with `--profile beat`)
- **redis**: Redis service used as Celery broker and result backend

## API Endpoints

- `GET /api/ping` - Health check endpoint
- `GET /api/add/{x}/{y}` - Trigger asynchronous addition task
- `GET /api/task?task_id={id}` - Check task status
- `POST /api/add_user` - Create a new user (JSON body or query parameters)
- `GET /api/user/{user_id}` - Get user data (cached)

For interactive API documentation, visit: http://localhost:5000/api/ui

## Testing

Run tests using pytest:

```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_users.py
```

Tests are located in the `tests/` directory with fixtures defined in `tests/conftest.py`.

## Environment Variables

The application uses a `.env` file for configuration. Both `python wsgi.py` and `docker-compose` automatically load environment variables from the `.env` file.

**Important Notes:**
- The `.env` file is already in `.gitignore` and will not be committed to version control
- For production, set environment variables directly or use a secure secrets management system
- The application will fail to start if `SECRET_KEY` is not set

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
│   │   └── v1/                  # Versioned API controllers
│   │       ├── auth.py          # Authentication endpoints
│   │       ├── health.py        # Health check endpoints
│   │       ├── tasks.py         # Task endpoints
│   │       └── users.py         # User endpoints
│   ├── config/                  # Environment-specific configurations
│   ├── models/                  # SQLAlchemy database models
│   ├── services/                # Business logic layer
│   ├── utils/                   # Utility functions
│   ├── celery_app.py            # Celery application setup
│   └── connexion_app.py         # Connexion application factory
├── tests/                       # Test suite
│   ├── conftest.py              # Pytest fixtures
│   ├── test_auth.py             # Authentication tests
│   ├── test_health.py           # Health endpoint tests
│   ├── test_tasks.py            # Task endpoint tests
│   └── test_users.py            # User endpoint tests
├── openapi/
│   └── openapi.yaml             # OpenAPI 3.0 specification
├── migrations/                  # Alembic database migrations
├── docs/                        # Additional documentation
├── wsgi.py                      # Application entry point
├── Dockerfile                   # Docker image build file
├── docker-compose.yml           # Docker Compose configuration
├── docker-entrypoint.sh         # Docker container entrypoint script
├── .env.example                 # Environment variables example
├── pyproject.toml               # Poetry project configuration
└── poetry.lock                  # Locked dependency versions
```

## Technologies

- **Flask 2.x** - Web framework
- **Connexion 3.x** - OpenAPI/Swagger framework
- **Celery 5.x** - Distributed task queue
- **Redis** - Message broker and cache
- **Flask-SQLAlchemy** - Database ORM
- **Flask-Caching** - Caching support
- **Alembic** - Database migrations
- **PyJWT** - JWT authentication
- **Poetry** - Dependency management

## License

MIT
