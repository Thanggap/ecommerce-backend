# Refund Feature - Implementation Summary

## ✅ COMPLETED - Backend Implementation

### **1. Model Updates** ✅
- Added `REFUND_PENDING` and `REFUNDED` to `OrderStatus` enum
- Added payment & refund tracking columns to `Order` model:
  - `payment_intent_id` - Store Stripe payment ID for refunds
  - `refund_id` - Store Stripe refund ID
  - `refund_amount` - Amount refunded
  - `refund_reason` - Reason for refund
  - `refunded_at` - Timestamp when refunded

### **2. Database Migration** ✅  
- SQL migration created: `migrations/add_refund_columns.sql`
- Run manually in DB:
```sql
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS payment_intent_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS refund_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS refund_amount FLOAT,
ADD COLUMN IF NOT EXISTS refund_reason TEXT,
ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMP;
```

### **3. Payment Flow Update** ✅
- `webhook_router.py` updated to save `payment_intent_id` when payment succeeds
- New method: `OrderService.confirm_payment()` - Updates order to CONFIRMED + saves payment_intent_id

### **4. Refund Service** ✅
Created `app/services/refund_service.py` with:
- `create_refund()` - Create Stripe refund, update order to REFUND_PENDING
- `handle_refund_succeeded()` - Process webhook when refund succeeds → REFUNDED + rollback stock
- `handle_refund_failed()` - Handle refund failures
- `get_refund_status()` - Get refund details for order

### **5. Cancel Order Logic** ✅
Updated `OrderService.user_cancel_order()` with smart logic:

| Order Status | Action | Refund? | Stock Rollback? |
|--------------|--------|---------|-----------------|
| PENDING | → CANCELLED | ❌ No | ❌ No (not deducted yet) |
| CONFIRMED | → REFUND_PENDING → REFUNDED | ✅ Yes | ✅ Yes (via webhook) |
| PROCESSING | ❌ Error (need approval) | - | - |
| SHIPPED/DELIVERED | ❌ Error (cannot cancel) | - | - |

### **6. Webhook Handlers** ✅
Updated `webhook_router.py` to handle:
- `checkout.session.completed` - Save payment_intent_id
- `charge.refunded` - Process refund, rollback stock, update to REFUNDED

### **7. Schema Updates** ✅
Updated `OrderResponse` schema to include refund fields

---

## 📋 TODO - Frontend Implementation

### **Frontend Changes Needed:**

#### **1. Update TypeScript Types**
File: `src/services/Order.ts`

```typescript
export interface IOrder {
  id: number;
  user_id: string;
  // ... existing fields ...
  status: string;
  
  // NEW: Payment & Refund fields
  payment_intent_id?: string;
  refund_id?: string;
  refund_amount?: number;
  refund_reason?: string;
  refunded_at?: string;
  
  items: IOrderItem[];
  created_at: string;
  updated_at: string;
}
```

#### **2. Update Cancel Button Logic**
File: `src/pages/orders/OrderDetailPage.tsx`

```typescript
const canCancelOrder = () => {
  if (!order) return false;
  // Only allow cancel for PENDING or CONFIRMED
  return ['pending', 'confirmed'].includes(order.status);
};

const getCancelButtonText = () => {
  if (order.status === 'pending') return 'Cancel Order';
  if (order.status === 'confirmed') return 'Cancel & Refund';
  return 'Cannot Cancel';
};
```

#### **3. Update Status Display**
File: `src/pages/orders/OrderDetailPage.tsx` và `src/pages/admin/AdminOrders.tsx`

```typescript
const getStatusColor = (status: string) => {
  switch (status) {
    case 'pending': return 'warning';
    case 'confirmed': return 'info';
    case 'processing': return 'info';
    case 'shipped': return 'primary';
    case 'delivered': return 'success';
    case 'cancelled': return 'error';
    case 'refund_pending': return 'warning';  // NEW
    case 'refunded': return 'secondary';      // NEW
    default: return 'default';
  }
};

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'refund_pending': return 'Refund Pending';
    case 'refunded': return 'Refunded';
    // ... other cases
  }
};
```

#### **4. Show Refund Info**
File: `src/pages/orders/OrderDetailPage.tsx`

```tsx
{order.refund_id && (
  <Box sx={{ mt: 2, p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
    <Typography variant="subtitle2" gutterBottom>
      Refund Information
    </Typography>
    <Typography variant="body2">
      Refund ID: {order.refund_id}
    </Typography>
    <Typography variant="body2">
      Amount: ${order.refund_amount?.toFixed(2)}
    </Typography>
    {order.refund_reason && (
      <Typography variant="body2">
        Reason: {order.refund_reason}
      </Typography>
    )}
    {order.refunded_at && (
      <Typography variant="body2">
        Refunded At: {new Date(order.refunded_at).toLocaleString()}
      </Typography>
    )}
  </Box>
)}
```

