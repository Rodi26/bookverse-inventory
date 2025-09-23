



import re
import uuid
from typing import Optional


def validate_email(email: str) -> bool:
    
    
        
    if not email or not isinstance(email, str):
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return bool(re.match(email_pattern, email.strip()))


def validate_uuid(uuid_string: str) -> bool:
    
    
        
    if not uuid_string or not isinstance(uuid_string, str):
        return False
    
    try:
        uuid.UUID(uuid_string.strip())
        return True
    except (ValueError, AttributeError):
        return False


def sanitize_string(
    input_string: str,
    max_length: int = 1000,
    allow_html: bool = False
) -> str:
    
    
        
        
    if not input_string:
        return ""
    
    if not isinstance(input_string, str):
        input_string = str(input_string)
    
    sanitized = input_string.strip()
    
    if len(sanitized) > max_length:
        raise ValueError(
            f"String too long: {len(sanitized)} characters. "
            f"Maximum allowed: {max_length}. "
            f"Demo tip: Consider truncating or splitting long inputs."
        )
    
    if not allow_html:
        sanitized = re.sub(r'<[^>]+>', '', sanitized)
    
    dangerous_chars = ['<script', '</script>', 'javascript:', 'onclick=']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized


def validate_service_name(name: str) -> bool:
    
    
        
    if not name or not isinstance(name, str):
        return False
    
    pattern = r'^[a-z0-9][a-z0-9-]*[a-z0-9]$'
    
    name = name.strip().lower()
    
    if len(name) < 2 or len(name) > 50:
        return False
    
    return bool(re.match(pattern, name))


def validate_version_string(version: str) -> bool:
    
    
        
    if not version or not isinstance(version, str):
        return False
    
    pattern = r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9-]+)?$'
    
    return bool(re.match(pattern, version.strip()))


def validate_port_number(port: int) -> bool:
    
    
        
    if not isinstance(port, int):
        return False
    
    return 1024 <= port <= 65535


def validate_url(url: str, require_https: bool = False) -> bool:
    
    
        
    if not url or not isinstance(url, str):
        return False
    
    if require_https:
        pattern = r'^https://[a-zA-Z0-9.-]+(?:\:[0-9]+)?(?:/.*)?$'
    else:
        pattern = r'^https?://[a-zA-Z0-9.-]+(?:\:[0-9]+)?(?:/.*)?$'
    
    return bool(re.match(pattern, url.strip()))


def create_validation_error_message(field: str, value: str, reason: str) -> str:
    
    
        
    if len(str(value)) > 50:
        display_value = str(value)[:47] + "..."
    else:
        display_value = str(value)
    
    return (
        f"Validation failed for '{field}': {reason}. "
        f"Provided value: '{display_value}'. "
        f"Demo tip: Check the field requirements and try again."
    )
