#!/usr/bin/env python3
"""
Test cart add with .myshopify.com stores (less protected)
"""

import aiohttp
import asyncio
import json

async def test_myshopify_cart():
    """Test cart add with myshopify.com stores"""
    
    # Small myshopify stores from validated list
    test_stores = [
        'regioninfo.myshopify.com',
        'dejey.myshopify.com',
        'artthang.myshopify.com',
        'puppylove.myshopify.com',
        'theaterchurch.myshopify.com',
        'fdbf.myshopify.com',
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    async with aiohttp.ClientSession() as session:
        for store in test_stores:
            print(f"\n{'='*60}")
            print(f"Testing: {store}")
            print('='*60)
            
            # Get products
            products_url = f"https://{store}/products.json"
            print(f"Fetching products...")
            
            try:
                async with session.get(products_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        print(f"  Products failed: {resp.status}")
                        continue
                    
                    data = await resp.json()
                    products = data.get('products', [])
                    print(f"  Found {len(products)} products")
                    
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
                        print("  No available variants")
                        continue
                    
                    print(f"  Using variant: {variant_id} ({product_title})")
                    
                    # Try cart add
                    cart_url = f"https://{store}/cart/add.js"
                    print(f"  Adding to cart...")
                    
                    # Method: Simple data dict
                    async with session.post(cart_url, data={'id': variant_id}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        print(f"  Cart add status: {resp.status}")
                        if resp.status in [200, 201]:
                            cart_data = await resp.json()
                            print(f"  SUCCESS! Added: {cart_data.get('title', 'Unknown')}")
                            
                            # Try to get checkout
                            checkout_url = f"https://{store}/checkout"
                            async with session.get(checkout_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15), allow_redirects=True) as resp:
                                print(f"  Checkout status: {resp.status}")
                                final_url = str(resp.url)
                                print(f"  Final URL: {final_url[:80]}...")
                                
                                if '/account/login' in final_url.lower():
                                    print("  Store requires login")
                                elif 'checkout' in final_url.lower():
                                    print("  CHECKOUT ACCESSIBLE!")
                        else:
                            text = await resp.text()
                            print(f"  Cart add failed: {text[:200]}")
                            
            except Exception as e:
                print(f"  Error: {e}")


if __name__ == "__main__":
    print("="*60)
    print("TESTING MYSHOPIFY.COM STORES (LESS PROTECTED)")
    print("="*60)
    asyncio.run(test_myshopify_cart())
