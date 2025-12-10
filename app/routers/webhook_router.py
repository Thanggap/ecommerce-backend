import os
import stripe
from fastapi import APIRouter, Request, HTTPException

from app.services.order_service import OrderService

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

webhook_router = APIRouter()


@webhook_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events
    - Verify signature
    - Process checkout.session.completed event
    - Update order status to 'confirmed' (paid)
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        # Get order_id from metadata
        order_id = session.get("metadata", {}).get("order_id")
        
        if order_id:
            try:
                # Update order status to confirmed (paid)
                OrderService.admin_update_order_status(
                    int(order_id), 
                    "confirmed"
                )
                # Deduct stock after successful payment
                OrderService.deduct_stock_on_payment(int(order_id))
                print(f"[Stripe Webhook] Order {order_id} marked as CONFIRMED (paid) and stock deducted")
            except Exception as e:
                print(f"[Stripe Webhook] Error updating order {order_id}: {e}")
    
    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        order_id = session.get("metadata", {}).get("order_id")
        
        if order_id:
            print(f"[Stripe Webhook] Checkout expired for order {order_id}")
    
    return {"status": "success"}
