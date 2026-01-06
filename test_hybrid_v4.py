#!/usr/bin/env python3
"""
Test Shopify Hybrid Gateway V4 - Fixed Single-Page Checkout
"""

import sys
sys.path.insert(0, '.')

from core.shopify_hybrid_gateway_v4 import ShopifyHybridGatewayV4

def main():
    print("\n" + "="*70)
    print("SHOPIFY HYBRID GATEWAY V4 TEST - SINGLE-PAGE CHECKOUT FIX")
    print("="*70)
    
    # Initialize gateway
    print("\n→ Initializing gateway with proxy support...")
    gateway = ShopifyHybridGatewayV4(
        proxy_file='webshare_proxies_auth.txt',
        headless=False  # Show browser for debugging
    )
    
    # Test card
    test_card = "4111111111111111|12|2025|123"
    
    print(f"\n→ Testing card: {test_card}")
    print("→ Target amount: $1.00")
    print("\n" + "-"*70)
    
    # Run check
    status, message, card_type = gateway.check(test_card, amount=1.0)
    
    # Display results
    print("\n" + "="*70)
    print("FINAL RESULT:")
    print("="*70)
    print(f"  Status: {status}")
    print(f"  Message: {message}")
    print(f"  Card Type: {card_type}")
    print("="*70)
    
    # Status emoji
    if status == "approved":
        print("\n✅ APPROVED - Card charged successfully!")
    elif status == "declined":
        print("\n❌ DECLINED - Card was declined")
    elif status == "unknown":
        print("\n⚠️  UNKNOWN - Payment submitted but response unclear")
    else:
        print("\n❌ ERROR - Check failed")
    
    print("\n" + "="*70)
    print("DEBUG FILES:")
    print("="*70)
    print("  /tmp/shopify_payment_page.html - Payment page HTML")
    print("  /tmp/shopify_payment_response.html - Payment response HTML")
    print("="*70)

if __name__ == "__main__":
    main()
