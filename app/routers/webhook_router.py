import os
import stripe
from fastapi import APIRouter, Request, HTTPException
import logging

from app.services.order_service import OrderService

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

webhook_router = APIRouter()

# Setup logging
logger = logging.getLogger(__name__)


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
    
    # DEBUG: Log webhook received
    logger.info(f"[Webhook] Received webhook request")
    logger.info(f"[Webhook] Signature header: {sig_header}")
    logger.info(f"[Webhook] Webhook secret configured: {bool(webhook_secret)}")
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        logger.info(f"[Webhook] Signature verified successfully")
        logger.info(f"[Webhook] Event type: {event.get('type')}")
    except ValueError as e:
        # Invalid payload
        logger.error(f"[Webhook] Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"[Webhook] Signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        # Get order_id and payment_intent from session
        order_id = session.get("metadata", {}).get("order_id")
        payment_intent_id = session.get("payment_intent")
        
        logger.info(f"[Webhook] checkout.session.completed - Order ID: {order_id}")
        logger.info(f"[Webhook] Payment Intent ID: {payment_intent_id}")
        logger.info(f"[Webhook] Session metadata: {session.get('metadata')}")
        
        if order_id:
            try:
                # Update order status to confirmed (paid) and save payment_intent_id
                # Don't store the response in cache - just execute the update
                from app.db import get_db_session
                from app.models.sqlalchemy.order import Order, OrderStatus
                
                db = get_db_session()
                try:
                    order = db.query(Order).filter(Order.id == int(order_id)).first()
                    if order:
                        logger.info(f"[Webhook] Found order {order_id}, current status: {order.status}")
                        order.status = OrderStatus.CONFIRMED.value
                        if payment_intent_id:
                            order.payment_intent_id = payment_intent_id
                            logger.info(f"[Webhook] Set payment_intent_id: {payment_intent_id}")
                        else:
                            logger.warning(f"[Webhook] No payment_intent_id in session!")
                        
                        db.commit()
                        logger.info(f"[Webhook] Database committed for order {order_id}")
                        
                        # Deduct stock after successful payment
                        OrderService.deduct_stock_on_payment(int(order_id))
                        logger.info(f"[Webhook] SUCCESS - Order {order_id} marked as CONFIRMED and stock deducted")
                        print(f"[Stripe Webhook] Order {order_id} marked as CONFIRMED (paid) with payment_intent={payment_intent_id}")
                    else:
                        logger.error(f"[Webhook] Order {order_id} not found in database!")
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"[Webhook] FAILED - Error updating order {order_id}: {e}", exc_info=True)
                print(f"[Stripe Webhook] Error updating order {order_id}: {e}")
        else:
            logger.warning(f"[Webhook] No order_id found in session metadata")
    
    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        order_id = session.get("metadata", {}).get("order_id")
        
        logger.info(f"[Webhook] checkout.session.expired - Order ID: {order_id}")
        
        if order_id:
            print(f"[Stripe Webhook] Checkout expired for order {order_id}")
    
    elif event["type"] == "charge.refunded":
        # Handle refund succeeded
        from app.services.refund_service import RefundService
        
        charge = event["data"]["object"]
        refunds = charge.get("refunds", {}).get("data", [])
        
        logger.info(f"[Webhook] charge.refunded event received")
        
        for refund in refunds:
            refund_id = refund.get("id")
            logger.info(f"[Webhook] Processing refund: {refund_id}")
            
            if refund_id:
                try:
                    if refund.get("status") == "succeeded":
                        RefundService.handle_refund_succeeded(refund_id)
                        logger.info(f"[Webhook] Refund {refund_id} succeeded and processed")
                    elif refund.get("status") == "failed":
                        RefundService.handle_refund_failed(refund_id)
                        logger.warning(f"[Webhook] Refund {refund_id} failed")
                except Exception as e:
                    logger.error(f"[Webhook] Error processing refund {refund_id}: {e}")
    
    else:
        logger.info(f"[Webhook] Unhandled event type: {event.get('type')}")
    
    return {"status": "success"}


# DEBUG ENDPOINT - Manual payment confirmation (for testing)
@webhook_router.post("/webhook/manual-confirm/{order_id}")
async def manual_confirm_payment(order_id: int, request: Request):
    """
    Manually confirm payment for an order (for testing without Stripe Checkout)
    Body: {"payment_intent_id": "pi_xxx"}
    """
    from app.db import get_db_session
    from app.models.sqlalchemy.order import Order, OrderStatus
    
    try:
        body = await request.json()
        payment_intent_id = body.get("payment_intent_id")
        
        if not payment_intent_id:
            raise HTTPException(400, "payment_intent_id required")
        
        logger.info(f"[Manual] Confirming payment for order {order_id} with payment_intent {payment_intent_id}")
        
        db = get_db_session()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise HTTPException(404, "Order not found")
            
            order.status = OrderStatus.CONFIRMED.value
            order.payment_intent_id = payment_intent_id
            db.commit()
            
            # Deduct stock
            OrderService.deduct_stock_on_payment(order_id)
            
            logger.info(f"[Manual] Order {order_id} confirmed successfully")
            return {"status": "success", "message": f"Order {order_id} confirmed with payment_intent {payment_intent_id}"}
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Manual] Error confirming order {order_id}: {e}")
        raise HTTPException(500, str(e))


# DEBUG ENDPOINT - Manual refund processing (for testing when webhook is missed)
@webhook_router.post("/webhook/manual-refund/{refund_id}")
async def manual_process_refund(refund_id: str):
    """
    Manually trigger refund processing (for testing/debugging)
    Use when webhook was missed or for manual testing
    """
    from app.services.refund_service import RefundService
    
    try:
        logger.info(f"[Manual] Processing refund manually: {refund_id}")
        RefundService.handle_refund_succeeded(refund_id)
        return {
            "status": "success",
            "message": f"Refund {refund_id} processed manually"
        }
    except Exception as e:
        logger.error(f"[Manual] Error processing refund {refund_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
