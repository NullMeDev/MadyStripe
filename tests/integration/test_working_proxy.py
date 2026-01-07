"""
Quick test of working proxy with Shopify stores
"""

from core.shopify_simple_gateway import SimpleShopifyGateway
import time

def test_proxy():
    print("="*70)
    print("TESTING WORKING PROXY WITH SHOPIFY STORES")
    print("="*70)
    
    # Load proxy
    with open('proxies.txt', 'r') as f:
        proxy = f.read().strip()
    
    print(f"\n✅ Loaded proxy: {proxy.split(':')[0]}:{proxy.split(':')[1]}")
    
    # Test stores
    test_stores = [
        'sifrinerias.myshopify.com',
        'premium.myshopify.com',
        'viltrox.com',
        'goods.myshopify.com',
        'lehsoap.com'
    ]
    
    print(f"\n🔍 Testing {len(test_stores)} stores with proxy...")
    print("-"*70)
    
    working_stores = []
    
    for i, store in enumerate(test_stores, 1):
        print(f"\n[{i}/{len(test_stores)}] Testing: {store}")
        
        try:
            gateway = SimpleShopifyGateway(proxy=proxy)
            
            # Try to get product
            product = gateway._get_cheapest_product(store)
            if not product:
                print(f"  ❌ No products found")
                continue
            
            print(f"  ✅ Found product: {product['title']} (${product['price']})")
            
            # Try to create checkout
            checkout = gateway._create_checkout(store, product['variant_id'])
            if not checkout:
                print(f"  ⚠️  Checkout creation failed")
                continue
            
            print(f"  ✅ CHECKOUT WORKS! This store is usable!")
            working_stores.append({
                'url': store,
                'product': product['title'],
                'price': product['price']
            })
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        time.sleep(2)
    
    # Summary
    print(f"\n{'='*70}")
    print(f"RESULTS:")
    print(f"  Tested: {len(test_stores)}")
    print(f"  Working: {len(working_stores)}")
    print(f"{'='*70}")
    
    if working_stores:
        print(f"\n🎉 Found {len(working_stores)} working store(s)!")
        for store in working_stores:
            print(f"  • {store['url']}")
            print(f"    Product: {store['product']} (${store['price']})")
    else:
        print(f"\n⚠️  No working stores found in this batch")
        print(f"  Recommendation: Use Stripe gates instead (they work reliably)")

if __name__ == "__main__":
    test_proxy()
