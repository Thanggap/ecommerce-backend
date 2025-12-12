#!/bin/bash

BASE_URL="http://localhost:8000"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1YjhhNjZiYi1jNjczLTQzNzEtYmNmNi0zNDNiNDVjZWRkYTciLCJyb2xlIjoidXNlciIsImV4cCI6MTc2NTYwODQ0Mn0.i9mLhRasDW9GCFKbCt5XGnjs5YYSgkM1o3ujJRTs87k"

echo "========================================="
echo "FULL REFUND FLOW TEST"
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
      "note": "Test order for refund flow"
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
echo "=== Step 3: Create Stripe checkout session ==="
CHECKOUT_RESPONSE=$(curl -s -X POST "$BASE_URL/payments/create-session" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"order_id\": $ORDER_ID}")

CHECKOUT_URL=$(echo "$CHECKOUT_RESPONSE" | jq -r '.checkout_url')
SESSION_ID=$(echo "$CHECKOUT_RESPONSE" | jq -r '.session_id')

echo "Checkout session created: $SESSION_ID"
echo "Checkout URL: $CHECKOUT_URL"

echo ""
echo "=== Step 3.1: Trigger payment completion via Stripe CLI ==="
stripe trigger checkout.session.completed --override checkout_session:id=$SESSION_ID --override checkout_session:metadata[order_id]=$ORDER_ID

echo ""
echo "=== Step 4: Verify payment confirmed ==="
sleep 3  # Wait for webhook to process

ORDER_AFTER_PAYMENT=$(curl -s -X GET "$BASE_URL/orders/$ORDER_ID" \
  -H "Authorization: Bearer $TOKEN")

STATUS_AFTER_PAYMENT=$(echo "$ORDER_AFTER_PAYMENT" | jq -r '.status')
PAYMENT_INTENT=$(echo "$ORDER_AFTER_PAYMENT" | jq -r '.payment_intent_id')

echo "Order status: $STATUS_AFTER_PAYMENT"
echo "Payment intent: $PAYMENT_INTENT"

if [ "$STATUS_AFTER_PAYMENT" != "confirmed" ]; then
  echo "❌ Order not confirmed. Current status: $STATUS_AFTER_PAYMENT"
  echo "Full order details:"
  echo "$ORDER_AFTER_PAYMENT" | jq '.'
  exit 1
fi

if [ "$PAYMENT_INTENT" == "null" ] || [ -z "$PAYMENT_INTENT" ]; then
  echo "❌ No payment_intent_id saved!"
  exit 1
fi

echo "✅ Payment confirmed with payment_intent: $PAYMENT_INTENT"

echo ""
echo "=== Step 5: Cancel order (trigger refund) ==="
CANCEL_RESPONSE=$(curl -s -X POST "$BASE_URL/orders/$ORDER_ID/cancel" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "$CANCEL_RESPONSE" | jq '{id, status, refund_id, refund_amount}'

echo ""
echo "=== Step 6: Wait for refund webhook ==="
sleep 3

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
echo "Final Status: $STATUS_FINAL"
echo "Refund ID: $REFUND_ID"
echo "Refund Amount: \$$REFUND_AMOUNT"
echo "Refunded At: $REFUNDED_AT"

if [ "$STATUS_FINAL" == "refunded" ]; then
  echo ""
  echo "✅ SUCCESS: Order fully refunded!"
  
  # Check if refund amount is correct (should be full amount for CONFIRMED cancel)
  if [ "$REFUND_AMOUNT" == "$TOTAL_AMOUNT" ]; then
    echo "✅ Refund amount correct: Full refund (100%)"
  else
    echo "⚠️  Refund amount mismatch: Expected \$$TOTAL_AMOUNT, Got \$$REFUND_AMOUNT"
  fi
elif [ "$STATUS_FINAL" == "refund_pending" ]; then
  echo ""
  echo "⏳ Refund pending (webhook may be delayed)"
  echo "Check Stripe CLI logs for webhook events"
else
  echo ""
  echo "❌ FAILED: Unexpected status: $STATUS_FINAL"
fi
