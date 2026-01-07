#!/usr/bin/env python3
"""Test store cycling functionality with the validated store database"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.shopify_api_gateway import ShopifyAPIGateway

def test_store_loading():
    """Test that stores are loaded from the database"""
    print("="*60)
    print("STORE CYCLING TEST")
    print("="*60)
    
    gateway = ShopifyAPIGateway()
    
    print(f"\nTotal stores loaded: {len(gateway.stores)}")
    
    # Count pre-validated stores
    pre_validated = [s for s in gateway.stores if s.get('pre_validated')]
    print(f"Pre-validated stores: {len(pre_validated)}")
    
    # Show first 10 stores
    print("\nFirst 10 stores:")
    for i, store in enumerate(gateway.stores[:10]):
        variant = store.get('variant_id', 'N/A')
        if variant and len(variant) > 15:
            variant = variant[:15] + '...'
        pre = '✓' if store.get('pre_validated') else ' '
        print(f"  {pre} {i+1}. {store['url'][:40]:<40} variant: {variant}")
    
    return len(gateway.stores) > 0

def test_store_cycling():
    """Test that stores cycle properly"""
    print("\n" + "="*60)
    print("CYCLING TEST")
    print("="*60)
    
    gateway = ShopifyAPIGateway()
    
    # Get 10 stores in sequence
    print("\nGetting 10 stores in sequence:")
    stores_seen = []
    for i in range(10):
        store = gateway.get_next_store()
        stores_seen.append(store['url'])
        print(f"  {i+1}. {store['url']}")
    
    # Verify cycling
    print(f"\nUnique stores: {len(set(stores_seen))}")
    
    # Test that cycling wraps around
    print("\nTesting wrap-around (getting more stores than total):")
    gateway2 = ShopifyAPIGateway()
    total = len(gateway2.stores)
    
    # Get more stores than available
    for i in range(total + 5):
        store = gateway2.get_next_store()
    
    print(f"  Successfully cycled through {total + 5} requests with {total} stores")
    
    return True

def test_failed_store_tracking():
    """Test that failed stores are tracked and skipped"""
    print("\n" + "="*60)
    print("FAILED STORE TRACKING TEST")
    print("="*60)
    
    gateway = ShopifyAPIGateway()
    
    # Mark first 3 stores as failed
    for i in range(3):
        gateway.mark_store_failed(gateway.stores[i]['url'])
    
    print(f"\nMarked {len(gateway.failed_stores)} stores as failed")
    
    # Get next store - should skip failed ones
    store = gateway.get_next_store()
    print(f"Next store (should skip failed): {store['url']}")
    
    # Verify it's not in failed list
    is_failed = store['url'] in gateway.failed_stores
    print(f"Store is in failed list: {is_failed}")
    
    # Mark store as success
    gateway.mark_store_success(store['url'])
    print(f"Marked {store['url']} as success")
    
    return not is_failed

def test_price_distribution():
    """Show price distribution of stores"""
    print("\n" + "="*60)
    print("PRICE DISTRIBUTION")
    print("="*60)
    
    gateway = ShopifyAPIGateway()
    
    prices = []
    for store in gateway.stores:
        if store.get('price'):
            try:
                price = float(store['price'])
                prices.append(price)
            except:
                pass
    
    if prices:
        print(f"\nStores with prices: {len(prices)}")
        print(f"Min price: ${min(prices):.2f}")
        print(f"Max price: ${max(prices):.2f}")
        print(f"Avg price: ${sum(prices)/len(prices):.2f}")
        
        # Price buckets
        under_1 = len([p for p in prices if p < 1])
        under_5 = len([p for p in prices if 1 <= p < 5])
        under_10 = len([p for p in prices if 5 <= p < 10])
        under_50 = len([p for p in prices if 10 <= p < 50])
        over_50 = len([p for p in prices if p >= 50])
        
        print(f"\nPrice buckets:")
        print(f"  Under $1:    {under_1}")
        print(f"  $1-$5:       {under_5}")
        print(f"  $5-$10:      {under_10}")
        print(f"  $10-$50:     {under_50}")
        print(f"  Over $50:    {over_50}")
    
    return len(prices) > 0

if __name__ == "__main__":
    results = []
    
    results.append(("Store Loading", test_store_loading()))
    results.append(("Store Cycling", test_store_cycling()))
    results.append(("Failed Store Tracking", test_failed_store_tracking()))
    results.append(("Price Distribution", test_price_distribution()))
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED")
    print("="*60)
