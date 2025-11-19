"""Tests for authentication endpoints and services."""
import os
import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app import db
from app.models import User
from app.services.auth_service import AuthService
from app.utils.jwt_utils import decode_token, generate_access_token



@pytest.fixture
def mock_redis():
    """Mock Redis client for session storage."""
    mock_redis_client = MagicMock()
    mock_redis_client.setex = MagicMock()
    mock_redis_client.keys = MagicMock(return_value=[])
    mock_redis_client.delete = MagicMock()
    mock_redis_client.exists = MagicMock(return_value=False)
    return mock_redis_client


class TestUserRegistration:
    """Test user registration functionality."""

    def test_register_user_success(self, client):
        """Test successful user registration."""
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123"
        }

        response = client.post("/api/auth/register", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert body["message"] == "User registered successfully"
        assert "id" in body

        # Verify user was created in database
        with client.application.app_context():
            user = User.query.filter_by(username="newuser").first()
            assert user is not None
            assert user.email == "newuser@example.com"
            assert user.password_hash is not None

    def test_register_user_missing_fields(self, client):
        """Test registration with missing required fields."""
        # Missing password
        response = client.post("/api/auth/register", json={
            "username": "user1",
            "email": "user1@example.com"
        })
        # Connexion may return validation error or our custom error
        assert response.status_code == 400
        body = response.json()
        # Check for either Connexion format or our custom format
        error_msg = body.get("error", "") or body.get("detail", "") or str(body)
        assert "required" in error_msg.lower() or "password" in error_msg.lower()

        # Missing username
        response = client.post("/api/auth/register", json={
            "email": "user2@example.com",
            "password": "password123"
        })
        assert response.status_code == 400

        # Missing email
        response = client.post("/api/auth/register", json={
            "username": "user3",
            "password": "password123"
        })
        assert response.status_code == 400

    def test_register_user_short_password(self, client):
        """Test registration with password too short."""
        payload = {
            "username": "user4",
            "email": "user4@example.com",
            "password": "short"  # Less than 6 characters
        }

        response = client.post("/api/auth/register", json=payload)

        assert response.status_code == 400
        body = response.json()
        error_msg = body.get("error", "") or body.get("detail", "") or str(body)
        assert "password" in error_msg.lower()

    def test_register_user_duplicate_username(self, client, test_user):
        """Test registration with duplicate username."""
        payload = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "password123"
        }

        response = client.post("/api/auth/register", json=payload)

        assert response.status_code == 409
        assert "already exists" in response.json().get("error", "").lower()

    def test_register_user_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        payload = {
            "username": "differentuser",
            "email": test_user.email,
            "password": "password123"
        }

        response = client.post("/api/auth/register", json=payload)

        assert response.status_code == 409
        assert "already exists" in response.json().get("error", "").lower()


