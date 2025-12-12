-- Manual fix for Order #11 - Update status to REFUNDED
-- Run this in PostgreSQL when webhook is missed

UPDATE orders 
SET 
    status = 'refunded',
    refunded_at = NOW()
WHERE id = 11 AND status = 'refund_pending';

-- Verify update
SELECT id, status, refund_id, refunded_at FROM orders WHERE id = 11;
