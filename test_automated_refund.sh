#!/bin/bash

BASE_URL="http://localhost:8000"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1YjhhNjZiYi1jNjczLTQzNzEtYmNmNi0zNDNiNDVjZWRkYTciLCJyb2xlIjoidXNlciIsImV4cCI6MTc2NTYwODQ0Mn0.i9mLhRasDW9GCFKbCt5XGnjs5YYSgkM1o3ujJRTs87k"

echo "========================================="
echo "FULL REFUND FLOW TEST (AUTOMATED)"
echo "========================================="

echo ""
echo "=== Step 1: Add product to cart ==="
CART_RESPONSE=$(curl -s -X POST "$BASE_URL/cart" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 12,
    "quantity": 1,
    "size": "30 servings"
  }')

echo "$CART_RESPONSE" | jq '{total_items, total_price}'

echo ""
echo "=== Step 2: Create order ==="
ORDER_RESPONSE=$(curl -s -X POST "$BASE_URL/orders" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shipping": {
      "name": "Test User",
      "phone": "0123456789",
      "email": "test@example.com",
      "address": "123 Test Street",
      "note": "Automated test order"
    }
  }')

ORDER_ID=$(echo "$ORDER_RESPONSE" | jq -r '.id')
TOTAL_AMOUNT=$(echo "$ORDER_RESPONSE" | jq -r '.total_amount')
SUBTOTAL=$(echo "$ORDER_RESPONSE" | jq -r '.subtotal')
SHIPPING_FEE=$(echo "$ORDER_RESPONSE" | jq -r '.shipping_fee')

echo "Order created:"
echo "$ORDER_RESPONSE" | jq '{id, status, total_amount, subtotal, shipping_fee}'

if [ "$ORDER_ID" == "null" ] || [ -z "$ORDER_ID" ]; then
  echo "❌ Failed to create order"
  exit 1
fi

echo ""
echo "Order #$ORDER_ID created: Total=$TOTAL_AMOUNT (Subtotal=$SUBTOTAL + Shipping=$SHIPPING_FEE)"

echo ""
echo "=== Step 3: Create and confirm payment via Stripe ==="

# Convert to cents
AMOUNT_CENTS=$(echo "$TOTAL_AMOUNT * 100 / 1" | bc)

echo "Creating PaymentIntent for $AMOUNT_CENTS cents..."

# Create PaymentIntent
PI_RESPONSE=$(stripe payment_intents create \
  --amount=$AMOUNT_CENTS \
  --currency=usd \
  --payment-method=pm_card_visa \
  --confirm=true \
  --return-url=http://localhost:3000 \
  --metadata[order_id]=$ORDER_ID)

PAYMENT_INTENT_ID=$(echo "$PI_RESPONSE" | jq -r '.id')
PI_STATUS=$(echo "$PI_RESPONSE" | jq -r '.status')

echo "Payment Intent created: $PAYMENT_INTENT_ID"
echo "Payment Intent status: $PI_STATUS"

if [ "$PAYMENT_INTENT_ID" == "null" ] || [ -z "$PAYMENT_INTENT_ID" ]; then
  echo "❌ Failed to create payment intent"
  exit 1
fi

echo ""
echo "=== Step 4: Manually update order with payment_intent_id ==="
# Since we bypassed Stripe Checkout, webhook won't fire
# We need to manually update the order

# Use SQL or direct DB update (for testing only)
echo "Simulating webhook: updating order status to CONFIRMED with payment_intent_id"

# Trigger webhook manually using our debug endpoint
curl -s -X POST "$BASE_URL/webhook/manual-confirm/$ORDER_ID" \
  -H "Content-Type: application/json" \
  -d "{\"payment_intent_id\": \"$PAYMENT_INTENT_ID\"}" > /dev/null

sleep 1

ORDER_AFTER_PAYMENT=$(curl -s -X GET "$BASE_URL/orders/$ORDER_ID" \
  -H "Authorization: Bearer $TOKEN")

