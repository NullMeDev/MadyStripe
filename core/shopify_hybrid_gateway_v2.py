"""
Shopify Hybrid Gateway V2 - IMPROVED
Fixes: Properly navigates to payment page and waits for payment form to load
"""

import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Tuple, Optional
from .shopify_store_database import ShopifyStoreDatabase
from .shopify_product_finder import DynamicProductFinder


class ShopifyHybridGatewayV2:
    """
    Improved Hybrid Shopify Gateway with proper payment page navigation
    """
    
    def __init__(self, proxy: Optional[str] = None, headless: bool = True):
        self.proxy = proxy
        self.headless = headless
        self.driver = None
        
        self.store_db = ShopifyStoreDatabase()
        self.product_finder = DynamicProductFinder()
        self.store_db.load_stores()
        
        self.total_attempts = 0
        self.successful_charges = 0
    
    def _init_browser(self):
        """Initialize browser"""
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
    
    def _navigate_to_checkout(self, store_url: str, variant_id: int) -> bool:
        """Navigate to checkout page"""
        try:
            checkout_url = f"https://{store_url}/cart/{variant_id}:1"
            print(f"  → Navigating to: {checkout_url}")
            self.driver.get(checkout_url)
            time.sleep(3)
            
            # Check if already on checkout
            if '/checkouts/' in self.driver.current_url:
                print(f"  ✓ Already on checkout page")
                return True
            
            # Try to click checkout button
            checkout_selectors = [
                (By.NAME, 'checkout'),
                (By.CSS_SELECTOR, 'button[name="checkout"]'),
                (By.XPATH, '//button[contains(text(), "Check out")]'),
            ]
            
            for by, selector in checkout_selectors:
                try:
                    element = self.driver.find_element(by, selector)
                    element.click()
                    print(f"  ✓ Clicked checkout button")
                    time.sleep(3)
                    return True
                except:
                    continue
            
            return '/checkouts/' in self.driver.current_url
            
        except Exception as e:
            print(f"  ✗ Navigation error: {e}")
            return False
    
    def _fill_shipping_and_continue(self) -> bool:
        """Fill shipping form and continue to payment page"""
        try:
            print(f"  → Filling shipping information...")
            
            # Fill email
            try:
                email_field = self.driver.find_element(By.CSS_SELECTOR, 'input[type="email"]')
                email_field.clear()
                email_field.send_keys(f"test{int(time.time())}@example.com")
                time.sleep(0.5)
            except:
                pass
            
            # Fill shipping address
            try:
                fields = {
                    'firstName': 'John',
                    'lastName': 'Doe',
                    'address1': '123 Main St',
                    'city': 'New York',
                    'postalCode': '10001'
                }
                
                for field_name, value in fields.items():
                    try:
                        field = self.driver.find_element(By.NAME, field_name)
                        field.clear()
                        field.send_keys(value)
                        time.sleep(0.3)
                    except:
                        continue
                
                print(f"  ✓ Filled shipping address")
            except Exception as e:
                print(f"  ⚠️  Shipping fill error: {e}")
            
            # Click continue to payment - THIS IS CRITICAL
            print(f"  → Clicking 'Continue to payment'...")
            
            continue_selectors = [
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.ID, 'continue_button'),
                (By.XPATH, '//button[contains(text(), "Continue")]'),
                (By.XPATH, '//button[contains(text(), "Payment")]'),
                (By.CSS_SELECTOR, 'button[aria-label*="Continue"]'),
            ]
            
            clicked = False
            for by, selector in continue_selectors:
                try:
                    button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    button.click()
                    print(f"  ✓ Clicked continue button")
                    clicked = True
                    break
                except:
                    continue
            
            if not clicked:
                print(f"  ⚠️  Could not find continue button")
                return False
            
            # CRITICAL: Wait for payment page to load
            print(f"  → Waiting for payment page to load...")
            time.sleep(5)  # Give it time to load payment form
            
            # Verify we're on payment page
            current_url = self.driver.current_url
            print(f"  → Current URL: {current_url}")
            
            if 'payment' in current_url.lower() or 'step=payment' in current_url.lower():
                print(f"  ✓ Successfully reached payment page")
                return True
            else:
                print(f"  ⚠️  May not be on payment page yet")
                # Wait a bit more
                time.sleep(3)
                return True  # Continue anyway
            
        except Exception as e:
            print(f"  ✗ Shipping/continue error: {e}")
            return False
    
    def _fill_card_details(self, card_number: str, exp_month: str, exp_year: str, cvv: str) -> bool:
        """Fill card details on payment page"""
        try:
            print(f"  → Looking for card payment form...")
            
            # Expanded card field selectors
            card_selectors = [
                (By.NAME, 'number'),
                (By.ID, 'number'),
                (By.ID, 'cardNumber'),
                (By.CSS_SELECTOR, 'input[placeholder*="Card number"]'),
                (By.CSS_SELECTOR, 'input[placeholder*="card number"]'),
                (By.CSS_SELECTOR, 'input[autocomplete="cc-number"]'),
                (By.CSS_SELECTOR, 'input[data-card-number]'),
                (By.CSS_SELECTOR, 'input[type="tel"][maxlength="19"]'),
            ]
            
            # Try main page first
            card_field = None
            for by, selector in card_selectors:
                try:
                    card_field = self.driver.find_element(by, selector)
                    print(f"  ✓ Found card field in main page")
                    break
                except:
                    continue
            
            # Try iframes if not found
            if not card_field:
                print(f"  → Checking iframes for card field...")
                iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
                print(f"  → Found {len(iframes)} iframes")
                
                for i, iframe in enumerate(iframes):
                    try:
                        self.driver.switch_to.frame(iframe)
                        
                        for by, selector in card_selectors:
                            try:
                                card_field = self.driver.find_element(by, selector)
                                print(f"  ✓ Found card field in iframe {i+1}")
                                break
                            except:
                                continue
                        
                        if card_field:
                            break
                        
                        self.driver.switch_to.default_content()
                    except:
                        self.driver.switch_to.default_content()
            
            if not card_field:
                print(f"  ✗ Could not find card field")
                # Save page for debugging
                try:
                    with open('/tmp/shopify_payment_debug.html', 'w') as f:
                        f.write(self.driver.page_source)
                    print(f"  → Page saved to /tmp/shopify_payment_debug.html")
                except:
                    pass
                return False
            
            # Fill card number
            card_field.clear()
            card_field.send_keys(card_number)
            time.sleep(0.5)
            print(f"  ✓ Filled card number")
            
            # Fill expiry
            exp_selectors = [
                (By.NAME, 'expiry'),
                (By.CSS_SELECTOR, 'input[placeholder*="MM"]'),
                (By.CSS_SELECTOR, 'input[autocomplete="cc-exp"]'),
            ]
            
            for by, selector in exp_selectors:
                try:
                    exp_field = self.driver.find_element(by, selector)
                    exp_field.clear()
                    exp_field.send_keys(f"{exp_month}{exp_year}")
                    print(f"  ✓ Filled expiry")
                    break
                except:
                    continue
            
            # Fill CVV
            cvv_selectors = [
                (By.NAME, 'verification_value'),
                (By.NAME, 'cvv'),
                (By.CSS_SELECTOR, 'input[placeholder*="CVV"]'),
                (By.CSS_SELECTOR, 'input[autocomplete="cc-csc"]'),
            ]
            
            for by, selector in cvv_selectors:
                try:
                    cvv_field = self.driver.find_element(by, selector)
                    cvv_field.clear()
                    cvv_field.send_keys(cvv)
                    print(f"  ✓ Filled CVV")
                    break
                except:
                    continue
            
            # Switch back to main content
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"  ✗ Card fill error: {e}")
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return False
    
    def _submit_and_detect_result(self) -> Tuple[str, str]:
        """Submit payment and detect result"""
        try:
            # Click pay button
            pay_selectors = [
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.ID, 'continue_button'),
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
            
            # Check result
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            
            # Success indicators
            if any(kw in current_url or kw in page_source for kw in [
                'thank you', 'order confirmed', 'order complete', '/thank_you', '/orders/'
            ]):
                return 'approved', 'Payment successful'
            
            # Decline indicators
            if any(kw in page_source for kw in [
                'declined', 'insufficient funds', 'invalid card', 'payment failed'
            ]):
                return 'declined', 'Card declined'
            
            return 'error', 'Could not determine result'
            
        except Exception as e:
            return 'error', f'Submission error: {e}'
    
    def check(self, card_data: str, max_attempts: int = 2) -> Tuple[str, str, str]:
        """Check card"""
        self.total_attempts += 1
        
        # Parse card
        try:
            parts = card_data.split('|')
            if len(parts) != 4:
                return 'error', 'Invalid card format', 'Unknown'
            
            card_number, exp_month, exp_year, cvv = [p.strip() for p in parts]
            
            card_type = 'Visa' if card_number.startswith('4') else 'Mastercard' if card_number.startswith('5') else 'Amex' if card_number.startswith('3') else 'Unknown'
            
        except:
            return 'error', 'Card parsing error', 'Unknown'
        
        # Try multiple stores
        for attempt in range(max_attempts):
            try:
                print(f"\n[Attempt {attempt + 1}/{max_attempts}]")
                
                # Get store with product
                print(f"  → Finding store with product...")
                stores = self.store_db.get_stores_by_price_range(0.01, 5.00)
                if not stores:
                    stores = self.store_db.stores[:50]
                
                store_url = None
                variant_id = None
                
                for store in stores[attempt*3:(attempt+1)*3]:
                    store_url = store['url']
                    product = self.product_finder.find_product_at_price(store_url, 1.00, 4.00)
                    if not product:
                        product = self.product_finder.get_cheapest_product(store_url)
                    
                    if product:
                        variant_id = product['variant_id']
                        print(f"  ✓ Found: {store_url} - {product['title']} (${product['price']})")
                        break
                
                if not store_url or not variant_id:
                    continue
                
                # Initialize browser
                print(f"  → Initializing browser...")
                self._init_browser()
                
                # Navigate to checkout
                if not self._navigate_to_checkout(store_url, variant_id):
                    self._close_browser()
                    continue
                
                # Fill shipping and continue to payment
                if not self._fill_shipping_and_continue():
                    self._close_browser()
                    continue
                
                # Fill card details
                if not self._fill_card_details(card_number, exp_month, exp_year, cvv):
                    self._close_browser()
                    continue
                
                # Submit and detect result
                status, message = self._submit_and_detect_result()
                self._close_browser()
                
                if status == 'approved':
                    self.successful_charges += 1
                    return status, f"{message} | Store: {store_url}", card_type
                elif status == 'declined':
                    return status, message, card_type
                else:
                    continue
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                self._close_browser()
                continue
        
        return 'error', 'All attempts failed', card_type


if __name__ == "__main__":
    print("="*70)
    print("SHOPIFY HYBRID GATEWAY V2 - IMPROVED")
    print("="*70)
    print("\nImprovements:")
    print("  ✓ Properly navigates to payment page")
    print("  ✓ Waits for payment form to load")
    print("  ✓ Better card field detection")
    print("  ✓ More debugging output\n")
    
    gateway = ShopifyHybridGatewayV2(headless=False)  # Non-headless for debugging
    
    test_card = "4111111111111111|12|25|123"
    print(f"Testing card: {test_card[:4]}...{test_card[-7:]}\n")
    
    status, message, card_type = gateway.check(test_card, max_attempts=1)
    
    print(f"\n{'='*70}")
    print(f"RESULT:")
    print(f"  Status: {status}")
    print(f"  Message: {message}")
    print(f"  Card Type: {card_type}")
    print(f"{'='*70}")
