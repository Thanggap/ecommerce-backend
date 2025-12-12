"""
Script test Stripe Webhook locally
Dùng để simulate webhook event và test flow update order status
"""

import requests
import json
import hmac
import hashlib
import time
import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = "http://localhost:8000/webhook/stripe"
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_test_secret")

def create_test_webhook_payload(order_id: int):
    """Tạo fake webhook payload cho testing"""
    return {
        "id": f"evt_test_{int(time.time())}",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": f"cs_test_{int(time.time())}",
                "object": "checkout.session",
                "payment_status": "paid",
                "metadata": {
                    "order_id": str(order_id)
                }
            }
        }
    }

def generate_stripe_signature(payload: str, secret: str):
    """Generate Stripe webhook signature"""
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload}"
    signature = hmac.new(
        secret.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"

def test_webhook(order_id: int):
    """Send test webhook to local server"""
    print(f"\n=== Testing Webhook for Order #{order_id} ===")
    
    payload = create_test_webhook_payload(order_id)
    payload_str = json.dumps(payload)
    
    # Generate signature
    signature = generate_stripe_signature(payload_str, WEBHOOK_SECRET)
    
    headers = {
        "Content-Type": "application/json",
        "stripe-signature": signature
    }
    
    print(f"Sending webhook to: {WEBHOOK_URL}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(WEBHOOK_URL, data=payload_str, headers=headers)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print(f"\n✅ Webhook processed successfully!")
            print(f"Now check order #{order_id} status in database")
        else:
            print(f"\n❌ Webhook failed!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Make sure backend server is running on localhost:8000")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python test_webhook_local.py <order_id>")
        print("Example: python test_webhook_local.py 5")
        sys.exit(1)
    
    order_id = int(sys.argv[1])
    test_webhook(order_id)
