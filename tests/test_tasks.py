"""Tests for Celery task endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from app.tasks import add

class TestTasks:
    """Test task endpoints."""

    @patch('app.api.v1.tasks.add.delay')
    def test_add_route(self, mock_delay, client):
        """Test triggering the add task."""
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_delay.return_value = mock_task

        response = client.get("/api/add/2/3")

        assert response.status_code == 200
        assert response.json() == {"task_id": "test-task-id"}
        mock_delay.assert_called_once_with(2, 3)

    @patch('app.api.v1.tasks.AsyncResult')
    def test_task_status_success(self, mock_async_result, client):
        """Test task status endpoint for successful task."""
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.result = 5
        mock_async_result.return_value = mock_result

        response = client.get("/api/task?task_id=test-id")

        assert response.status_code == 200
        body = response.json()
        assert body["state"] == "SUCCESS"
        assert body["result"] == 5

    @patch('app.api.v1.tasks.AsyncResult')
    def test_task_status_pending(self, mock_async_result, client):
        """Test task status endpoint for pending task."""
        mock_result = MagicMock()
        mock_result.state = "PENDING"
        mock_result.ready.return_value = False
        mock_async_result.return_value = mock_result

        response = client.get("/api/task?task_id=test-id")

        assert response.status_code == 200
        body = response.json()
        assert body["state"] == "PENDING"
        assert "result" not in body

    def test_task_status_missing_id(self, client):
        """Test task status endpoint without task_id."""
        response = client.get("/api/task")
        assert response.status_code == 400
        body = response.json()
        # Connexion validation error or custom error
        error_msg = body.get("detail", "") or body.get("error", "")
        assert "Missing" in error_msg and "task_id" in error_msg


class TestCeleryTasks:
    """Test Celery task logic directly."""

    def test_add_task(self):
        """Test the add task logic."""
        # Directly calling the function (not the task wrapper) if possible,
        # or calling the .run method if it's bound.
        # Since 'add' is decorated, add.run or add(x, y) works in eager mode or unit test
        # provided celery is configured for testing (task_always_eager).
        
        # For unit testing the logic inside the task:
        res = add(2, 3)
        assert res == 5

    @patch('app.tasks.celery')
    def test_add_task_with_app_context(self, mock_celery):
        """Test task execution with app context check."""
        mock_celery.app = MagicMock()
        # We just want to ensure no error is raised and logic flows
        res = add(10, 20)
        assert res == 30

