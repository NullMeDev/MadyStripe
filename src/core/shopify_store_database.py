"""
Shopify Store Database Manager
Manages 11,419 validated Shopify stores with dynamic product selection
"""

import os
import json
import time
import random
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta


class ShopifyStoreDatabase:
    """
    Manages validated Shopify stores with intelligent selection and fallback
    """
    
    def __init__(self, stores_file: str = "valid_shopify_stores.txt"):
        self.stores_file = stores_file
        self.stores = []  # List of {url, products, cheapest_price}
        self.failed_stores = {}  # {url: last_failed_time}
        self.success_rates = {}  # {url: success_count}
        self.cache_file = "shopify_store_cache.json"
        self.load_stores()
    
    def load_stores(self):
        """Load stores from valid_shopify_stores.txt"""
        if not os.path.exists(self.stores_file):
            print(f"⚠️ Warning: {self.stores_file} not found")
            return
        
        # Try to load from cache first
        if self._load_from_cache():
            print(f"✅ Loaded {len(self.stores)} stores from cache")
            return
        
        # Parse stores file
        print(f"📁 Parsing {self.stores_file}...")
        current_store = None
        
        with open(self.stores_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip header lines
                if line.startswith('Valid Shopify Stores') or line.startswith('Total:'):
                    continue
                
                # Check if this is a store URL
                if '.myshopify.com' in line and not line.startswith(' '):
                    if current_store:
                        self.stores.append(current_store)
                    
                    current_store = {
                        'url': line,
                        'products': 0,
                        'cheapest_price': None,
                        'cheapest_product': None
                    }
                
                # Parse product count (with flexible spacing)
                elif 'Products:' in line and current_store:
                    try:
                        current_store['products'] = int(line.split(':')[1].strip())
                    except:
                        pass
                
                # Parse cheapest product (with flexible spacing)
                elif 'Cheapest:' in line and '$' in line and current_store:
                    try:
                        # Format: "  Cheapest: $19.0 - Product Name"
                        parts = line.split('$')[1].split(' - ')
                        price = float(parts[0].strip())
                        product_name = parts[1].strip() if len(parts) > 1 else "Unknown"
                        
                        current_store['cheapest_price'] = price
                        current_store['cheapest_product'] = product_name
                    except Exception as e:
                        pass
            
            # Add last store
            if current_store:
                self.stores.append(current_store)
        
        print(f"✅ Loaded {len(self.stores)} stores")
        
        # Save to cache
        self._save_to_cache()
    
    def _load_from_cache(self) -> bool:
        """Load stores from cache if available and recent"""
        if not os.path.exists(self.cache_file):
            return False
        
        try:
            # Check if cache is less than 24 hours old
            cache_age = time.time() - os.path.getmtime(self.cache_file)
            if cache_age > 86400:  # 24 hours
                return False
            
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                self.stores = data.get('stores', [])
                self.failed_stores = data.get('failed_stores', {})
                self.success_rates = data.get('success_rates', {})
            
            return len(self.stores) > 0
        except:
            return False
    
    def _save_to_cache(self):
        """Save stores to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump({
                    'stores': self.stores,
                    'failed_stores': self.failed_stores,
                    'success_rates': self.success_rates,
                    'updated': datetime.now().isoformat()
                }, f)
        except Exception as e:
            print(f"⚠️ Failed to save cache: {e}")
    
    def get_stores_by_price_range(self, min_price: float, max_price: float, limit: int = 50) -> List[Dict]:
        """
        Find stores with products in the specified price range (alias for find_stores_by_price)
        
        Args:
            min_price: Minimum price
            max_price: Maximum price
            limit: Maximum number of stores to return
        
        Returns:
            List of store dictionaries
        """
        return self.find_stores_by_price(min_price, max_price, limit)
    
    def find_stores_by_price(self, min_price: float, max_price: float, limit: int = 50) -> List[Dict]:
        """
        Find stores with products in the specified price range
        
        Args:
            min_price: Minimum price
            max_price: Maximum price
            limit: Maximum number of stores to return
        
        Returns:
            List of store dictionaries
        """
        matching_stores = []
        
        for store in self.stores:
            if store['cheapest_price'] is None:
                continue
            
            price = store['cheapest_price']
            if min_price <= price <= max_price:
                # Skip recently failed stores
                if not self._is_store_failed(store['url']):
                    matching_stores.append(store)
        
        # Sort by success rate (if available) and price
        matching_stores.sort(key=lambda s: (
            -self.success_rates.get(s['url'], 0),  # Higher success rate first
            s['cheapest_price']  # Lower price first
        ))
        
        return matching_stores[:limit]
    
    def get_random_store(self, price_range: str = "any") -> Optional[Dict]:
        """
        Get a random working store
        
        Args:
            price_range: "penny" ($0.01-$1), "low" ($1-$10), "medium" ($10-$50), 
                        "high" ($50+), or "any"
        
        Returns:
            Store dictionary or None
        """
        price_ranges = {
            "penny": (0.01, 1.00),
            "low": (1.00, 10.00),
            "medium": (10.00, 50.00),
            "high": (50.00, 1000.00),
            "any": (0.01, 1000.00)
        }
        
        min_price, max_price = price_ranges.get(price_range, (0.01, 1000.00))
        stores = self.find_stores_by_price(min_price, max_price, limit=100)
        
        if not stores:
            return None
        
        # Return random store from top 20 (for load balancing)
        return random.choice(stores[:min(20, len(stores))])
    
    def get_store_at_price(self, target_price: float, tolerance: float = 0.50) -> Optional[Dict]:
        """
        Find a store with a product close to the target price
        
        Args:
            target_price: Desired price
            tolerance: Price tolerance (e.g., 0.50 = ±$0.50)
        
        Returns:
            Store dictionary or None
        """
        min_price = max(0.01, target_price - tolerance)
        max_price = target_price + tolerance
        
        stores = self.find_stores_by_price(min_price, max_price, limit=10)
        
        if not stores:
            return None
        
        # Return store with price closest to target
        stores.sort(key=lambda s: abs(s['cheapest_price'] - target_price))
        return stores[0]
    
    def mark_store_failed(self, store_url: str):
        """Mark a store as failed (temporarily blacklist)"""
        self.failed_stores[store_url] = time.time()
        self._save_to_cache()
    
    def mark_store_success(self, store_url: str):
        """Mark a store as successful"""
        self.success_rates[store_url] = self.success_rates.get(store_url, 0) + 1
        
        # Remove from failed list if present
        if store_url in self.failed_stores:
            del self.failed_stores[store_url]
        
        self._save_to_cache()
    
    def _is_store_failed(self, store_url: str) -> bool:
        """Check if store recently failed (within last hour)"""
        if store_url not in self.failed_stores:
            return False
        
        failed_time = self.failed_stores[store_url]
        time_since_failure = time.time() - failed_time
        
        # Blacklist for 1 hour
        if time_since_failure < 3600:
            return True
        
        # Remove from failed list after 1 hour
        del self.failed_stores[store_url]
        return False
    
    def get_working_stores(self, limit: int = 100) -> List[Dict]:
        """Get list of working stores (not recently failed)"""
        working = []
        
        for store in self.stores:
            if not self._is_store_failed(store['url']):
                working.append(store)
            
            if len(working) >= limit:
                break
        
        return working
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        total_stores = len(self.stores)
        failed_stores = len([url for url in self.failed_stores.keys() 
                           if self._is_store_failed(url)])
        working_stores = total_stores - failed_stores
        
        # Price distribution
        prices = [s['cheapest_price'] for s in self.stores if s['cheapest_price']]
        
        return {
            'total_stores': total_stores,
            'working_stores': working_stores,
            'failed_stores': failed_stores,
            'avg_price': sum(prices) / len(prices) if prices else 0,
            'min_price': min(prices) if prices else 0,
            'max_price': max(prices) if prices else 0,
            'stores_with_success': len(self.success_rates)
        }


if __name__ == "__main__":
    print("="*70)
    print("SHOPIFY STORE DATABASE TEST")
    print("="*70)
    
    db = ShopifyStoreDatabase()
    
    print(f"\n📊 Database Stats:")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n💰 Finding stores by price range:")
    
    # Test penny range
    penny_stores = db.find_stores_by_price(0.01, 1.00, limit=5)
    print(f"\n  Penny ($0.01-$1.00): {len(penny_stores)} stores")
    for store in penny_stores[:3]:
        print(f"    - {store['url']}: ${store['cheapest_price']}")
    
    # Test low range
    low_stores = db.find_stores_by_price(1.00, 10.00, limit=5)
    print(f"\n  Low ($1-$10): {len(low_stores)} stores")
    for store in low_stores[:3]:
        print(f"    - {store['url']}: ${store['cheapest_price']}")
    
    # Test specific price
    print(f"\n🎯 Finding store at $5.00:")
    store = db.get_store_at_price(5.00, tolerance=0.50)
    if store:
        print(f"  Found: {store['url']} (${store['cheapest_price']})")
    
    # Test random selection
    print(f"\n🎲 Random store selection:")
    random_store = db.get_random_store("low")
    if random_store:
        print(f"  {random_store['url']}: ${random_store['cheapest_price']}")
    
    print(f"\n✅ Store database ready!")
