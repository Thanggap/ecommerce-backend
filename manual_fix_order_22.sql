-- Quick check order 22
SELECT id, status, payment_intent_id, refund_id 
FROM orders 
WHERE id = 22;

-- Update manually
UPDATE orders 
SET payment_intent_id = 'pi_3SdXQqGglbd86DfO180Bgv7M'
WHERE id = 22;

-- Verify
SELECT id, status, payment_intent_id, refund_id 
FROM orders 
WHERE id = 22;
