"""
Shopify Smart Gateway
Intelligently selects stores and products, with automatic fallback
Integrates: Store Database + Product Finder + Payment Processor
"""

import time
import random
from typing import Tuple, Optional, Dict, List
from .shopify_store_database import ShopifyStoreDatabase
from .shopify_product_finder import DynamicProductFinder
from .shopify_payment_processor import ShopifyPaymentProcessor


class ShopifySmartGateway:
    """
    Intelligent Shopify gateway with automatic store/product selection and fallback
    """
    
    def __init__(self, target_price: float = 0.01, price_tolerance: float = 0.50):
        """
        Initialize smart gateway
        
        Args:
            target_price: Target price for products (default $0.01)
            price_tolerance: Price tolerance (±)
        """
        self.target_price = target_price
        self.price_tolerance = price_tolerance
        
        # Initialize components
        self.store_db = ShopifyStoreDatabase()
        self.product_finder = DynamicProductFinder()
        self.payment_processor = ShopifyPaymentProcessor()
        
        # Load stores
        self.store_db.load_stores()
        
        # Statistics
        self.total_attempts = 0
        self.successful_charges = 0
        self.failed_stores = set()
    
    def _get_next_store(self, exclude_stores: set = None) -> Optional[Dict]:
        """
        Get next store to try
        
        Args:
            exclude_stores: Set of store URLs to exclude
        
        Returns:
            Store dict or None
        """
        if exclude_stores is None:
            exclude_stores = set()
        
        # Combine with globally failed stores
        all_excluded = exclude_stores | self.failed_stores
        
        # Get stores in price range
        min_price = max(0.01, self.target_price - self.price_tolerance)
        max_price = self.target_price + self.price_tolerance
        
        stores = self.store_db.get_stores_by_price_range(min_price, max_price)
        
        # Filter out excluded stores
        available_stores = [s for s in stores if s['url'] not in all_excluded]
        
        if not available_stores:
            # Try getting any store with products
            all_stores = [s for s in self.store_db.stores if s['url'] not in all_excluded]
            if all_stores:
                return random.choice(all_stores)
            return None
        
        # Prefer stores with higher success rates
        # For now, just return random
        return random.choice(available_stores)
    
    def _find_product_for_store(self, store_url: str) -> Optional[Dict]:
        """
        Find suitable product from store
        
        Args:
            store_url: Store URL
        
        Returns:
            Product dict with variant_id, price, etc.
        """
        try:
            # Try to find product at target price
            product = self.product_finder.find_product_at_price(
                store_url,
                self.target_price,
                self.price_tolerance
            )
            
            if product:
                return product
            
            # Fallback: get cheapest product
            product = self.product_finder.get_cheapest_product(store_url)
            
            return product
            
        except Exception as e:
            print(f"Product finder error for {store_url}: {e}")
            return None
    
    def check(self, card_data: str, max_attempts: int = 3) -> Tuple[str, str, str]:
        """
        Check card with automatic store/product selection and fallback
        
        Args:
            card_data: Card in format "number|month|year|cvv"
            max_attempts: Maximum number of stores to try
        
        Returns:
            (status, message, card_type)
            - status: 'approved', 'declined', or 'error'
            - message: Detailed message
            - card_type: Card brand
        """
        self.total_attempts += 1
        
        # Parse card data
        try:
            parts = card_data.split('|')
            if len(parts) != 4:
                return 'error', 'Invalid card format (use: number|month|year|cvv)', 'Unknown'
            
            card_number, exp_month, exp_year, cvv = parts
            card_number = card_number.strip()
            exp_month = exp_month.strip()
            exp_year = exp_year.strip()
            cvv = cvv.strip()
            
        except Exception as e:
            return 'error', f'Card parsing error: {e}', 'Unknown'
        
        # Try multiple stores if needed
        tried_stores = set()
        last_error = None
        
        for attempt in range(max_attempts):
            # Get next store
            store = self._get_next_store(tried_stores)
            if not store:
                return 'error', 'No available stores', 'Unknown'
            
            store_url = store['url']
            tried_stores.add(store_url)
            
            print(f"\n[Attempt {attempt + 1}/{max_attempts}] Trying store: {store_url}")
            
            try:
                # Find product
                product = self._find_product_for_store(store_url)
                if not product:
                    print(f"  ❌ No suitable products found")
                    self.store_db.mark_store_failed(store_url)
                    self.failed_stores.add(store_url)
                    continue
                
                variant_id = product['variant_id']
                product_price = product['price']
                product_name = product['title']
                
                print(f"  ✅ Found product: {product_name} (${product_price})")
                print(f"  🔄 Processing payment...")
                
                # Process payment
                status, message, card_type = self.payment_processor.process_card(
                    f"https://{store_url}",
                    variant_id,
                    card_number,
                    exp_month,
                    exp_year,
                    cvv
                )
                
                # Handle result
                if status == 'approved':
                    print(f"  ✅ APPROVED!")
                    self.successful_charges += 1
                    self.store_db.mark_store_success(store_url)
                    return status, f"{message} | Store: {store_url} | Product: {product_name} (${product_price})", card_type
                
                elif status == 'declined':
                    print(f"  ❌ DECLINED: {message}")
                    # Card was declined - don't try other stores
                    return status, message, card_type
                
                else:  # error
                    print(f"  ⚠️  ERROR: {message}")
                    last_error = message
                    # Try next store
                    continue
                
            except Exception as e:
                print(f"  ⚠️  Exception: {e}")
                last_error = str(e)
                continue
        
        # All attempts failed
        return 'error', f'All stores failed. Last error: {last_error}', 'Unknown'
    
    def get_stats(self) -> Dict:
        """Get gateway statistics"""
        return {
            'total_attempts': self.total_attempts,
            'successful_charges': self.successful_charges,
            'success_rate': f"{(self.successful_charges / self.total_attempts * 100):.1f}%" if self.total_attempts > 0 else "0%",
            'failed_stores': len(self.failed_stores),
            'available_stores': len(self.store_db.stores) - len(self.failed_stores),
        }


