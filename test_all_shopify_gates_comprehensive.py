#!/usr/bin/env python3
"""
Comprehensive Test for All 4 Shopify Price Gates
Tests Penny, Low, Medium, and High gates
"""

from core.shopify_price_gateways import (
    ShopifyPennyGateway,
    ShopifyLowGateway,
    ShopifyMediumGateway,
    ShopifyHighGateway
)

print("="*70)
print("COMPREHENSIVE SHOPIFY GATES TEST")
print("="*70)

# Test cards
test_cards = [
    "4283322091041036|12|25|123",
    "377481330446334|12|25|221",
]

gates = [
    (ShopifyPennyGateway(), "Penny Gate ($0.01)"),
    (ShopifyLowGateway(), "Low Gate ($5)"),
    (ShopifyMediumGateway(), "Medium Gate ($20)"),
    (ShopifyHighGateway(), "High Gate ($100)"),
]

results = {
    "total_tests": 0,
    "approved": 0,
    "declined": 0,
    "errors": 0,
    "false_positives": 0
}

for gateway, gate_name in gates:
    print(f"\n{'='*70}")
    print(f"🧪 Testing {gate_name}")
    print(f"{'='*70}")
    print(f"Gateway: {gateway.name}")
    print(f"Store: {gateway.store_url}")
    print(f"Charge Amount: {gateway.charge_amount}\n")
    
    for i, card in enumerate(test_cards, 1):
        print(f"Test {i}: {card[:4]}...{card[-3:]}")
        results["total_tests"] += 1
        
        try:
            status, message, card_type = gateway.check(card)
            
            print(f"  Status: {status}")
            print(f"  Message: {message}")
            print(f"  Card Type: {card_type}")
            
            # Check for false positives
            if status == "approved":
                results["approved"] += 1
                # Check if message contains decline keywords
                msg_lower = message.lower()
                if any(word in msg_lower for word in ["insufficient", "cvv", "cvc", "declined", "invalid"]):
                    print(f"  ❌ FALSE POSITIVE DETECTED!")
                    results["false_positives"] += 1
                else:
                    print(f"  ✅ Truly approved")
            elif status == "declined":
                results["declined"] += 1
                print(f"  ✅ Correctly declined")
            else:
                results["errors"] += 1
                print(f"  ⚠️  Error status")
            
        except Exception as e:
            results["errors"] += 1
            print(f"  ❌ Exception: {str(e)[:100]}")
        
        print()

# Summary
print("\n" + "="*70)
print("📊 TEST SUMMARY")
print("="*70)
print(f"Total Tests: {results['total_tests']}")
print(f"Approved: {results['approved']}")
print(f"Declined: {results['declined']}")
print(f"Errors: {results['errors']}")
print(f"False Positives: {results['false_positives']}")

if results['false_positives'] == 0:
    print("\n✅ SUCCESS: No false positives detected!")
else:
    print(f"\n❌ FAILURE: {results['false_positives']} false positive(s) detected!")

print("\n" + "="*70)
print("EXPECTED BEHAVIOR:")
print("="*70)
print("✅ All gates should work without false positives")
print("✅ Declined cards should show status='declined'")
print("✅ Approved cards should show status='approved'")
print("✅ Messages should be clean and accurate")
