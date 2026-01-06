"""
Test Shopify Hybrid Gateway V3 with 1000 Proxies
Tests scalability with larger proxy pool
"""

import sys
import time
from core.shopify_hybrid_gateway_v3 import ShopifyHybridGatewayV3

def test_1000_proxies():
    """Test V3 gateway with 1000 proxies"""
    
    print("\n" + "="*70)
    print("SHOPIFY HYBRID GATEWAY V3 - 1000 PROXY SCALE TEST")
    print("="*70)
    
    # Initialize gateway with 1000 proxies
    print("\n→ Loading 1000 proxies...")
    load_start = time.time()
    
    try:
        gateway = ShopifyHybridGatewayV3(
            proxy_file='webshare_proxies_1000.txt',
            headless=False  # Set to True for production
        )
        
        load_time = time.time() - load_start
        
        print(f"✅ Loaded proxies in {load_time:.2f}s")
        
    except Exception as e:
        print(f"✗ Failed to load proxies: {e}")
        return False
    
    # Test card
    test_card = "4111111111111111|12|25|123"
    
    print(f"\n→ Testing card: {test_card}")
    print(f"→ Target amount: $1.00")
    print(f"→ Max store attempts: 5")
    print(f"→ This will test 5 different proxies from the 1000-proxy pool")
    
    # Run test
    start_time = time.time()
    
    try:
        status, message, card_type = gateway.check(
            card_data=test_card,
            amount=1.0,
            max_store_attempts=5  # Test 5 proxies
        )
        
        elapsed = time.time() - start_time
        
        print("\n" + "="*70)
        print("RESULT:")
        print("="*70)
        print(f"  Status: {status}")
        print(f"  Message: {message}")
        print(f"  Card Type: {card_type}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Proxy Load Time: {load_time:.2f}s")
        print("="*70)
        
        # Success if we loaded proxies and ran test
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_1000_proxies()
    sys.exit(0 if success else 1)
