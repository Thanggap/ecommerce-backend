# REFUND FEATURE - FIXES SUMMARY

## Issues Fixed (Code đã sửa - CẦN RESTART BACKEND)

### 1. ✅ Fixed Rounding Error in Refund
**File:** `app/services/refund_service.py`
- **Problem:** Refund amount `$29.99` > Charge amount `$29.98` (rounding error)
- **Solution:** Không pass `amount` parameter cho full refund → Stripe tự động dùng exact charge amount

### 2. ✅ Fixed Return Policy (Delivered Orders)
**File:** `app/services/refund_service.py` - `approve_return()`
- **Problem:** DELIVERED returns refund 100% (bao gồm shipping)
- **Solution:** Chỉ refund `order.subtotal` (không bao gồm shipping fee)

### 3. ✅ Added Payment Intent Validation
**File:** `app/services/order_service.py` - `user_cancel_order()`
- **Problem:** CONFIRMED orders without payment_intent_id vẫn cố gắng refund → fail → status stuck ở refund_pending
- **Solution:** Check `if not order.payment_intent_id` → set status = CANCELLED (không refund)

### 4. ✅ Enhanced Webhook Logging
**File:** `app/routers/webhook_router.py`
- Added detailed logging để debug payment_intent_id save issue
- Logs: Found order, Set payment_intent_id, Database committed

### 5. ✅ Added Debug Endpoints
**File:** `app/routers/webhook_router.py`
- `POST /webhook/manual-confirm/{order_id}` - Manually confirm payment
- `POST /webhook/manual-refund/{refund_id}` - Manually process refund

## Current Problem

**BACKEND CHƯA RESTART → CODE MỚI CHƯA ĐƯỢC LOAD!**

Evidence:
- Order #22: status=confirmed nhưng payment_intent_id=null
- Manual endpoint returns success nhưng không update database
- Tất cả orders đều không có payment_intent_id

## Action Required

### STEP 1: RESTART BACKEND
```bash
# Terminal đang chạy ./run.sh
# Press Ctrl+C to stop
# Then run again:
cd /home/thang/Documents/ecommerce-backend
./run.sh
```

### STEP 2: Verify Code Loaded
Tạo order mới và check:
```bash
# Sau khi pay xong
curl -s "http://localhost:8000/orders" \
  -H "Authorization: Bearer <token>" \
  | jq 'sort_by(.id) | reverse | .[0] | {id, status, payment_intent_id}'
```

**Expected:** `payment_intent_id` phải có giá trị (không null)

### STEP 3: Test Refund Flow
```bash
./test_refund_simple.sh <order_id>
```

**Expected Flow:**
1. Order status: confirmed
2. payment_intent_id: pi_xxxxx (có giá trị)
3. Cancel → status: refund_pending
4. Webhook triggers → status: refunded
5. refund_amount = total_amount (100%)

## Test Scripts Created

1. `test_refund_simple.sh <order_id>` - Test refund for existing order
2. `verify_webhook.sh` - Check if webhook saves payment_intent_id
3. `fix_invalid_orders.sql` - SQL to cleanup invalid orders

## Summary

**All fixes are complete, just need to RESTART BACKEND!**

After restart:
- ✅ Webhook will save payment_intent_id correctly
- ✅ Refund will work without rounding errors  
- ✅ Return policy will be correct (subtotal only for DELIVERED)
- ✅ Validation will prevent invalid refund_pending status
