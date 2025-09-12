"""
Tests for JWT Authentication Module

Comprehensive test suite for validating OIDC/JWT authentication functionality
including token validation, user claims, and authorization checks.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.auth import (
    AuthUser, validate_jwt_token, get_current_user, require_authentication,
    get_oidc_configuration, get_jwks, get_public_key, get_auth_status,
    test_auth_connection
)


class TestAuthUser:
    """Test AuthUser class functionality"""
    
    def test_auth_user_creation(self):
        """Test creating AuthUser from token claims"""
        claims = {
            "sub": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "scope": "openid profile email bookverse:api",
            "roles": ["user", "admin"]
        }
        
        user = AuthUser(claims)
        
        assert user.user_id == "user123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.roles == ["user", "admin"]
        assert user.scopes == ["openid", "profile", "email", "bookverse:api"]
    
    def test_auth_user_minimal_claims(self):
        """Test AuthUser with minimal required claims"""
        claims = {
            "sub": "user123",
            "email": "test@example.com"
        }
        
        user = AuthUser(claims)
        
        assert user.user_id == "user123"
        assert user.email == "test@example.com"
        assert user.name == "test@example.com"  # Falls back to email
        assert user.roles == []
        assert user.scopes == []
    
    def test_has_scope(self):
        """Test scope checking functionality"""
        claims = {
            "sub": "user123",
            "scope": "openid profile bookverse:api admin:write"
        }
        
        user = AuthUser(claims)
        
        assert user.has_scope("bookverse:api")
        assert user.has_scope("admin:write")
        assert not user.has_scope("admin:delete")
    
    def test_has_role(self):
        """Test role checking functionality"""
        claims = {
            "sub": "user123",
            "roles": ["user", "moderator"]
        }
        
        user = AuthUser(claims)
        
        assert user.has_role("user")
        assert user.has_role("moderator")
        assert not user.has_role("admin")


class TestOIDCConfiguration:
    """Test OIDC configuration fetching"""
    
    @patch('app.auth.requests.get')
    def test_get_oidc_configuration_success(self, mock_get):
        """Test successful OIDC configuration retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "issuer": "https://auth.example.com",
            "jwks_uri": "https://auth.example.com/.well-known/jwks.json"
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Reset global config cache
        import app.auth
        app.auth._oidc_config = None
        
        config = app.auth.get_oidc_configuration()
        
        assert config["issuer"] == "https://auth.example.com"
        assert "jwks_uri" in config
        mock_get.assert_called_once()
    
    @patch('app.auth.requests.get')
    def test_get_oidc_configuration_failure(self, mock_get):
        """Test OIDC configuration retrieval failure"""
        mock_get.side_effect = Exception("Network error")
        
        # Reset global config cache
        import app.auth
        app.auth._oidc_config = None
        
        with pytest.raises(HTTPException) as exc_info:
            app.auth.get_oidc_configuration()
        
        assert exc_info.value.status_code == 503
        assert "Authentication service unavailable" in str(exc_info.value.detail)


