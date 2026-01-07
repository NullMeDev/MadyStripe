#!/usr/bin/env python3
"""
Test Shopify Cart API to debug "Failed to add to cart" error
Tests each step of the cart/checkout process
"""

import requests
import json
import re

def test_store_cart_api(store_url):
    """Test cart API for a specific store"""
    print(f"\n{'='*70}")
    print(f"Testing: {store_url}")
    print(f"{'='*70}")
    
    session = requests.Session()
    base_url = f"https://{store_url}"
    
    # Step 1: Get products
    print("\n1️⃣ Fetching products...")
    try:
        products_response = session.get(f"{base_url}/products.json", timeout=10)
        print(f"   Status: {products_response.status_code}")
        
        if products_response.status_code == 200:
            products = products_response.json().get('products', [])
            print(f"   ✅ Found {len(products)} products")
            
            if products and products[0].get('variants'):
                variant_id = products[0]['variants'][0]['id']
                product_title = products[0]['title']
                price = products[0]['variants'][0]['price']
                print(f"   Using: {product_title} (${price})")
                print(f"   Variant ID: {variant_id}")
            else:
                print(f"   ❌ No variants found")
                return False
        else:
            print(f"   ❌ Failed to fetch products")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Step 2: Test cart/add.js (AJAX method)
    print("\n2️⃣ Testing cart/add.js (AJAX)...")
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        }
        
        data = {
            'items': [{
                'id': variant_id,
                'quantity': 1
            }]
        }
        
        cart_response = session.post(
            f"{base_url}/cart/add.js",
            json=data,
            headers=headers,
            timeout=10
        )
        
        print(f"   Status: {cart_response.status_code}")
        print(f"   Response: {cart_response.text[:200]}")
        
        if cart_response.status_code == 200:
            print(f"   ✅ Cart add successful!")
            return True
        else:
            print(f"   ❌ Cart add failed")
            
            # Try alternative method
            print("\n3️⃣ Trying alternative: /cart/add (form POST)...")
            form_data = {
                'id': variant_id,
                'quantity': 1
            }
            
            alt_response = session.post(
                f"{base_url}/cart/add",
                data=form_data,
                timeout=10,
                allow_redirects=False
            )
            
            print(f"   Status: {alt_response.status_code}")
            if alt_response.status_code in [200, 302, 303]:
                print(f"   ✅ Alternative method works!")
                return True
            else:
                print(f"   ❌ Alternative also failed")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    return False

def main():
    print("🔍 Shopify Cart API Debugger")
    print("="*70)
    
    # Test stores from penny gate
    test_stores = [
        "ratterriers.myshopify.com",
        "turningpointe.myshopify.com",
        "liddelton.myshopify.com",
        "isimple.myshopify.com",
        "sifrinerias.myshopify.com"
    ]
    
    results = {}
    
    for store in test_stores:
        success = test_store_cart_api(store)
        results[store] = success
    
    # Summary
    print(f"\n\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}")
    
    working = [s for s, success in results.items() if success]
    failing = [s for s, success in results.items() if not success]
    
    print(f"\n✅ Working: {len(working)}/{len(test_stores)}")
    for store in working:
        print(f"   - {store}")
    
    print(f"\n❌ Failing: {len(failing)}/{len(test_stores)}")
    for store in failing:
        print(f"   - {store}")
    
    if working:
        print(f"\n💡 Recommendation: Use these working stores in the gateway")
    else:
        print(f"\n⚠️ All stores failing - need to investigate Shopify API changes")

if __name__ == '__main__':
    main()
