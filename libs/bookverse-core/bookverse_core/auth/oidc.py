

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

import requests
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

OIDC_AUTHORITY = os.getenv("OIDC_AUTHORITY", "https://dev-auth.bookverse.com")
JWKS_CACHE_DURATION = int(os.getenv("JWKS_CACHE_DURATION", "3600"))

_oidc_config: Optional[Dict[str, Any]] = None
_jwks: Optional[Dict[str, Any]] = None
_jwks_last_updated: Optional[float] = None


async def get_oidc_configuration() -> Dict[str, Any]:
    """
    Get OIDC configuration with graceful degradation for demo environments.
    
    In development/demo mode, returns a mock configuration when the real
    OIDC service is unavailable, allowing the demo to continue functioning.
    
    Returns:
        Dict[str, Any]: OIDC configuration or mock configuration in development mode
        
    Raises:
        HTTPException: Only in production mode when OIDC service is unavailable
    """
    global _oidc_config
    
    if _oidc_config is None:
        try:
            response = requests.get(
                f"{OIDC_AUTHORITY}/.well-known/openid_configuration", 
                timeout=10
            )
            response.raise_for_status()
            _oidc_config = response.json()
            logger.info("✅ OIDC configuration loaded successfully")
        except Exception as e:
            from .jwt_auth import is_development_mode
            if is_development_mode():
                logger.warning(f"⚠️ OIDC service unavailable in demo mode, using mock configuration: {e}")
                # Return mock OIDC configuration for demo purposes
                _oidc_config = {
                    "issuer": OIDC_AUTHORITY,
                    "authorization_endpoint": f"{OIDC_AUTHORITY}/auth",
                    "token_endpoint": f"{OIDC_AUTHORITY}/token",
                    "userinfo_endpoint": f"{OIDC_AUTHORITY}/userinfo",
                    "jwks_uri": f"{OIDC_AUTHORITY}/.well-known/jwks.json",
                    "scopes_supported": ["openid", "profile", "email", "bookverse:api"],
                    "response_types_supported": ["code", "token", "id_token"],
                    "grant_types_supported": ["authorization_code", "implicit", "refresh_token"],
                    "subject_types_supported": ["public"],
                    "id_token_signing_alg_values_supported": ["RS256"],
                    "demo_mode": True
                }
            else:
                logger.error(f"❌ Failed to fetch OIDC configuration: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service unavailable"
                )
    
    return _oidc_config


async def get_jwks() -> Dict[str, Any]:
    
    
        
    global _jwks, _jwks_last_updated
    
    current_time = datetime.now().timestamp()
    
    if (
        _jwks is None
        or _jwks_last_updated is None
        or current_time - _jwks_last_updated > JWKS_CACHE_DURATION
    ):
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


def get_public_key(token_header: Dict[str, Any], jwks: Dict[str, Any]) -> Dict[str, Any]:
    
        
        
    kid = token_header.get("kid")
    if not kid:
        raise ValueError("Token header missing 'kid' field")
    
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    
    raise ValueError(f"No matching key found for kid: {kid}")


def clear_cache() -> None:
    
    global _oidc_config, _jwks, _jwks_last_updated
    _oidc_config = None
    _jwks = None
    _jwks_last_updated = None
    logger.info("🔄 OIDC and JWKS cache cleared")
