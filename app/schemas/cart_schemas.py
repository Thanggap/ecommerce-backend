from pydantic import BaseModel, Field
from typing import List, Optional

class ProductSizeInfo(BaseModel):
    size: str
    stock_quantity: int

    class Config:
        from_attributes = True

class CartItemBase(BaseModel):
    id: int = Field(..., description="The ID of the cart item")
    product_id: int = Field(..., description="The ID of the product")
    product_name: Optional[str] = Field(None, description="The name of the product")
    product_image: Optional[str] = Field(None, description="The image URL of the product")
    product_slug: Optional[str] = Field(None, description="The slug of the product")
    product_size: str = Field(..., description="The size of the product")
    product_size_info: Optional[ProductSizeInfo] = Field(None, description="Full product size info with stock")
    quantity: int = Field(default=1, gt=0, description="The quantity of the product")
    unit_price: float = Field(default=0.0, description="Price per unit")
    total_price: float = Field(default=0.0, description="Total price for this item")

    class Config:
        from_attributes = True

class CartBase(BaseModel):
    id: int = Field(..., description="The ID of the cart")
    user_id: str = Field(..., description="The UUID of the user")
    items: List[CartItemBase] = Field(default_factory=list, description="List of items in the cart")
    subtotal: float = Field(default=0.0, description="Subtotal of all items")
    total: float = Field(default=0.0, description="Total including any discounts")

    class Config:
        from_attributes = True

class AddToCartRequest(BaseModel):
    product_id: int = Field(..., description="The ID of the product")
    size: str = Field(..., description="The size of the product")
    quantity: int = Field(default=1, gt=0, description="Quantity to add")

class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="New quantity")
