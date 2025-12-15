from typing import Optional
import json
from fastapi import APIRouter, FastAPI, HTTPException, Query, Path, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from app.schemas.product_schemas import ProductBase, ProductCreate, ProductResponse, ProductUpdate
from app.schemas.review_schemas import ReviewCreate, ReviewResponse, ReviewListResponse
from app.models.sqlalchemy import Product
from app.services.product_service import Product_Service
from app.services.review_service import ReviewService
from app.services.cloudinary_service import CloudinaryService
from app.services.user_service import require_admin, require_user
from app.i18n_keys import I18nKeys
from app.cache import cache_get, cache_set, invalidate_product_cache

product_router = APIRouter()

# Cache key builders
def build_products_cache_key(page: int, limit: int, category: str = None, product_type: str = None, 
                              min_price: float = None, max_price: float = None, search: str = None,
                              on_sale: bool = None) -> str:
    """Build cache key for products list based on query params"""
    return f"products:page={page}:limit={limit}:cat={category}:type={product_type}:min={min_price}:max={max_price}:search={search}:sale={on_sale}"

def build_product_cache_key(product_slug: str) -> str:
    """Build cache key for single product"""
    return f"product:slug:{product_slug}"


@product_router.get("/products")
async def read_products(
    page: int = Query(0, ge=0, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category name"),
    product_type: Optional[str] = Query(None, description="Filter by product type (Vitamins, Protein, etc.)"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    search: Optional[str] = Query(None, description="Search by product name or description"),
    manufacturer: Optional[str] = Query(None, description="Filter by manufacturer/brand"),
    certification: Optional[str] = Query(None, description="Filter by certification (FDA, GMP, NSF, etc.)"),
    on_sale: Optional[bool] = Query(None, description="Filter products on sale (with sale_price)"),
    sort_by: Optional[str] = Query("newest", description="Sort by: newest, price_asc, price_desc, popular")
):
    """Get products with optional filters - delegates to Elasticsearch for fast search"""
    from app.routers.search_router import search_products
    
    # Delegate to Elasticsearch search (much faster than SQL)
    return await search_products(
        q=search,
        product_type=product_type,
        category=category,
        manufacturer=manufacturer,
        certification=certification,
        min_price=min_price,
        max_price=max_price,
        on_sale=on_sale,
        page=page,
        limit=limit,
        sort_by=sort_by
    )


@product_router.get("/products/{product_slug}", response_model=ProductResponse)
async def read_product(product_slug: str):
    """Get single product by slug - with Redis cache"""
    cache_key = build_product_cache_key(product_slug)
    
    # Try cache first
    cached = await cache_get(cache_key)
    if cached:
        return cached
    
    # Cache miss - query DB  
    product = Product_Service.get_product(product_slug)
    
    # Convert to dict for caching (Pydantic model -> dict)
    from app.services.product_service import map_product_to_response
    product_dict = map_product_to_response(product).dict()
    
    # Set cache (TTL 5 minutes)
    await cache_set(cache_key, product_dict, ttl=300)
    
    return product

@product_router.post("/products", response_model=dict)
async def create_product(product: ProductCreate, current_user = Depends(require_admin)):
    """Create a new product (admin only)"""
    # product: ProductCreate đã nhận sizes/colors
    result = Product_Service.create_product(product)
    await invalidate_product_cache()
    return result


@product_router.put("/products/{product_slug}", response_model=dict)
async def update_product(product_slug: str, product: ProductUpdate, current_user = Depends(require_admin)):
    """Update a product (admin only)"""
    result = Product_Service.update_product(product_slug, product.dict(exclude_unset=True))
    # Invalidate caches (specific product + list)
    await invalidate_product_cache(slug=product_slug)
    return result


@product_router.put("/products/{product_slug}/stock", response_model=dict)
async def update_product_stock(product_slug: str, stock: int, current_user = Depends(require_admin)):
    """Update product stock (admin only)"""
    if stock < 0:
        raise HTTPException(status_code=400, detail="Stock cannot be negative")
    
    result = Product_Service.update_product_stock(product_slug, stock)
    # Invalidate caches
    await invalidate_product_cache(slug=product_slug)
    return result


@product_router.post("/upload-image")
async def upload_product_image(file: UploadFile = File(...)):
    """Upload product image to Cloudinary"""
    result = CloudinaryService.upload_image(file, folder="products")
    return result


# Review endpoints
@product_router.get("/products/{product_slug}/reviews", response_model=ReviewListResponse)
def get_product_reviews(product_slug: str):
    """Get all reviews for a product with average rating"""
    return ReviewService.get_product_reviews(product_slug)


@product_router.post("/products/{product_slug}/reviews", response_model=ReviewResponse)
def create_review(product_slug: str, review: ReviewCreate, current_user = Depends(require_user)):
    """Create a new review for a product (authenticated users only)"""
    return ReviewService.create_review(product_slug, review, current_user.uuid)


@product_router.delete("/reviews/{review_id}")
def delete_review(review_id: int, current_user = Depends(require_user)):
    """Delete a review (owner or admin only)"""
    is_admin = getattr(current_user, 'role', None) == 'admin'
    ReviewService.delete_review(review_id, current_user.uuid, is_admin)
    return {"message": I18nKeys.REVIEW_DELETED}
