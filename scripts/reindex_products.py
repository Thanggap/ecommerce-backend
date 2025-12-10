"""
Re-index script to sync all existing products from PostgreSQL to Elasticsearch
Run this after setting up Elasticsearch for the first time
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import get_db_session
from app.models.sqlalchemy import Product
from app.search.product_sync import bulk_index_products
from app.search.product_index import ensure_product_index, get_index_stats
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def reindex_all_products():
    """
    Fetch all products from PostgreSQL and index them to Elasticsearch
    """
    logger.info("Starting re-index process...")
    
    # Ensure index exists
    logger.info("Ensuring Elasticsearch index exists...")
    ensure_product_index()
    
    # Get database session
    db = get_db_session()
    
    try:
        # Fetch all products
        logger.info("Fetching all products from PostgreSQL...")
        products = db.query(Product).all()
        total_products = len(products)
        
        if total_products == 0:
            logger.warning("No products found in database!")
            return
        
        logger.info(f"Found {total_products} products to index")
        
        # Bulk index in batches of 100
        batch_size = 100
        total_indexed = 0
        total_failed = 0
        
        for i in range(0, total_products, batch_size):
            batch = products[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_products + batch_size - 1) // batch_size
            
            logger.info(f"Indexing batch {batch_num}/{total_batches} ({len(batch)} products)...")
            
            result = bulk_index_products(batch)
            total_indexed += result["success"]
            total_failed += result["failed"]
            
            if result["failed"] > 0:
                logger.error(f"Batch {batch_num} had {result['failed']} failures")
                for error in result["errors"][:5]:  # Show first 5 errors
                    logger.error(f"  - {error}")
        
        # Summary
        logger.info("=" * 60)
        logger.info("Re-index Summary:")
        logger.info(f"  Total products in DB: {total_products}")
        logger.info(f"  Successfully indexed: {total_indexed}")
        logger.info(f"  Failed: {total_failed}")
        logger.info("=" * 60)
        
        # Get index stats
        stats = get_index_stats()
        if "doc_count" in stats:
            logger.info(f"Elasticsearch index now contains {stats['doc_count']} documents")
        
        if total_failed == 0:
            logger.info("✅ Re-index completed successfully!")
        else:
            logger.warning(f"⚠️  Re-index completed with {total_failed} failures")
            
    except Exception as e:
        logger.error(f"Re-index failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Re-index products to Elasticsearch")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm re-indexing (required to prevent accidental runs)"
    )
    
    args = parser.parse_args()
    
    if not args.confirm:
        print("⚠️  This will re-index ALL products to Elasticsearch.")
        print("   Run with --confirm flag to proceed:")
        print("   python scripts/reindex_products.py --confirm")
        sys.exit(0)
    
    reindex_all_products()
