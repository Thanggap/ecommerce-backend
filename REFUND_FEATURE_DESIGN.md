# Refund Feature Design - Ecommerce System

## 🎯 Business Logic (Logic nghiệp vụ)

### **Khi nào user có thể CANCEL order?**

#### ✅ **User có thể cancel:**
1. **PENDING** - Order chưa thanh toán
   - Cancel → Status = CANCELLED
   - Không cần refund (chưa trả tiền)
   - Không cần rollback stock (chưa trừ stock)

2. **CONFIRMED** - Đã thanh toán nhưng chưa ship
   - Cancel → Status = CANCELLED
   - **CẦN REFUND** tiền về Stripe
   - **CẦN ROLLBACK** stock (vì đã trừ khi thanh toán)

#### ❌ **User KHÔNG thể cancel:**
3. **PROCESSING** - Đang chuẩn bị hàng
   - Có thể cho phép nhưng cần approval
   - Thời gian ngắn để cancel

4. **SHIPPED** - Đã giao cho vận chuyển
   - KHÔNG cho phép cancel
   - Phải chờ nhận hàng rồi return

5. **DELIVERED** - Đã giao hàng
   - KHÔNG cho phép cancel
   - Chỉ cho phép RETURN/REFUND

6. **CANCELLED** - Đã cancel rồi
   - Không thể cancel lại

---

## 🔄 Order Status Flow với Refund

```
PENDING (chưa thanh toán)
   ↓
   |--[Cancel]--→ CANCELLED (no refund needed)
   ↓
CONFIRMED (đã thanh toán)
   ↓
   |--[Cancel by User]--→ REFUND_PENDING → REFUNDED (rollback stock + refund money)
   ↓
PROCESSING (đang chuẩn bị)
   ↓
   |--[Cancel - Need approval]--→ REFUND_PENDING → REFUNDED
   ↓
SHIPPED (đang giao)
   ↓ (KHÔNG cho cancel)
   ↓
DELIVERED (đã giao)
   ↓
   |--[Return request]--→ RETURN_PENDING → REFUND_PENDING → REFUNDED
   ↓
```

---

## 📋 Implementation Plan

### **Phase 1: Update Order Status Enum**
Add thêm statuses:
- `REFUND_PENDING` - Đang chờ xử lý refund
- `REFUNDED` - Đã hoàn tiền

### **Phase 2: Stripe Refund Integration**
- Create Stripe refund service
- Store Stripe payment_intent_id hoặc charge_id
- Call Stripe API để refund

### **Phase 3: Refund Business Logic**
Rules:
- PENDING → CANCELLED: No refund
- CONFIRMED → REFUND_PENDING: Full refund + rollback stock
- PROCESSING → REFUND_PENDING: Full refund (need admin approval)
- SHIPPED/DELIVERED: Cannot cancel, only return

### **Phase 4: Frontend UI**
- "Cancel Order" button với conditions
- Refund status tracking
- Refund confirmation modal

### **Phase 5: Webhook Handle Refund**
- Listen `charge.refunded` event
- Update order status automatically

---

## 🛠️ Technical Implementation

### **1. Database Changes**

#### Add columns to `orders` table:
```sql
ALTER TABLE orders ADD COLUMN payment_intent_id VARCHAR(255);
ALTER TABLE orders ADD COLUMN refund_id VARCHAR(255);
ALTER TABLE orders ADD COLUMN refund_amount FLOAT;
ALTER TABLE orders ADD COLUMN refund_reason TEXT;
ALTER TABLE orders ADD COLUMN refunded_at TIMESTAMP;
```

#### Update OrderStatus enum:
```python
class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUND_PENDING = "refund_pending"  # NEW
    REFUNDED = "refunded"              # NEW
```

### **2. Store Payment Intent ID**

Update payment creation để lưu `payment_intent_id`:
```python
# In payment_router.py - after checkout session created
order.payment_intent_id = session.payment_intent
db.commit()
```

### **3. Refund Service**

```python
# app/services/refund_service.py
import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class RefundService:
    
    @staticmethod
    def create_refund(order_id: int, reason: str = None) -> dict:
        """
        Create refund for order
        - Validates order can be refunded
        - Creates Stripe refund
        - Updates order status
        - Rollbacks stock
        """
        db = get_db_session()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            
            # Validate
            if not order:
                raise HTTPException(404, "Order not found")
            
            if order.status not in ["confirmed", "processing"]:
                raise HTTPException(400, f"Cannot refund order with status {order.status}")
            
            if not order.payment_intent_id:
                raise HTTPException(400, "No payment intent found for this order")
            
            # Create Stripe refund
            refund = stripe.Refund.create(
                payment_intent=order.payment_intent_id,
                reason=reason or "requested_by_customer"
            )
            
            # Update order
            order.status = OrderStatus.REFUND_PENDING.value
            order.refund_id = refund.id
            order.refund_amount = refund.amount / 100  # Convert cents to dollars
            order.refund_reason = reason
            db.commit()
            
            return {
                "refund_id": refund.id,
                "status": refund.status,
                "amount": refund.amount / 100
            }
            
        finally:
            db.close()
    
    @staticmethod
    def handle_refund_succeeded(refund_id: str):
        """Handle webhook event when refund succeeded"""
        db = get_db_session()
        try:
            order = db.query(Order).filter(Order.refund_id == refund_id).first()
            if order:
                # Update status to refunded
                order.status = OrderStatus.REFUNDED.value
                order.refunded_at = datetime.utcnow()
                
                # Rollback stock
                OrderService.rollback_stock_on_cancel(order.id)
                
                db.commit()
                print(f"[Refund] Order {order.id} refunded successfully")
        finally:
            db.close()
```

