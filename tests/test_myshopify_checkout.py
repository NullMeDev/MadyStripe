#!/usr/bin/env python3
"""
Test full checkout flow with .myshopify.com stores
"""

import aiohttp
import asyncio
import json
import re

async def test_full_checkout():
    """Test full checkout flow with myshopify.com stores"""
    
    # Small myshopify stores from validated list
    test_stores = [
        'puppylove.myshopify.com',
        'theaterchurch.myshopify.com',
        'fdbf.myshopify.com',
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    connector = aiohttp.TCPConnector(ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        for store in test_stores:
            print(f"\n{'='*60}")
            print(f"Testing: {store}")
            print('='*60)
            
            # Get products
            products_url = f"https://{store}/products.json"
            print(f"1. Fetching products...")
            
            try:
                async with session.get(products_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        print(f"   Products failed: {resp.status}")
                        continue
                    
                    data = await resp.json()
                    products = data.get('products', [])
                    print(f"   Found {len(products)} products")
                    
                    if not products:
                        continue
                    
                    # Find first available variant
                    variant_id = None
                    product_title = None
                    price = None
                    for product in products:
                        for variant in product.get('variants', []):
                            if variant.get('available', True):
                                variant_id = str(variant['id'])
                                product_title = product.get('title', 'Unknown')
                                price = variant.get('price', '0')
                                break
                        if variant_id:
                            break
                    
                    if not variant_id:
                        print("   No available variants")
                        continue
                    
                    print(f"   Using: {product_title} (${price}) - variant {variant_id}")
                    
                    # Cart add
                    cart_url = f"https://{store}/cart/add.js"
                    print(f"2. Adding to cart...")
                    
                    async with session.post(cart_url, data={'id': variant_id}, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        print(f"   Cart add status: {resp.status}")
                        if resp.status in [200, 201]:
                            # Read as text (might be JS or JSON)
                            text = await resp.text()
                            print(f"   Cart response: {text[:100]}...")
                            print("   SUCCESS - Item added to cart!")
                        else:
                            text = await resp.text()
                            print(f"   Cart add failed: {text[:200]}")
                            continue
                    
                    # Get checkout
                    checkout_url = f"https://{store}/checkout"
                    print(f"3. Getting checkout page...")
                    
                    async with session.get(checkout_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15), allow_redirects=True) as resp:
                        print(f"   Checkout status: {resp.status}")
                        final_url = str(resp.url)
                        print(f"   Final URL: {final_url[:80]}...")
                        
                        if '/account/login' in final_url.lower():
                            print("   Store requires login - SKIP")
                            continue
                        
                        if 'checkout' not in final_url.lower():
                            print("   Not redirected to checkout - SKIP")
                            continue
                        
                        checkout_html = await resp.text()
                        
                        # Extract session token
                        sst = None
                        
                        # Method 1: serialized-session-token
                        match = re.search(r'name="serialized-session-token" content="&quot;([^&]+)&q', checkout_html)
                        if match:
                            sst = match.group(1)
                        
                        # Method 2: sessionToken in JSON
                        if not sst:
                            match = re.search(r'"sessionToken"\s*:\s*"([^"]+)"', checkout_html)
                            if match:
                                sst = match.group(1)
                        
                        if sst:
                            print(f"   Session token: {sst[:50]}...")
                            print("   CHECKOUT ACCESSIBLE - Ready for payment!")
                            
                            # Extract other tokens
                            queue_token = None
                            match = re.search(r'queueToken&quot;:&quot;([^&]+)&q', checkout_html)
                            if match:
                                queue_token = match.group(1)
                            if not queue_token:
                                match = re.search(r'"queueToken"\s*:\s*"([^"]+)"', checkout_html)
                                if match:
                                    queue_token = match.group(1)
                            
                            if queue_token:
                                print(f"   Queue token: {queue_token[:30]}...")
                            
                            # Check for GraphQL endpoint
                            if '/checkouts/unstable/graphql' in checkout_html or 'graphql' in checkout_html.lower():
                                print("   GraphQL endpoint available!")
                            
                            print("\n   *** STORE IS WORKING FOR CHECKOUT ***")
                            return store, sst, queue_token
                        else:
                            print("   No session token found")
                            # Check what's in the page
                            if 'password' in checkout_html.lower():
                                print("   Store is password protected")
                            elif 'closed' in checkout_html.lower():
                                print("   Store might be closed")
                            else:
                                print(f"   Page content: {checkout_html[:500]}...")
                            
            except Exception as e:
                print(f"   Error: {e}")
    
    return None, None, None


if __name__ == "__main__":
    print("="*60)
    print("TESTING FULL CHECKOUT FLOW WITH MYSHOPIFY.COM STORES")
    print("="*60)
    result = asyncio.run(test_full_checkout())
    
    if result[0]:
        print(f"\n{'='*60}")
        print(f"WORKING STORE FOUND: {result[0]}")
        print(f"Session Token: {result[1][:50] if result[1] else 'None'}...")
        print(f"Queue Token: {result[2][:30] if result[2] else 'None'}...")
        print("="*60)
    else:
        print("\nNo working stores found in test set")
