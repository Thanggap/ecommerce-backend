# 🔧 Hướng dẫn Debug & Fix Order Status Bug

## ❌ Vấn đề
Order status vẫn **PENDING** sau khi thanh toán thành công, thay vì chuyển sang **CONFIRMED**

## 🔍 Root Cause (Nguyên nhân)
Stripe webhook **KHÔNG ĐƯỢC TRIGGER** hoặc **FAIL** vì:

1. **STRIPE_WEBHOOK_SECRET chưa config đúng**  
   - File `.env` có `STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE` (placeholder)
   - Webhook signature verification sẽ fail → không update được status

2. **Localhost không nhận được webhook từ Stripe**  
   - Stripe cần public URL để gửi webhook
   - `localhost:8000` không accessible từ internet

---

## ✅ Solutions (Cách fix)

### **Option 1: Dùng Stripe CLI (Recommended - Nhanh nhất)**

```bash
# 1. Install Stripe CLI
# Download tại: https://stripe.com/docs/stripe-cli
# Hoặc:
brew install stripe/stripe-cli/stripe  # macOS
# wget https://... # Linux

# 2. Login vào Stripe account
stripe login

# 3. Listen và forward webhooks sang localhost
stripe listen --forward-to localhost:8000/webhook/stripe

# Output sẽ show webhook signing secret:
# > Ready! Your webhook signing secret is whsec_xxxxxxxxxxxxx

# 4. Copy secret đó vào .env
# STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx

# 5. Test payment flow - webhook sẽ tự động forward
```

### **Option 2: Dùng ngrok (Public URL)**

```bash
# 1. Install ngrok
# Download tại: https://ngrok.com/download

# 2. Start ngrok
ngrok http 8000

# Output:
# Forwarding: https://abc123.ngrok.io -> http://localhost:8000

# 3. Vào Stripe Dashboard
# https://dashboard.stripe.com/test/webhooks

# 4. Click "Add endpoint"
# - URL: https://abc123.ngrok.io/webhook/stripe
# - Events: checkout.session.completed, checkout.session.expired

# 5. Copy webhook signing secret vào .env
# STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

### **Option 3: Test local với script (Không cần Stripe)**

```bash
# 1. Check order status hiện tại
cd /home/thang/Documents/ecommerce-backend
python scripts/check_order_status.py 5

# 2. Manually trigger webhook (fake)
python scripts/test_webhook_local.py 5

# 3. Check lại status
python scripts/check_order_status.py 5
```

---

## 🧪 Testing Steps

### 1. Check backend logs
```bash
# Start backend với logs
cd /home/thang/Documents/ecommerce-backend
python main.py

# Watch cho messages:
# [Webhook] Received webhook request
# [Webhook] SUCCESS - Order X marked as CONFIRMED
```

### 2. Check database
```bash
# Option A: Dùng script
python scripts/check_order_status.py 5

# Option B: Direct SQL
psql -U your_user -d ecommerce_db
SELECT id, status, created_at, updated_at FROM orders WHERE id = 5;
```

### 3. Check Stripe Dashboard
- Go to: https://dashboard.stripe.com/test/webhooks
- Click vào webhook endpoint
- Tab "Events" - xem có events được gửi không
- Nếu có failed events → check error message

---

## 📝 Files đã update

1. **`app/routers/webhook_router.py`**  
   - Added detailed logging
   - Log mỗi bước: receive → verify → process → success/fail

2. **`scripts/check_order_status.py`**  
   - Query database để check order status
   - Usage: `python scripts/check_order_status.py [order_id]`

3. **`scripts/test_webhook_local.py`**  
   - Simulate Stripe webhook locally
   - Usage: `python scripts/test_webhook_local.py <order_id>`

4. **`DEBUG_WEBHOOK.md`**  
   - Full documentation

---

## 🚀 Quick Fix Commands

```bash
# Terminal 1: Start backend
cd /home/thang/Documents/ecommerce-backend
python main.py

# Terminal 2: Start Stripe CLI (nếu dùng Option 1)
stripe listen --forward-to localhost:8000/webhook/stripe
# Copy webhook secret vào .env

# Terminal 3: Test
# Create order → Pay → Check logs → Check DB
python scripts/check_order_status.py

# Hoặc manually trigger webhook:
python scripts/test_webhook_local.py 5
```

---

## 🔍 Debug Checklist

- [ ] Backend server đang chạy (`localhost:8000`)
- [ ] `.env` có `STRIPE_WEBHOOK_SECRET` đúng (không phải placeholder)
- [ ] Stripe CLI hoặc ngrok đang chạy
- [ ] Webhook endpoint registered trong Stripe Dashboard
- [ ] Backend logs show `[Webhook] Received webhook request`
- [ ] No signature verification errors
- [ ] Order status updated trong database

---

## 📌 Expected Logs (Khi success)

```
[Webhook] Received webhook request
[Webhook] Signature header: t=1234567890,v1=abc...
[Webhook] Webhook secret configured: True
[Webhook] Signature verified successfully
[Webhook] Event type: checkout.session.completed
[Webhook] checkout.session.completed - Order ID: 5
[Webhook] Session metadata: {'order_id': '5'}
[Webhook] SUCCESS - Order 5 marked as CONFIRMED and stock deducted
```

---

## 💡 Notes

- Nếu testing production: Dùng live mode keys và real webhook secret
- Ngrok free tier có session timeout → cần restart và update URL
- Stripe CLI automatically updates webhook secret khi listen
- Database query cần check cả `created_at` vs `updated_at` để verify update
