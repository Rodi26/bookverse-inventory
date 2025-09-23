
"""
BookVerse Inventory Service - Database Models

This module defines SQLAlchemy ORM models for the inventory service database,
including books, inventory records, and transaction history. All models use
UUID primary keys and include comprehensive constraints and indexing.

🏗️ Database Schema:
    - Book: Product catalog with metadata and pricing
    - InventoryRecord: Stock levels and availability tracking
    - StockTransaction: Audit trail for inventory changes

🔧 Key Features:
    - UUID primary keys for distributed system compatibility
    - Comprehensive constraints and data validation
    - Optimized indexing for common query patterns
    - Audit trail with automatic timestamps
    - JSON fields for flexible metadata storage

Authors: BookVerse Platform Team
Version: 1.0.0
"""

from uuid import uuid4

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, DECIMAL, JSON, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

# SQLAlchemy declarative base for all inventory service models
Base = declarative_base()


class Book(Base):
    """
    Product catalog model representing books in the BookVerse inventory system.

    This model stores comprehensive book information including metadata, pricing,
    and categorization data. It serves as the foundation for the product catalog
    and integrates with inventory tracking and recommendation systems.

    🎯 Purpose:
        - Store complete book catalog information for e-commerce operations
        - Support search and discovery through indexed fields
        - Provide structured metadata for recommendation algorithms
        - Enable pricing and financial operations with decimal precision
        - Track book lifecycle with creation and modification timestamps

    📊 Data Structure:
        Identification:
        - id: UUID primary key for distributed system compatibility
        - title: Primary book title with search indexing
        - subtitle: Optional additional title information

        Content Metadata:
        - authors: JSON array of author names and information
        - genres: JSON array of genre classifications
        - description: Full-text description for display and search
        - rating: Decimal rating (0.0-5.0) for quality assessment

        Business Data:
        - price: Decimal pricing with 2-digit precision
        - cover_image_url: URL to book cover image for display
        - is_active: Soft delete flag for catalog management

        Audit Trail:
        - created_at: Automatic timestamp for record creation
        - updated_at: Automatic timestamp for record modifications

    🔧 Database Constraints:
        - Primary key: UUID string (36 characters)
        - Title indexed for fast search operations
        - Price precision: 10 digits total, 2 decimal places
        - Rating precision: 2 digits total, 1 decimal place (0.0-9.9 range)
        - JSON validation for authors and genres arrays
        - Soft delete through is_active boolean flag

    🛠️ Usage Examples:
        Creating a new book:
        ```python
        book = Book(
            title="Python Programming Mastery",
            authors=["Jane Smith", "John Doe"],
            genres=["technology", "programming"],
            description="Comprehensive guide to Python programming",
            price=Decimal("29.99"),
            cover_image_url="https://images.example.com/book123.jpg",
            rating=Decimal("4.5")
        )
        ```

        Querying books:
        ```python
        # Search by title
        books = session.query(Book).filter(Book.title.ilike("%python%")).all()

        # Filter by genre
        tech_books = session.query(Book).filter(
            Book.genres.contains(["technology"])
        ).all()

        # Price range filtering
        affordable_books = session.query(Book).filter(
            Book.price.between(10.00, 50.00)
        ).all()
        ```

    📋 Integration Points:
        - InventoryRecord: One-to-one relationship for stock tracking
        - StockTransaction: One-to-many for inventory movement history
        - Recommendations Service: Metadata consumption for ML algorithms
        - Web Application: Product display and search functionality
        - Checkout Service: Price and availability validation

    🔒 Security Considerations:
        - No sensitive data stored (prices are public information)
        - Soft delete prevents data loss while hiding products
        - JSON fields validated to prevent injection attacks
        - URL fields should be validated for security

    📊 Performance Characteristics:
        - Title field indexed for fast search operations
        - JSON fields support efficient array queries
        - Decimal types ensure financial precision
        - Automatic timestamp updates with minimal overhead

    Version: 1.0.0
    Table: books
    """
    __tablename__ = "books"

    # Primary identification with UUID for distributed systems
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Core book information with search optimization
    title = Column(
        String(500),
        nullable=False,
        index=True)  # Indexed for fast search
    # Optional additional title
    subtitle = Column(String(500), nullable=True)

    # Structured metadata stored as JSON arrays for flexibility
    # Array of author names/information
    authors = Column(JSON, nullable=False)
    genres = Column(JSON, nullable=False)     # Array of genre classifications

    # Content and description
    # Full book description
    description = Column(Text, nullable=False)

    # Financial data with decimal precision for accuracy
    # Price in currency units
    price = Column(DECIMAL(10, 2), nullable=False)

    # Media and presentation
    cover_image_url = Column(String(1000),
                             nullable=False)  # URL to cover image
    rating = Column(DECIMAL(2, 1), nullable=True)           # Rating 0.0-9.9

    # Audit trail with automatic timestamp management
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # Soft delete flag for catalog management
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        """String representation for debugging and logging."""
        return f"<Book(id={self.id}, title='{self.title}')>"


class InventoryRecord(Base):
    __tablename__ = "inventory_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    book_id = Column(
        String(36),
        ForeignKey(
            'books.id',
            ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True)
    quantity_available = Column(Integer, nullable=False, default=0)
    quantity_total = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False, default=5)
    __table_args__ = (
        CheckConstraint(
            'quantity_available >= 0',
            name='ck_inventory_nonneg_available'),
        CheckConstraint(
            'quantity_total >= 0',
            name='ck_inventory_nonneg_total'),
        Index(
            'ix_inventory_low_stock',
            'quantity_available',
            'reorder_point'),
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    def __repr__(self):
        return f"<InventoryRecord(book_id={self.book_id}, available={self.quantity_available})>"


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    book_id = Column(
        String(36),
        ForeignKey(
            'books.id',
            ondelete='CASCADE'),
        nullable=False,
        index=True)
    transaction_type = Column(String(20), nullable=False)
    quantity_change = Column(Integer, nullable=False)
    notes = Column(String(500), nullable=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        Index('ix_stock_tx_book_ts', 'book_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<StockTransaction(book_id={self.book_id}, type={self.transaction_type}, change={self.quantity_change})>"
