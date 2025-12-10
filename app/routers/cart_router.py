from fastapi import APIRouter, Depends
from app.schemas.cart_schemas import CartBase, AddToCartRequest, UpdateCartItemRequest
from app.services.cart_service import CartService
from app.services.user_service import require_user
from app.models.sqlalchemy.user import User

cart_router = APIRouter()

# NOTE: Cart uses Optimistic UI pattern
# - GET /cart: Full cart for hydration (on login/refresh)
# - POST/PUT/DELETE: Return {status: ok} only, FE manages state locally


@cart_router.get("/cart", response_model=CartBase)
def get_user_cart(current_user: User = Depends(require_user)):
    """Get current user's cart for hydration (on login/page refresh)"""
    return CartService.get_cart(str(current_user.uuid))


@cart_router.post("/cart", response_model=CartBase)
def add_to_cart(request: AddToCartRequest, current_user: User = Depends(require_user)):
    """Add item to cart - returns full cart (FE needs new item ID)"""
    return CartService.add_to_cart(str(current_user.uuid), request)


@cart_router.put("/cart/{cart_item_id}")
def update_cart_item(
    cart_item_id: int,
    request: UpdateCartItemRequest,
    current_user: User = Depends(require_user)
):
    """Update quantity - return status only (FE uses optimistic UI)"""
    CartService.update_cart_item(str(current_user.uuid), cart_item_id, request.quantity)
    return {"status": "ok"}


@cart_router.delete("/cart/{cart_item_id}")
def remove_from_cart(cart_item_id: int, current_user: User = Depends(require_user)):
    """Remove item - return status only (FE uses optimistic UI)"""
    CartService.remove_from_cart(str(current_user.uuid), cart_item_id)
    return {"status": "ok"}


@cart_router.delete("/cart")
def clear_cart(current_user: User = Depends(require_user)):
    """Clear cart - return status only"""
    CartService.clear_cart(str(current_user.uuid))
    return {"status": "ok"}
