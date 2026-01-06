#!/usr/bin/env python3
"""
Find Shopify stores at ALL requested price points
Target prices: $1-2, $2, $4-10, $6, $8, $12-18, $45+, and HIGHEST
Goal: 20+ stores per price point
"""

import json

def parse_price(price_str):
    """Extract numeric price from string like '$5.0 - Product'"""
    try:
        return float(price_str.split('$')[1].split(' ')[0])
    except:
        return None

def find_stores_by_all_prices():
    """Find stores for all requested price ranges"""
    
    # Define price ranges (min, max, label)
    price_ranges = [
        (0.99, 2.00, '$1-$2 (Penny)'),
        (2.00, 2.01, '$2 (Exact)'),
        (4.00, 10.00, '$4-$10 (Low)'),
        (6.00, 6.01, '$6 (Exact)'),
        (8.00, 8.01, '$8 (Exact)'),
        (12.00, 18.00, '$12-$18 (Medium)'),
        (45.00, 200.00, '$45-$200 (High)'),
        (200.00, 999999.00, '$200+ (Highest)'),
    ]
    
    results = {label: [] for _, _, label in price_ranges}
    
    current_store = None
    
    print("🔍 Scanning 11,419 stores...")
    
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
    print("FINDING STORES AT ALL PRICE POINTS")
    print("="*70)
    print("\nTarget: 20+ stores per price point\n")
    
    stores = find_stores_by_all_prices()
    
    # Display results
    total_found = 0
    for price_point, store_list in stores.items():
        print(f"\n{'='*70}")
        print(f"💰 {price_point}")
        print(f"{'='*70}")
        print(f"Found: {len(store_list)} stores")
        total_found += len(store_list)
        
        if store_list:
            # Show first 5 stores
            for i, store_info in enumerate(store_list[:5], 1):
                print(f"  {i}. {store_info['store']} - ${store_info['price']}")
            
            if len(store_list) > 5:
                print(f"  ... and {len(store_list) - 5} more")
        else:
            print("  ❌ No stores found")
    
    # Save detailed results
    print(f"\n\n{'='*70}")
    print("💾 Saving results...")
    print(f"{'='*70}\n")
    
    # Save JSON
    with open('all_price_stores.json', 'w') as f:
        json.dump(stores, f, indent=2)
    print("✅ Saved: all_price_stores.json")
    
    # Save text
    with open('all_price_stores.txt', 'w') as f:
        f.write("# All Price Point Stores for MadyStripe\n")
        f.write(f"# Total: {total_found} stores found\n")
        f.write("# Generated from 11,419 validated stores\n\n")
        
        for price_point, store_list in stores.items():
            f.write(f"\n{'='*70}\n")
            f.write(f"{price_point} ({len(store_list)} stores)\n")
            f.write(f"{'='*70}\n\n")
            
            if store_list:
                for store_info in store_list:
                    f.write(f"{store_info['store']}\n")
                    f.write(f"  Price: ${store_info['price']}\n")
                    f.write(f"  Product: {store_info['product']}\n\n")
            else:
                f.write("No stores found\n\n")
    
    print("✅ Saved: all_price_stores.txt")
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}")
    for price_point, store_list in stores.items():
        status = "✅" if len(store_list) >= 20 else "⚠️" if len(store_list) > 0 else "❌"
        print(f"{status} {price_point:25} : {len(store_list):4} stores")
    
    print(f"\nTotal stores found: {total_found}")

if __name__ == '__main__':
    main()
