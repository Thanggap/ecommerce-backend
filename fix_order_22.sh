#!/bin/bash

# Manually fix order #22 by setting payment_intent_id from Stripe
ORDER_ID=22

echo "=== Fixing Order #$ORDER_ID ==="

# Get latest payment intent from Stripe
PI_ID=$(stripe charges list --limit 1 | grep '"payment_intent"' | awk -F'"' '{print $4}')

echo "Latest Payment Intent: $PI_ID"

if [ -z "$PI_ID" ]; then
  echo "❌ Could not get payment intent from Stripe"
  exit 1
fi

echo ""
echo "Updating order #$ORDER_ID with payment_intent_id=$PI_ID"

curl -X POST "http://localhost:8000/webhook/manual-confirm/$ORDER_ID" \
  -H "Content-Type: application/json" \
  -d "{\"payment_intent_id\": \"$PI_ID\"}"

echo ""
echo ""
echo "=== Verifying update ==="
curl -s "http://localhost:8000/orders/$ORDER_ID" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1YjhhNjZiYi1jNjczLTQzNzEtYmNmNi0zNDNiNDVjZWRkYTciLCJyb2xlIjoidXNlciIsImV4cCI6MTc2NTYwODQ0Mn0.i9mLhRasDW9GCFKbCt5XGnjs5YYSgkM1o3ujJRTs87k" \
  | jq '{id, status, payment_intent_id, total_amount, subtotal, shipping_fee}'

echo ""
echo "✅ Order fixed! Now you can test refund:"
echo "   ./test_refund_simple.sh $ORDER_ID"
