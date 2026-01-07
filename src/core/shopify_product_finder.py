"""
Shopify Dynamic Product Finder
Finds products at any price point from Shopify stores in real-time
"""

import requests
import time
import random
from typing import Optional, Dict, List, Tuple


class DynamicProductFinder:
    """
    Dynamically finds products from Shopify stores at specified price points
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
        self.cache = {}  # {store_url: {products, timestamp}}
        self.cache_duration = 3600  # 1 hour
    
    def get_products(self, store_url: str, use_cache: bool = True) -> Optional[List[Dict]]:
        """
        Get all products from a Shopify store
        
        Args:
            store_url: Store URL (e.g., 'example.myshopify.com')
            use_cache: Whether to use cached results
        
        Returns:
            List of product dictionaries or None if failed
        """
        # Clean URL
        store_url = store_url.replace('https://', '').replace('http://', '').strip('/')
        
        # Check cache
        if use_cache and store_url in self.cache:
            cached_data = self.cache[store_url]
            age = time.time() - cached_data['timestamp']
            if age < self.cache_duration:
                return cached_data['products']
        
        try:
            # Fetch products from Shopify API
            url = f"https://{store_url}/products.json"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            products = data.get('products', [])
            
            # Cache results
            self.cache[store_url] = {
                'products': products,
                'timestamp': time.time()
            }
            
            return products
            
        except Exception as e:
            return None
    
    def find_product_at_price(self, store_url: str, target_price: float, 
                             tolerance: float = 0.50) -> Optional[Dict]:
        """
        Find a product at a specific price point
        
        Args:
            store_url: Store URL
            target_price: Target price
            tolerance: Price tolerance (±)
        
        Returns:
            Product info dict or None
        """
        products = self.get_products(store_url)
        if not products:
            return None
        
        min_price = max(0.01, target_price - tolerance)
        max_price = target_price + tolerance
        
        matching_products = []
        
        for product in products:
            for variant in product.get('variants', []):
                try:
                    price = float(variant.get('price', 0))
                    
                    if min_price <= price <= max_price:
                        matching_products.append({
                            'product_id': product['id'],
                            'variant_id': variant['id'],
                            'title': product['title'],
                            'variant_title': variant.get('title', 'Default'),
                            'price': price,
                            'available': variant.get('available', False),
                            'image': product.get('images', [{}])[0].get('src', ''),
                        })
                except:
                    continue
        
        if not matching_products:
            return None
        
        # Sort by price difference from target
        matching_products.sort(key=lambda p: abs(p['price'] - target_price))
        
        # Return closest match that's available
        for product in matching_products:
            if product['available']:
                return product
        
        # If none available, return closest anyway
        return matching_products[0] if matching_products else None
    
    def get_cheapest_product(self, store_url: str) -> Optional[Dict]:
        """
        Get the cheapest available product from a store
        
        Args:
            store_url: Store URL
        
        Returns:
            Product info dict or None
        """
        products = self.get_products(store_url)
        if not products:
            return None
        
        all_variants = []
        
        for product in products:
            for variant in product.get('variants', []):
                try:
                    price = float(variant.get('price', 0))
                    
                    if price > 0:  # Skip free products
                        all_variants.append({
                            'product_id': product['id'],
                            'variant_id': variant['id'],
                            'title': product['title'],
                            'variant_title': variant.get('title', 'Default'),
                            'price': price,
                            'available': variant.get('available', False),
                            'image': product.get('images', [{}])[0].get('src', ''),
                        })
                except:
                    continue
        
        if not all_variants:
            return None
        
        # Sort by price
        all_variants.sort(key=lambda v: v['price'])
        
        # Return cheapest available product
        for variant in all_variants:
            if variant['available']:
                return variant
        
        # If none available, return cheapest anyway
        return all_variants[0] if all_variants else None
    
    def get_product_in_range(self, store_url: str, min_price: float, 
                            max_price: float) -> Optional[Dict]:
        """
        Get a random product within a price range
        
        Args:
            store_url: Store URL
            min_price: Minimum price
            max_price: Maximum price
        
        Returns:
            Product info dict or None
        """
        products = self.get_products(store_url)
        if not products:
            return None
        
        matching_variants = []
        
        for product in products:
            for variant in product.get('variants', []):
                try:
                    price = float(variant.get('price', 0))
                    
                    if min_price <= price <= max_price:
                        matching_variants.append({
                            'product_id': product['id'],
                            'variant_id': variant['id'],
                            'title': product['title'],
                            'variant_title': variant.get('title', 'Default'),
                            'price': price,
                            'available': variant.get('available', False),
                            'image': product.get('images', [{}])[0].get('src', ''),
                        })
                except:
                    continue
        
        if not matching_variants:
            return None
        
        # Filter available products
        available = [v for v in matching_variants if v['available']]
        
        if available:
            return random.choice(available)
        
        # If none available, return random anyway
        return random.choice(matching_variants) if matching_variants else None
    
    def validate_product_available(self, store_url: str, variant_id: int) -> bool:
        """
        Check if a specific product variant is still available
        
        Args:
            store_url: Store URL
            variant_id: Variant ID to check
        
        Returns:
            True if available, False otherwise
        """
        products = self.get_products(store_url, use_cache=False)  # Don't use cache
        if not products:
            return False
        
        for product in products:
            for variant in product.get('variants', []):
                if variant['id'] == variant_id:
                    return variant.get('available', False)
        
        return False
    
    def get_product_details(self, store_url: str, variant_id: int) -> Optional[Dict]:
        """
        Get detailed information about a specific product variant
        
        Args:
            store_url: Store URL
            variant_id: Variant ID
        
        Returns:
            Product info dict or None
        """
        products = self.get_products(store_url)
        if not products:
            return None
        
        for product in products:
            for variant in product.get('variants', []):
                if variant['id'] == variant_id:
                    return {
                        'product_id': product['id'],
                        'variant_id': variant['id'],
                        'title': product['title'],
                        'variant_title': variant.get('title', 'Default'),
                        'price': float(variant.get('price', 0)),
                        'available': variant.get('available', False),
                        'image': product.get('images', [{}])[0].get('src', ''),
                        'sku': variant.get('sku', ''),
                        'requires_shipping': variant.get('requires_shipping', True),
                    }
        
        return None


if __name__ == "__main__":
    print("="*70)
    print("SHOPIFY DYNAMIC PRODUCT FINDER TEST")
    print("="*70)
    
    finder = DynamicProductFinder()
    
    # Test with a known store
    test_store = "sifrinerias.myshopify.com"
    
    print(f"\n🔍 Testing with store: {test_store}")
    
    # Get all products
    print(f"\n📦 Fetching all products...")
    products = finder.get_products(test_store)
    if products:
        print(f"  Found {len(products)} products")
        for i, product in enumerate(products[:3], 1):
            print(f"  {i}. {product['title']}")
            variants = product.get('variants', [])
            if variants:
                print(f"     Price: ${variants[0].get('price', 'N/A')}")
    
    # Get cheapest product
    print(f"\n💰 Finding cheapest product...")
    cheapest = finder.get_cheapest_product(test_store)
    if cheapest:
        print(f"  Product: {cheapest['title']}")
        print(f"  Variant: {cheapest['variant_title']}")
        print(f"  Price: ${cheapest['price']}")
        print(f"  Available: {cheapest['available']}")
        print(f"  Variant ID: {cheapest['variant_id']}")
    
    # Find product at specific price
    print(f"\n🎯 Finding product at $5.00...")
    product_5 = finder.find_product_at_price(test_store, 5.00, tolerance=2.00)
    if product_5:
        print(f"  Product: {product_5['title']}")
        print(f"  Price: ${product_5['price']}")
        print(f"  Variant ID: {product_5['variant_id']}")
    else:
        print(f"  No products found at $5.00")
    
    # Get product in range
    print(f"\n📊 Finding product in range $1-$10...")
    product_range = finder.get_product_in_range(test_store, 1.00, 10.00)
    if product_range:
        print(f"  Product: {product_range['title']}")
        print(f"  Price: ${product_range['price']}")
    
    print(f"\n✅ Product finder ready!")
