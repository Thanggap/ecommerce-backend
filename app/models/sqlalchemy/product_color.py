from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class ProductColor(Base):
    __tablename__ = 'product_colors'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    color = Column(String, nullable=False)
    image_url = Column(String, nullable=True)

    product = relationship('Product', back_populates='colors')
