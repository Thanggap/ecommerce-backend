from fastapi import APIRouter, HTTPException, Depends
from datetime import timedelta, datetime, timezone
import traceback
import secrets
from typing import List

from app.schemas.user_schemas import (
    UserCreate, UserResponse, LoginRequest, TokenResponse, 
    ProfileUpdate, PasswordChange, ForgotPasswordRequest, ResetPasswordRequest
)
from app.services.user_service import UserServices, require_user, require_admin
from app.models.sqlalchemy import User
from app.db import get_db_session
from app.i18n_keys import I18nKeys


router = APIRouter()


# Registration route
@router.post("/register", response_model=UserResponse)
def register(user: UserCreate):
    try:
        user_obj = UserServices.register(user.model_dump())
        return user_obj
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Register error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Login route
@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest):
    user = UserServices.authenticate(login_data.email, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail=I18nKeys.AUTH_INVALID_CREDENTIALS)

    access_token = UserServices.create_access_token(
        str(user.uuid),
        user.role,
        timedelta(minutes=UserServices.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    user_response = UserResponse.model_validate(user)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


# Get current user info
@router.get("/me", response_model=UserResponse)
def get_me(current_user = Depends(require_user)):
    return UserResponse.model_validate(current_user)


# Update profile
@router.put("/profile", response_model=UserResponse)
def update_profile(profile_data: ProfileUpdate, current_user = Depends(require_user)):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.uuid == current_user.uuid).first()
        if not user:
            raise HTTPException(status_code=404, detail=I18nKeys.USER_NOT_FOUND)
        
        # Update fields if provided
        if profile_data.first_name is not None:
            user.first_name = profile_data.first_name
        if profile_data.last_name is not None:
            user.last_name = profile_data.last_name
        if profile_data.phone_number is not None:
            user.phone_number = profile_data.phone_number
        if profile_data.address is not None:
            user.address = profile_data.address
        
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)
    finally:
        db.close()


# Change password
@router.put("/change-password")
def change_password(password_data: PasswordChange, current_user = Depends(require_user)):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.uuid == current_user.uuid).first()
        if not user:
            raise HTTPException(status_code=404, detail=I18nKeys.USER_NOT_FOUND)
        
        # Verify current password
        if not UserServices.verify_password(password_data.current_password, user.hashed_password, user.salt):
            raise HTTPException(status_code=400, detail=I18nKeys.PROFILE_WRONG_PASSWORD)
        
        # Hash new password
        new_hashed, new_salt = UserServices.hash_password(password_data.new_password)
        user.hashed_password = new_hashed
        user.salt = new_salt
        
        db.commit()
        return {"message": I18nKeys.PROFILE_PASSWORD_CHANGED}
    finally:
        db.close()


# Forgot password - generate reset token
@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    """Request password reset - generates token and mocks email sending"""
    db = get_db_session()
    try:
        user = db.query(User).filter(User.email == request.email).first()
        
        # Always return success to prevent email enumeration
        if not user:
            return {"message": I18nKeys.AUTH_RESET_EMAIL_SENT}
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        
        user.reset_token = reset_token
        user.reset_token_expires = reset_expires
        db.commit()
        
        # Mock email sending (in production, send actual email)
        print(f"[MOCK EMAIL] Password reset link for {user.email}:")
        print(f"[MOCK EMAIL] http://localhost:3000/reset-password?token={reset_token}")
        
        return {"message": I18nKeys.AUTH_RESET_EMAIL_SENT}
    finally:
        db.close()


# Reset password with token
@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest):
    """Reset password using token from email"""
    db = get_db_session()
    try:
        user = db.query(User).filter(User.reset_token == request.token).first()
        
        if not user:
            raise HTTPException(status_code=400, detail=I18nKeys.AUTH_INVALID_RESET_TOKEN)
        
        # Check if token expired
        if user.reset_token_expires and user.reset_token_expires < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail=I18nKeys.AUTH_RESET_TOKEN_EXPIRED)
        
        # Update password
        new_hashed, new_salt = UserServices.hash_password(request.new_password)
        user.hashed_password = new_hashed
        user.salt = new_salt
        
        # Clear reset token
        user.reset_token = None
        user.reset_token_expires = None
        
        db.commit()
        return {"message": I18nKeys.AUTH_PASSWORD_RESET_SUCCESS}
    finally:
        db.close()


# Protected route example (user only)
@router.get("/protected")
def protected_route(current_user = Depends(require_user)):
    return {"message": I18nKeys.AUTH_LOGIN_REQUIRED, "user": current_user.email}


# Admin only route example
@router.get("/admin-only")
def admin_only_route(current_user = Depends(require_admin)):
    return {"message": I18nKeys.AUTH_ADMIN_ONLY, "user": current_user.email}


# Get all users (admin only)
@router.get("/users", response_model=List[UserResponse])
def get_all_users(current_user = Depends(require_admin)):
    db = get_db_session()
    try:
        users = db.query(User).all()
        return [UserResponse.model_validate(u) for u in users]
    finally:
        db.close()


# Promote user to admin (admin only)
@router.put("/users/{user_id}/promote", response_model=UserResponse)
def promote_user(user_id: str, current_user = Depends(require_admin)):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.uuid == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=I18nKeys.USER_NOT_FOUND)
        
        if user.role == "admin":
            raise HTTPException(status_code=400, detail=I18nKeys.USER_ALREADY_ADMIN)
        
        user.role = "admin"
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)
    finally:
        db.close()


# Demote admin to user (admin only)
@router.put("/users/{user_id}/demote", response_model=UserResponse)
def demote_user(user_id: str, current_user = Depends(require_admin)):
    db = get_db_session()
    try:
        user = db.query(User).filter(User.uuid == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=I18nKeys.USER_NOT_FOUND)
        
        if str(user.uuid) == str(current_user.uuid):
            raise HTTPException(status_code=400, detail=I18nKeys.USER_CANNOT_DEMOTE_SELF)
        
        if user.role == "user":
            raise HTTPException(status_code=400, detail=I18nKeys.USER_ALREADY_USER)
        
        user.role = "user"
        db.commit()
        db.refresh(user)
        return UserResponse.model_validate(user)
    finally:
        db.close()

