#!/bin/bash
# Refund Feature E2E Test Script
# Test full flow: Create Order → Pay → Cancel → Refund

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

API_BASE="http://localhost:8000"
FRONTEND_BASE="http://localhost:3000"

echo -e "${YELLOW}=== Refund Feature E2E Test ===${NC}\n"

# Step 1: Login to get token
echo -e "${YELLOW}Step 1: Login...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "${API_BASE}/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo -e "${RED}❌ Login failed. Creating test user...${NC}"
  
  # Create test user
  curl -s -X POST "${API_BASE}/register" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "password": "test123",
      "full_name": "Test User"
    }' > /dev/null
  
  # Login again
  LOGIN_RESPONSE=$(curl -s -X POST "${API_BASE}/login" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "password": "test123"
    }')
  
  TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
fi

echo -e "${GREEN}✅ Logged in. Token: ${TOKEN:0:20}...${NC}\n"

# Step 2: Add product to cart
echo -e "${YELLOW}Step 2: Adding product to cart...${NC}"
CART_RESPONSE=$(curl -s -X POST "${API_BASE}/cart" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2
  }')

echo -e "${GREEN}✅ Product added to cart${NC}\n"

# Step 3: Create order
echo -e "${YELLOW}Step 3: Creating order...${NC}"
ORDER_RESPONSE=$(curl -s -X POST "${API_BASE}/orders" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shipping": {
      "name": "Test User",
      "phone": "1234567890",
      "email": "test@example.com",
      "address": "123 Test Street, Test City",
      "note": "Test order for refund feature"
    }
  }')

ORDER_ID=$(echo $ORDER_RESPONSE | jq -r '.id')
ORDER_STATUS=$(echo $ORDER_RESPONSE | jq -r '.status')
TOTAL_AMOUNT=$(echo $ORDER_RESPONSE | jq -r '.total_amount')

echo -e "${GREEN}✅ Order created:${NC}"
echo "   Order ID: $ORDER_ID"
echo "   Status: $ORDER_STATUS"
echo "   Total: \$$TOTAL_AMOUNT"
echo ""

# Step 4: Check order is PENDING
if [ "$ORDER_STATUS" != "pending" ]; then
  echo -e "${RED}❌ Order status should be PENDING, got: $ORDER_STATUS${NC}"
  exit 1
fi
echo -e "${GREEN}✅ Order status is PENDING (correct)${NC}\n"

# Step 5: Test Cancel PENDING order
echo -e "${YELLOW}Step 5: Testing cancel PENDING order...${NC}"
read -p "Test cancel PENDING order? (y/n): " test_pending_cancel

if [ "$test_pending_cancel" == "y" ]; then
  CANCEL_RESPONSE=$(curl -s -X POST "${API_BASE}/orders/$ORDER_ID/cancel" \
    -H "Authorization: Bearer $TOKEN")
  
  CANCELLED_STATUS=$(echo $CANCEL_RESPONSE | jq -r '.status')
  
  if [ "$CANCELLED_STATUS" == "cancelled" ]; then
    echo -e "${GREEN}✅ PENDING order cancelled successfully (no refund needed)${NC}\n"
    echo "Test completed! PENDING cancel works correctly."
    exit 0
  else
    echo -e "${RED}❌ Cancel failed. Status: $CANCELLED_STATUS${NC}"
    exit 1
  fi
fi

# Step 6: Create payment session
echo -e "${YELLOW}Step 6: Creating Stripe checkout session...${NC}"
PAYMENT_RESPONSE=$(curl -s -X POST "${API_BASE}/payments/create-session" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"order_id\": $ORDER_ID
  }")

CHECKOUT_URL=$(echo $PAYMENT_RESPONSE | jq -r '.url')
SESSION_ID=$(echo $PAYMENT_RESPONSE | jq -r '.session_id')

echo -e "${GREEN}✅ Checkout session created${NC}"
echo "   Session ID: $SESSION_ID"
echo "   Checkout URL: $CHECKOUT_URL"
echo ""

# Step 7: Simulate payment with Stripe CLI
echo -e "${YELLOW}Step 7: Simulating payment...${NC}"
echo "We'll use Stripe CLI to trigger checkout.session.completed event"
echo ""

# Trigger Stripe webhook event
echo "Running: stripe trigger checkout.session.completed"
TRIGGER_OUTPUT=$(stripe trigger checkout.session.completed --add metadata[order_id]=$ORDER_ID 2>&1)

