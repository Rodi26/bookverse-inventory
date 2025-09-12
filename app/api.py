"""
API routes for BookVerse Inventory Service - Demo Version
Simplified 5-endpoint API optimized for demo showcase.
"""

import logging
import math
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .database import get_db
from .auth import AuthUser, RequireUser, get_auth_status, test_auth_connection
from .services import BookService, InventoryService, TransactionService
from .schemas import (
    BookResponse, BookCreate, BookUpdate, BookListResponse, BookListItem,
    InventoryDetailResponse, InventoryListResponse, InventoryAdjustment,
    TransactionResponse, TransactionListResponse, HealthResponse,
    PaginationMeta
)
from .config import SERVICE_NAME, SERVICE_VERSION, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter()


def create_pagination_meta(total: int, page: int, per_page: int) -> PaginationMeta:
    """Create pagination metadata"""
    pages = max(1, math.ceil(total / per_page))
    return PaginationMeta(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring and load balancers
    """
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        database_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_status = "unhealthy"
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        timestamp=datetime.utcnow(),
        database=database_status
    )


@router.get("/auth/status")
async def auth_status():
    """Get authentication service status"""
    return get_auth_status()


@router.get("/auth/test")
async def auth_test():
    """Test authentication service connectivity"""
    return await test_auth_connection()


@router.get("/auth/me")
async def get_current_user_info(user: AuthUser = RequireUser):
    """Get current authenticated user information"""
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "roles": user.roles,
        "scopes": user.scopes,
        "authenticated": True
    }


@router.get("/api/v1/books", response_model=BookListResponse)
async def list_books(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    List books with availability information and pagination
    """
    skip = (page - 1) * per_page
    
    try:
        books_data, total = BookService.get_books_with_availability(
            db=db, skip=skip, limit=per_page
        )
        
        # Convert to response format
        books = [BookListItem(**book_data) for book_data in books_data]
        
        pagination = create_pagination_meta(total, page, per_page)
        
        return BookListResponse(books=books, pagination=pagination)
    
    except Exception as e:
        logger.error(f"Error listing books: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/v1/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: UUID, db: Session = Depends(get_db)):
    """
    Get detailed book information by ID
    """
    try:
        book = BookService.get_book_by_id(db=db, book_id=book_id)
        
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return BookResponse.model_validate(book)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/v1/books", response_model=BookResponse, status_code=201)
async def create_book(
    book_data: BookCreate, 
    db: Session = Depends(get_db),
    user: AuthUser = RequireUser
):
    """
    Create a new book in the catalog
    """
    try:
        book = BookService.create_book(db=db, book_data=book_data)
        return BookResponse.model_validate(book)
    
    except Exception as e:
        logger.error(f"Error creating book: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/api/v1/books/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: UUID, 
    book_data: BookUpdate, 
    db: Session = Depends(get_db),
    user: AuthUser = RequireUser
):
    """
    Update existing book information
    """
    try:
        book = BookService.update_book(db=db, book_id=book_id, book_data=book_data)
        
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return BookResponse.model_validate(book)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/api/v1/books/{book_id}", status_code=204)
async def delete_book(
    book_id: UUID, 
    db: Session = Depends(get_db),
    user: AuthUser = RequireUser
):
    """
    Soft delete a book from the catalog
    """
    try:
        success = BookService.delete_book(db=db, book_id=book_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Book not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/v1/inventory", response_model=InventoryListResponse)
async def list_inventory(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    low_stock: bool = Query(False, description="Filter for low stock items only"),
    db: Session = Depends(get_db)
):
    """
    List inventory records with book details and pagination
    """
    skip = (page - 1) * per_page
    
    try:
        inventory_data, total = InventoryService.get_inventory_list(
            db=db, skip=skip, limit=per_page, low_stock_only=low_stock
        )
        
        # Convert to response format
        inventory = [InventoryDetailResponse(**item) for item in inventory_data]
        
        pagination = create_pagination_meta(total, page, per_page)
        
        return InventoryListResponse(inventory=inventory, pagination=pagination)
    
    except Exception as e:
        logger.error(f"Error listing inventory: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/v1/inventory/{book_id}", response_model=InventoryDetailResponse)
async def get_book_inventory(book_id: UUID, db: Session = Depends(get_db)):
    """
    Get inventory information for a specific book
    """
    try:
        inventory_data = InventoryService.get_inventory_by_book_id(db=db, book_id=book_id)
        
        if not inventory_data:
            raise HTTPException(status_code=404, detail="Inventory record not found")
        
        return InventoryDetailResponse(**inventory_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting inventory for book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/v1/inventory/adjust", response_model=TransactionResponse)
async def adjust_inventory(
    book_id: UUID = Query(..., description="Book ID to adjust"),
    adjustment: InventoryAdjustment = ...,
    db: Session = Depends(get_db),
    user: AuthUser = RequireUser
):
    """
    Adjust inventory levels for a book (for demo stock management)
    """
    try:
        transaction = InventoryService.adjust_inventory(
            db=db, book_id=book_id, adjustment=adjustment
        )
        
        if not transaction:
            raise HTTPException(
                status_code=400, 
                detail="Invalid adjustment - would result in negative inventory"
            )
        
        return TransactionResponse.model_validate(transaction)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adjusting inventory for book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/v1/transactions", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    book_id: Optional[UUID] = Query(None, description="Filter by book ID"),
    db: Session = Depends(get_db)
):
    """
    List stock transactions for demo audit trail
    """
    skip = (page - 1) * per_page
    
    try:
        transactions, total = TransactionService.get_transactions(
            db=db, book_id=book_id, skip=skip, limit=per_page
        )
        
        # Convert to response format
        transaction_list = [TransactionResponse.model_validate(t) for t in transactions]
        
        pagination = create_pagination_meta(total, page, per_page)
        
        return TransactionListResponse(transactions=transaction_list, pagination=pagination)
    
    except Exception as e:
        logger.error(f"Error listing transactions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
