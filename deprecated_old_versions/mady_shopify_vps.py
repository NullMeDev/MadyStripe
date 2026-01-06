#!/usr/bin/env python3
"""
MADY Shopify Payments Checker - VPS CLI Version
Fast HTTP-based checker for Shopify Payments (CHARGED MODE)
Usage: python3 mady_shopify_vps.py <cards_file> <store_url> [--limit N]
"""

import sys
import os
import argparse
import time
from datetime import datetime

# Add gateway path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '100$/100$/'))

from Charge10_ShopifyPayments import ShopifyPaymentsCheck

def print_banner():
    """Print banner"""
    print("="*70)
    print("MADY SHOPIFY PAYMENTS CHECKER - VPS CLI")
    print("Fast HTTP-based checker (CHARGED MODE)")
    print("="*70)
    print()

def check_cards(cards_file, store_url, limit=None):
    """Check cards from file"""
    
    # Read cards
    try:
        with open(cards_file, 'r') as f:
            cards = [line.strip() for line in f if line.strip() and '|' in line]
    except FileNotFoundError:
        print(f"❌ Error: File not found: {cards_file}")
        return
    
    if not cards:
        print(f"❌ Error: No valid cards found in {cards_file}")
        return
    
    # Apply limit
    if limit:
        cards = cards[:limit]
    
    print(f"📁 Loaded {len(cards)} cards from {cards_file}")
    print(f"🏪 Store: {store_url}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Results
    results = {
        'approved': [],
        'declined': [],
        'errors': []
    }
    
    # Check each card
    start_time = time.time()
    
    for i, card in enumerate(cards, 1):
        card_masked = f"{card.split('|')[0][:6]}****{card.split('|')[0][-4:]}"
        
        print(f"[{i}/{len(cards)}] Checking {card_masked}...", end=' ', flush=True)
        
        try:
            result = ShopifyPaymentsCheck(card, store_url)
            result_lower = result.lower() if isinstance(result, str) else str(result).lower()
            
            # Categorize result
            if any(x in result_lower for x in ['charged', 'cvv', 'insufficient', '3ds', 'success']):
                results['approved'].append((card, result))
                print(f"✅ {result}")
            elif 'error' in result_lower:
                results['errors'].append((card, result))
                print(f"⚠️ {result}")
            else:
                results['declined'].append((card, result))
                print(f"❌ {result}")
                
        except Exception as e:
            error_msg = str(e)[:50]
            results['errors'].append((card, error_msg))
            print(f"⚠️ Error: {error_msg}")
        
        # Small delay to avoid rate limits
        if i < len(cards):
            time.sleep(0.5)
    
    # Calculate stats
    elapsed = time.time() - start_time
    avg_time = elapsed / len(cards) if cards else 0
    
    # Print summary
    print()
    print("="*70)
    print("RESULTS SUMMARY")
    print("="*70)
    print(f"Total Cards: {len(cards)}")
    print(f"✅ Approved: {len(results['approved'])}")
    print(f"❌ Declined: {len(results['declined'])}")
    print(f"⚠️ Errors: {len(results['errors'])}")
    print(f"⏱️ Time: {elapsed:.1f}s (avg {avg_time:.1f}s/card)")
    print("="*70)
    print()
    
    # Print approved cards
    if results['approved']:
        print("✅ APPROVED CARDS:")
        print("-"*70)
        for card, result in results['approved']:
            print(f"{card}")
            print(f"  → {result}")
            print()
    
    # Print errors if any
    if results['errors']:
        print("⚠️ ERRORS:")
        print("-"*70)
        for card, error in results['errors'][:10]:  # Show first 10
            card_masked = f"{card.split('|')[0][:6]}****{card.split('|')[0][-4:]}"
            print(f"{card_masked}: {error}")
        if len(results['errors']) > 10:
            print(f"... and {len(results['errors']) - 10} more errors")
        print()
    
    # Save results
    output_file = f"shopify_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(output_file, 'w') as f:
            f.write(f"MADY Shopify Payments Checker Results\n")
            f.write(f"Store: {store_url}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total: {len(cards)} | Approved: {len(results['approved'])} | Declined: {len(results['declined'])} | Errors: {len(results['errors'])}\n")
            f.write("="*70 + "\n\n")
            
            if results['approved']:
                f.write("APPROVED CARDS:\n")
                f.write("-"*70 + "\n")
                for card, result in results['approved']:
                    f.write(f"{card}\n")
                    f.write(f"  → {result}\n\n")
            
            if results['declined']:
                f.write("\nDECLINED CARDS:\n")
                f.write("-"*70 + "\n")
                for card, result in results['declined']:
                    f.write(f"{card}\n")
                    f.write(f"  → {result}\n\n")
            
            if results['errors']:
                f.write("\nERRORS:\n")
                f.write("-"*70 + "\n")
                for card, error in results['errors']:
                    f.write(f"{card}\n")
                    f.write(f"  → {error}\n\n")
        
        print(f"💾 Results saved to: {output_file}")
    except Exception as e:
        print(f"⚠️ Could not save results: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='MADY Shopify Payments Checker - VPS CLI (CHARGED MODE)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check all cards from file
  python3 mady_shopify_vps.py cards.txt https://example-store.myshopify.com
  
  # Check first 10 cards only
  python3 mady_shopify_vps.py cards.txt https://example-store.myshopify.com --limit 10
  
  # Use test cards
  python3 mady_shopify_vps.py /home/null/Desktop/TestCards.txt https://example-store.myshopify.com --limit 5

Card Format: CARD|MM|YY|CVV
Example: 4242424242424242|12|25|123
        """
    )
    
    parser.add_argument('cards_file', help='Path to cards file (one card per line)')
    parser.add_argument('store_url', help='Shopify store URL (e.g., https://example-store.myshopify.com)')
    parser.add_argument('--limit', type=int, help='Limit number of cards to check')
    
    args = parser.parse_args()
    
    print_banner()
    check_cards(args.cards_file, args.store_url, args.limit)

if __name__ == '__main__':
    main()
