"""
Simple SQL migration - Add payment & refund columns
Copy SQL và chạy trực tiếp trong DB hoặc dùng alembic
"""

SQL_MIGRATION = """
-- Add payment and refund tracking columns to orders table
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS payment_intent_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS refund_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS refund_amount FLOAT,
ADD COLUMN IF NOT EXISTS refund_reason TEXT,
ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMP;

-- Verify columns added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'orders' 
AND column_name IN ('payment_intent_id', 'refund_id', 'refund_amount', 'refund_reason', 'refunded_at');
"""

print(SQL_MIGRATION)
