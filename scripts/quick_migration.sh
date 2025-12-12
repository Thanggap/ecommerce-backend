#!/bin/bash
# Quick migration script - Add refund columns
# Run with: bash scripts/quick_migration.sh

set -e

echo "=== Adding Refund Columns to Orders Table ==="
echo ""

# Get DB URL from .env
export $(cat .env | grep DATABASE_URL | xargs)

echo "Database URL: ${DATABASE_URL:0:50}..."
echo ""

# Run SQL directly with psql
psql "$DATABASE_URL" << EOF
-- Add refund tracking columns
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_intent_id VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_id VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_amount FLOAT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_reason TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMP;

-- Verify columns added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'orders' 
AND column_name IN ('payment_intent_id', 'refund_id', 'refund_amount', 'refund_reason', 'refunded_at')
ORDER BY column_name;
EOF

echo ""
echo "✅ Migration completed successfully!"
echo ""
echo "Columns added:"
echo "  - payment_intent_id (VARCHAR)"
echo "  - refund_id (VARCHAR)"
echo "  - refund_amount (FLOAT)"
echo "  - refund_reason (TEXT)"
echo "  - refunded_at (TIMESTAMP)"
echo ""
echo "🎉 You can now create orders with refund support!"
