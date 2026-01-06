"""
Test Shopify gateway WITHOUT proxy to isolate proxy issues
"""

from core.shopify_simple_gateway import SimpleShopifyGateway

print("="*80)
print("SHOPIFY GATEWAY TEST - NO PROXY")
print("="*80)

# Initialize WITHOUT proxy
print("\n[1/3] Initializing gateway (NO PROXY)...")
gateway = SimpleShopifyGateway(proxy=None)

print(f"✅ Gateway initialized with {len(gateway.stores)} stores")

# Test with one card
test_card = "4111111111111111|12|25|123"

print(f"\n[2/3] Testing card: {test_card[:4]}...{test_card[-7:]}")
print("-" * 80)

status, message, card_type = gateway.check(test_card, max_attempts=3)

print(f"\n[3/3] RESULT:")
print(f"  Status: {status}")
print(f"  Message: {message}")
print(f"  Card Type: {card_type}")

# Stats
stats = gateway.get_stats()
print(f"\nGateway Stats:")
for key, value in stats.items():
    print(f"  {key}: {value}")

print(f"\n{'='*80}")
if status in ['approved', 'declined']:
    print("✅ TEST PASSED - Card was processed")
else:
    print("❌ TEST FAILED - All stores failed")
print(f"{'='*80}")
