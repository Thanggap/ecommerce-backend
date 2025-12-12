# Debug Webhook - Order Status Not Updating

## Problem
After payment success, order status vẫn PENDING thay vì CONFIRMED

## Root Causes (Nguyên nhân có thể)

### 1. Stripe Webhook Secret chưa config đúng
- File `.env` có `STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE` (placeholder)
- Cần get webhook secret từ Stripe Dashboard

### 2. Webhook endpoint chưa được expose ra public
- Localhost (127.0.0.1:8000) không thể nhận webhook từ Stripe
- Cần dùng ngrok hoặc deploy lên server public

### 3. Webhook chưa được register trong Stripe Dashboard
- Cần thêm webhook endpoint vào Stripe Dashboard

---

## Solution (Cách fix)

### Option 1: Test với Stripe CLI (Recommended cho local dev)

```bash
# Install Stripe CLI
# https://stripe.com/docs/stripe-cli

# Login to Stripe
stripe login

# Forward webhooks to local
stripe listen --forward-to localhost:8000/webhook/stripe

# Trigger test event
stripe trigger checkout.session.completed
```

### Option 2: Dùng ngrok (Public URL cho localhost)

```bash
# Install ngrok
# https://ngrok.com/download

# Start ngrok
ngrok http 8000

# Copy public URL (ví dụ: https://abc123.ngrok.io)
# Add webhook endpoint trong Stripe Dashboard:
# https://abc123.ngrok.io/webhook/stripe
```

### Option 3: Add debug logging để check webhook có đến không

See: `ENHANCED_WEBHOOK_DEBUG.py` below

---

## Quick Fix: Bypass webhook để test (Temporary)

Nếu muốn test nhanh mà không config webhook:
- Sau khi create order, manually update status qua admin panel
- Hoặc gọi API `PUT /admin/orders/{order_id}/status` với body `{"status": "confirmed"}`

---

## Verification Steps

1. Check backend logs xem có message `[Stripe Webhook] Order X marked as CONFIRMED` không
2. Check Stripe Dashboard > Developers > Webhooks > Events để xem webhook có được gửi không
3. Query database: `SELECT id, status FROM orders WHERE id = 5;`
4. Check network tab trong browser xem có request đến `/webhook/stripe` không

---

## Next Steps

1. ✅ Add enhanced logging to webhook handler
2. ✅ Setup Stripe CLI hoặc ngrok
3. ✅ Get real webhook secret từ Stripe
4. ✅ Test lại payment flow
