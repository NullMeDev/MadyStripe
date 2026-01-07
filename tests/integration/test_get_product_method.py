#!/usr/bin/env python3
"""
Test the _get_cheapest_product method directly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.shopify_gateway_real import RealShopifyGateway

stores = [
    'turningpointe.myshopify.com',
    'smekenseducation.myshopify.com',
    'buger.myshopify.com'
]

print("="*70)
print("TESTING _get_cheapest_product METHOD")
print("="*70)

for store in stores:
    print(f"\n{'='*70}")
    print(f"Testing: {store}")
    print(f"{'='*70}")
    
    gateway = RealShopifyGateway(store)
    
    try:
        product_info = gateway._get_cheapest_product(None)
        
        if product_info:
            print(f"✅ Product Found:")
            print(f"  Title: {product_info['title']}")
            print(f"  Price: ${product_info['price']}")
            print(f"  Variant ID: {product_info['variant_id']}")
        else:
            print(f"❌ No product returned (None)")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

print(f"\n{'='*70}")
print("TEST COMPLETE")
print(f"{'='*70}")
