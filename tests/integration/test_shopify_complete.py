#!/usr/bin/env python3
"""
Test Complete Shopify Gateway Implementation
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

def test_gateway(gateway, name, test_card):
    """Test a single gateway"""
    print(f"\n{'='*70}")
    print(f"Testing {name}")
    print(f"{'='*70}")
    print(f"Store: {gateway.store_url}")
    print(f"Charge: {gateway.charge_amount}")
    print(f"\nTesting with card: {test_card[:4]}...{test_card[-4:]}")
    
    try:
        status, message, card_type = gateway.check(test_card)
        
        print(f"\n✅ Result:")
        print(f"  Status: {status}")
        print(f"  Message: {message}")
        print(f"  Card Type: {card_type}")
        
        return status != "error"
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║          COMPLETE SHOPIFY GATEWAY TEST                    ║
║          Testing All 4 Price Tiers                        ║
╚════════════════════════════════════════════════════════════╝
""")
    
    # Test card (this will likely decline but should process)
    test_card = "4118104014949771|02|34|001"
    
    results = []
    
    # Test Penny Gate
    penny = ShopifyPennyGateway()
    results.append(("Penny Gate ($1-$2)", test_gateway(penny, "Penny Gate ($1-$2)", test_card)))
    
    # Test Low Gate
    low = ShopifyLowGateway()
    results.append(("Low Gate ($4-$10)", test_gateway(low, "Low Gate ($4-$10)", test_card)))
    
    # Test Medium Gate
    medium = ShopifyMediumGateway()
    results.append(("Medium Gate ($12-$18)", test_gateway(medium, "Medium Gate ($12-$18)", test_card)))
    
    # Test High Gate
    high = ShopifyHighGateway()
    results.append(("High Gate ($45-$1000)", test_gateway(high, "High Gate ($45-$1000)", test_card)))
    
    # Summary
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}\n")
    
    for name, success in results:
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"{name:30} : {status}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    
    print(f"\n{'='*70}")
    print(f"Total: {passed}/{total} gates working")
    print(f"{'='*70}\n")
    
    if passed == total:
        print("🎉 All Shopify gates are working!")
    elif passed > 0:
        print(f"⚠️  {passed} out of {total} gates working")
    else:
        print("❌ No gates working - check implementation")

if __name__ == "__main__":
    main()
