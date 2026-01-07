#!/usr/bin/env python3
"""
Test full Shopify API Gateway flow with a test card
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.shopify_api_gateway import ShopifyAPIGateway

def test_gateway():
    """Test the Shopify API Gateway"""
    print("="*60)
    print("SHOPIFY API GATEWAY - FULL TEST")
    print("="*60)
    
    # Initialize gateway
    gateway = ShopifyAPIGateway()
    print(f"\nLoaded {len(gateway.stores)} stores")
    
    # Show first few stores
    print("\nFirst 5 stores:")
    for i, store in enumerate(gateway.stores[:5]):
        priority = "PRIORITY" if store.get('priority') else ""
        print(f"  {i+1}. {store['url']} {priority}")
    
    # Test with a test card (Stripe test card - will be declined but shows flow)
    test_card = "4242424242424242|12|25|123"
    print(f"\nTesting card: {test_card}")
    print("-"*60)
    
    status, message, card_type = gateway.check(test_card)
    
    print("-"*60)
    print(f"Result: {status}")
    print(f"Message: {message}")
    print(f"Card Type: {card_type}")
    print("="*60)
    
    return status, message


if __name__ == "__main__":
    test_gateway()
