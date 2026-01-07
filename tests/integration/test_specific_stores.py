#!/usr/bin/env python3
"""
Test specific Shopify stores we found with different prices
"""

import requests
import time
import json

# Stores we found with different prices from grep output
STORES_TO_TEST = {
    'penny': [
        'turningpointe.myshopify.com',  # $1.0
        'smekenseducation.myshopify.com',  # $1.0
        'buger.myshopify.com',  # $1.99
    ],
    'low': [
        'sasters.myshopify.com',  # $4.45
        'performancetrainingsystems.myshopify.com',  # $4.99
        'tabithastreasures.myshopify.com',  # $6.95
        'fdbf.myshopify.com',  # $8.0
        'toosmart.myshopify.com',  # $9.95
        'runescapemoney.myshopify.com',  # $9.99
        'theaterchurch.myshopify.com',  # $10.0
    ],
    'medium': [
        'vehicleyard.myshopify.com',  # $12.0
        'fishnet.myshopify.com',  # $14.99
        'auction-sniper.myshopify.com',  # $15.0
        'jackaroo.myshopify.com',  # $15.0
        'themacnurse.myshopify.com',  # $17.5
    ],
    'high': [
        'maps.myshopify.com',  # $45.0
        'zetacom.myshopify.com',  # $399.0
        'hugo.myshopify.com',  # $1000.0
    ]
}

def test_store(store_url):
    """Test if store has accessible products"""
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
                            'title': product.get('title', 'Product')[:50]
                        }
                except (ValueError, TypeError):
                    continue
        
        return min_product
        
    except Exception as e:
        return None

def main():
    print("="*70)
    print("TESTING SPECIFIC SHOPIFY STORES")
    print("="*70)
    print()
    
    validated = {
        'penny': [],
        'low': [],
        'medium': [],
        'high': []
    }
    
    for category, store_list in STORES_TO_TEST.items():
        if category == 'penny':
            print(f"\n💰 Testing PENNY stores ($0.01-$2)...")
        elif category == 'low':
            print(f"\n💵 Testing LOW stores ($2-$15)...")
        elif category == 'medium':
            print(f"\n💳 Testing MEDIUM stores ($15-$50)...")
        else:
            print(f"\n💎 Testing HIGH stores ($50+)...")
        
        for i, store_url in enumerate(store_list, 1):
            print(f"  [{i}/{len(store_list)}] {store_url}...", end=' ')
            
            product_info = test_store(store_url)
            
            if product_info:
                print(f"✅ ${product_info['price']:.2f} - {product_info['title']}")
                validated[category].append({
                    'store': store_url,
                    'price': product_info['price'],
                    'product': product_info['title'],
                    'variant_id': product_info['variant_id']
                })
            else:
                print("❌ No products or API error")
            
            time.sleep(0.5)
        
        print(f"  ✅ Validated {len(validated[category])} stores")
    
    # Save results
    print(f"\n{'='*70}")
    print("💾 Saving results...")
    print(f"{'='*70}\n")
    
    with open('working_shopify_stores.json', 'w') as f:
        json.dump(validated, f, indent=2)
    
    with open('working_shopify_stores.txt', 'w') as f:
        f.write("# Working Shopify Stores for MadyStripe\n")
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
    
    print("✅ Results saved!")
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 VALIDATION SUMMARY")
    print(f"{'='*70}")
    print(f"  Penny Gate:   {len(validated['penny']):2} stores")
    print(f"  Low Gate:     {len(validated['low']):2} stores")
    print(f"  Medium Gate:  {len(validated['medium']):2} stores")
    print(f"  High Gate:    {len(validated['high']):2} stores")
    print(f"  TOTAL:        {sum(len(v) for v in validated.values())} stores")
    
    print(f"\n{'='*70}")
    print("✅ Testing complete!")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    main()
