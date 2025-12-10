import pytest
from app.models.sqlalchemy.product import Product
from app.schemas.product_schemas import ProductCreate, ProductUpdate


class TestProductModel:
    """Test Product model và stock field"""

    def test_product_model_has_stock_field(self, db_session):
        """Test Product model có stock field với default value"""
        product = Product(
            slug="test-product",
            product_type="test",
            product_name="Test Product",
            price=100.0
        )
        db_session.add(product)
        db_session.commit()

        # Check stock field exists and has default value 0
        assert hasattr(product, 'stock')
        assert product.stock == 0

    def test_product_model_stock_positive(self, db_session):
        """Test Product stock có thể set positive value"""
        product = Product(
            slug="test-product-2",
            product_type="test",
            product_name="Test Product 2",
            price=100.0,
            stock=25
        )
        db_session.add(product)
        db_session.commit()

        assert product.stock == 25

    def test_product_model_stock_zero(self, db_session):
        """Test Product stock có thể set 0"""
        product = Product(
            slug="test-product-3",
            product_type="test",
            product_name="Test Product 3",
            price=100.0,
            stock=0
        )
        db_session.add(product)
        db_session.commit()

        assert product.stock == 0