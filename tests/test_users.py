"""Tests for user management endpoints."""
import pytest
from unittest.mock import patch

class TestUserEndpoints:
    
    @patch('app.api.v1.users._load_user_from_source')
    def test_get_user_cached(self, mock_load, client):
        """Test get_user endpoint and caching."""
        mock_load.return_value = "Cached Data"
        
        # First call
        response = client.get("/api/user/123")
        assert response.status_code == 200
        assert response.text == "Cached Data"
        
        # Verify mock called
        mock_load.assert_called_with("123")

    @patch('app.services.user_service.UserService.get_all_users')
    def test_list_users_admin_only(self, mock_get_all, client, test_user):
        """Test that list_users endpoint requires admin role."""
        from app.utils.jwt_utils import generate_access_token
        from unittest.mock import patch as mock_patch
        
        # Mock Redis for session verification
        with mock_patch('app.services.auth_service.get_redis_client') as mock_get_redis:
            mock_redis = mock_get_redis.return_value
            mock_redis.keys.return_value = [f"session:{test_user.id}:anyprefix"]
            mock_redis.exists.return_value = False
            
            # Test with regular user (should fail)
            # First, update test_user to have 'user' role
            with client.application.app_context():
                from app import db
                test_user.role = 'user'
                db.session.commit()
            
            token = generate_access_token(test_user.id, test_user.username, 'user')
            headers = {"Authorization": f"Bearer {token}"}
            
            response = client.get("/api/users", headers=headers)
            assert response.status_code == 403
            
            # Test with admin user (should succeed)
            with client.application.app_context():
                test_user.role = 'admin'
                db.session.commit()
            
            admin_token = generate_access_token(test_user.id, test_user.username, 'admin')
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            
            mock_get_all.return_value = ([{"id": 1, "username": "test", "email": "test@example.com", "role": "admin"}], 200)
            
            response = client.get("/api/users", headers=admin_headers)
            assert response.status_code == 200
            mock_get_all.assert_called_once()

    def test_list_users_requires_auth(self, client):
        """Test that list_users endpoint requires authentication."""
        response = client.get("/api/users")
        assert response.status_code == 401
