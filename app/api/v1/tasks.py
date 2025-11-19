"""Task-related endpoints."""
import logging
from flask import request
from celery.result import AsyncResult

from app.tasks import add

logger = logging.getLogger(__name__)


def add_route(x: int, y: int):
    """Trigger the Celery add task."""
    logger.info("Received add request: %s + %s", x, y)
    task = add.delay(int(x), int(y))
    logger.debug("Queued task id: %s", task.id)
    return {"task_id": task.id}


def task_status():
    """Return the state/result for a Celery task."""
    task_id = request.args.get("task_id")
    if not task_id:
        logger.warning("Task status requested without task_id")
        return {"error": "Missing parameter 'task_id'"}, 400

    result = AsyncResult(task_id)
    logger.debug("Task %s state: %s", task_id, result.state)

    if result.ready():
        return {"state": result.state, "result": result.result}
    return {"state": result.state}