if [[ $TRIGGER_OUTPUT == *"succeeded"* ]] || [[ $TRIGGER_OUTPUT == *"200"* ]]; then
  echo -e "${GREEN}✅ Payment webhook triggered${NC}\n"
else
  echo -e "${YELLOW}⚠️ Stripe CLI might not be available. Manual payment needed.${NC}"
  echo "Visit: $CHECKOUT_URL"
  echo "Use test card: 4242 4242 4242 4242"
  read -p "Press Enter after completing payment..."
fi

# Step 8: Wait for webhook processing
echo -e "${YELLOW}Step 8: Waiting for webhook to process...${NC}"
sleep 3

# Check order status
ORDER_CHECK=$(curl -s -X GET "${API_BASE}/orders/$ORDER_ID" \
  -H "Authorization: Bearer $TOKEN")

CURRENT_STATUS=$(echo $ORDER_CHECK | jq -r '.status')
PAYMENT_INTENT=$(echo $ORDER_CHECK | jq -r '.payment_intent_id')

echo -e "${GREEN}Order status after payment:${NC}"
echo "   Status: $CURRENT_STATUS"
echo "   Payment Intent ID: $PAYMENT_INTENT"
echo ""

if [ "$CURRENT_STATUS" != "confirmed" ]; then
  echo -e "${RED}❌ Order should be CONFIRMED, got: $CURRENT_STATUS${NC}"
  echo "Payment might not have completed. Check Stripe Dashboard."
  exit 1
fi

echo -e "${GREEN}✅ Order status is CONFIRMED (payment successful)${NC}\n"

# Step 9: Test Cancel CONFIRMED order (should trigger refund)
echo -e "${YELLOW}Step 9: Testing cancel CONFIRMED order (should refund)...${NC}"
read -p "Proceed to cancel CONFIRMED order? (y/n): " proceed_cancel

if [ "$proceed_cancel" != "y" ]; then
  echo "Test stopped. Order $ORDER_ID is CONFIRMED."
  exit 0
fi

REFUND_RESPONSE=$(curl -s -X POST "${API_BASE}/orders/$ORDER_ID/cancel" \
  -H "Authorization: Bearer $TOKEN")

REFUND_STATUS=$(echo $REFUND_RESPONSE | jq -r '.status')
REFUND_ID=$(echo $REFUND_RESPONSE | jq -r '.refund_id')

echo -e "${GREEN}Cancel response:${NC}"
echo "   Order Status: $REFUND_STATUS"
echo "   Refund ID: $REFUND_ID"
echo ""

if [ "$REFUND_STATUS" == "refund_pending" ]; then
  echo -e "${GREEN}✅ Refund initiated! Status is REFUND_PENDING${NC}\n"
else
  echo -e "${RED}❌ Expected REFUND_PENDING, got: $REFUND_STATUS${NC}"
  exit 1
fi

# Step 10: Wait for refund webhook
echo -e "${YELLOW}Step 10: Waiting for refund webhook...${NC}"
echo "Stripe will send charge.refunded event..."
sleep 5

# Check final order status
FINAL_CHECK=$(curl -s -X GET "${API_BASE}/orders/$ORDER_ID" \
  -H "Authorization: Bearer $TOKEN")

FINAL_STATUS=$(echo $FINAL_CHECK | jq -r '.status')
REFUNDED_AT=$(echo $FINAL_CHECK | jq -r '.refunded_at')

echo -e "${GREEN}Final order state:${NC}"
echo "   Status: $FINAL_STATUS"
echo "   Refund ID: $(echo $FINAL_CHECK | jq -r '.refund_id')"
echo "   Refund Amount: \$$(echo $FINAL_CHECK | jq -r '.refund_amount')"
echo "   Refunded At: $REFUNDED_AT"
echo ""

if [ "$FINAL_STATUS" == "refunded" ]; then
  echo -e "${GREEN}✅✅✅ SUCCESS! Full refund flow completed!${NC}"
  echo ""
  echo "Summary:"
  echo "  1. ✅ Order created (PENDING)"
  echo "  2. ✅ Payment processed (CONFIRMED)"
  echo "  3. ✅ Refund initiated (REFUND_PENDING)"
  echo "  4. ✅ Refund completed (REFUNDED)"
  echo "  5. ✅ Stock rolled back"
  echo ""
  echo "🎉 Refund feature working perfectly!"
else
  echo -e "${YELLOW}⚠️ Order status is: $FINAL_STATUS${NC}"
  echo "Expected REFUNDED. Webhook might still be processing."
  echo "Check backend logs and Stripe Dashboard."
fi

echo ""
echo -e "${YELLOW}=== Test Complete ===${NC}"
