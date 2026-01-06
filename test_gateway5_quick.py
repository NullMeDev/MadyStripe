#!/usr/bin/env python3
"""
Quick test for Gateway 5 with fresh nonce
"""

import sys
import time
sys.path.insert(0, '100$/100$/')

from Charge5 import StaleksFloridaCheckoutVNew

# Test cards
test_cards = [
    "5566258985615466|12|25|299",  # Card 1
    "4304450802433666|12|25|956",  # Card 2
    "5587170478868301|12|25|286",  # Card 3
]

print("="*60)
print("GATEWAY 5 QUICK TEST - WITH FRESH NONCE")
print("="*60)
print("\nFresh parameters applied:")
print("- Nonce: 3c9233e7eb")
print("- Form ID: 6955db3333cec")
print("- Campaign: 988003")
print("-"*60)

for i, card in enumerate(test_cards, 1):
    print(f"\nTest {i}: {card[:4]}****")
    start = time.time()
    result = StaleksFloridaCheckoutVNew(card)
    elapsed = time.time() - start
    
    # Check result type
    if "Charged" in str(result):
        print(f"✅ SUCCESS: {result} - {elapsed:.1f}s")
    elif "declined" in str(result).lower():
        print(f"❌ DECLINED: {result} - {elapsed:.1f}s")
    else:
        print(f"⚠️  ERROR: {result} - {elapsed:.1f}s")
    
    # Small delay between tests
    if i < len(test_cards):
        time.sleep(2)

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