class TestUserLogin:
    """Test user login functionality."""

    @patch('app.services.auth_service.get_redis_client')
    def test_login_success(self, mock_get_redis, client, test_user, mock_redis):
        """Test successful user login."""
        mock_get_redis.return_value = mock_redis

        payload = {
            "username": test_user.username,
            "password": "testpassword123"
        }

        response = client.post("/api/auth/login", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert "expires_in" in body
        assert "user" in body
        assert body["user"]["id"] == test_user.id
        assert body["user"]["username"] == test_user.username

        # Verify tokens are valid
        access_token = body["access_token"]
        decoded = decode_token(access_token)
        assert decoded is not None
        assert decoded["user_id"] == test_user.id
        assert decoded["username"] == test_user.username
        assert decoded["type"] == "access"

    def test_login_invalid_username(self, client):
        """Test login with non-existent username."""
        payload = {
            "username": "nonexistent",
            "password": "password123"
        }

        response = client.post("/api/auth/login", json=payload)

        assert response.status_code == 401
        assert "invalid" in response.json().get("error", "").lower()

    def test_login_invalid_password(self, client, test_user):
        """Test login with incorrect password."""
        payload = {
            "username": test_user.username,
            "password": "wrongpassword"
        }

        response = client.post("/api/auth/login", json=payload)

        assert response.status_code == 401
        assert "invalid" in response.json().get("error", "").lower()

    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        # Missing password
        response = client.post("/api/auth/login", json={"username": "testuser"})
        assert response.status_code == 400

        # Missing username
        response = client.post("/api/auth/login", json={"password": "password123"})
        assert response.status_code == 400

        # Empty body
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 400


class TestTokenRefresh:
    """Test token refresh functionality."""

    @patch('app.services.auth_service.get_redis_client')
    def test_refresh_token_success(self, mock_get_redis, client, test_user, mock_redis):
        """Test successful token refresh."""
        mock_get_redis.return_value = mock_redis

        # First login to get refresh token
        login_response = client.post("/api/auth/login", json={
            "username": test_user.username,
            "password": "testpassword123"
        })
        refresh_token = login_response.json()["refresh_token"]

        # Refresh access token
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert "expires_in" in body

        # Verify new token is valid
        new_token = body["access_token"]
        decoded = decode_token(new_token)
        assert decoded is not None
        assert decoded["user_id"] == test_user.id

    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token."""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid.token.here"
        })

        assert response.status_code == 401
        assert "invalid" in response.json().get("error", "").lower()

    def test_refresh_token_missing(self, client):
        """Test refresh without token."""
        response = client.post("/api/auth/refresh", json={})

        assert response.status_code == 400
        body = response.json()
        error_msg = body.get("error", "") or body.get("detail", "") or str(body)
        assert "refresh_token" in error_msg.lower()


class TestLogout:
    """Test user logout functionality."""

    @patch('app.services.auth_service.get_redis_client')
    def test_logout_success(self, mock_get_redis, client, test_user, mock_redis):
        """Test successful logout."""
        mock_get_redis.return_value = mock_redis
        # Mock for login (session storage)
        mock_redis.setex = MagicMock()
        # Mock for logout (session lookup and deletion)
        mock_redis.keys.return_value = [f"session:{test_user.id}:abc123"]
        mock_redis.exists.return_value = False  # Not blacklisted

        # Login first
        login_response = client.post("/api/auth/login", json={
            "username": test_user.username,
            "password": "testpassword123"
        })
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        # Update mock for logout - need to return session keys for verify_session
        mock_redis.keys.return_value = [f"session:{test_user.id}:anyprefix"]

        # Logout
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/api/auth/logout", headers=headers)

        assert response.status_code == 200
        assert "successfully" in response.json().get("message", "").lower()

    def test_logout_without_token(self, client):
        """Test logout without authentication token."""
        response = client.post("/api/auth/logout")

        assert response.status_code == 401

    def test_logout_invalid_token(self, client):
        """Test logout with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.post("/api/auth/logout", headers=headers)

        assert response.status_code == 401


class TestGetCurrentUser:
    """Test get current user information."""

    @patch('app.services.auth_service.get_redis_client')
    def test_get_current_user_success(self, mock_get_redis, client, test_user, mock_redis):
        """Test successfully getting current user info."""
        mock_get_redis.return_value = mock_redis
        # Mock for login
        mock_redis.setex = MagicMock()
        # Mock for session verification
        mock_redis.keys.return_value = [f"session:{test_user.id}:anyprefix"]
        mock_redis.exists.return_value = False  # Not blacklisted

        # Login first
        login_response = client.post("/api/auth/login", json={
            "username": test_user.username,
            "password": "testpassword123"
        })
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        # Get current user (verify_session will check Redis)
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == 200
        body = response.json()
        assert body["user_id"] == test_user.id
        assert body["username"] == test_user.username

    def test_get_current_user_without_token(self, client):
        """Test getting current user without token."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == 401


class TestAuthService:
    """Test AuthService utility methods."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)

        # Hashes should be different (salt)
        assert hash1 != hash2
        # But both should verify correctly
        assert AuthService.verify_password(password, hash1)
        assert AuthService.verify_password(password, hash2)

    def test_verify_password(self):
        """Test password verification."""
        password = "testpassword123"
        hashed = AuthService.hash_password(password)

        # Correct password
        assert AuthService.verify_password(password, hashed) is True

        # Wrong password
        assert AuthService.verify_password("wrongpassword", hashed) is False

    def test_authenticate_user_success(self, client, test_user):
        """Test successful user authentication."""
        with client.application.app_context():
            user = AuthService.authenticate_user(test_user.username, "testpassword123")
            assert user is not None
            assert user.id == test_user.id
            assert user.username == test_user.username

    def test_authenticate_user_invalid_password(self, client, test_user):
        """Test authentication with invalid password."""
        with client.application.app_context():
            user = AuthService.authenticate_user(test_user.username, "wrongpassword")
            assert user is None

    def test_authenticate_user_nonexistent(self, client):
        """Test authentication with non-existent user."""
        with client.application.app_context():
            user = AuthService.authenticate_user("nonexistent", "password123")
            assert user is None


class TestJWTUtils:
    """Test JWT utility functions."""

    def test_generate_and_decode_token(self):
        """Test token generation and decoding."""
        user_id = 1
        username = "testuser"

        token = generate_access_token(user_id, username)
        assert token is not None

        decoded = decode_token(token)
        assert decoded is not None
        assert decoded["user_id"] == user_id
        assert decoded["username"] == username
        assert decoded["type"] == "access"

    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        decoded = decode_token("invalid.token.here")
        assert decoded is None

    def test_decode_expired_token(self):
        """Test decoding expired token."""
        # Create an expired token
        payload = {
            "user_id": 1,
            "username": "testuser",
            "type": "access",
            "iat": datetime.utcnow() - timedelta(hours=1),
            "exp": datetime.utcnow() - timedelta(minutes=1),  # Expired 1 minute ago
        }
        secret = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "dev-secret"))
        expired_token = jwt.encode(payload, secret, algorithm="HS256")

        decoded = decode_token(expired_token)
        assert decoded is None


