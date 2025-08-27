"""
Pydantic schemas for BookVerse Inventory Service - Demo Version
Request/response models for API validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Base response model
class BaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Book schemas
class BookBase(BaseModel):
    title: str = Field(..., max_length=500, description="Book title")
    subtitle: Optional[str] = Field(None, max_length=500, description="Book subtitle")
    authors: List[str] = Field(..., min_length=1, description="List of author names")
    genres: List[str] = Field(..., min_length=1, description="List of book genres")
    description: str = Field(..., description="Book description")
    price: Decimal = Field(..., gt=0, description="Book price in USD")
    cover_image_url: str = Field(..., description="URL to book cover image")


class BookCreate(BookBase):
    """Schema for creating a new book"""
    pass


class BookUpdate(BaseModel):
    """Schema for updating a book (all fields optional)"""
    title: Optional[str] = Field(None, max_length=500)
    subtitle: Optional[str] = Field(None, max_length=500)
    authors: Optional[List[str]] = Field(None, min_length=1)
    genres: Optional[List[str]] = Field(None, min_length=1)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    cover_image_url: Optional[str] = None


class BookResponse(BookBase, BaseResponse):
    """Schema for book response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool


class BookListItem(BaseResponse):
    """Schema for book list items (with availability info)"""
    id: UUID
    title: str
    subtitle: Optional[str]
    authors: List[str]
    genres: List[str]
    price: Decimal
    cover_image_url: str
    availability: "AvailabilityInfo"


# Inventory schemas
class AvailabilityInfo(BaseModel):
    """Schema for book availability information"""
    quantity_available: int = Field(..., ge=0)
    in_stock: bool
    low_stock: bool


class InventoryBase(BaseModel):
    quantity_available: int = Field(..., ge=0, description="Available quantity")
    quantity_total: int = Field(..., ge=0, description="Total quantity")
    reorder_point: int = Field(..., ge=0, description="Reorder threshold")


class InventoryResponse(InventoryBase, BaseResponse):
    """Schema for inventory response"""
    id: UUID
    book_id: UUID
    created_at: datetime
    updated_at: datetime


class InventoryDetailResponse(BaseResponse):
    """Schema for detailed inventory with book info"""
    inventory: InventoryResponse
    book: BookResponse


class InventoryAdjustment(BaseModel):
    """Schema for inventory adjustment request"""
    quantity_change: int = Field(..., description="Positive or negative quantity change")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes")


# Transaction schemas
class TransactionResponse(BaseResponse):
    """Schema for stock transaction response"""
    id: UUID
    book_id: UUID
    transaction_type: str
    quantity_change: int
    notes: Optional[str]
    timestamp: datetime


# Pagination schemas
class PaginationMeta(BaseModel):
    """Schema for pagination metadata"""
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, description="Items per page")
    pages: int = Field(..., ge=1, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class BookListResponse(BaseModel):
    """Schema for paginated book list response"""
    books: List[BookListItem]
    pagination: PaginationMeta


class InventoryListResponse(BaseModel):
    """Schema for paginated inventory list response"""
    inventory: List[InventoryDetailResponse]
    pagination: PaginationMeta


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list response"""
    transactions: List[TransactionResponse]
    pagination: PaginationMeta


# Health check schema
class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Response timestamp")
    database: str = Field(..., description="Database status")


# Update forward references
BookListItem.model_rebuild()
