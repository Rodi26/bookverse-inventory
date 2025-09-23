

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict

T = TypeVar('T')


class BaseResponse(BaseModel):
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(default=None)
    
    model_config = ConfigDict(from_attributes=True)


class SuccessResponse(BaseResponse, Generic[T]):
    
    success: bool = Field(default=True)
    data: T
    message: Optional[str] = Field(default=None)


class ErrorResponse(BaseResponse):
    
    success: bool = Field(default=False)
    error: str
    error_code: Optional[str] = Field(default=None)
    details: Optional[Dict[str, Any]] = Field(default=None)


class ValidationErrorResponse(ErrorResponse):
    
    error_code: str = Field(default="validation_error")
    field_errors: Optional[List[Dict[str, Any]]] = Field(default=None)


class PaginationMeta(BaseModel):
    
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")


class PaginatedResponse(BaseResponse, Generic[T]):
    
    items: List[T]
    pagination: PaginationMeta
    success: bool = Field(default=True)


class HealthResponse(BaseResponse):
    
    status: str = Field(description="Health status (healthy, unhealthy, degraded)")
    service: str = Field(description="Service name")
    version: str = Field(description="Service version")
    checks: Optional[Dict[str, Any]] = Field(default=None, description="Individual health checks")
    uptime: Optional[float] = Field(default=None, description="Service uptime in seconds")


class InfoResponse(BaseResponse):
    
    service: str = Field(description="Service name")
    version: str = Field(description="Service version")
    description: Optional[str] = Field(default=None)
    environment: Optional[str] = Field(default=None)
    api_version: Optional[str] = Field(default=None)
    build_info: Optional[Dict[str, Any]] = Field(default=None)
    features: Optional[Dict[str, bool]] = Field(default=None)


class StatusResponse(BaseResponse):
    
    status: str
    message: Optional[str] = Field(default=None)
    data: Optional[Dict[str, Any]] = Field(default=None)


class BatchResponse(BaseResponse, Generic[T]):
    
    total_processed: int
    successful: int
    failed: int
    results: List[T]
    errors: Optional[List[Dict[str, Any]]] = Field(default=None)


class AsyncOperationResponse(BaseResponse):
    
    operation_id: str = Field(default_factory=lambda: str(uuid4()))
    status: str = Field(description="Operation status (pending, running, completed, failed)")
    message: Optional[str] = Field(default=None)
    progress: Optional[float] = Field(default=None, description="Progress percentage (0-100)")
    estimated_completion: Optional[datetime] = Field(default=None)


def create_success_response(
    data: Any,
    message: Optional[str] = None,
    request_id: Optional[str] = None
) -> SuccessResponse:
    
        
    return SuccessResponse(
        data=data,
        message=message,
        request_id=request_id
    )


def create_error_response(
    error: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    
        
    return ErrorResponse(
        error=error,
        error_code=error_code,
        details=details,
        request_id=request_id
    )


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    per_page: int,
    request_id: Optional[str] = None
) -> PaginatedResponse:
    
        
    import math
    
    pages = max(1, math.ceil(total / per_page))
    
    pagination = PaginationMeta(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )
    
    return PaginatedResponse(
        items=items,
        pagination=pagination,
        request_id=request_id
    )


def create_health_response(
    status: str,
    service: str,
    version: str,
    checks: Optional[Dict[str, Any]] = None,
    uptime: Optional[float] = None
) -> HealthResponse:
    
        
    return HealthResponse(
        status=status,
        service=service,
        version=version,
        checks=checks,
        uptime=uptime
    )
