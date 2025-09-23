
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class BaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BookBase(BaseModel):
    title: str = Field(..., max_length=500, description="Book title")
    subtitle: Optional[str] = Field(None, max_length=500, description="Book subtitle")
    authors: List[str] = Field(..., min_length=1, description="List of author names")
    genres: List[str] = Field(..., min_length=1, description="List of book genres")
    description: str = Field(..., description="Book description")
    price: Decimal = Field(..., gt=0, description="Book price in USD")
    cover_image_url: str = Field(..., description="URL to book cover image")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Book rating (0-5)")


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    subtitle: Optional[str] = Field(None, max_length=500)
    authors: Optional[List[str]] = Field(None, min_length=1)
    genres: Optional[List[str]] = Field(None, min_length=1)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    cover_image_url: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=5)


class BookResponse(BookBase, BaseResponse):
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool


class BookListItem(BaseResponse):
    id: UUID
    title: str
    subtitle: Optional[str]
    authors: List[str]
    genres: List[str]
    price: Decimal
    cover_image_url: str
    rating: Optional[float] = Field(None, ge=0, le=5, description="Book rating (0-5)")
    availability: "AvailabilityInfo"


class AvailabilityInfo(BaseModel):
    quantity_available: int = Field(..., ge=0)
    in_stock: bool
    low_stock: bool


class InventoryBase(BaseModel):
    quantity_available: int = Field(..., ge=0, description="Available quantity")
    quantity_total: int = Field(..., ge=0, description="Total quantity")
    reorder_point: int = Field(..., ge=0, description="Reorder threshold")


class InventoryResponse(InventoryBase, BaseResponse):
    id: UUID
    book_id: UUID
    created_at: datetime
    updated_at: datetime


class InventoryDetailResponse(BaseResponse):
    inventory: InventoryResponse
    book: BookResponse


class InventoryAdjustment(BaseModel):
    quantity_change: int = Field(..., description="Positive or negative quantity change")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")


class TransactionResponse(BaseResponse):
    id: UUID
    book_id: UUID
    transaction_type: str
    quantity_change: int
    notes: Optional[str]
    timestamp: datetime


class PaginationMeta(BaseModel):
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, description="Items per page")
    pages: int = Field(..., ge=1, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class BookListResponse(BaseModel):
    books: List[BookListItem]
    pagination: PaginationMeta


class InventoryListResponse(BaseModel):
    inventory: List[InventoryDetailResponse]
    pagination: PaginationMeta


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    pagination: PaginationMeta


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Response timestamp")
    database: str = Field(..., description="Database status")


BookListItem.model_rebuild()
