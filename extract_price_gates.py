#!/usr/bin/env python3
"""
Extract Shopify stores at specific price points for gateway testing
"""

def extract_stores_by_price():
    """Extract stores at $0.01, $5, $20, and $100 price points"""
    
    target_prices = {
        '0.01': [],
        '5.0': [],
        '5.00': [],
        '20.0': [],
        '20.00': [],
        '100.0': [],
        '100.00': []
    }
    
    current_store = None
    
    with open('valid_shopify_stores.txt', 'r') as f:
        for line in f:
            line = line.strip()
            
            # Check if this is a store line
            if '.myshopify.com' in line and not line.startswith('#'):
                current_store = line
            
            # Check if this is a price line
            elif line.startswith('  Cheapest: $') and current_store:
                # Extract price
                price_str = line.split('$')[1].split(' - ')[0]
                
                # Check if this price matches our targets
                for target_price in target_prices.keys():
                    if price_str == target_price:
                        product_name = line.split(' - ', 1)[1] if ' - ' in line else 'Unknown'
                        target_prices[target_price].append({
                            'store': current_store,
                            'price': price_str,
                            'product': product_name
                        })
    
    # Consolidate similar prices
    results = {
        '$0.01': target_prices['0.01'],
        '$5': target_prices['5.0'] + target_prices['5.00'],
        '$20': target_prices['20.0'] + target_prices['20.00'],
        '$100': target_prices['100.0'] + target_prices['100.00']
    }
    
    return results

def main():
    print("🔍 Extracting Shopify stores at specific price points...\n")
    
    stores = extract_stores_by_price()
    
    for price_point, store_list in stores.items():
        print(f"\n{'='*60}")
        print(f"💰 {price_point} GATES ({len(store_list)} found)")
        print(f"{'='*60}")
        
        if store_list:
            for i, store_info in enumerate(store_list[:5], 1):  # Show first 5
                print(f"\n{i}. {store_info['store']}")
                print(f"   Price: ${store_info['price']}")
                print(f"   Product: {store_info['product']}")
        else:
            print("❌ No stores found at this exact price point")
    
    # Save to file
    print(f"\n\n{'='*60}")
    print("💾 Saving results to shopify_price_gates.txt...")
    print(f"{'='*60}\n")
    
    with open('shopify_price_gates.txt', 'w') as f:
        f.write("# Shopify Price Gates for MadyStripe Bot\n")
        f.write("# Generated from 11,419 validated stores\n\n")
        
        for price_point, store_list in stores.items():
            f.write(f"\n{'='*60}\n")
            f.write(f"{price_point} GATES ({len(store_list)} stores)\n")
            f.write(f"{'='*60}\n\n")
            
            if store_list:
                for store_info in store_list:
                    f.write(f"{store_info['store']}\n")
                    f.write(f"  Price: ${store_info['price']}\n")
                    f.write(f"  Product: {store_info['product']}\n\n")
            else:
                f.write("No stores found at this exact price point\n\n")
    
    print("✅ Results saved to shopify_price_gates.txt")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    for price_point, store_list in stores.items():
        print(f"{price_point:8} : {len(store_list):3} stores")

if __name__ == '__main__':
    main()
