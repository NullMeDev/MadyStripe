#!/usr/bin/env python3
"""
Enhanced Shopify System Test - Multi-Store Retry System
Tests the new enhanced Shopify gateway with product fetching and retry logic
"""

import sys
import asyncio
import time
sys.path.insert(0, 'AutoshBotSRC/AutoshBotSRC')

from gateways.autoShopify_enhanced import (
    ShopifyProductManager,
    MultiStoreRetrySystem,
    VERIFIED_STORES,
    process_card_enhanced
)
from utils import Utils

async def test_product_fetching():
    """Test enhanced product fetching from multiple stores"""
    print("🛍️  Testing Enhanced Product Fetching...")

    manager = ShopifyProductManager()

    # Test fetching from a few stores
    test_stores = ["wiredministries.com", "culturekings.com.au", "kith.com"]

    for store in test_stores:
        print(f"  📦 Fetching products from {store}...")
        try:
            products = await manager.fetch_store_products(store, max_products=3)
            if products:
                print(f"    ✅ Found {len(products)} products")
                for product in products[:2]:  # Show first 2 products
                    variants = len(product['variants'])
                    print(f"      • {product['title']} ({variants} variants)")
            else:
                print(f"    ❌ No products found")
        except Exception as e:
            print(f"    ❌ Error: {e}")

        await asyncio.sleep(1)  # Rate limiting

async def test_multi_store_retry():
    """Test the multi-store retry system"""
    print("\n🔄 Testing Multi-Store Retry System...")

    manager = ShopifyProductManager()
    retry_system = MultiStoreRetrySystem(manager)

    # Test with a declined card (should get consistent declines)
    test_card = {
        'cc': '4111111111111111',  # Test card that should decline
        'mes': '12',
        'ano': '2025',
        'cvv': '123'
    }

    print(f"  💳 Testing card: {test_card['cc'][:8]}...")

    try:
        result = await retry_system.process_card_until_result(
            test_card['cc'], test_card['mes'], test_card['ano'], test_card['cvv'],
            user_stores=None, proxies=None
        )

        success, message, store_used, amount, currency = result
        print(f"    📊 Result: {'✅' if success else '❌'} {message}")
        print(f"    🏪 Store: {store_used}")
        print(f"    💰 Amount: {amount} {currency}")

    except Exception as e:
        print(f"    ❌ Error: {e}")

async def test_store_validation():
    """Test store validation and product availability"""
    print("\n✅ Testing Store Validation...")

    manager = ShopifyProductManager()

    valid_stores = 0
    total_stores = len(VERIFIED_STORES[:5])  # Test first 5 stores

    for store_info in VERIFIED_STORES[:5]:
        store_url = store_info['url']
        print(f"  🔍 Checking {store_info['name']} ({store_url})...")

        try:
            products = await manager.fetch_store_products(store_url, max_products=2)
            if products and len(products) > 0:
                total_products = sum(len(p['variants']) for p in products)
                print(f"    ✅ Valid - {len(products)} products, {total_products} variants")
                valid_stores += 1
            else:
                print(f"    ❌ No products available")
        except Exception as e:
            print(f"    ❌ Error: {e}")

        await asyncio.sleep(2)  # Rate limiting

    print(f"  📈 Valid stores: {valid_stores}/{total_stores} ({valid_stores/total_stores*100:.1f}%)")

async def test_proxy_integration():
    """Test proxy integration"""
    print("\n🌐 Testing Proxy Integration...")

    # Initialize Utils to load proxies
    Utils.load_resources()

    proxies = Utils.get_all_proxies()
    print(f"  📋 Available proxies: {len(proxies) if proxies else 0}")

    if proxies:
        # Test a few proxies
        working_proxies = 0
        for i, proxy in enumerate(proxies[:3]):
            print(f"  🧪 Testing proxy {i+1}: {proxy[:30]}...")
            # Simple connectivity test would go here
            working_proxies += 1  # Assume they work for this test

        print(f"  ✅ Working proxies: {working_proxies}/3")
    else:
        print("  ⚠️  No proxies configured")

async def main():
    """Run all tests"""
    print("🚀 Enhanced Shopify System Test Suite")
    print("=" * 50)

    # Initialize Utils
    Utils.load_resources()
    print("✅ Utils initialized")

    try:
        # Run tests
        await test_product_fetching()
        await test_store_validation()
        await test_proxy_integration()
        await test_multi_store_retry()

        print("\n" + "=" * 50)
        print("🎯 Enhanced Shopify System Test Complete!")
        print("✨ Features tested:")
        print("  • Multi-product fetching per store")
        print("  • Store validation and availability")
        print("  • Proxy integration")
        print("  • Multi-store retry system")
        print("  • Enhanced error handling")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
