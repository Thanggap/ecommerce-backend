"""
Chat Service - Intelligent AI Assistant for E-commerce
Enhanced with product search, recommendations, and contextual help
"""
import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from app.db import get_db_session
from app.models.sqlalchemy import Product
from sqlalchemy import or_, desc

# Load API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Enhanced system prompt with function calling
SYSTEM_PROMPT = """You are a knowledgeable health supplement advisor for an online supplement store.

Your capabilities:
1. **Product Search** - Help customers find specific supplements based on their health goals
2. **Recommendations** - Suggest supplements for fitness, immunity, beauty, weight management, etc.
3. **Order Support** - Answer questions about orders, shipping, returns
4. **Health Guidance** - Explain supplement benefits, usage instructions, and certifications

When customers ask about supplements:
- Search the catalog and recommend specific products
- Provide product details (name, price, ingredients, certifications)
- Explain health benefits and usage
- Suggest alternatives or complementary products
- Always mention to consult healthcare provider for medical advice

Store Information:
- Free shipping on orders over $100
- 30-day money-back guarantee (unopened products)
- Payment: Credit cards, PayPal, Stripe
- Delivery: 3-7 business days
- Categories: Vitamins & Minerals, Protein & Fitness, Weight Management, Beauty & Skin, Digestive Health, Brain & Focus, Immune Support

Important Disclaimers:
- DO NOT diagnose medical conditions
- DO NOT make medical claims
- Always include: "These statements have not been evaluated by the FDA. This product is not intended to diagnose, treat, cure, or prevent any disease."
- Recommend consulting healthcare provider before use

Communication Style:
- Knowledgeable and trustworthy
- Concise but informative
- Use emojis sparingly (� � 🌿 ✨)
- Always provide actionable next steps
- Only recommend products that exist in our database"""


