


import pytest
from datetime import datetime

from bookverse_core.api import (
    BaseResponse,
    HealthResponse,
    ErrorResponse,
    create_success_response,
    create_error_response
)
from bookverse_core.api.pagination import (
    PaginationParams,
    PaginationMeta,
    paginate
)


class TestResponseModels:
    
    def test_base_response(self):
        timestamp = datetime.fromisoformat("2023-01-01T00:00:00")
        response = BaseResponse(
            timestamp=timestamp,
            request_id="test-request-123"
        )
        
        assert response.timestamp == timestamp
        assert response.request_id == "test-request-123"
    
    def test_health_response(self):
        response = HealthResponse(
            status="healthy",
            service="test-service",
            version="1.0.0",
            uptime=3600,
            checks={"database": "healthy"}
        )
        
        assert response.status == "healthy"
        assert response.service == "test-service"
        assert response.version == "1.0.0"
        assert response.uptime == 3600
        assert response.checks["database"] == "healthy"
    
    def test_error_response(self):
        response = ErrorResponse(
            error="Test error",
            error_code="test_error",
            details={"field": "value"}
        )
        
        assert response.success is False
        assert response.error == "Test error"
        assert response.error_code == "test_error"
        assert response.details["field"] == "value"
    
    def test_create_success_response(self):
        response = create_success_response(
            data={"key": "value"},
            message="Success message"
        )
        
        assert response.success is True
        assert response.message == "Success message"
        assert response.data["key"] == "value"
        assert response.timestamp is not None
    
    def test_create_error_response(self):
        response = create_error_response(
            error="Error message",
            error_code="test_error",
            details={"context": "test"}
        )
        
        assert response.success is False
        assert response.error == "Error message"
        assert response.error_code == "test_error"
        assert response.details["context"] == "test"
        assert response.timestamp is not None


class TestPagination:
    
    def test_pagination_params(self):
        params = PaginationParams(page=2, per_page=20)
        
        assert params.page == 2
        assert params.per_page == 20
        assert params.offset == 20
    
    def test_pagination_params_defaults(self):
        params = PaginationParams()
        
        assert params.page == 1
        assert params.per_page == 20
        assert params.offset == 0
    
    def test_pagination_params_validation(self):
        params = PaginationParams(page=1, per_page=1)
        assert params.page == 1
        assert params.per_page == 1
        
        with pytest.raises(ValueError):
            PaginationParams(page=0)
        
        with pytest.raises(ValueError):
            PaginationParams(per_page=0)
        
        with pytest.raises(ValueError):
            PaginationParams(per_page=101)
    
    def test_pagination_meta(self):
        meta = PaginationMeta(
            page=2,
            per_page=10,
            total=25,
            pages=3,
            has_next=True,
            has_prev=True
        )
        
        assert meta.page == 2
        assert meta.per_page == 10
        assert meta.total == 25
        assert meta.pages == 3
        assert meta.has_next is True
        assert meta.has_prev is True
    
    def test_paginate_function(self):
        all_items = [f"item-{i}" for i in range(1, 6)]
        pagination = PaginationParams(page=1, per_page=3)
        
        page_items = all_items[pagination.offset:pagination.offset + pagination.per_page]
        
        result = paginate(items=page_items, total=5, pagination=pagination)
        
        assert len(result.items) == 3
        assert result.items == ["item-1", "item-2", "item-3"]
        assert result.pagination.total == 5
        assert result.pagination.page == 1
        assert result.pagination.per_page == 3
        assert result.pagination.pages == 2
        assert result.pagination.has_next is True
        assert result.pagination.has_prev is False
    
    def test_paginate_function_edge_cases(self):
        pagination = PaginationParams(page=1, per_page=10)
        result = paginate(items=[], total=0, pagination=pagination)
        
        assert result.pagination.pages == 1
        assert result.pagination.has_prev is False
        assert result.pagination.has_next is False


class TestMiddleware:
    
    def test_error_response_serialization(self):
        response = ErrorResponse(
            error="Test error",
            error_code="test_error"
        )
        
        response_dict = response.model_dump()
        
        assert response_dict["success"] is False
        assert response_dict["error"] == "Test error"
        assert response_dict["error_code"] == "test_error"
        assert "timestamp" in response_dict

