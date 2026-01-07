#!/usr/bin/env python3
"""
Quick verification test for AutoshBotSRC integration fixes
"""
import sys
import os
sys.path.insert(0, 'AutoshBotSRC/AutoshBotSRC')

def test_imports():
    """Test basic imports"""
    print("🔍 Testing AutoshBotSRC Integration...")

    # Test 1: Gateway imports
    print("\n1. Testing gateway imports...")
    try:
        from gateways.autoShopify_fixed import fetchProducts
        print("   ✅ Shopify gateway import successful")
    except Exception as e:
        print(f"   ❌ Shopify import failed: {e}")

    try:
        from gateways.autoStripe import STRIPE_KEY
        print(f"   ✅ Stripe gateway import successful (key: {STRIPE_KEY[:20]}...)")
    except Exception as e:
        print(f"   ❌ Stripe import failed: {e}")

    try:
        from gateways.autoUnified import process_card
        print("   ✅ Unified gateway import successful")
    except Exception as e:
        print(f"   ❌ Unified import failed: {e}")

    # Test 2: Enhanced Shopify import
    print("\n2. Testing enhanced Shopify...")
    try:
        from commands.shopify_enhanced import register_resource_commands
        print("   ✅ Enhanced Shopify commands import successful")
    except Exception as e:
        print(f"   ❌ Enhanced Shopify import failed: {e}")

    # Test 3: Original Shopify (check for bugs)
    print("\n3. Testing original Shopify...")
    try:
        from commands.shopify import fetchProducts as original_fetchProducts
        print("   ✅ Original Shopify import successful")
        # Test the function signature to check for variant bug
        import inspect
        sig = inspect.signature(original_fetchProducts)
        print(f"   ✅ Function signature: {sig}")
    except Exception as e:
        print(f"   ❌ Original Shopify import failed: {e}")

    print("\n🎯 Quick verification complete!")

if __name__ == "__main__":
    test_imports()
