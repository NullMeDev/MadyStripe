#!/usr/bin/env python3
"""
Debug Shopify stores to see why they're failing
"""

import requests
import sys

# Test stores from penny gate
test_stores = [
    "sifrinerias.myshopify.com",
    "ratterriers.myshopify.com",
    "turningpointe.myshopify.com",
    "liddelton.myshopify.com",
    "isimple.myshopify.com"
]

def test_store(store_url):
    """Test if a store is accessible"""
    print(f"\n{'='*70}")
    print(f"Testing: {store_url}")
    print(f"{'='*70}")
    
    try:
        # Try to access the store
        url = f"https://{store_url}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"1. Accessing {url}...")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Length: {len(response.text)}")
        
        # Check if it's a valid Shopify store
        if 'shopify' in response.text.lower() or 'cdn.shopify.com' in response.text:
            print(f"   ✅ Valid Shopify store")
        else:
            print(f"   ❌ Not a Shopify store or blocked")
            
        # Try to find session token
        if 'authenticity_token' in response.text:
            print(f"   ✅ Has authenticity_token")
        else:
            print(f"   ⚠️ No authenticity_token found")
            
        # Check for products API
        products_url = f"https://{store_url}/products.json"
        print(f"\n2. Checking products API...")
        prod_response = requests.get(products_url, headers=headers, timeout=10)
        print(f"   Status: {prod_response.status_code}")
        
        if prod_response.status_code == 200:
            products = prod_response.json().get('products', [])
            print(f"   ✅ Found {len(products)} products")
            if products:
                cheapest = min(products, key=lambda p: float(p['variants'][0]['price']) if p.get('variants') else 999999)
                print(f"   Cheapest: ${cheapest['variants'][0]['price']} - {cheapest['title']}")
        else:
            print(f"   ❌ Products API failed")
            
        return True
        
    except requests.exceptions.Timeout:
        print(f"   ❌ TIMEOUT - Store not responding")
        return False
    except requests.exceptions.ConnectionError:
        print(f"   ❌ CONNECTION ERROR - Cannot reach store")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)[:100]}")
        return False

def main():
    print("🔍 Debugging Shopify Stores")
    print("="*70)
    
    working = []
    failing = []
    
    for store in test_stores:
        if test_store(store):
            working.append(store)
        else:
            failing.append(store)
    
    print(f"\n\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}")
    print(f"✅ Working: {len(working)}/{len(test_stores)}")
    print(f"❌ Failing: {len(failing)}/{len(test_stores)}")
    
    if working:
        print(f"\n✅ Working stores:")
        for store in working:
            print(f"   - {store}")
    
    if failing:
        print(f"\n❌ Failing stores:")
        for store in failing:
            print(f"   - {store}")

if __name__ == '__main__':
    main()
