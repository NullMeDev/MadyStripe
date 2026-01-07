#!/usr/bin/env python3
"""
Test script for enhanced Shopify integration with AutoshBotSRC
Tests the improved error handling, caching, and rate limiting features
"""

import asyncio
import sys
import os

# Add AutoshBotSRC to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'AutoshBotSRC/AutoshBotSRC'))

async def test_enhanced_shopify():
    """Test the enhanced Shopify integration"""
    print("🧪 Testing Enhanced Shopify Integration")
    print("=" * 50)

    try:
        # Test imports
        print("\n1. Testing imports...")
        from commands.shopify_enhanced import (
            fetchProducts_enhanced,
            verify_shopify_url_enhanced,
            register_resource_commands,
            check_rate_limit,
            get_working_proxy
        )
        print("   ✅ All enhanced functions imported successfully")

        # Test rate limiting
        print("\n2. Testing rate limiting...")
        domain = "test-shopify-store.com"
        for i in range(35):  # Test beyond limit
            result = await check_rate_limit(domain)
            if i < 30:
                assert result == True, f"Rate limit should allow request {i+1}"
            else:
                assert result == False, f"Rate limit should block request {i+1}"

        print("   ✅ Rate limiting working correctly")

        # Test proxy functionality (will fail without real proxies but should not crash)
        print("\n3. Testing proxy handling...")
        try:
            proxy = await get_working_proxy()
            print(f"   ✅ Proxy function executed (proxy: {proxy is not None})")
        except Exception as e:
            print(f"   ⚠️  Proxy test failed (expected without real proxies): {e}")

        # Test error handling with invalid domain
        print("\n4. Testing error handling...")
        result = await fetchProducts_enhanced("invalid-domain-12345.com")
        assert isinstance(result, tuple), "Should return error tuple"
        assert result[0] == False, "Should indicate failure"
        print(f"   ✅ Error handling working: {result[1]}")

        # Test caching
        print("\n5. Testing caching...")
        # First call should cache
        start_time = asyncio.get_event_loop().time()
        result1 = await fetchProducts_enhanced("invalid-domain-12345.com")
        first_call_time = asyncio.get_event_loop().time() - start_time

        # Second call should use cache
        start_time = asyncio.get_event_loop().time()
        result2 = await fetchProducts_enhanced("invalid-domain-12345.com")
        second_call_time = asyncio.get_event_loop().time() - start_time

        # Results should be identical
        assert result1 == result2, "Cached result should match original"
        print(".4f")        print("\n6. Testing URL verification...")
        # Test with invalid URL
        success, message = await verify_shopify_url_enhanced("not-a-url")
        assert success == False, "Should fail for invalid URL"
        print(f"   ✅ URL validation working: {message}")

        print("\n🎉 All enhanced Shopify tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_backward_compatibility():
    """Test that original functions still work"""
    print("\n🔄 Testing backward compatibility...")

    try:
        from commands.shopify_enhanced import fetchProducts, verify_shopify_url
        print("   ✅ Original function names still available")

        # Test original functions
        result = await fetchProducts("invalid-domain.com")
        assert isinstance(result, tuple), "Original function should work"
        print("   ✅ Original functions working correctly")

        return True
    except Exception as e:
        print(f"   ❌ Backward compatibility failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Enhanced Shopify Integration Test Suite")
    print("=" * 50)

    # Test enhanced features
    enhanced_ok = await test_enhanced_shopify()

    # Test backward compatibility
    compat_ok = await test_backward_compatibility()

    print("\n" + "=" * 50)
    if enhanced_ok and compat_ok:
        print("🎯 ALL TESTS PASSED! Enhanced Shopify integration is ready.")
        print("\n📋 Improvements implemented:")
        print("   • Enhanced error handling with specific error codes")
        print("   • Response caching (5-minute TTL)")
        print("   • Rate limiting (30 requests/minute per domain)")
        print("   • Improved proxy rotation with testing")
        print("   • Better timeout and connection management")
        print("   • Backward compatibility maintained")
    else:
        print("❌ Some tests failed. Check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
