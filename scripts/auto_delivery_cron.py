#!/usr/bin/env python3
"""
Cron job script to auto-mark shipped orders as delivered after 14 days
Run daily: 0 2 * * * /path/to/ecommerce-backend/scripts/auto_delivery_cron.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.auto_delivery_service import AutoDeliveryService


if __name__ == "__main__":
    print("[Auto-Delivery Cron] Starting auto-delivery job...")
    
    result = AutoDeliveryService.process_auto_delivery(dry_run=False)
    
    if result.get("success"):
        print(f"[Auto-Delivery Cron] SUCCESS - Updated {result['updated_count']} orders")
        print(f"[Auto-Delivery Cron] Order IDs: {result['updated_order_ids']}")
    else:
        print(f"[Auto-Delivery Cron] FAILED - {result.get('error')}")
        sys.exit(1)