class ChatService:
    """Intelligent chat service with product search integration"""
    
    _client: OpenAI = None
    
    @classmethod
    def get_client(cls) -> OpenAI:
        """Get or create OpenAI client"""
        if cls._client is None:
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured")
            cls._client = OpenAI(api_key=OPENAI_API_KEY)
        return cls._client
    
    @classmethod
    def search_products(cls, query: str, category: str = None, limit: int = 5) -> List[Dict]:
        """
        Search products in database based on query
        
        Args:
            query: Search keywords (supports multi-word, will search each word with OR logic)
            category: Optional category filter
            limit: Max results
            
        Returns:
            List of product dicts with name, price, description, slug
        """
        db = get_db_session()
        try:
            products_query = db.query(Product)
            
            # Search in product name, description, blurb, and product_type
            if query:
                # Split query into individual words for flexible matching
                keywords = query.split()
                
                # Build OR conditions for each keyword across all searchable fields
                search_conditions = []
                for keyword in keywords:
                    search_conditions.append(Product.product_name.ilike(f"%{keyword}%"))
                    search_conditions.append(Product.description.ilike(f"%{keyword}%"))
                    search_conditions.append(Product.blurb.ilike(f"%{keyword}%"))
                    search_conditions.append(Product.product_type.ilike(f"%{keyword}%"))
                
                # Apply OR filter
                products_query = products_query.filter(or_(*search_conditions))
            
            # Filter by category
            if category:
                products_query = products_query.filter(Product.product_type.ilike(f"%{category}%"))
            
            # Get results - order by id DESC (latest products first)
            products = products_query.order_by(desc(Product.id)).limit(limit).all()
            
            return [{
                "name": p.product_name,
                "price": float(p.sale_price or p.price),
                "original_price": float(p.price) if p.sale_price else None,
                "category": p.product_type,
                "description": p.blurb or p.description[:100] if p.description else "",
                "slug": p.slug,
                "stock": p.stock,
                "on_sale": bool(p.sale_price)
            } for p in products]
        except Exception as e:
            print(f"Product search error: {e}")
            return []
        finally:
            db.close()
    
    @classmethod
    def get_featured_products(cls, limit: int = 4) -> List[Dict]:
        """Get featured/popular products for recommendations"""
        db = get_db_session()
        try:
            # Get products with stock, order by id DESC (latest)
            products = db.query(Product).filter(
                Product.stock > 0
            ).order_by(desc(Product.id)).limit(limit).all()
            
            return [{
                "name": p.product_name,
                "price": float(p.sale_price or p.price),
                "original_price": float(p.price) if p.sale_price else None,
                "slug": p.slug,
                "category": p.product_type,
                "description": p.blurb or p.description[:100] if p.description else "",
                "stock": p.stock,
                "on_sale": bool(p.sale_price)
            } for p in products]
        except Exception as e:
            print(f"Featured products error: {e}")
            return []
        finally:
            db.close()
    
    @classmethod
    def extract_search_keywords(cls, message: str) -> str:
        """
        Extract meaningful search keywords from user message
        Remove common filler words to improve search accuracy
        
        Args:
            message: User's raw message
            
        Returns:
            Cleaned search keywords
        """
        # Common words to remove
        stopwords = [
            "show", "me", "find", "looking", "for", "search", "need", "want", 
            "to", "buy", "get", "some", "the", "a", "an", "can", "you", 
            "i", "am", "is", "are", "was", "were", "do", "does"
        ]
        
        # Split and filter
        words = message.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        
        # Join back
        return " ".join(keywords) if keywords else message
    
    @classmethod
    def detect_intent(cls, message: str) -> Dict[str, any]:
        """
        Detect user intent from message
        
        Returns:
            {
                "intent": "product_search|recommendations|order_help|general",
                "keywords": [...],
                "category": "..." or None
            }
        """
        message_lower = message.lower()
        
        # Product search intent - expanded keywords
        product_keywords = [
            "looking for", "find", "search", "show me", "need", "want to buy",
            "get", "buy", "purchase", "interested in"
        ]
        
        # Supplement-specific product keywords (strong indicators)
        supplement_keywords = [
            "protein", "vitamin", "collagen", "omega", "probiotic", "bcaa",
            "creatine", "multivitamin", "supplement", "capsule", "powder",
            "fish oil", "biotin", "elderberry", "zinc", "magnesium"
        ]
        
        # Check for product search intent
        has_product_keyword = any(kw in message_lower for kw in product_keywords)
        has_supplement_keyword = any(kw in message_lower for kw in supplement_keywords)
        
        if has_product_keyword or has_supplement_keyword:
            # Extract category
            categories = ["vitamin", "protein", "weight", "beauty", "skin", "digestive", "brain", "focus", "immune", "fitness", "mineral"]
            detected_category = next((cat for cat in categories if cat in message_lower), None)
            
            return {
                "intent": "product_search",
                "keywords": message_lower.split(),
                "category": detected_category
            }
        
        # Recommendations intent
        rec_keywords = ["recommend", "suggest", "what should", "best", "popular", "trending"]
        if any(kw in message_lower for kw in rec_keywords):
            return {
                "intent": "recommendations",
                "keywords": message_lower.split(),
                "category": None
            }
        
        # Order/shipping help
        order_keywords = ["order", "shipping", "delivery", "track", "return", "refund"]
        if any(kw in message_lower for kw in order_keywords):
            return {
                "intent": "order_help",
                "keywords": message_lower.split(),
                "category": None
            }
        
        return {
            "intent": "general",
            "keywords": [],
            "category": None
        }
    
    
    @classmethod
    def chat(cls, messages: List[Dict[str, str]], user_id: str = None) -> Dict[str, any]:
        """
        Enhanced chat with product search and recommendations
        
        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            user_id: Optional user ID for personalization
            
        Returns:
            {
                "message": "AI response text",
                "products": [...],  # Suggested products if any
                "intent": "..."     # Detected intent
            }
        """
        client = cls.get_client()
        
        # Get last user message for intent detection
        last_message = next((m for m in reversed(messages) if m["role"] == "user"), None)
        if not last_message:
            return {
                "message": "Hello! How can I help you today?",
                "products": [],
                "intent": "general"
            }
        
        # Detect intent
        intent_data = cls.detect_intent(last_message["content"])
        intent = intent_data["intent"]
        
        # Search products if needed
        products = []
        product_context = ""
        
        if intent == "product_search":
            # Search for products based on user query
            # Extract meaningful keywords from user message
            search_keywords = cls.extract_search_keywords(last_message["content"])
            category = intent_data.get("category")
            
            # Search by extracted keywords for better accuracy
            products = cls.search_products(
                query=search_keywords,
                category=category,
                limit=5
            )
            
            if products:
                product_context = f"\n\nAvailable products matching the query:\n"
                for i, p in enumerate(products, 1):
                    price_str = f"${p['price']:.2f}"
                    if p.get('on_sale') and p.get('original_price'):
                        price_str = f"${p['price']:.2f} (was ${p['original_price']:.2f})"
                    product_context += f"{i}. {p['name']} - {price_str} - {p['category']}\n"
                    if p.get('description'):
                        product_context += f"   Description: {p['description']}\n"
                    product_context += f"   Stock: {p['stock']} available\n"
                product_context += "\n**IMPORTANT**: Only mention the EXACT product information provided above. DO NOT make up or invent descriptions, features, or details that are not listed. If no description is given, just mention the product name, price, and availability."
                product_context += "\n\n**REQUIRED FDA DISCLAIMER**: You MUST include this exact disclaimer in your response: 'These statements have not been evaluated by the FDA. This product is not intended to diagnose, treat, cure, or prevent any disease.'"
        
        elif intent == "recommendations":
            # Get featured products
            products = cls.get_featured_products(limit=4)
            if products:
                product_context = f"\n\nFeatured products to recommend:\n"
                for i, p in enumerate(products, 1):
                    price_str = f"${p['price']:.2f}"
                    if p.get('on_sale') and p.get('original_price'):
                        price_str = f"${p['price']:.2f} (was ${p['original_price']:.2f})"
                    product_context += f"{i}. {p['name']} - {price_str} - {p['category']}\n"
                    if p.get('description'):
                        product_context += f"   Description: {p['description']}\n"
                    product_context += f"   Stock: {p['stock']} available\n"
                product_context += "\n**IMPORTANT**: Only recommend the EXACT products listed above. DO NOT make up product names or details."
                product_context += "\n\n**REQUIRED FDA DISCLAIMER**: You MUST include this exact disclaimer in your response: 'These statements have not been evaluated by the FDA. This product is not intended to diagnose, treat, cure, or prevent any disease.'"
        
        # Build enhanced prompt with product context
        enhanced_system = SYSTEM_PROMPT
        if product_context:
            enhanced_system += product_context
        
        # Build full message list
        full_messages = [{"role": "system", "content": enhanced_system}]
        full_messages.extend(messages)
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=full_messages,
                max_tokens=400,
                temperature=0.7,
            )
            
            ai_message = response.choices[0].message.content
            
            return {
                "message": ai_message,
                "products": products,
                "intent": intent
            }
            
        except Exception as e:
            # Log error and return fallback with products if available
            print(f"OpenAI API error: {e}")
            
            # Provide fallback response with products
            if products:
                fallback_msg = "I found some products for you! Check them out below. "
                fallback_msg += "Let me know if you need more information or have questions."
            else:
                fallback_msg = "Sorry, I'm having trouble right now. Please try again or contact our support team."
            
            return {
                "message": fallback_msg,
                "products": products,
                "intent": intent
            }
