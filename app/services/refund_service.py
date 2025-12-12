"""
Refund Service - Handle Stripe refund logic
"""

import os
import stripe
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import joinedload

from app.db import get_db_session
from app.models.sqlalchemy.order import Order, OrderStatus
from app.services.order_service import OrderService
from app.schemas.order_schemas import OrderResponse

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class RefundService:
    """Handle order refunds with Stripe integration"""
    
    @staticmethod
    def create_refund(order_id: int, reason: str = None, amount: float = None) -> dict:
        """
        Create refund for order
        - Validates order can be refunded
        - Creates Stripe refund
        - Updates order status to REFUND_PENDING
        - Stock will be rolled back when refund succeeds (via webhook)
        
        Args:
            order_id: Order ID to refund
            reason: Reason for refund (optional)
            amount: Partial refund amount (optional, default = full refund)
        
        Returns:
            dict with refund details
        """
        db = get_db_session()
        try:
            order = db.query(Order).options(
                joinedload(Order.items)
            ).filter(Order.id == order_id).first()
            
            # Validate order exists
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            # Validate order status - can only refund CONFIRMED or PROCESSING
            if order.status not in [OrderStatus.CONFIRMED.value, OrderStatus.PROCESSING.value]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot refund order with status '{order.status}'. Only CONFIRMED or PROCESSING orders can be refunded."
                )
            
            # Validate payment_intent_id exists
            if not order.payment_intent_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No payment intent found for this order. Cannot process refund."
                )
            
            # Stripe only accepts: duplicate, fraudulent, requested_by_customer
            # Store custom reason in order.refund_reason, use fixed value for Stripe
            stripe_reason = "requested_by_customer"
            
            # Get actual charged amount from Stripe to avoid rounding errors
            # Don't calculate locally - use Stripe's actual charge amount
            refund_amount_cents = None  # None = full refund (Stripe will use actual charge amount)
            
            if amount:
                # Partial refund requested - calculate in cents
                refund_amount_cents = int(amount * 100)
            
            # Create Stripe refund
            try:
                refund_params = {
                    "payment_intent": order.payment_intent_id,
                    "reason": stripe_reason,
                    "metadata": {
                        "order_id": str(order_id)
                    }
                }
                
                # Only add amount if partial refund (None = full refund)
                if refund_amount_cents is not None:
                    refund_params["amount"] = refund_amount_cents
                
                refund = stripe.Refund.create(**refund_params)
                
                print(f"[Refund] Created Stripe refund {refund.id} for order {order_id}")
                
            except stripe.error.InvalidRequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stripe refund failed: {str(e)}"
                )
            
            # Update order with refund info
            order.status = OrderStatus.REFUND_PENDING.value
            order.refund_id = refund.id
            order.refund_amount = refund.amount / 100  # Convert cents to dollars
            order.refund_reason = reason
            
            db.commit()
            db.refresh(order)
            
            print(f"[Refund] Order {order_id} status updated to REFUND_PENDING")
            
            return {
                "success": True,
                "refund_id": refund.id,
                "status": refund.status,
                "amount": refund.amount / 100,
                "order_status": order.status
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            print(f"[Refund] Error creating refund for order {order_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create refund: {str(e)}"
            )
        finally:
            db.close()
    
    @staticmethod
    def handle_refund_succeeded(refund_id: str):
        """
        Handle webhook event when refund succeeded
        - Updates order status to REFUNDED
        - Rollbacks stock
        - Records refunded timestamp
        """
        db = get_db_session()
        try:
            order = db.query(Order).options(
                joinedload(Order.items)
            ).filter(Order.refund_id == refund_id).first()
            
            if not order:
                print(f"[Refund Webhook] Order not found for refund {refund_id}")
                return
            
            # Update status to refunded
            order.status = OrderStatus.REFUNDED.value
            order.refunded_at = datetime.utcnow()
            
            # Rollback stock
            OrderService.rollback_stock_on_cancel(order.id)
            
            db.commit()
            
            print(f"[Refund Webhook] Order {order.id} refunded successfully and stock rolled back")
            
        except Exception as e:
            db.rollback()
            print(f"[Refund Webhook] Error handling refund succeeded for {refund_id}: {e}")
        finally:
            db.close()
    
    @staticmethod
    def handle_refund_failed(refund_id: str):
        """Handle webhook event when refund failed"""
        db = get_db_session()
        try:
            order = db.query(Order).filter(Order.refund_id == refund_id).first()
            
            if order:
                # Revert status back to CONFIRMED
                order.status = OrderStatus.CONFIRMED.value
                db.commit()
                
                print(f"[Refund Webhook] Refund failed for order {order.id}, status reverted to CONFIRMED")
        except Exception as e:
            db.rollback()
            print(f"[Refund Webhook] Error handling refund failed: {e}")
        finally:
            db.close()
    
    @staticmethod
    def get_refund_status(order_id: int) -> dict:
        """Get refund status for an order"""
        db = get_db_session()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                raise HTTPException(404, "Order not found")
            
            if not order.refund_id:
                return {
                    "has_refund": False,
                    "order_status": order.status
                }
            
            return {
                "has_refund": True,
                "refund_id": order.refund_id,
                "refund_amount": order.refund_amount,
                "refund_reason": order.refund_reason,
                "refunded_at": order.refunded_at,
                "order_status": order.status
            }
        finally:
            db.close()

    @staticmethod
    def request_return(order_id: int, user_id: str, reason: str = None) -> OrderResponse:
        """
        User request return for DELIVERED order (within 7 days)
        - Validates order is DELIVERED
        - Checks 7-day return window
        - Updates status to RETURN_REQUESTED
        """
        from datetime import timedelta
        
        db = get_db_session()
        try:
            order = db.query(Order).options(
                joinedload(Order.items)
            ).filter(Order.id == order_id).first()
            
            # Validate order exists
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            # Validate ownership
            if str(order.user_id) != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to return this order"
                )
            
            # Validate order status - only DELIVERED can be returned
            if order.status != OrderStatus.DELIVERED.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only DELIVERED orders can be returned. Current status: {order.status}"
                )
            
            # Check 7-day return window
            # Assuming order reaches DELIVERED status via updated_at timestamp
            days_since_delivery = (datetime.utcnow() - order.updated_at).days
            if days_since_delivery > 7:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Return window expired. You can only return orders within 7 days of delivery. This order was delivered {days_since_delivery} days ago."
                )
            
            # Update status to RETURN_REQUESTED
            order.status = OrderStatus.RETURN_REQUESTED.value
            order.return_requested_at = datetime.utcnow()
            if reason:
                order.refund_reason = reason
            
            db.commit()
            db.refresh(order)
            
            print(f"[Return] Order {order_id} return requested by user {user_id}")
            
            return OrderService.get_order_detail(user_id, order_id)
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            print(f"[Return] Error requesting return for order {order_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to request return: {str(e)}"
            )
        finally:
            db.close()
    
    @staticmethod
    def approve_return(order_id: int) -> dict:
        """
        Admin approve return request
        - Updates status to RETURN_APPROVED
        - Creates Stripe refund automatically (product cost only, NO shipping fee)
        - Updates to REFUND_PENDING
        """
        db = get_db_session()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                raise HTTPException(404, "Order not found")
            
            # Validate status
            if order.status != OrderStatus.RETURN_REQUESTED.value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Can only approve orders with RETURN_REQUESTED status. Current: {order.status}"
                )
            
            # Update to RETURN_APPROVED
            order.status = OrderStatus.RETURN_APPROVED.value
            db.commit()
            
            print(f"[Return] Order {order_id} return approved by admin")
            
            # Calculate refund amount: subtotal only (NO shipping fee)
            # Return policy: refund product cost, customer pays shipping
            refund_amount = order.subtotal
            
            print(f"[Return] Refund amount: ${refund_amount} (subtotal only, shipping fee ${order.shipping_fee} not refunded)")
            
            # Automatically create refund
            result = RefundService.create_refund(
                order_id=order_id,
                reason=order.refund_reason or "Return approved by admin",
                amount=refund_amount  # Partial refund: subtotal only
            )
            
            return {
                "success": True,
                "message": "Return approved and refund initiated (product cost only, no shipping fee)",
                "refund_amount": refund_amount,
                "shipping_fee_not_refunded": order.shipping_fee,
                "refund_details": result
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            print(f"[Return] Error approving return for order {order_id}: {e}")
            raise HTTPException(500, f"Failed to approve return: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    def reject_return(order_id: int, rejection_reason: str = None) -> dict:
        """
        Admin reject return request
        - Reverts status back to DELIVERED
        - Records rejection reason
        """
        db = get_db_session()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                raise HTTPException(404, "Order not found")
            
            # Validate status
            if order.status != OrderStatus.RETURN_REQUESTED.value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Can only reject orders with RETURN_REQUESTED status. Current: {order.status}"
                )
            
            # Revert to DELIVERED
            order.status = OrderStatus.DELIVERED.value
            order.return_requested_at = None
            if rejection_reason:
                order.refund_reason = f"Return rejected: {rejection_reason}"
            
            db.commit()
            
            print(f"[Return] Order {order_id} return rejected by admin")
            
            return {
                "success": True,
                "message": "Return request rejected",
                "order_status": order.status
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            print(f"[Return] Error rejecting return for order {order_id}: {e}")
            raise HTTPException(500, f"Failed to reject return: {str(e)}")
        finally:
            db.close()
