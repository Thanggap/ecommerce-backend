from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, DateTime, Table, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base
from .join_tables import product_categories
from .review import *
from .product_color import ProductColor

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    slug = Column(String)
    product_type = Column(String, index=True)
    product_name = Column(String)
    price = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=True)
    stock = Column(Integer, nullable=False, default=0)
    blurb = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    
    # Supplement-specific fields
    serving_size = Column(String(100), nullable=True)
    servings_per_container = Column(Integer, nullable=True)
    ingredients = Column(Text, nullable=True)
    allergen_info = Column(Text, nullable=True)
    usage_instructions = Column(Text, nullable=True)
    warnings = Column(Text, nullable=True)
    expiry_date = Column(Date, nullable=True)
    manufacturer = Column(String(255), nullable=True)
    country_of_origin = Column(String(100), nullable=True)
    certification = Column(String(255), nullable=True)

    reviews = relationship("Review", back_populates="product")
    categories = relationship("Category", secondary=product_categories, back_populates="products")
    sizes = relationship("ProductSize", back_populates="product")
    colors = relationship("ProductColor", back_populates="product")


class ProductSize(Base):
    __tablename__ = 'product_sizes'
    __table_args__ = {'extend_existing': True}

    size_id = Column("id", Integer, primary_key=True)
    product_id = Column("product_id", Integer, ForeignKey('products.id'), nullable=False)
    size = Column("size", String)
    stock_quantity = Column("stock_quantity", Integer, nullable=False, default=0)

    product = relationship("Product", back_populates="sizes")
    cart_items = relationship("Cart_Item", back_populates="product_size")
