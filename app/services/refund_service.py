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
        - NO auto refund (wait for product to be returned)
        - Provides return instructions to user
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
            
            # Update to RETURN_APPROVED (NO refund yet)
            order.status = OrderStatus.RETURN_APPROVED.value
            db.commit()
            
            print(f"[Return] Order {order_id} return approved by admin. Waiting for user to ship product back.")
            
            # Calculate expected refund amount (for display only)
            refund_amount = order.subtotal
            
            return {
                "success": True,
                "message": "Return approved. User must ship product back with evidence before refund is processed.",
                "expected_refund_amount": refund_amount,
                "shipping_fee_not_refunded": order.shipping_fee,
                "next_steps": "User must upload evidence and confirm shipment"
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
    
    @staticmethod
    def user_confirm_shipped(
        order_id: int,
        user_id: str,
        evidence_photos: list,
        evidence_description: str,
        evidence_video: str = None,
        shipping_provider: str = None,
        tracking_number: str = None
    ) -> dict:
        """
        User confirms product has been shipped back with evidence
        - Validates: status = RETURN_APPROVED, user owns order
        - Stores: Evidence photos, video, description, tracking
        - Updates: status → RETURN_SHIPPING, sets return_shipped_at
        """
        db = get_db_session()
        try:
            order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
            
            if not order:
                raise HTTPException(404, "Order not found or you don't have permission")
            
            # Validate status
            if order.status != OrderStatus.RETURN_APPROVED.value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Can only upload evidence for RETURN_APPROVED orders. Current: {order.status}"
                )
            
            # Validate evidence
            if not evidence_photos or len(evidence_photos) == 0:
                raise HTTPException(400, "At least 1 photo is required")
            
            if len(evidence_photos) > 5:
                raise HTTPException(400, "Maximum 5 photos allowed")
            
            if not evidence_description or len(evidence_description.strip()) == 0:
                raise HTTPException(400, "Product condition description is required")
            
            # Store evidence
            order.return_evidence_photos = evidence_photos
            order.return_evidence_video = evidence_video
            order.return_evidence_description = evidence_description
            order.return_shipping_provider = shipping_provider
            order.return_tracking_number = tracking_number
            order.return_shipped_at = datetime.utcnow()
            order.status = OrderStatus.RETURN_SHIPPING.value
            
            db.commit()
            
            print(f"[Return] Order {order_id} - User confirmed shipment with {len(evidence_photos)} photos")
            
            return {
                "success": True,
                "message": "Return shipment confirmed. Admin will review upon receiving the product.",
                "order_status": order.status,
                "shipped_at": order.return_shipped_at.isoformat(),
                "evidence_count": {
                    "photos": len(evidence_photos),
                    "video": 1 if evidence_video else 0
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            print(f"[Return] Error confirming shipment for order {order_id}: {e}")
            raise HTTPException(500, f"Failed to confirm shipment: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    def admin_confirm_received(order_id: int, qc_notes: str = None) -> dict:
        """
        Admin confirms product has been received
        - Validates: status = RETURN_SHIPPING
        - Updates: status → RETURN_RECEIVED, sets return_received_at
        - Auto triggers: Stripe refund (subtotal only, no shipping fee)
        - Final status: REFUND_PENDING → REFUNDED (via webhook)
        """
        db = get_db_session()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                raise HTTPException(404, "Order not found")
            
            # Validate status
            if order.status != OrderStatus.RETURN_SHIPPING.value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Can only mark as received for RETURN_SHIPPING orders. Current: {order.status}"
                )
            
            # Validate payment_intent_id exists
            if not order.payment_intent_id:
                raise HTTPException(400, "No payment intent found. Cannot process refund.")
            
            # Update order to RETURN_RECEIVED first
            order.status = OrderStatus.RETURN_RECEIVED.value
            order.return_received_at = datetime.utcnow()
            if qc_notes:
                order.qc_notes = qc_notes
            
            db.commit()
            
            print(f"[Return] Order {order_id} - Admin confirmed product received. Auto-triggering refund...")
            
            # Auto create Stripe refund (subtotal only - no shipping fee for returns)
            refund_amount = order.subtotal  # Refund subtotal only
            
            try:
                refund = stripe.Refund.create(
                    payment_intent=order.payment_intent_id,
                    amount=int(refund_amount * 100),  # Convert to cents
                    reason="requested_by_customer",
                    metadata={"order_id": str(order_id), "type": "return_refund"}
                )
                
                print(f"[Return] Created Stripe refund {refund.id} for ${refund_amount:.2f} (subtotal only)")
                
                # Update order with refund info
                order.status = OrderStatus.REFUND_PENDING.value
                order.refund_id = refund.id
                order.refund_amount = refund_amount
                order.refund_reason = "Product returned and received by admin"
                
                db.commit()
                
                return {
                    "success": True,
                    "message": "Product received and refund initiated automatically",
                    "order_status": order.status,
                    "received_at": order.return_received_at.isoformat(),
                    "refund_id": refund.id,
                    "refund_amount": refund_amount,
                    "note": "Refund includes subtotal only (no shipping fee)"
                }
                
            except stripe.error.InvalidRequestError as e:
                db.rollback()
                raise HTTPException(400, f"Stripe refund failed: {str(e)}")
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            print(f"[Return] Error processing return receipt for order {order_id}: {e}")
            raise HTTPException(500, f"Failed to process return: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    def admin_confirm_refund(order_id: int, refund_amount: float = None) -> dict:
        """
        Admin confirms refund after QC check
        - Validates: status = RETURN_RECEIVED
        - Creates: Stripe refund (partial: subtotal only or custom amount)
        - Updates: status → REFUND_PENDING
        """
        db = get_db_session()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                raise HTTPException(404, "Order not found")
            
            # Validate status
            if order.status != OrderStatus.RETURN_RECEIVED.value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Can only confirm refund for RETURN_RECEIVED orders. Current: {order.status}"
                )
            
            # Calculate refund amount (subtotal only, NO shipping fee)
            if refund_amount is None:
                refund_amount = order.subtotal
            else:
                # Validate custom amount doesn't exceed subtotal
                if refund_amount > order.subtotal:
                    raise HTTPException(400, f"Refund amount (${refund_amount}) cannot exceed order subtotal (${order.subtotal})")
            
            print(f"[Return] Order {order_id} - Admin approving refund: ${refund_amount} (subtotal only)")
            
            # Create Stripe refund
            result = RefundService.create_refund(
                order_id=order_id,
                reason=order.refund_reason or "Return approved after QC check",
                amount=refund_amount
            )
            
            return {
                "success": True,
                "message": "Refund initiated after QC approval",
                "refund_amount": refund_amount,
                "shipping_fee_not_refunded": order.shipping_fee,
                "refund_details": result
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            print(f"[Return] Error confirming refund for order {order_id}: {e}")
            raise HTTPException(500, f"Failed to confirm refund: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    def reject_qc(order_id: int, reason: str) -> dict:
        """
        Admin rejects QC check
        - Validates: status = RETURN_RECEIVED
        - Updates: status → RETURN_REJECTED
        - Records: QC rejection reason
        """
        db = get_db_session()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            
            if not order:
                raise HTTPException(404, "Order not found")
            
            # Validate status
            if order.status != OrderStatus.RETURN_RECEIVED.value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Can only reject QC for RETURN_RECEIVED orders. Current: {order.status}"
                )
            
            if not reason or len(reason.strip()) == 0:
                raise HTTPException(400, "QC rejection reason is required")
            
            # Update order
            order.status = OrderStatus.RETURN_REJECTED.value
            order.qc_notes = f"QC Rejected: {reason}"
            order.refund_reason = f"QC Rejected: {reason}"
            
            db.commit()
            
            print(f"[Return] Order {order_id} - QC rejected. Reason: {reason}")
            
            return {
                "success": True,
                "message": "QC check failed. Return rejected.",
                "order_status": order.status,
                "rejection_reason": reason,
                "next_steps": "Product will be shipped back to customer"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            print(f"[Return] Error rejecting QC for order {order_id}: {e}")
            raise HTTPException(500, f"Failed to reject QC: {str(e)}")
        finally:
            db.close()
