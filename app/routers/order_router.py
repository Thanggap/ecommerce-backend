from typing import List, Optional
from fastapi import APIRouter, Depends, Query
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
def cancel_order(order_id: int, current_user: User = Depends(require_user)):
    """Cancel order (only if status is Pending or Confirmed)"""
    return OrderService.user_cancel_order(str(current_user.uuid), order_id)


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
