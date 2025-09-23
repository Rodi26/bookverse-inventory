

import pytest
from bookverse_core.auth import AuthUser


class TestAuthUser:

    def test_auth_user_creation(self):
        token_claims = {
            "sub": "test-123",
            "email": "test@example.com",
            "name": "Test User",
            "roles": ["user", "admin"],
            "scope": "read write"
        }

        user = AuthUser(token_claims)

        assert user.user_id == "test-123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.roles == ["user", "admin"]
        assert user.scopes == ["read", "write"]

    def test_auth_user_has_role(self):
        token_claims = {
            "sub": "test-123",
            "email": "test@example.com",
            "name": "Test User",
            "roles": ["user", "admin"],
            "scopes": ["read"]
        }

        user = AuthUser(token_claims)

        assert user.has_role("user") is True
        assert user.has_role("admin") is True
        assert user.has_role("superuser") is False

    def test_auth_user_has_scope(self):
        token_claims = {
            "sub": "test-123",
            "email": "test@example.com",
            "name": "Test User",
            "roles": ["user"],
            "scope": "read write"
        }

        user = AuthUser(token_claims)

        assert user.has_scope("read") is True
        assert user.has_scope("write") is True
        assert user.has_scope("delete") is False


class TestJWTValidation:

    def test_validate_jwt_token_development_mode(self):
        from bookverse_core.auth.jwt_auth import is_development_mode, create_mock_user

        if is_development_mode():
            mock_user = create_mock_user()
            assert isinstance(mock_user, AuthUser)
            assert mock_user.user_id == "dev-user"
            assert mock_user.email == "dev@bookverse.com"
            assert "user" in mock_user.roles
        else:
            pytest.skip("Not in development mode")
