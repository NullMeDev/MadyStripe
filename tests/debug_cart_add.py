#!/usr/bin/env python3
"""
Debug cart add to see what's happening
"""

import aiohttp
import asyncio
import json

async def test_cart_add():
    """Test cart add with different stores"""
    
    # Test stores and their products
    test_cases = [
        {
            'store': 'allbirds.com',
            'variant_id': '41271108239440'  # From earlier test
        },
        {
            'store': 'gymshark.com',
            'variant_id': None  # Will fetch
        }
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
    }
    
    async with aiohttp.ClientSession() as session:
        for test in test_cases:
            store = test['store']
            print(f"\n{'='*60}")
            print(f"Testing: {store}")
            print('='*60)
            
            # First get products
            products_url = f"https://{store}/products.json"
            print(f"Fetching products from: {products_url}")
            
            try:
                async with session.get(products_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    print(f"Products response status: {resp.status}")
                    if resp.status != 200:
                        print(f"Failed to get products")
                        continue
                    
                    data = await resp.json()
                    products = data.get('products', [])
                    print(f"Found {len(products)} products")
                    
                    if not products:
                        continue
                    
                    # Find first available variant
                    variant_id = None
                    product_title = None
                    for product in products:
                        for variant in product.get('variants', []):
                            if variant.get('available', True):
                                variant_id = str(variant['id'])
                                product_title = product.get('title', 'Unknown')
                                break
                        if variant_id:
                            break
                    
                    if not variant_id:
                        print("No available variants found")
                        continue
                    
                    print(f"Using variant: {variant_id} ({product_title})")
                    
                    # Try cart add
                    cart_url = f"https://{store}/cart/add.js"
                    print(f"\nTrying cart add to: {cart_url}")
                    
                    # Method 1: Form data with dict
                    print("\n--- Method 1: data={'id': variant_id} ---")
                    async with session.post(cart_url, data={'id': variant_id}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        print(f"Status: {resp.status}")
                        text = await resp.text()
                        print(f"Response: {text[:500]}")
                    
                    # Method 2: JSON
                    print("\n--- Method 2: json={'id': variant_id, 'quantity': 1} ---")
                    json_headers = headers.copy()
                    json_headers['Content-Type'] = 'application/json'
                    async with session.post(cart_url, json={'id': int(variant_id), 'quantity': 1}, headers=json_headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        print(f"Status: {resp.status}")
                        text = await resp.text()
                        print(f"Response: {text[:500]}")
                    
                    # Method 3: Form string
                    print("\n--- Method 3: data=f'id={variant_id}&quantity=1' ---")
                    form_headers = headers.copy()
                    form_headers['Content-Type'] = 'application/x-www-form-urlencoded'
                    async with session.post(cart_url, data=f'id={variant_id}&quantity=1', headers=form_headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        print(f"Status: {resp.status}")
                        text = await resp.text()
                        print(f"Response: {text[:500]}")
                        
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_cart_add())
