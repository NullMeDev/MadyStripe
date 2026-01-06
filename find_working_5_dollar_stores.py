#!/usr/bin/env python3
"""
Find working $5 Shopify stores by testing them
"""

import sys
sys.path.insert(0, '/home/null/Desktop/MadyStripe')

from core.shopify_gateway_fixed import FixedShopifyGateway
import time

# Get different $5 stores from our validated list
test_stores = [
    'escnet.myshopify.com',
    'sandf.myshopify.com',
    'lament.myshopify.com',
    'theaterchurch.myshopify.com',
    'isimple.myshopify.com',
    'matias.myshopify.com',
    'liddelton.myshopify.com',
    'performancetrainingsystems.myshopify.com'
]

# Test card
test_card = "4677851515520336|12|25|395"

print("="*70)
print("TESTING $5 STORES")
print("="*70)

working_stores = []

for store in test_stores:
    print(f"\n🔍 Testing: {store}")
    
    try:
        gateway = FixedShopifyGateway(store)
        
        # Quick test
        status, message, card_type = gateway.check(test_card)
        
        print(f"   Status: {status}")
        print(f"   Message: {message}")
        
        if status == 'approved':
            print(f"   ✅ WORKING!")
            working_stores.append(store)
        elif 'No products' in message or 'Failed to add' in message:
            print(f"   ❌ Store issue")
        else:
            print(f"   ⚠️ {message}")
        
        time.sleep(2)  # Rate limiting
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    if len(working_stores) >= 5:
        break

print(f"\n\n{'='*70}")
print(f"WORKING $5 STORES FOUND: {len(working_stores)}")
print(f"{'='*70}\n")

for i, store in enumerate(working_stores, 1):
    print(f"{i}. {store}")

if len(working_stores) >= 5:
    print("\n✅ Found enough working stores!")
    print("\nReplace in core/shopify_price_gateways.py:")
    print("STORES = [")
    for store in working_stores:
        print(f"    '{store}',")
    print("]")
else:
    print(f"\n⚠️ Only found {len(working_stores)} working stores")
    print("May need to test more stores")
