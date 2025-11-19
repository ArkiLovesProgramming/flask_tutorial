"""Tests for authentication decorators."""
import pytest
from flask import Flask, request
from app.utils.auth_decorator import require_auth, optional_auth
from app.utils.jwt_utils import generate_access_token


@pytest.fixture
def test_app(client):
    """Get Flask app from client."""
    return client.application


class TestRequireAuthDecorator:
    """Test @require_auth decorator."""

    def test_require_auth_with_valid_token(self, client, test_user):
        """Test decorator with valid token."""
        from unittest.mock import patch

        # Generate token
        token = generate_access_token(test_user.id, test_user.username)

        # Mock Redis to return session
        with patch('app.services.auth_service.get_redis_client') as mock_get_redis:
            mock_redis = mock_get_redis.return_value
            # Mock session exists for this user
            mock_redis.keys.return_value = [f"session:{test_user.id}:anyprefix"]
            mock_redis.exists.return_value = False

            # Create a test endpoint
            @require_auth
            def protected_endpoint():
                return {"user_id": request.current_user["user_id"]}

            # Set up request context
            with client.application.test_request_context(
                headers={"Authorization": f"Bearer {token}"}
            ):
                response = protected_endpoint()
                # Decorator should allow access, return dict
                assert isinstance(response, dict)
                assert response["user_id"] == test_user.id

    def test_require_auth_without_token(self, client):
        """Test decorator without token."""
        @require_auth
        def protected_endpoint():
            return {"message": "success"}

        with client.application.test_request_context():
            response = protected_endpoint()
            # Decorator returns Flask Response object or tuple
            if isinstance(response, tuple):
                assert response[1] == 401
                assert "required" in response[0].get_json().get("error", "").lower()
            else:
                assert response.status_code == 401
                assert "required" in response.get_json().get("error", "").lower()

    def test_require_auth_with_invalid_token(self, client):
        """Test decorator with invalid token."""
        from unittest.mock import patch
        
        @require_auth
        def protected_endpoint():
            return {"message": "success"}

        with patch('app.services.auth_service.get_redis_client') as mock_get_redis:
            mock_redis = mock_get_redis.return_value
            mock_redis.keys.return_value = []
            mock_redis.exists.return_value = False
            
            with client.application.test_request_context(
                headers={"Authorization": "Bearer invalid.token"}
            ):
                response = protected_endpoint()
                if isinstance(response, tuple):
                    assert response[1] == 401
                else:
                    assert response.status_code == 401


class TestOptionalAuthDecorator:
    """Test @optional_auth decorator."""

    def test_optional_auth_with_valid_token(self, client, test_user):
        """Test decorator with valid token."""
        from unittest.mock import patch

        token = generate_access_token(test_user.id, test_user.username)

        with patch('app.services.auth_service.get_redis_client') as mock_get_redis:
            mock_redis = mock_get_redis.return_value
            # Mock session exists for this user
            mock_redis.keys.return_value = [f"session:{test_user.id}:anyprefix"]
            mock_redis.exists.return_value = False

            @optional_auth
            def public_endpoint():
                if hasattr(request, 'current_user') and request.current_user:
                    return {"user_id": request.current_user["user_id"], "authenticated": True}
                return {"authenticated": False}

            with client.application.test_request_context(
                headers={"Authorization": f"Bearer {token}"}
            ):
                response = public_endpoint()
                assert isinstance(response, dict)
                assert response["authenticated"] is True
                assert response["user_id"] == test_user.id

    def test_optional_auth_without_token(self, client):
        """Test decorator without token."""
        @optional_auth
        def public_endpoint():
            if hasattr(request, 'current_user') and request.current_user:
                return {"authenticated": True}
            return {"authenticated": False}

        with client.application.test_request_context():
            response = public_endpoint()
            assert response["authenticated"] is False

    def test_optional_auth_with_invalid_token(self, client):
        """Test decorator with invalid token (should still work, just not authenticated)."""
        @optional_auth
        def public_endpoint():
            if hasattr(request, 'current_user') and request.current_user:
                return {"authenticated": True}
            return {"authenticated": False}

        with client.application.test_request_context(
            headers={"Authorization": "Bearer invalid.token"}
        ):
            response = public_endpoint()
            assert response["authenticated"] is False

