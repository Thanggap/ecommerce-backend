"""
Search router for Elasticsearch-powered product search
Provides advanced search capabilities with Vietnamese text support
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from app.search.elastic_client import get_es_client, check_es_health
from app.search.product_index import INDEX_NAME, get_index_stats
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/health")
def elasticsearch_health():
    """
    Check Elasticsearch health status
    """
    return check_es_health()


@router.get("/stats")
def index_statistics():
    """
    Get product index statistics
    """
    return get_index_stats()


@router.get("/products")
def search_products(
    q: Optional[str] = Query(None, min_length=1, description="Search query"),
    product_type: Optional[str] = Query(None, description="Filter by product type"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    on_sale: Optional[bool] = Query(None, description="Filter products on sale"),
    page: int = Query(0, ge=0, description="Page number (0-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query("relevance", description="Sort by: relevance, price_asc, price_desc, newest")
):
    """
    Search products with Elasticsearch
    
    Features:
    - Vietnamese text support with diacritics handling
    - Fuzzy matching for typo tolerance
    - Multi-field search (name, description, ingredients, etc.)
    - Price range filtering
    - Product type filtering
    - Sale items filtering
    - Pagination
    - Multiple sort options
    
    Args:
        q: Search query string (optional, returns all if not provided)
        product_type: Filter by product type (e.g., "Vitamins & Minerals")
        min_price: Minimum price filter
        max_price: Maximum price filter
        on_sale: Filter only products with sale_price
        page: Page number (0-indexed)
        limit: Items per page (1-100)
        sort_by: Sort order (relevance, price_asc, price_desc, newest)
        
    Returns:
        dict: Search results with items, total, page info
    """
    try:
        es = get_es_client()
        
        # Build query
        must = []
        filter_queries = []
        
        # Search query
        if q:
            must.append({
                "multi_match": {
                    "query": q,
                    "fields": [
                        "product_name^4",           # Highest priority
                        "product_name.autocomplete^3",
                        "blurb^2",
                        "description^2",
                        "ingredients",
                        "usage_instructions",
                        "health_benefits",
                    ],
                    "fuzziness": "AUTO",            # Typo tolerance
                    "operator": "or",
                    "minimum_should_match": "75%"   # Relevance threshold
                }
            })
        
        # Filter: product_type
        if product_type:
            filter_queries.append({"term": {"product_type": product_type}})
        
        # Filter: price range
        if min_price is not None or max_price is not None:
            price_range = {}
            if min_price is not None:
                price_range["gte"] = min_price
            if max_price is not None:
                price_range["lte"] = max_price
            filter_queries.append({"range": {"price": price_range}})
        
        # Filter: on_sale
        if on_sale:
            filter_queries.append({"term": {"has_sale": True}})
        
        # Build query body
        query_body = {
            "query": {
                "bool": {
                    "must": must if must else [{"match_all": {}}],
                    "filter": filter_queries
                }
            },
            "from": page * limit,
            "size": limit,
        }
        
        # Sort
        if sort_by == "price_asc":
            query_body["sort"] = [{"price": {"order": "asc"}}]
        elif sort_by == "price_desc":
            query_body["sort"] = [{"price": {"order": "desc"}}]
        elif sort_by == "newest":
            query_body["sort"] = [{"created_at": {"order": "desc"}}]
        # else: relevance (default _score)
        
        # Execute search
        result = es.search(index=INDEX_NAME, body=query_body)
        
        # Format results
        hits = result["hits"]["hits"]
        total = result["hits"]["total"]["value"]
        
        products = []
        for hit in hits:
            source = hit["_source"]
            products.append({
                "id": source["id"],
                "product_name": source["product_name"],
                "slug": source["slug"],
                "product_type": source.get("product_type"),
                "price": source["price"],
                "sale_price": source.get("sale_price"),
                "stock": source.get("stock", 0),
                "image_url": source.get("image_url"),
                "blurb": source.get("blurb"),
                "has_sale": source.get("has_sale", False),
                "discount_percentage": source.get("discount_percentage", 0),
                "score": hit["_score"]  # Relevance score
            })
        
        return {
            "items": products,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,  # Ceiling division
            "query": q,
            "took_ms": result["took"]  # Search time in milliseconds
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/autocomplete")
def autocomplete_search(
    q: str = Query(..., min_length=2, description="Autocomplete query"),
    limit: int = Query(5, ge=1, le=10, description="Max suggestions")
):
    """
    Autocomplete suggestions for search
    
    Args:
        q: Query string (min 2 chars)
        limit: Maximum suggestions to return
        
    Returns:
        list: Suggested product names
    """
    try:
        es = get_es_client()
        
        result = es.search(
            index=INDEX_NAME,
            body={
                "query": {
                    "match": {
                        "product_name.autocomplete": {
                            "query": q,
                            "operator": "and"
                        }
                    }
                },
                "size": limit,
                "_source": ["product_name", "product_type"]
            }
        )
        
        suggestions = []
        for hit in result["hits"]["hits"]:
            source = hit["_source"]
            suggestions.append({
                "name": source["product_name"],
                "type": source.get("product_type")
            })
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Autocomplete failed: {e}")
        return {"suggestions": []}


@router.get("/aggregations")
def search_aggregations(
    q: Optional[str] = Query(None, description="Search query for aggregations")
):
    """
    Get aggregations (facets) for search results
    Useful for showing filter options with counts
    
    Args:
        q: Optional search query to scope aggregations
        
    Returns:
        dict: Aggregation results (product types, price ranges)
    """
    try:
        es = get_es_client()
        
        # Base query
        query = {
            "match_all": {}
        }
        if q:
            query = {
                "multi_match": {
                    "query": q,
                    "fields": ["product_name^3", "blurb", "description"],
                    "fuzziness": "AUTO"
                }
            }
        
        result = es.search(
            index=INDEX_NAME,
            body={
                "query": query,
                "size": 0,  # Don't return documents, just aggregations
                "aggs": {
                    "product_types": {
                        "terms": {
                            "field": "product_type",
                            "size": 20
                        }
                    },
                    "price_ranges": {
                        "range": {
                            "field": "price",
                            "ranges": [
                                {"key": "under_100k", "to": 100000},
                                {"key": "100k_500k", "from": 100000, "to": 500000},
                                {"key": "500k_1m", "from": 500000, "to": 1000000},
                                {"key": "over_1m", "from": 1000000}
                            ]
                        }
                    },
                    "on_sale_count": {
                        "filter": {"term": {"has_sale": True}}
                    }
                }
            }
        )
        
        aggs = result["aggregations"]
        
        return {
            "product_types": [
                {"type": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggs["product_types"]["buckets"]
            ],
            "price_ranges": [
                {"range": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggs["price_ranges"]["buckets"]
            ],
            "on_sale_count": aggs["on_sale_count"]["doc_count"]
        }
        
    except Exception as e:
        logger.error(f"Aggregations failed: {e}")
        raise HTTPException(status_code=500, detail="Aggregations failed")
