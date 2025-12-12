#!/bin/bash

# Complete return flow test
BASE_URL="http://localhost:8000"
USER_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1YjhhNjZiYi1jNjczLTQzNzEtYmNmNi0zNDNiNDVjZWRkYTciLCJyb2xlIjoidXNlciIsImV4cCI6MTc2NTYwODQ0Mn0.i9mLhRasDW9GCFKbCt5XGnjs5YYSgkM1o3ujJRTs87k"
ORDER_ID=12

echo "========================================="
echo "RETURN FLOW TEST - Order #$ORDER_ID"
echo "========================================="

echo ""
echo "Step 0: Get ADMIN token"
read -p "Enter admin token: " ADMIN_TOKEN

if [ -z "$ADMIN_TOKEN" ]; then
  echo "❌ No admin token provided"
  exit 1
fi

echo ""
echo "=== Step 1: Check order status BEFORE (as user) ==="
ORDER_BEFORE=$(curl -s -X GET "$BASE_URL/orders/$ORDER_ID" \
  -H "Authorization: Bearer $USER_TOKEN")

echo "$ORDER_BEFORE" | jq '{id, status, return_requested_at, refunded_at, updated_at}'

STATUS_INITIAL=$(echo "$ORDER_BEFORE" | jq -r '.status')
echo "Initial status: $STATUS_INITIAL"

echo ""
echo "=== Step 2: Admin marks order as DELIVERED ==="
ADMIN_UPDATE=$(curl -s -X PUT "$BASE_URL/admin/orders/$ORDER_ID/status" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "delivered"}')

echo "$ADMIN_UPDATE" | jq '{id, status, updated_at}'

echo ""
echo "=== Step 3: Verify order is now DELIVERED ==="
ORDER_DELIVERED=$(curl -s -X GET "$BASE_URL/orders/$ORDER_ID" \
  -H "Authorization: Bearer $USER_TOKEN")

STATUS_DELIVERED=$(echo "$ORDER_DELIVERED" | jq -r '.status')
echo "Status after admin update: $STATUS_DELIVERED"

if [ "$STATUS_DELIVERED" != "delivered" ]; then
  echo "❌ Failed to update to DELIVERED status"
  exit 1
fi

echo "✅ Order is now DELIVERED"

echo ""
echo "=== Step 4: User requests return ==="
REQUEST_RETURN=$(curl -s -X POST "$BASE_URL/orders/$ORDER_ID/cancel" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json")

echo "$REQUEST_RETURN" | jq '{id, status, return_requested_at, refund_reason}'

echo ""
echo "=== Step 5: Verify status changed to RETURN_REQUESTED ==="
ORDER_AFTER=$(curl -s -X GET "$BASE_URL/orders/$ORDER_ID" \
  -H "Authorization: Bearer $USER_TOKEN")

echo "$ORDER_AFTER" | jq '{id, status, return_requested_at, refunded_at, updated_at}'

STATUS_AFTER=$(echo "$ORDER_AFTER" | jq -r '.status')
RETURN_REQUESTED_AT=$(echo "$ORDER_AFTER" | jq -r '.return_requested_at')

echo ""
echo "========================================="
echo "RESULTS"
echo "========================================="
echo "Initial status:        $STATUS_INITIAL"
echo "After admin update:    $STATUS_DELIVERED"
echo "After user request:    $STATUS_AFTER"
echo "Return requested at:   $RETURN_REQUESTED_AT"

if [ "$STATUS_AFTER" == "return_requested" ] && [ "$RETURN_REQUESTED_AT" != "null" ]; then
  echo ""
  echo "✅ SUCCESS: Status updated correctly"
  echo "   delivered → return_requested"
  echo "   return_requested_at timestamp set: $RETURN_REQUESTED_AT"
else
  echo ""
  echo "❌ FAILED: Status did not update as expected"
  echo "   Expected: return_requested"
  echo "   Got: $STATUS_AFTER"
fi
