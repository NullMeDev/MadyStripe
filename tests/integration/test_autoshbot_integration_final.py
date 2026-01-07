#!/usr/bin/env python3
"""
Comprehensive AutoshBotSRC Integration Test Suite
Tests end-to-end functionality including Shopify and Stripe integrations
"""

import asyncio
import sys
import os
import time
from datetime import datetime
import json

# Add AutoshBotSRC to path
sys.path.insert(0, 'AutoshBotSRC/AutoshBotSRC')

class IntegrationTester:
    def __init__(self):
        self.results = {
            'imports': {},
            'functions': {},
            'commands': {},
            'database': {},
            'end_to_end': {},
            'performance': {},
            'error_handling': {}
        }
        self.start_time = time.time()

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    async def test_imports(self):
        """Test 1: Import verification"""
        self.log("🔍 Testing imports...")

        # Test Shopify imports
        try:
            from gateways.autoShopify_fixed import fetchProducts
            from commands.shopify_enhanced import register_resource_commands
            self.results['imports']['shopify'] = True
            self.log("   ✅ Shopify imports successful")
        except Exception as e:
            self.results['imports']['shopify'] = False
            self.log(f"   ❌ Shopify import failed: {e}")

        # Test Stripe imports
        try:
            from gateways.autoStripe import process_card, STRIPE_KEY
            self.results['imports']['stripe'] = True
            self.log(f"   ✅ Stripe imports successful (key: {STRIPE_KEY[:20]}...)")
        except Exception as e:
            self.results['imports']['stripe'] = False
            self.log(f"   ❌ Stripe import failed: {e}")

        # Test Unified gateway
        try:
            from gateways.autoUnified import process_card as unified_process
            self.results['imports']['unified'] = True
            self.log("   ✅ Unified gateway import successful")
        except Exception as e:
            self.results['imports']['unified'] = False
            self.log(f"   ❌ Unified import failed: {e}")

        # Test database imports
        try:
            from database import add_shopify_site, get_user_shopify_sites, add_proxy
            self.results['imports']['database'] = True
            self.log("   ✅ Database imports successful")
        except Exception as e:
            self.results['imports']['database'] = False
            self.log(f"   ❌ Database import failed: {e}")

    async def test_function_signatures(self):
        """Test 2: Function signature verification"""
        self.log("🔍 Testing function signatures...")

        try:
            from gateways.autoShopify_fixed import fetchProducts
            import inspect
            sig = inspect.signature(fetchProducts)
            expected_params = ['domain', 'startPrice']
            actual_params = list(sig.parameters.keys())

            if all(param in actual_params for param in expected_params):
                self.results['functions']['shopify_signature'] = True
                self.log(f"   ✅ Shopify fetchProducts signature correct: {sig}")
            else:
                self.results['functions']['shopify_signature'] = False
                self.log(f"   ❌ Shopify signature missing params: {sig}")
        except Exception as e:
            self.results['functions']['shopify_signature'] = False
            self.log(f"   ❌ Shopify signature check failed: {e}")

        try:
            from gateways.autoStripe import process_card
            sig = inspect.signature(process_card)
            expected_params = ['card_number', 'expiry_month', 'expiry_year', 'cvv', 'amount']
            actual_params = list(sig.parameters.keys())

            if all(param in actual_params for param in expected_params):
                self.results['functions']['stripe_signature'] = True
                self.log(f"   ✅ Stripe process_card signature correct: {sig}")
            else:
                self.results['functions']['stripe_signature'] = False
                self.log(f"   ❌ Stripe signature missing params: {sig}")
        except Exception as e:
            self.results['functions']['stripe_signature'] = False
            self.log(f"   ❌ Stripe signature check failed: {e}")

    async def test_command_registration(self):
        """Test 3: Command registration verification"""
        self.log("🔍 Testing command registration...")

        try:
            from commands.shopify_enhanced import register_resource_commands
            import inspect

            if inspect.iscoroutinefunction(register_resource_commands):
                self.results['commands']['registration'] = True
                self.log("   ✅ register_resource_commands is async and available")
            else:
                self.results['commands']['registration'] = False
                self.log("   ⚠️  register_resource_commands is not async")
        except Exception as e:
            self.results['commands']['registration'] = False
            self.log(f"   ❌ Command registration failed: {e}")

    async def test_database_operations(self):
        """Test 4: Database operations"""
        self.log("🔍 Testing database operations...")

        try:
            from database import add_shopify_site, get_user_shopify_sites, remove_shopify_site

            # Test adding a store
            test_user_id = "test_user_123"
            test_store = "https://test-shopify-store.com"

            # Add store
            result = add_shopify_site(test_user_id, test_store, "test_variant_123")
            if result:
                self.results['database']['add_store'] = True
                self.log("   ✅ Add Shopify store successful")
            else:
                self.results['database']['add_store'] = False
                self.log("   ❌ Add Shopify store failed")

            # Get stores
            stores = get_user_shopify_sites(test_user_id)
            if test_store in stores:
                self.results['database']['get_stores'] = True
                self.log("   ✅ Get Shopify stores successful")
            else:
                self.results['database']['get_stores'] = False
                self.log("   ❌ Get Shopify stores failed")

            # Remove store
            result = remove_shopify_site(test_user_id, test_store)
            if result:
                self.results['database']['remove_store'] = True
                self.log("   ✅ Remove Shopify store successful")
            else:
                self.results['database']['remove_store'] = False
                self.log("   ❌ Remove Shopify store failed")

        except Exception as e:
            self.log(f"   ❌ Database operations failed: {e}")
            self.results['database']['operations'] = False

    async def test_shopify_fetch_products(self):
        """Test 5: Shopify product fetching"""
        self.log("🔍 Testing Shopify product fetching...")

        try:
            from gateways.autoShopify_fixed import fetchProducts

            # Test with a known working Shopify store
            test_domain = "https://wiredministries.com"  # Known working store

            success, result = await fetchProducts(test_domain, 0)

            if success and isinstance(result, dict):
                self.results['end_to_end']['shopify_fetch'] = True
                self.log(f"   ✅ Shopify fetch successful: {result.get('site', 'unknown')}")
            else:
                self.results['end_to_end']['shopify_fetch'] = False
                self.log(f"   ❌ Shopify fetch failed: {result}")

        except Exception as e:
            self.results['end_to_end']['shopify_fetch'] = False
            self.log(f"   ❌ Shopify fetch test failed: {e}")

    async def test_stripe_processing(self):
        """Test 6: Stripe payment processing"""
        self.log("🔍 Testing Stripe payment processing...")

        try:
            from gateways.autoStripe import process_card

            # Test with a known declined card (safe for testing)
            test_card = {
                'card_number': '4000000000000002',  # Stripe test card that declines
                'expiry_month': '12',
                'expiry_year': '2025',
                'cvv': '123',
                'amount': '1.00'
            }

            success, message, gateway = await process_card(test_card["card_number"], test_card["expiry_month"], test_card["expiry_year"], test_card["cvv"], "1.00")

            # We expect this to fail (card declined), so success=False is correct
            if not success and 'declined' in message.lower():
                self.results['end_to_end']['stripe_process'] = True
                self.log("   ✅ Stripe processing test successful (expected decline)")
            else:
                self.results['end_to_end']['stripe_process'] = False
                self.log(f"   ❌ Stripe processing unexpected result: {success}, {message}")

        except Exception as e:
            self.results['end_to_end']['stripe_process'] = False
            self.log(f"   ❌ Stripe processing test failed: {e}")

    async def test_error_handling(self):
        """Test 7: Error handling scenarios"""
        self.log("🔍 Testing error handling...")

        try:
            from gateways.autoShopify_fixed import fetchProducts

            # Test invalid domain
            success, result = await fetchProducts("https://invalid-domain-that-does-not-exist-12345.com", 0)
            if not success and "site_error" in result:
                self.results['error_handling']['invalid_domain'] = True
                self.log("   ✅ Invalid domain error handling correct")
            else:
                self.results['error_handling']['invalid_domain'] = False
                self.log(f"   ❌ Invalid domain error handling failed: {result}")

            # Test non-Shopify site
            success, result = await fetchProducts("https://google.com", 0)
            if not success and "not_shopify" in result:
                self.results['error_handling']['non_shopify'] = True
                self.log("   ✅ Non-Shopify site error handling correct")
            else:
                self.results['error_handling']['non_shopify'] = False
                self.log(f"   ❌ Non-Shopify site error handling failed: {result}")

        except Exception as e:
            self.log(f"   ❌ Error handling test failed: {e}")
            self.results['error_handling']['general'] = False

    async def test_performance(self):
        """Test 8: Performance testing"""
        self.log("🔍 Testing performance...")

        try:
            from gateways.autoShopify_fixed import fetchProducts
            import time

            # Test response time
            start_time = time.time()
            success, result = await fetchProducts("https://wiredministries.com", 0)
            end_time = time.time()

            response_time = end_time - start_time

            if response_time < 30:  # Should respond within 30 seconds
                self.results['performance']['response_time'] = True
                self.log(f"   ✅ Response time acceptable: {response_time:.2f}s")
            else:
                self.results['performance']['response_time'] = False
                self.log(f"   ❌ Response time too slow: {response_time:.2f}s")

        except Exception as e:
            self.results['performance']['response_time'] = False
            self.log(f"   ❌ Performance test failed: {e}")

    async def test_proxy_rotation(self):
        """Test 9: Proxy rotation"""
        self.log("🔍 Testing proxy rotation...")

        try:
            from utils import Utils

            # Test proxy retrieval
            proxy1 = Utils.get_random_proxy()
            proxy2 = Utils.get_random_proxy()

            if proxy1 and proxy2:
                # Check if proxies are different (rotation working)
                if proxy1 != proxy2:
                    self.results['end_to_end']['proxy_rotation'] = True
                    self.log("   ✅ Proxy rotation working")
                else:
                    self.results['end_to_end']['proxy_rotation'] = False
                    self.log("   ⚠️  Proxy rotation may not be working (same proxy returned)")
            else:
                self.results['end_to_end']['proxy_rotation'] = False
                self.log("   ❌ Proxy retrieval failed")

        except Exception as e:
            self.results['end_to_end']['proxy_rotation'] = False
            self.log(f"   ❌ Proxy rotation test failed: {e}")

    def generate_report(self):
        """Generate comprehensive test report"""
        end_time = time.time()
        duration = end_time - self.start_time

        self.log(f"\n📊 FINAL TEST REPORT (Duration: {duration:.2f}s)")
        self.log("=" * 60)

        categories = {
            'imports': 'Module Imports',
            'functions': 'Function Signatures',
            'commands': 'Command Registration',
            'database': 'Database Operations',
            'end_to_end': 'End-to-End Functionality',
            'performance': 'Performance Tests',
            'error_handling': 'Error Handling'
        }

        total_tests = 0
        passed_tests = 0

        for category_key, category_name in categories.items():
            if category_key in self.results:
                self.log(f"\n🔍 {category_name}:")
                category_results = self.results[category_key]

                for test_name, result in category_results.items():
                    total_tests += 1
                    status = "✅ PASS" if result else "❌ FAIL"
                    passed_tests += 1 if result else 0
                    self.log(f"   {status} {test_name.replace('_', ' ').title()}")

        # Overall summary
        self.log(f"\n🎯 OVERALL RESULTS:")
        self.log(f"   Total Tests: {total_tests}")
        self.log(f"   Passed: {passed_tests}")
        self.log(f"   Failed: {total_tests - passed_tests}")
        self.log(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "No tests run")

        if passed_tests == total_tests:
            self.log("   🎉 ALL TESTS PASSED!")
        elif passed_tests >= total_tests * 0.8:
            self.log("   ✅ MOSTLY SUCCESSFUL - Minor issues to address")
        else:
            self.log("   ⚠️  SIGNIFICANT ISSUES - Requires attention")

        return passed_tests == total_tests

    async def run_all_tests(self):
        """Run all integration tests"""
        self.log("🚀 Starting AutoshBotSRC Integration Test Suite")
        self.log("=" * 60)

        await self.test_imports()
        await self.test_function_signatures()
        await self.test_command_registration()
        await self.test_database_operations()
        await self.test_shopify_fetch_products()
        await self.test_stripe_processing()
        await self.test_error_handling()
        await self.test_performance()
        await self.test_proxy_rotation()

        return self.generate_report()

async def main():
    """Main test runner"""
    tester = IntegrationTester()
    success = await tester.run_all_tests()

    if success:
        print("\n🎉 Integration tests completed successfully!")
        return 0
    else:
        print("\n⚠️  Some tests failed - check the report above")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
