"""
Test Shopify Hybrid Gateway V2
"""

import sys
sys.path.insert(0, '.')

from core.shopify_hybrid_gateway_v2 import ShopifyHybridGatewayV2

print("="*70)
print("SHOPIFY HYBRID GATEWAY V2 - TEST")
print("="*70)
print("\nImprovements:")
print("  ✓ Properly navigates to payment page")
print("  ✓ Waits for payment form to load")
print("  ✓ Better card field detection")
print("  ✓ More debugging output\n")

gateway = ShopifyHybridGatewayV2(headless=False)  # Non-headless to see what happens

test_card = "4111111111111111|12|25|123"
print(f"Testing card: {test_card[:4]}...{test_card[-7:]}\n")

status, message, card_type = gateway.check(test_card, max_attempts=1)

print(f"\n{'='*70}")
print(f"RESULT:")
print(f"  Status: {status}")
print(f"  Message: {message}")
print(f"  Card Type: {card_type}")
print(f"{'='*70}")
