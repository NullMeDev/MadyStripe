#!/usr/bin/env python3
"""
Test script for AutoshBotSRC gateways
Tests the fixed Shopify, new Stripe, and Unified gateways
"""

import asyncio
import sys
import os

# Add AutoshBotSRC to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'AutoshBotSRC', 'AutoshBotSRC'))

# Test card (use a test card for validation)
TEST_CARD = "4242424242424242|12|2028|123"


async def test_stripe_gateway():
    """Test the Stripe gateway"""
    print("\n" + "="*60)
    print("Testing Stripe Gateway (CC Foundation)")
    print("="*60)
    
    try:
        from gateways.autoStripe import process_card, create_payment_method
        
        cc, mes, ano, cvv = TEST_CARD.split("|")
        
        print(f"Card: {cc[:6]}...{cc[-4:]}")
        print(f"Expiry: {mes}/{ano}")
        
        result = await process_card(cc, mes, ano, cvv)
        
        print(f"\nResult: {result}")
        
        if isinstance(result, tuple):
            success = result[0]
            message = result[1] if len(result) > 1 else "Unknown"
            gateway = result[2] if len(result) > 2 else "Stripe"
            
            print(f"Success: {success}")
            print(f"Message: {message}")
            print(f"Gateway: {gateway}")
            
            return success, message
        
        return False, "Invalid result format"
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Make sure you're running from the correct directory")
        return False, str(e)
    except Exception as e:
        print(f"Error: {e}")
        return False, str(e)


async def test_shopify_gateway():
    """Test the fixed Shopify gateway"""
    print("\n" + "="*60)
    print("Testing Shopify Gateway (Fixed)")
    print("="*60)
    
    try:
        from gateways.autoShopify_fixed import process_card, fetchProducts
        
        # Test product fetching first
        print("\nTesting product fetching...")
        
        test_stores = [
            "wiredministries.com",
            "shopnicekicks.com",
            "kith.com",
        ]
        
        for store in test_stores:
            print(f"\nFetching products from: {store}")
            result = await fetchProducts(None, store, timeout=10, retries=1)
            
            if isinstance(result, dict):
                print(f"  ✓ Found product: {result.get('title', 'Unknown')}")
                print(f"    Price: ${result.get('price', '?')}")
                print(f"    Variant ID: {result.get('variant_id', '?')}")
                break
            else:
                print(f"  ✗ Failed: {result[1] if isinstance(result, tuple) else result}")
        
        # Test card processing (without proxy - will likely fail but tests the flow)
        print("\n\nTesting card processing (no proxy)...")
        cc, mes, ano, cvv = TEST_CARD.split("|")
        
        # Create a mock site object
        class MockSite:
            def __init__(self, url, variant_id=""):
                self.url = url
                self.variant_id = variant_id
        
        site = MockSite("wiredministries.com")
        
        result = await process_card(cc, mes, ano, cvv, site=site, proxies=None)
        
        print(f"\nResult: {result}")
        
        if isinstance(result, tuple):
            success = result[0]
            message = result[1] if len(result) > 1 else "Unknown"
            
            print(f"Success: {success}")
            print(f"Message: {message}")
            
            return success, message
        
        return False, "Invalid result format"
        
    except ImportError as e:
        print(f"Import Error: {e}")
        return False, str(e)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


async def test_unified_gateway():
    """Test the unified gateway"""
    print("\n" + "="*60)
    print("Testing Unified Gateway (Auto-select)")
    print("="*60)
    
    try:
        from gateways.autoUnified import process_card
        
        cc, mes, ano, cvv = TEST_CARD.split("|")
        
        print(f"Card: {cc[:6]}...{cc[-4:]}")
        print("Testing without site/proxy (should use Stripe)...")
        
        result = await process_card(cc, mes, ano, cvv)
        
        print(f"\nResult: {result}")
        
        if isinstance(result, tuple):
            success = result[0]
            message = result[1] if len(result) > 1 else "Unknown"
            gateway = result[2] if len(result) > 2 else "Unified"
            
            print(f"Success: {success}")
            print(f"Message: {message}")
            print(f"Gateway: {gateway}")
            
            return success, message
        
        return False, "Invalid result format"
        
    except ImportError as e:
        print(f"Import Error: {e}")
        return False, str(e)
    except Exception as e:
        print(f"Error: {e}")
        return False, str(e)


async def test_gateway_registration():
    """Test that gateways can be registered"""
    print("\n" + "="*60)
    print("Testing Gateway Registration")
    print("="*60)
    
    try:
        # Mock bot object
        class MockBot:
            def __init__(self):
                self.commands = {}
            
            def register_message_handler(self, handler, **kwargs):
                cmd = kwargs.get('commands', ['unknown'])[0]
                self.commands[cmd] = handler
                print(f"  Registered command: /{cmd}")
        
        mock_bot = MockBot()
        
        # Test Stripe registration
        from gateways.autoStripe import register_stripe_gateway, register_cc_gateway
        await register_stripe_gateway(mock_bot)
        await register_cc_gateway(mock_bot)
        
        # Test Shopify registration
        from gateways.autoShopify_fixed import register_shopify_gateway
        await register_shopify_gateway(mock_bot)
        
        # Test Unified registration
        from gateways.autoUnified import register_unified_gateway
        await register_unified_gateway(mock_bot)
        
        print(f"\nRegistered {len(mock_bot.commands)} commands")
        
        return True, f"Registered {len(mock_bot.commands)} commands"
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


async def main():
    """Run all tests"""
    print("="*60)
    print("AutoshBotSRC Gateway Tests")
    print("="*60)
    
    results = {}
    
    # Test 1: Gateway Registration
    success, msg = await test_gateway_registration()
    results['Registration'] = (success, msg)
    
    # Test 2: Stripe Gateway
    success, msg = await test_stripe_gateway()
    results['Stripe'] = (success, msg)
    
    # Test 3: Shopify Gateway
    success, msg = await test_shopify_gateway()
    results['Shopify'] = (success, msg)
    
    # Test 4: Unified Gateway
    success, msg = await test_unified_gateway()
    results['Unified'] = (success, msg)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, (success, msg) in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{test_name}: {status} - {msg[:50]}")
    
    print("\n" + "="*60)
    
    # Return overall success
    return all(s for s, _ in results.values())


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
