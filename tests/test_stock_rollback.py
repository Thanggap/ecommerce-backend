import pytest
from app.services.order_service import OrderService
from app.models.sqlalchemy import Order, OrderItem, Product


class TestOrderServiceStockRollback:
    """Test OrderService rollback_stock_on_cancel"""

    def test_rollback_stock_success(self, db_session, sample_product):
        """Test hoàn lại stock thành công khi hủy đơn"""
        # Create order with items
        order = Order(
            user_id="test-user",
            shipping_name="Test User",
            shipping_phone="123456789",
            shipping_email="test@example.com",
            shipping_address="Test Address",
            subtotal=500.0,
            shipping_fee=10.0,
            total_amount=510.0,
            status="confirmed"
        )
        db_session.add(order)

        # Add order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=sample_product.id,
            quantity=5,
            unit_price=100.0,
            total_price=500.0
        )
        db_session.add(order_item)
        db_session.commit()

        # Initial stock = 50
        initial_stock = sample_product.stock

        # Rollback stock
        OrderService.rollback_stock_on_cancel(order.id)

        # Verify stock added back
        updated_product = db_session.query(Product).filter(Product.id == sample_product.id).first()
        assert updated_product.stock == initial_stock + 5

    def test_rollback_stock_order_not_found(self, db_session):
        """Test rollback stock với order không tồn tại"""
        # Should not raise exception, just log
        OrderService.rollback_stock_on_cancel(99999)

        # No assertion needed, just ensure no exception

    def test_rollback_stock_product_not_found(self, db_session):
        """Test rollback stock khi product không tồn tại"""
        # Create order with non-existent product
        order = Order(
            user_id="test-user",
            shipping_name="Test User",
            shipping_phone="123456789",
            shipping_email="test@example.com",
            shipping_address="Test Address",
            subtotal=500.0,
            shipping_fee=10.0,
            total_amount=510.0,
            status="confirmed"
        )
        db_session.add(order)

        order_item = OrderItem(
            order_id=order.id,
            product_id=99999,  # Non-existent product
            quantity=5,
            unit_price=100.0,
            total_price=500.0
        )
        db_session.add(order_item)
        db_session.commit()

        # Should not raise exception, just log
        OrderService.rollback_stock_on_cancel(order.id)