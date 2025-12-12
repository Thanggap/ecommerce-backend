# Return & Refund Feature - Implementation Summary

## Overview
Comprehensive return and refund system cho eCommerce platform with Stripe integration.

## Business Logic Flow

### 1. PENDING Orders
```
User clicks "Cancel Order"
→ Status: CANCELLED
→ No refund (chưa thanh toán)
→ No stock rollback (chưa deduct)
```

### 2. CONFIRMED Orders  
```
User clicks "Cancel & Refund"
→ Auto create Stripe refund
→ Status: REFUND_PENDING
→ Webhook receives charge.refunded
→ Status: REFUNDED
→ Stock rollback automatically
```

### 3. PROCESSING Orders
```
User clicks "Cancel"
→ Error: "Order is being processed. Contact support."
→ Admin intervention required
```

### 4. SHIPPED Orders
```
User clicks "Cancel"
→ Error: "Cannot cancel shipped orders. Wait for delivery to request return."
```

### 5. DELIVERED Orders (NEW!)
```
User clicks "Request Return" (within 7 days)
→ Status: RETURN_REQUESTED
→ Admin reviews request
→ Admin approves:
   → Status: RETURN_APPROVED
   → Auto create Stripe refund
   → Status: REFUND_PENDING
   → Webhook confirms
   → Status: REFUNDED
   → Stock rollback
→ Admin rejects:
   → Status: DELIVERED (reverted)
   → User notified
```

## Database Changes

### OrderStatus Enum
```python
class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURN_REQUESTED = "return_requested"    # NEW
    RETURN_APPROVED = "return_approved"      # NEW
    REFUND_PENDING = "refund_pending"
    REFUNDED = "refunded"
```

### New Column
```sql
ALTER TABLE orders ADD COLUMN return_requested_at TIMESTAMP WITH TIME ZONE;
```
**Migration:** `7c3f8a9b2e1d_add_return_tracking_column_to_orders.py`

## Backend Implementation

### RefundService Methods

#### 1. request_return()
```python
RefundService.request_return(order_id, user_id, reason)
```
- Validates: Order exists, user owns it, status = DELIVERED
- Checks: 7-day return window from `updated_at`
- Updates: status → RETURN_REQUESTED, sets `return_requested_at`
- Returns: OrderResponse

#### 2. approve_return()
```python
RefundService.approve_return(order_id)
```
- Validates: status = RETURN_REQUESTED
- Updates: status → RETURN_APPROVED
- Auto calls: `create_refund()` → REFUND_PENDING
- Returns: Refund details

#### 3. reject_return()
```python
RefundService.reject_return(order_id, rejection_reason)
```
- Validates: status = RETURN_REQUESTED
- Reverts: status → DELIVERED
- Clears: `return_requested_at`
- Records: rejection reason in `refund_reason`

### API Endpoints

#### User Endpoints
```
POST /orders/{order_id}/cancel
- PENDING → CANCELLED
- CONFIRMED → REFUND_PENDING
- DELIVERED → RETURN_REQUESTED (if within 7 days)
```

#### Admin Endpoints
```
GET /admin/orders/returns/pending
- List all return_requested orders
- Pagination support

POST /admin/orders/{order_id}/returns/approve
- Approve return
- Auto initiate refund

POST /admin/orders/{order_id}/returns/reject?rejection_reason=...
- Reject return
- Revert to DELIVERED
```

## Return Policy

### Time Limit
- **7 days** from delivery (`updated_at` timestamp)
- Calculated as: `(datetime.utcnow() - order.updated_at).days`
- Error message: "Return window expired. You can only return orders within 7 days of delivery. This order was delivered X days ago."

### Eligibility
✅ **Can Request Return:**
- Order status = DELIVERED
- Within 7 days of delivery
- User is order owner

❌ **Cannot Request Return:**
- Order already cancelled/refunded
- More than 7 days since delivery
- Order not yet delivered

### Admin Approval Required
- All DELIVERED returns need manual approval
- Prevents abuse (verify product condition)
- Full control over refund process

