#!/bin/bash
set -e

echo "Starting application entrypoint..."

# 等待数据库/Redis 就绪（如果需要）
if [ -n "$WAIT_FOR_HOST" ]; then
    echo "Waiting for $WAIT_FOR_HOST to be ready..."
    while ! nc -z $WAIT_FOR_HOST $WAIT_FOR_PORT; do
        sleep 0.1
    done
    echo "$WAIT_FOR_HOST is ready!"
fi

# 运行数据库迁移
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# 执行传入的命令
exec "$@"