class ShopifyPennyGate(ShopifySmartGateway):
    """Penny gate ($0.01 - $1.00)"""
    def __init__(self):
        super().__init__(target_price=0.01, price_tolerance=0.99)


class ShopifyFiveDollarGate(ShopifySmartGateway):
    """$5 gate"""
    def __init__(self):
        super().__init__(target_price=5.00, price_tolerance=2.00)


class ShopifyTwentyDollarGate(ShopifySmartGateway):
    """$20 gate"""
    def __init__(self):
        super().__init__(target_price=20.00, price_tolerance=5.00)


class ShopifyHundredDollarGate(ShopifySmartGateway):
    """$100 gate"""
    def __init__(self):
        super().__init__(target_price=100.00, price_tolerance=20.00)


if __name__ == "__main__":
    print("="*70)
    print("SHOPIFY SMART GATEWAY TEST")
    print("="*70)
    
    # Test penny gate
    print("\n🪙 Testing Penny Gate ($0.01 - $1.00)")
    print("-" * 70)
    
    gateway = ShopifyPennyGate()
    
    # Test with a card (will be declined)
    test_card = "4111111111111111|12|25|123"
    
    print(f"\nTesting card: {test_card[:4]}...{test_card[-7:]}")
    print()
    
    status, message, card_type = gateway.check(test_card, max_attempts=2)
    
    print(f"\n{'='*70}")
    print(f"RESULT:")
    print(f"  Status: {status}")
    print(f"  Message: {message}")
    print(f"  Card Type: {card_type}")
    print(f"{'='*70}")
    
    # Show stats
    stats = gateway.get_stats()
    print(f"\nGateway Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
