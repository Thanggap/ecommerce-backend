#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1YjhhNjZiYi1jNjczLTQzNzEtYmNmNi0zNDNiNDVjZWRkYTciLCJyb2xlIjoidXNlciIsImV4cCI6MTc2NTYwODQ0Mn0.i9mLhRasDW9GCFKbCt5XGnjs5YYSgkM1o3ujJRTs87k"

echo "=== All user orders with payment details ==="
curl -s -X GET "http://localhost:8000/orders" \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {id, status, payment_intent_id, refund_id, created_at: .created_at[:19], updated_at: .updated_at[:19]}'
