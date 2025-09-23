


import logging
import os
from typing import Dict, Any, List

from fastapi import HTTPException, status
from jose import jwt, JWTError

from .oidc import get_jwks, get_public_key

logger = logging.getLogger(__name__)

OIDC_AUTHORITY = os.getenv("OIDC_AUTHORITY", "https://dev-auth.bookverse.com")
OIDC_AUDIENCE = os.getenv("OIDC_AUDIENCE", "bookverse:api")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "true").lower() == "true"


class AuthUser:
    
    
    
    def __init__(self, token_claims: Dict[str, Any]):
        
        self.claims = token_claims
        self.user_id = token_claims.get("sub")
        self.email = token_claims.get("email")
        self.name = token_claims.get("name", self.email)
        self.roles = token_claims.get("roles", [])
        self.scopes = token_claims.get("scope", "").split() if token_claims.get("scope") else []
    
    def has_scope(self, scope: str) -> bool:
        
            
        return scope in self.scopes
    
    def has_role(self, role: str) -> bool:
        
            
        return role in self.roles
    
    
    def __str__(self) -> str:
        return f"AuthUser(id={self.user_id}, email={self.email})"
    
    def __repr__(self) -> str:
        return self.__str__()


async def validate_jwt_token(token: str) -> AuthUser:
    
    
        
        
    try:
        header = jwt.get_unverified_header(token)
        
        jwks = await get_jwks()
        
        public_key = get_public_key(header, jwks)
        
        claims = jwt.decode(
            token,
            public_key,
            algorithms=[JWT_ALGORITHM],
            audience=OIDC_AUDIENCE,
            issuer=OIDC_AUTHORITY
        )
        
        if not claims.get("sub"):
            raise ValueError("Token missing 'sub' claim")
        
        scopes = claims.get("scope", "").split() if claims.get("scope") else []
        if "bookverse:api" not in scopes:
            raise ValueError("Token missing required 'bookverse:api' scope")
        
        logger.debug(f"✅ Token validated for user: {claims.get('email', claims.get('sub'))}")
        return AuthUser(claims)
        
    except JWTError as e:
        logger.warning(f"⚠️ JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"❌ Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )


def create_mock_user() -> AuthUser:
    
    return AuthUser({
        "sub": "dev-user",
        "email": "dev@bookverse.com",
        "name": "Development User",
        "scope": "openid profile email bookverse:api",
        "roles": ["user", "admin"]
    })


def is_auth_enabled() -> bool:
    
    return AUTH_ENABLED


def is_development_mode() -> bool:
    
    return DEVELOPMENT_MODE
