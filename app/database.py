"""
Database setup for BookVerse Inventory Service - Demo Version
SQLite database with automatic table creation and demo data loading.
"""

import json
import logging
from decimal import Decimal
from typing import List, Dict, Any
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .config import DATABASE_URL, DEMO_BOOKS_FILE, DEMO_INVENTORY_FILE
from .models import Base, Book, InventoryRecord, StockTransaction

logger = logging.getLogger(__name__)

# Create SQLite engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def load_demo_data():
    """Load demo books and inventory data from JSON files"""
    logger.info("Loading demo data...")
    
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(Book).count() > 0:
            logger.info("Demo data already exists, skipping load")
            return
        
        # Load books data
        books_data = _load_json_file(DEMO_BOOKS_FILE)
        inventory_data = _load_json_file(DEMO_INVENTORY_FILE)
        
        # Create books
        book_objects = []
        for book_data in books_data:
            book = Book(
                id=str(uuid4()),
                title=book_data["title"],
                subtitle=book_data.get("subtitle"),
                authors=book_data["authors"],
                genres=book_data["genres"],
                description=book_data["description"],
                price=Decimal(str(book_data["price"])),
                cover_image_url=book_data["cover_image_url"],
                rating=Decimal(str(book_data["rating"])) if book_data.get("rating") else None
            )
            book_objects.append(book)
            db.add(book)
        
        db.commit()
        logger.info(f"Created {len(book_objects)} demo books")
        
        # Create inventory records
        inventory_objects = []
        for i, inventory_item in enumerate(inventory_data):
            if i < len(book_objects):  # Ensure we don't exceed book count
                inventory = InventoryRecord(
                    id=str(uuid4()),
                    book_id=book_objects[i].id,
                    quantity_available=inventory_item["quantity_available"],
                    quantity_total=inventory_item["quantity_total"],
                    reorder_point=inventory_item.get("reorder_point", 5)
                )
                inventory_objects.append(inventory)
                db.add(inventory)
        
        db.commit()
        logger.info(f"Created {len(inventory_objects)} inventory records")
        
        # Create some demo transactions
        _create_demo_transactions(db, book_objects[:5])  # Just for first 5 books
        
        logger.info("Demo data loading completed successfully")
        
    except Exception as e:
        logger.error(f"Error loading demo data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def _load_json_file(file_path) -> List[Dict[str, Any]]:
    """Load JSON data from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Demo data file not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file {file_path}: {e}")
        return []


def _create_demo_transactions(db: Session, books: List[Book]):
    """Create some demo transactions for audit trail showcase"""
    transactions = [
        StockTransaction(
            id=str(uuid4()),
            book_id=books[0].id,
            transaction_type="stock_in",
            quantity_change=50,
            notes="Initial inventory"
        ),
        StockTransaction(
            id=str(uuid4()),
            book_id=books[1].id,
            transaction_type="stock_in", 
            quantity_change=30,
            notes="Restock shipment"
        ),
        StockTransaction(
            id=str(uuid4()),
            book_id=books[0].id,
            transaction_type="stock_out",
            quantity_change=-3,
            notes="Customer purchase"
        ),
        StockTransaction(
            id=str(uuid4()),
            book_id=books[2].id,
            transaction_type="adjustment",
            quantity_change=5,
            notes="Inventory correction"
        ),
    ]
    
    for transaction in transactions:
        db.add(transaction)
    
    db.commit()
    logger.info(f"Created {len(transactions)} demo transactions")


async def initialize_database():
    """Initialize database on application startup"""
    logger.info("Initializing database...")
    create_tables()
    load_demo_data()
    logger.info("Database initialization completed")
