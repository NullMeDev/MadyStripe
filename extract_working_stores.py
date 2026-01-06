#!/usr/bin/env python3
"""
Extract and Test Working Shopify Stores
Finds stores with products at various price points and validates them
"""

import requests
import time
import json
import re

def test_store_api(store_url):
    """Test if store's products.json API is accessible"""
    try:
        url = f"https://{store_url}/products.json"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        products = data.get('products', [])
        
        if not products:
            return None
        
        # Find cheapest available product
        min_price = float('inf')
        min_product = None
        
        for product in products:
            if not product.get('variants'):
                continue
            
            for variant in product['variants']:
                if not variant.get('available', True):
                    continue
                
                try:
                    price_str = variant.get('price', '0')
                    price = float(str(price_str).replace(',', ''))
                    
                    if 0 < price < min_price:
                        min_price = price
                        min_product = {
                            'variant_id': str(variant['id']),
                            'price': price,
                            'title': product.get('title', 'Product')
                        }
                except (ValueError, TypeError):
                    continue
        
        return min_product
        
    except Exception as e:
        return None

def parse_stores_file():
    """Parse valid_shopify_stores.txt and extract stores by price"""
    
    price_categories = {
        'penny': [],      # $0.01 - $2
        'low': [],        # $2 - $15
        'medium': [],     # $15 - $50
        'high': []        # $50+
    }
    
    current_store = None
    current_price = None
    
    print("📖 Reading valid_shopify_stores.txt...")
    
    with open('valid_shopify_stores.txt', 'r') as f:
        for line in f:
            line = line.strip()
            
            # Store line
            if '.myshopify.com' in line and not line.startswith(' '):
                current_store = line
                current_price = None
            
            # Price line
            elif line.startswith('  Cheapest: $') and current_store:
                # Extract price
                match = re.search(r'\$(\d+\.?\d*)', line)
                if match:
                    price = float(match.group(1))
                    current_price = price
                    
                    # Categorize
                    if 0.01 <= price < 2:
                        price_categories['penny'].append((current_store, price))
                    elif 2 <= price < 15:
                        price_categories['low'].append((current_store, price))
                    elif 15 <= price < 50:
                        price_categories['medium'].append((current_store, price))
                    elif price >= 50:
                        price_categories['high'].append((current_store, price))
    
    return price_categories

def main():
    print("="*70)
    print("SHOPIFY STORE EXTRACTOR & VALIDATOR")
    print("="*70)
    print()
    
    # Parse stores
    stores = parse_stores_file()
    
    print("\n📊 Stores found by category:")
    print(f"  Penny ($0.01-$2):   {len(stores['penny'])} stores")
    print(f"  Low ($2-$15):       {len(stores['low'])} stores")
    print(f"  Medium ($15-$50):   {len(stores['medium'])} stores")
    print(f"  High ($50+):        {len(stores['high'])} stores")
    
    print(f"\n{'='*70}")
    print("🧪 Testing stores for API accessibility...")
    print(f"{'='*70}\n")
    
    validated = {
        'penny': [],
        'low': [],
        'medium': [],
        'high': []
    }
    
    for category, store_list in stores.items():
        if category == 'penny':
            print(f"\n💰 Testing PENNY stores ($0.01-$2)...")
            target = 10
        elif category == 'low':
            print(f"\n💵 Testing LOW stores ($2-$15)...")
            target = 10
        elif category == 'medium':
            print(f"\n💳 Testing MEDIUM stores ($15-$50)...")
            target = 10
        else:
            print(f"\n💎 Testing HIGH stores ($50+)...")
            target = 10
        
        tested = 0
        for store_url, listed_price in store_list:
            if len(validated[category]) >= target:
                break
            
            tested += 1
            print(f"  [{tested}] {store_url} (${listed_price})...", end=' ')
            
            # Test API
            product_info = test_store_api(store_url)
            
            if product_info:
                print(f"✅ ${product_info['price']:.2f}")
                validated[category].append({
                    'store': store_url,
                    'price': product_info['price'],
                    'product': product_info['title'],
                    'variant_id': product_info['variant_id']
                })
            else:
                print("❌")
            
            time.sleep(0.5)  # Rate limiting
        
        print(f"  ✅ Validated {len(validated[category])} working stores")
    
    # Save results
    print(f"\n{'='*70}")
    print("💾 Saving results...")
    print(f"{'='*70}\n")
    
    # JSON format
    with open('working_shopify_stores.json', 'w') as f:
        json.dump(validated, f, indent=2)
    
    # Human-readable format
    with open('working_shopify_stores.txt', 'w') as f:
        f.write("# Working Shopify Stores for MadyStripe\n")
        f.write("# Tested and validated\n")
        f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for category, store_list in validated.items():
            if category == 'penny':
                f.write(f"\n{'='*70}\n")
                f.write(f"PENNY GATE ($0.01-$2) - {len(store_list)} stores\n")
                f.write(f"{'='*70}\n\n")
            elif category == 'low':
                f.write(f"\n{'='*70}\n")
                f.write(f"LOW GATE ($2-$15) - {len(store_list)} stores\n")
                f.write(f"{'='*70}\n\n")
            elif category == 'medium':
                f.write(f"\n{'='*70}\n")
                f.write(f"MEDIUM GATE ($15-$50) - {len(store_list)} stores\n")
                f.write(f"{'='*70}\n\n")
            else:
                f.write(f"\n{'='*70}\n")
                f.write(f"HIGH GATE ($50+) - {len(store_list)} stores\n")
                f.write(f"{'='*70}\n\n")
            
            for i, store_info in enumerate(store_list, 1):
                f.write(f"{i}. {store_info['store']}\n")
                f.write(f"   Price: ${store_info['price']:.2f}\n")
                f.write(f"   Product: {store_info['product']}\n")
                f.write(f"   Variant ID: {store_info['variant_id']}\n\n")
    
    print("✅ Results saved to:")
    print("   - working_shopify_stores.json")
    print("   - working_shopify_stores.txt")
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 VALIDATION SUMMARY")
    print(f"{'='*70}")
    print(f"  Penny Gate:   {len(validated['penny']):2} stores")
    print(f"  Low Gate:     {len(validated['low']):2} stores")
    print(f"  Medium Gate:  {len(validated['medium']):2} stores")
    print(f"  High Gate:    {len(validated['high']):2} stores")
    print(f"  TOTAL:        {sum(len(v) for v in validated.values())} stores")
    
    # Show top stores
    print(f"\n{'='*70}")
    print("🎯 TOP STORES PER CATEGORY")
    print(f"{'='*70}\n")
    
    for category, store_list in validated.items():
        if store_list:
            if category == 'penny':
                print(f"💰 Penny Gate: {store_list[0]['store']} (${store_list[0]['price']:.2f})")
            elif category == 'low':
                print(f"💵 Low Gate:   {store_list[0]['store']} (${store_list[0]['price']:.2f})")
            elif category == 'medium':
                print(f"💳 Medium Gate: {store_list[0]['store']} (${store_list[0]['price']:.2f})")
            else:
                print(f"💎 High Gate:  {store_list[0]['store']} (${store_list[0]['price']:.2f})")
    
    print(f"\n{'='*70}")
    print("✅ Extraction and validation complete!")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    main()
