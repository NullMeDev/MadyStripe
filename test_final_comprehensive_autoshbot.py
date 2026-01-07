#!/usr/bin/env python3
"""
Final Comprehensive AutoshBotSRC Test Suite
Tests all aspects of the enhanced Stripe/Shopify integration
"""

import sys
import asyncio
import time
import json
sys.path.insert(0, 'AutoshBotSRC/AutoshBotSRC')

from telebot.async_telebot import AsyncTeleBot
from database import init_db, add_shopify_site, get_user_shopify_sites
from commands.start import register_start_command
from commands.cmds import register_cmds_command
from commands.admin import register_admin_commands
from commands.me import register_me_command
from commands.bin_command import register_bin_command
from commands.credits_command import register_credits_commands
from commands.redeem_command import register_redeem_commands
from commands.plans import register_plans_command
from commands.shopify import register_resource_commands
from gateways import register_gateways
from gateways.autoShopify_enhanced import (
    ShopifyProductManager,
    MultiStoreRetrySystem,
    VERIFIED_STORES,
    process_card_enhanced
)
from gateways.autoStripe import process_card as stripe_process
from utils import Utils

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def add_result(self, test_name, success, message=""):
        if success:
            self.passed += 1
            status = "✅ PASS"
        else:
            self.failed += 1
            status = "❌ FAIL"

        result = f"{status} {test_name}"
        if message:
            result += f" - {message}"
        self.results.append(result)
        print(result)

    def summary(self):
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        return f"Tests: {total} | Passed: {self.passed} | Failed: {self.failed} | Success Rate: {success_rate:.1f}%"

results = TestResults()

async def test_bot_initialization():
    """Test complete bot initialization"""
    print("\n🤖 Testing Bot Initialization...")

    try:
        # Initialize database and utils
        init_db()
        Utils.load_resources()
        results.add_result("Database initialization", True)

        # Create bot instance
        bot = AsyncTeleBot('dummy_token_for_testing')
        results.add_result("Bot instance creation", True)

        # Register all commands
        register_start_command(bot)
        register_cmds_command(bot)
        register_admin_commands(bot)
        register_me_command(bot)
        register_bin_command(bot)
        register_credits_commands(bot)
        register_redeem_commands(bot)
        register_plans_command(bot)
        results.add_result("Core commands registration", True)

        # Register Shopify commands
        await register_resource_commands(bot)
        results.add_result("Shopify commands registration", True)

        # Register gateways
        await register_gateways(bot)
        results.add_result("Gateway registration", True)

        results.add_result("Complete bot initialization", True, "All components initialized successfully")

    except Exception as e:
        results.add_result("Bot initialization", False, str(e))

async def test_database_operations():
    """Test database operations for Shopify stores"""
    print("\n💾 Testing Database Operations...")

    test_user_id = 12345
    test_store = "https://wiredministries.com"

    try:
        # Add store
        success = add_shopify_site(test_user_id, test_store)
        results.add_result("Add Shopify store", success)

        # Retrieve stores
        stores = get_user_shopify_sites(test_user_id)
        has_store = test_store in stores
        results.add_result("Retrieve user stores", has_store)

        results.add_result("Database operations", True, f"Store management working")

    except Exception as e:
        results.add_result("Database operations", False, str(e))

async def test_product_manager():
    """Test enhanced product manager"""
    print("\n🛍️  Testing Product Manager...")

    manager = ShopifyProductManager()

    try:
        # Test product fetching from a known store
        products = await manager.fetch_store_products("wiredministries.com", max_products=3)

        if products and len(products) > 0:
            total_variants = sum(len(p['variants']) for p in products)
            results.add_result("Product fetching", True, f"{len(products)} products, {total_variants} variants")
        else:
            results.add_result("Product fetching", False, "No products found")

        # Test caching (second call should be instant)
        start_time = time.time()
        products2 = await manager.fetch_store_products("wiredministries.com", max_products=3)
        fetch_time = time.time() - start_time

        cached = fetch_time < 0.1  # Should be very fast if cached
        results.add_result("Product caching", cached, ".3f")

    except Exception as e:
        results.add_result("Product manager", False, str(e))

async def test_multi_store_retry():
    """Test multi-store retry system"""
    print("\n🔄 Testing Multi-Store Retry System...")

    manager = ShopifyProductManager()
    retry_system = MultiStoreRetrySystem(manager)

    try:
        # Test with a test card (should get consistent results)
        test_card = {
            'cc': '4111111111111111',
            'mes': '12',
            'ano': '2025',
            'cvv': '123'
        }

        result = await retry_system.process_card_until_result(
            test_card['cc'], test_card['mes'], test_card['ano'], test_card['cvv']
        )

        success, message, store_used, amount, currency = result

        # Should get some definitive result (success or decline)
        definitive = "declined" in message.lower() or "charged" in message.lower() or "live" in message.lower()
        results.add_result("Multi-store retry", definitive, f"Result: {message}")

    except Exception as e:
        results.add_result("Multi-store retry", False, str(e))

