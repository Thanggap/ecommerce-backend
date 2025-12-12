-- Fix invalid orders that are stuck in refund_pending without payment_intent_id
-- These orders were created before the validation fix was deployed

UPDATE orders 
SET status = 'cancelled', 
    updated_at = NOW()
WHERE status = 'refund_pending' 
  AND payment_intent_id IS NULL 
  AND refund_id IS NULL;

-- Show affected orders
SELECT id, status, payment_intent_id, refund_id, created_at, updated_at
FROM orders 
WHERE id IN (11, 13, 14, 15, 16, 17, 19, 20)
ORDER BY id;
