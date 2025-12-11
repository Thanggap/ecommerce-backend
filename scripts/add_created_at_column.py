"""
Script để add created_at column vào products table nếu chưa có
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db import get_db_session

def add_created_at_column():
    db = get_db_session()
    
    try:
        # Check if column exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='products' AND column_name='created_at'
        """))
        
        if result.fetchone():
            print("Column 'created_at' already exists in products table")
            return
        
        # Add column
        print("Adding 'created_at' column to products table...")
        db.execute(text("""
            ALTER TABLE products 
            ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """))
        db.commit()
        print("Successfully added 'created_at' column")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_created_at_column()
