"""
Simplified data models for BookVerse Inventory Service - Demo Version
All models in one file for simplicity and demo focus.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import uuid4, UUID

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, DECIMAL, JSON, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Book(Base):
    """
    Simplified Book model - Essential fields only for demo
    """
    __tablename__ = "books"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title = Column(String(500), nullable=False, index=True)
    subtitle = Column(String(500), nullable=True)
    authors = Column(JSON, nullable=False)  # List of author names
    genres = Column(JSON, nullable=False)   # List of genre strings
    description = Column(Text, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    cover_image_url = Column(String(1000), nullable=False)
    rating = Column(DECIMAL(2, 1), nullable=True)  # Rating from 0.0 to 5.0
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Soft delete
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}')>"


class InventoryRecord(Base):
    """
    Simplified Inventory model - Just book + quantity for demo
    """
    __tablename__ = "inventory_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    book_id = Column(String(36), ForeignKey('books.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)  # One record per book
    quantity_available = Column(Integer, nullable=False, default=0)
    quantity_total = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False, default=5)
    __table_args__ = (
        CheckConstraint('quantity_available >= 0', name='ck_inventory_nonneg_available'),
        CheckConstraint('quantity_total >= 0', name='ck_inventory_nonneg_total'),
        Index('ix_inventory_low_stock', 'quantity_available', 'reorder_point'),
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<InventoryRecord(book_id={self.book_id}, available={self.quantity_available})>"


class StockTransaction(Base):
    """
    Simple transaction log for demo audit trail
    """
    __tablename__ = "stock_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    book_id = Column(String(36), ForeignKey('books.id', ondelete='CASCADE'), nullable=False, index=True)
    transaction_type = Column(String(20), nullable=False)  # 'stock_in', 'stock_out', 'adjustment'
    quantity_change = Column(Integer, nullable=False)
    notes = Column(String(500), nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        Index('ix_stock_tx_book_ts', 'book_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<StockTransaction(book_id={self.book_id}, type={self.transaction_type}, change={self.quantity_change})>"