## Frontend TODO

### 1. OrderDetailPage Updates
```tsx
// Status labels
case 'return_requested': return 'Return Requested';
case 'return_approved': return 'Return Approved';

// Button logic
canRequestReturn() {
  return order.status === 'delivered' && 
         daysS inceDelivery <= 7;
}

// Display return info
{order.return_requested_at && (
  <Alert severity="info">
    Return requested on {formatDate(order.return_requested_at)}
    Pending admin approval...
  </Alert>
)}
```

### 2. Admin Return Management Page
```tsx
// Page: /admin/returns
- List: All RETURN_REQUESTED orders
- Actions: Approve | Reject buttons
- Display: Return reason, days since delivery
- Filters: Pending, Approved, Rejected
```

## Testing Checklist

### Scenario 1: Happy Path
1. Create order → Pay → Status: CONFIRMED
2. Admin: Update status to DELIVERED
3. User: Click "Request Return" → Status: RETURN_REQUESTED
4. Admin: Approve return → Status: RETURN_APPROVED → REFUND_PENDING
5. Webhook: charge.refunded → Status: REFUNDED
6. Verify: Stock rolled back

### Scenario 2: 7-Day Limit
1. Create order → Admin: DELIVERED
2. Mock `updated_at` to 8 days ago
3. User: Click "Request Return"
4. Verify: Error "Return window expired"

### Scenario 3: Rejection
1. Create order → Admin: DELIVERED
2. User: Request return → RETURN_REQUESTED
3. Admin: Reject with reason
4. Verify: Status reverted to DELIVERED
5. Verify: Rejection reason stored

## Stock Management

### Automatic Rollback
- Triggered by: `RefundService.handle_refund_succeeded()`
- Calls: `OrderService.rollback_stock_on_cancel(order_id)`
- Increases: `product_size.stock` for each order item
- When: Refund webhook confirms successful

### Manual Rollback (Admin)
- Admin can manually adjust stock via product management
- Independent of refund system

## Stripe Integration

### Refund Creation
```python
stripe.Refund.create(
    payment_intent=order.payment_intent_id,
    amount=refund_amount_cents,  # Full order amount
    reason="requested_by_customer",
    metadata={"order_id": str(order_id)}
)
```

### Webhook Handling
```python
# Event: charge.refunded
→ RefundService.handle_refund_succeeded(refund_id)
→ Update order: REFUND_PENDING → REFUNDED
→ Set refunded_at timestamp
→ Rollback stock
```

## Error Handling

### Common Errors
```python
# No payment intent
→ "No payment intent found for this order. Cannot process refund."

# Wrong status
→ "Only DELIVERED orders can be returned. Current status: {status}"

# Time expired
→ "Return window expired. You can only return orders within 7 days of delivery."

# Already processed
→ "Order is already {status}"

# Not owner
→ "You don't have permission to return this order"
```

## Files Modified

### Backend
1. `app/models/sqlalchemy/order.py` - Added status enum + column
2. `app/services/refund_service.py` - Added return methods
3. `app/services/order_service.py` - Updated cancel logic
4. `app/routers/order_router.py` - Added admin endpoints
5. `app/schemas/order_schemas.py` - Added return_requested_at field
6. `alembic/versions/7c3f8a9b2e1d_*.py` - Migration file

### Frontend (TODO)
1. `src/services/Order.ts` - Add return_requested_at to IOrder
2. `src/pages/orders/OrderDetailPage.tsx` - Return button + status
3. `src/pages/admin/AdminReturns.tsx` - NEW: Return management page
4. `src/pages/admin/AdminOrders.tsx` - Add return status filters

## Next Steps

1. ✅ Backend complete
2. ⏳ Update frontend UI
3. ⏳ Test end-to-end flow
4. ⏳ Document for users
5. ⏳ Monitor Stripe webhooks in production

---

**Implementation Date:** December 12, 2025  
**Developer:** Thang  
**Status:** Backend Complete, Frontend Pending
