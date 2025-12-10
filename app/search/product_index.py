"""
Product index configuration and management for Elasticsearch
Includes Vietnamese text analyzer support
"""
from elasticsearch import NotFoundError
from .elastic_client import get_es_client
import os
import logging

logger = logging.getLogger(__name__)

INDEX_NAME = os.getenv("ELASTICSEARCH_INDEX_PRODUCTS", "products")

# Vietnamese-optimized index mapping with custom analyzer
PRODUCT_INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "vietnamese_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "asciifolding",  # Convert Vietnamese diacritics
                        "word_delimiter"
                    ]
                },
                "autocomplete_analyzer": {
                    "type": "custom",
                    "tokenizer": "edge_ngram_tokenizer",
                    "filter": ["lowercase", "asciifolding"]
                }
            },
            "tokenizer": {
                "edge_ngram_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 10,
                    "token_chars": ["letter", "digit"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            # Core fields
            "id": {"type": "keyword"},
            "product_name": {
                "type": "text",
                "analyzer": "vietnamese_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "autocomplete": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer"
                    }
                }
            },
            "slug": {"type": "keyword"},
            
            # Category & Classification
            "product_type": {"type": "keyword"},
            "brand": {"type": "keyword"},
            "manufacturer": {"type": "keyword"},
            "country_of_origin": {"type": "keyword"},
            
            # Pricing
            "price": {"type": "float"},
            "sale_price": {"type": "float"},
            "stock": {"type": "integer"},
            
            # Text fields with Vietnamese support
            "blurb": {
                "type": "text",
                "analyzer": "vietnamese_analyzer"
            },
            "description": {
                "type": "text",
                "analyzer": "vietnamese_analyzer"
            },
            "ingredients": {
                "type": "text",
                "analyzer": "vietnamese_analyzer"
            },
            "usage_instructions": {
                "type": "text",
                "analyzer": "vietnamese_analyzer"
            },
            "warnings": {
                "type": "text",
                "analyzer": "vietnamese_analyzer"
            },
            "health_benefits": {
                "type": "text",
                "analyzer": "vietnamese_analyzer"
            },
            "certifications": {"type": "text"},
            
            # Dates
            "expiry_date": {"type": "date"},
            "created_at": {"type": "date"},
            
            # Image
            "image_url": {"type": "keyword", "index": False},
            
            # Computed fields
            "has_sale": {"type": "boolean"},
            "discount_percentage": {"type": "float"}
        }
    }
}


def ensure_product_index():
    """
    Create product index if it doesn't exist
    Safe to call multiple times (idempotent)
    """
    try:
        es = get_es_client()
        
        if not es.indices.exists(index=INDEX_NAME):
            logger.info(f"Creating index: {INDEX_NAME}")
            es.indices.create(index=INDEX_NAME, body=PRODUCT_INDEX_MAPPING)
            logger.info(f"Index {INDEX_NAME} created successfully")
        else:
            logger.info(f"Index {INDEX_NAME} already exists")
            
    except Exception as e:
        logger.error(f"Failed to ensure product index: {e}")
        # Don't raise - allow app to start even if ES is down
        

def delete_product_index():
    """
    Delete product index (use for testing/reset)
    """
    try:
        es = get_es_client()
        if es.indices.exists(index=INDEX_NAME):
            es.indices.delete(index=INDEX_NAME)
            logger.info(f"Deleted index: {INDEX_NAME}")
    except Exception as e:
        logger.error(f"Failed to delete index: {e}")
        

def get_index_stats():
    """
    Get statistics about the product index
    Returns:
        dict: Index statistics including doc count
    """
    try:
        es = get_es_client()
        stats = es.indices.stats(index=INDEX_NAME)
        return {
            "index_name": INDEX_NAME,
            "doc_count": stats["indices"][INDEX_NAME]["total"]["docs"]["count"],
            "store_size": stats["indices"][INDEX_NAME]["total"]["store"]["size_in_bytes"],
        }
    except Exception as e:
        logger.error(f"Failed to get index stats: {e}")
        return {"error": str(e)}
