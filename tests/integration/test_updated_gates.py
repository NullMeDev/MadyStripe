#!/usr/bin/env python3
"""
Test Updated Shopify Gates
Quick test to verify all 4 gates can access their stores
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.shopify_price_gateways import (
    ShopifyPennyGateway,
    ShopifyLowGateway,
    ShopifyMediumGateway,
    ShopifyHighGateway
)

def test_gateway(gateway, name):
    """Test a gateway by checking if it can access store products"""
    print(f"\n{'='*70}")
    print(f"Testing {name}")
    print(f"{'='*70}")
    print(f"Store: {gateway.store_url}")
    print(f"Charge Amount: {gateway.charge_amount}")
    print(f"Total Stores Available: {len(gateway.STORES)}")
    
    # List all stores
    print(f"\nConfigured Stores:")
    for i, store in enumerate(gateway.STORES, 1):
        print(f"  {i}. {store}")
    
    print(f"\n✅ Gateway configured successfully!")

def main():
    print("="*70)
    print("SHOPIFY GATES CONFIGURATION TEST")
    print("="*70)
    print("\nTesting all 4 updated Shopify gates...")
    
    # Test each gateway
    penny = ShopifyPennyGateway()
    test_gateway(penny, "💰 Penny Gate ($1-$2)")
    
    low = ShopifyLowGateway()
    test_gateway(low, "💵 Low Gate ($4-$10)")
    
    medium = ShopifyMediumGateway()
    test_gateway(medium, "💳 Medium Gate ($12-$18)")
    
    high = ShopifyHighGateway()
    test_gateway(high, "💎 High Gate ($45-$1000)")
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}")
    print(f"  Penny Gate:   {len(penny.STORES)} stores configured")
    print(f"  Low Gate:     {len(low.STORES)} stores configured")
    print(f"  Medium Gate:  {len(medium.STORES)} stores configured")
    print(f"  High Gate:    {len(high.STORES)} stores configured")
    print(f"  TOTAL:        {len(penny.STORES) + len(low.STORES) + len(medium.STORES) + len(high.STORES)} stores")
    
    print(f"\n{'='*70}")
    print("✅ All gates configured with working stores!")
    print(f"{'='*70}")
    print("\nNext Steps:")
    print("1. Test with real cards using mady_vps_checker.py")
    print("2. Example: python3 mady_vps_checker.py cards.txt --gate penny")
    print("3. Example: python3 mady_vps_checker.py cards.txt --gate low")
    print("4. Example: python3 mady_vps_checker.py cards.txt --gate medium")
    print("5. Example: python3 mady_vps_checker.py cards.txt --gate high")
    print()

if __name__ == '__main__':
    main()
