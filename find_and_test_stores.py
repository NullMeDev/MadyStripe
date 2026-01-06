#!/usr/bin/env python3
"""
Find and Test Shopify Stores for Price Gates
Searches for stores with products in price ranges and validates them
"""

import requests
import time
import json
from typing import List, Dict, Optional

def parse_price(price_str):
    """Extract numeric price from string like '$5.0 - Product'"""
    try:
        return float(price_str.split('$')[1].split(' ')[0])
    except:
        return None

def test_store_products(store_url: str) -> Optional[Dict]:
    """
    Test if store has accessible products via API
    Returns dict with cheapest product info or None if failed
    """
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
                            'title': product.get('title', 'Product'),
                            'available': True
                        }
                except (ValueError, TypeError):
                    continue
        
        return min_product
        
    except Exception as e:
        return None

def find_stores_by_price_range():
    """Find stores within broader price ranges"""
    
    # Define broader price ranges (min, max, label)
    price_ranges = [
        (0.01, 1.00, '$0.01-$1'),      # Penny to $1
        (1.00, 10.00, '$1-$10'),       # $1 to $10 (for $5 gate)
        (10.00, 30.00, '$10-$30'),     # $10 to $30 (for $20 gate)
        (30.00, 150.00, '$30-$150')    # $30 to $150 (for $100 gate)
    ]
    
    results = {label: [] for _, _, label in price_ranges}
    
    current_store = None
    
    print("🔍 Parsing valid_shopify_stores.txt...")
    
    with open('valid_shopify_stores.txt', 'r') as f:
        for line in f:
            line = line.strip()
            
            # Check if this is a store line
            if '.myshopify.com' in line and not line.startswith('#') and not line.startswith(' '):
                current_store = line
            
            # Check if this is a price line
            elif line.startswith('  Cheapest: $') and current_store:
                price = parse_price(line)
                
                if price:
                    # Check which range this price falls into
                    for min_price, max_price, label in price_ranges:
                        if min_price <= price <= max_price:
                            product_name = line.split(' - ', 1)[1] if ' - ' in line else 'Unknown'
                            results[label].append({
                                'store': current_store,
                                'price': price,
                                'product': product_name
                            })
                            break
    
    return results

def main():
    print("="*70)
    print("SHOPIFY STORE FINDER & VALIDATOR")
    print("="*70)
    print("\n🔍 Step 1: Finding stores in price ranges...\n")
    
    stores = find_stores_by_price_range()
    
    # Display initial results
    for price_point, store_list in stores.items():
        print(f"  {price_point:12} : {len(store_list):4} stores found")
    
    print(f"\n{'='*70}")
    print("🧪 Step 2: Testing stores for product availability...")
    print(f"{'='*70}\n")
    
    validated_stores = {}
    
    for price_range, store_list in stores.items():
        print(f"\n📋 Testing {price_range} stores...")
        validated = []
        
        # Test up to 20 stores per range
        for i, store_info in enumerate(store_list[:20], 1):
            store_url = store_info['store']
            print(f"  [{i}/20] Testing {store_url}...", end=' ')
            
            # Test store
            product_info = test_store_products(store_url)
            
            if product_info:
                print(f"✅ ${product_info['price']:.2f} - {product_info['title'][:30]}")
                validated.append({
                    'store': store_url,
                    'price': product_info['price'],
                    'product': product_info['title'],
                    'variant_id': product_info['variant_id']
                })
                
                # Stop after finding 10 working stores
                if len(validated) >= 10:
                    print(f"  ✅ Found 10 working stores, moving to next range...")
                    break
            else:
                print("❌ No products or API error")
            
            # Rate limiting
            time.sleep(1)
        
        validated_stores[price_range] = validated
        print(f"  ✅ Validated {len(validated)} working stores for {price_range}")
    
    # Save results
    print(f"\n{'='*70}")
    print("💾 Saving results...")
    print(f"{'='*70}\n")
    
    # Save to JSON for easy parsing
    with open('validated_stores.json', 'w') as f:
        json.dump(validated_stores, f, indent=2)
    
    # Save human-readable format
    with open('validated_stores.txt', 'w') as f:
        f.write("# Validated Shopify Stores for MadyStripe\n")
        f.write("# Tested and confirmed working\n")
        f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for price_range, store_list in validated_stores.items():
            f.write(f"\n{'='*70}\n")
            f.write(f"{price_range} STORES ({len(store_list)} validated)\n")
            f.write(f"{'='*70}\n\n")
            
            if store_list:
                for i, store_info in enumerate(store_list, 1):
                    f.write(f"{i}. {store_info['store']}\n")
                    f.write(f"   Price: ${store_info['price']:.2f}\n")
                    f.write(f"   Product: {store_info['product']}\n")
                    f.write(f"   Variant ID: {store_info['variant_id']}\n\n")
            else:
                f.write("No validated stores in this range\n\n")
    
    print("✅ Results saved to:")
    print("   - validated_stores.json (machine-readable)")
    print("   - validated_stores.txt (human-readable)")
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 VALIDATION SUMMARY")
    print(f"{'='*70}")
    
    for price_range, store_list in validated_stores.items():
        print(f"{price_range:12} : {len(store_list):2} validated stores")
    
    # Map to gateway price points
    print(f"\n{'='*70}")
    print("🎯 GATEWAY MAPPING")
    print(f"{'='*70}\n")
    
    gateway_mapping = {
        '$0.01 Gate (Penny)': '$0.01-$1',
        '$5 Gate (Low)': '$1-$10',
        '$20 Gate (Medium)': '$10-$30',
        '$100 Gate (High)': '$30-$150'
    }
    
    for gateway, price_range in gateway_mapping.items():
        stores_list = validated_stores.get(price_range, [])
        print(f"{gateway:25} : {len(stores_list)} stores available")
        if stores_list:
            print(f"  Best: {stores_list[0]['store']} (${stores_list[0]['price']:.2f})")
    
    print(f"\n{'='*70}")
    print("✅ Store validation complete!")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    main()
