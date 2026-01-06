"""
Find Working Shopify Stores
Tests stores with proxies to identify which ones allow checkout
Saves working stores to a file for future use
"""

import time
import json
import random
from core.shopify_simple_gateway import SimpleShopifyGateway


def load_proxies(filename='proxies.txt'):
    """Load proxies from file"""
    try:
        with open(filename, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies
    except:
        return []


def load_stores(filename='valid_shopify_stores_urls_only.txt'):
    """Load stores from file"""
    try:
        with open(filename, 'r') as f:
            stores = [line.strip() for line in f if line.strip()]
        return stores
    except:
        return []


def test_store_checkout(store_url, proxy=None):
    """
    Test if a store allows checkout creation
    Returns: (success, has_products, checkout_works, error_msg)
    """
    try:
        gateway = SimpleShopifyGateway(proxy=proxy)
        
        # Get product
        product = gateway._get_cheapest_product(store_url)
        if not product:
            return False, False, False, "No products"
        
        # Try to create checkout
        checkout = gateway._create_checkout(store_url, product['variant_id'])
        if not checkout:
            return False, True, False, "Checkout failed"
        
        # Success!
        return True, True, True, f"Works! Product: {product['title']} (${product['price']})"
        
    except Exception as e:
        return False, False, False, f"Error: {str(e)}"


def main():
    print("="*80)
    print("SHOPIFY STORE FINDER - Find Working Stores with Proxies")
    print("="*80)
    
    # Load resources
    print("\n[1/5] Loading resources...")
    proxies = load_proxies()
    stores = load_stores()
    
    print(f"  ✅ Loaded {len(proxies)} proxies")
    print(f"  ✅ Loaded {len(stores)} stores")
    
    if not proxies:
        print("  ⚠️  No proxies found, testing without proxy")
        proxies = [None]
    
    if not stores:
        print("  ❌ No stores found!")
        return
    
    # Test configuration
    stores_to_test = 100  # Test first 100 stores
    test_stores = random.sample(stores, min(stores_to_test, len(stores)))
    
    print(f"\n[2/5] Testing {len(test_stores)} random stores...")
    print(f"  Using {len(proxies)} proxy/proxies")
    print(f"  This will take approximately {len(test_stores) * 10 / 60:.1f} minutes")
    
    # Results tracking
    working_stores = []
    stores_with_products = []
    failed_stores = []
    
    # Test stores
    print(f"\n[3/5] Testing stores...")
    print("-"*80)
    
    for i, store in enumerate(test_stores, 1):
        # Rotate through proxies
        proxy = proxies[(i-1) % len(proxies)] if proxies[0] is not None else None
        
        print(f"\n[{i}/{len(test_stores)}] Testing: {store}")
        if proxy:
            proxy_host = proxy.split(':')[0]
            print(f"  Using proxy: {proxy_host}")
        
        success, has_products, checkout_works, msg = test_store_checkout(store, proxy)
        
        if success:
            print(f"  ✅ WORKING! {msg}")
            working_stores.append({
                'url': store,
                'message': msg,
                'proxy_used': proxy_host if proxy else 'none'
            })
        elif has_products:
            print(f"  ⚠️  Has products but checkout failed")
            stores_with_products.append(store)
        else:
            print(f"  ❌ {msg}")
            failed_stores.append(store)
        
        # Rate limiting
        time.sleep(2)
    
    # Save results
    print(f"\n[4/5] Saving results...")
    
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_tested': len(test_stores),
        'working_stores': working_stores,
        'stores_with_products': stores_with_products,
        'failed_stores': failed_stores,
        'proxies_used': len(proxies)
    }
    
    # Save to JSON
    with open('working_stores_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"  ✅ Saved to working_stores_results.json")
    
    # Save working stores to text file
    if working_stores:
        with open('working_shopify_stores.txt', 'w') as f:
            for store in working_stores:
                f.write(f"{store['url']}\n")
        print(f"  ✅ Saved {len(working_stores)} working stores to working_shopify_stores.txt")
    
    # Print summary
    print(f"\n[5/5] Summary")
    print("="*80)
    print(f"Total Tested: {len(test_stores)}")
    print(f"✅ Working Stores: {len(working_stores)} ({len(working_stores)/len(test_stores)*100:.1f}%)")
    print(f"⚠️  Stores with Products (checkout failed): {len(stores_with_products)} ({len(stores_with_products)/len(test_stores)*100:.1f}%)")
    print(f"❌ Failed Stores: {len(failed_stores)} ({len(failed_stores)/len(test_stores)*100:.1f}%)")
    print("="*80)
    
    if working_stores:
        print(f"\n🎉 Found {len(working_stores)} working stores!")
        print("\nWorking Stores:")
        for store in working_stores[:10]:  # Show first 10
            print(f"  • {store['url']}")
            print(f"    {store['message']}")
        if len(working_stores) > 10:
            print(f"  ... and {len(working_stores) - 10} more")
    else:
        print("\n⚠️  No working stores found in this batch.")
        print("Recommendations:")
        print("  1. Try testing more stores (increase stores_to_test)")
        print("  2. Try different proxies")
        print("  3. Test at different times (stores may have rate limiting)")
        print("  4. Consider using Stripe gates instead (they work reliably)")
    
    print(f"\n📄 Full results saved to: working_stores_results.json")


if __name__ == "__main__":
    main()
