#!/usr/bin/env python3
"""
Debug Penny Gate - Check why products aren't being found
"""

import requests
import json

stores = [
    'turningpointe.myshopify.com',
    'smekenseducation.myshopify.com',
    'buger.myshopify.com'
]

print("="*70)
print("DEBUGGING PENNY GATE STORES")
print("="*70)

for store in stores:
    print(f"\n{'='*70}")
    print(f"Testing: {store}")
    print(f"{'='*70}")
    
    url = f"https://{store}/products.json"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            print(f"Products Found: {len(products)}")
            
            if products:
                print(f"\n📦 First Product:")
                product = products[0]
                print(f"  Title: {product.get('title', 'N/A')}")
                print(f"  ID: {product.get('id', 'N/A')}")
                
                variants = product.get('variants', [])
                if variants:
                    variant = variants[0]
                    price = variant.get('price', 'N/A')
                    variant_id = variant.get('id', 'N/A')
                    print(f"  Price: ${price}")
                    print(f"  Variant ID: {variant_id}")
                    print(f"  Available: {variant.get('available', False)}")
                    print(f"  ✅ Store is WORKING")
                else:
                    print(f"  ⚠️ No variants found")
            else:
                print(f"  ❌ No products found")
        else:
            print(f"  ❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Exception: {str(e)}")

print(f"\n{'='*70}")
print("DEBUG COMPLETE")
print(f"{'='*70}")
