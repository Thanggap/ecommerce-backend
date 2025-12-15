"""
Update image URLs for existing products
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_db_session
from app.models.sqlalchemy import Product

# Real supplement image URLs from Unsplash
SUPPLEMENT_IMAGES = [
    "https://images.unsplash.com/photo-1607619056574-7b8d3ee536b2?w=500&h=500&fit=crop",
    "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&h=500&fit=crop",
    "https://images.unsplash.com/photo-1550572017-4a6e8c296b7e?w=500&h=500&fit=crop",
    "https://images.unsplash.com/photo-1612929633738-8fe44f7ec841?w=500&h=500&fit=crop",
    "https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=500&h=500&fit=crop",
    "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500&h=500&fit=crop",
    "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?w=500&h=500&fit=crop",
    "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&h=500&fit=crop",
    "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=500&h=500&fit=crop",
    "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&h=500&fit=crop",
    "https://images.unsplash.com/photo-1579722820308-d74e571900a9?w=500&h=500&fit=crop",
    "https://images.unsplash.com/photo-1593095948071-474c5cc2989d?w=500&h=500&fit=crop",
    "https://images.unsplash.com/photo-1594737626072-90dc274bc2bd?w=500&h=500&fit=crop",
    "https://images.unsplash.com/photo-1541534741688-6078c6bfb5c5?w=500&h=500&fit=crop",
    "https://images.unsplash.com/photo-1610970881699-44a5587cabec?w=500&h=500&fit=crop",
]

def main():
    print("🔄 Updating product image URLs...")
    
    db = get_db_session()
    
    try:
        products = db.query(Product).all()
        total = len(products)
        
        print(f"Found {total} products to update")
        
        for idx, product in enumerate(products):
            # Cycle through available images
            product.image_url = SUPPLEMENT_IMAGES[idx % len(SUPPLEMENT_IMAGES)]
            
            if (idx + 1) % 10 == 0:
                print(f"  Updated {idx + 1}/{total} products...")
        
        db.commit()
        print(f"\n✅ Successfully updated {total} product images!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
