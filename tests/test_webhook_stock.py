import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from app.routers.webhook_router import stripe_webhook
from app.models.sqlalchemy import Order, OrderItem, Product


class TestWebhookStockHandling:
    """Test webhook stock deduction integration"""

    def test_webhook_checkout_completed_deducts_stock(self, db_session, sample_product):
        """Test webhook checkout.session.completed deducts stock"""
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

        # Initial stock
        initial_stock = sample_product.stock

        # Mock Stripe webhook payload
        payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {
                        "order_id": str(order.id)
                    }
                }
            }
        }

        # Mock Stripe webhook verification
        with patch('stripe.Webhook.construct_event', return_value=payload):
            with patch('stripe.Webhook') as mock_webhook:
                # Call webhook
                result = stripe_webhook(MagicMock(), MagicMock())

                assert result == {"status": "success"}

                # Verify stock was deducted
                updated_product = db_session.query(Product).filter(Product.id == sample_product.id).first()
                assert updated_product.stock == initial_stock - 5

    def test_webhook_checkout_expired_no_stock_change(self, db_session, sample_product):
        """Test webhook checkout.session.expired doesn't change stock"""
        # Create order
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
        db_session.commit()

        # Initial stock
        initial_stock = sample_product.stock

        # Mock Stripe webhook payload for expired session
        payload = {
            "type": "checkout.session.expired",
            "data": {
                "object": {
                    "metadata": {
                        "order_id": str(order.id)
                    }
                }
            }
        }

        # Mock Stripe webhook verification
        with patch('stripe.Webhook.construct_event', return_value=payload):
            # Call webhook
            result = stripe_webhook(MagicMock(), MagicMock())

            assert result == {"status": "success"}

            # Verify stock unchanged
            updated_product = db_session.query(Product).filter(Product.id == sample_product.id).first()
            assert updated_product.stock == initial_stock

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature(self):
        """Test webhook với invalid signature"""
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=b'payload')
        mock_request.headers.get = MagicMock(return_value='signature')
        
        with patch('stripe.Webhook.construct_event', side_effect=ValueError("Invalid signature")):
            with pytest.raises(HTTPException) as exc_info:
                await stripe_webhook(mock_request)

            assert exc_info.value.status_code == 400
            assert "Invalid payload" in str(exc_info.value.detail)

    def test_webhook_checkout_completed_no_order_id(self, db_session):
        """Test webhook checkout completed without order_id"""
        # Mock Stripe webhook payload without order_id
        payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {}
                }
            }
        }

        # Mock Stripe webhook verification
        with patch('stripe.Webhook.construct_event', return_value=payload):
            mock_request = MagicMock()
            mock_request.body = AsyncMock(return_value=b'payload')
            mock_request.headers.get = MagicMock(return_value='signature')
            
            # Call webhook - should not crash
            result = stripe_webhook(mock_request)

            assert result == {"status": "success"}