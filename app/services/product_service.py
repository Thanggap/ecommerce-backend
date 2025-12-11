from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.sqlalchemy import Product, ProductSize, Category
from app.schemas.product_schemas import ProductBase, ProductResponse, CategoryResponse, ProductSizeResponse
from app.db import get_db_session
from fastapi import HTTPException
from fastapi_pagination import Page, paginate
from app import app
from app.i18n_keys import I18nKeys
from app.search.product_sync import index_product, delete_product_from_index
import os
from colorama import Fore
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

db = get_db_session()
def map_product_to_response(db_product: Product) -> ProductResponse:
    categories = [CategoryResponse(name=category.name, id=category.id) for category in db_product.categories]
    sizes = [ProductSizeResponse(size=size.size, stock_quantity=size.stock_quantity, size_id=size.size_id) for size in db_product.sizes]
    return ProductResponse(
        id=db_product.id,
        slug=db_product.slug,
        product_type=db_product.product_type,
        product_name=db_product.product_name,
        price=db_product.price,
        blurb=db_product.blurb,
        description=db_product.description,
        image_url=db_product.image_url,
        categories=categories,
        sizes=sizes,
        sale_price=db_product.sale_price,
        stock=db_product.stock,
        created_at=db_product.created_at if hasattr(db_product, 'created_at') and db_product.created_at else datetime.now()
    )
class Product_Service():
    
    # Create a new product
    def create_product(product: ProductBase) -> Dict:
        # Tạo product chính
        product_data = product.dict(exclude={"sizes", "colors"})
        db_product = Product(**product_data)
        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        # Tạo size nếu có
        sizes = getattr(product, "sizes", None)
        if sizes:
            for size in sizes:
                db_size = ProductSize(
                    product_id=db_product.id,
                    size=size.size,
                    stock_quantity=size.stock_quantity
                )
                db.add(db_size)
            db.commit()

        # Tạo màu nếu có
        colors = getattr(product, "colors", None)
        if colors:
            from app.models.sqlalchemy.product_color import ProductColor
            for color in colors:
                db_color = ProductColor(
                    product_id=db_product.id,
                    color=color.color,
                    image_url=color.image_url
                )
                db.add(db_color)
            db.commit()

        # Sync to Elasticsearch (non-blocking, don't fail if ES is down)
        try:
            index_product(db_product)
        except Exception as e:
            logger.error(f"Failed to sync product {db_product.id} to Elasticsearch: {e}")

        return map_product_to_response(db_product).dict()

    # Get a list of all products with filters
    def get_products(
        page: int = 0, 
        limit: int = 10,
        category: Optional[str] = None,
        product_type: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        search: Optional[str] = None,
        manufacturer: Optional[str] = None,
        certification: Optional[str] = None,
        on_sale: Optional[bool] = None,
        sort_by: Optional[str] = "newest"
    ) -> List[Dict]:
        try:
            query = db.query(Product)
            
            # Filter by product_type (e.g., "Vitamins", "Protein", etc.)
            if product_type:
                query = query.filter(Product.product_type.ilike(f"%{product_type}%"))
            
            # Filter by category name
            if category:
                query = query.join(Product.categories).filter(Category.name.ilike(f"%{category}%"))
            
            # Filter by price range
            if min_price is not None:
                query = query.filter(Product.price >= min_price)
            if max_price is not None:
                query = query.filter(Product.price <= max_price)
            
            # Filter by manufacturer/brand
            if manufacturer:
                query = query.filter(Product.manufacturer.ilike(f"%{manufacturer}%"))
            
            # Filter by certification (supports comma-separated: "FDA,GMP")
            if certification:
                query = query.filter(Product.certification.ilike(f"%{certification}%"))
            
            # Filter products on sale (has sale_price)
            if on_sale:
                query = query.filter(Product.sale_price.isnot(None))
            
            # Search by product name or description
            if search:
                query = query.filter(
                    or_(
                        Product.product_name.ilike(f"%{search}%"),
                        Product.description.ilike(f"%{search}%"),
                        Product.blurb.ilike(f"%{search}%")
                    )
                )
            
            # Sort
            if sort_by == "price_asc":
                query = query.order_by(Product.price.asc())
            elif sort_by == "price_desc":
                query = query.order_by(Product.price.desc())
            elif sort_by == "popular":
                # Sort by number of reviews or sales (currently sorting by ID as placeholder)
                query = query.order_by(Product.id.desc())
            else:  # "newest" or default
                query = query.order_by(Product.created_at.desc())
            
            # Pagination
            products = query.offset(page * limit).limit(limit).all()
            return [map_product_to_response(p).dict() for p in products]
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=I18nKeys.PRODUCT_FETCH_ERROR)
    # Get a single product by ID
    def get_product(product_slug: str):
        try:
            product = db.query(Product).filter(Product.slug == product_slug).one()
            print(product)
            return product
        except Exception as e:
            db.rollback()  # Ensure to rollback on any error.
            raise HTTPException(status_code=404, detail=I18nKeys.PRODUCT_NOT_FOUND)


    # Update a product
    def update_product(product_slug: str, product_data: dict) -> Dict:
        try:
            db_product = db.query(Product).filter(Product.slug == product_slug).first()
            if not db_product:
                raise HTTPException(status_code=404, detail=I18nKeys.PRODUCT_NOT_FOUND)
            
            # Update only provided fields
            for key, value in product_data.items():
                if value is not None and hasattr(db_product, key):
                    setattr(db_product, key, value)
            
            db.commit()
            db.refresh(db_product)
            
            # Sync to Elasticsearch
            try:
                index_product(db_product)
            except Exception as e:
                logger.error(f"Failed to update product {db_product.id} in Elasticsearch: {e}")
            
            return map_product_to_response(db_product).dict()
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=I18nKeys.GENERAL_ERROR)

    # Delete a product
    def delete_product(product_slug: str) -> bool:
        try:
            db_product = db.query(Product).filter(Product.slug == product_slug).first()
            if not db_product:
                raise HTTPException(status_code=404, detail=I18nKeys.PRODUCT_NOT_FOUND)
            
            product_id = db_product.id
            
            db.delete(db_product)
            db.commit()
            
            # Remove from Elasticsearch
            try:
                delete_product_from_index(product_id)
            except Exception as e:
                logger.error(f"Failed to delete product {product_id} from Elasticsearch: {e}")
            
            return True
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=I18nKeys.GENERAL_ERROR)

    @staticmethod
    def update_product_stock(product_slug: str, stock: int) -> Dict:
        """Update product stock"""
        try:
            db_product = db.query(Product).filter(Product.slug == product_slug).first()
            if not db_product:
                raise HTTPException(status_code=404, detail=I18nKeys.PRODUCT_NOT_FOUND)
            
            db_product.stock = stock
            db.commit()
            db.refresh(db_product)
            return {"message": "Stock updated successfully", "stock": stock}
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=I18nKeys.GENERAL_ERROR)

