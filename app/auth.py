

import logging
import os
from typing import Optional
from datetime import datetime

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests

from bookverse_core.auth import AuthUser, validate_jwt_token

logger = logging.getLogger(__name__)

OIDC_AUTHORITY = os.getenv("OIDC_AUTHORITY", "https://dev-auth.bookverse.com")
OIDC_AUDIENCE = os.getenv("OIDC_AUDIENCE", "bookverse:api")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"

_oidc_config = None
_jwks = None
_jwks_last_updated = None
JWKS_CACHE_DURATION = 3600

security = HTTPBearer(auto_error=False)




async def get_oidc_configuration() -> dict:
    global _oidc_config
    
    if _oidc_config is None:
        try:
            response = requests.get(f"{OIDC_AUTHORITY}/.well-known/openid_configuration", timeout=10)
            response.raise_for_status()
            _oidc_config = response.json()
            logger.info("✅ OIDC configuration loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to fetch OIDC configuration: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable"
            )
    
    return _oidc_config


async def get_jwks() -> dict:
    global _jwks, _jwks_last_updated
    
    current_time = datetime.now().timestamp()
    
    if (_jwks is None or 
        _jwks_last_updated is None or 
        current_time - _jwks_last_updated > JWKS_CACHE_DURATION):
        
        try:
            oidc_config = await get_oidc_configuration()
            jwks_uri = oidc_config.get("jwks_uri")
            
            if not jwks_uri:
                raise ValueError("No jwks_uri found in OIDC configuration")
            
            response = requests.get(jwks_uri, timeout=10)
            response.raise_for_status()
            _jwks = response.json()
            _jwks_last_updated = current_time
            logger.info("✅ JWKS refreshed successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch JWKS: {e}")
            if _jwks is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service unavailable"
                )
            logger.warning("⚠️ Using cached JWKS due to fetch failure")
    
    return _jwks


def get_public_key(token_header: dict, jwks: dict) -> str:
    kid = token_header.get("kid")
    if not kid:
        raise ValueError("Token header missing 'kid' field")
    
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    
    raise ValueError(f"No matching key found for kid: {kid}")




async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthUser]:
    
    
    logger.debug("🎯 Demo mode: Using mock user (K8s inter-service auth not in scope)")
    return AuthUser({
        "sub": "demo-user",
        "email": "demo@bookverse.com",
        "name": "Demo User",
        "scope": "openid profile email bookverse:api",
        "roles": ["user", "admin"]
    })


async def require_authentication(
    user: Optional[AuthUser] = Depends(get_current_user)
) -> AuthUser:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def require_scope(scope: str):
    async def scope_checker(user: AuthUser = Depends(require_authentication)) -> AuthUser:
        if not user.has_scope(scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {scope}"
            )
        return user
    return scope_checker


def require_role(role: str):
    async def role_checker(user: AuthUser = Depends(require_authentication)) -> AuthUser:
        if not user.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {role}"
            )
        return user
    return role_checker


RequireAuth = Depends(require_authentication)
RequireUser = Depends(get_current_user)
RequireApiScope = Depends(require_scope("bookverse:api"))


def get_auth_status() -> dict:
    return {
        "auth_enabled": AUTH_ENABLED,
        "development_mode": DEVELOPMENT_MODE,
        "oidc_authority": OIDC_AUTHORITY,
        "audience": OIDC_AUDIENCE,
        "algorithm": JWT_ALGORITHM,
        "jwks_cached": _jwks is not None,
        "config_cached": _oidc_config is not None
    }


async def test_auth_connection() -> dict:
    try:
        config = await get_oidc_configuration()
        jwks = await get_jwks()
        return {
            "status": "healthy",
            "oidc_config_loaded": bool(config),
            "jwks_loaded": bool(jwks),
            "keys_count": len(jwks.get("keys", [])) if jwks else 0
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
