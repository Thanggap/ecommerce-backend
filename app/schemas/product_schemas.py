from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
import uuid

class ProductColorBase(BaseModel):
    color: str = Field(..., example="Red")
    image_url: Optional[str] = Field(None, example="http://example.com/red.png")

class ProductColorResponse(ProductColorBase):
    id: int = Field(..., example=1)

class CategoryBase(BaseModel):
    name: str = Field(..., example="Electronics")

class ProductSizeBase(BaseModel):
    size: str = Field(..., example="Medium")
    stock_quantity: int = Field(..., description="The quantity of this size in stock", example=100)

class ProductBase(BaseModel):
    slug: str = Field(..., example="unique-product-slug-1234")
    product_type: str = Field(..., example="Accessory")
    product_name: str = Field(..., example="Stylish Sunglasses")
    price: float = Field(..., gt=0, example=19.99)
    blurb: Optional[str] = Field(None, example="A short description of the product")
    description: Optional[str] = Field(None, example="A detailed description of the product")
    image_url: Optional[str] = Field(None, example="http://example.com/image.png")
    sale_price: Optional[float] = Field(None, gt=0, example=9.99)
    stock: int = Field(..., ge=0, example=100)
    
    # Supplement-specific fields
    serving_size: Optional[str] = Field(None, example="2 capsules")
    servings_per_container: Optional[int] = Field(None, example=30)
    ingredients: Optional[str] = Field(None, example="Whey Protein Isolate, Natural Flavors, Stevia")
    allergen_info: Optional[str] = Field(None, example="Contains: Milk, Soy")
    usage_instructions: Optional[str] = Field(None, example="Take 2 capsules daily with water")
    warnings: Optional[str] = Field(None, example="Consult physician if pregnant or nursing")
    expiry_date: Optional[date] = Field(None, example="2026-12-31")
    manufacturer: Optional[str] = Field(None, example="Nature's Best Co.")
    country_of_origin: Optional[str] = Field(None, example="USA")
    certification: Optional[str] = Field(None, example="FDA, GMP, NSF Certified")

class ProductCreate(ProductBase):
    stock: Optional[int] = Field(None, ge=0, example=100)
    sizes: Optional[List[ProductSizeBase]] = Field(None, description="List of sizes with stock")
    colors: Optional[List[ProductColorBase]] = Field(None, description="List of colors with image")

class ProductUpdate(BaseModel):
    slug: Optional[str] = Field(None, example="unique-product-slug-1234")
    product_type: Optional[str] = Field(None, example="Accessory")
    product_name: Optional[str] = Field(None, example="Stylish Sunglasses")
    price: Optional[float] = Field(None, gt=0, example=19.99)
    blurb: Optional[str] = Field(None, example="A short description of the product")
    description: Optional[str] = Field(None, example="A detailed description of the product")
    image_url: Optional[str] = Field(None, example="http://example.com/image.png")
    sale_price: Optional[float] = Field(None, gt=0, example=9.99)
    stock: Optional[int] = Field(None, ge=0, example=100)

    @validator('price')
    def check_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Price must be greater than zero.")
        return v

class ProductResponse(ProductBase):
    id: int = Field(..., example=1)
    created_at: Optional[datetime] = Field(None, example=datetime.now())
    categories: List[CategoryBase] = []
    sizes: List[ProductSizeBase] = []
    colors: List[ProductColorResponse] = []

class ProductListResponse(BaseModel):
    products: List[ProductResponse]

class CategoryResponse(CategoryBase):
    id: int = Field(..., example=1)

class ProductSizeResponse(ProductSizeBase):
    size_id: int = Field(..., example=1)
