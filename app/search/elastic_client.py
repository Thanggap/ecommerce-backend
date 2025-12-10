"""
Elasticsearch client module
Provides singleton access to Elasticsearch connection
Supports both local development and Elastic Cloud with API key
"""
from elasticsearch import Elasticsearch
from functools import lru_cache
import os
import logging

logger = logging.getLogger(__name__)

ELASTIC_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTIC_API_KEY = os.getenv("ELASTICSEARCH_API_KEY")  # For Elastic Cloud


@lru_cache(maxsize=1)
def get_es_client() -> Elasticsearch:
    """
    Get Elasticsearch client instance (singleton pattern)
    Supports:
    - Local development: http://localhost:9200
    - Elastic Cloud: https://... with API key authentication
    
    Returns:
        Elasticsearch: ES client instance
    """
    try:
        # Check if using Elastic Cloud (API key auth)
        if ELASTIC_API_KEY:
            logger.info("Connecting to Elastic Cloud with API key authentication")
            client = Elasticsearch(
                ELASTIC_URL,
                api_key=ELASTIC_API_KEY,
                request_timeout=60,
                retry_on_timeout=True,
                max_retries=3,
                verify_certs=True,  # Enable SSL verification for cloud
            )
        else:
            # Local development mode
            logger.info("Connecting to local Elasticsearch")
            client = Elasticsearch(
                ELASTIC_URL,
                request_timeout=60,
                retry_on_timeout=True,
                max_retries=3
            )
        
        # Test connection
        if client.ping():
            logger.info(f"Successfully connected to Elasticsearch at {ELASTIC_URL}")
        else:
            logger.warning(f"Elasticsearch ping failed at {ELASTIC_URL}")
            
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {e}")
        raise


def check_es_health() -> dict:
    """
    Check Elasticsearch cluster health
    Returns:
        dict: Health status information
    """
    try:
        es = get_es_client()
        health = es.cluster.health()
        return {
            "status": health["status"],
            "cluster_name": health["cluster_name"],
            "number_of_nodes": health["number_of_nodes"],
            "active_shards": health["active_shards"],
        }
    except Exception as e:
        logger.error(f"Failed to check ES health: {e}")
        return {"status": "unavailable", "error": str(e)}