### **4. Update Cancel Order Logic**

```python
# In order_service.py
@staticmethod
def user_cancel_order(user_id: str, order_id: int) -> OrderResponse:
    """Cancel order by user"""
    db = get_db_session()
    try:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id
        ).first()
        
        if not order:
            raise HTTPException(404, "Order not found")
        
        # Check if can cancel
        if order.status == OrderStatus.PENDING.value:
            # Just cancel - no payment yet
            order.status = OrderStatus.CANCELLED.value
            db.commit()
            return OrderService.get_order_detail(user_id, order_id)
        
        elif order.status == OrderStatus.CONFIRMED.value:
            # Need refund - paid already
            RefundService.create_refund(
                order_id=order_id,
                reason="Customer requested cancellation"
            )
            # Status will be REFUND_PENDING
            db.commit()
            return OrderService.get_order_detail(user_id, order_id)
        
        elif order.status == OrderStatus.PROCESSING.value:
            # Need admin approval
            raise HTTPException(
                400, 
                "Order is being processed. Please contact support to cancel."
            )
        
        else:
            # Cannot cancel
            raise HTTPException(
                400,
                f"Cannot cancel order with status {order.status}"
            )
    finally:
        db.close()
```

### **5. Webhook Handler**

```python
# In webhook_router.py - add new event handler
elif event["type"] == "charge.refunded":
    refund = event["data"]["object"]
    refund_id = refund.get("id")
    
    if refund_id:
        RefundService.handle_refund_succeeded(refund_id)
```

### **6. API Endpoints**

```python
# In order_router.py
@order_router.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int, current_user: User = Depends(require_user)):
    """
    Cancel order (auto refund if paid)
    - PENDING → CANCELLED (no refund)
    - CONFIRMED → REFUND_PENDING → REFUNDED (auto refund)
    - PROCESSING → Error (need support)
    - SHIPPED/DELIVERED → Error (cannot cancel)
    """
    return OrderService.user_cancel_order(str(current_user.uuid), order_id)

@order_router.get("/orders/{order_id}/refund-status")
def get_refund_status(order_id: int, current_user: User = Depends(require_user)):
    """Get refund status for order"""
    # Return refund details
    pass
```

---

## 🎨 Frontend Changes

### **Cancel Button Logic**
```typescript
const canCancelOrder = (status: string) => {
  return ['pending', 'confirmed'].includes(status);
};

const getCancelButtonText = (status: string) => {
  if (status === 'pending') return 'Cancel Order';
  if (status === 'confirmed') return 'Cancel & Refund';
  return null;
};
```

### **Status Display**
```typescript
const getStatusColor = (status: string) => {
  switch (status) {
    case 'pending': return 'warning';
    case 'confirmed': return 'info';
    case 'processing': return 'info';
    case 'shipped': return 'primary';
    case 'delivered': return 'success';
    case 'cancelled': return 'error';
    case 'refund_pending': return 'warning';
    case 'refunded': return 'secondary';
    default: return 'default';
  }
};
```

---

## 📊 Summary Table - Cancel Rules

| Order Status | User Can Cancel? | Refund? | Rollback Stock? | Notes |
|--------------|------------------|---------|-----------------|-------|
| PENDING | ✅ Yes | ❌ No | ❌ No | Chưa thanh toán, chưa trừ stock |
| CONFIRMED | ✅ Yes | ✅ Yes | ✅ Yes | Đã thanh toán, đã trừ stock |
| PROCESSING | ⚠️ Need approval | ✅ Yes | ✅ Yes | Đang chuẩn bị, cần admin approve |
| SHIPPED | ❌ No | - | - | Đã giao vận chuyển |
| DELIVERED | ❌ No | - | - | Chỉ cho phép Return |
| CANCELLED | ❌ No | - | - | Đã cancel rồi |

---

## 🚀 Implementation Steps

1. ✅ Update OrderStatus enum (add REFUND_PENDING, REFUNDED)
2. ✅ Add migration for new columns
3. ✅ Create RefundService
4. ✅ Update payment flow to store payment_intent_id
5. ✅ Update cancel order logic with refund
6. ✅ Add webhook handler for refund events
7. ✅ Update frontend Cancel button logic
8. ✅ Add refund status tracking UI
9. ✅ Testing với Stripe test mode

---

## 🧪 Testing Checklist

- [ ] Cancel PENDING order → Status = CANCELLED, no refund
- [ ] Cancel CONFIRMED order → Refund created, stock rollback
- [ ] Cancel PROCESSING order → Error or approval flow
- [ ] Cancel SHIPPED order → Error
- [ ] Webhook refund.succeeded → Status = REFUNDED
- [ ] Frontend shows correct cancel button based on status
- [ ] Refund amount displayed correctly
