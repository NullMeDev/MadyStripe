#!/usr/bin/env python3
"""
Simple test script for the new gateways
Tests core functionality without bot registration
"""

import asyncio
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'AutoshBotSRC', 'AutoshBotSRC'))

# Test card
TEST_CARD = "4242424242424242|12|2028|123"


async def test_stripe_payment_method():
    """Test Stripe payment method creation"""
    print("\n" + "="*60)
    print("TEST 1: Stripe Payment Method Creation")
    print("="*60)
    
    try:
        import aiohttp
        from gateways.autoStripe import create_payment_method, STRIPE_KEY
        
        cc, mes, ano, cvv = TEST_CARD.split("|")
        
        print(f"Card: {cc[:6]}...{cc[-4:]}")
        print(f"Stripe Key: {STRIPE_KEY[:20]}...")
        
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            pm_id, error = await create_payment_method(session, cc, mes, ano, cvv)
            
            if pm_id:
                print(f"✓ Payment Method Created: {pm_id[:20]}...")
                return True, pm_id
            else:
                print(f"✗ Error: {error}")
                return False, error
                
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


async def test_shopify_product_fetch():
    """Test Shopify product fetching"""
    print("\n" + "="*60)
    print("TEST 2: Shopify Product Fetching")
    print("="*60)
    
    try:
        from gateways.autoShopify_fixed import fetchProducts
        
        stores = [
            "shopnicekicks.com",
            "kith.com",
            "culturekings.com.au",
        ]
        
        for store in stores:
            print(f"\nTrying: {store}")
            result = await fetchProducts(None, store, timeout=15, retries=2)
            
            if isinstance(result, dict):
                print(f"  ✓ Found: {result.get('title', 'Unknown')[:40]}")
                print(f"    Price: ${result.get('price', '?')}")
                print(f"    Variant: {result.get('variant_id', '?')}")
                return True, result
            else:
                error = result[1] if isinstance(result, tuple) else str(result)
                print(f"  ✗ Failed: {error}")
        
        return False, "All stores failed"
        
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


async def test_stripe_full_flow():
    """Test full Stripe gateway flow"""
    print("\n" + "="*60)
    print("TEST 3: Stripe Full Flow (process_card)")
    print("="*60)
    
    try:
        from gateways.autoStripe import process_card
        
        cc, mes, ano, cvv = TEST_CARD.split("|")
        
        print(f"Processing card: {cc[:6]}...{cc[-4:]}")
        
        result = await process_card(cc, mes, ano, cvv)
        
        print(f"Result: {result}")
        
        if isinstance(result, tuple) and len(result) >= 2:
            success = result[0]
            message = result[1]
            gateway = result[2] if len(result) > 2 else "Stripe"
            
            print(f"Success: {success}")
            print(f"Message: {message}")
            print(f"Gateway: {gateway}")
            
            # For test card, we expect a decline or error (not a real card)
            return True, message
        
        return False, "Invalid result"
        
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


async def test_unified_gateway():
    """Test unified gateway"""
    print("\n" + "="*60)
    print("TEST 4: Unified Gateway (auto-select)")
    print("="*60)
    
    try:
        from gateways.autoUnified import process_card
        
        cc, mes, ano, cvv = TEST_CARD.split("|")
        
        print(f"Processing card: {cc[:6]}...{cc[-4:]}")
        print("Mode: No site/proxy (should use Stripe)")
        
        result = await process_card(cc, mes, ano, cvv)
        
        print(f"Result: {result}")
        
        if isinstance(result, tuple) and len(result) >= 2:
            success = result[0]
            message = result[1]
            gateway = result[2] if len(result) > 2 else "Unified"
            
            print(f"Success: {success}")
            print(f"Message: {message}")
            print(f"Gateway: {gateway}")
            
            return True, message
        
        return False, "Invalid result"
        
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


async def test_cc_foundation_direct():
    """Test CC Foundation gateway directly (sync version)"""
    print("\n" + "="*60)
    print("TEST 5: CC Foundation Direct (core/cc_foundation_gateway.py)")
    print("="*60)
    
    try:
        # Add core to path
        sys.path.insert(0, os.path.dirname(__file__))
        from core.cc_foundation_gateway import CCFoundationGateway
        
        gateway = CCFoundationGateway(mode="auth")  # Auth mode - no charge
        
        print(f"Gateway: {gateway.name}")
        print(f"Mode: {gateway.mode}")
        
        status, message, card_type = gateway.check(TEST_CARD)
        
        print(f"Status: {status}")
        print(f"Message: {message}")
        print(f"Card Type: {card_type}")
        
        return status == "approved" or "live" in message.lower(), message
        
    except Exception as e:
        print(f"✗ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


async def main():
    """Run all tests"""
    print("="*60)
    print("GATEWAY INTEGRATION TESTS")
    print("="*60)
    print(f"Test Card: {TEST_CARD}")
    
    results = {}
    
    # Test 1: Stripe Payment Method
    success, msg = await test_stripe_payment_method()
    results['Stripe PM'] = (success, msg[:50] if isinstance(msg, str) else str(msg)[:50])
    
    # Test 2: Shopify Products
    success, msg = await test_shopify_product_fetch()
    results['Shopify Products'] = (success, str(msg)[:50])
    
    # Test 3: Stripe Full Flow
    success, msg = await test_stripe_full_flow()
    results['Stripe Flow'] = (success, msg[:50] if isinstance(msg, str) else str(msg)[:50])
    
    # Test 4: Unified Gateway
    success, msg = await test_unified_gateway()
    results['Unified'] = (success, msg[:50] if isinstance(msg, str) else str(msg)[:50])
    
    # Test 5: CC Foundation Direct
    success, msg = await test_cc_foundation_direct()
    results['CC Foundation'] = (success, msg[:50] if isinstance(msg, str) else str(msg)[:50])
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, (success, msg) in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        if success:
            passed += 1
        else:
            failed += 1
        print(f"{test_name}: {status} - {msg}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
