#!/usr/bin/env python3
"""
Test gateway with debug output to see what's failing
"""

import sys
sys.path.insert(0, '/home/null/Desktop/MadyStripe')

from core.shopify_gateway_fixed import FixedShopifyGateway
import requests

def test_products_directly():
    """Test if _get_cheapest_product works"""
    print("="*70)
    print("Testing _get_cheapest_product() method")
    print("="*70)
    
    gateway = FixedShopifyGateway("ratterriers.myshopify.com")
    
    # Test the method
    print("\nCalling _get_cheapest_product()...")
    try:
        result = gateway._get_cheapest_product(None)
        print(f"Result: {result}")
        
        if result:
            print(f"✅ Success!")
            print(f"   Variant ID: {result['variant_id']}")
            print(f"   Price: ${result['price']}")
            print(f"   Title: {result['title']}")
        else:
            print(f"❌ Returned None")
            
            # Try manually
            print("\nTrying manually...")
            url = f"https://ratterriers.myshopify.com/products.json"
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                print(f"Products found: {len(products)}")
                
                if products:
                    product = products[0]
                    print(f"First product: {product.get('title')}")
                    if product.get('variants'):
                        variant = product['variants'][0]
                        print(f"First variant ID: {variant.get('id')}")
                        print(f"Price: ${variant.get('price')}")
                        print(f"Available: {variant.get('available')}")
                        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

def test_full_check():
    """Test full card check"""
    print("\n" + "="*70)
    print("Testing full check() method")
    print("="*70)
    
    gateway = FixedShopifyGateway("ratterriers.myshopify.com")
    
    # Test card
    card = "4532015112830366|12|25|123"
    
    print(f"\nChecking card...")
    status, message, card_type = gateway.check(card)
    
    print(f"Status: {status}")
    print(f"Message: {message}")
    print(f"Card Type: {card_type}")

if __name__ == '__main__':
    test_products_directly()
    test_full_check()
