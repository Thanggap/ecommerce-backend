"""
Check Order Status trong Database
Dùng để debug xem order có được update status hay không
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_db_session
from app.models.sqlalchemy.order import Order
from sqlalchemy import desc

def check_order_status(order_id=None):
    """Check status của order trong database"""
    db = get_db_session()
    try:
        if order_id:
            # Check specific order
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                print(f"\n=== Order #{order.id} ===")
                print(f"User ID: {order.user_id}")
                print(f"Status: {order.status}")
                print(f"Total: ${order.total_amount}")
                print(f"Created: {order.created_at}")
                print(f"Updated: {order.updated_at}")
                print(f"Shipping: {order.shipping_name}")
                print(f"Email: {order.shipping_email}")
            else:
                print(f"Order #{order_id} not found")
        else:
            # Show recent orders
            orders = db.query(Order).order_by(desc(Order.created_at)).limit(10).all()
            print(f"\n=== Recent 10 Orders ===")
            print(f"{'ID':<5} {'Status':<12} {'Total':<10} {'Created':<20} {'Updated':<20}")
            print("-" * 80)
            for order in orders:
                print(f"{order.id:<5} {order.status:<12} ${order.total_amount:<9.2f} {str(order.created_at):<20} {str(order.updated_at):<20}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        order_id = int(sys.argv[1])
        check_order_status(order_id)
    else:
        check_order_status()
