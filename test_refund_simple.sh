#!/bin/bash

# Simple refund test - assumes you'll pay via UI
BASE_URL="http://localhost:8000"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1YjhhNjZiYi1jNjczLTQzNzEtYmNmNi0zNDNiNDVjZWRkYTciLCJyb2xlIjoidXNlciIsImV4cCI6MTc2NTYwODQ0Mn0.i9mLhRasDW9GCFKbCt5XGnjs5YYSgkM1o3ujJRTs87k"

if [ -z "$1" ]; then
  echo "Usage: $0 <order_id>"
  echo ""
  echo "This script tests the refund flow for an existing CONFIRMED order"
  echo ""
  echo "Steps:"
  echo "1. Create order via UI and complete payment"
  echo "2. Note the order ID"
  echo "3. Run: $0 <order_id>"
  exit 1
fi

ORDER_ID=$1

echo "========================================="
echo "REFUND FLOW TEST FOR ORDER #$ORDER_ID"
echo "========================================="

echo ""
echo "=== Step 1: Check order status BEFORE cancel ==="
ORDER_BEFORE=$(curl -s -X GET "$BASE_URL/orders/$ORDER_ID" \
  -H "Authorization: Bearer $TOKEN")

STATUS_BEFORE=$(echo "$ORDER_BEFORE" | jq -r '.status')
PAYMENT_INTENT=$(echo "$ORDER_BEFORE" | jq -r '.payment_intent_id')
TOTAL_AMOUNT=$(echo "$ORDER_BEFORE" | jq -r '.total_amount')
SUBTOTAL=$(echo "$ORDER_BEFORE" | jq -r '.subtotal')
SHIPPING_FEE=$(echo "$ORDER_BEFORE" | jq -r '.shipping_fee')

echo "Order #$ORDER_ID:"
echo "  Status: $STATUS_BEFORE"
echo "  Total: \$$TOTAL_AMOUNT"
echo "  Subtotal: \$$SUBTOTAL"
echo "  Shipping: \$$SHIPPING_FEE"
echo "  Payment Intent: $PAYMENT_INTENT"

if [ "$STATUS_BEFORE" != "confirmed" ]; then
  echo ""
  echo "❌ Order must be CONFIRMED to test refund"
  echo "   Current status: $STATUS_BEFORE"
  exit 1
fi

if [ "$PAYMENT_INTENT" == "null" ] || [ -z "$PAYMENT_INTENT" ]; then
  echo ""
  echo "❌ No payment_intent_id found"
  echo "   Order may not have been paid via Stripe"
  exit 1
fi

echo ""
read -p "Cancel this order? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
  echo "Cancelled."
  exit 0
fi

echo ""
echo "=== Step 2: Cancel order (initiate refund) ==="
CANCEL_RESPONSE=$(curl -s -X POST "$BASE_URL/orders/$ORDER_ID/cancel" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "$CANCEL_RESPONSE" | jq '{id, status, refund_id, refund_amount}'

echo ""
echo "=== Step 3: Wait for refund webhook (5 seconds) ==="
sleep 5

echo ""
echo "=== Step 4: Check final status ==="
ORDER_AFTER=$(curl -s -X GET "$BASE_URL/orders/$ORDER_ID" \
  -H "Authorization: Bearer $TOKEN")

STATUS_AFTER=$(echo "$ORDER_AFTER" | jq -r '.status')
REFUND_ID=$(echo "$ORDER_AFTER" | jq -r '.refund_id')
REFUND_AMOUNT=$(echo "$ORDER_AFTER" | jq -r '.refund_amount')
REFUNDED_AT=$(echo "$ORDER_AFTER" | jq -r '.refunded_at')

echo ""
echo "========================================="
echo "RESULTS"
echo "========================================="
echo "Order ID: $ORDER_ID"
echo "Status: $STATUS_BEFORE → $STATUS_AFTER"
echo "Total Amount: \$$TOTAL_AMOUNT"
echo "Refund ID: $REFUND_ID"
echo "Refund Amount: \$$REFUND_AMOUNT"
echo "Refunded At: $REFUNDED_AT"

echo ""
if [ "$STATUS_AFTER" == "refunded" ]; then
  echo "✅ SUCCESS: Order refunded!"
  
  # Check refund amount (should be 100% for CONFIRMED cancel)
  if (( $(echo "$REFUND_AMOUNT == $TOTAL_AMOUNT" | bc -l) )); then
    echo "✅ Refund amount: 100% (includes shipping)"
  else
    echo "⚠️  Refund amount mismatch"
    echo "   Expected: \$$TOTAL_AMOUNT"
    echo "   Got: \$$REFUND_AMOUNT"
  fi
  
elif [ "$STATUS_AFTER" == "refund_pending" ]; then
  echo "⏳ Status: REFUND_PENDING"
  echo ""
  echo "Webhook may still be processing. Options:"
  echo ""
  echo "1. Wait a few more seconds and check order detail page"
  echo "2. Check Stripe CLI terminal for webhook events"
  echo "3. Manually trigger refund webhook:"
  echo "   curl -X POST $BASE_URL/webhook/manual-refund/$REFUND_ID"
  
else
  echo "❌ Unexpected status: $STATUS_AFTER"
fi
