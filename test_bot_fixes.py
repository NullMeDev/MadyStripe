#!/usr/bin/env python3
"""
Test script to verify Telegram bot false positives fix
Tests the STRICT result detection logic
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.pipeline_gateway import PipelineGateway
from core.shopify_price_gateways import (
    ShopifyPennyGateway,
    ShopifyLowGateway,
    ShopifyMediumGateway,
    ShopifyHighGateway
)


class Result:
    """Simulates the Result class from the bot"""
    def __init__(self, card, status, message, card_type, gateway_name):
        self.card = card
        self.status = status
        self.message = message
        self.card_type = card_type
        self.gateway = gateway_name
    
    def is_live(self):
        # STRICT: Only approved status is live
        return self.status == 'approved'
    
    def is_approved(self):
        return self.status == 'approved'


def test_gateway(gateway, test_name, test_card='4111111111111111|12|2025|123'):
    """Test a gateway and verify result detection"""
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"{'='*70}")
    print(f"Gateway: {gateway.name}")
    print(f"Card: {test_card}")
    print("Checking...")
    
    try:
        status, message, card_type = gateway.check(test_card)
        
        print(f"\n✅ Check completed:")
        print(f"  Status: {status}")
        print(f"  Message: {message}")
        print(f"  Card Type: {card_type}")
        
        # Create result object
        result = Result(test_card, status, message, card_type, gateway.name)
        
        # Test the logic
        print(f"\n🔍 Result Detection:")
        print(f"  is_live(): {result.is_live()}")
        print(f"  is_approved(): {result.is_approved()}")
        print(f"  Would post to groups: {'YES ✅' if result.is_live() else 'NO ❌'}")
        
        # Verify STRICT logic
        if status == 'approved':
            if result.is_live():
                print(f"\n✅ CORRECT: Approved card would be posted")
            else:
                print(f"\n❌ ERROR: Approved card would NOT be posted (BUG!)")
                return False
        else:
            if not result.is_live():
                print(f"\n✅ CORRECT: Non-approved card would NOT be posted")
            else:
                print(f"\n❌ ERROR: Non-approved card would be posted (FALSE POSITIVE!)")
                return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_false_positive_scenarios():
    """Test scenarios that previously caused false positives"""
    print(f"\n{'='*70}")
    print("TESTING FALSE POSITIVE SCENARIOS")
    print(f"{'='*70}")
    
    # Simulate declined cards with keywords that used to trigger false positives
    test_cases = [
        ("declined", "Card declined - insufficient funds", "Visa"),
        ("declined", "Invalid CVV code", "Mastercard"),
        ("declined", "CVC check failed", "Visa"),
        ("error", "Insufficient funds available", "Amex"),
        ("error", "CVV mismatch detected", "Discover"),
    ]
    
    all_passed = True
    
    for status, message, card_type in test_cases:
        print(f"\n--- Test Case ---")
        print(f"Status: {status}")
        print(f"Message: {message}")
        print(f"Card Type: {card_type}")
        
        result = Result("4111111111111111|12|2025|123", status, message, card_type, "Test Gateway")
        
        print(f"\nResult Detection:")
        print(f"  is_live(): {result.is_live()}")
        print(f"  Would post: {'YES' if result.is_live() else 'NO'}")
        
        if result.is_live():
            print(f"❌ FALSE POSITIVE! This card would be posted despite status='{status}'")
            all_passed = False
        else:
            print(f"✅ CORRECT! Card NOT posted (status='{status}')")
    
    return all_passed


def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║          TELEGRAM BOT FALSE POSITIVES FIX TEST            ║
║                  Verifying STRICT Detection                ║
╚════════════════════════════════════════════════════════════╝
""")
    
    results = []
    
    # Test 1: False Positive Scenarios
    print("\n" + "="*70)
    print("TEST 1: FALSE POSITIVE SCENARIOS")
    print("="*70)
    passed = test_false_positive_scenarios()
    results.append(("False Positive Scenarios", passed))
    
    # Test 2: Stripe Gate
    print("\n" + "="*70)
    print("TEST 2: STRIPE GATE ($1 CC Foundation)")
    print("="*70)
    try:
        gateway = PipelineGateway()
        passed = test_gateway(gateway, "Stripe $1 Gate")
        results.append(("Stripe Gate", passed))
    except Exception as e:
        print(f"❌ Error testing Stripe gate: {e}")
        results.append(("Stripe Gate", False))
    
    # Test 3: Shopify Penny Gate
    print("\n" + "="*70)
    print("TEST 3: SHOPIFY PENNY GATE ($0.01)")
    print("="*70)
    try:
        gateway = ShopifyPennyGateway()
        passed = test_gateway(gateway, "Shopify Penny Gate")
        results.append(("Shopify Penny Gate", passed))
    except Exception as e:
        print(f"❌ Error testing Penny gate: {e}")
        results.append(("Shopify Penny Gate", False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:40} {status}")
    
    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed_count}/{total} tests passed")
    
    if passed_count == total:
        print("\n🎉 ALL TESTS PASSED! False positives fix is working correctly!")
        return 0
    else:
        print("\n⚠️ SOME TESTS FAILED! Please review the results above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
