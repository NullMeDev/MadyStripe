"""
Test with wiredministries.com ONLY - the known working store
"""

from core.shopify_simple_gateway import SimpleShopifyGateway

print("="*80)
print("WIREDMINISTRIES.COM TEST - KNOWN WORKING STORE")
print("="*80)

# Create temporary store file with ONLY wiredministries
with open('test_wired_only.txt', 'w') as f:
    f.write('wiredministries.com\n')

# Initialize with ONLY this store
print("\n[1/3] Initializing gateway with wiredministries.com ONLY...")
gateway = SimpleShopifyGateway(stores_file='test_wired_only.txt', proxy=None)

print(f"✅ Gateway initialized with {len(gateway.stores)} store(s)")

# Test card
test_card = "4111111111111111|12|25|123"

print(f"\n[2/3] Testing card: {test_card[:4]}...{test_card[-7:]}")
print("-" * 80)

status, message, card_type = gateway.check(test_card, max_attempts=1)

print(f"\n[3/3] RESULT:")
print(f"  Status: {status}")
print(f"  Message: {message}")
print(f"  Card Type: {card_type}")

print(f"\n{'='*80}")
if status in ['approved', 'declined']:
    print("✅ TEST PASSED - Card was processed!")
    print("This proves the implementation works with the right store.")
else:
    print("❌ TEST FAILED - Even wiredministries failed")
    print("This means there's an issue with the checkout process itself.")
print(f"{'='*80}")

# Cleanup
import os
os.remove('test_wired_only.txt')
