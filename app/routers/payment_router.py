import os
import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services.user_service import require_user
from app.services.order_service import OrderService
from app.models.sqlalchemy.user import User

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

payment_router = APIRouter()


class CreateCheckoutRequest(BaseModel):
    """Request to create Stripe checkout session"""
    order_id: int


class CheckoutSessionResponse(BaseModel):
    """Response with Stripe checkout URL"""
    checkout_url: str
    session_id: str


@payment_router.post("/payments/create-session", response_model=CheckoutSessionResponse)
def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user: User = Depends(require_user)
):
    """
    Create Stripe Checkout Session for an order
    - Get order from DB
    - Create Stripe session with line items
    - Return checkout URL for redirect
    """
    user_id = str(current_user.uuid)
    
    # Get order and validate ownership
    order = OrderService.get_order_detail(user_id, request.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Build line items for Stripe
    line_items = []
    for item in order.items:
        line_items.append({
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": item.product_name,
                    "images": [item.product_image] if item.product_image else [],
                },
                "unit_amount": int(item.unit_price * 100),  # Convert to cents
            },
            "quantity": item.quantity,
        })
    
    # Add shipping fee as a line item if exists
    if order.shipping_fee > 0:
        line_items.append({
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "Shipping Fee",
                },
                "unit_amount": int(order.shipping_fee * 100),
            },
            "quantity": 1,
        })
    
    try:
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=f"{os.getenv('FRONTEND_SUCCESS_URL')}?session_id={{CHECKOUT_SESSION_ID}}&order_id={order.id}",
            cancel_url=f"{os.getenv('FRONTEND_CANCEL_URL')}?order_id={order.id}",
            metadata={
                "order_id": str(order.id),
                "user_id": user_id,
            },
            customer_email=order.shipping_email,
        )
        
        return CheckoutSessionResponse(
            checkout_url=session.url,
            session_id=session.id
        )
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@payment_router.post("/payments/verify-session/{session_id}")
def verify_payment_session(
    session_id: str,
    current_user: User = Depends(require_user)
):
    """
    Verify Stripe session and auto-confirm order if payment succeeded
    This is a fallback for when webhooks don't work (dev environment)
    """
    try:
        # Retrieve session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Check if payment was successful
        if session.payment_status == "paid":
            order_id = session.metadata.get("order_id")
            
            if order_id:
                # Update order status to confirmed
                from app.db import get_db_session
                from app.models.sqlalchemy.order import Order, OrderStatus
                
                db = get_db_session()
                try:
                    order = db.query(Order).filter(Order.id == int(order_id)).first()
                    if order and order.status == OrderStatus.PENDING.value:
                        order.status = OrderStatus.CONFIRMED.value
                        order.payment_intent_id = session.payment_intent
                        db.commit()
                        
                        # Deduct stock
                        OrderService.deduct_stock_on_payment(int(order_id))
                        
                        return {
                            "success": True,
                            "order_id": order_id,
                            "status": "confirmed",
                            "message": "Order confirmed successfully"
                        }
                    elif order and order.status == OrderStatus.CONFIRMED.value:
                        return {
                            "success": True,
                            "order_id": order_id,
                            "status": "already_confirmed",
                            "message": "Order already confirmed"
                        }
                finally:
                    db.close()
        
        return {
            "success": False,
            "payment_status": session.payment_status,
            "message": "Payment not completed"
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
