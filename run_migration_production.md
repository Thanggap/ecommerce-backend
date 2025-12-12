# Hướng dẫn chạy migration trên Production (Render.com)

## Vấn đề hiện tại:
- Migration `4f9a2e1c8d5b` (add payment_intent_id column) chưa được apply vào production database
- Backend code đã có column trong model nhưng database thật chưa có
- Dẫn đến mọi lần save payment_intent_id đều fail silently

## Cách fix:

### Option 1: Chạy migration qua Render Shell (Recommended)
1. Vào Render Dashboard: https://dashboard.render.com
2. Chọn service **ecommerce-backend**
3. Click tab **Shell** 
4. Chạy lệnh:
   ```bash
   alembic upgrade head
   ```
5. Verify bằng cách check logs xem có apply migration `4f9a2e1c8d5b` không

### Option 2: Trigger deploy để auto-run migration
1. Add migration command vào `render.yaml` hoặc Dockerfile entrypoint:
   ```yaml
   # render.yaml
   services:
     - type: web
       name: ecommerce-backend
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

2. Commit và push code để trigger deploy:
   ```bash
   git add .
   git commit -m "Add auto-migration to deploy process"
   git push
   ```

### Option 3: Manual SQL (Last resort)
Nếu không access được shell, chạy trực tiếp SQL:
```sql
ALTER TABLE orders ADD COLUMN payment_intent_id VARCHAR(255);
ALTER TABLE orders ADD COLUMN refund_id VARCHAR(255);
ALTER TABLE orders ADD COLUMN refund_amount NUMERIC(10, 2);
ALTER TABLE orders ADD COLUMN refund_reason VARCHAR;
ALTER TABLE orders ADD COLUMN refunded_at TIMESTAMP WITH TIME ZONE;

-- Update alembic_version table
UPDATE alembic_version SET version_num = '7c3f8a9b2e1d';
```

## Verify sau khi chạy migration:
1. Tạo order mới (#27)
2. Complete payment qua Stripe checkout
3. Check backend logs xem có:
   ```
   [Stripe Webhook] Order 27 marked as CONFIRMED (paid) with payment_intent=pi_xxx
   ```
4. Query order 27:
   ```bash
   curl https://ecommerce-backend-dpxr.onrender.com/orders/27 \
     -H "Authorization: Bearer <token>"
   ```
5. Verify `payment_intent_id` có value (không phải null)

## Next steps sau khi fix:
- Test refund flow với order mới
- Clean up orders cũ (#11-26) bằng cách set status về CANCELLED
