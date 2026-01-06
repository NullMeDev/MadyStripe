#!/usr/bin/env python3
"""
Test VPS Checker Integration with Fixed Shopify Gates
Verify no false positives are posted to Telegram
"""

import sys
from core.shopify_price_gateways import ShopifyLowGateway

print("="*70)
print("VPS CHECKER INTEGRATION TEST")
print("="*70)

# Test cards
test_cards = [
    ("4283322091041036|12|25|123", "Test Card 1"),
    ("377481330446334|12|25|221", "Test Card 2"),
]

gateway = ShopifyLowGateway()
print(f"\nGateway: {gateway.name}")
print(f"Store: {gateway.store_url}")
print(f"Charge Amount: {gateway.charge_amount}\n")

print("="*70)
print("TESTING VPS CHECKER LOGIC")
print("="*70)

for card, label in test_cards:
    print(f"\n{label}: {card[:4]}...{card[-3:]}")
    print("-" * 70)
    
    # Check card
    status, message, card_type = gateway.check(card)
    
    print(f"Status: {status}")
    print(f"Message: {message}")
    print(f"Card Type: {card_type}")
    
    # Simulate VPS Checker logic (from mady_vps_checker.py line 169)
    would_post = (status == "approved")
    
    print(f"\nVPS Checker Logic:")
    print(f"  if status == 'approved': {status == 'approved'}")
    print(f"  Would post to Telegram: {'YES ✅' if would_post else 'NO ❌'}")
    
    # Check for false positive
    if would_post:
        msg_lower = message.lower()
        if any(word in msg_lower for word in ["insufficient", "cvv", "cvc", "declined", "invalid"]):
            print(f"  ⚠️  WARNING: Would post declined card as approved!")
            print(f"  ❌ FALSE POSITIVE DETECTED!")
        else:
            print(f"  ✅ Correctly would post approved card")
    else:
        print(f"  ✅ Correctly would NOT post declined card")

print("\n" + "="*70)
print("EXPECTED BEHAVIOR:")
print("="*70)
print("✅ Only cards with status='approved' should be posted")
print("✅ Declined cards (insufficient funds, invalid CVV) should NOT be posted")
print("✅ Message should be clean without misleading symbols")
print("\n" + "="*70)
