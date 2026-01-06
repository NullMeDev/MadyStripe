"""
Shopify Real Payment Processor
Implements complete GraphQL payment flow extracted from AutoshBot
Converts async code to sync for integration with MadyStripe
"""

import requests
import json
import time
import re
from typing import Tuple, Optional, Dict, Any


class ShopifyPaymentProcessor:
    """
    Real Shopify payment processor using GraphQL mutations
    NO STUB FUNCTIONS - All API calls are real
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
    
    def _extract_between(self, text: str, start: str, end: str) -> Optional[str]:
        """Extract text between two markers"""
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
        """Format card with spaces every 4 digits"""
        # Remove existing spaces
        card_number = card_number.replace(' ', '')
        # Add spaces every 4 digits
        return ' '.join([card_number[i:i+4] for i in range(0, len(card_number), 4)])
    
    def get_payment_token(self, card_number: str, exp_month: str, exp_year: str, 
                         cvv: str, first_name: str, last_name: str, 
                         store_domain: str) -> Optional[str]:
        """
        Step 1: Get payment token from deposit.shopifycs.com
        
        Args:
            card_number: Card number (will be formatted with spaces)
            exp_month: Expiration month (MM)
            exp_year: Expiration year (YY or YYYY)
            cvv: CVV code
            first_name: Cardholder first name
            last_name: Cardholder last name
            store_domain: Store domain (e.g., 'example.myshopify.com')
        
        Returns:
            Payment token ID or None if failed
        """
        try:
            # Format card with spaces
            formatted_card = self._format_card(card_number)
            
            # Ensure year is 4 digits
            if len(exp_year) == 2:
                exp_year = '20' + exp_year
            
            # Prepare payload
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
            
            # Make request
            response = self.session.post(
                'https://deposit.shopifycs.com/sessions',
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                token_id = data.get('id')
                return token_id
            
            return None
            
        except Exception as e:
            print(f"Token generation error: {e}")
            return None
    
    def create_checkout(self, store_url: str, variant_id: int) -> Optional[Dict[str, Any]]:
        """
        Create checkout session and extract session token
        
        Args:
            store_url: Full store URL (e.g., 'https://example.myshopify.com')
            variant_id: Product variant ID
        
        Returns:
            Dict with session_token, queue_token, stable_id, currency, etc.
        """
        try:
            # Clean URL
            if not store_url.startswith('http'):
                store_url = 'https://' + store_url
            
            # Add to cart
            cart_url = f"{store_url}/cart/add.js"
            self.session.post(cart_url, data={'id': variant_id}, timeout=10)
            
            # Go to checkout
            checkout_url = f"{store_url}/checkout/"
            response = self.session.post(checkout_url, timeout=10)
            checkout_url = str(response.url)
            
            # Check for login requirement
            if 'login' in checkout_url.lower():
                return None
            
            # Get checkout page
            response = self.session.get(checkout_url, timeout=10)
            text = response.text
            
            # Extract session token
            sst = self._extract_between(text, 'name="serialized-session-token" content="&quot;', '&q')
            if not sst:
                # Retry once
                time.sleep(1)
                response = self.session.get(checkout_url, timeout=10)
                text = response.text
                sst = self._extract_between(text, 'name="serialized-session-token" content="&quot;', '&q')
            
            if not sst:
                return None
            
            # Extract other required data
            queue_token = self._extract_between(text, 'queueToken&quot;:&quot;', '&q')
            stable_id = self._extract_between(text, 'stableId&quot;:&quot;', '&q')
            
            # Extract currency
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
            print(f"Checkout creation error: {e}")
            return None
    
    def submit_shipping(self, session_token: str, queue_token: str, stable_id: str,
                       variant_id: int, store_url: str, shipping_address: Dict[str, str],
                       email: str, phone: str) -> Optional[Dict[str, Any]]:
        """
        Step 2: Submit shipping information using Proposal GraphQL mutation
        
        This is the REAL implementation - no stubs!
        
        Returns:
            Dict with updated queue_token, delivery_strategy, amounts, etc.
        """
        try:
            # Clean store URL
            store_domain = store_url.replace('https://', '').replace('http://', '').split('/')[0]
            graphql_url = f"https://{store_domain}/checkouts/unstable/graphql"
            
            # Build the massive Proposal GraphQL mutation
            # (This is extracted directly from AutoshBot - lines 270-489)
            query = '''query Proposal($alternativePaymentCurrency:AlternativePaymentCurrencyInput,$delivery:DeliveryTermsInput,$discounts:DiscountTermsInput,$payment:PaymentTermInput,$merchandise:MerchandiseTermInput,$buyerIdentity:BuyerIdentityTermInput,$taxes:TaxTermInput,$sessionInput:SessionTokenInput!,$checkpointData:String,$queueToken:String,$reduction:ReductionInput,$availableRedeemables:AvailableRedeemablesInput,$changesetTokens:[String!],$tip:TipTermInput,$note:NoteInput,$localizationExtension:LocalizationExtensionInput,$nonNegotiableTerms:NonNegotiableTermsInput,$scriptFingerprint:ScriptFingerprintInput,$transformerFingerprintV2:String,$optionalDuties:OptionalDutiesInput,$attribution:AttributionInput,$captcha:CaptchaInput,$poNumber:String,$saleAttributions:SaleAttributionsInput){session(sessionInput:$sessionInput){negotiate(input:{purchaseProposal:{alternativePaymentCurrency:$alternativePaymentCurrency,delivery:$delivery,discounts:$discounts,payment:$payment,merchandise:$merchandise,buyerIdentity:$buyerIdentity,taxes:$taxes,reduction:$reduction,availableRedeemables:$availableRedeemables,tip:$tip,note:$note,poNumber:$poNumber,nonNegotiableTerms:$nonNegotiableTerms,localizationExtension:$localizationExtension,scriptFingerprint:$scriptFingerprint,transformerFingerprintV2:$transformerFingerprintV2,optionalDuties:$optionalDuties,attribution:$attribution,captcha:$captcha,saleAttributions:$saleAttributions},checkpointData:$checkpointData,queueToken:$queueToken,changesetTokens:$changesetTokens}){__typename result{...on NegotiationResultAvailable{checkpointData queueToken sellerProposal{delivery{...on FilledDeliveryTerms{deliveryLines{selectedDeliveryStrategy{...on CompleteDeliveryStrategy{handle __typename}__typename}__typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}__typename}}}'''
            
            # Build variables
            variables = {
                'sessionInput': {
                    'sessionToken': session_token,
                },
                'queueToken': queue_token,
                'discounts': {
                    'lines': [],
                    'acceptUnexpectedDiscounts': True,
                },
                'delivery': {
                    'deliveryLines': [
                        {
                            'destination': {
                                'partialStreetAddress': {
                                    'address1': shipping_address.get('address1', '123 Main St'),
                                    'address2': shipping_address.get('address2', ''),
                                    'city': shipping_address.get('city', 'New York'),
                                    'countryCode': shipping_address.get('country', 'US'),
                                    'postalCode': shipping_address.get('zip', '10001'),
                                    'firstName': shipping_address.get('first_name', 'John'),
                                    'lastName': shipping_address.get('last_name', 'Doe'),
                                    'zoneCode': shipping_address.get('state', 'NY'),
                                    'phone': phone,
                                },
                            },
                            'selectedDeliveryStrategy': {
                                'deliveryStrategyMatchingConditions': {
                                    'estimatedTimeInTransit': {
                                        'lowerBound': 0,
                                        'upperBound': 999,
                                    },
                                },
                            },
                            'targetMerchandise': {
                                'lines': [
                                    {
                                        'stableId': stable_id,
                                    },
                                ],
                            },
                        },
                    ],
                },
                'merchandise': {
                    'lines': [
                        {
                            'merchandise': {
                                'productVariantReference': {
                                    'id': f'gid://shopify/ProductVariant/{variant_id}',
                                },
                            },
                            'quantity': 1,
                            'stableId': stable_id,
                        },
                    ],
                },
                'buyerIdentity': {
                    'email': email,
                    'phone': phone,
                },
            }
            
            # Make GraphQL request
            payload = {
                'operationName': 'Proposal',
                'query': query,
                'variables': variables
            }
            
            response = self.session.post(
                graphql_url,
                json=payload,
                timeout=20
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Extract response data
            try:
                result = data['data']['session']['negotiate']['result']
                seller_proposal = result.get('sellerProposal', {})
                
                # Extract delivery strategy
                delivery_lines = seller_proposal.get('delivery', {}).get('deliveryLines', [])
                delivery_strategy = None
                if delivery_lines:
                    strategy = delivery_lines[0].get('selectedDeliveryStrategy', {})
                    delivery_strategy = strategy.get('handle')
                
                # Extract total amount
                checkout_total = seller_proposal.get('checkoutTotal', {}).get('value', {})
                total_amount = checkout_total.get('amount', '0')
                currency = checkout_total.get('currencyCode', 'USD')
                
                # Extract new queue token
                new_queue_token = result.get('queueToken', queue_token)
                
                return {
                    'queue_token': new_queue_token,
                    'delivery_strategy': delivery_strategy,
                    'total_amount': total_amount,
                    'currency': currency,
                    'success': True
                }
                
            except (KeyError, TypeError) as e:
                print(f"Failed to parse shipping response: {e}")
                return None
            
        except Exception as e:
            print(f"Shipping submission error: {e}")
            return None
    
    def submit_payment(self, session_token: str, queue_token: str, payment_token: str,
                      stable_id: str, variant_id: int, store_url: str,
                      shipping_address: Dict[str, str], billing_address: Dict[str, str],
                      email: str, phone: str, delivery_strategy: Optional[str] = None) -> Tuple[bool, str]:
        """
        Step 3: Submit payment using SubmitForCompletion GraphQL mutation
        
        This is the REAL implementation that actually charges the card!
        
        Returns:
            (success: bool, message: str)
            - If success=True, message contains receipt ID
            - If success=False, message contains error description
        """
        try:
            # Clean store URL
            store_domain = store_url.replace('https://', '').replace('http://', '').split('/')[0]
            graphql_url = f"https://{store_domain}/checkouts/unstable/graphql"
            
            # Build the massive SubmitForCompletion GraphQL mutation
            # (Extracted from AutoshBot - line 704)
            query = '''mutation SubmitForCompletion($input:NegotiationInput!,$attemptToken:String!){submitForCompletion(input:$input attemptToken:$attemptToken){...on SubmitSuccess{receipt{...on ProcessedReceipt{id __typename}__typename}__typename}...on SubmitAlreadyAccepted{receipt{...on ProcessedReceipt{id __typename}__typename}__typename}...on SubmitFailed{reason __typename}...on SubmitRejected{errors{code localizedMessage __typename}__typename}__typename}}'''
            
            # Build variables
            variables = {
                'attemptToken': payment_token,
                'input': {
                    'sessionToken': session_token,
                    'queueToken': queue_token,
                    'purchaseProposal': {
                        'delivery': {
                            'deliveryLines': [
                                {
                                    'destination': {
                                        'partialStreetAddress': {
                                            'address1': shipping_address.get('address1', '123 Main St'),
                                            'address2': shipping_address.get('address2', ''),
                                            'city': shipping_address.get('city', 'New York'),
                                            'countryCode': shipping_address.get('country', 'US'),
                                            'postalCode': shipping_address.get('zip', '10001'),
                                            'firstName': shipping_address.get('first_name', 'John'),
                                            'lastName': shipping_address.get('last_name', 'Doe'),
                                            'zoneCode': shipping_address.get('state', 'NY'),
                                            'phone': phone,
                                        },
                                    },
                                    'selectedDeliveryStrategy': {
                                        'handle': delivery_strategy
                                    } if delivery_strategy else {
                                        'deliveryStrategyMatchingConditions': {
                                            'estimatedTimeInTransit': {
                                                'lowerBound': 0,
                                                'upperBound': 999,
                                            },
                                        },
                                    },
                                    'targetMerchandise': {
                                        'lines': [
                                            {
                                                'stableId': stable_id,
                                            },
                                        ],
                                    },
                                },
                            ],
                        },
                        'merchandise': {
                            'lines': [
                                {
                                    'merchandise': {
                                        'productVariantReference': {
                                            'id': f'gid://shopify/ProductVariant/{variant_id}',
                                        },
                                    },
                                    'quantity': 1,
                                    'stableId': stable_id,
                                },
                            ],
                        },
                        'buyerIdentity': {
                            'email': email,
                            'phone': phone,
                        },
                        'payment': {
                            'billingAddress': {
                                'address1': billing_address.get('address1', '123 Main St'),
                                'address2': billing_address.get('address2', ''),
                                'city': billing_address.get('city', 'New York'),
                                'countryCode': billing_address.get('country', 'US'),
                                'postalCode': billing_address.get('zip', '10001'),
                                'firstName': billing_address.get('first_name', 'John'),
                                'lastName': billing_address.get('last_name', 'Doe'),
                                'zoneCode': billing_address.get('state', 'NY'),
                                'phone': phone,
                            },
                            'paymentLines': [
                                {
                                    'paymentMethod': {
                                        'directPaymentMethod': {
                                            'sessionId': payment_token,
                                        },
                                    },
                                },
                            ],
                        },
                        'discounts': {
                            'lines': [],
                            'acceptUnexpectedDiscounts': True,
                        },
                    },
                },
            }
            
            # Make GraphQL request
            payload = {
                'operationName': 'SubmitForCompletion',
                'query': query,
                'variables': variables
            }
            
            response = self.session.post(
                graphql_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}"
            
            data = response.json()
            
            # Parse response
            try:
                submit_result = data['data']['submitForCompletion']
                typename = submit_result.get('__typename', '')
                
                # Check for success
                if typename in ['SubmitSuccess', 'SubmitAlreadyAccepted']:
                    receipt = submit_result.get('receipt', {})
                    receipt_id = receipt.get('id')
                    if receipt_id:
                        return True, f"Receipt ID: {receipt_id}"
                    return True, "Payment successful"
                
                # Check for rejection
                elif typename == 'SubmitRejected':
                    errors = submit_result.get('errors', [])
                    if errors:
                        error_msg = errors[0].get('localizedMessage', 'Payment declined')
                        return False, error_msg
                    return False, "Payment rejected"
                
                # Check for failure
                elif typename == 'SubmitFailed':
                    reason = submit_result.get('reason', 'Unknown failure')
                    return False, reason
                
                else:
                    return False, f"Unknown response type: {typename}"
                
            except (KeyError, TypeError) as e:
                return False, f"Failed to parse payment response: {e}"
            
        except Exception as e:
            return False, f"Payment submission error: {e}"
    
    def process_card(self, store_url: str, variant_id: int, card_number: str,
                    exp_month: str, exp_year: str, cvv: str,
                    shipping_address: Optional[Dict[str, str]] = None,
                    billing_address: Optional[Dict[str, str]] = None) -> Tuple[str, str, str]:
        """
        Complete payment processing flow
        
        Args:
            store_url: Store URL
            variant_id: Product variant ID
            card_number: Card number
            exp_month: Expiration month
            exp_year: Expiration year
            cvv: CVV code
            shipping_address: Optional shipping address dict
            billing_address: Optional billing address dict
        
        Returns:
            (status, message, card_type)
            - status: 'approved', 'declined', or 'error'
            - message: Detailed message
            - card_type: Card brand
        """
        try:
            # Default addresses if not provided
            if not shipping_address:
                shipping_address = {
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'address1': '123 Main St',
                    'address2': '',
                    'city': 'New York',
                    'state': 'NY',
                    'zip': '10001',
                    'country': 'US',
                }
            
            if not billing_address:
                billing_address = shipping_address.copy()
            
            # Generate email and phone
            email = f"test{int(time.time())}@example.com"
            phone = "+12125551234"
            
            # Extract store domain
            store_domain = store_url.replace('https://', '').replace('http://', '').split('/')[0]
            
            # Step 1: Create checkout
            print(f"[1/4] Creating checkout...")
            checkout_data = self.create_checkout(store_url, variant_id)
            if not checkout_data:
                return 'error', 'Failed to create checkout', 'Unknown'
            
            session_token = checkout_data['session_token']
            queue_token = checkout_data['queue_token']
            stable_id = checkout_data['stable_id']
            
            # Step 2: Get payment token
            print(f"[2/4] Getting payment token...")
            payment_token = self.get_payment_token(
                card_number, exp_month, exp_year, cvv,
                shipping_address['first_name'], shipping_address['last_name'],
                store_domain
            )
            if not payment_token:
                return 'declined', 'Invalid card details', 'Unknown'
            
            # Step 3: Submit shipping
            print(f"[3/4] Submitting shipping...")
            shipping_result = self.submit_shipping(
                session_token, queue_token, stable_id, variant_id,
                store_url, shipping_address, email, phone
            )
            if not shipping_result:
                return 'error', 'Failed to submit shipping', 'Unknown'
            
            # Update queue token
            queue_token = shipping_result['queue_token']
            delivery_strategy = shipping_result.get('delivery_strategy')
            
            # Step 4: Submit payment
            print(f"[4/4] Submitting payment...")
            success, message = self.submit_payment(
                session_token, queue_token, payment_token, stable_id, variant_id,
                store_url, shipping_address, billing_address, email, phone,
                delivery_strategy
            )
            
            # Determine card type from number
            card_type = 'Unknown'
            if card_number.startswith('4'):
                card_type = 'Visa'
            elif card_number.startswith('5'):
                card_type = 'Mastercard'
            elif card_number.startswith('3'):
                card_type = 'Amex'
            
            if success:
                return 'approved', message, card_type
            else:
                # Check if it's a decline or error
                decline_keywords = ['insufficient', 'declined', 'invalid', 'expired', 'incorrect']
                if any(keyword in message.lower() for keyword in decline_keywords):
                    return 'declined', message, card_type
                else:
                    return 'error', message, card_type
            
        except Exception as e:
            return 'error', f"Processing error: {e}", 'Unknown'


if __name__ == "__main__":
    print("="*70)
    print("SHOPIFY REAL PAYMENT PROCESSOR TEST")
    print("="*70)
    print("\n⚠️  WARNING: This will attempt REAL payment processing!")
    print("Only use with test cards or cards you own.\n")
    
    processor = ShopifyPaymentProcessor()
    
    # Test with a store and product
    test_store = "sifrinerias.myshopify.com"
    test_variant = 31135  # $0.01 product
    
    # Test card (this will be declined - insufficient funds)
    test_card = "4111111111111111"
    
    print(f"Testing with:")
    print(f"  Store: {test_store}")
    print(f"  Variant: {test_variant}")
    print(f"  Card: {test_card[:4]}...{test_card[-4:]}")
    print()
    
    status, message, card_type = processor.process_card(
        f"https://{test_store}",
        test_variant,
        test_card,
        "12",
        "25",
        "123"
    )
    
    print(f"\n{'='*70}")
    print(f"Result:")
    print(f"  Status: {status}")
    print(f"  Message: {message}")
    print(f"  Card Type: {card_type}")
    print(f"{'='*70}")
