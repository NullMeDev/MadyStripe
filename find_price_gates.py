#!/usr/bin/env python3
"""
Find Shopify stores at specific price points for gateway testing
Searches for prices close to $0.01, $5, $20, and $100
"""

def parse_price(price_str):
    """Extract numeric price from string like '$5.0 - Product'"""
    try:
        return float(price_str.split('$')[1].split(' ')[0])
    except:
        return None

def find_stores_by_price_range():
    """Find stores within price ranges"""
    
    # Define price ranges (min, max, label)
    price_ranges = [
        (0.01, 0.01, '$0.01'),
        (4.99, 5.01, '$5'),
        (19.99, 20.01, '$20'),
        (99.99, 100.01, '$100')
    ]
    
    results = {label: [] for _, _, label in price_ranges}
    
    current_store = None
    
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
    print("🔍 Finding Shopify stores at specific price points...\n")
    
    stores = find_stores_by_price_range()
    
    # Display results
    for price_point, store_list in stores.items():
        print(f"\n{'='*70}")
        print(f"💰 {price_point} GATES ({len(store_list)} found)")
        print(f"{'='*70}")
        
        if store_list:
            # Show first 3 stores
            for i, store_info in enumerate(store_list[:3], 1):
                print(f"\n{i}. {store_info['store']}")
                print(f"   Price: ${store_info['price']}")
                print(f"   Product: {store_info['product']}")
            
            if len(store_list) > 3:
                print(f"\n   ... and {len(store_list) - 3} more stores")
        else:
            print("❌ No stores found at this price point")
    
    # Save detailed results
    print(f"\n\n{'='*70}")
    print("💾 Saving results to shopify_price_gates.txt...")
    print(f"{'='*70}\n")
    
    with open('shopify_price_gates.txt', 'w') as f:
        f.write("# Shopify Price Gates for MadyStripe Bot\n")
        f.write("# Generated from 11,419 validated stores\n")
        f.write("# Format: store_url | price | product_name\n\n")
        
        for price_point, store_list in stores.items():
            f.write(f"\n{'='*70}\n")
            f.write(f"{price_point} GATES ({len(store_list)} stores)\n")
            f.write(f"{'='*70}\n\n")
            
            if store_list:
                for store_info in store_list:
                    f.write(f"{store_info['store']}\n")
                    f.write(f"  Price: ${store_info['price']}\n")
                    f.write(f"  Product: {store_info['product']}\n\n")
            else:
                f.write("No stores found at this price point\n\n")
    
    print("✅ Results saved to shopify_price_gates.txt")
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}")
    for price_point, store_list in stores.items():
        print(f"{price_point:8} : {len(store_list):4} stores")
    
    # Recommend best stores
    print(f"\n{'='*70}")
    print("🎯 RECOMMENDED STORES FOR MADY BOT")
    print(f"{'='*70}\n")
    
    for price_point, store_list in stores.items():
        if store_list:
            best = store_list[0]
            print(f"{price_point:8} : {best['store']}")
            print(f"           ${best['price']} - {best['product']}\n")

if __name__ == '__main__':
    main()
