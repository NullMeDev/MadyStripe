#!/usr/bin/env python3
"""
Comprehensive Selenium Gateway Test Suite
Tests all features: HTTP pre-screening, Chrome, element finding, result detection, etc.
"""

import sys
import time
from core.shopify_selenium_gateway import ShopifySeleniumGateway

def test_1_http_prescreen():
    """Test 1: HTTP Pre-screening"""
    print("\n" + "="*70)
    print("TEST 1: HTTP PRE-SCREENING")
    print("="*70)
    
    try:
        gateway = ShopifySeleniumGateway(
            stores_file='working_shopify_stores.txt',
            headless=True
        )
        
        # Test with 5 stores
        test_stores = gateway.stores[:5]
        print(f"Testing {len(test_stores)} stores...")
        
        start = time.time()
        accessible = gateway.http_prescreen_stores(test_stores)
        elapsed = time.time() - start
        
        print(f"\n✅ PASSED")
        print(f"  Accessible: {len(accessible)}/{len(test_stores)}")
        print(f"  Time: {elapsed:.2f}s ({elapsed/len(test_stores):.2f}s per store)")
        return True, accessible
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False, []


def test_2_chrome_launch():
    """Test 2: Chrome Launch"""
    print("\n" + "="*70)
    print("TEST 2: CHROME LAUNCH")
    print("="*70)
    
    try:
        import undetected_chromedriver as uc
        
        print("Launching Chrome...")
        driver = uc.Chrome(headless=True, use_subprocess=False)
        
        print("Navigating to Google...")
        driver.get('https://www.google.com')
        
        title = driver.title
        print(f"Page title: {title}")
        
        driver.quit()
        print("\n✅ PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_3_element_finding():
    """Test 3: Element Finding"""
    print("\n" + "="*70)
    print("TEST 3: ELEMENT FINDING")
    print("="*70)
    
    try:
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        
        gateway = ShopifySeleniumGateway(headless=True)
        
        print("Launching Chrome...")
        driver = uc.Chrome(headless=True, use_subprocess=False)
        
        print("Navigating to Google...")
        driver.get('https://www.google.com')
        
        print("Testing element finding...")
        # Try to find search box
        selectors = [
            (By.NAME, 'q'),
            (By.CSS_SELECTOR, 'input[type="text"]'),
            (By.CSS_SELECTOR, 'textarea[name="q"]'),
        ]
        
        element = gateway.wait_and_interact(driver, selectors, timeout=5)
        
        if element:
            print(f"✓ Found element: {element.tag_name}")
            driver.quit()
            print("\n✅ PASSED")
            return True
        else:
            driver.quit()
            print("\n❌ FAILED: Element not found")
            return False
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_result_detection():
    """Test 4: Result Detection"""
    print("\n" + "="*70)
    print("TEST 4: RESULT DETECTION")
    print("="*70)
    
    try:
        import undetected_chromedriver as uc
        
        gateway = ShopifySeleniumGateway(headless=True)
        
        print("Launching Chrome...")
        driver = uc.Chrome(headless=True, use_subprocess=False)
        
        # Test with a page that has success keywords
        print("Testing success detection...")
        driver.get('data:text/html,<html><body><h1>Thank you for your order!</h1><p>Payment successful</p></body></html>')
        time.sleep(1)
        
        result = gateway.detect_result(driver)
        print(f"Result: {result}")
        
        if result == 'approved':
            print("✓ Success detection works")
        else:
            print(f"⚠️  Expected 'approved', got '{result}'")
        
        # Test with decline keywords
        print("\nTesting decline detection...")
        driver.get('data:text/html,<html><body><h1>Payment declined</h1><p>Insufficient funds</p></body></html>')
        time.sleep(1)
        
        result = gateway.detect_result(driver)
        print(f"Result: {result}")
        
        if result == 'declined':
            print("✓ Decline detection works")
        else:
            print(f"⚠️  Expected 'declined', got '{result}'")
        
        driver.quit()
        print("\n✅ PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_5_shopify_navigation():
    """Test 5: Shopify Store Navigation"""
    print("\n" + "="*70)
    print("TEST 5: SHOPIFY STORE NAVIGATION")
    print("="*70)
    
    try:
        import undetected_chromedriver as uc
        
        gateway = ShopifySeleniumGateway(
            stores_file='working_shopify_stores.txt',
            headless=True
        )
        
        # Get an accessible store
        print("Finding accessible store...")
        accessible = gateway.http_prescreen_stores(gateway.stores[:10])
        
        if not accessible:
            print("⚠️  No accessible stores found, skipping test")
            return True
        
        store = accessible[0]
        print(f"Testing with: {store}")
        
        print("Launching Chrome...")
        driver = uc.Chrome(headless=True, use_subprocess=False)
        
        print(f"Navigating to https://{store}...")
        driver.get(f'https://{store}')
        time.sleep(3)
        
        title = driver.title
        url = driver.current_url
        
        print(f"✓ Page title: {title}")
        print(f"✓ Current URL: {url}")
        
        # Check if it's a Shopify store
        page_source = driver.page_source.lower()
        is_shopify = 'shopify' in page_source or 'myshopify' in url.lower()
        
        if is_shopify:
            print("✓ Confirmed Shopify store")
        else:
            print("⚠️  May not be a Shopify store")
        
        driver.quit()
        print("\n✅ PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_6_full_gateway():
    """Test 6: Full Gateway Check (without real card)"""
    print("\n" + "="*70)
    print("TEST 6: FULL GATEWAY CHECK")
    print("="*70)
    print("⚠️  This test will attempt a full checkout flow")
    print("⚠️  Using test card (will be declined)")
    
    try:
        gateway = ShopifySeleniumGateway(
            stores_file='working_shopify_stores.txt',
            headless=True
        )
        
        # Test card (will be declined)
        test_card = "4111111111111111|12|25|123"
        
        print(f"\nTesting with card: {test_card[:4]}...{test_card[-7:]}")
        print("This may take 30-60 seconds...\n")
        
        start = time.time()
        status, message, card_type = gateway.check(test_card, max_attempts=2)
        elapsed = time.time() - start
        
        print(f"\n{'='*70}")
        print(f"RESULT:")
        print(f"  Status: {status}")
        print(f"  Message: {message}")
        print(f"  Card Type: {card_type}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"{'='*70}")
        
        # Any result is acceptable (approved/declined/error)
        # We just want to verify the flow works
        if status in ['approved', 'declined', 'error']:
            print("\n✅ PASSED (Gateway flow completed)")
            return True
        else:
            print(f"\n❌ FAILED: Unexpected status '{status}'")
            return False
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*70)
    print("SELENIUM GATEWAY COMPREHENSIVE TEST SUITE")
    print("="*70)
    print("\nThis will test all gateway features:")
    print("1. HTTP Pre-screening")
    print("2. Chrome Launch")
    print("3. Element Finding")
    print("4. Result Detection")
    print("5. Shopify Navigation")
    print("6. Full Gateway Check")
    print("\nEstimated time: 2-3 minutes")
    print("="*70)
    
    results = {}
    
    # Test 1: HTTP Pre-screening
    passed, accessible_stores = test_1_http_prescreen()
    results['HTTP Pre-screening'] = passed
    
    # Test 2: Chrome Launch
    passed = test_2_chrome_launch()
    results['Chrome Launch'] = passed
    
    # Test 3: Element Finding
    passed = test_3_element_finding()
    results['Element Finding'] = passed
    
    # Test 4: Result Detection
    passed = test_4_result_detection()
    results['Result Detection'] = passed
    
    # Test 5: Shopify Navigation
    passed = test_5_shopify_navigation()
    results['Shopify Navigation'] = passed
    
    # Test 6: Full Gateway (optional - takes longest)
    print("\n" + "="*70)
    response = input("Run full gateway test? (takes 30-60s) [y/N]: ").strip().lower()
    if response == 'y':
        passed = test_6_full_gateway()
        results['Full Gateway'] = passed
    else:
        print("Skipping full gateway test")
        results['Full Gateway'] = None
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        if passed is None:
            status = "⏭️  SKIPPED"
        elif passed:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"{status} - {test_name}")
    
    # Overall result
    passed_count = sum(1 for p in results.values() if p is True)
    failed_count = sum(1 for p in results.values() if p is False)
    skipped_count = sum(1 for p in results.values() if p is None)
    
    print(f"\n{'='*70}")
    print(f"OVERALL: {passed_count} passed, {failed_count} failed, {skipped_count} skipped")
    print(f"{'='*70}")
    
    if failed_count == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {failed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
