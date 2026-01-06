#!/usr/bin/env python3
"""
End-to-End Test for All Shopify Gates
Tests each gate with a real card to verify complete functionality
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.shopify_price_gateways import (
    ShopifyPennyGateway,
    ShopifyLowGateway,
    ShopifyMediumGateway,
    ShopifyHighGateway
)

def test_gateway(gateway, name, card):
    """Test a gateway with a real card"""
    print(f"\n{'='*70}")
    print(f"Testing {name}")
    print(f"{'='*70}")
    print(f"Store: {gateway.store_url}")
    print(f"Charge Amount: {gateway.charge_amount}")
    print(f"Card: {card[:4]}...{card[-4:]}")
    
    print(f"\n🔄 Processing card...")
    start_time = time.time()
    
    try:
        status, message, card_type = gateway.check(card)
        elapsed = time.time() - start_time
        
        print(f"\n📊 Results:")
        print(f"  Status: {status}")
        print(f"  Message: {message}")
        print(f"  Card Type: {card_type}")
        print(f"  Time: {elapsed:.2f}s")
        
        if status == "approved":
            print(f"  ✅ SUCCESS - Card approved!")
            return True
        elif status == "declined":
            print(f"  ❌ DECLINED - Card declined")
            return True  # Still counts as working gate
        else:
            print(f"  ⚠️ ERROR - {message}")
            return False
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ EXCEPTION: {str(e)}")
        print(f"  Time: {elapsed:.2f}s")
        return False

def main():
    print("="*70)
    print("END-TO-END TEST - ALL SHOPIFY GATES")
    print("="*70)
    
    # Test card
    card = "4118104014949771|02|34|001"
    print(f"\nTest Card: {card[:4]}...{card[-4:]}")
    
    results = {}
    
    # Test each gateway
    print(f"\n{'='*70}")
    print("TESTING ALL 4 GATES")
    print(f"{'='*70}")
    
    # 1. Penny Gate
    penny = ShopifyPennyGateway()
    results['Penny'] = test_gateway(penny, "💰 Penny Gate ($1-$2)", card)
    time.sleep(2)  # Brief delay between tests
    
    # 2. Low Gate
    low = ShopifyLowGateway()
    results['Low'] = test_gateway(low, "💵 Low Gate ($4-$10)", card)
    time.sleep(2)
    
    # 3. Medium Gate
    medium = ShopifyMediumGateway()
    results['Medium'] = test_gateway(medium, "💳 Medium Gate ($12-$18)", card)
    time.sleep(2)
    
    # 4. High Gate
    high = ShopifyHighGateway()
    results['High'] = test_gateway(high, "💎 High Gate ($45+)", card)
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 TEST SUMMARY")
    print(f"{'='*70}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for gate, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {gate} Gate: {status}")
    
    print(f"\n  Total: {passed}/{total} gates working")
    
    if passed == total:
        print(f"\n{'='*70}")
        print("🎉 ALL GATES WORKING!")
        print(f"{'='*70}")
        print("\nAll Shopify gates are operational and ready for production use.")
    else:
        print(f"\n{'='*70}")
        print("⚠️ SOME GATES FAILED")
        print(f"{'='*70}")
        print(f"\n{total - passed} gate(s) need attention.")

if __name__ == '__main__':
    main()
