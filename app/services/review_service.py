from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models.sqlalchemy import Review, Product, User
from app.models.sqlalchemy.order import Order, OrderItem, OrderStatus
from app.schemas.review_schemas import ReviewCreate, ReviewResponse, ReviewListResponse, ReviewAuthor
from app.db import get_db_session
from fastapi import HTTPException
from app.i18n_keys import I18nKeys
import uuid


db = get_db_session()


def map_review_to_response(review: Review) -> ReviewResponse:
    # Build display name from first_name + last_name if available
    display_name = None
    if review.author.first_name or review.author.last_name:
        parts = []
        if review.author.first_name:
            parts.append(review.author.first_name)
        if review.author.last_name:
            parts.append(review.author.last_name)
        display_name = ' '.join(parts) if parts else None
    
    author = ReviewAuthor(
        uuid=review.author.uuid,
        display_name=display_name,
        email=review.author.email
    )
    return ReviewResponse(
        id=review.id,
        product_id=review.product_id,
        content=review.content,
        rating=review.rating,
        images=review.images,
        video=review.video,
        created_at=review.created_at,
        author=author
    )


class ReviewService:
    
    @staticmethod
    def create_order_review(
        order_id: int,
        user_id: str,
        rating: int,
        comment: str,
        images: List[str],
        video: Optional[str]
    ) -> dict:
        """Create review for a specific order (with media support)"""
        db = get_db_session()
        try:
            # Get order and verify ownership
            order = db.query(Order).options(
                joinedload(Order.items)
            ).filter(
                Order.id == order_id,
                Order.user_id == user_id
            ).first()
            
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Validate order is delivered
            if order.status != OrderStatus.DELIVERED.value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Can only review delivered orders. Current status: {order.status}"
                )
            
            # Get all products in order
            if not order.items:
                raise HTTPException(status_code=400, detail="Order has no items")
            
            # For simplicity, create one review for the first product
            # (In real app, might want to review each product separately)
            first_item = order.items[0]
            product_id = first_item.product_id
            
            # Check if already reviewed this product from this order
            existing_review = db.query(Review).filter(
                Review.order_id == order_id,
                Review.product_id == product_id,
                Review.user_id == user_id
            ).first()
            
            if existing_review:
                raise HTTPException(
                    status_code=400,
                    detail="You have already reviewed this order"
                )
            
            # Create review
            new_review = Review(
                product_id=product_id,
                user_id=uuid.UUID(user_id),
                order_id=order_id,
                content=comment,
                rating=rating,
                images=images if images else None,
                video=video
            )
            
            db.add(new_review)
            db.commit()
            db.refresh(new_review)
            
            print(f"[Review] User {user_id} reviewed order {order_id}, rating: {rating}")
            
            return {
                "message": "Review submitted successfully",
                "review_id": new_review.id,
                "order_id": order_id,
                "product_id": product_id,
                "rating": rating
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            print(f"[Review] Error creating review: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            db.close()
    
    @staticmethod
    def create_review(product_slug: str, review_data: ReviewCreate, user_id: uuid.UUID) -> ReviewResponse:
        """Create a new review for a product"""
        # Find product by slug
        product = db.query(Product).filter(Product.slug == product_slug).first()
        if not product:
            raise HTTPException(status_code=404, detail=I18nKeys.PRODUCT_NOT_FOUND)
        
        # Check if user has purchased and received this product
        has_purchased = db.query(Order).join(OrderItem).filter(
            Order.user_id == user_id,
            OrderItem.product_id == product.id,
            Order.status == OrderStatus.DELIVERED.value
        ).first()
        
        if not has_purchased:
            raise HTTPException(
                status_code=403, 
                detail=I18nKeys.REVIEW_PURCHASE_REQUIRED
            )
        
        # Check if user already reviewed this product
        existing_review = db.query(Review).filter(
            Review.product_id == product.id,
            Review.user_id == user_id
        ).first()
        if existing_review:
            raise HTTPException(status_code=400, detail=I18nKeys.REVIEW_ALREADY_EXISTS)
        
        # Create review
        new_review = Review(
            product_id=product.id,
            user_id=user_id,
            content=review_data.content,
            rating=review_data.rating
        )
        db.add(new_review)
        db.commit()
        db.refresh(new_review)
        
        # Load author relationship
        new_review = db.query(Review).options(
            joinedload(Review.author)
        ).filter(Review.id == new_review.id).first()
        
        return map_review_to_response(new_review)
    
    @staticmethod
    def get_product_reviews(product_slug: str) -> ReviewListResponse:
        """Get all reviews for a product with average rating"""
        # Find product by slug
        product = db.query(Product).filter(Product.slug == product_slug).first()
        if not product:
            raise HTTPException(status_code=404, detail=I18nKeys.PRODUCT_NOT_FOUND)
        
        print(f"[Review] Fetching reviews for product {product.id} (slug: {product_slug})")
        
        # Get reviews with author
        reviews = db.query(Review).options(
            joinedload(Review.author)
        ).filter(
            Review.product_id == product.id
        ).order_by(Review.created_at.desc()).all()
        
        print(f"[Review] Found {len(reviews)} reviews for product {product.id}")
        
        # Calculate average rating
        if reviews:
            avg_rating = db.query(func.avg(Review.rating)).filter(
                Review.product_id == product.id
            ).scalar() or 0.0
        else:
            avg_rating = 0.0
        
        review_responses = [map_review_to_response(r) for r in reviews]
        
        return ReviewListResponse(
            reviews=review_responses,
            average_rating=round(float(avg_rating), 1),
            total_reviews=len(reviews)
        )
    
    @staticmethod
    def delete_review(review_id: int, user_id: uuid.UUID, is_admin: bool = False) -> bool:
        """Delete a review (user can delete own, admin can delete any)"""
        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail=I18nKeys.REVIEW_NOT_FOUND)
        
        # Check permission: owner or admin
        if not is_admin and review.user_id != user_id:
            raise HTTPException(status_code=403, detail=I18nKeys.UNAUTHORIZED)
        
        db.delete(review)
        db.commit()
        return True
