from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class ShippingInfo(BaseModel):
    """Shipping information for checkout"""
    name: str
    phone: str
    email: EmailStr
    address: str
    note: Optional[str] = None


class CreateOrderRequest(BaseModel):
    """Request to create order from cart"""
    shipping: ShippingInfo


class OrderItemResponse(BaseModel):
    """Single item in an order"""
    id: int
    product_id: int
    product_name: str
    product_image: Optional[str] = None
    product_size: Optional[str] = None
    quantity: int
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response with all details"""
    id: int
    user_id: str
    
    # Shipping
    shipping_name: str
    shipping_phone: str
    shipping_email: str
    shipping_address: str
    
    # Amounts
    subtotal: float
    shipping_fee: float
    total_amount: float
    status: str
    note: Optional[str] = None
    
    # Payment & Refund info
    payment_intent_id: Optional[str] = None
    refund_id: Optional[str] = None
    refund_amount: Optional[float] = None
    refund_reason: Optional[str] = None
    refunded_at: Optional[datetime] = None
    
    # Return tracking
    return_requested_at: Optional[datetime] = None
    
    # Return evidence
    return_evidence_photos: Optional[List[str]] = None
    return_evidence_video: Optional[str] = None
    return_evidence_description: Optional[str] = None
    
    # Items
    items: List[OrderItemResponse] = []
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderListItem(BaseModel):
    """Order summary for list view"""
    id: int
    total_amount: float
    status: str
    items_count: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =====================
# Admin Schemas
# =====================

class AdminOrderListItem(BaseModel):
    """Order summary for admin list view - includes user info"""
    id: int
    user_id: str
    user_email: Optional[str] = None
    shipping_name: str
    shipping_email: str
    total_amount: float
    status: str
    items_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Return evidence fields
    return_evidence_photos: Optional[List[str]] = None
    return_evidence_video: Optional[str] = None
    return_evidence_description: Optional[str] = None

    class Config:
        from_attributes = True


class AdminOrdersResponse(BaseModel):
    """Paginated orders list for admin"""
    orders: List[AdminOrderListItem]
    total: int
    page: int
    size: int
    total_pages: int


class UpdateOrderStatusRequest(BaseModel):
    """Request to update order status"""
    status: str  # pending, confirmed, shipped, delivered, cancelled
