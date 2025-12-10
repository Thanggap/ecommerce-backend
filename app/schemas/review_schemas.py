from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import uuid


class ReviewCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000, example="Great product!")
    rating: int = Field(..., ge=1, le=5, example=5)
    
    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewAuthor(BaseModel):
    uuid: uuid.UUID
    display_name: Optional[str] = None
    email: str
    
    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    id: int
    product_id: int
    content: str
    rating: int
    created_at: Optional[datetime] = None
    author: ReviewAuthor
    
    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    reviews: List[ReviewResponse]
    average_rating: float = 0.0
    total_reviews: int = 0
