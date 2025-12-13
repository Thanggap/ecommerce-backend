from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

from app.routers.product_router import product_router
from app.routers.cart_router import cart_router
from app.routers.support_router import support_router
from app.routers.auth_router import router as auth_router
from app.routers.order_router import order_router
from app.routers.chat_router import chat_router
from app.routers.payment_router import payment_router
from app.routers.webhook_router import webhook_router
from app.routers.search_router import router as search_router
from app.routers.upload_router import upload_router

from app.db import create_tables
from app.models.sqlalchemy import *
from app.cache import init_redis, close_redis
from app.search.product_index import ensure_product_index

from fastapi_pagination import Page, add_pagination, paginate


# =====================
# Security Headers Middleware
# =====================
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses (equivalent to Helmet.js)"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Skip CSP for Swagger docs (development convenience)
        path = request.url.path
        if path in ["/docs", "/redoc", "/openapi.json"] or path.startswith("/docs"):
            return response
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy (disable sensitive features)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy (basic - adjust for production)
        # Note: Allow 'unsafe-inline' for development, tighten in production
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        
        # Strict Transport Security (HSTS)
        # Force HTTPS for 1 year, include subdomains
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    await init_redis()
    ensure_product_index()  # Create ES index if not exists
    yield
    # Shutdown
    await close_redis()


description = """
Health Supplements E-Commerce API

A comprehensive e-commerce platform cho health supplements với full-featured order management system.

## Core Features
* **Product Management** - Browse products with advanced filtering, search (Elasticsearch), và multi-language support
* **Shopping Cart** - Complete cart system với real-time stock validation
* **Order Processing** - Full order lifecycle từ creation đến fulfillment với Stripe payment integration
* **Returns & Refunds** - Professional return request handling với evidence upload (images/videos)
* **Product Reviews** - Customer reviews với rating system và media attachments
* **Admin Dashboard** - Comprehensive admin tools cho user/product/order management
* **AI Chatbot** - Gemini-powered chatbot cho product recommendations
* **Internationalization** - Multi-language (EN/VI) và currency support (USD/VND)

## Tech Stack
* **Framework**: FastAPI với async/await
* **Database**: PostgreSQL + SQLAlchemy ORM
* **Cache**: Redis (configured)
* **Search**: Elasticsearch
* **Payment**: Stripe
* **Storage**: Cloudinary (images/videos)
* **AI**: ChatGPT API
"""
app = FastAPI(
    title="Health Supplements E-Commerce API", 
    description=description,
    summary="Professional e-commerce backend with order management, returns, reviews & AI chatbot",
    contact={
        "name": "LTK Support",
        "email": "support@ltk-ecommerce.com",
    },
    root_path="/api",
    lifespan=lifespan
)


# Security Headers Middleware (Helmet equivalent)
app.add_middleware(SecurityHeadersMiddleware)

# CORS Middleware - Tightened security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development
        "http://localhost:3001",
        "https://localhost:3000",  # HTTPS development
        "https://localhost:3001",
        "https://ecommerce-frontend-orpin.vercel.app",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "X-Total-Count"],
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(product_router)
app.include_router(cart_router)
app.include_router(order_router, tags=["Orders"])
app.include_router(chat_router, tags=["Chat"])
app.include_router(payment_router, tags=["Payments"])
app.include_router(webhook_router, tags=["Webhooks"])
app.include_router(support_router)
app.include_router(search_router, tags=["Search"])  # Elasticsearch search
app.include_router(upload_router, tags=["Upload"])  # File uploads
add_pagination(app)

create_tables()

@app.get("/")
async def root():
    return {"message": "Hello, world!"}
