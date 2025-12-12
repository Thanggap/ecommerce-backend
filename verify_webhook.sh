#!/bin/bash

# Quick test: Create order and verify webhook saves payment_intent_id
BASE_URL="http://localhost:8000"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1YjhhNjZiYi1jNjczLTQzNzEtYmNmNi0zNDNiNDVjZWRkYTciLCJyb2xlIjoidXNlciIsImV4cCI6MTc2NTYwODQ0Mn0.i9mLhRasDW9GCFKbCt5XGnjs5YYSgkM1o3ujJRTs87k"

echo "Quick test: Verify webhook saves payment_intent_id"
echo ""

# Get latest order ID
LATEST_ORDER=$(curl -s "$BASE_URL/orders" -H "Authorization: Bearer $TOKEN" | jq 'sort_by(.id) | reverse | .[0]')
LATEST_ID=$(echo "$LATEST_ORDER" | jq -r '.id')
LATEST_STATUS=$(echo "$LATEST_ORDER" | jq -r '.status')
LATEST_PI=$(echo "$LATEST_ORDER" | jq -r '.payment_intent_id')

echo "Latest order: #$LATEST_ID"
echo "Status: $LATEST_STATUS"
echo "Payment Intent: $LATEST_PI"
echo ""

if [ "$LATEST_STATUS" == "confirmed" ] && [ "$LATEST_PI" != "null" ]; then
  echo "✅ Code mới đang chạy đúng!"
  echo "   Webhook đã save payment_intent_id"
  echo ""
  echo "Giờ test cancel/refund với order này:"
  echo "   ./test_refund_simple.sh $LATEST_ID"
elif [ "$LATEST_STATUS" == "confirmed" ] && [ "$LATEST_PI" == "null" ]; then
  echo "❌ Code cũ vẫn đang chạy!"
  echo "   Webhook KHÔNG save payment_intent_id"
  echo "   Cần restart backend!"
elif [ "$LATEST_STATUS" == "pending" ]; then
  echo "⏳ Order vẫn đang pending (chưa payment)"
  echo "   Hãy tạo order mới và checkout để test"
else
  echo "Order status: $LATEST_STATUS"
fi
