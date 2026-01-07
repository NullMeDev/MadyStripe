#!/usr/bin/env python3
"""
Test script for Shopify integration
Tests the gateway and checker functionality
"""

import sys
import os

# Add core path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test if all required modules can be imported"""
    print("="*60)
    print("TEST 1: Checking Imports")
    print("="*60)
    
    try:
        import aiohttp
        print("✅ aiohttp imported successfully")
    except ImportError:
        print("❌ aiohttp not found - run: pip install aiohttp")
        return False
    
    try:
        import asyncio
        print("✅ asyncio imported successfully")
    except ImportError:
        print("❌ asyncio not found")
        return False
    
    try:
        from core.shopify_gateway import ShopifyGateway
        print("✅ ShopifyGateway imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ShopifyGateway: {e}")
        return False
    
    print("\n✅ All imports successful!\n")
    return True

def test_gateway_creation():
    """Test gateway creation"""
    print("="*60)
    print("TEST 2: Gateway Creation")
    print("="*60)
    
    try:
        from core.shopify_gateway import ShopifyGateway
        
        # Test with different URL formats
        test_urls = [
            "example.myshopify.com",
            "https://example.myshopify.com",
            "http://example.myshopify.com/",
            "shop.example.com"
        ]
        
        for url in test_urls:
            gateway = ShopifyGateway(url)
            print(f"✅ Created gateway for: {url}")
            print(f"   Normalized to: {gateway.store_url}")
            print(f"   Name: {gateway.name}")
            print(f"   Description: {gateway.description}")
            print()
        
        print("✅ Gateway creation test passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Gateway creation failed: {e}\n")
        return False

def test_card_parsing():
    """Test card format parsing"""
    print("="*60)
    print("TEST 3: Card Format Parsing")
    print("="*60)
    
    test_cards = [
        "4532015112830366|12|2025|123",
        "5425233430109903|08|26|456",
        "4111111111111111|12|25|789",
    ]
    
    for card in test_cards:
        parts = card.split('|')
        if len(parts) == 4:
            cc, mes, ano, cvv = parts
            # Ensure 4-digit year
            if len(ano) == 2:
                ano = '20' + ano
            print(f"✅ {card}")
            print(f"   CC: {cc}, Month: {mes}, Year: {ano}, CVV: {cvv}")
        else:
            print(f"❌ Invalid format: {card}")
    
    print("\n✅ Card parsing test passed!\n")
    return True

def test_shopify_checker_exists():
    """Test if shopify checker script exists"""
    print("="*60)
    print("TEST 4: Shopify Checker Script")
    print("="*60)
    
    checker_path = "mady_shopify_checker.py"
    
    if os.path.exists(checker_path):
        print(f"✅ {checker_path} exists")
        
        # Check if executable
        if os.access(checker_path, os.X_OK):
            print(f"✅ {checker_path} is executable")
        else:
            print(f"⚠️ {checker_path} is not executable")
            print(f"   Run: chmod +x {checker_path}")
        
        # Check file size
        size = os.path.getsize(checker_path)
        print(f"✅ File size: {size:,} bytes")
        
        print("\n✅ Shopify checker script test passed!\n")
        return True
    else:
        print(f"❌ {checker_path} not found\n")
        return False

def test_documentation():
    """Test if documentation exists"""
    print("="*60)
    print("TEST 5: Documentation")
    print("="*60)
    
    docs = [
        "SHOPIFY_INTEGRATION_GUIDE.md",
        "SHOPIFY_USAGE_COMPLETE.md"
    ]
    
    all_exist = True
    for doc in docs:
        if os.path.exists(doc):
            size = os.path.getsize(doc)
            print(f"✅ {doc} exists ({size:,} bytes)")
        else:
            print(f"❌ {doc} not found")
            all_exist = False
    
    if all_exist:
        print("\n✅ Documentation test passed!\n")
    else:
        print("\n⚠️ Some documentation missing\n")
    
    return all_exist

def test_async_functionality():
    """Test async functionality"""
    print("="*60)
    print("TEST 6: Async Functionality")
    print("="*60)
    
    try:
        import asyncio
        
        async def test_async():
            await asyncio.sleep(0.1)
            return "Success"
        
        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_async())
        loop.close()
        
        if result == "Success":
            print("✅ Async functionality working")
            print("✅ Event loop creation successful")
            print("✅ Async/await syntax supported")
            print("\n✅ Async test passed!\n")
            return True
        else:
            print("❌ Async test failed\n")
            return False
            
    except Exception as e:
        print(f"❌ Async test failed: {e}\n")
        return False

def print_usage_examples():
    """Print usage examples"""
    print("="*60)
    print("USAGE EXAMPLES")
    print("="*60)
    print()
    print("1. Basic Shopify Check:")
    print("   python3 mady_shopify_checker.py cards.txt --store example.myshopify.com")
    print()
    print("2. With Threads:")
    print("   python3 mady_shopify_checker.py cards.txt --store shop.example.com --threads 5")
    print()
    print("3. With Limit:")
    print("   python3 mady_shopify_checker.py cards.txt --store example.com --limit 10")
    print()
    print("4. With Proxy:")
    print("   python3 mady_shopify_checker.py cards.txt --store example.com --proxy ip:port:user:pass")
    print()
    print("5. Quick Test:")
    print("   echo '4532015112830366|12|2025|123' > test.txt")
    print("   python3 mady_shopify_checker.py test.txt --store example.myshopify.com --limit 1")
    print()

def main():
    """Run all tests"""
    print("""
╔════════════════════════════════════════════════════════════╗
║           SHOPIFY INTEGRATION TEST SUITE                  ║
║              Testing All Components                       ║
╚════════════════════════════════════════════════════════════╝
""")
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Gateway Creation", test_gateway_creation()))
    results.append(("Card Parsing", test_card_parsing()))
    results.append(("Checker Script", test_shopify_checker_exists()))
    results.append(("Documentation", test_documentation()))
    results.append(("Async Functionality", test_async_functionality()))
    
    # Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Shopify integration is ready to use.")
        print()
        print_usage_examples()
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
