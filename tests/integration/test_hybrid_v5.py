#!/usr/bin/env python3
"""
Test Shopify Hybrid Gateway V5 - Enhanced Stealth
Tests the improved browser detection bypass
"""

import sys
from core.shopify_hybrid_gateway_v5 import ShopifyHybridGatewayV5

def test_v5_gateway():
    """Test V5 gateway with enhanced stealth"""
    
    print("=" * 70)
    print("SHOPIFY HYBRID GATEWAY V5 TEST - ENHANCED STEALTH")
    print("=" * 70)
    print()
    
    # Initialize gateway (headless=False for better stealth)
    print("→ Initializing gateway with enhanced stealth...")
    gateway = ShopifyHybridGatewayV5(
        proxy_file='webshare_proxies_auth.txt',
        headless=False  # Non-headless for better stealth
    )
    
    # Test card
    test_card = "4111111111111111|12|2025|123"
    target_amount = 1.0
    
    print(f"→ Testing card: {test_card}")
    print(f"→ Target amount: ${target_amount}")
    print()
    print("-" * 70)
    print()
    
    # Run check
    status, message, card_type = gateway.check(test_card, target_amount)
    
    # Display result
    print()
    print("=" * 70)
    print("FINAL RESULT:")
    print("=" * 70)
    print(f"  Status: {status}")
    print(f"  Message: {message}")
    print(f"  Card Type: {card_type}")
    print("=" * 70)
    print()
    
    # Status indicator
    if status == "approved":
        print("✅ APPROVED - Card successfully charged!")
    elif status == "declined":
        print("❌ DECLINED - Card was declined")
    elif status == "unknown":
        print("⚠️  UNKNOWN - Payment submitted but response unclear")
    else:
        print("❌ ERROR - Check failed")
    
    print()
    print("=" * 70)
    print("DEBUG FILES:")
    print("=" * 70)
    print("  /tmp/shopify_v5_response.html - Response HTML (if unknown)")
    print("=" * 70)
    print()
    
    return status

if __name__ == "__main__":
    try:
        result = test_v5_gateway()
        sys.exit(0 if result in ["approved", "declined"] else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
