#!/bin/bash

# Test return request flow
BASE_URL="http://localhost:8000"

echo "=== Step 1: Login ==="
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "thangenz0507@gmail.com", "password": "111111"}')

echo "Login response: $LOGIN_RESPONSE"

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  exit 1
fi

echo "✅ Token: ${TOKEN:0:20}..."

echo ""
echo "=== Step 2: Get user orders ==="
ORDERS=$(curl -s -X GET "$BASE_URL/orders/my-orders" \
  -H "Authorization: Bearer $TOKEN")

echo "Orders: $ORDERS" | jq '.'

echo ""
echo "=== Step 3: Request return for order (enter order ID) ==="
read -p "Enter order ID to request return: " ORDER_ID

if [ -z "$ORDER_ID" ]; then
  echo "No order ID provided, exiting"
  exit 0
fi

echo ""
echo "=== Step 4: Check order status BEFORE request ==="
ORDER_BEFORE=$(curl -s -X GET "$BASE_URL/orders/$ORDER_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Order before:" | jq '.'
echo $ORDER_BEFORE | jq '{id, status, return_requested_at, refunded_at}'

echo ""
echo "=== Step 5: Request return ==="
CANCEL_RESPONSE=$(curl -s -X POST "$BASE_URL/orders/$ORDER_ID/cancel" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Product not as expected"}')

echo "Cancel response: $CANCEL_RESPONSE" | jq '.'

echo ""
echo "=== Step 6: Check order status AFTER request ==="
ORDER_AFTER=$(curl -s -X GET "$BASE_URL/orders/$ORDER_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "Order after:" | jq '.'
echo $ORDER_AFTER | jq '{id, status, return_requested_at, refunded_at, refund_reason}'

echo ""
echo "=== Comparison ==="
STATUS_BEFORE=$(echo $ORDER_BEFORE | jq -r '.status')
STATUS_AFTER=$(echo $ORDER_AFTER | jq -r '.status')

echo "Status BEFORE: $STATUS_BEFORE"
echo "Status AFTER:  $STATUS_AFTER"

if [ "$STATUS_BEFORE" == "delivered" ] && [ "$STATUS_AFTER" == "return_requested" ]; then
  echo "✅ Status updated successfully: delivered → return_requested"
else
  echo "⚠️  Status change: $STATUS_BEFORE → $STATUS_AFTER"
fi
