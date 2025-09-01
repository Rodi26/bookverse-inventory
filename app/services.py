"""
Business logic services for BookVerse Inventory Service - Demo Version
Simplified service layer focusing on core demo functionality.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import Book, InventoryRecord, StockTransaction
from .schemas import BookCreate, BookUpdate, InventoryAdjustment
from .config import LOW_STOCK_THRESHOLD

logger = logging.getLogger(__name__)


class BookService:
    """Service for book catalog operations"""
    
    @staticmethod
    def get_books_with_availability(
        db: Session, 
        skip: int = 0, 
        limit: int = 20,
        include_inactive: bool = False
    ) -> Tuple[List[dict], int]:
        """Get books with availability information"""
        
        # Build query
        query = db.query(Book)
        if not include_inactive:
            query = query.filter(Book.is_active == True)
        
        # Get total count
        total = query.count()
        
        # Get books with pagination
        books = query.offset(skip).limit(limit).all()

        # Preload inventory for this page in a single query (avoid N+1)
        book_ids = [book.id for book in books]
        inventory_by_book_id = {}
        if book_ids:
            inventory_records = db.query(InventoryRecord).filter(
                InventoryRecord.book_id.in_(book_ids)
            ).all()
            inventory_by_book_id = {inv.book_id: inv for inv in inventory_records}

        # Enrich with availability info
        books_with_availability: List[dict] = []
        for book in books:
            inventory = inventory_by_book_id.get(book.id)

            if inventory:
                availability = {
                    "quantity_available": inventory.quantity_available,
                    "in_stock": inventory.quantity_available > 0,
                    "low_stock": inventory.quantity_available <= inventory.reorder_point
                }
            else:
                availability = {
                    "quantity_available": 0,
                    "in_stock": False,
                    "low_stock": True
                }

            book_dict = {
                "id": book.id,
                "title": book.title,
                "subtitle": book.subtitle,
                "authors": book.authors,
                "genres": book.genres,
                "price": book.price,
                "cover_image_url": book.cover_image_url,
                "availability": availability
            }
            books_with_availability.append(book_dict)

        return books_with_availability, total
    
    @staticmethod
    def get_book_by_id(db: Session, book_id: UUID) -> Optional[Book]:
        """Get book by ID"""
        return db.query(Book).filter(
            and_(Book.id == str(book_id), Book.is_active == True)
        ).first()
    
    @staticmethod
    def create_book(db: Session, book_data: BookCreate) -> Book:
        """Create new book"""
        book_dict = book_data.model_dump()
        book_dict['id'] = str(uuid4())  # Add UUID as string
        book = Book(**book_dict)

        # Create book and initial inventory atomically
        with db.begin():
            db.add(book)
            inventory = InventoryRecord(
                id=str(uuid4()),
                book_id=book.id,
                quantity_available=0,
                quantity_total=0,
                reorder_point=LOW_STOCK_THRESHOLD
            )
            db.add(inventory)

        db.refresh(book)

        logger.info(f"Created new book: {book.title} (ID: {book.id})")
        return book
    
    @staticmethod
    def update_book(db: Session, book_id: UUID, book_data: BookUpdate) -> Optional[Book]:
        """Update existing book"""
        book = BookService.get_book_by_id(db, book_id)
        if not book:
            return None
        
        # Update only provided fields
        update_data = book_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(book, field, value)
        
        book.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(book)
        
        logger.info(f"Updated book: {book.title} (ID: {book.id})")
        return book
    
    @staticmethod
    def delete_book(db: Session, book_id: UUID) -> bool:
        """Soft delete book"""
        book = BookService.get_book_by_id(db, book_id)
        if not book:
            return False
        
        book.is_active = False
        book.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Deleted book: {book.title} (ID: {book.id})")
        return True


class InventoryService:
    """Service for inventory management operations"""
    
    @staticmethod
    def get_inventory_list(
        db: Session, 
        skip: int = 0, 
        limit: int = 20,
        low_stock_only: bool = False
    ) -> Tuple[List[dict], int]:
        """Get inventory records with book details"""
        
        # Build query joining inventory with books
        query = db.query(InventoryRecord, Book).join(
            Book, InventoryRecord.book_id == Book.id
        ).filter(Book.is_active == True)
        
        # Filter for low stock if requested
        if low_stock_only:
            query = query.filter(
                InventoryRecord.quantity_available <= InventoryRecord.reorder_point
            )
        
        # Get total count
        total = query.count()
        
        # Get records with pagination
        records = query.offset(skip).limit(limit).all()
        
        # Format response
        inventory_list = []
        for inventory_record, book in records:
            item = {
                "inventory": {
                    "id": inventory_record.id,
                    "book_id": inventory_record.book_id,
                    "quantity_available": inventory_record.quantity_available,
                    "quantity_total": inventory_record.quantity_total,
                    "reorder_point": inventory_record.reorder_point,
                    "created_at": inventory_record.created_at,
                    "updated_at": inventory_record.updated_at
                },
                "book": {
                    "id": book.id,
                    "title": book.title,
                    "subtitle": book.subtitle,
                    "authors": book.authors,
                    "genres": book.genres,
                    "description": book.description,
                    "price": book.price,
                    "cover_image_url": book.cover_image_url,
                    "created_at": book.created_at,
                    "updated_at": book.updated_at,
                    "is_active": book.is_active
                }
            }
            inventory_list.append(item)
        
        return inventory_list, total
    
    @staticmethod
    def get_inventory_by_book_id(db: Session, book_id: UUID) -> Optional[dict]:
        """Get inventory record for specific book"""
        book_id_str = str(book_id)
        inventory = db.query(InventoryRecord).filter(
            InventoryRecord.book_id == book_id_str
        ).first()
        
        if not inventory:
            return None
        
        book = db.query(Book).filter(Book.id == book_id_str).first()
        if not book:
            return None
        
        return {
            "inventory": {
                "id": inventory.id,
                "book_id": inventory.book_id,
                "quantity_available": inventory.quantity_available,
                "quantity_total": inventory.quantity_total,
                "reorder_point": inventory.reorder_point,
                "created_at": inventory.created_at,
                "updated_at": inventory.updated_at
            },
            "book": {
                "id": book.id,
                "title": book.title,
                "subtitle": book.subtitle,
                "authors": book.authors,
                "genres": book.genres,
                "description": book.description,
                "price": book.price,
                "cover_image_url": book.cover_image_url,
                "created_at": book.created_at,
                "updated_at": book.updated_at,
                "is_active": book.is_active
            }
        }
    
    @staticmethod
    def adjust_inventory(
        db: Session, 
        book_id: UUID, 
        adjustment: InventoryAdjustment
    ) -> Optional[StockTransaction]:
        """Adjust inventory levels and create transaction record"""
        
        book_id_str = str(book_id)
        
        # Get or create inventory record (demo allows creating inventory without a book)
        inventory = db.query(InventoryRecord).filter(
            InventoryRecord.book_id == book_id_str
        ).first()
        inventory_is_new = False
        if not inventory:
            inventory = InventoryRecord(
                id=str(uuid4()),
                book_id=book_id_str,
                quantity_available=0,
                quantity_total=0,
                reorder_point=LOW_STOCK_THRESHOLD
            )
            inventory_is_new = True
        
        # Calculate new quantities
        new_available = inventory.quantity_available + adjustment.quantity_change
        new_total = inventory.quantity_total + adjustment.quantity_change
        
        # Validate that quantities don't go negative
        if new_available < 0:
            logger.warning(f"Adjustment would result in negative available quantity for book {book_id}")
            return None
        if new_total < 0:
            logger.warning(f"Adjustment would result in negative total quantity for book {book_id}")
            return None
        
        # Determine transaction type
        if adjustment.quantity_change > 0:
            transaction_type = "stock_in"
        elif adjustment.quantity_change < 0:
            transaction_type = "stock_out"
        else:
            transaction_type = "adjustment"

        # Apply changes using the current session transaction
        transaction = StockTransaction(
            id=str(uuid4()),
            book_id=book_id_str,
            transaction_type=transaction_type,
            quantity_change=adjustment.quantity_change,
            notes=adjustment.notes
        )

        if inventory_is_new:
            db.add(inventory)
        inventory.quantity_available = new_available
        inventory.quantity_total = new_total
        inventory.updated_at = datetime.utcnow()
        db.add(transaction)

        db.commit()
        db.refresh(transaction)
        
        logger.info(
            f"Adjusted inventory for book {book_id}: {adjustment.quantity_change} "
            f"(new available: {new_available}, new total: {new_total})"
        )
        
        return transaction


class TransactionService:
    """Service for stock transaction operations"""
    
    @staticmethod
    def get_transactions(
        db: Session,
        book_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[StockTransaction], int]:
        """Get stock transactions with optional book filter"""
        
        query = db.query(StockTransaction)
        
        if book_id:
            query = query.filter(StockTransaction.book_id == str(book_id))
        
        # Order by timestamp descending (most recent first)
        query = query.order_by(StockTransaction.timestamp.desc())
        
        # Get total count
        total = query.count()
        
        # Get transactions with pagination
        transactions = query.offset(skip).limit(limit).all()
        
        return transactions, total
