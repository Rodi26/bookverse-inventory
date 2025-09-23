



import math
from typing import Any, List, Optional, TypeVar, Generic

from fastapi import Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Query as SQLQuery

from .responses import PaginatedResponse, PaginationMeta

T = TypeVar('T')


class PaginationParams(BaseModel):
    
    
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-based)"
    )
    
    per_page: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page (max 100)"
    )
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        return self.per_page


def create_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
) -> PaginationParams:
    
        
    return PaginationParams(page=page, per_page=per_page)


def create_pagination_meta(
    total: int,
    page: int,
    per_page: int
) -> PaginationMeta:
    
        
    pages = max(1, math.ceil(total / per_page))
    
    return PaginationMeta(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )


def paginate_query(
    query: SQLQuery,
    pagination: PaginationParams
) -> tuple[List[Any], int]:
    
        
    total = query.count()
    
    items = query.offset(pagination.offset).limit(pagination.limit).all()
    
    return items, total


def paginate(
    items: List[T],
    total: int,
    pagination: PaginationParams,
    request_id: Optional[str] = None
) -> PaginatedResponse[T]:
    
        
    pagination_meta = create_pagination_meta(
        total=total,
        page=pagination.page,
        per_page=pagination.per_page
    )
    
    return PaginatedResponse(
        items=items,
        pagination=pagination_meta,
        request_id=request_id
    )


class PaginatedList(Generic[T]):
    
    
    def __init__(
        self,
        items: List[T],
        total: int,
        page: int,
        per_page: int
    ):
        
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page
        self.pages = max(1, math.ceil(total / per_page))
    
    @property
    def has_next(self) -> bool:
        return self.page < self.pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1
    
    @property
    def next_page(self) -> Optional[int]:
        return self.page + 1 if self.has_next else None
    
    @property
    def prev_page(self) -> Optional[int]:
        return self.page - 1 if self.has_prev else None
    
    @property
    def start_index(self) -> int:
        return (self.page - 1) * self.per_page + 1
    
    @property
    def end_index(self) -> int:
        return min(self.page * self.per_page, self.total)
    
    def to_response(self, request_id: Optional[str] = None) -> PaginatedResponse[T]:
        
            
        return PaginatedResponse(
            items=self.items,
            pagination=PaginationMeta(
                total=self.total,
                page=self.page,
                per_page=self.per_page,
                pages=self.pages,
                has_next=self.has_next,
                has_prev=self.has_prev
            ),
            request_id=request_id
        )
    
    def __len__(self) -> int:
        return len(self.items)
    
    def __iter__(self):
        return iter(self.items)
    
    def __getitem__(self, index: int) -> T:
        return self.items[index]