class TestJWKS:
    """Test JWKS (JSON Web Key Set) functionality"""
    
    @patch('app.auth.get_oidc_configuration')
    @patch('app.auth.requests.get')
    def test_get_jwks_success(self, mock_get, mock_oidc_config):
        """Test successful JWKS retrieval"""
        mock_oidc_config.return_value = {
            "jwks_uri": "https://auth.example.com/.well-known/jwks.json"
        }
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "keys": [
                {
                    "kid": "key1",
                    "kty": "RSA",
                    "n": "example_modulus",
                    "e": "AQAB"
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Reset global JWKS cache
        import app.auth
        app.auth._jwks = None
        app.auth._jwks_last_updated = None
        
        jwks = app.auth.get_jwks()
        
        assert "keys" in jwks
        assert len(jwks["keys"]) == 1
        assert jwks["keys"][0]["kid"] == "key1"
    
    def test_get_public_key_success(self):
        """Test successful public key extraction"""
        token_header = {"kid": "key1"}
        jwks = {
            "keys": [
                {"kid": "key1", "kty": "RSA"},
                {"kid": "key2", "kty": "RSA"}
            ]
        }
        
        key = get_public_key(token_header, jwks)
        
        assert key["kid"] == "key1"
        assert key["kty"] == "RSA"
    
    def test_get_public_key_missing_kid(self):
        """Test public key extraction with missing kid"""
        token_header = {}
        jwks = {"keys": []}
        
        with pytest.raises(ValueError, match="Token header missing 'kid' field"):
            get_public_key(token_header, jwks)
    
    def test_get_public_key_no_matching_key(self):
        """Test public key extraction with no matching key"""
        token_header = {"kid": "nonexistent"}
        jwks = {"keys": [{"kid": "key1"}]}
        
        with pytest.raises(ValueError, match="No matching key found"):
            get_public_key(token_header, jwks)


class TestTokenValidation:
    """Test JWT token validation"""
    
    @patch('app.auth.get_jwks')
    @patch('app.auth.jwt.get_unverified_header')
    @patch('app.auth.jwt.decode')
    def test_validate_jwt_token_success(self, mock_decode, mock_header, mock_jwks):
        """Test successful JWT token validation"""
        mock_header.return_value = {"kid": "key1"}
        mock_jwks.return_value = {
            "keys": [{"kid": "key1", "kty": "RSA"}]
        }
        mock_decode.return_value = {
            "sub": "user123",
            "email": "test@example.com",
            "scope": "openid profile bookverse:api"
        }
        
        user = validate_jwt_token("valid.jwt.token")
        
        assert isinstance(user, AuthUser)
        assert user.user_id == "user123"
        assert user.email == "test@example.com"
        assert user.has_scope("bookverse:api")
    
    @patch('app.auth.get_jwks')
    @patch('app.auth.jwt.get_unverified_header')
    @patch('app.auth.jwt.decode')
    def test_validate_jwt_token_missing_sub(self, mock_decode, mock_header, mock_jwks):
        """Test JWT validation with missing sub claim"""
        mock_header.return_value = {"kid": "key1"}
        mock_jwks.return_value = {"keys": [{"kid": "key1"}]}
        mock_decode.return_value = {"email": "test@example.com"}
        
        with pytest.raises(HTTPException) as exc_info:
            validate_jwt_token("invalid.jwt.token")
        
        assert exc_info.value.status_code == 401
    
    @patch('app.auth.get_jwks')
    @patch('app.auth.jwt.get_unverified_header')
    @patch('app.auth.jwt.decode')
    def test_validate_jwt_token_missing_scope(self, mock_decode, mock_header, mock_jwks):
        """Test JWT validation with missing required scope"""
        mock_header.return_value = {"kid": "key1"}
        mock_jwks.return_value = {"keys": [{"kid": "key1"}]}
        mock_decode.return_value = {
            "sub": "user123",
            "scope": "openid profile"  # Missing bookverse:api
        }
        
        with pytest.raises(HTTPException) as exc_info:
            validate_jwt_token("invalid.jwt.token")
        
        assert exc_info.value.status_code == 401
    
    @patch('app.auth.get_jwks')
    @patch('app.auth.jwt.get_unverified_header')
    @patch('app.auth.jwt.decode')
    def test_validate_jwt_token_jwt_error(self, mock_decode, mock_header, mock_jwks):
        """Test JWT validation with JWT decode error"""
        mock_header.return_value = {"kid": "key1"}
        mock_jwks.return_value = {"keys": [{"kid": "key1"}]}
        mock_decode.side_effect = jwt.JWTError("Invalid token")
        
        with pytest.raises(HTTPException) as exc_info:
            validate_jwt_token("invalid.jwt.token")
        
        assert exc_info.value.status_code == 401
        assert "Invalid authentication token" in str(exc_info.value.detail)


class TestAuthenticationDependencies:
    """Test FastAPI authentication dependencies"""
    
    @patch('app.auth.AUTH_ENABLED', False)
    def test_get_current_user_auth_disabled(self):
        """Test get_current_user when authentication is disabled"""
        user = get_current_user(None)
        
        assert isinstance(user, AuthUser)
        assert user.user_id == "dev-user"
        assert user.email == "dev@bookverse.com"
        assert user.has_scope("bookverse:api")
    
    @patch('app.auth.AUTH_ENABLED', True)
    @patch('app.auth.DEVELOPMENT_MODE', True)
    def test_get_current_user_dev_mode_no_credentials(self):
        """Test get_current_user in development mode without credentials"""
        user = get_current_user(None)
        
        assert user is None
    
    @patch('app.auth.AUTH_ENABLED', True)
    @patch('app.auth.DEVELOPMENT_MODE', False)
    def test_get_current_user_production_no_credentials(self):
        """Test get_current_user in production mode without credentials"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(None)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in str(exc_info.value.detail)
    
    @patch('app.auth.AUTH_ENABLED', True)
    @patch('app.auth.validate_jwt_token')
    def test_get_current_user_with_valid_token(self, mock_validate):
        """Test get_current_user with valid token"""
        mock_user = AuthUser({"sub": "user123", "email": "test@example.com"})
        mock_validate.return_value = mock_user
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.jwt.token"
        )
        
        user = get_current_user(credentials)
        
        assert user == mock_user
        mock_validate.assert_called_once_with("valid.jwt.token")
    
    def test_require_authentication_with_user(self):
        """Test require_authentication with authenticated user"""
        mock_user = AuthUser({"sub": "user123"})
        
        user = require_authentication(mock_user)
        
        assert user == mock_user
    
    def test_require_authentication_without_user(self):
        """Test require_authentication without user"""
        with pytest.raises(HTTPException) as exc_info:
            require_authentication(None)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in str(exc_info.value.detail)


class TestAuthStatus:
    """Test authentication status and health endpoints"""
    
    @patch('app.auth.AUTH_ENABLED', True)
    @patch('app.auth.DEVELOPMENT_MODE', False)
    def test_get_auth_status(self):
        """Test get_auth_status function"""
        status = get_auth_status()
        
        assert status["auth_enabled"] is True
        assert status["development_mode"] is False
        assert "oidc_authority" in status
        assert "audience" in status
    
    @patch('app.auth.get_oidc_configuration')
    @patch('app.auth.get_jwks')
    def test_test_auth_connection_success(self, mock_jwks, mock_config):
        """Test successful auth connection test"""
        mock_config.return_value = {"issuer": "https://auth.example.com"}
        mock_jwks.return_value = {"keys": [{"kid": "key1"}, {"kid": "key2"}]}
        
        result = test_auth_connection()
        
        assert result["status"] == "healthy"
        assert result["oidc_config_loaded"] is True
        assert result["jwks_loaded"] is True
        assert result["keys_count"] == 2
    
    @patch('app.auth.get_oidc_configuration')
    def test_test_auth_connection_failure(self, mock_config):
        """Test failed auth connection test"""
        mock_config.side_effect = Exception("Connection failed")
        
        result = test_auth_connection()
        
        assert result["status"] == "unhealthy"
        assert "error" in result


# Integration tests
class TestAuthIntegration:
    """Integration tests for authentication flow"""
    
    @pytest.fixture
    def mock_jwt_token(self):
        """Create a mock JWT token for testing"""
        return "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6InRlc3Qta2V5In0.eyJzdWIiOiJ1c2VyMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwibmFtZSI6IlRlc3QgVXNlciIsInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwgYm9va3ZlcnNlOmFwaSIsInJvbGVzIjpbInVzZXIiXSwiaWF0IjoxNjQwOTk1MjAwLCJleHAiOjE2NDA5OTg4MDB9.signature"
    
    @patch('app.auth.AUTH_ENABLED', True)
    @patch('app.auth.validate_jwt_token')
    def test_full_authentication_flow(self, mock_validate, mock_jwt_token):
        """Test complete authentication flow from token to user"""
        expected_user = AuthUser({
            "sub": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "scope": "openid profile email bookverse:api",
            "roles": ["user"]
        })
        mock_validate.return_value = expected_user
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=mock_jwt_token
        )
        
        # Test get_current_user
        user = get_current_user(credentials)
        assert user.user_id == "user123"
        assert user.has_scope("bookverse:api")
        
        # Test require_authentication
        auth_user = require_authentication(user)
        assert auth_user == user
        
        mock_validate.assert_called_with(mock_jwt_token)
    
    def test_unauthorized_access_flow(self):
        """Test handling of unauthorized access attempts"""
        # Test with no credentials
        with pytest.raises(HTTPException) as exc_info:
            require_authentication(None)
        assert exc_info.value.status_code == 401
        
        # Test with invalid user (None)
        with pytest.raises(HTTPException) as exc_info:
            require_authentication(None)
        assert exc_info.value.status_code == 401
