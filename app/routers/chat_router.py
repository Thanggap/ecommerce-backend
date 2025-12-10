"""
Chat Router - Enhanced AI Assistant API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.chat_service import ChatService

chat_router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    user_id: Optional[str] = None


class ProductSuggestion(BaseModel):
    name: str
    price: float
    original_price: Optional[float] = None
    category: str
    description: str
    slug: str
    stock: int
    on_sale: bool


class ChatResponse(BaseModel):
    message: str
    products: List[Dict[str, Any]] = []
    intent: str = "general"


@chat_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Intelligent chat with AI assistant
    
    Features:
    - Product search and recommendations
    - Order and shipping support
    - Contextual help
    
    Returns:
        - AI response message
        - Product suggestions (if applicable)
        - Detected intent
    """
    try:
        # Convert to dict format for OpenAI
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        response = ChatService.chat(messages, request.user_id)
        
        return ChatResponse(
            message=response["message"],
            products=response.get("products", []),
            intent=response.get("intent", "general")
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail="Chat service not configured. Please set OPENAI_API_KEY.")
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Chat service error")
