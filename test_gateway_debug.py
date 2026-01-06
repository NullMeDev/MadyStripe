#!/usr/bin/env python3
"""
Debug test for Shopify gateway - with detailed logging
"""

import requests
import json

def test_products_api():
    """Test if we can fetch products"""
    print("="*70)
    print("STEP 1: Testing Products API")
    print("="*70)
    
    store = "ratterriers.myshopify.com"
    url = f"https://{store}/products.json"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Length: {len(response.text)} bytes")
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            print(f"✅ Found {len(products)} products")
            
            if products:
                product = products[0]
                print(f"\nFirst Product:")
                print(f"  Title: {product.get('title')}")
                print(f"  ID: {product.get('id')}")
                
                if product.get('variants'):
                    variant = product['variants'][0]
                    print(f"\nFirst Variant:")
                    print(f"  ID: {variant.get('id')}")
                    print(f"  Price: ${variant.get('price')}")
                    print(f"  Available: {variant.get('available')}")
                    
                    return variant.get('id'), variant.get('price')
        else:
            print(f"❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None, None

def test_cart_add(variant_id):
    """Test adding to cart"""
    print(f"\n{'='*70}")
    print("STEP 2: Testing Cart Add")
    print(f"{'='*70}")
    
    store = "ratterriers.myshopify.com"
    base_url = f"https://{store}"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    })
    
    # Method 1: Form POST
    print("\nMethod 1: Form POST to /cart/add")
    try:
        form_data = {
            'id': str(variant_id),
            'quantity': '1'
        }
        
        response = session.post(
            f"{base_url}/cart/add",
            data=form_data,
            timeout=15,
            allow_redirects=True
        )
        
        print(f"  Status: {response.status_code}")
        print(f"  Final URL: {response.url}")
        
        if response.status_code in [200, 302, 303]:
            print(f"  ✅ Form POST works!")
            return True
        else:
            print(f"  ❌ Form POST failed")
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Method 2: AJAX JSON
    print("\nMethod 2: AJAX POST to /cart/add.js")
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        }
        
        json_data = {
            'items': [{
                'id': int(variant_id),
                'quantity': 1
            }]
        }
        
        response = session.post(
            f"{base_url}/cart/add.js",
            json=json_data,
            headers=headers,
            timeout=15
        )
        
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print(f"  ✅ AJAX POST works!")
            return True
        else:
            print(f"  ❌ AJAX POST failed")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    return False

def main():
    print("🔍 Shopify Gateway Debug Test\n")
    
    # Test products
    variant_id, price = test_products_api()
    
    if not variant_id:
        print("\n❌ Cannot proceed - no products found")
        return
    
    print(f"\n✅ Will use variant {variant_id} (${price})")
    
    # Test cart
    cart_success = test_cart_add(variant_id)
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Products API: ✅ Working")
    print(f"Cart API: {'✅ Working' if cart_success else '❌ Not Working'}")
    
    if cart_success:
        print("\n💡 Cart API works! The gateway code needs fixing.")
    else:
        print("\n⚠️ Cart API not working - may need different approach.")

if __name__ == '__main__':
    main()
