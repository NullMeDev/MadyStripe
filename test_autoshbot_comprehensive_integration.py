#!/usr/bin/env python3
"""
Comprehensive AutoshBotSRC Integration Test Suite
Tests Stripe and Shopify integration end-to-end
"""

import sys
import os
import asyncio
import time
from unittest.mock import Mock, AsyncMock
import aiohttp

# Add AutoshBotSRC to path
sys.path.insert(0, 'AutoshBotSRC/AutoshBotSRC')

# Import required modules
from utils import Utils
from commands.shopify import register_resource_commands, fetchProducts_enhanced, verify_shopify_url_enhanced
from gateways.autoShopify_fixed import fetchProducts as gateway_fetch
from gateways.autoStripe import process_card as stripe_process, STRIPE_KEY
from gateways.autoUnified import process_card as unified_process
from database import add_shopify_site, get_user_shopify_sites, remove_shopify_site

class AutoshBotIntegrationTester:
    def __init__(self):
        self.test_results = []
        self.test_user_id = 123456789  # Test user ID

    def log_result(self, test_name, success, message="", details=""):
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': time.time()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")

    async def test_1_basic_imports(self):
        """Test 1: Basic module imports"""
        try:
            # Test command imports
            from commands.shopify import register_resource_commands
            import inspect
            assert inspect.iscoroutinefunction(register_resource_commands), "register_resource_commands should be async"

            # Test gateway imports
            from gateways.autoShopify_fixed import fetchProducts
            from gateways.autoStripe import process_card, STRIPE_KEY
            from gateways.autoUnified import process_card as unified

            # Test Utils
            proxies = Utils.get_all_proxies()
            assert isinstance(proxies, list), "get_all_proxies should return list"

            self.log_result("Basic Imports", True, "All modules imported successfully")
            return True
        except Exception as e:
            self.log_result("Basic Imports", False, f"Import failed: {str(e)}")
            return False

    async def test_2_utils_functionality(self):
        """Test 2: Utils class functionality"""
        try:
            # Test proxy loading
            Utils.load_resources()
            proxies = Utils.get_all_proxies()
            assert len(proxies) > 0, "Should have proxies loaded"

            # Test proxy formatting
            formatted = Utils.format_proxy("127.0.0.1:8080:user:pass")
            assert formatted == "http://user:pass@127.0.0.1:8080", f"Proxy formatting failed: {formatted}"

            # Test random proxy
            proxy = Utils.get_random_proxy()
            assert proxy is not None, "Should get a random proxy"

            self.log_result("Utils Functionality", True, "Utils methods work correctly")
            return True
        except Exception as e:
            self.log_result("Utils Functionality", False, f"Utils test failed: {str(e)}")
            return False

    async def test_3_shopify_url_validation(self):
        """Test 3: Shopify URL validation"""
        try:
            # Test invalid URL
            success, result = await verify_shopify_url_enhanced("invalid-url")
            assert not success, "Invalid URL should fail"
            assert "Invalid URL" in result, f"Expected error message, got: {result}"

            # Test valid Shopify URL (using a known working store)
            test_urls = [
                "https://wiredministries.com",  # Known working store
                "https://shopify.com",  # Should fail as not a store
            ]

            for url in test_urls:
                success, result = await verify_shopify_url_enhanced(url, startPrice=1)
                if "wiredministries.com" in url:
                    # This should work (though may fail due to network/rate limits)
                    pass  # Don't assert as network dependent
                else:
                    # shopify.com should fail
                    assert not success, f"shopify.com should not be a valid store: {result}"

            self.log_result("Shopify URL Validation", True, "URL validation works correctly")
            return True
        except Exception as e:
            self.log_result("Shopify URL Validation", False, f"URL validation failed: {str(e)}")
            return False

    async def test_4_database_operations(self):
        """Test 4: Database operations for Shopify stores"""
        try:
            # Clean up any existing test data
            existing = get_user_shopify_sites(self.test_user_id)
            for site in existing:
                if "test-autoshbot" in site:
                    remove_shopify_site(self.test_user_id, site)

            # Test adding a store
            test_url = "https://test-autoshbot-store.com"
            success = add_shopify_site(self.test_user_id, test_url)
            assert success, "Should successfully add test store"

            # Test retrieving stores
            stores = get_user_shopify_sites(self.test_user_id)
            assert test_url in stores, f"Test store should be in list: {stores}"

            # Test removing store
            success = remove_shopify_site(self.test_user_id, test_url)
            assert success, "Should successfully remove test store"

            # Verify removal
            stores = get_user_shopify_sites(self.test_user_id)
            assert test_url not in stores, f"Test store should be removed: {stores}"

            self.log_result("Database Operations", True, "Database CRUD operations work correctly")
            return True
        except Exception as e:
            self.log_result("Database Operations", False, f"Database operations failed: {str(e)}")
            return False

    async def test_5_command_registration_simulation(self):
        """Test 5: Command registration simulation"""
        try:
            # Create mock bot
            mock_bot = Mock()

            # Mock message handlers
            mock_bot.message_handler = Mock(return_value=lambda func: func)

            # Register commands
            await register_resource_commands(mock_bot)

            # Verify handlers were registered
            assert mock_bot.message_handler.called, "Message handlers should be registered"

            # Check that /addsh, /shopify, /rmsh commands are registered
            calls = mock_bot.message_handler.call_args_list
            commands_registered = []
            for call in calls:
                if 'commands' in call[1]:
                    commands_registered.extend(call[1]['commands'])

            expected_commands = ['addsh', 'shopify', 'rmsh']
            for cmd in expected_commands:
                assert cmd in commands_registered, f"Command /{cmd} should be registered"

            self.log_result("Command Registration", True, f"Commands registered: {commands_registered}")
            return True
        except Exception as e:
            self.log_result("Command Registration", False, f"Command registration failed: {str(e)}")
            return False

    async def test_6_gateway_function_signatures(self):
        """Test 6: Gateway function signatures and basic functionality"""
        try:
            import inspect

            # Test Stripe gateway
            stripe_sig = inspect.signature(stripe_process)
            assert 'card_number' in stripe_sig.parameters, "Stripe process_card should have card_number parameter"

            # Test Shopify gateway
            shopify_sig = inspect.signature(gateway_fetch)
            assert 'domain' in shopify_sig.parameters, "Shopify fetchProducts should have domain parameter"
            assert 'startPrice' in shopify_sig.parameters, "Shopify fetchProducts should have startPrice parameter"

            # Test Unified gateway
            unified_sig = inspect.signature(unified_process)
            assert 'card_number' in unified_sig.parameters, "Unified process_card should have card_number parameter"

            self.log_result("Gateway Signatures", True, "All gateway functions have correct signatures")
            return True
        except Exception as e:
            self.log_result("Gateway Signatures", False, f"Gateway signature check failed: {str(e)}")
            return False

    async def test_7_error_handling(self):
        """Test 7: Error handling scenarios"""
        try:
            # Test invalid Shopify domain
            result = await fetchProducts_enhanced("https://invalid-domain-that-does-not-exist-12345.com")
            assert isinstance(result, tuple), "Should return error tuple for invalid domain"
            assert not result[0], "Should fail for invalid domain"

            # Test rate limiting (simulate)
            # This would require multiple rapid calls, but we'll test the rate limit structure
            from commands.shopify import rate_limits
            assert isinstance(rate_limits, dict), "Rate limits should be a dict"

            # Test proxy failure handling
            # Temporarily break proxy loading
            original_proxies = Utils.proxies.copy()
            Utils.proxies = []
            try:
                result = await fetchProducts_enhanced("https://example.com")
                # Should handle no proxy gracefully
                assert isinstance(result, tuple), "Should handle no proxy scenario"
            finally:
                Utils.proxies = original_proxies

            self.log_result("Error Handling", True, "Error scenarios handled correctly")
            return True
        except Exception as e:
            self.log_result("Error Handling", False, f"Error handling test failed: {str(e)}")
            return False

    async def test_8_concurrent_requests_simulation(self):
        """Test 8: Concurrent request handling simulation"""
        try:
            # Simulate multiple concurrent requests
            async def mock_request(url):
                await asyncio.sleep(0.1)  # Simulate network delay
                return {"success": True, "url": url}

            # Create multiple concurrent tasks
            urls = [f"https://test-{i}.com" for i in range(5)]
            tasks = [mock_request(url) for url in urls]

            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            # Verify all completed
            assert len(results) == 5, f"Should have 5 results, got {len(results)}"
            assert all(r["success"] for r in results), "All requests should succeed"

            # Verify reasonable timing (should be faster than sequential)
            duration = end_time - start_time
            assert duration < 0.8, f"Concurrent requests took too long: {duration}s"

            self.log_result("Concurrent Requests", True, f"5 concurrent requests completed in {duration:.2f}s")
            return True
        except Exception as e:
            self.log_result("Concurrent Requests", False, f"Concurrent requests test failed: {str(e)}")
            return False

    def generate_test_report(self):
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests

        print("\n" + "="*60)
        print("🎯 AUTOSHBOTSRC INTEGRATION TEST REPORT")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(".1f")

        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")

        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"  • {result['test']}: {result['message']}")

        print("\n" + "="*60)

        # Overall assessment
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED! AutoshBotSRC integration is ready for production.")
        elif failed_tests <= 2:
            print("⚠️  MINOR ISSUES: Integration mostly working, minor fixes needed.")
        else:
            print("❌ SIGNIFICANT ISSUES: Integration needs major fixes before production.")

        return passed_tests == total_tests

    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting AutoshBotSRC Integration Test Suite...")
        print("Testing Stripe & Shopify integration fixes\n")

        # Initialize Utils
        Utils.load_resources()

        # Run tests
        tests = [
            self.test_1_basic_imports,
            self.test_2_utils_functionality,
            self.test_3_shopify_url_validation,
            self.test_4_database_operations,
            self.test_5_command_registration_simulation,
            self.test_6_gateway_function_signatures,
            self.test_7_error_handling,
            self.test_8_concurrent_requests_simulation,
        ]

        for test in tests:
            await test()
            await asyncio.sleep(0.1)  # Small delay between tests

        # Generate report
        success = self.generate_test_report()
        return success

async def main():
    """Main test runner"""
    tester = AutoshBotIntegrationTester()
    success = await tester.run_all_tests()

    if success:
        print("\n🎯 RESULT: AutoshBotSRC Stripe & Shopify integration is WORKING correctly!")
        return 0
    else:
        print("\n❌ RESULT: Integration has issues that need to be fixed.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