STATUS_AFTER_PAYMENT=$(echo "$ORDER_AFTER_PAYMENT" | jq -r '.status')
SAVED_PAYMENT_INTENT=$(echo "$ORDER_AFTER_PAYMENT" | jq -r '.payment_intent_id')

echo "Order status: $STATUS_AFTER_PAYMENT"
echo "Saved payment_intent: $SAVED_PAYMENT_INTENT"

if [ "$STATUS_AFTER_PAYMENT" != "confirmed" ]; then
  echo "❌ Order not confirmed. Manually setting..."
  # Fallback: call confirm endpoint if exists
fi

echo "✅ Payment simulated with payment_intent: $PAYMENT_INTENT_ID"

echo ""
echo "=== Step 5: Cancel order (trigger refund) ==="
CANCEL_RESPONSE=$(curl -s -X POST "$BASE_URL/orders/$ORDER_ID/cancel" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

CANCEL_STATUS=$(echo "$CANCEL_RESPONSE" | jq -r '.status')
echo "Cancel response status: $CANCEL_STATUS"

if [ "$CANCEL_STATUS" == "null" ]; then
  echo "Cancel response:"
  echo "$CANCEL_RESPONSE" | jq '.'
fi

echo ""
echo "=== Step 6: Wait for refund webhook ==="
sleep 4

ORDER_AFTER_CANCEL=$(curl -s -X GET "$BASE_URL/orders/$ORDER_ID" \
  -H "Authorization: Bearer $TOKEN")

STATUS_FINAL=$(echo "$ORDER_AFTER_CANCEL" | jq -r '.status')
REFUND_ID=$(echo "$ORDER_AFTER_CANCEL" | jq -r '.refund_id')
REFUNDED_AT=$(echo "$ORDER_AFTER_CANCEL" | jq -r '.refunded_at')
REFUND_AMOUNT=$(echo "$ORDER_AFTER_CANCEL" | jq -r '.refund_amount')

echo ""
echo "========================================="
echo "RESULTS"
echo "========================================="
echo "Order ID: $ORDER_ID"
echo "Total Amount: \$$TOTAL_AMOUNT"
echo "Subtotal: \$$SUBTOTAL"
echo "Shipping Fee: \$$SHIPPING_FEE"
echo ""
echo "Payment Intent: $PAYMENT_INTENT_ID"
echo "Final Status: $STATUS_FINAL"
echo "Refund ID: $REFUND_ID"
echo "Refund Amount: \$$REFUND_AMOUNT"
echo "Refunded At: $REFUNDED_AT"

echo ""
if [ "$STATUS_FINAL" == "refunded" ]; then
  echo "✅ SUCCESS: Order fully refunded!"
  
  # Verify refund amount
  EXPECTED_REFUND=$TOTAL_AMOUNT
  if (( $(echo "$REFUND_AMOUNT == $EXPECTED_REFUND" | bc -l) )); then
    echo "✅ Refund amount correct: \$$REFUND_AMOUNT (100% - includes shipping)"
  else
    echo "⚠️  Refund amount: \$$REFUND_AMOUNT (Expected: \$$EXPECTED_REFUND)"
  fi
elif [ "$STATUS_FINAL" == "refund_pending" ]; then
  echo "⏳ Status: REFUND_PENDING"
  echo "   Webhook may still be processing. Check Stripe CLI terminal."
  echo ""
  echo "   To manually complete refund, run:"
  echo "   curl -X POST http://localhost:8000/webhook/manual-refund/$REFUND_ID"
elif [ "$STATUS_FINAL" == "confirmed" ]; then
  echo "❌ Order still CONFIRMED - refund may have failed"
  echo "Check backend logs for errors"
else
  echo "❌ Unexpected status: $STATUS_FINAL"
fi

echo ""
echo "Check Stripe CLI and backend logs for details."
