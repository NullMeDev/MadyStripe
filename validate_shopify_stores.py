#!/usr/bin/env python3
"""
Shopify Store Validator
Validates stores from 15000stores.txt and finds working ones with products
"""

import requests
import json
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

class StoreValidator:
    def __init__(self):
        self.valid_stores = []
        self.invalid_stores = []
        self.checked = 0
        self.total = 0
        
    def check_store(self, store_url):
        """Check if a store is valid and has products"""
        try:
            # Normalize URL
            store_url = store_url.strip()
            if not store_url:
                return None
                
            # Remove protocol if present
            store_url = store_url.replace('https://', '').replace('http://', '')
            
            # Try to fetch products
            url = f"https://{store_url}/products.json"
            
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                data = response.json()
                
                if 'products' in data and len(data['products']) > 0:
                    # Store is valid and has products
                    products = data['products']
                    
                    # Find cheapest product
                    cheapest = None
                    cheapest_price = float('inf')
                    
                    for product in products:
                        if product.get('variants'):
                            for variant in product['variants']:
                                price = float(variant.get('price', 0))
                                if price > 0 and price < cheapest_price:
                                    cheapest_price = price
                                    cheapest = {
                                        'title': product.get('title', 'Unknown'),
                                        'price': price,
                                        'variant_id': variant.get('id'),
                                        'available': variant.get('available', False)
                                    }
                    
                    return {
                        'url': store_url,
                        'status': 'valid',
                        'product_count': len(products),
                        'cheapest': cheapest
                    }
                else:
                    return {
                        'url': store_url,
                        'status': 'no_products',
                        'product_count': 0
                    }
            else:
                return {
                    'url': store_url,
                    'status': 'not_shopify',
                    'code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {
                'url': store_url,
                'status': 'timeout'
            }
        except requests.exceptions.ConnectionError:
            return {
                'url': store_url,
                'status': 'connection_error'
            }
        except Exception as e:
            return {
                'url': store_url,
                'status': 'error',
                'error': str(e)[:50]
            }
    
    def validate_stores(self, stores, max_workers=10, limit=None):
        """Validate multiple stores concurrently"""
        self.total = len(stores) if not limit else min(limit, len(stores))
        stores_to_check = stores[:limit] if limit else stores
        
        print(f"\n{'='*70}")
        print(f"SHOPIFY STORE VALIDATOR")
        print(f"{'='*70}")
        print(f"Total stores to check: {self.total}")
        print(f"Threads: {max_workers}")
        print(f"{'='*70}\n")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.check_store, store): store for store in stores_to_check}
            
            for future in as_completed(futures):
                result = future.result()
                self.checked += 1
                
                if result:
                    if result['status'] == 'valid':
                        self.valid_stores.append(result)
                        print(f"✅ [{self.checked}/{self.total}] {result['url']}")
                        print(f"   Products: {result['product_count']}")
                        if result.get('cheapest'):
                            print(f"   Cheapest: ${result['cheapest']['price']} - {result['cheapest']['title'][:50]}")
                    elif result['status'] == 'no_products':
                        self.invalid_stores.append(result)
                        print(f"⚠️  [{self.checked}/{self.total}] {result['url']} - No products")
                    else:
                        self.invalid_stores.append(result)
                        print(f"❌ [{self.checked}/{self.total}] {result['url']} - {result['status']}")
                
                # Progress update every 10 stores
                if self.checked % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = self.checked / elapsed if elapsed > 0 else 0
                    print(f"\n📊 Progress: {self.checked}/{self.total} | Valid: {len(self.valid_stores)} | Rate: {rate:.1f} stores/sec\n")
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*70}")
        print(f"VALIDATION COMPLETE")
        print(f"{'='*70}")
        print(f"Total checked: {self.checked}")
        print(f"✅ Valid stores: {len(self.valid_stores)}")
        print(f"❌ Invalid stores: {len(self.invalid_stores)}")
        print(f"⏱️  Time: {elapsed:.1f}s")
        print(f"📈 Rate: {self.checked/elapsed:.1f} stores/sec")
        print(f"{'='*70}\n")
        
        return self.valid_stores
    
    def save_results(self, filename='valid_shopify_stores.txt'):
        """Save valid stores to file"""
        if not self.valid_stores:
            print("⚠️  No valid stores to save")
            return
        
        with open(filename, 'w') as f:
            f.write(f"# Valid Shopify Stores - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total: {len(self.valid_stores)} stores\n\n")
            
            for store in self.valid_stores:
                f.write(f"{store['url']}\n")
                f.write(f"  Products: {store['product_count']}\n")
                if store.get('cheapest'):
                    f.write(f"  Cheapest: ${store['cheapest']['price']} - {store['cheapest']['title']}\n")
                f.write("\n")
        
        print(f"✅ Saved {len(self.valid_stores)} valid stores to: {filename}")
        
        # Also save just URLs for easy use
        urls_file = filename.replace('.txt', '_urls_only.txt')
        with open(urls_file, 'w') as f:
            for store in self.valid_stores:
                f.write(f"{store['url']}\n")
        
        print(f"✅ Saved URLs only to: {urls_file}")
    
    def save_detailed_report(self, filename='store_validation_report.json'):
        """Save detailed JSON report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_checked': self.checked,
            'valid_count': len(self.valid_stores),
            'invalid_count': len(self.invalid_stores),
            'valid_stores': self.valid_stores,
            'invalid_stores': self.invalid_stores
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Saved detailed report to: {filename}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate Shopify stores')
    parser.add_argument('file', nargs='?', default='15000stores.txt',
                       help='File containing store URLs (default: 15000stores.txt)')
    parser.add_argument('-t', '--threads', type=int, default=10,
                       help='Number of threads (default: 10)')
    parser.add_argument('-l', '--limit', type=int, default=100,
                       help='Limit number of stores to check (default: 100, 0 = all)')
    parser.add_argument('-o', '--output', default='valid_shopify_stores.txt',
                       help='Output file for valid stores')
    
    args = parser.parse_args()
    
    # Check if file exists
    try:
        with open(args.file, 'r') as f:
            stores = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print(f"❌ Error: File not found: {args.file}")
        sys.exit(1)
    
    if not stores:
        print(f"❌ Error: No stores found in {args.file}")
        sys.exit(1)
    
    print(f"📁 Loaded {len(stores)} stores from {args.file}")
    
    # Validate stores
    validator = StoreValidator()
    limit = args.limit if args.limit > 0 else None
    valid_stores = validator.validate_stores(stores, max_workers=args.threads, limit=limit)
    
    # Save results
    if valid_stores:
        validator.save_results(args.output)
        validator.save_detailed_report()
        
        print(f"\n🎉 Found {len(valid_stores)} valid stores!")
        print(f"\nTop 5 stores with cheapest products:")
        
        # Sort by cheapest price
        sorted_stores = sorted(
            [s for s in valid_stores if s.get('cheapest')],
            key=lambda x: x['cheapest']['price']
        )[:5]
        
        for i, store in enumerate(sorted_stores, 1):
            print(f"{i}. {store['url']}")
            print(f"   ${store['cheapest']['price']} - {store['cheapest']['title'][:60]}")
    else:
        print("\n⚠️  No valid stores found. Try:")
        print("  - Increasing the limit (-l)")
        print("  - Checking a different store list")
        print("  - Verifying your internet connection")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("""
╔════════════════════════════════════════════════════════════╗
║              SHOPIFY STORE VALIDATOR                      ║
║         Find Valid Stores with Products                   ║
╚════════════════════════════════════════════════════════════╝

Usage: python3 validate_shopify_stores.py [options]

Quick Start:
  python3 validate_shopify_stores.py                    # Check first 100 stores
  python3 validate_shopify_stores.py -l 500             # Check first 500 stores
  python3 validate_shopify_stores.py -l 0               # Check all stores
  python3 validate_shopify_stores.py -t 20 -l 1000      # 20 threads, 1000 stores

Options:
  file                  Store list file (default: 15000stores.txt)
  -t, --threads        Number of threads (default: 10)
  -l, --limit          Limit stores to check (default: 100, 0 = all)
  -o, --output         Output file (default: valid_shopify_stores.txt)

Examples:
  python3 validate_shopify_stores.py 15000stores.txt -l 200
  python3 validate_shopify_stores.py -t 20 -l 0 -o working_stores.txt

Run with --help for more info
""")
        sys.exit(0)
    
    main()