#### **5. Update Admin Order Statuses**
File: `src/pages/admin/AdminOrders.tsx`

```typescript
const ORDER_STATUSES = [
  { value: "pending", label: "Pending", color: "warning" },
  { value: "confirmed", label: "Confirmed", color: "info" },
  { value: "processing", label: "Processing", color: "info" },
  { value: "shipped", label: "Shipped", color: "primary" },
  { value: "delivered", label: "Delivered", color: "success" },
  { value: "cancelled", label: "Cancelled", color: "error" },
  { value: "refund_pending", label: "Refund Pending", color: "warning" },  // NEW
  { value: "refunded", label: "Refunded", color: "secondary" },           // NEW
];
```

---

## 🧪 Testing Checklist

### **Backend Tests:**
- [ ] Create order → Status = PENDING
- [ ] Pay with Stripe → Status = CONFIRMED + payment_intent_id saved
- [ ] Cancel PENDING order → Status = CANCELLED (no refund)
- [ ] Cancel CONFIRMED order → Refund created, Status = REFUND_PENDING
- [ ] Webhook refund succeeded → Status = REFUNDED + stock rollback
- [ ] Cancel PROCESSING order → Error
- [ ] Cancel SHIPPED order → Error
- [ ] Check refund in Stripe Dashboard

### **Frontend Tests:**
- [ ] Cancel button shows for PENDING and CONFIRMED orders
- [ ] Cancel button text correct ("Cancel Order" vs "Cancel & Refund")
- [ ] Status displays correctly (colors + labels)
- [ ] Refund info shows when order is refunded
- [ ] Cannot cancel SHIPPED/DELIVERED orders
- [ ] Refund status updates in real-time

---

## 🚀 Deployment Steps

1. **Run Database Migration**
   ```bash
   # Execute SQL in production DB
   psql -U user -d database -f migrations/add_refund_columns.sql
   ```

2. **Deploy Backend**
   - Push code to production
   - Restart backend server

3. **Update Stripe Webhook**
   - Add event: `charge.refunded` to webhook endpoint
   - Verify webhook secret is configured

4. **Deploy Frontend**
   - Update TypeScript types
   - Update UI components
   - Build and deploy

5. **Test End-to-End**
   - Create test order
   - Pay with Stripe test card
   - Cancel order
   - Verify refund in Stripe Dashboard
   - Verify order status updates
   - Verify stock rollback

---

## 📝 Key Files Modified

### Backend:
- `app/models/sqlalchemy/order.py` - Added refund columns
- `app/routers/webhook_router.py` - Save payment_intent_id, handle refund events
- `app/services/order_service.py` - Updated cancel logic with refund
- `app/services/refund_service.py` - NEW: Refund business logic
- `app/schemas/order_schemas.py` - Added refund fields to response
- `migrations/add_refund_columns.sql` - NEW: DB migration

### Frontend (TODO):
- `src/services/Order.ts` - Update IOrder interface
- `src/pages/orders/OrderDetailPage.tsx` - Cancel button + refund display
- `src/pages/admin/AdminOrders.tsx` - Add refund statuses

---

## 💡 Notes

- Refund is **async** - Status goes REFUND_PENDING → REFUNDED via webhook
- Stock rollback happens when refund **succeeds** (not when initiated)
- PENDING orders can cancel instantly (no payment/stock involved)
- CONFIRMED orders trigger Stripe refund automatically
- Admin can still manually update status to REFUNDED if needed
- Stripe test mode: Use test cards to test refunds
- Keep Stripe CLI running for local webhook testing

---

## 🎯 Business Rules Summary

**Can User Cancel?**
- ✅ PENDING: Yes (instant cancel, no refund)
- ✅ CONFIRMED: Yes (auto refund)
- ⚠️ PROCESSING: Need approval
- ❌ SHIPPED: No (contact support)
- ❌ DELIVERED: No (use return flow)

**Refund Flow:**
1. User clicks "Cancel & Refund"
2. Backend creates Stripe refund
3. Order status → REFUND_PENDING
4. Stripe processes refund
5. Webhook triggers
6. Order status → REFUNDED
7. Stock rolled back
8. User notified

---

**Implementation Status:** Backend ✅ COMPLETE | Frontend ⏳ PENDING
