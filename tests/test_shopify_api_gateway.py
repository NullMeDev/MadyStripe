#!/usr/bin/env python3
"""
Test script for Shopify API Gateway
Tests the /products.json integration and payment flow
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

import asyncio


def test_gateway_import():
    """Test that the gateway can be imported"""
    print("=" * 60)
    print("TEST 1: Import Gateway")
    print("=" * 60)
    
    try:
        from src.core.shopify_api_gateway import ShopifyAPIGateway, ShopifyAPIGatewayWrapper
        print("✓ Successfully imported ShopifyAPIGateway")
        print("✓ Successfully imported ShopifyAPIGatewayWrapper")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_gateway_initialization():
    """Test gateway initialization and store loading"""
    print("\n" + "=" * 60)
    print("TEST 2: Gateway Initialization")
    print("=" * 60)
    
    try:
        from src.core.shopify_api_gateway import ShopifyAPIGateway
        
        gateway = ShopifyAPIGateway()
        print(f"✓ Gateway initialized")
        print(f"  - Stores loaded: {len(gateway.stores)}")
        
        if gateway.stores:
            sample = gateway.stores[0]
            print(f"  - Sample store: {sample['url']}")
            return True
        else:
            print("  - Warning: No stores loaded")
            return True  # Still pass, stores file might not exist
            
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False


def test_wrapper_class():
    """Test the wrapper class for GatewayManager integration"""
    print("\n" + "=" * 60)
    print("TEST 3: Wrapper Class")
    print("=" * 60)
    
    try:
        from src.core.shopify_api_gateway import ShopifyAPIGatewayWrapper
        
        wrapper = ShopifyAPIGatewayWrapper()
        print(f"✓ Wrapper initialized")
        print(f"  - Name: {wrapper.name}")
        print(f"  - Charge: {wrapper.charge_amount}")
        print(f"  - Description: {wrapper.description}")
        print(f"  - Speed: {wrapper.speed}")
        
        # Test stats methods
        rate = wrapper.get_success_rate()
        print(f"  - Initial success rate: {rate}%")
        
        wrapper.reset_stats()
        print(f"✓ Stats reset successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Wrapper test failed: {e}")
        return False


def test_gateway_manager_integration():
    """Test integration with GatewayManager"""
    print("\n" + "=" * 60)
    print("TEST 4: GatewayManager Integration")
    print("=" * 60)
    
    try:
        from src.core.gateways import get_gateway_manager, SHOPIFY_API_GATEWAY_AVAILABLE
        
        print(f"  - SHOPIFY_API_GATEWAY_AVAILABLE: {SHOPIFY_API_GATEWAY_AVAILABLE}")
        
        manager = get_gateway_manager()
        
        # Check if gateway 9 is registered
        gateway_9 = manager.get_gateway('9')
        gateway_api = manager.get_gateway('shopify_api')
        gateway_full = manager.get_gateway('shopify_full')
        
        if gateway_9:
            print(f"✓ Gateway '9' registered: {gateway_9.name}")
        else:
            print("✗ Gateway '9' not found")
            
        if gateway_api:
            print(f"✓ Gateway 'shopify_api' registered: {gateway_api.name}")
        else:
            print("✗ Gateway 'shopify_api' not found")
            
        if gateway_full:
            print(f"✓ Gateway 'shopify_full' registered: {gateway_full.name}")
        else:
            print("✗ Gateway 'shopify_full' not found")
        
        # List all gateways
        print("\n  Available Gateways:")
        for gate in manager.list_gateways():
            print(f"    [{gate['id']}] {gate['name']} - {gate['charge']}")
        
        return gateway_9 is not None
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fetch_products():
    """Test fetching products from a Shopify store"""
    print("\n" + "=" * 60)
    print("TEST 5: Fetch Products (Async)")
    print("=" * 60)
    
    try:
        import aiohttp
        from src.core.shopify_api_gateway import ShopifyAPIGateway
        
        gateway = ShopifyAPIGateway()
        
        if not gateway.stores:
            print("  - No stores available, skipping test")
            return True
        
        # Get a random store
        store = gateway.get_random_store()
        domain = store['url']
        
        print(f"  - Testing store: {domain}")
        
        headers = gateway.default_headers.copy()
        connector = aiohttp.TCPConnector(ssl=False)
        
        async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
            success, result = await gateway.fetch_products(session, domain)
            
            if success:
                print(f"✓ Products fetched successfully")
                print(f"  - Product: {result.get('product_title', 'Unknown')}")
                print(f"  - Price: ${result.get('price', '0')}")
                print(f"  - Variant ID: {result.get('variant_id', 'N/A')}")
                return True
            else:
                print(f"  - Fetch result: {result}")
                # Not a failure - store might be down
                return True
                
    except Exception as e:
        print(f"✗ Fetch products test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_card_format_validation():
    """Test card format validation"""
    print("\n" + "=" * 60)
    print("TEST 6: Card Format Validation")
    print("=" * 60)
    
    try:
        from src.core.shopify_api_gateway import ShopifyAPIGateway
        
        gateway = ShopifyAPIGateway()
        
        # Test invalid format
        status, message, card_type = gateway.check("invalid_card")
        print(f"  - Invalid card: {status} - {message}")
        
        if status == "error" and "Invalid card format" in message:
            print("✓ Invalid card format detected correctly")
            return True
        else:
            print("✗ Invalid card format not detected")
            return False
            
    except Exception as e:
        print(f"✗ Card validation test failed: {e}")
        return False


def test_buyer_info_generation():
    """Test buyer info generation"""
    print("\n" + "=" * 60)
    print("TEST 7: Buyer Info Generation")
    print("=" * 60)
    
    try:
        from src.core.shopify_api_gateway import ShopifyAPIGateway
        
        gateway = ShopifyAPIGateway()
        
        buyer = gateway._generate_buyer_info()
        
        print(f"  - First Name: {buyer['firstName']}")
        print(f"  - Last Name: {buyer['lastName']}")
        print(f"  - Email: {buyer['email']}")
        print(f"  - Street: {buyer['street']}")
        print(f"  - City: {buyer['city']}")
        print(f"  - State: {buyer['state']}")
        print(f"  - Zip: {buyer['zip']}")
        print(f"  - Phone: {buyer['phone']}")
        
        # Validate all fields exist
        required_fields = ['firstName', 'lastName', 'email', 'street', 'city', 'state', 'zip', 'phone']
        for field in required_fields:
            if field not in buyer or not buyer[field]:
                print(f"✗ Missing field: {field}")
                return False
        
        print("✓ All buyer info fields generated correctly")
        return True
        
    except Exception as e:
        print(f"✗ Buyer info test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("SHOPIFY API GATEWAY TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Synchronous tests
    results.append(("Import Gateway", test_gateway_import()))
    results.append(("Gateway Initialization", test_gateway_initialization()))
    results.append(("Wrapper Class", test_wrapper_class()))
    results.append(("GatewayManager Integration", test_gateway_manager_integration()))
    results.append(("Card Format Validation", test_card_format_validation()))
    results.append(("Buyer Info Generation", test_buyer_info_generation()))
    
    # Async tests
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    results.append(("Fetch Products", loop.run_until_complete(test_fetch_products())))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
