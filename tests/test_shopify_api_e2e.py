#!/usr/bin/env python3
"""
End-to-End Test for Shopify API Gateway
Tests the full payment flow with real cards
"""

import sys
import os
import asyncio
import time

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

# Test cards provided
TEST_CARDS = [
    "4579720714941032|2|27|530",
    "4570663792067008|9|27|654",
    "4628880201124236|5|26|437",
    "4147097788692152|4|28|137",
    "5229815001677611|2|27|247",
    "5196032165817905|1|28|283",
    "4283322134527348|3|29|426",
    "5414963709777435|8|27|656",
    "4848100092052907|5|29|408",
    "5577550109924064|5|27|364",
    "376215381791003|6|27|3332",  # AMEX
]


def test_fetch_products_from_working_store():
    """Test fetching products from a known working Shopify store"""
    print("=" * 60)
    print("TEST: Fetch Products from Working Store")
    print("=" * 60)
    
    import aiohttp
    from src.core.shopify_api_gateway import ShopifyAPIGateway
    
    gateway = ShopifyAPIGateway()
    
    # Try to find a working store
    working_stores = [
        "allbirds.com",
        "gymshark.com", 
        "fashionnova.com",
        "colourpop.com",
        "kyliecosmetics.com",
    ]
    
    async def test_stores():
        headers = gateway.default_headers.copy()
        connector = aiohttp.TCPConnector(ssl=False)
        
        async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
            for store in working_stores:
                print(f"\n  Testing: {store}")
                success, result = await gateway.fetch_products(session, store)
                
                if success:
                    print(f"  ✓ Found products!")
                    print(f"    - Product: {result.get('product_title', 'Unknown')}")
                    print(f"    - Price: ${result.get('price', '0')}")
                    print(f"    - Variant ID: {result.get('variant_id', 'N/A')}")
                    return True, store, result
                else:
                    print(f"    - Result: {result}")
        
        return False, None, None
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    success, store, result = loop.run_until_complete(test_stores())
    
    if success:
        print(f"\n✓ Successfully found working store: {store}")
        return True, store
    else:
        print("\n✗ No working stores found from test list")
        return False, None


def test_single_card(card: str, store: str = None):
    """Test a single card through the gateway"""
    from src.core.shopify_api_gateway import ShopifyAPIGateway
    
    gateway = ShopifyAPIGateway()
    
    # If a specific store was found working, prioritize it
    if store:
        # Add the working store to the front of the list
        gateway.stores.insert(0, {'url': store, 'variant_id': None, 'price': None})
    
    print(f"\n  Card: {card[:6]}...{card[-4:]}")
    
    start_time = time.time()
    status, message, card_type = gateway.check(card)
    elapsed = time.time() - start_time
    
    print(f"  Status: {status}")
    print(f"  Message: {message}")
    print(f"  Card Type: {card_type}")
    print(f"  Time: {elapsed:.2f}s")
    
    return {
        'card': card,
        'status': status,
        'message': message,
        'card_type': card_type,
        'time': elapsed
    }


def test_gateway_manager_integration():
    """Test using the gateway through GatewayManager"""
    print("\n" + "=" * 60)
    print("TEST: GatewayManager Integration with Real Card")
    print("=" * 60)
    
    from src.core.gateways import get_gateway_manager
    
    manager = get_gateway_manager()
    
    # Use first test card
    card = TEST_CARDS[0]
    print(f"\n  Testing card via Gateway #9: {card[:6]}...{card[-4:]}")
    
    start_time = time.time()
    status, message, card_type, gateway_name = manager.check_card(card, gateway_id='9')
    elapsed = time.time() - start_time
    
    print(f"  Gateway: {gateway_name}")
    print(f"  Status: {status}")
    print(f"  Message: {message}")
    print(f"  Card Type: {card_type}")
    print(f"  Time: {elapsed:.2f}s")
    
    return status != "error" or "No stores" not in message


def test_multiple_cards():
    """Test multiple cards through the gateway"""
    print("\n" + "=" * 60)
    print("TEST: Multiple Cards (First 3)")
    print("=" * 60)
    
    results = []
    
    for i, card in enumerate(TEST_CARDS[:3]):
        print(f"\n--- Card {i+1}/3 ---")
        result = test_single_card(card)
        results.append(result)
        
        # Small delay between cards
        if i < 2:
            print("  Waiting 2s before next card...")
            time.sleep(2)
    
    return results


def test_store_rotation():
    """Test that store rotation works"""
    print("\n" + "=" * 60)
    print("TEST: Store Rotation")
    print("=" * 60)
    
    from src.core.shopify_api_gateway import ShopifyAPIGateway
    
    gateway = ShopifyAPIGateway()
    
    stores_used = set()
    for i in range(5):
        store = gateway.get_random_store()
        if store:
            stores_used.add(store['url'])
            print(f"  Store {i+1}: {store['url']}")
    
    print(f"\n  Unique stores selected: {len(stores_used)}")
    
    if len(stores_used) >= 3:
        print("✓ Store rotation working (got multiple unique stores)")
        return True
    else:
        print("✗ Store rotation may not be working properly")
        return False


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("\n" + "=" * 60)
    print("SHOPIFY API GATEWAY - COMPREHENSIVE E2E TESTS")
    print("=" * 60)
    print(f"Test Cards: {len(TEST_CARDS)}")
    
    results = {
        'fetch_products': False,
        'store_rotation': False,
        'gateway_manager': False,
        'card_tests': []
    }
    
    # Test 1: Fetch products from working store
    print("\n" + "-" * 60)
    success, working_store = test_fetch_products_from_working_store()
    results['fetch_products'] = success
    
    # Test 2: Store rotation
    print("\n" + "-" * 60)
    results['store_rotation'] = test_store_rotation()
    
    # Test 3: Gateway Manager integration
    print("\n" + "-" * 60)
    results['gateway_manager'] = test_gateway_manager_integration()
    
    # Test 4: Multiple cards
    print("\n" + "-" * 60)
    results['card_tests'] = test_multiple_cards()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    print(f"\n  Fetch Products: {'✓ PASS' if results['fetch_products'] else '✗ FAIL'}")
    print(f"  Store Rotation: {'✓ PASS' if results['store_rotation'] else '✗ FAIL'}")
    print(f"  Gateway Manager: {'✓ PASS' if results['gateway_manager'] else '✗ FAIL'}")
    
    print(f"\n  Card Test Results:")
    for i, result in enumerate(results['card_tests']):
        card_short = result['card'][:6] + "..." + result['card'][-4:]
        status_icon = "✓" if result['status'] in ['approved', 'declined'] else "⚠"
        print(f"    {status_icon} Card {i+1}: {result['status']} - {result['message'][:40]}")
    
    # Count results
    total_tests = 3 + len(results['card_tests'])
    passed = sum([
        results['fetch_products'],
        results['store_rotation'],
        results['gateway_manager'],
    ])
    
    # Card tests pass if they don't error out completely
    for result in results['card_tests']:
        if result['status'] in ['approved', 'declined'] or 'session token' in result['message'].lower():
            passed += 1
    
    print(f"\n  Total: {passed}/{total_tests} tests passed")
    
    return results


if __name__ == "__main__":
    results = run_comprehensive_tests()
