import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.services.order_service import OrderService
from app.schemas.order_schemas import CreateOrderRequest, ShippingInfo
from app.models.sqlalchemy import Cart, Cart_Item, Product, ProductSize


class TestOrderServiceStockValidation:
    """Test OrderService create_order với stock validation"""

    def test_create_order_sufficient_stock(self, db_session, sample_user, sample_product):
        """Test tạo order thành công khi stock đủ"""
        # Create cart with item
        cart = Cart(user_id=sample_user.uuid)
        db_session.add(cart)

        cart_item = Cart_Item(
            cart_id=cart.id,
            product_id=sample_product.id,
            quantity=5  # Stock = 50, đủ cho 5
        )
        db_session.add(cart_item)
        db_session.commit()

        # Create order request
        request = CreateOrderRequest(
            shipping=ShippingInfo(
                name="Test User",
                phone="123456789",
                email="test@example.com",
                address="Test Address"
            )
        )

        # Mock payment service
        with patch('app.services.order_service.payment_service') as mock_payment:
            mock_payment.create_checkout_session.return_value = {"id": "test_session", "url": "test_url"}

            result = OrderService.create_order(sample_user.uuid, request)

            assert result.id is not None
            assert result.shipping_name == "Test User"
            # Verify stock not deducted yet (only after payment)
            updated_product = db_session.query(Product).filter(Product.id == sample_product.id).first()
            assert updated_product.stock == 50

    def test_create_order_insufficient_stock(self, db_session, sample_user, sample_product):
        """Test tạo order fail khi stock không đủ"""
        # Set stock to 3
        sample_product.stock = 3
        db_session.commit()

        # Create cart with item requesting more than available
        cart = Cart(user_id=sample_user.uuid)
        db_session.add(cart)

        cart_item = Cart_Item(
            cart_id=cart.id,
            product_id=sample_product.id,
            quantity=10  # Stock = 3, không đủ
        )
        db_session.add(cart_item)
        db_session.commit()

        request = CreateOrderRequest(
            shipping=ShippingInfo(
                name="Test User",
                phone="123456789",
                email="test@example.com",
                address="Test Address"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            OrderService.create_order(sample_user.uuid, request)

        assert exc_info.value.status_code == 400
        assert "out of stock" in str(exc_info.value.detail).lower()

    def test_create_order_empty_cart(self, db_session, sample_user):
        """Test tạo order fail với cart rỗng"""
        # Create empty cart
        cart = Cart(user_id=sample_user.uuid)
        db_session.add(cart)
        db_session.commit()

        request = CreateOrderRequest(
            shipping=ShippingInfo(
                name="Test User",
                phone="123456789",
                email="test@example.com",
                address="Test Address"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            OrderService.create_order(sample_user.uuid, request)

        assert exc_info.value.status_code == 400
        assert "empty" in str(exc_info.value.detail).lower()

    def test_create_order_no_cart(self, db_session, sample_user):
        """Test tạo order fail khi không có cart"""
        request = CreateOrderRequest(
            shipping=ShippingInfo(
                name="Test User",
                phone="123456789",
                email="test@example.com",
                address="Test Address"
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            OrderService.create_order(sample_user.uuid, request)

        assert exc_info.value.status_code == 400
        assert "empty" in str(exc_info.value.detail).lower()