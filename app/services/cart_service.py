from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import joinedload

from app.models.sqlalchemy.cart import Cart, Cart_Item
from app.models.sqlalchemy.product import Product, ProductSize
from app.models.sqlalchemy.user import User
from app.schemas.cart_schemas import CartBase, CartItemBase, AddToCartRequest
from app.db import get_db_session
from app.i18n_keys import I18nKeys

# Cart cache disabled - sync SQLAlchemy incompatible with async cache
# Cart data changes frequently, DB queries are fast enough


class CartService:
    @staticmethod
    def get_cart(user_id: str) -> CartBase:
        """Get user's cart with all items"""
        # Fetch from DB
        db = get_db_session()
        try:
            cart = db.query(Cart).options(
                joinedload(Cart.items).joinedload(Cart_Item.product_size).joinedload(ProductSize.product)
            ).filter(Cart.user_id == user_id).first()

            if not cart:
                cart = Cart(user_id=user_id)
                db.add(cart)
                db.commit()
                db.refresh(cart)
                return CartBase(
                    id=cart.id,
                    user_id=str(cart.user_id),
                    items=[],
                    subtotal=0.0,
                    total=0.0
                )

            # Build response
            items = []
            subtotal = 0.0
            
            for item in cart.items or []:
                product = item.product_size.product if item.product_size else None
                unit_price = product.sale_price or product.price if product else item.price
                total_price = unit_price * item.quantity
                subtotal += total_price
                
                # Build product_size_info if available
                from app.schemas.cart_schemas import ProductSizeInfo
                product_size_info = None
                if item.product_size:
                    product_size_info = ProductSizeInfo(
                        size=item.product_size.size,
                        stock_quantity=item.product_size.stock_quantity
                    )
                
                items.append(CartItemBase(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=product.product_name if product else None,
                    product_image=product.image_url if product else None,
                    product_slug=product.slug if product else None,
                    product_size=item.product_size.size if item.product_size else "",
                    product_size_info=product_size_info,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    total_price=total_price
                ))

            return CartBase(
                id=cart.id,
                user_id=str(cart.user_id),
                items=items,
                subtotal=subtotal,
                total=subtotal
            )
        finally:
            db.close()

    @staticmethod
    def add_to_cart(user_id: str, request: AddToCartRequest) -> CartBase:
        """Add item to cart"""
        db = get_db_session()
        try:
            # Get or create cart
            cart = db.query(Cart).filter(Cart.user_id == user_id).first()
            if not cart:
                cart = Cart(user_id=user_id)
                db.add(cart)
                db.commit()
                db.refresh(cart)

            # Find product and size
            product = db.query(Product).filter(Product.id == request.product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail=I18nKeys.PRODUCT_NOT_FOUND)

            product_size = db.query(ProductSize).filter(
                ProductSize.product_id == request.product_id,
                ProductSize.size == request.size
            ).first()

            if not product_size:
                # Create size if not exists (for products without explicit sizes)
                # Use product's stock as initial stock_quantity
                product_size = ProductSize(
                    product_id=request.product_id,
                    size=request.size,
                    stock_quantity=product.stock
                )
                db.add(product_size)
                db.commit()
                db.refresh(product_size)

            # Check if item already in cart
            existing_item = db.query(Cart_Item).filter(
                Cart_Item.cart_id == cart.id,
                Cart_Item.product_id == request.product_id,
                Cart_Item.product_size_id == product_size.size_id
            ).first()

            unit_price = product.sale_price or product.price

            if existing_item:
                existing_item.quantity += request.quantity
                existing_item.price = unit_price
            else:
                new_item = Cart_Item(
                    cart_id=cart.id,
                    product_id=request.product_id,
                    product_size_id=product_size.size_id,
                    quantity=request.quantity,
                    price=unit_price
                )
                db.add(new_item)

            db.commit()
            
            return CartService.get_cart(user_id)
        finally:
            db.close()

    @staticmethod
    def update_cart_item(user_id: str, cart_item_id: int, quantity: int) -> bool:
        """Update quantity of cart item - returns success status only"""
        db = get_db_session()
        try:
            # Single optimized query - no joins needed
            result = db.query(Cart_Item).join(Cart).filter(
                Cart.user_id == user_id,
                Cart_Item.id == cart_item_id
            ).first()

            if not result:
                raise HTTPException(status_code=404, detail=I18nKeys.CART_ITEM_NOT_FOUND)

            result.quantity = quantity
            db.commit()
            return True
        finally:
            db.close()

    @staticmethod
    def remove_from_cart(user_id: str, cart_item_id: int) -> bool:
        """Remove item from cart - returns success status only"""
        db = get_db_session()
        try:
            cart = db.query(Cart).filter(Cart.user_id == user_id).first()
            if not cart:
                raise HTTPException(status_code=404, detail=I18nKeys.CART_EMPTY)

            cart_item = db.query(Cart_Item).filter(
                Cart_Item.id == cart_item_id,
                Cart_Item.cart_id == cart.id
            ).first()

            if not cart_item:
                raise HTTPException(status_code=404, detail=I18nKeys.CART_ITEM_NOT_FOUND)

            db.delete(cart_item)
            db.commit()
            
            return True
        finally:
            db.close()

    @staticmethod
    def clear_cart(user_id: str) -> bool:
        """Remove all items from cart - returns success status only"""
        db = get_db_session()
        try:
            cart = db.query(Cart).filter(Cart.user_id == user_id).first()
            if cart:
                db.query(Cart_Item).filter(Cart_Item.cart_id == cart.id).delete()
                db.commit()
            
            return True
        finally:
            db.close()
