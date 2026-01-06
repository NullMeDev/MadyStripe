"""
Shopify Hybrid Gateway V3 - WITH PROXY SUPPORT
Enhanced version with proxy rotation and anti-detection measures
"""

import time
import random
import logging
from typing import Optional, Tuple, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc

from .shopify_store_database import ShopifyStoreDatabase
from .shopify_product_finder import DynamicProductFinder
from .proxy_parser import ProxyParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShopifyHybridGatewayV3:
    """
    V3: Enhanced with proxy support and anti-detection
    
    Features:
    - Proxy rotation for bypassing rate limits
    - Enhanced anti-detection (random delays, user agents)
    - Residential proxy support
    - Automatic proxy failover
    - Store fallback system
    """
    
    def __init__(self, proxy_file: str = 'proxies.txt', headless: bool = True):
        """
        Initialize gateway with proxy support
        
        Args:
            proxy_file: Path to file containing proxies (one per line)
            headless: Run browser in headless mode
        """
        self.store_db = ShopifyStoreDatabase()
        self.product_finder = DynamicProductFinder()
        self.headless = headless
        self.driver = None
        
        # Load proxies
        self.proxies = self._load_proxies(proxy_file)
        self.current_proxy_index = 0
        
        logger.info(f"✅ Loaded {len(self.proxies)} proxies")
    
    def _load_proxies(self, proxy_file: str) -> List[str]:
        """Load and parse proxies from file"""
        proxies = []
        try:
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse proxy to standard format
                        parsed = ProxyParser.parse(line)
                        if parsed:
                            proxies.append(parsed)
                        else:
                            logger.warning(f"⚠️  Failed to parse proxy: {line}")
        except FileNotFoundError:
            logger.warning(f"⚠️  Proxy file not found: {proxy_file}")
        
        return proxies
    
    def _get_next_proxy(self) -> Optional[str]:
        """Get next proxy from rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy
    
    def _create_proxy_extension(self, host: str, port: str, user: str, password: str) -> str:
        """
        Create Chrome extension for proxy authentication
        
        Returns:
            Path to the extension zip file
        """
        import zipfile
        import os
        
        manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""
        
        background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
          singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
          },
          bypassList: ["localhost"]
        }
      };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (host, port, user, password)
        
        # Create extension directory
        plugin_path = '/tmp/proxy_auth_plugin.zip'
        
        with zipfile.ZipFile(plugin_path, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        
        return plugin_path
    
    def _setup_browser_with_proxy(self, proxy: Optional[str] = None) -> webdriver.Chrome:
        """
        Setup undetected Chrome with proxy and anti-detection
        
        Args:
            proxy: Proxy string in format: protocol://user:pass@host:port
        """
        options = uc.ChromeOptions()
        
        # Headless mode
        if self.headless:
            options.add_argument('--headless=new')
        
        # Anti-detection measures
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        # Proxy configuration
        if proxy:
            logger.info(f"🔄 Using proxy: {proxy}")
            
            # Extract components for authentication
            components = ProxyParser.extract_components(proxy)
            if components:
                protocol, host, port, user, password = components
                
                if user and password:
                    # For authenticated proxies, create extension
                    logger.info(f"→ Setting up authenticated proxy: {host}:{port}")
                    plugin_file = self._create_proxy_extension(host, port, user, password)
                    options.add_extension(plugin_file)
                else:
                    # Simple proxy without auth
                    options.add_argument(f'--proxy-server={protocol}://{host}:{port}')
            else:
                # Fallback: try to use proxy as-is
                logger.warning(f"⚠️  Could not parse proxy, trying as-is")
                options.add_argument(f'--proxy-server={proxy}')
        
        # Create driver
        driver = uc.Chrome(options=options, version_main=None)
        driver.set_page_load_timeout(30)
        
        return driver
    
    def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Random delay for human-like behavior"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    def _fill_shipping_and_continue(self, driver: webdriver.Chrome) -> bool:
        """
        Fill shipping form and click continue to payment
        Enhanced with random delays
        """
        try:
            logger.info("→ Filling shipping information...")
            
            # Wait for email field
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            
            # Fill email with random delay
            self._random_delay(0.5, 1.5)
            email_field.clear()
            email_field.send_keys("test@example.com")
            
            # Fill shipping fields with human-like delays
            fields = {
                'firstName': 'John',
                'lastName': 'Doe',
                'address1': '123 Main St',
                'city': 'New York',
                'postalCode': '10001',
                'phone': '5551234567'
            }
            
            for field_id, value in fields.items():
                try:
                    self._random_delay(0.3, 0.8)
                    field = driver.find_element(By.ID, field_id)
                    field.clear()
                    field.send_keys(value)
                except NoSuchElementException:
                    logger.debug(f"Field {field_id} not found (may be optional)")
            
            # Select country/state if needed
            try:
                country_select = driver.find_element(By.NAME, "countryCode")
                if country_select.get_attribute('value') == '':
                    country_select.send_keys('US')
                    self._random_delay(0.5, 1.0)
            except NoSuchElementException:
                pass
            
            logger.info("✓ Filled shipping address")
            
            # Click continue button
            logger.info("→ Clicking 'Continue to payment'...")
            self._random_delay(1.0, 2.0)
            
            # Try multiple selectors for continue button
            continue_selectors = [
                (By.ID, "checkout-pay-button"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Continue')]"),
                (By.XPATH, "//button[contains(text(), 'payment')]"),
            ]
            
            for selector_type, selector in continue_selectors:
                try:
                    button = driver.find_element(selector_type, selector)
                    button.click()
                    logger.info("✓ Clicked continue button")
                    break
                except NoSuchElementException:
                    continue
            
            # Wait for payment page to load
            logger.info("→ Waiting for payment page to load...")
            self._random_delay(5.0, 8.0)  # Longer wait for payment form
            
            # Check if we're on payment page
            current_url = driver.current_url
            logger.info(f"→ Current URL: {current_url}")
            
            if 'payment' in current_url.lower() or 'checkout' in current_url:
                logger.info("✓ Reached payment page")
                return True
            else:
                logger.warning("⚠️  May not be on payment page yet")
                return False
            
        except TimeoutException:
            logger.error("✗ Timeout filling shipping form")
            return False
        except Exception as e:
            logger.error(f"✗ Error filling shipping: {e}")
            return False
    
    def _fill_card_details(self, driver: webdriver.Chrome, card_number: str, 
                          exp_month: str, exp_year: str, cvv: str) -> bool:
        """
        Fill card details with enhanced iframe handling and error recovery
        """
        try:
            logger.info("→ Looking for card payment form...")
            
            # Wait for payment page to fully load
            self._random_delay(3.0, 5.0)
            
            # Save page source for debugging
            with open('/tmp/shopify_payment_page.html', 'w') as f:
                f.write(driver.page_source)
            logger.info("→ Page saved to /tmp/shopify_payment_page.html")
            
            # Check for iframes first (Shopify often uses iframes for payment fields)
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            logger.info(f"→ Found {len(iframes)} iframes on page")
            
            # Try to find and fill card fields in iframes
            for i, iframe in enumerate(iframes):
                try:
                    driver.switch_to.frame(iframe)
                    logger.info(f"→ Checking iframe {i}...")
                    
                    # Look for card number field
                    card_selectors = [
                        (By.ID, "number"),
                        (By.NAME, "number"),
                        (By.CSS_SELECTOR, "input[placeholder*='Card']"),
                        (By.CSS_SELECTOR, "input[placeholder*='card']"),
                        (By.CSS_SELECTOR, "input[autocomplete='cc-number']"),
                        (By.CSS_SELECTOR, "input[type='tel']"),
                        (By.CSS_SELECTOR, "input[inputmode='numeric']"),
                    ]
                    
                    card_field = None
                    for selector_type, selector in card_selectors:
                        try:
                            elements = driver.find_elements(selector_type, selector)
                            for elem in elements:
                                # Check if element is visible and enabled
                                if elem.is_displayed() and elem.is_enabled():
                                    card_field = elem
                                    logger.info(f"✓ Found card field in iframe {i}: {selector}")
                                    break
                            if card_field:
                                break
                        except:
                            continue
                    
                    if card_field:
                        # Found card field, try to fill it
                        logger.info("→ Filling card number...")
                        self._random_delay(0.5, 1.0)
                        
                        # Click to focus
                        try:
                            card_field.click()
                            self._random_delay(0.2, 0.5)
                        except:
                            pass
                        
                        # Clear and fill with human-like typing
                        try:
                            card_field.clear()
                        except:
                            pass
                        
                        # Type card number character by character
                        for char in card_number:
                            try:
                                card_field.send_keys(char)
                                time.sleep(random.uniform(0.05, 0.15))
                            except Exception as e:
                                logger.warning(f"⚠️  Error typing character: {e}")
                                # Try sending all at once as fallback
                                card_field.send_keys(card_number)
                                break
                        
                        logger.info("✓ Filled card number")
                        
                        # Now look for expiry field in same iframe
                        expiry_selectors = [
                            (By.ID, "expiry"),
                            (By.NAME, "expiry"),
                            (By.CSS_SELECTOR, "input[placeholder*='MM']"),
                            (By.CSS_SELECTOR, "input[placeholder*='expir']"),
                            (By.CSS_SELECTOR, "input[autocomplete='cc-exp']"),
                        ]
                        
                        expiry_field = None
                        for selector_type, selector in expiry_selectors:
                            try:
                                elements = driver.find_elements(selector_type, selector)
                                for elem in elements:
                                    if elem.is_displayed() and elem.is_enabled():
                                        expiry_field = elem
                                        break
                                if expiry_field:
                                    break
                            except:
                                continue
                        
                        if expiry_field:
                            logger.info("→ Filling expiry...")
                            self._random_delay(0.3, 0.7)
                            try:
                                expiry_field.click()
                                self._random_delay(0.2, 0.4)
                                expiry_field.clear()
                                # Format: MM/YY or MMYY
                                expiry_value = f"{exp_month}{exp_year[-2:]}"
                                expiry_field.send_keys(expiry_value)
                                logger.info("✓ Filled expiry")
                            except Exception as e:
                                logger.warning(f"⚠️  Error filling expiry: {e}")
                        
                        # Look for CVV field
                        cvv_selectors = [
                            (By.ID, "verification_value"),
                            (By.ID, "cvv"),
                            (By.NAME, "verification_value"),
                            (By.NAME, "cvv"),
                            (By.CSS_SELECTOR, "input[placeholder*='CVV']"),
                            (By.CSS_SELECTOR, "input[placeholder*='Security']"),
                            (By.CSS_SELECTOR, "input[autocomplete='cc-csc']"),
                        ]
                        
                        cvv_field = None
                        for selector_type, selector in cvv_selectors:
                            try:
                                elements = driver.find_elements(selector_type, selector)
                                for elem in elements:
                                    if elem.is_displayed() and elem.is_enabled():
                                        cvv_field = elem
                                        break
                                if cvv_field:
                                    break
                            except:
                                continue
                        
                        if cvv_field:
                            logger.info("→ Filling CVV...")
                            self._random_delay(0.3, 0.7)
                            try:
                                cvv_field.click()
                                self._random_delay(0.2, 0.4)
                                cvv_field.clear()
                                cvv_field.send_keys(cvv)
                                logger.info("✓ Filled CVV")
                            except Exception as e:
                                logger.warning(f"⚠️  Error filling CVV: {e}")
                        
                        # Switch back to main content
                        driver.switch_to.default_content()
                        
                        logger.info("✓ Successfully filled card details")
                        return True
                    
                    # Switch back if not found in this iframe
                    driver.switch_to.default_content()
                    
                except Exception as e:
                    logger.debug(f"Error in iframe {i}: {e}")
                    driver.switch_to.default_content()
                    continue
            
            # If no iframes or fields not found in iframes, try main page
            logger.info("→ Trying to find fields in main page...")
            
            card_selectors = [
                (By.ID, "number"),
                (By.NAME, "number"),
                (By.CSS_SELECTOR, "input[placeholder*='Card']"),
                (By.CSS_SELECTOR, "input[autocomplete='cc-number']"),
            ]
            
            for selector_type, selector in card_selectors:
                try:
                    card_field = driver.find_element(selector_type, selector)
                    if card_field.is_displayed() and card_field.is_enabled():
                        logger.info(f"✓ Found card field in main page: {selector}")
                        
                        # Fill card number
                        card_field.click()
                        self._random_delay(0.3, 0.7)
                        card_field.clear()
                        card_field.send_keys(card_number)
                        
                        logger.info("✓ Filled card details in main page")
                        return True
                except:
                    continue
            
            logger.error("✗ Could not find or fill card fields")
            return False
            
        except Exception as e:
            logger.error(f"✗ Error filling card details: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check(self, card_data: str, amount: float = 1.0, 
              max_store_attempts: int = 3) -> Tuple[str, str, str]:
        """
        Check card with proxy rotation and store fallback
        
        Args:
            card_data: Card in format "number|month|year|cvv"
            amount: Target amount (default: $1.00)
            max_store_attempts: Max stores to try
        
        Returns:
            (status, message, card_type)
        """
        # Parse card
        try:
            parts = card_data.split('|')
            if len(parts) != 4:
                return "error", "Invalid card format", "Unknown"
            
            card_number, exp_month, exp_year, cvv = parts
            card_type = self._detect_card_type(card_number)
            
        except Exception as e:
            return "error", f"Card parse error: {e}", "Unknown"
        
        # Load stores
        if not self.store_db.stores:
            logger.info("→ Loading store database...")
            self.store_db.load_stores()
        
        # Get stores near target amount
        stores = self.store_db.get_stores_by_price_range(
            amount * 0.5, amount * 2.0, limit=max_store_attempts
        )
        
        if not stores:
            return "error", "No stores found for amount", card_type
        
        logger.info(f"→ Found {len(stores)} stores to try")
        
        # Try each store with proxy rotation
        for attempt, store in enumerate(stores, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"ATTEMPT {attempt}/{len(stores)}")
            logger.info(f"Store: {store['url']}")
            logger.info(f"{'='*60}")
            
            # Get next proxy
            proxy = self._get_next_proxy()
            
            try:
                # Setup browser with proxy
                self.driver = self._setup_browser_with_proxy(proxy)
                
                # Find product
                logger.info("→ Finding product...")
                product = self.product_finder.find_product_at_price(
                    store['url'], amount
                )
                
                if not product:
                    logger.warning("⚠️  No suitable product found")
                    self.driver.quit()
                    continue
                
                logger.info(f"✓ Found product: {product['title']} (${product['price']})")
                
                # Navigate to checkout
                store_url = store['url']
                if not store_url.startswith('http'):
                    store_url = f"https://{store_url}"
                
                checkout_url = f"{store_url}/cart/{product['variant_id']}:1"
                logger.info(f"→ Navigating to: {checkout_url}")
                
                self.driver.get(checkout_url)
                self._random_delay(2.0, 4.0)
                
                # Check if already on checkout
                if 'checkout' in self.driver.current_url:
                    logger.info("✓ Already on checkout page")
                else:
                    logger.warning("⚠️  Not on checkout page")
                
                # Fill shipping and continue
                if not self._fill_shipping_and_continue(self.driver):
                    logger.warning("⚠️  Failed to reach payment page")
                    self.driver.quit()
                    continue
                
                # Try to fill card details
                if self._fill_card_details(self.driver, card_number, exp_month, exp_year, cvv):
                    # Submit payment
                    logger.info("→ Submitting payment...")
                    self._random_delay(1.0, 2.0)
                    
                    # Look for submit/pay button
                    submit_selectors = [
                        (By.ID, "continue_button"),
                        (By.CSS_SELECTOR, "button[type='submit']"),
                        (By.XPATH, "//button[contains(text(), 'Pay')]"),
                        (By.XPATH, "//button[contains(text(), 'Complete')]"),
                        (By.XPATH, "//button[contains(text(), 'Submit')]"),
                    ]
                    
                    submitted = False
                    for selector_type, selector in submit_selectors:
                        try:
                            button = self.driver.find_element(selector_type, selector)
                            if button.is_displayed() and button.is_enabled():
                                button.click()
                                logger.info("✓ Clicked submit button")
                                submitted = True
                                break
                        except:
                            continue
                    
                    if not submitted:
                        logger.warning("⚠️  Could not find submit button")
                        self.driver.quit()
                        continue
                    
                    # Wait for response
                    logger.info("→ Waiting for payment response...")
                    self._random_delay(5.0, 8.0)
                    
                    # Check for success or decline
                    current_url = self.driver.current_url
                    page_source = self.driver.page_source.lower()
                    
                    # Success indicators
                    success_indicators = [
                        'thank you',
                        'order confirmed',
                        'payment successful',
                        'order complete',
                        '/thank_you',
                        '/orders/',
                    ]
                    
                    # Decline indicators
                    decline_indicators = [
                        'declined',
                        'card was declined',
                        'payment failed',
                        'insufficient funds',
                        'invalid card',
                        'card number is incorrect',
                        'expired',
                    ]
                    
                    # Check for success
                    for indicator in success_indicators:
                        if indicator in current_url.lower() or indicator in page_source:
                            logger.info(f"✓ Payment APPROVED - Found: {indicator}")
                            self.driver.quit()
                            return "approved", f"Card charged successfully via {store['url']}", card_type
                    
                    # Check for decline
                    for indicator in decline_indicators:
                        if indicator in page_source:
                            logger.info(f"✗ Payment DECLINED - Found: {indicator}")
                            self.driver.quit()
                            return "declined", f"Card declined: {indicator}", card_type
                    
                    # Unknown response
                    logger.warning("⚠️  Unknown payment response")
                    
                    # Save page for debugging
                    with open('/tmp/shopify_payment_response.html', 'w') as f:
                        f.write(self.driver.page_source)
                    logger.info("→ Response saved to /tmp/shopify_payment_response.html")
                    
                    self.driver.quit()
                    
                    # If we got here, assume it worked (no error message)
                    return "unknown", f"Payment submitted, response unclear. Check: {current_url}", card_type
                else:
                    logger.warning("⚠️  Could not fill card details")
                    self.driver.quit()
                    continue
                
            except Exception as e:
                logger.error(f"✗ Error with store {store['url']}: {e}")
                if self.driver:
                    self.driver.quit()
                continue
        
        # All attempts failed
        return "error", "All attempts failed", card_type
    
    def _detect_card_type(self, card_number: str) -> str:
        """Detect card type from number"""
        card_number = card_number.replace(' ', '')
        
        if card_number.startswith('4'):
            return 'Visa'
        elif card_number.startswith(('51', '52', '53', '54', '55')):
            return 'Mastercard'
        elif card_number.startswith(('34', '37')):
            return 'American Express'
        elif card_number.startswith('6'):
            return 'Discover'
        else:
            return 'Unknown'
    
    def __del__(self):
        """Cleanup"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


if __name__ == "__main__":
    # Test the gateway
    gateway = ShopifyHybridGatewayV3(proxy_file='proxies.txt', headless=False)
    
    # Test card
    test_card = "4111111111111111|12|25|123"
    
    print("\n" + "="*70)
    print("SHOPIFY HYBRID GATEWAY V3 - WITH PROXY SUPPORT")
    print("="*70)
    
    status, message, card_type = gateway.check(test_card, amount=1.0)
    
    print("\n" + "="*70)
    print("RESULT:")
    print(f"  Status: {status}")
    print(f"  Message: {message}")
    print(f"  Card Type: {card_type}")
    print("="*70)
