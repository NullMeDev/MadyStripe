#!/usr/bin/env python3
"""
Build a database of validated Shopify stores with pre-fetched product information.
This script scans stores from shopify_stores.txt, validates them, and saves
working stores with their cheapest product variant for fast card checking.
"""

import asyncio
import aiohttp
import json
import os
import sys
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configuration
MAX_STORES = 500  # Maximum stores to scan
TARGET_WORKING = 200  # Target number of working stores
CONCURRENT_REQUESTS = 20  # Concurrent requests
TIMEOUT = 10  # Request timeout in seconds
OUTPUT_FILE = 'validated_stores_db.json'

# Store files
STORES_FILE = 'shopify_stores.txt'
VALID_STORES_FILE = 'valid_shopify_stores.txt'


async def fetch_products(session: aiohttp.ClientSession, domain: str) -> Tuple[bool, Dict]:
    """
    Fetch products from a Shopify store and find the cheapest available variant.
    
    Returns:
        (success, data) where data contains store info and cheapest product
    """
    try:
        url = f"https://{domain}/products.json"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        }
        
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=TIMEOUT), ssl=False) as resp:
            if resp.status != 200:
                return False, {'error': f'Status {resp.status}'}
            
            text = await resp.text()
            
            # Verify it's a Shopify store
            if 'shopify' not in text.lower() and '"products"' not in text:
                return False, {'error': 'Not a Shopify store'}
            
            try:
                data = json.loads(text)
                products = data.get('products', [])
            except json.JSONDecodeError:
                return False, {'error': 'Invalid JSON'}
            
            if not products:
                return False, {'error': 'No products'}
            
            # Find cheapest available variant
            min_price = float('inf')
            best_variant = None
            best_product = None
            
            for product in products:
                if not product.get('variants'):
                    continue
                
                for variant in product['variants']:
                    if not variant.get('available', True):
                        continue
                    
                    try:
                        price = variant.get('price', '0')
                        if isinstance(price, str):
                            price = float(price.replace(',', ''))
                        else:
                            price = float(price)
                        
                        if 0 < price < min_price:
                            min_price = price
                            best_variant = variant
                            best_product = product
                    except (ValueError, TypeError):
                        continue
            
            if not best_variant:
                return False, {'error': 'No available variants'}
            
            return True, {
                'domain': domain,
                'variant_id': str(best_variant['id']),
                'price': f"{min_price:.2f}",
                'product_title': best_product.get('title', 'Unknown'),
                'product_handle': best_product.get('handle', ''),
                'total_products': len(products),
                'validated_at': datetime.now().isoformat()
            }
            
    except asyncio.TimeoutError:
        return False, {'error': 'Timeout'}
    except aiohttp.ClientError as e:
        return False, {'error': f'Connection error: {str(e)[:30]}'}
    except Exception as e:
        return False, {'error': f'Exception: {str(e)[:30]}'}


async def test_cart_add(session: aiohttp.ClientSession, domain: str, variant_id: str) -> bool:
    """Test if we can add the product to cart"""
    try:
        cart_url = f"https://{domain}/cart/add.js"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
        }
        
        async with session.post(cart_url, data={'id': variant_id}, headers=headers, 
                               timeout=aiohttp.ClientTimeout(total=TIMEOUT), ssl=False) as resp:
            return resp.status in [200, 201]
    except:
        return False


async def test_checkout_access(session: aiohttp.ClientSession, domain: str) -> Tuple[bool, str]:
    """Test if checkout is accessible (not requiring login)"""
    try:
        checkout_url = f"https://{domain}/checkout"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        async with session.get(checkout_url, headers=headers, 
                              timeout=aiohttp.ClientTimeout(total=TIMEOUT), 
                              ssl=False, allow_redirects=True) as resp:
            final_url = str(resp.url)
            
            if '/account/login' in final_url.lower():
                return False, 'Requires login'
            
            if 'checkout' in final_url.lower():
                text = await resp.text()
                if 'sessionToken' in text or 'serialized-session-token' in text:
                    return True, 'Checkout accessible'
            
            return False, 'Checkout not accessible'
    except:
        return False, 'Error'


async def validate_store(session: aiohttp.ClientSession, domain: str, semaphore: asyncio.Semaphore) -> Optional[Dict]:
    """Validate a single store - fetch products, test cart, test checkout"""
    async with semaphore:
        # Step 1: Fetch products
        success, data = await fetch_products(session, domain)
        if not success:
            return None
        
        # Step 2: Test cart add
        cart_ok = await test_cart_add(session, domain, data['variant_id'])
        if not cart_ok:
            return None
        
        # Step 3: Test checkout access
        checkout_ok, checkout_msg = await test_checkout_access(session, domain)
        
        data['cart_add_works'] = cart_ok
        data['checkout_accessible'] = checkout_ok
        data['checkout_status'] = checkout_msg
        
        # Only return if checkout is accessible
        if checkout_ok:
            return data
        
        return None


