from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base


class Review(Base):
    __tablename__ = 'reviews'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.uuid'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=True)  # Link to order
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    images = Column(JSON, nullable=True)  # Array of image URLs
    video = Column(String(500), nullable=True)  # Video URL
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="reviews")
    author = relationship("User", back_populates="reviews")
