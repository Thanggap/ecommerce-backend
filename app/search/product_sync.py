"""
Product synchronization utilities for Elasticsearch
Handles indexing, updating, and deletion of products in ES with proper error handling
"""
from .elastic_client import get_es_client
from .product_index import INDEX_NAME
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def map_product_to_es_doc(product) -> dict:
    """
    Map SQLAlchemy Product model to Elasticsearch document
    
    Args:
        product: Product model instance
        
    Returns:
        dict: Elasticsearch document
    """
    # Calculate has_sale and discount_percentage
    has_sale = product.sale_price is not None and product.sale_price < product.price
    discount_percentage = 0.0
    
    if has_sale:
        discount_percentage = ((product.price - product.sale_price) / product.price) * 100
    
    return {
        "id": str(product.id),
        "product_name": product.product_name,
        "slug": product.slug,
        "product_type": product.product_type,
        "brand": getattr(product, "brand", None),
        "manufacturer": getattr(product, "manufacturer", None),
        "country_of_origin": getattr(product, "country_of_origin", None),
        "price": float(product.price) if product.price else 0.0,
        "sale_price": float(product.sale_price) if product.sale_price else None,
        "stock": product.stock if hasattr(product, "stock") else 0,
        "blurb": product.blurb,
        "description": product.description,
        "ingredients": getattr(product, "ingredients", None),
        "usage_instructions": getattr(product, "usage_instructions", None),
        "warnings": getattr(product, "warnings", None),
        "health_benefits": getattr(product, "health_benefits", None),
        "certifications": getattr(product, "certifications", None),
        "expiry_date": product.expiry_date.isoformat() if hasattr(product, "expiry_date") and product.expiry_date else None,
        "created_at": product.created_at.isoformat() if hasattr(product, "created_at") and product.created_at else datetime.utcnow().isoformat(),
        "image_url": product.image_url if hasattr(product, "image_url") else None,
        "has_sale": has_sale,
        "discount_percentage": round(discount_percentage, 2)
    }


def index_product(product) -> bool:
    """
    Index a single product to Elasticsearch
    
    Args:
        product: Product model instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        es = get_es_client()
        doc = map_product_to_es_doc(product)
        
        result = es.index(
            index=INDEX_NAME,
            id=str(product.id),
            document=doc,
            refresh=True  # Make immediately searchable (dev mode)
        )
        
        logger.info(f"Indexed product {product.id} ({product.product_name}) - result: {result['result']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to index product {product.id}: {e}", exc_info=True)
        # Don't raise - allow the main operation to continue
        return False


def bulk_index_products(products: list) -> dict:
    """
    Bulk index multiple products to Elasticsearch
    More efficient for large batches
    
    Args:
        products: List of Product model instances
        
    Returns:
        dict: Statistics about the bulk operation
    """
    try:
        es = get_es_client()
        
        # Prepare bulk actions
        actions = []
        for product in products:
            doc = map_product_to_es_doc(product)
            actions.append({
                "_index": INDEX_NAME,
                "_id": str(product.id),
                "_source": doc
            })
        
        if not actions:
            return {"success": 0, "failed": 0, "errors": []}
        
        # Execute bulk operation
        from elasticsearch.helpers import bulk
        success, failed = bulk(es, actions, raise_on_error=False, refresh=True)
        
        logger.info(f"Bulk indexed {success} products, {len(failed)} failed")
        
        return {
            "success": success,
            "failed": len(failed),
            "errors": [str(f) for f in failed] if failed else []
        }
        
    except Exception as e:
        logger.error(f"Bulk index failed: {e}", exc_info=True)
        return {"success": 0, "failed": len(products), "errors": [str(e)]}


def update_product_in_index(product) -> bool:
    """
    Update an existing product in Elasticsearch
    Same as index_product (ES handles create or update)
    
    Args:
        product: Product model instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    return index_product(product)


def delete_product_from_index(product_id: int) -> bool:
    """
    Delete a product from Elasticsearch index
    
    Args:
        product_id: Product ID to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        es = get_es_client()
        
        result = es.delete(
            index=INDEX_NAME,
            id=str(product_id),
            ignore=[404],  # Ignore if already deleted
            refresh=True
        )
        
        logger.info(f"Deleted product {product_id} from index - result: {result.get('result', 'not_found')}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete product {product_id} from index: {e}", exc_info=True)
        return False


def search_products_by_name(query: str, limit: int = 10) -> list:
    """
    Simple search function for testing
    
    Args:
        query: Search query string
        limit: Maximum results to return
        
    Returns:
        list: List of matching products
    """
    try:
        es = get_es_client()
        
        result = es.search(
            index=INDEX_NAME,
            query={
                "multi_match": {
                    "query": query,
                    "fields": ["product_name^3", "blurb^2", "description"],
                    "fuzziness": "AUTO"
                }
            },
            size=limit
        )
        
        hits = result["hits"]["hits"]
        return [hit["_source"] for hit in hits]
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []
