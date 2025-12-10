from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, DateTime, Table, Enum
from sqlalchemy.orm import relationship, Mapped
from datetime import datetime
from app.db import Base
from sqlalchemy.dialects.postgresql import UUID
from typing import TYPE_CHECKING, List
from datetime import datetime
import enum

if TYPE_CHECKING:
    from .user import User


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = 'orders'
    
    id = Column("id", Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.uuid'), nullable=False)
    
    # Shipping info
    shipping_name = Column("shipping_name", String(255), nullable=False)
    shipping_phone = Column("shipping_phone", String(20), nullable=False)
    shipping_email = Column("shipping_email", String(255), nullable=False)
    shipping_address = Column("shipping_address", Text, nullable=False)
    
    # Order details
    subtotal = Column("subtotal", Float, nullable=False, default=0.0)
    shipping_fee = Column("shipping_fee", Float, nullable=False, default=0.0)
    total_amount = Column("total_amount", Float, nullable=False, default=0.0)
    status = Column("status", String(20), default=OrderStatus.PENDING.value)
    note = Column("note", Text, nullable=True)
    
    created_at = Column("created_at", DateTime, default=datetime.utcnow)
    updated_at = Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user: Mapped["User"] = relationship("User", back_populates="orders", foreign_keys=[user_id])
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column("id", Integer, primary_key=True, index=True)
    order_id = Column("order_id", Integer, ForeignKey('orders.id'))
    product_id = Column("product_id", Integer, ForeignKey('products.id'))
    product_name = Column("product_name", String(255), nullable=False)
    product_image = Column("product_image", String(500), nullable=True)
    product_size = Column("product_size", String(20), nullable=True)
    quantity = Column("quantity", Integer, nullable=False)
    unit_price = Column("unit_price", Float, nullable=False)
    total_price = Column("total_price", Float, nullable=False)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
