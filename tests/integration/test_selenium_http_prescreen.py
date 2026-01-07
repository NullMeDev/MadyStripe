#!/usr/bin/env python3
"""
Test HTTP Pre-screening functionality
This tests the fast filtering without needing Chrome
"""

import sys
import time
from core.shopify_selenium_gateway import ShopifySeleniumGateway

def test_http_prescreen():
    """Test HTTP pre-screening with sample stores"""
    
    print("="*70)
    print("TESTING HTTP PRE-SCREENING")
    print("="*70)
    print("\nThis tests the fast filtering (Phase 1) without Chrome")
    print("Expected: ~3 seconds per store\n")
    
    # Initialize gateway
    gateway = ShopifySeleniumGateway(
        stores_file='working_shopify_stores.txt',
        headless=True
    )
    
    # Get first 10 stores
    test_stores = gateway.stores[:10] if len(gateway.stores) >= 10 else gateway.stores
    
    print(f"Testing {len(test_stores)} stores from working_shopify_stores.txt\n")
    
    # Test each store
    accessible_count = 0
    start_time = time.time()
    
    for i, store in enumerate(test_stores, 1):
        print(f"[{i}/{len(test_stores)}] Testing: {store}")
        
        store_start = time.time()
        # Use the batch method with single store
        accessible_stores = gateway.http_prescreen_stores([store])
        is_accessible = store in accessible_stores
        store_time = time.time() - store_start
        
        if is_accessible:
            print(f"  ✅ ACCESSIBLE ({store_time:.2f}s)")
            accessible_count += 1
        else:
            print(f"  ❌ NOT ACCESSIBLE ({store_time:.2f}s)")
    
    total_time = time.time() - start_time
    avg_time = total_time / len(test_stores)
    
    print(f"\n{'='*70}")
    print("RESULTS:")
    print(f"{'='*70}")
    print(f"Total stores tested: {len(test_stores)}")
    print(f"Accessible stores: {accessible_count} ({accessible_count/len(test_stores)*100:.1f}%)")
    print(f"Inaccessible stores: {len(test_stores) - accessible_count}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time per store: {avg_time:.2f}s")
    print(f"{'='*70}")
    
    # Performance check
    if avg_time <= 5:
        print("\n✅ PERFORMANCE: Excellent! (≤5s per store)")
    elif avg_time <= 10:
        print("\n⚠️  PERFORMANCE: Good (5-10s per store)")
    else:
        print("\n❌ PERFORMANCE: Slow (>10s per store)")
    
    # Accessibility check
    if accessible_count >= len(test_stores) * 0.5:
        print(f"✅ ACCESSIBILITY: Good! ({accessible_count}/{len(test_stores)} stores accessible)")
    else:
        print(f"⚠️  ACCESSIBILITY: Low ({accessible_count}/{len(test_stores)} stores accessible)")
    
    print("\n" + "="*70)
    print("HTTP PRE-SCREENING TEST COMPLETE")
    print("="*70)
    
    return accessible_count > 0


if __name__ == "__main__":
    try:
        success = test_http_prescreen()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