class TestSessionManagement:
    """Test session management with Redis."""

    @patch('app.services.auth_service.get_redis_client')
    def test_session_stored_on_login(self, mock_get_redis, client, test_user, mock_redis):
        """Test that session is stored in Redis on login."""
        mock_get_redis.return_value = mock_redis

        response = client.post("/api/auth/login", json={
            "username": test_user.username,
            "password": "testpassword123"
        })

        assert response.status_code == 200
        # Verify Redis setex was called
        assert mock_redis.setex.called

    @patch('app.services.auth_service.get_redis_client')
    def test_session_removed_on_logout(self, mock_get_redis, client, test_user, mock_redis):
        """Test that session is removed from Redis on logout."""
        mock_get_redis.return_value = mock_redis
        session_key = f"session:{test_user.id}:abc123"
        mock_redis.keys.return_value = [session_key]

        # Login
        login_response = client.post("/api/auth/login", json={
            "username": test_user.username,
            "password": "testpassword123"
        })
        access_token = login_response.json()["access_token"]

        # Logout
        headers = {"Authorization": f"Bearer {access_token}"}
        client.post("/api/auth/logout", headers=headers)

        # Verify delete was called
        assert mock_redis.delete.called

    @patch('app.services.auth_service.get_redis_client')
    def test_verify_session_with_redis(self, mock_get_redis, client, test_user, mock_redis):
        """Test session verification checks Redis."""
        mock_get_redis.return_value = mock_redis
        mock_redis.exists.return_value = False  # Token not blacklisted

        # Generate token first
        token = generate_access_token(test_user.id, test_user.username)
        
        # Mock Redis to return session keys matching the pattern
        # verify_session uses pattern: session:{user_id}:*
        session_key = f"session:{test_user.id}:anyprefix"
        mock_redis.keys.return_value = [session_key]

        # Verify session
        with client.application.app_context():
            payload = AuthService.verify_session(token)
            # Note: verify_session checks if any session exists for the user
            # It doesn't need to match the exact token prefix, just that a session exists
            assert payload is not None
            assert payload["user_id"] == test_user.id

    @patch('app.services.auth_service.get_redis_client')
    def test_verify_session_not_in_redis(self, mock_get_redis, client, test_user, mock_redis):
        """Test that session not in Redis is rejected."""
        mock_get_redis.return_value = mock_redis
        mock_redis.keys.return_value = []  # No sessions found

        # Generate token
        token = generate_access_token(test_user.id, test_user.username)

        # Verify session (should fail because not in Redis)
        with client.application.app_context():
            payload = AuthService.verify_session(token)
            # Session not found in Redis, so verification should fail
            assert payload is None

    @patch('app.services.auth_service.get_redis_client')
    def test_blacklisted_token_rejected(self, mock_get_redis, client, test_user, mock_redis):
        """Test that blacklisted tokens are rejected."""
        mock_get_redis.return_value = mock_redis
        mock_redis.keys.return_value = [f"session:{test_user.id}:abc123"]

        # Generate token
        token = generate_access_token(test_user.id, test_user.username)
        
        # Mock exists to return True for blacklist check
        # verify_session checks blacklist key: blacklist:{token_prefix}
        token_prefix = token[:16]
        blacklist_key = f"blacklist:{token_prefix}"
        
        def exists_side_effect(key):
            return key == blacklist_key
        
        mock_redis.exists.side_effect = exists_side_effect

        # Verify session (should fail because token is blacklisted)
        with client.application.app_context():
            payload = AuthService.verify_session(token)
            assert payload is None

