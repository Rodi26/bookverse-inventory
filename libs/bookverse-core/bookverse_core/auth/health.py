

import logging
from typing import Dict, Any

from .oidc import get_oidc_configuration, get_jwks, _oidc_config, _jwks
from .jwt_auth import is_auth_enabled, is_development_mode

logger = logging.getLogger(__name__)


def get_auth_status() -> Dict[str, Any]:
    
    return {
        "auth_enabled": is_auth_enabled(),
        "development_mode": is_development_mode(),
        "oidc_authority": "https://dev-auth.bookverse.com",
        "audience": "bookverse:api",
        "algorithm": "RS256",
        "jwks_cached": _jwks is not None,
        "config_cached": _oidc_config is not None,
        "status": "configured"
    }


async def check_auth_connection() -> Dict[str, Any]:
    
    
    if not is_auth_enabled():
        return {
            "status": "disabled",
            "message": "Authentication is disabled"
        }
    
    try:
        config = await get_oidc_configuration()
        
        jwks = await get_jwks()
        
        return {
            "status": "healthy",
            "oidc_config_loaded": bool(config),
            "jwks_loaded": bool(jwks),
            "keys_count": len(jwks.get("keys", [])) if jwks else 0,
            "message": "Authentication service is accessible"
        }
    except Exception as e:
        if is_development_mode():
            logger.warning(f"⚠️ Authentication service unavailable in demo mode: {e}")
        else:
            logger.error(f"❌ Authentication connectivity check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Authentication service unavailable (expected in demo mode)" if is_development_mode() else "Authentication service is not accessible"
        }
