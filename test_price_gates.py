#!/usr/bin/env python3
"""
Test Shopify Price Gates - Validate store availability and products
"""
import requests
import json
import time
from datetime import datetime

# Recommended stores from each price point
TEST_STORES = {
    '0.01': [
        {'store': 'sifrinerias.myshopify.com', 'product': 'Otra cadena'},
        {'store': 'ratterriers.myshopify.com', 'product': 'tshirt'},
        {'store': 'furls.myshopify.com', 'product': 'Stand-up pouches with ziplock'}
    ],
    '5.00': [
        {'store': 'performancetrainingsystems.myshopify.com', 'product': 'Boston Marathon Course Video'},
        {'store': 'escnet.myshopify.com', 'product': 'Vine'},
        {'store': 'liddelton.myshopify.com', 'product': 'The Foolish Spies Tape'}
    ],
    '20.00': [
        {'store': 'tuscanolive.myshopify.com', 'product': 'Ollio Small Bottle'},
        {'store': 'xtremevids.myshopify.com', 'product': 'SX Exposed 1.3'},
        {'store': 'qontent.myshopify.com', 'product': 'TestSchoen'}
    ],
    '100.00': [
        {'store': 'jmsps.myshopify.com', 'product': 'General Services'},
        {'store': 'mitienda.myshopify.com', 'product': 'Otro Producto'},
        {'store': 'electricwheel-store.myshopify.com', 'product': 'Shoescoo Gift Cards'}
    ]
}

def test_store_availability(store_url):
    """Test if store is accessible"""
    try:
        response = requests.get(f"https://{store_url}/products.json", timeout=10)
        return {
            'status': response.status_code,
            'accessible': response.status_code == 200,
            'products_count': len(response.json().get('products', [])) if response.status_code == 200 else 0
        }
    except Exception as e:
        return {
            'status': 'error',
            'accessible': False,
            'error': str(e),
            'products_count': 0
        }

def find_product_in_store(store_url, product_name):
    """Check if specific product exists in store"""
    try:
        response = requests.get(f"https://{store_url}/products.json", timeout=10)
        if response.status_code == 200:
            products = response.json().get('products', [])
            for product in products:
                if product_name.lower() in product.get('title', '').lower():
                    variants = product.get('variants', [])
                    if variants:
                        return {
                            'found': True,
                            'product_id': product.get('id'),
                            'variant_id': variants[0].get('id'),
                            'price': variants[0].get('price'),
                            'available': variants[0].get('available', False)
                        }
            return {'found': False, 'reason': 'Product not found in store'}
        return {'found': False, 'reason': f'Store returned {response.status_code}'}
    except Exception as e:
        return {'found': False, 'reason': str(e)}

def main():
    print("🧪 Testing Shopify Price Gates")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    total_tested = 0
    total_accessible = 0
    total_products_found = 0
    
    for price_point, stores in TEST_STORES.items():
        print(f"\n{'='*70}")
        print(f"💰 Testing ${price_point} Gates")
        print(f"{'='*70}\n")
        
        results[price_point] = []
        
        for i, store_info in enumerate(stores, 1):
            store_url = store_info['store']
            product_name = store_info['product']
            
            print(f"{i}. Testing {store_url}")
            print(f"   Looking for: {product_name}")
            
            # Test store availability
            availability = test_store_availability(store_url)
            
            if availability['accessible']:
                print(f"   ✅ Store accessible (HTTP {availability['status']})")
                print(f"   📦 Products available: {availability['products_count']}")
                total_accessible += 1
                
                # Test product availability
                product_result = find_product_in_store(store_url, product_name)
                
                if product_result['found']:
                    print(f"   ✅ Product found!")
                    print(f"   💵 Price: ${product_result['price']}")
                    print(f"   📊 Available: {product_result['available']}")
                    total_products_found += 1
                else:
                    print(f"   ❌ Product not found: {product_result.get('reason', 'Unknown')}")
                
                results[price_point].append({
                    'store': store_url,
                    'accessible': True,
                    'products_count': availability['products_count'],
                    'product_found': product_result['found'],
                    'product_details': product_result if product_result['found'] else None
                })
            else:
                print(f"   ❌ Store not accessible")
                if 'error' in availability:
                    print(f"   Error: {availability['error']}")
                results[price_point].append({
                    'store': store_url,
                    'accessible': False,
                    'error': availability.get('error', 'Unknown error')
                })
            
            total_tested += 1
            print()
            time.sleep(1)  # Rate limiting
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 TEST SUMMARY")
    print(f"{'='*70}\n")
    print(f"Total stores tested: {total_tested}")
    print(f"Accessible stores: {total_accessible} ({total_accessible/total_tested*100:.1f}%)")
    print(f"Products found: {total_products_found} ({total_products_found/total_tested*100:.1f}%)")
    
    # Recommendations
    print(f"\n{'='*70}")
    print("🎯 RECOMMENDATIONS")
    print(f"{'='*70}\n")
    
    for price_point, store_results in results.items():
        working_stores = [s for s in store_results if s.get('accessible') and s.get('product_found')]
        if working_stores:
            best = working_stores[0]
            print(f"${price_point:6} : {best['store']}")
            if best.get('product_details'):
                print(f"         Price: ${best['product_details']['price']}")
        else:
            accessible = [s for s in store_results if s.get('accessible')]
            if accessible:
                print(f"${price_point:6} : {accessible[0]['store']} (product not found, but store accessible)")
            else:
                print(f"${price_point:6} : ⚠️  No accessible stores found")
    
    # Save results
    with open('price_gates_test_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tested': total_tested,
                'accessible': total_accessible,
                'products_found': total_products_found
            },
            'results': results
        }, f, indent=2)
    
    print(f"\n✅ Results saved to price_gates_test_results.json")
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()