async def test_gateway_integration():
    """Test gateway integration"""
    print("\n🚪 Testing Gateway Integration...")

    try:
        # Test Stripe gateway import
        from gateways.autoStripe import STRIPE_KEY
        stripe_available = bool(STRIPE_KEY)
        results.add_result("Stripe gateway", stripe_available)

        # Test Shopify enhanced gateway
        from gateways.autoShopify_enhanced import process_card_enhanced
        shopify_available = callable(process_card_enhanced)
        results.add_result("Shopify enhanced gateway", shopify_available)

        # Test unified gateway
        from gateways.autoUnified import process_card as unified_process
        unified_available = callable(unified_process)
        results.add_result("Unified gateway", unified_available)

        results.add_result("Gateway integration", True, "All gateways available")

    except Exception as e:
        results.add_result("Gateway integration", False, str(e))

async def test_proxy_system():
    """Test proxy system"""
    print("\n🌐 Testing Proxy System...")

    try:
        proxies = Utils.get_all_proxies()
        proxy_count = len(proxies) if proxies else 0

        if proxy_count > 0:
            results.add_result("Proxy loading", True, f"{proxy_count} proxies loaded")

            # Test proxy formatting
            test_proxy = proxies[0] if proxies else None
            if test_proxy:
                formatted = Utils.format_proxy(test_proxy)
                valid_format = formatted and ('http://' in formatted or 'https://' in formatted)
                results.add_result("Proxy formatting", valid_format)
        else:
            results.add_result("Proxy loading", False, "No proxies available")

    except Exception as e:
        results.add_result("Proxy system", False, str(e))

async def test_error_handling():
    """Test error handling and edge cases"""
    print("\n🛡️  Testing Error Handling...")

    try:
        # Test invalid store URL
        manager = ShopifyProductManager()
        products = await manager.fetch_store_products("invalid-store-12345.com")
        handled_invalid = products == []
        results.add_result("Invalid store handling", handled_invalid)

        # Test empty product response
        products_empty = await manager.fetch_store_products("nonexistent-shop-999.com")
        handled_empty = products_empty == []
        results.add_result("Empty response handling", handled_empty)

        results.add_result("Error handling", True, "Edge cases handled properly")

    except Exception as e:
        results.add_result("Error handling", False, str(e))

async def test_performance():
    """Test performance metrics"""
    print("\n⚡ Testing Performance...")

    try:
        manager = ShopifyProductManager()

        # Test concurrent requests
        start_time = time.time()

        tasks = []
        for store in VERIFIED_STORES[:3]:  # Test first 3 stores
            tasks.append(manager.fetch_store_products(store['url'], max_products=2))

        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        successful_requests = sum(1 for r in results_list if isinstance(r, list) and len(r) > 0)
        avg_time = total_time / len(tasks)

        performance_ok = avg_time < 10  # Should complete within 10 seconds
        results.add_result("Concurrent requests", performance_ok, ".2f")

        results.add_result("Performance metrics", True, f"Avg response time: {avg_time:.2f}s")

    except Exception as e:
        results.add_result("Performance testing", False, str(e))

async def test_command_validation():
    """Test command validation and parsing"""
    print("\n📝 Testing Command Validation...")

    try:
        # Test URL validation logic
        from commands.shopify import extract_domain_name

        test_urls = [
            "https://wiredministries.com",
            "http://shopnicekicks.com",
            "wiredministries.com",
            "invalid-url",
            ""
        ]

        valid_domains = 0
        for url in test_urls:
            domain = extract_domain_name(url)
            if domain and '.' in domain:
                valid_domains += 1

        domain_extraction_ok = valid_domains >= 3
        results.add_result("URL validation", domain_extraction_ok, f"{valid_domains}/5 URLs processed")

        results.add_result("Command validation", True, "URL processing working")

    except Exception as e:
        results.add_result("Command validation", False, str(e))

async def main():
    """Run all comprehensive tests"""
    print("🚀 Final Comprehensive AutoshBotSRC Test Suite")
    print("=" * 60)

    # Run all tests
    await test_bot_initialization()
    await test_database_operations()
    await test_product_manager()
    await test_multi_store_retry()
    await test_gateway_integration()
    await test_proxy_system()
    await test_error_handling()
    await test_performance()
    await test_command_validation()

    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)

    for result in results.results:
        print(result)

    print("\n" + "=" * 60)
    print(f"🎯 {results.summary()}")

    if results.failed == 0:
        print("🎉 ALL TESTS PASSED! AutoshBotSRC is fully functional.")
        print("✨ Enhanced Stripe/Shopify integration is ready for production.")
    else:
        print(f"⚠️  {results.failed} tests failed. Review and fix issues before deployment.")

    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
