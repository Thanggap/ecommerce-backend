from builtins import ValueError, any, bool, str
from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum
import uuid

class UserBase(BaseModel):
    email: EmailStr = Field(..., example="john.doe@exmaple.com")
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    phone_number: Optional[str] = Field(None, example="0912345678")
    address: Optional[str] = Field(None, example="123 Main St, District 1, HCM")
    is_active: Optional[bool] = Field(None, example = True)

    class Config:
        from_attributes = True

class UserCreate(UserBase):
    email: EmailStr = Field(..., example="john.doe@example.com")
    password: str = Field(..., example="SecurePassword&*1234")

class UserUpdate(UserBase):
    email: EmailStr = Field(..., example="john.doe@example.com")
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    phone_number: Optional[str] = Field(None, example="0912345678")
    address: Optional[str] = Field(None, example="123 Main St, District 1, HCM")
    is_active: Optional[bool] = Field(None, example = True)

    @root_validator(pre=True)
    def check_at_least_one_value(cls, values):
        if not any(values.values()):
            raise ValueError("At least one field must be provided for update")
        return values

class ProfileUpdate(BaseModel):
    """Schema for user to update their own profile"""
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    phone_number: Optional[str] = Field(None, example="0912345678")
    address: Optional[str] = Field(None, example="123 Main St, District 1, HCM")
    
    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str = Field(..., example="OldPassword123")
    new_password: str = Field(..., min_length=8, example="NewPassword123")


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr = Field(..., example="john.doe@example.com")


class ResetPasswordRequest(BaseModel):
    """Schema for reset password with token"""
    token: str = Field(..., example="abc123token")
    new_password: str = Field(..., min_length=8, example="NewSecurePassword123")

    
class UserResponse(UserBase):
    id: uuid.UUID = Field(..., alias="uuid", example=uuid.uuid4())
    email: EmailStr = Field(..., example="john.doe@example.com")
    first_name: Optional[str] = Field(None, example="John")    
    last_name: Optional[str] = Field(None, example="Doe")
    phone_number: Optional[str] = Field(None, example="0912345678")
    address: Optional[str] = Field(None, example="123 Main St, District 1, HCM")
    role: str = Field(default="user", example="user")

    class Config:
        from_attributes = True
        populate_by_name = True

class LoginRequest(BaseModel):
    email: str = Field(..., example="john.doe@example.com")
    password: str = Field(..., example="SecurePassword&*1234")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ErrorResponse(BaseModel):
    error: str = Field(..., example="Not Found")
    details: Optional[str] = Field(None, example="The requested resource was not found.")