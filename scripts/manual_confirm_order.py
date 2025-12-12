"""
TEMPORARY FIX: Manually update order status to CONFIRMED
Dùng khi webhook chưa config được nhưng cần test tiếp

Usage:
    python scripts/manual_confirm_order.py <order_id>
    python scripts/manual_confirm_order.py 5
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.order_service import OrderService

def confirm_order(order_id: int):
    """Manually confirm order và deduct stock"""
    try:
        print(f"\n=== Manually Confirming Order #{order_id} ===")
        
        # Update status to confirmed
        result = OrderService.admin_update_order_status(order_id, "confirmed")
        print(f"✅ Order status updated to: {result.status}")
        
        # Deduct stock
        OrderService.deduct_stock_on_payment(order_id)
        print(f"✅ Stock deducted for order items")
        
        print(f"\n✅ SUCCESS - Order #{order_id} is now CONFIRMED")
        print(f"Total: ${result.total_amount}")
        print(f"Items: {len(result.items)}")
        
        return result
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manual_confirm_order.py <order_id>")
        print("Example: python manual_confirm_order.py 5")
        sys.exit(1)
    
    order_id = int(sys.argv[1])
    confirm_order(order_id)
