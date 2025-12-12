from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Body
from app.schemas.order_schemas import (
    CreateOrderRequest, OrderResponse, OrderListItem,
    AdminOrdersResponse, UpdateOrderStatusRequest
)
from app.services.order_service import OrderService
from app.services.user_service import require_user, require_admin
from app.models.sqlalchemy.user import User

order_router = APIRouter()


@order_router.post("/orders", response_model=OrderResponse)
def create_order(
    request: CreateOrderRequest,
    current_user: User = Depends(require_user)
):
    """Create order from current user's cart"""
    user_id = str(current_user.uuid)
    return OrderService.create_order(user_id, request)


@order_router.get("/orders", response_model=List[OrderListItem])
def get_my_orders(current_user: User = Depends(require_user)):
    """Get all orders for current user"""
    return OrderService.get_user_orders(str(current_user.uuid))


@order_router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order_detail(order_id: int, current_user: User = Depends(require_user)):
    """Get order detail by ID"""
    return OrderService.get_order_detail(str(current_user.uuid), order_id)


@order_router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    reason: Optional[str] = Body(None),
    evidence_photos: Optional[List[str]] = Body(None),
    evidence_video: Optional[str] = Body(None),
    evidence_description: Optional[str] = Body(None),
    current_user: User = Depends(require_user)
):
    """Cancel order (only if status is Pending or Confirmed) or request return with evidence (if DELIVERED)"""
    return_data = None
    
    # If any evidence provided, package into return_data dict
    if reason or evidence_photos or evidence_video or evidence_description:
        return_data = {
            'reason': reason,
            'evidence_photos': evidence_photos,
            'evidence_video': evidence_video,
            'evidence_description': evidence_description
        }
    
    return OrderService.user_cancel_order(str(current_user.uuid), order_id, return_data)


@order_router.post("/orders/{order_id}/confirm-delivery")
def confirm_delivery(order_id: int, current_user: User = Depends(require_user)):
    """User confirms they received the order"""
    return OrderService.user_confirm_delivery(str(current_user.uuid), order_id)


@order_router.post("/orders/{order_id}/review")
def create_order_review(
    order_id: int,
    rating: int = Body(..., ge=1, le=5),
    comment: str = Body(..., min_length=1),
    images: Optional[List[str]] = Body(None),
    video: Optional[str] = Body(None),
    current_user: User = Depends(require_user)
):
    """User submits review for a delivered order"""
    from app.services.review_service import ReviewService
    return ReviewService.create_order_review(
        order_id=order_id,
        user_id=str(current_user.uuid),
        rating=rating,
        comment=comment,
        images=images or [],
        video=video
    )


# =====================
# Admin Endpoints
# =====================

@order_router.get("/admin/orders", response_model=AdminOrdersResponse)
def admin_get_all_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(require_admin)
):
    """Get all orders with pagination (admin only)"""
    return OrderService.admin_get_all_orders(page=page, size=size, status_filter=status)


@order_router.get("/admin/orders/{order_id}", response_model=OrderResponse)
def admin_get_order_detail(
    order_id: int,
    current_user: User = Depends(require_admin)
):
    """Get any order detail (admin only)"""
    return OrderService.admin_get_order_detail(order_id)


@order_router.put("/admin/orders/{order_id}/status", response_model=OrderResponse)
def admin_update_order_status(
    order_id: int,
    request: UpdateOrderStatusRequest,
    current_user: User = Depends(require_admin)
):
    """Update order status (admin only)"""
    return OrderService.admin_update_order_status(order_id, request.status)


# =====================
# Return Management (Admin)
# =====================

@order_router.get("/admin/orders/returns/pending")
def admin_get_pending_returns(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin)
):
    """Get all pending return requests (admin only)"""
    return OrderService.admin_get_all_orders(page=page, size=size, status_filter="return_requested")


@order_router.post("/admin/orders/{order_id}/returns/approve")
def admin_approve_return(
    order_id: int,
    current_user: User = Depends(require_admin)
):
    """Approve return request and initiate refund (admin only)"""
    from app.services.refund_service import RefundService
    return RefundService.approve_return(order_id)


@order_router.post("/admin/orders/{order_id}/returns/reject")
def admin_reject_return(
    order_id: int,
    rejection_reason: Optional[str] = Query(None),
    current_user: User = Depends(require_admin)
):
    """Reject return request (admin only)"""
    from app.services.refund_service import RefundService
    return RefundService.reject_return(order_id, rejection_reason)


# === NEW: Enhanced Return Flow Endpoints ===

@order_router.post("/orders/{order_id}/return/ship")
def user_confirm_shipped(
    order_id: int,
    evidence_photos: list[str] = Body(...),
    evidence_description: str = Body(...),
    evidence_video: Optional[str] = Body(None),
    shipping_provider: Optional[str] = Body(None),
    tracking_number: Optional[str] = Body(None),
    current_user: User = Depends(require_user)
):
    """User confirms product shipped with evidence"""
    from app.services.refund_service import RefundService
    return RefundService.user_confirm_shipped(
        order_id=order_id,
        user_id=str(current_user.uuid),
        evidence_photos=evidence_photos,
        evidence_description=evidence_description,
        evidence_video=evidence_video,
        shipping_provider=shipping_provider,
        tracking_number=tracking_number
    )


@order_router.post("/admin/orders/{order_id}/return/receive")
def admin_confirm_received(
    order_id: int,
    qc_notes: Optional[str] = Body(None, embed=True),
    current_user: User = Depends(require_admin)
):
    """Admin confirms product received (admin only)"""
    from app.services.refund_service import RefundService
    return RefundService.admin_confirm_received(order_id, qc_notes)


@order_router.post("/admin/orders/{order_id}/return/refund")
def admin_confirm_refund(
    order_id: int,
    refund_amount: Optional[float] = Body(None),
    current_user: User = Depends(require_admin)
):
    """Admin confirms refund after QC (admin only)"""
    from app.services.refund_service import RefundService
    return RefundService.admin_confirm_refund(order_id, refund_amount)


@order_router.post("/admin/orders/{order_id}/return/reject-qc")
def admin_reject_qc(
    order_id: int,
    reason: str = Body(...),
    current_user: User = Depends(require_admin)
):
    """Admin rejects QC check (admin only)"""
    from app.services.refund_service import RefundService
    return RefundService.reject_qc(order_id, reason)


@order_router.post("/admin/orders/auto-delivery")
def admin_trigger_auto_delivery(
    dry_run: bool = Query(False, description="If true, only return count without updating"),
    current_user: User = Depends(require_admin)
):
    """Manually trigger auto-delivery job (admin only)"""
    from app.services.auto_delivery_service import AutoDeliveryService
    return AutoDeliveryService.process_auto_delivery(dry_run=dry_run)
