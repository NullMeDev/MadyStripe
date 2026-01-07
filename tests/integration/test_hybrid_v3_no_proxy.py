"""
Test Shopify Hybrid Gateway V3 WITHOUT proxy
To isolate proxy-related issues
"""

import sys
import time
from core.shopify_hybrid_gateway_v3 import ShopifyHybridGatewayV3

def main():
    print("=" * 70)
    print("SHOPIFY HYBRID GATEWAY V3 - NO PROXY TEST")
    print("=" * 70)
    
    # Initialize gateway WITHOUT proxy
    print("\n→ Initializing gateway (no proxy)...")
    gateway = ShopifyHybridGatewayV3(proxy_file='nonexistent.txt', headless=True)
    
    # Test card
    test_card = "4111111111111111|12|25|123"
    
    print(f"\n→ Testing card: {test_card}")
    print(f"→ Target amount: $1.00")
    print(f"→ Max store attempts: 3")
    
    start_time = time.time()
    
    # Run test
    status, message, card_type = gateway.check(
        test_card,
        amount=1.0,
        max_store_attempts=3
    )
    
    elapsed = time.time() - start_time
    
    # Print results
    print("\n" + "=" * 70)
    print("RESULT:")
    print("=" * 70)
    print(f"  Status: {status}")
    print(f"  Message: {message}")
    print(f"  Card Type: {card_type}")
    print(f"  Time: {elapsed:.2f}s")
    print("=" * 70)

if __name__ == "__main__":
    main()
