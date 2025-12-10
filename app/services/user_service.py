import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from dotenv import load_dotenv

from app.models.sqlalchemy import User
from app.schemas.user_schemas import UserCreate, UserResponse, LoginRequest, TokenResponse
from app.db import get_db_session
from app.i18n_keys import I18nKeys

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class UserServices:
    ACCESS_TOKEN_EXPIRE_MINUTES = ACCESS_TOKEN_EXPIRE_MINUTES

    @staticmethod
    def hash_password(password: str) -> tuple[str, str]:
        """Hash password with bcrypt - bcrypt auto generates salt internally"""
        # Truncate password to 72 bytes (bcrypt limit)
        truncated = password[:72]
        hashed = pwd_context.hash(truncated)
        # Return empty salt since bcrypt handles it internally
        return hashed, ""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash"""
        truncated = plain_password[:72]
        return pwd_context.verify(truncated, hashed_password)

    @staticmethod
    def register(user_data: dict) -> UserResponse:
        db = get_db_session()
        try:
            # Check if email exists
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            if existing_user:
                raise ValueError(I18nKeys.AUTH_EMAIL_ALREADY_EXISTS)

            # Hash password
            hashed_password, salt = UserServices.hash_password(user_data["password"])

            # Create user
            user = User(
                email=user_data["email"],
                hashed_password=hashed_password,
                salt=salt,
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                role="user",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return UserResponse.model_validate(user)
        finally:
            db.close()

    @staticmethod
    def authenticate(email: str, password: str) -> Optional[User]:
        db = get_db_session()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None
            if not UserServices.verify_password(password, user.hashed_password, user.salt):
                return None
            return user
        finally:
            db.close()

    @staticmethod
    def create_access_token(user_id: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
        data = {"sub": user_id, "role": role}
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        data.update({"exp": expire})
        encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=I18nKeys.AUTH_TOKEN_INVALID,
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        db = get_db_session()
        try:
            user = db.query(User).filter(User.uuid == user_id).first()
            if user is None:
                raise credentials_exception
            return user
        finally:
            db.close()

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        db = get_db_session()
        try:
            return db.query(User).filter(User.uuid == user_id).first()
        finally:
            db.close()


# Dependencies for route protection
def require_user(current_user: User = Depends(UserServices.get_current_user)) -> User:
    """Dependency: Require authenticated user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=I18nKeys.AUTH_ACCOUNT_DISABLED
        )
    return current_user


def require_admin(current_user: User = Depends(UserServices.get_current_user)) -> User:
    """Dependency: Require admin role"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=I18nKeys.AUTH_ACCOUNT_DISABLED
        )
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=I18nKeys.AUTH_ADMIN_ONLY
        )
    return current_user
