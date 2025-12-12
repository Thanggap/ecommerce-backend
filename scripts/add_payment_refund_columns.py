"""
Add payment and refund columns to orders table
Run: python scripts/add_payment_refund_columns.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db import get_db_session

def add_payment_refund_columns():
    """Add payment_intent_id and refund columns to orders table"""
    db = get_db_session()
    try:
        print("Adding payment and refund columns to orders table...")
        
        # Add columns
        db.execute(text("""
            ALTER TABLE orders 
            ADD COLUMN IF NOT EXISTS payment_intent_id VARCHAR(255),
            ADD COLUMN IF NOT EXISTS refund_id VARCHAR(255),
            ADD COLUMN IF NOT EXISTS refund_amount FLOAT,
            ADD COLUMN IF NOT EXISTS refund_reason TEXT,
            ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMP;
        """))
        
        db.commit()
        print("✅ Successfully added columns:")
        print("   - payment_intent_id (for Stripe payment tracking)")
        print("   - refund_id (for Stripe refund tracking)")
        print("   - refund_amount (refund amount in USD)")
        print("   - refund_reason (reason for refund)")
        print("   - refunded_at (timestamp when refunded)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding columns: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_payment_refund_columns()
