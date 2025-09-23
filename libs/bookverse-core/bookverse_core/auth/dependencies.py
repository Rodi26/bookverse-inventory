

import logging
from typing import Optional

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt_auth import AuthUser, validate_jwt_token, create_mock_user, is_auth_enabled, is_development_mode

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthUser]:
    """
    Get the current authenticated user if available.
    
    This function is designed for OPTIONAL authentication patterns.
    Returns None when no credentials are provided, allowing endpoints
    to handle both authenticated and unauthenticated requests.
    
    For REQUIRED authentication, use require_authentication() instead.
    
    Returns:
        Optional[AuthUser]: The authenticated user or None if not authenticated
    """
    if not is_auth_enabled():
        logger.debug("🔓 Authentication disabled - returning mock user")
        return create_mock_user()
    
    if not credentials:
        # For optional authentication, always return None when no credentials provided
        # This allows endpoints to handle both authenticated and unauthenticated users
        logger.debug("🔓 No credentials provided - returning None for optional auth")
        return None
    
    try:
        return await validate_jwt_token(credentials.credentials)
    except HTTPException:
        # For optional authentication, invalid tokens should also return None
        # rather than raising exceptions. This allows graceful degradation.
        logger.debug("⚠️ Invalid token provided - returning None for optional auth")
        return None


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
    
    scope_checker.__name__ = f"require_scope_{scope.replace(':', '_').replace('-', '_')}"
    return scope_checker


def require_role(role: str):
    
        
    async def role_checker(user: AuthUser = Depends(require_authentication)) -> AuthUser:
        if not user.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {role}"
            )
        return user
    
    role_checker.__name__ = f"require_role_{role}"
    return role_checker


def require_any_scope(*scopes: str):
    
        
    async def scope_checker(user: AuthUser = Depends(require_authentication)) -> AuthUser:
        if not user.has_any_scope(list(scopes)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required one of scopes: {', '.join(scopes)}"
            )
        return user
    
    scope_checker.__name__ = f"require_any_scope_{'_'.join(s.replace(':', '_').replace('-', '_') for s in scopes)}"
    return scope_checker


def require_any_role(*roles: str):
    
        
    async def role_checker(user: AuthUser = Depends(require_authentication)) -> AuthUser:
        if not user.has_any_role(list(roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required one of roles: {', '.join(roles)}"
            )
        return user
    
    role_checker.__name__ = f"require_any_role_{'_'.join(roles)}"
    return role_checker


RequireAuth = Depends(require_authentication)
RequireUser = Depends(get_current_user)
RequireApiScope = Depends(require_scope("bookverse:api"))
RequireAdminRole = Depends(require_role("admin"))
RequireUserRole = Depends(require_role("user"))
