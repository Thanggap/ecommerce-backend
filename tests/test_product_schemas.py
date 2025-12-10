import pytest
from pydantic import ValidationError
from app.schemas.product_schemas import ProductBase, ProductCreate, ProductUpdate, ProductResponse


class TestProductSchemas:
    """Test Product schemas với stock validation"""

    def test_product_base_valid_stock(self):
        """Test ProductBase với stock hợp lệ"""
        product = ProductBase(
            slug="test-slug",
            product_type="test-type",
            product_name="Test Product",
            price=100.0,
            stock=50
        )
        assert product.stock == 50

    def test_product_base_stock_zero(self):
        """Test ProductBase với stock = 0"""
        product = ProductBase(
            slug="test-slug",
            product_type="test-type",
            product_name="Test Product",
            price=100.0,
            stock=0
        )
        assert product.stock == 0

    def test_product_base_negative_stock_fails(self):
        """Test ProductBase với stock âm sẽ fail"""
        with pytest.raises(ValidationError) as exc_info:
            ProductBase(
                slug="test-slug",
                product_type="test-type",
                product_name="Test Product",
                price=100.0,
                stock=-5
            )
        assert "stock" in str(exc_info.value)

    def test_product_create_without_stock(self):
        """Test ProductCreate không cần stock (optional)"""
        product = ProductCreate(
            slug="test-slug",
            product_type="test-type",
            product_name="Test Product",
            price=100.0
        )
        # Stock sẽ được set default trong model
        assert product.stock is None

    def test_product_update_stock_optional(self):
        """Test ProductUpdate với stock optional"""
        # Update without stock
        update_data = ProductUpdate(price=150.0)
        assert update_data.price == 150.0
        assert update_data.stock is None

        # Update with stock
        update_data_with_stock = ProductUpdate(stock=25)
        assert update_data_with_stock.stock == 25

    def test_product_response_includes_stock(self):
        """Test ProductResponse includes stock field"""
        from datetime import datetime
        response = ProductResponse(
            id=1,
            slug="test-slug",
            product_type="test-type",
            product_name="Test Product",
            price=100.0,
            stock=30,
            created_at=datetime.now()
        )
        assert response.stock == 30
        assert response.id == 1