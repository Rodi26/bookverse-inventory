



import logging
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class BookVerseHTTPException(HTTPException):
    
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        log_level: str = "warning"
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.context = context or {}
        
        log_message = f"HTTP {status_code}: {detail}"
        if error_code:
            log_message += f" (code: {error_code})"
        if context:
            log_message += f" - Context: {context}"
        
        if log_level == "error":
            logger.error(log_message)
        elif log_level == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)



def raise_validation_error(
    message: str,
    field: Optional[str] = None,
    value: Optional[Any] = None
) -> None:
    
    
        
    context = {}
    if field:
        context["field"] = field
    if value is not None:
        context["value"] = str(value)
    
    raise BookVerseHTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
        error_code="validation_error",
        context=context,
        log_level="info"
    )


def raise_not_found_error(
    resource_type: str,
    resource_id: Union[str, int],
    message: Optional[str] = None
) -> None:
    
    
        
    detail = message or f"{resource_type.title()} not found"
    
    raise BookVerseHTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail,
        error_code="not_found",
        context={
            "resource_type": resource_type,
            "resource_id": str(resource_id)
        },
        log_level="info"
    )


def raise_conflict_error(
    message: str,
    conflict_type: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    
    
        
    error_code = f"{conflict_type}_conflict" if conflict_type else "conflict"
    
    raise BookVerseHTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=message,
        error_code=error_code,
        context=context or {},
        log_level="warning"
    )


def raise_idempotency_conflict(
    idempotency_key: str,
    message: Optional[str] = None
) -> None:
    
    
        
    detail = message or "Idempotency key conflict - request hash mismatch"
    
    raise BookVerseHTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
        error_code="idempotency_conflict",
        context={"idempotency_key": idempotency_key},
        log_level="warning"
    )


def raise_insufficient_stock_error(
    book_id: str,
    requested: int,
    available: int
) -> None:
    
    
        
    raise BookVerseHTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Insufficient stock for book {book_id}",
        error_code="insufficient_stock",
        context={
            "book_id": book_id,
            "requested": requested,
            "available": available
        },
        log_level="info"
    )



def raise_upstream_error(
    service_name: str,
    error: Exception,
    message: Optional[str] = None
) -> None:
    
    
        
    detail = message or f"Upstream service error: {service_name}"
    
    logger.error(
        f"Upstream service '{service_name}' error: {error}",
        exc_info=True
    )
    
    raise BookVerseHTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=detail,
        error_code="upstream_error",
        context={
            "service": service_name,
            "error_type": type(error).__name__
        },
        log_level="error"
    )


def raise_internal_error(
    message: str,
    error: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    
    
        
    if error:
        logger.error(f"Internal server error: {message} - {error}", exc_info=True)
    else:
        logger.error(f"Internal server error: {message}")
    
    raise BookVerseHTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
        error_code="internal_error",
        context=context or {},
        log_level="error"
    )



def handle_service_exception(
    error: Exception,
    service_name: str = "unknown",
    operation: str = "operation"
) -> None:
    
    
    
        
    if isinstance(error, ValueError):
        detail = str(error)
        
        if detail.startswith("idempotency_conflict"):
            raise_conflict_error(detail, "idempotency")
        elif detail.startswith("insufficient_stock"):
            raise_conflict_error(detail, "stock")
        elif "not found" in detail.lower():
            parts = detail.split()
            resource_id = parts[-1] if parts else "unknown"
            raise_not_found_error("resource", resource_id, detail)
        else:
            raise_validation_error(detail)
    
    elif isinstance(error, FileNotFoundError):
        raise_not_found_error("file", str(error.filename or "unknown"))
    
    elif isinstance(error, PermissionError):
        raise BookVerseHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
            error_code="permission_denied",
            context={"operation": operation}
        )
    
    elif isinstance(error, ConnectionError):
        raise_upstream_error(service_name, error)
    
    else:
        raise_internal_error(
            f"Unexpected error in {operation}",
            error,
            {"service": service_name, "operation": operation}
        )


def create_error_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    
    
        
    context = {}
    
    if request_id:
        context["request_id"] = request_id
    if user_id:
        context["user_id"] = user_id
    
    context.update(kwargs)
    return context

