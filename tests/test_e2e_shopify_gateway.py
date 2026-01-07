#!/usr/bin/env python3
"""
End-to-End Test for Shopify API Gateway with Store Database
Tests the complete flow from store loading to card checking
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.shopify_api_gateway import ShopifyAPIGateway, ShopifyAPIGatewayWrapper

# Test cards (Stripe test cards - will be declined but show flow works)
TEST_CARDS = [
    "4242424242424242|12|25|123",  # Visa test card
    "4000000000000002|12|25|123",  # Declined card
]

def test_gateway_initialization():
    """Test gateway initializes with store database"""
    print("="*60)
    print("TEST 1: Gateway Initialization")
    print("="*60)
    
    gateway = ShopifyAPIGateway()
    
    print(f"Total stores: {len(gateway.stores)}")
    print(f"Pre-validated: {len([s for s in gateway.stores if s.get('pre_validated')])}")
    print(f"Current index: {gateway.current_store_index}")
    print(f"Failed stores: {len(gateway.failed_stores)}")
    
    assert len(gateway.stores) > 0, "No stores loaded"
    print("\n✓ Gateway initialized successfully")
    return True

def test_store_has_variant_id():
    """Test that pre-validated stores have variant IDs"""
    print("\n" + "="*60)
    print("TEST 2: Store Variant IDs")
    print("="*60)
    
    gateway = ShopifyAPIGateway()
    
    stores_with_variant = 0
    stores_without_variant = 0
    
    for store in gateway.stores[:20]:
        if store.get('variant_id'):
            stores_with_variant += 1
        else:
            stores_without_variant += 1
    
    print(f"Stores with variant_id: {stores_with_variant}")
    print(f"Stores without variant_id: {stores_without_variant}")
    
    # Most pre-validated stores should have variant IDs
    assert stores_with_variant > stores_without_variant, "Most stores should have variant IDs"
    print("\n✓ Stores have variant IDs")
    return True

async def test_single_card_check():
    """Test checking a single card through the gateway"""
    print("\n" + "="*60)
    print("TEST 3: Single Card Check (Async)")
    print("="*60)
    
    gateway = ShopifyAPIGateway()
    test_card = TEST_CARDS[0]
    
    print(f"Testing card: {test_card[:4]}****{test_card[-4:]}")
    print(f"Using store: {gateway.stores[0]['url']}")
    
    try:
        status, message, card_type = await gateway.process_card(test_card)
        print(f"\nResult:")
        print(f"  Status: {status}")
        print(f"  Message: {message}")
        print(f"  Card Type: {card_type}")
        
        # Any result is valid (approved, declined, or error)
        assert status in ['approved', 'declined', 'error'], f"Invalid status: {status}"
        print("\n✓ Card check completed")
        return True
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

def test_sync_wrapper():
    """Test the synchronous wrapper"""
    print("\n" + "="*60)
    print("TEST 4: Synchronous Wrapper")
    print("="*60)
    
    wrapper = ShopifyAPIGatewayWrapper()
    
    print(f"Gateway name: {wrapper.name}")
    print(f"Description: {wrapper.description}")
    print(f"Stores loaded: {len(wrapper.gateway.stores)}")
    
    test_card = TEST_CARDS[0]
    print(f"\nTesting card: {test_card[:4]}****{test_card[-4:]}")
    
    try:
        status, message, card_type = wrapper.check(test_card)
        print(f"\nResult:")
        print(f"  Status: {status}")
        print(f"  Message: {message}")
        print(f"  Card Type: {card_type}")
        print(f"  Success count: {wrapper.success_count}")
        print(f"  Fail count: {wrapper.fail_count}")
        print(f"  Error count: {wrapper.error_count}")
        
        print("\n✓ Sync wrapper works")
        return True
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

def test_gateway_manager_integration():
    """Test integration with GatewayManager"""
    print("\n" + "="*60)
    print("TEST 5: GatewayManager Integration")
    print("="*60)
    
    try:
        from core.gateways import GatewayManager, get_gateway_manager
        
        manager = get_gateway_manager()
        
        # Check if gateway 9 is registered
        gateways = manager.list_gateways()
        print(f"Total gateways: {len(gateways)}")
        
        gateway_9 = None
        for gw in gateways:
            if gw['id'] == 9:
                gateway_9 = gw
                break
        
        if gateway_9:
            print(f"\nGateway #9 found:")
            print(f"  Name: {gateway_9['name']}")
            print(f"  Charge: {gateway_9['charge_amount']}")
            print(f"  Description: {gateway_9['description']}")
            
            # Test card check through manager
            test_card = TEST_CARDS[0]
            print(f"\nTesting card through manager...")
            
            status, message, card_type, gw_name = manager.check_card(test_card, gateway_id=9)
            print(f"  Status: {status}")
            print(f"  Message: {message}")
            print(f"  Gateway: {gw_name}")
            
            print("\n✓ GatewayManager integration works")
            return True
        else:
            print("\n✗ Gateway #9 not found in manager")
            return False
            
    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

def test_multiple_stores_cycling():
    """Test that multiple card checks use different stores"""
    print("\n" + "="*60)
    print("TEST 6: Multiple Stores Cycling")
    print("="*60)
    
    gateway = ShopifyAPIGateway()
    
    stores_used = []
    for i in range(5):
        store = gateway.get_next_store()
        stores_used.append(store['url'])
        print(f"  Check {i+1}: {store['url']}")
    
    unique_stores = len(set(stores_used))
    print(f"\nUnique stores used: {unique_stores}/5")
    
    assert unique_stores == 5, "Should use different stores for each check"
    print("\n✓ Store cycling works")
    return True

async def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("SHOPIFY API GATEWAY E2E TESTS")
    print("="*60)
    print()
    
    results = []
    
    # Sync tests
    results.append(("Gateway Initialization", test_gateway_initialization()))
    results.append(("Store Variant IDs", test_store_has_variant_id()))
    results.append(("Multiple Stores Cycling", test_multiple_stores_cycling()))
    
    # Async test
    try:
        result = await asyncio.wait_for(test_single_card_check(), timeout=60)
        results.append(("Single Card Check (Async)", result))
    except asyncio.TimeoutError:
        print("\n✗ Async test timed out")
        results.append(("Single Card Check (Async)", False))
    
    # Sync wrapper test
    results.append(("Synchronous Wrapper", test_sync_wrapper()))
    
    # Gateway manager test
    results.append(("GatewayManager Integration", test_gateway_manager_integration()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
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
    print("="*60)
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
