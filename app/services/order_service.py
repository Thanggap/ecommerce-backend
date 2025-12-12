from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import joinedload
import math

from app.models.sqlalchemy.order import Order, OrderItem, OrderStatus
from app.models.sqlalchemy.cart import Cart, Cart_Item
from app.models.sqlalchemy.product import ProductSize, Product
from app.models.sqlalchemy.user import User
from app.schemas.order_schemas import (
    CreateOrderRequest, OrderResponse, OrderItemResponse, OrderListItem,
    AdminOrderListItem, AdminOrdersResponse
)
from app.db import get_db_session
from app.i18n_keys import I18nKeys


class OrderService:
    
    @staticmethod
    def create_order(user_id: str, request: CreateOrderRequest) -> OrderResponse:
        """Create order from user's cart - validates stock at checkout"""
        db = get_db_session()
        try:
            # Get user's cart with items
            cart = db.query(Cart).options(
                joinedload(Cart.items)
                .joinedload(Cart_Item.product_size)
                .joinedload(ProductSize.product)
            ).filter(Cart.user_id == user_id).first()
            
            if not cart or not cart.items:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=I18nKeys.CART_EMPTY
                )
            
            # Calculate totals and validate stock
            subtotal = 0.0
            order_items = []
            out_of_stock_items = []
            
            for cart_item in cart.items:
                product = cart_item.product_size.product if cart_item.product_size else None
                if not product:
                    continue
                
                # Phase 5: Stock validation at checkout only
                # Check size stock first if available, otherwise check product stock
                if cart_item.product_size:
                    # If product has sizes, check size stock
                    available_stock = cart_item.product_size.stock_quantity
                else:
                    # If no size, check product stock
                    available_stock = product.stock
                
                if available_stock < cart_item.quantity:
                    out_of_stock_items.append({
                        'name': product.product_name,
                        'size': cart_item.product_size.size if cart_item.product_size else None,
                        'available': available_stock,
                        'requested': cart_item.quantity
                    })
                    continue
                    
                unit_price = product.sale_price or product.price
                total_price = unit_price * cart_item.quantity
                subtotal += total_price
                
                order_items.append({
                    'product_id': cart_item.product_id,
                    'product_name': product.product_name,
                    'product_image': product.image_url,
                    'product_size': cart_item.product_size.size if cart_item.product_size else None,
                    'quantity': cart_item.quantity,
                    'unit_price': unit_price,
                    'total_price': total_price
                })
            
            # Return error if any items out of stock
            if out_of_stock_items:
                items_msg = ", ".join([
                    f"{item['name']} (size {item['size']}): only {item['available']} left" 
                    for item in out_of_stock_items
                ])
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Some items are out of stock: {items_msg}"
                )
            
            if not order_items:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=I18nKeys.CART_EMPTY
                )
            
            # Shipping fee (free over 100 USD)
            shipping_fee = 0.0 if subtotal >= 100 else 10.0
            total_amount = subtotal + shipping_fee
            
            # Create order
            order = Order(
                user_id=user_id,
                shipping_name=request.shipping.name,
                shipping_phone=request.shipping.phone,
                shipping_email=request.shipping.email,
                shipping_address=request.shipping.address,
                note=request.shipping.note,
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                total_amount=total_amount,
                status=OrderStatus.PENDING.value
            )
            db.add(order)
            db.flush()  # Get order.id
            
            # Create order items
            for item_data in order_items:
                order_item = OrderItem(
                    order_id=order.id,
                    **item_data
                )
                db.add(order_item)
            
            # Clear cart
            db.query(Cart_Item).filter(Cart_Item.cart_id == cart.id).delete()
            
            db.commit()
            db.refresh(order)
            
            return OrderService._map_to_response(order, order_items)
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            print(f"Create order error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=I18nKeys.GENERAL_ERROR
            )
        finally:
            db.close()
    
    @staticmethod
    def get_user_orders(user_id: str) -> List[OrderListItem]:
        """Get all orders for a user"""
        db = get_db_session()
        try:
            orders = db.query(Order).options(
                joinedload(Order.items)
            ).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
            
            return [
                OrderListItem(
                    id=order.id,
                    total_amount=order.total_amount,
                    status=order.status,
                    items_count=len(order.items) if order.items else 0,
                    created_at=order.created_at
                )
                for order in orders
            ]
        finally:
            db.close()
    
    @staticmethod
    def get_order_detail(user_id: str, order_id: int) -> OrderResponse:
        """Get order detail - only if belongs to user"""
        db = get_db_session()
        try:
            order = db.query(Order).options(
                joinedload(Order.items)
            ).filter(Order.id == order_id, Order.user_id == user_id).first()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=I18nKeys.ORDER_NOT_FOUND
                )
            
            items = [
                OrderItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    product_image=item.product_image,
                    product_size=item.product_size,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price
                )
                for item in order.items
            ]
            
            return OrderResponse(
                id=order.id,
                user_id=str(order.user_id),
                shipping_name=order.shipping_name,
                shipping_phone=order.shipping_phone,
                shipping_email=order.shipping_email,
                shipping_address=order.shipping_address,
                subtotal=order.subtotal,
                shipping_fee=order.shipping_fee,
                total_amount=order.total_amount,
                status=order.status,
                note=order.note,
                payment_intent_id=order.payment_intent_id,
                refund_id=order.refund_id,
                refund_amount=order.refund_amount,
                refund_reason=order.refund_reason,
                refunded_at=order.refunded_at,
                return_requested_at=order.return_requested_at,
                items=items,
                created_at=order.created_at,
                updated_at=order.updated_at
            )
        finally:
            db.close()
    
    @staticmethod
    def _map_to_response(order: Order, items_data: list) -> OrderResponse:
        """Map order to response"""
        items = [
            OrderItemResponse(
                id=0,  # Not saved yet
                product_id=item['product_id'],
                product_name=item['product_name'],
                product_image=item['product_image'],
                product_size=item['product_size'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['total_price']
            )
            for item in items_data
        ]
        
        return OrderResponse(
            id=order.id,
            user_id=str(order.user_id),
            shipping_name=order.shipping_name,
            shipping_phone=order.shipping_phone,
            shipping_email=order.shipping_email,
            shipping_address=order.shipping_address,
            subtotal=order.subtotal,
            shipping_fee=order.shipping_fee,
            total_amount=order.total_amount,
            status=order.status,
            note=order.note,
            payment_intent_id=order.payment_intent_id,
            refund_id=order.refund_id,
            refund_amount=order.refund_amount,
            refund_reason=order.refund_reason,
            refunded_at=order.refunded_at,
            return_requested_at=order.return_requested_at,
            items=items,
            created_at=order.created_at,
            updated_at=order.updated_at
        )

    # =====================
    # Admin Methods
    # =====================
    
    @staticmethod
    def admin_get_all_orders(
        page: int = 1,
        size: int = 20,
        status_filter: Optional[str] = None
    ) -> AdminOrdersResponse:
        """Get all orders with pagination (admin only)"""
        db = get_db_session()
        try:
            query = db.query(Order).options(
                joinedload(Order.items)
            )
            
            # Filter by status if provided
            if status_filter:
                query = query.filter(Order.status == status_filter)
            
            # Get total count
            total = query.count()
            total_pages = math.ceil(total / size) if total > 0 else 1
            
            # Paginate and order
            orders = query.order_by(Order.created_at.desc()).offset((page - 1) * size).limit(size).all()
            
            # Get user emails for orders
            user_ids = list(set(str(o.user_id) for o in orders))
            users_map = {}
            if user_ids:
                users = db.query(User).filter(User.uuid.in_(user_ids)).all()
                users_map = {str(u.uuid): u.email for u in users}
            
            order_items = [
                AdminOrderListItem(
                    id=order.id,
                    user_id=str(order.user_id),
                    user_email=users_map.get(str(order.user_id)),
                    shipping_name=order.shipping_name,
                    shipping_email=order.shipping_email,
                    total_amount=order.total_amount,
                    status=order.status,
                    items_count=len(order.items) if order.items else 0,
                    created_at=order.created_at,
                    updated_at=order.updated_at
                )
                for order in orders
            ]
            
            return AdminOrdersResponse(
                orders=order_items,
                total=total,
                page=page,
                size=size,
                total_pages=total_pages
            )
        finally:
            db.close()
    
    @staticmethod
    def admin_get_order_detail(order_id: int) -> OrderResponse:
        """Get any order detail (admin only)"""
        db = get_db_session()
        try:
            order = db.query(Order).options(
                joinedload(Order.items)
            ).filter(Order.id == order_id).first()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=I18nKeys.ORDER_NOT_FOUND
                )
            
            items = [
                OrderItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    product_image=item.product_image,
                    product_size=item.product_size,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price
                )
                for item in order.items
            ]
            
            return OrderResponse(
                id=order.id,
                user_id=str(order.user_id),
                shipping_name=order.shipping_name,
                shipping_phone=order.shipping_phone,
                shipping_email=order.shipping_email,
                shipping_address=order.shipping_address,
                subtotal=order.subtotal,
                shipping_fee=order.shipping_fee,
                total_amount=order.total_amount,
                status=order.status,
                note=order.note,
                payment_intent_id=order.payment_intent_id,
                refund_id=order.refund_id,
                refund_amount=order.refund_amount,
                refund_reason=order.refund_reason,
                refunded_at=order.refunded_at,
                return_requested_at=order.return_requested_at,
                items=items,
                created_at=order.created_at,
                updated_at=order.updated_at
            )
        finally:
            db.close()
    
    @staticmethod
    def user_cancel_order(user_id: str, order_id: int) -> OrderResponse:
        """
        Cancel/Return order by user with automatic refund logic
        - PENDING → CANCELLED (no refund, no stock rollback)
        - CONFIRMED → REFUND_PENDING → REFUNDED (auto refund + stock rollback via webhook)
        - PROCESSING → Error (need admin approval)
        - SHIPPED → Error (cannot cancel)
        - DELIVERED → RETURN_REQUESTED (need admin approval, 7-day window)
        """
        from app.services.refund_service import RefundService
        
        db = get_db_session()
        try:
            # Get order and verify ownership
            order = db.query(Order).options(
                joinedload(Order.items)
            ).filter(
                Order.id == order_id,
                Order.user_id == user_id
            ).first()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=I18nKeys.ORDER_NOT_FOUND
                )
            
            # Handle cancel/return based on order status
            if order.status == OrderStatus.PENDING.value:
                # PENDING: Just cancel - no payment yet, no stock deducted
                order.status = OrderStatus.CANCELLED.value
                db.commit()
                db.refresh(order)
                print(f"[Cancel] Order {order_id} cancelled (was PENDING, no refund needed)")
                return OrderService.get_order_detail(user_id, order_id)
            
            elif order.status == OrderStatus.CONFIRMED.value:
                # CONFIRMED: Need to refund - payment received, stock deducted
                
                # Validate payment_intent_id exists
                if not order.payment_intent_id:
                    # No payment intent = payment not completed via Stripe
                    # Just cancel the order without refund
                    order.status = OrderStatus.CANCELLED.value
                    db.commit()
                    db.refresh(order)
                    print(f"[Cancel] Order {order_id} cancelled (CONFIRMED but no payment_intent_id, no refund needed)")
                    return OrderService.get_order_detail(user_id, order_id)
                
                db.close()  # Close DB before calling RefundService
                
                try:
                    RefundService.create_refund(
                        order_id=order_id,
                        reason="Customer requested cancellation"
                    )
                    print(f"[Cancel] Order {order_id} refund initiated (was CONFIRMED)")
                    # Status is now REFUND_PENDING, will become REFUNDED via webhook
                    return OrderService.get_order_detail(user_id, order_id)
                except HTTPException:
                    raise
            
            elif order.status == OrderStatus.PROCESSING.value:
                # PROCESSING: Cannot cancel without approval
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order is being processed. Please contact support to cancel this order."
                )
            
            elif order.status == OrderStatus.SHIPPED.value:
                # SHIPPED: Cannot cancel
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot cancel order that has been shipped. Wait for delivery to request return."
                )
            
            elif order.status == OrderStatus.DELIVERED.value:
                # DELIVERED: Request return (7-day window, admin approval required)
                db.close()  # Close DB before calling RefundService
                
                try:
                    return RefundService.request_return(
                        order_id=order_id,
                        user_id=user_id,
                        reason="Customer requested return"
                    )
                except HTTPException:
                    raise
            
            else:
                # CANCELLED, RETURN_REQUESTED, REFUND_PENDING, REFUNDED: Already cancelled/refunded
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Order is already {order.status}"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            print(f"[Cancel] Error cancelling order {order_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel order"
            )
        finally:
            if db:
                db.close()

    @staticmethod
    def confirm_payment(order_id: int, payment_intent_id: str = None) -> OrderResponse:
        """
        Confirm payment for order (called by webhook)
        Updates status to CONFIRMED and saves payment_intent_id for future refunds
        """
        db = get_db_session()
        try:
            order = db.query(Order).options(
                joinedload(Order.items)
            ).filter(Order.id == order_id).first()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=I18nKeys.ORDER_NOT_FOUND
                )
            
            # Update status and payment_intent_id
            order.status = OrderStatus.CONFIRMED.value
            if payment_intent_id:
                order.payment_intent_id = payment_intent_id
            
            db.commit()
            db.refresh(order)
            
            return OrderService.admin_get_order_detail(order_id)
        finally:
            db.close()

    @staticmethod
    def admin_update_order_status(order_id: int, new_status: str) -> OrderResponse:
        """Update order status (admin only)"""
        # Validate status
        valid_statuses = [s.value for s in OrderStatus]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        db = get_db_session()
        try:
            order = db.query(Order).options(
                joinedload(Order.items)
            ).filter(Order.id == order_id).first()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=I18nKeys.ORDER_NOT_FOUND
                )
            
            # Check if we need to rollback stock
            old_status = order.status
            if old_status == "confirmed" and new_status in ["cancelled", "refunded"]:
                OrderService.rollback_stock_on_cancel(order_id)
            
            order.status = new_status
            db.commit()
            db.refresh(order)
            
            return OrderService.admin_get_order_detail(order_id)
        finally:
            db.close()

    @staticmethod
    def deduct_stock_on_payment(order_id: int):
        """Deduct stock from products when payment is confirmed"""
        db = get_db_session()
        try:
            # Get order with items
            order = db.query(Order).options(
                joinedload(Order.items)
            ).filter(Order.id == order_id).first()
            
            if not order:
                print(f"[Stock Deduction] Order {order_id} not found")
                return
            
            # Deduct stock for each item
            for item in order.items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if not product:
                    print(f"[Stock Deduction] Product {item.product_id} not found")
                    continue
                
                # Check if item has size - deduct from size stock if exists
                if item.product_size:
                    # Deduct from size-level stock
                    product_size = db.query(ProductSize).filter(
                        ProductSize.product_id == product.id,
                        ProductSize.size == item.product_size
                    ).first()
                    
                    if product_size:
                        if product_size.stock_quantity >= item.quantity:
                            product_size.stock_quantity -= item.quantity
                            print(f"[Stock Deduction] Deducted {item.quantity} from {product.product_name} size {item.product_size}, remaining: {product_size.stock_quantity}")
                        else:
                            print(f"[Stock Deduction] Insufficient size stock for {product.product_name} size {item.product_size}: has {product_size.stock_quantity}, need {item.quantity}")
                    else:
                        print(f"[Stock Deduction] Size {item.product_size} not found for product {product.product_name}")
                else:
                    # No size - deduct from product-level stock
                    if product.stock >= item.quantity:
                        product.stock -= item.quantity
                        print(f"[Stock Deduction] Deducted {item.quantity} from product {product.product_name}, remaining: {product.stock}")
                    else:
                        print(f"[Stock Deduction] Insufficient stock for product {product.product_name}: has {product.stock}, need {item.quantity}")
            
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[Stock Deduction] Error deducting stock for order {order_id}: {e}")
        finally:
            db.close()

    @staticmethod
    def rollback_stock_on_cancel(order_id: int):
        """Rollback stock when order is cancelled or refunded"""
        db = get_db_session()
        try:
            # Get order with items
            order = db.query(Order).options(
                joinedload(Order.items)
            ).filter(Order.id == order_id).first()
            
            if not order:
                print(f"[Stock Rollback] Order {order_id} not found")
                return
            
            # Add back stock for each item
            for item in order.items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if not product:
                    print(f"[Stock Rollback] Product {item.product_id} not found")
                    continue
                
                # Check if item has size - add back to size stock if exists
                if item.product_size:
                    # Add back to size-level stock
                    product_size = db.query(ProductSize).filter(
                        ProductSize.product_id == product.id,
                        ProductSize.size == item.product_size
                    ).first()
                    
                    if product_size:
                        product_size.stock_quantity += item.quantity
                        print(f"[Stock Rollback] Added back {item.quantity} to {product.product_name} size {item.product_size}, now: {product_size.stock_quantity}")
                    else:
                        print(f"[Stock Rollback] Size {item.product_size} not found for product {product.product_name}")
                else:
                    # No size - add back to product-level stock
                    product.stock += item.quantity
                    print(f"[Stock Rollback] Added back {item.quantity} to product {product.product_name}, now: {product.stock}")
            
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[Stock Rollback] Error rolling back stock for order {order_id}: {e}")
        finally:
            db.close()
