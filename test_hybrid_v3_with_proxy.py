"""
Test Shopify Hybrid Gateway V3 with Proxy Support
"""

import sys
import time
from core.shopify_hybrid_gateway_v3 import ShopifyHybridGatewayV3

def test_v3_gateway():
    """Test V3 gateway with proxy rotation"""
    
    print("\n" + "="*70)
    print("SHOPIFY HYBRID GATEWAY V3 - PROXY TEST")
    print("="*70)
    
    # Initialize gateway with proxy support
    print("\n→ Initializing gateway with Webshare residential proxies...")
    gateway = ShopifyHybridGatewayV3(
        proxy_file='webshare_proxies_auth.txt',
        headless=False  # Set to True for production
    )
    
    # Test card
    test_card = "4111111111111111|12|25|123"
    
    print(f"\n→ Testing card: {test_card}")
    print(f"→ Target amount: $1.00")
    print(f"→ Max store attempts: 3")
    
    # Run test
    start_time = time.time()
    
    try:
        status, message, card_type = gateway.check(
            card_data=test_card,
            amount=1.0,
            max_store_attempts=3
        )
        
        elapsed = time.time() - start_time
        
        print("\n" + "="*70)
        print("RESULT:")
        print("="*70)
        print(f"  Status: {status}")
        print(f"  Message: {message}")
        print(f"  Card Type: {card_type}")
        print(f"  Time: {elapsed:.2f}s")
        print("="*70)
        
        return status == "approved"
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_v3_gateway()
    sys.exit(0 if success else 1)
