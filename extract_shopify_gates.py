#!/usr/bin/env python3
"""
Extract Shopify stores at $0.01, $5, $20, and $100 price points
"""
import re

def main():
    print("🔍 Scanning 11,419 stores for specific price points...\n")
    
    stores = {'0.01': [], '5': [], '20': [], '100': []}
    current_store = None
    
    with open('valid_shopify_stores.txt', 'r') as f:
        for line in f:
            line = line.strip()
            
            # Store line
            if '.myshopify.com' in line and not line.startswith('#') and not line.startswith(' '):
                current_store = line
            
            # Price line
            elif line.startswith('Cheapest: $') and current_store:
                match = re.search(r'\$(\d+\.?\d*)', line)
                if match:
                    price = float(match.group(1))
                    product = line.split(' - ', 1)[1] if ' - ' in line else 'Unknown'
                    
                    # Categorize
                    if price == 0.01:
                        stores['0.01'].append((current_store, price, product))
                    elif 4.99 <= price <= 5.01:
                        stores['5'].append((current_store, price, product))
                    elif 19.99 <= price <= 20.01:
                        stores['20'].append((current_store, price, product))
                    elif 99.99 <= price <= 100.01:
                        stores['100'].append((current_store, price, product))
    
    # Display results
    for price_label in ['0.01', '5', '20', '100']:
        print(f"\n{'='*70}")
        print(f"💰 ${price_label} GATES ({len(stores[price_label])} stores found)")
        print(f"{'='*70}")
        
        if stores[price_label]:
            for i, (store, price, product) in enumerate(stores[price_label][:3], 1):
                print(f"\n{i}. {store}")
                print(f"   Price: ${price}")
                print(f"   Product: {product}")
            
            if len(stores[price_label]) > 3:
                print(f"\n   ... and {len(stores[price_label]) - 3} more")
        else:
            print("\n❌ No stores found")
    
    # Save to file
    print(f"\n\n{'='*70}")
    print("💾 Saving to shopify_price_gates.txt...")
    print(f"{'='*70}\n")
    
    with open('shopify_price_gates.txt', 'w') as f:
        f.write("# Shopify Price Gates for MadyStripe Bot\n")
        f.write("# Extracted from 11,419 validated stores\n\n")
        
        for price_label in ['0.01', '5', '20', '100']:
            f.write(f"\n{'='*70}\n")
            f.write(f"${price_label} GATES ({len(stores[price_label])} stores)\n")
            f.write(f"{'='*70}\n\n")
            
            if stores[price_label]:
                for store, price, product in stores[price_label]:
                    f.write(f"{store}\n")
                    f.write(f"  Price: ${price}\n")
                    f.write(f"  Product: {product}\n\n")
    
    print("✅ Complete!")
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}")
    for price_label in ['0.01', '5', '20', '100']:
        print(f"${price_label:6} : {len(stores[price_label]):4} stores")
    
    # Recommendations
    if any(stores.values()):
        print(f"\n{'='*70}")
        print("🎯 RECOMMENDED STORES FOR MADY BOT")
        print(f"{'='*70}\n")
        
        for price_label in ['0.01', '5', '20', '100']:
            if stores[price_label]:
                best = stores[price_label][0]
                print(f"${price_label:6} : {best[0]}")
                print(f"         ${best[1]} - {best[2]}\n")

if __name__ == '__main__':
    main()
