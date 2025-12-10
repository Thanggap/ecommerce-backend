import pytest
from app.services.order_service import OrderService
from app.models.sqlalchemy import Order, OrderItem


class TestOrderServiceStockDeduction:
    """Test OrderService deduct_stock_on_payment"""

    def test_deduct_stock_success(self, db_session, sample_product):
        """Test trừ stock thành công khi thanh toán"""
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

        # Deduct stock
        OrderService.deduct_stock_on_payment(order.id)

        # Verify stock deducted
        updated_product = db_session.query(Product).filter(Product.id == sample_product.id).first()
        assert updated_product.stock == initial_stock - 5

    def test_deduct_stock_insufficient_stock(self, db_session, sample_product):
        """Test trừ stock khi stock không đủ (edge case)"""
        # Set low stock
        sample_product.stock = 2
        db_session.commit()

        # Create order requesting more than available
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
            product_id=sample_product.id,
            quantity=5,  # More than available stock
            unit_price=100.0,
            total_price=500.0
        )
        db_session.add(order_item)
        db_session.commit()

        # This should still deduct (assuming payment already validated stock)
        OrderService.deduct_stock_on_payment(order.id)

        # Stock goes negative (business logic decision)
        updated_product = db_session.query(Product).filter(Product.id == sample_product.id).first()
        assert updated_product.stock == 2 - 5  # = -3

    def test_deduct_stock_order_not_found(self, db_session):
        """Test deduct stock với order không tồn tại"""
        # Should not raise exception, just log
        OrderService.deduct_stock_on_payment(99999)

        # No assertion needed, just ensure no exception

    def test_deduct_stock_product_not_found(self, db_session):
        """Test deduct stock khi product không tồn tại"""
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
        OrderService.deduct_stock_on_payment(order.id)