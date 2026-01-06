#!/usr/bin/env python3
"""
Test Shopify Gateway False Positive Fix
Verify that insufficient funds and CVV errors are properly declined
"""

from core.shopify_price_gateways import ShopifyLowGateway, ShopifyPennyGateway

print("="*70)
print("SHOPIFY FALSE POSITIVE FIX TEST")
print("="*70)

# Test cards that should be DECLINED
test_cards = [
    ("4283322091041036|12|25|123", "Test Card 1"),
    ("377481330446334|12|25|221", "Test Card 2"),
    ("5224407000339669|12|25|221", "Test Card 3"),
]

print("\n🧪 Testing Shopify Low Gate ($5)")
print("-" * 70)

gateway = ShopifyLowGateway()
print(f"Gateway: {gateway.name}")
print(f"Store: {gateway.store_url}\n")

for card, label in test_cards:
    print(f"Testing {label}: {card[:4]}...{card[-3:]}")
    status, message, card_type = gateway.check(card)
    
    print(f"  Status: {status}")
    print(f"  Message: {message}")
    print(f"  Card Type: {card_type}")
    
    # Check for false positives
    if status == "approved":
        if "insufficient" in message.lower() or "cvv" in message.lower() or "cvc" in message.lower():
            print(f"  ❌ FALSE POSITIVE DETECTED!")
        else:
            print(f"  ✅ Truly approved")
    else:
        print(f"  ✅ Correctly declined")
    
    print()

print("\n" + "="*70)
print("EXPECTED BEHAVIOR:")
print("="*70)
print("✅ Status should be 'declined' for insufficient funds")
print("✅ Status should be 'declined' for invalid CVV")
print("✅ Status should be 'approved' ONLY for successful charges")
print("✅ Messages should be clean (no 'CHARGED ✅' for declined cards)")
print("\n" + "="*70)