def load_stores() -> List[str]:
    """Load store domains from files"""
    stores = set()
    
    # Try valid stores file first
    for filename in [VALID_STORES_FILE, STORES_FILE]:
        if not os.path.exists(filename):
            continue
        
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Skip headers and metadata
                if line.startswith('Valid Shopify') or line.startswith('Total:') or line.startswith('  '):
                    continue
                
                # Extract domain
                parts = line.split()
                domain = parts[0].replace('https://', '').replace('http://', '').rstrip('/')
                
                # Validate domain format
                if '.' in domain and len(domain) > 4:
                    stores.add(domain)
    
    return list(stores)


async def main():
    """Main function to build the store database"""
    print("="*60)
    print("SHOPIFY STORE DATABASE BUILDER")
    print("="*60)
    print(f"Target: {TARGET_WORKING} working stores")
    print(f"Max scan: {MAX_STORES} stores")
    print(f"Concurrent: {CONCURRENT_REQUESTS} requests")
    print("="*60)
    
    # Load stores
    all_stores = load_stores()
    print(f"\nLoaded {len(all_stores)} stores from files")
    
    # Prioritize .myshopify.com stores (less protected)
    myshopify_stores = [s for s in all_stores if '.myshopify.com' in s]
    other_stores = [s for s in all_stores if '.myshopify.com' not in s]
    
    random.shuffle(myshopify_stores)
    random.shuffle(other_stores)
    
    # Combine with myshopify first
    stores_to_scan = myshopify_stores[:MAX_STORES//2] + other_stores[:MAX_STORES//2]
    stores_to_scan = stores_to_scan[:MAX_STORES]
    
    print(f"Scanning {len(stores_to_scan)} stores ({len([s for s in stores_to_scan if '.myshopify.com' in s])} myshopify)")
    
    # Create semaphore for rate limiting
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    
    # Validate stores
    validated_stores = []
    failed_count = 0
    
    connector = aiohttp.TCPConnector(ssl=False, limit=CONCURRENT_REQUESTS)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # Process in batches
        batch_size = 50
        
        for i in range(0, len(stores_to_scan), batch_size):
            batch = stores_to_scan[i:i+batch_size]
            
            print(f"\nProcessing batch {i//batch_size + 1}/{(len(stores_to_scan) + batch_size - 1)//batch_size}...")
            
            tasks = [validate_store(session, domain, semaphore) for domain in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for domain, result in zip(batch, results):
                if isinstance(result, Exception):
                    failed_count += 1
                elif result is not None:
                    validated_stores.append(result)
                    print(f"  ✓ {domain} - ${result['price']} - {result['product_title'][:30]}")
                else:
                    failed_count += 1
            
            print(f"  Progress: {len(validated_stores)} working / {failed_count} failed")
            
            # Stop if we have enough
            if len(validated_stores) >= TARGET_WORKING:
                print(f"\nReached target of {TARGET_WORKING} stores!")
                break
            
            # Small delay between batches
            await asyncio.sleep(1)
    
    # Save results
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Total scanned: {len(stores_to_scan)}")
    print(f"Working stores: {len(validated_stores)}")
    print(f"Failed: {failed_count}")
    
    if validated_stores:
        # Sort by price (cheapest first)
        validated_stores.sort(key=lambda x: float(x['price']))
        
        # Save to JSON
        output_data = {
            'generated_at': datetime.now().isoformat(),
            'total_stores': len(validated_stores),
            'stores': validated_stores
        }
        
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\nSaved to {OUTPUT_FILE}")
        
        # Show price distribution
        prices = [float(s['price']) for s in validated_stores]
        print(f"\nPrice distribution:")
        print(f"  Min: ${min(prices):.2f}")
        print(f"  Max: ${max(prices):.2f}")
        print(f"  Avg: ${sum(prices)/len(prices):.2f}")
        
        # Show top 10 cheapest
        print(f"\nTop 10 cheapest stores:")
        for i, store in enumerate(validated_stores[:10]):
            print(f"  {i+1}. {store['domain']} - ${store['price']} - {store['product_title'][:40]}")
    
    return validated_stores


if __name__ == "__main__":
    stores = asyncio.run(main())
    print(f"\n{'='*60}")
    print(f"Database built with {len(stores)} validated stores")
    print(f"{'='*60}")
