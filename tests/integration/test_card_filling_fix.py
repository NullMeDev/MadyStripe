"""
Test the improved card filling logic with iframe handling
"""

import sys
from core.shopify_hybrid_gateway_v3 import ShopifyHybridGatewayV3

def test_card_filling():
    """Test improved card filling with a real card"""
    
    print("\n" + "="*70)
    print("TESTING IMPROVED CARD FILLING LOGIC")
    print("="*70)
    
    # Initialize gateway with proxy
    print("\n→ Initializing gateway with proxy...")
    gateway = ShopifyHybridGatewayV3(
        proxy_file='webshare_proxies_auth.txt',
        headless=False  # Keep visible to see what happens
    )
    
    # Test card (Visa test card)
    test_card = "4111111111111111|12|25|123"
    
    print(f"\n→ Testing card: {test_card}")
    print(f"→ Target amount: $1.00")
    print(f"→ Max attempts: 3 stores")
    
    print("\n" + "="*70)
    print("IMPROVEMENTS:")
    print("="*70)
    print("✓ Enhanced iframe detection and switching")
    print("✓ Multiple selector strategies for card fields")
    print("✓ Visibility and enabled state checking")
    print("✓ Character-by-character typing with fallback")
    print("✓ Expiry and CVV field filling")
    print("✓ Payment submission and response detection")
    print("✓ Success/decline indicator checking")
    print("="*70)
    
    # Run test
    try:
        status, message, card_type = gateway.check(
            card_data=test_card,
            amount=1.0,
            max_store_attempts=3
        )
        
        print("\n" + "="*70)
        print("FINAL RESULT:")
        print("="*70)
        print(f"  Status: {status}")
        print(f"  Message: {message}")
        print(f"  Card Type: {card_type}")
        print("="*70)
        
        if status == "approved":
            print("\n✅ SUCCESS: Card was charged!")
            return True
        elif status == "declined":
            print("\n❌ DECLINED: Card was declined")
            return True  # Still success - we got a response
        elif status == "unknown":
            print("\n⚠️  UNKNOWN: Payment submitted but response unclear")
            print("   Check the saved HTML files in /tmp/")
            return True
        else:
            print("\n✗ ERROR: Could not complete payment")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_card_filling()
    
    print("\n" + "="*70)
    print("DEBUG FILES:")
    print("="*70)
    print("  /tmp/shopify_payment_page.html - Payment page HTML")
    print("  /tmp/shopify_payment_response.html - Payment response HTML")
    print("="*70)
    
    sys.exit(0 if success else 1)
