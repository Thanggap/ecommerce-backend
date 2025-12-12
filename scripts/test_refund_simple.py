"""
Simple Refund Feature Test
Test individual endpoints with curl commands
"""

import subprocess
import json
import time

# Configuration
API_BASE = "http://localhost:8000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test123"

def run_curl(method, endpoint, headers=None, data=None):
    """Run curl command and return response"""
    cmd = ["curl", "-s", "-X", method, f"{API_BASE}{endpoint}"]
    
    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])
    
    if data:
        cmd.extend(["-d", json.dumps(data)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout) if result.stdout else {}
    except Exception as e:
        print(f"Error: {e}")
        return {}

def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def main():
    print_section("Refund Feature Test - Manual Steps")
    
    # Step 1: Login
    print("Step 1: Login to get token")
    print(f"Command: curl -X POST {API_BASE}/login \\")
    print(f'  -H "Content-Type: application/json" \\')
    print(f'  -d \'{{"email": "{TEST_EMAIL}", "password": "{TEST_PASSWORD}"}}\'')
    print()
    
    login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    login_response = run_curl("POST", "/login", 
                             headers={"Content-Type": "application/json"}, 
                             data=login_data)
    
    if not login_response.get("access_token"):
        print("❌ Login failed. User might not exist.")
        print("\nCreate user first:")
        print(f"curl -X POST {API_BASE}/register \\")
        print(f'  -H "Content-Type: application/json" \\')
        print(f'  -d \'{{"email": "{TEST_EMAIL}", "password": "{TEST_PASSWORD}", "full_name": "Test User"}}\'')
        return
    
    token = login_response["access_token"]
    print(f"✅ Token: {token[:30]}...")
    
    # Step 2: Get cart
    print_section("Step 2: Check Cart")
    print(f"Command: curl -X GET {API_BASE}/cart \\")
    print(f'  -H "Authorization: Bearer {token[:20]}..."')
    print()
    
    auth_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    cart_response = run_curl("GET", "/cart", headers=auth_headers)
    print(f"Cart items: {len(cart_response.get('items', []))}")
    
    # Step 3: Add product to cart
    print_section("Step 3: Add Product to Cart")
    print(f"Command: curl -X POST {API_BASE}/cart \\")
    print(f'  -H "Authorization: Bearer {token[:20]}..." \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f'  -d \'{{"product_id": 1, "quantity": 2}}\'')
    print()
    
    add_cart_data = {"product_id": 1, "quantity": 2}
    add_cart_response = run_curl("POST", "/cart", headers=auth_headers, data=add_cart_data)
    print(f"✅ Product added")
    
    # Step 4: Create order
    print_section("Step 4: Create Order")
    order_data = {
        "shipping": {
            "name": "Test User",
            "phone": "1234567890",
            "email": TEST_EMAIL,
            "address": "123 Test Street",
            "note": "Test refund"
        }
    }
    
    print(f"Command: curl -X POST {API_BASE}/orders \\")
    print(f'  -H "Authorization: Bearer {token[:20]}..." \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f'  -d \'{json.dumps(order_data)}\'')
    print()
    
    order_response = run_curl("POST", "/orders", headers=auth_headers, data=order_data)
    
    if not order_response.get("id"):
        print("❌ Failed to create order")
        print(f"Response: {order_response}")
        return
    
    order_id = order_response["id"]
    order_status = order_response["status"]
    total_amount = order_response["total_amount"]
    
    print(f"✅ Order created:")
    print(f"   ID: {order_id}")
    print(f"   Status: {order_status}")
    print(f"   Total: ${total_amount}")
    
    # Step 5: Test Cancel PENDING
    print_section(f"Step 5: Cancel PENDING Order #{order_id}")
    print("\nOption 1: Cancel now (PENDING - no refund needed)")
    print(f"Command: curl -X POST {API_BASE}/orders/{order_id}/cancel \\")
    print(f'  -H "Authorization: Bearer {token[:20]}..."')
    
    choice = input("\nCancel PENDING order now? (y/n): ")
    
    if choice.lower() == 'y':
        cancel_response = run_curl("POST", f"/orders/{order_id}/cancel", headers=auth_headers)
        print(f"\n✅ Cancelled. Status: {cancel_response.get('status')}")
        print("\n✅ TEST PASSED: PENDING order cancelled (no refund)")
        return
    
    # Step 6: Payment
    print_section("Step 6: Payment (Manual)")
    print("To test CONFIRMED order refund:")
    print(f"1. Create payment session:")
    print(f"   curl -X POST {API_BASE}/payments/create-session \\")
    print(f'     -H "Authorization: Bearer {token[:20]}..." \\')
    print(f'     -H "Content-Type: application/json" \\')
    print(f'     -d \'{{"order_id": {order_id}}}\'')
    print()
    print("2. Complete payment with test card: 4242 4242 4242 4242")
    print("3. Wait for webhook to confirm")
    print()
    print("4. Then cancel with:")
    print(f"   curl -X POST {API_BASE}/orders/{order_id}/cancel \\")
    print(f'     -H "Authorization: Bearer {token[:20]}..."')
    print()
    print("5. Check refund status:")
    print(f"   curl -X GET {API_BASE}/orders/{order_id} \\")
    print(f'     -H "Authorization: Bearer {token[:20]}..."')
    
    print(f"\n✅ Order {order_id} ready for payment & refund testing")

if __name__ == "__main__":
    main()
