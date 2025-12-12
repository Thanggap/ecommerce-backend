"""
Auto-Delivery Service - Background job to auto-mark shipped orders as delivered after 14 days
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload

from app.db import get_db_session
from app.models.sqlalchemy.order import Order, OrderStatus


class AutoDeliveryService:
    """Handle automatic delivery confirmation for shipped orders"""
    
    @staticmethod
    def process_auto_delivery(dry_run: bool = False) -> dict:
        """
        Find all orders with status=SHIPPED and shipped_at > 14 days ago
        Auto-update them to DELIVERED
        
        Args:
            dry_run: If True, only return count without updating (for testing)
        
        Returns:
            dict with processing results
        """
        db = get_db_session()
        try:
            # Calculate 14 days ago from now
            cutoff_date = datetime.utcnow() - timedelta(days=14)
            
            # Find eligible orders
            eligible_orders = db.query(Order).filter(
                Order.status == OrderStatus.SHIPPED.value,
                Order.shipped_at.isnot(None),
                Order.shipped_at <= cutoff_date
            ).all()
            
            if dry_run:
                return {
                    "dry_run": True,
                    "eligible_count": len(eligible_orders),
                    "order_ids": [order.id for order in eligible_orders]
                }
            
            # Update orders to DELIVERED
            updated_count = 0
            updated_order_ids = []
            
            for order in eligible_orders:
                order.status = OrderStatus.DELIVERED.value
                order.delivered_at = datetime.utcnow()
                updated_count += 1
                updated_order_ids.append(order.id)
                
                print(f"[Auto-Delivery] Order {order.id} auto-marked as delivered (shipped {order.shipped_at})")
            
            db.commit()
            
            print(f"[Auto-Delivery] Processed {updated_count} orders")
            
            return {
                "success": True,
                "updated_count": updated_count,
                "updated_order_ids": updated_order_ids,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            db.rollback()
            print(f"[Auto-Delivery] Error processing auto-delivery: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            db.close()
    
    @staticmethod
    def get_eligible_orders_count() -> int:
        """Get count of orders eligible for auto-delivery (for monitoring)"""
        db = get_db_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=14)
            
            count = db.query(Order).filter(
                Order.status == OrderStatus.SHIPPED.value,
                Order.shipped_at.isnot(None),
                Order.shipped_at <= cutoff_date
            ).count()
            
            return count
        finally:
            db.close()
