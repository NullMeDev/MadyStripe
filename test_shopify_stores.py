#!/usr/bin/env python3
"""
Shopify Store Validator
Tests which stores are actually working by checking if they:
1. Have products
2. Accept checkout
3. Have Shopify Payments enabled

This helps filter your 15000+ stores to find valid ones.
"""

import sys
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def test_store_quick(store_url):
    """Quick test to see if store is alive and has products"""
    try:
        # Test 1: Check if store exists
        resp = requests.get(f"{store_url}/products.json?limit=1", timeout=10)
        
        if resp.status_code == 404:
            return {'store': store_url, 'status': 'DEAD', 'reason': 'Store not found (404)'}
        
        if resp.status_code == 403:
            return {'store': store_url, 'status': 'BLOCKED', 'reason': 'Access forbidden (403)'}
        
        if resp.status_code != 200:
            return {'store': store_url, 'status': 'ERROR', 'reason': f'HTTP {resp.status_code}'}
        
        # Test 2: Check if has products
        try:
            data = resp.json()
            products = data.get('products', [])
            
            if not products:
                return {'store': store_url, 'status': 'EMPTY', 'reason': 'No products'}
            
            # Test 3: Check if product has variants (needed for checkout)
            product = products[0]
            variants = product.get('variants', [])
            
            if not variants:
                return {'store': store_url, 'status': 'NO_VARIANTS', 'reason': 'Product has no variants'}
            
            # Test 4: Check if variant is available
            available = any(v.get('available', False) for v in variants)
            
            if not available:
                return {'store': store_url, 'status': 'SOLD_OUT', 'reason': 'All products sold out'}
            
            # Store looks good!
            return {
                'store': store_url,
                'status': 'VALID',
                'reason': 'Has products and variants',
                'product_count': len(products),
                'product_title': product.get('title', 'Unknown')
            }
            
        except json.JSONDecodeError:
            return {'store': store_url, 'status': 'INVALID', 'reason': 'Invalid JSON response'}
    
    except requests.exceptions.Timeout:
        return {'store': store_url, 'status': 'TIMEOUT', 'reason': 'Connection timeout'}
    
    except requests.exceptions.ConnectionError:
        return {'store': store_url, 'status': 'DEAD', 'reason': 'Connection failed'}
    
    except Exception as e:
        return {'store': store_url, 'status': 'ERROR', 'reason': str(e)[:50]}

def test_stores_parallel(stores, max_workers=20):
    """Test multiple stores in parallel"""
    results = {
        'valid': [],
        'dead': [],
        'blocked': [],
        'empty': [],
        'errors': []
    }
    
    print(f"Testing {len(stores)} stores with {max_workers} workers...")
    print()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(test_store_quick, store): store for store in stores}
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            
            status = result['status']
            store_short = result['store'].replace('https://', '').replace('http://', '')[:40]
            
            if status == 'VALID':
                results['valid'].append(result)
                print(f"[{completed}/{len(stores)}] ✅ {store_short} - {result['reason']}")
            elif status in ['DEAD', 'TIMEOUT']:
                results['dead'].append(result)
                print(f"[{completed}/{len(stores)}] ❌ {store_short} - {result['reason']}")
            elif status == 'BLOCKED':
                results['blocked'].append(result)
                print(f"[{completed}/{len(stores)}] 🚫 {store_short} - {result['reason']}")
            elif status in ['EMPTY', 'NO_VARIANTS', 'SOLD_OUT']:
                results['empty'].append(result)
                print(f"[{completed}/{len(stores)}] 📦 {store_short} - {result['reason']}")
            else:
                results['errors'].append(result)
                print(f"[{completed}/{len(stores)}] ⚠️ {store_short} - {result['reason']}")
    
    return results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Shopify stores to find valid ones')
    parser.add_argument('stores_file', help='File with store URLs (one per line)')
    parser.add_argument('--limit', type=int, help='Limit number of stores to test')
    parser.add_argument('--workers', type=int, default=20, help='Number of parallel workers (default: 20)')
    parser.add_argument('--output', default='valid_stores.txt', help='Output file for valid stores')
    
    args = parser.parse_args()
    
    # Load stores
    print(f"Loading stores from {args.stores_file}...")
    try:
        with open(args.stores_file, 'r') as f:
            stores = [line.strip() for line in f if line.strip() and 'http' in line.lower()]
    except FileNotFoundError:
        print(f"❌ Error: File not found: {args.stores_file}")
        return
    
    if args.limit:
        stores = stores[:args.limit]
    
    print(f"✅ Loaded {len(stores)} stores")
    print()
    
    # Test stores
    start_time = time.time()
    results = test_stores_parallel(stores, args.workers)
    elapsed = time.time() - start_time
    
    # Print summary
    print()
    print("="*70)
    print("RESULTS SUMMARY")
    print("="*70)
    print(f"Total Tested: {len(stores)}")
    print(f"✅ Valid: {len(results['valid'])}")
    print(f"❌ Dead: {len(results['dead'])}")
    print(f"🚫 Blocked: {len(results['blocked'])}")
    print(f"📦 Empty/Sold Out: {len(results['empty'])}")
    print(f"⚠️ Errors: {len(results['errors'])}")
    print(f"⏱️ Time: {elapsed:.1f}s ({elapsed/len(stores):.2f}s per store)")
    print("="*70)
    print()
    
    # Save valid stores
    if results['valid']:
        with open(args.output, 'w') as f:
            for result in results['valid']:
                f.write(f"{result['store']}\n")
        print(f"💾 Valid stores saved to: {args.output}")
        print()
        print("Valid stores:")
        for result in results['valid'][:20]:
            print(f"  {result['store']}")
            print(f"    → {result['product_title']}")
        if len(results['valid']) > 20:
            print(f"  ... and {len(results['valid']) - 20} more")
    else:
        print("❌ No valid stores found!")
    
    # Save detailed report
    report_file = f"store_test_report_{int(time.time())}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📊 Detailed report saved to: {report_file}")

if __name__ == '__main__':
    main()
