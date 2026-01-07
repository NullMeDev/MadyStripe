"""Test the hybrid Shopify gateway"""

import sys
sys.path.insert(0, '.')

from core.shopify_hybrid_gateway import ShopifyHybridGateway

print("="*70)
print("SHOPIFY HYBRID GATEWAY TEST")
print("="*70)
print("\nThis uses:")
print("  1. Store database for store selection")
print("  2. Product finder for product IDs")
print("  3. Selenium ONLY for checkout/payment")
print("\nThis is faster and more reliable than full Selenium!\n")

gateway = ShopifyHybridGateway(headless=True)

# Test card
test_card = "4111111111111111|12|25|123"

print(f"Testing card: {test_card[:4]}...{test_card[-7:]}\n")

status, message, card_type = gateway.check(test_card, max_attempts=2)

print(f"\n{'='*70}")
print(f"RESULT:")
print(f"  Status: {status}")
print(f"  Message: {message}")
print(f"  Card Type: {card_type}")
print(f"{'='*70}")

stats = gateway.get_stats()
print(f"\nStatistics:")
for key, value in stats.items():
    print(f"  {key}: {value}")
