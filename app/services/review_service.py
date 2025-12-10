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
    author = ReviewAuthor(
        uuid=review.author.uuid,
        display_name=review.author.display_name,
        email=review.author.email
    )
    return ReviewResponse(
        id=review.id,
        product_id=review.product_id,
        content=review.content,
        rating=review.rating,
        created_at=review.created_at,
        author=author
    )


class ReviewService:
    
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
        
        # Get reviews with author
        reviews = db.query(Review).options(
            joinedload(Review.author)
        ).filter(
            Review.product_id == product.id
        ).order_by(Review.created_at.desc()).all()
        
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
