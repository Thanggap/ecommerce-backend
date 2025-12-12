"""
Quick migration - Add refund columns to orders table
Run this to fix the error
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use environment variable for database URL
from app.config import DATABASE_URL
import psycopg2

def run_migration():
    """Add payment and refund columns to orders table"""
    
    # Parse DATABASE_URL
    print(f"Connecting to database...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("Adding refund columns to orders table...")
        
        # Add columns one by one (safer than all at once)
        migrations = [
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_intent_id VARCHAR(255);",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_id VARCHAR(255);",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_amount FLOAT;",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_reason TEXT;",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMP;",
        ]
        
        for sql in migrations:
            cursor.execute(sql)
            print(f"✅ Executed: {sql[:50]}...")
        
        conn.commit()
        
        # Verify columns
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'orders' 
            AND column_name IN ('payment_intent_id', 'refund_id', 'refund_amount', 'refund_reason', 'refunded_at')
            ORDER BY column_name;
        """)
        
        columns = cursor.fetchall()
        
        print("\n✅ Migration successful! Added columns:")
        for col in columns:
            print(f"   - {col[0]} ({col[1]})")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Database updated successfully!")
        print("You can now create orders with refund support.")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nTrying alternative method...")
        
        # Alternative: Use SQLAlchemy
        try_sqlalchemy_migration()

def try_sqlalchemy_migration():
    """Alternative migration using SQLAlchemy"""
    from sqlalchemy import create_engine, text
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        migrations = [
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_intent_id VARCHAR(255);",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_id VARCHAR(255);",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_amount FLOAT;",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_reason TEXT;",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMP;",
        ]
        
        for sql in migrations:
            conn.execute(text(sql))
            print(f"✅ {sql[:50]}...")
        
        conn.commit()
        print("\n✅ Migration successful via SQLAlchemy!")

if __name__ == "__main__":
    print("=== Running Refund Columns Migration ===\n")
    run_migration()
