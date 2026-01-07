#!/usr/bin/env python3
"""
Simple AutoshBotSRC Integration Test
"""

import asyncio
import sys
import time

# Add AutoshBotSRC to path
sys.path.insert(0, 'AutoshBotSRC/AutoshBotSRC')

from gateways.autoStripe import process_card as stripe_process
from gateways.autoShopify_fixed import process_card as shopify_process

async def test_stripe():
    """Test Stripe with one card"""
    print("Testing Stripe Gateway...")
    try:
        success, message, gateway = await stripe_process("4111111111111111", "12", "25", "123", None)
        print(f"Result: {'SUCCESS' if success else 'FAILED'} - {message}")
        return success
    except Exception as e:
        print(f"Error: {e}")
        return False

async def test_shopify():
    """Test Shopify with one store and card"""
    print("Testing Shopify Gateway...")
    try:
        success, message, gateway = await shopify_process("4111111111111111", "12", "25", "123", "wiredministries.com", None)
        print(f"Result: {'SUCCESS' if success else 'FAILED'} - {message}")
        return success
    except Exception as e:
        print(f"Error: {e}")
        return False

async def main():
    print("🚀 Starting Simple AutoshBotSRC Integration Test")

    stripe_ok = await test_stripe()
    shopify_ok = await test_shopify()

    print("
📊 RESULTS:"    print(f"Stripe: {'✅ PASS' if stripe_ok else '❌ FAIL'}")
    print(f"Shopify: {'✅ PASS' if shopify_ok else '❌ FAIL'}")

    if stripe_ok and shopify_ok:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")

if __name__ == "__main__":
    asyncio.run(main())
