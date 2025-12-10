import pytest
from app.services.order_service import OrderService
from app.models.sqlalchemy import Order, OrderItem, Product


class TestAdminOrderStatusRollback:
    """Test admin update order status với stock rollback"""

    def test_admin_update_status_confirmed_to_cancelled_rollbacks_stock(self, db_session, sample_product):
        """Test admin đổi status từ confirmed → cancelled rollback stock"""
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

        # Admin update status to cancelled
        result = OrderService.admin_update_order_status(order.id, "cancelled")

        # Verify status changed
        assert result.status == "cancelled"

        # Verify stock rolled back
        updated_product = db_session.query(Product).filter(Product.id == sample_product.id).first()
        assert updated_product.stock == initial_stock + 5

    def test_admin_update_status_confirmed_to_refunded_rollbacks_stock(self, db_session, sample_product):
        """Test admin đổi status từ confirmed → refunded rollback stock"""
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
            quantity=3,
            unit_price=100.0,
            total_price=300.0
        )
        db_session.add(order_item)
        db_session.commit()

        # Initial stock = 50
        initial_stock = sample_product.stock

        # Admin update status to refunded
        result = OrderService.admin_update_order_status(order.id, "refunded")

        # Verify status changed
        assert result.status == "refunded"

        # Verify stock rolled back
        updated_product = db_session.query(Product).filter(Product.id == sample_product.id).first()
        assert updated_product.stock == initial_stock + 3

    def test_admin_update_status_pending_to_confirmed_no_rollback(self, db_session, sample_product):
        """Test admin đổi status từ pending → confirmed không rollback"""
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
            status="pending"
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

        # Admin update status to confirmed
        result = OrderService.admin_update_order_status(order.id, "confirmed")

        # Verify status changed
        assert result.status == "confirmed"

        # Verify stock unchanged (no rollback)
        updated_product = db_session.query(Product).filter(Product.id == sample_product.id).first()
        assert updated_product.stock == initial_stock

    def test_admin_update_status_cancelled_to_pending_no_rollback(self, db_session, sample_product):
        """Test admin đổi status từ cancelled → pending không rollback"""
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
            status="cancelled"
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

        # Admin update status to pending
        result = OrderService.admin_update_order_status(order.id, "pending")

        # Verify status changed
        assert result.status == "pending"

        # Verify stock unchanged (no rollback)
        updated_product = db_session.query(Product).filter(Product.id == sample_product.id).first()
        assert updated_product.stock == initial_stock