# Stripe Webhook Setup for Local Development

## Problem
When testing payments locally, Stripe webhooks can't reach `localhost`. Orders stay in `PENDING` status even after successful payment.

## Solution: Use Stripe CLI

### 1. Install Stripe CLI
```bash
# macOS (Homebrew)
brew install stripe/stripe-cli/stripe

# Linux
wget https://github.com/stripe/stripe-cli/releases/latest/download/stripe_linux_x64.tar.gz
tar -xvf stripe_linux_x64.tar.gz
sudo mv stripe /usr/local/bin/

# Windows
scoop install stripe
```

### 2. Login to Stripe
```bash
stripe login
```

### 3. Forward webhooks to localhost
```bash
# Terminal 1: Run your backend server
cd /home/thang/Documents/ecommerce-backend
source env/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2: Forward Stripe webhooks
stripe listen --forward-to localhost:8000/webhook/stripe
```

This will output something like:
```
> Ready! Your webhook signing secret is whsec_xxxxxxxxxxxxx
```

### 4. Update .env with webhook secret
```bash
# In ecommerce-backend/.env
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx  # From stripe listen output
```

### 5. Test payment flow
1. Go to `http://localhost:3000`
2. Add items to cart
3. Checkout → Pay with test card: `4242 4242 4242 4242`
4. After payment, check Terminal 2 - you should see:
   ```
   2025-12-16 00:50:23   --> checkout.session.completed [evt_xxx]
   2025-12-16 00:50:23   <--  [200] POST http://localhost:8000/webhook/stripe
   ```
5. Order status should now be `CONFIRMED` ✅

---

## Alternative: Manual Status Update (Quick Fix)

If you don't want to set up Stripe CLI, you can manually update order status after payment:

### Backend endpoint to manually confirm order
Add to `app/routers/payment_router.py`:

```python
@payment_router.post("/payments/confirm-order/{order_id}")
def manual_confirm_order(
    order_id: int,
    current_user: User = Depends(require_user)
):
    """Manually confirm order after payment (dev only)"""
    from app.db import get_db_session
    from app.models.sqlalchemy.order import Order, OrderStatus
    
    db = get_db_session()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update status
        order.status = OrderStatus.CONFIRMED.value
        db.commit()
        
        # Deduct stock
        OrderService.deduct_stock_on_payment(order_id)
        
        return {"message": "Order confirmed", "order_id": order_id}
    finally:
        db.close()
```

Then call from frontend after payment success:
```typescript
// In PaymentSuccessPage.tsx
useEffect(() => {
  if (orderId) {
    // Manually confirm order (dev mode only)
    fetch(`http://localhost:8000/payments/confirm-order/${orderId}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
  }
}, [orderId]);
```

---

## Production Setup

For production, configure webhook in Stripe Dashboard:
1. Go to https://dashboard.stripe.com/webhooks
2. Add endpoint: `https://yourdomain.com/webhook/stripe`
3. Select events: `checkout.session.completed`, `checkout.session.expired`
4. Copy webhook signing secret → Update production `.env`

---

## Verification Commands

Check if webhook is working:
```bash
# Check Stripe webhook logs
stripe logs tail

# Check backend logs
tail -f backend.log | grep Webhook

# Query order status
curl http://localhost:8000/orders/{order_id} -H "Authorization: Bearer {token}"
```
