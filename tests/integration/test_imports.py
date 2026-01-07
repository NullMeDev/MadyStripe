"""Quick test to check if all modules import correctly"""

print("Testing imports...")
print("="*70)

try:
    print("\n1. Testing store database...")
    from core.shopify_store_database import ShopifyStoreDatabase
    print("   ✅ Store database imports successfully")
except Exception as e:
    print(f"   ❌ Store database error: {e}")

try:
    print("\n2. Testing product finder...")
    from core.shopify_product_finder import DynamicProductFinder
    print("   ✅ Product finder imports successfully")
except Exception as e:
    print(f"   ❌ Product finder error: {e}")

try:
    print("\n3. Testing payment processor...")
    from core.shopify_payment_processor import ShopifyPaymentProcessor
    print("   ✅ Payment processor imports successfully")
except Exception as e:
    print(f"   ❌ Payment processor error: {e}")

try:
    print("\n4. Testing smart gateway...")
    from core.shopify_smart_gateway import ShopifyPennyGate
    print("   ✅ Smart gateway imports successfully")
except Exception as e:
    print(f"   ❌ Smart gateway error: {e}")

try:
    print("\n5. Testing dynamic price gateways...")
    from core.shopify_price_gateways_dynamic import DynamicShopifyPennyGateway
    print("   ✅ Dynamic price gateways import successfully")
except Exception as e:
    print(f"   ❌ Dynamic price gateways error: {e}")

print("\n" + "="*70)
print("Import test complete!")
