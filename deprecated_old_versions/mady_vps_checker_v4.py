#!/usr/bin/env python3
"""
MADY VPS CHECKER v4.0 - Multi-Gate Shopify Support
Optimized for 15000+ gates with rotation and caching

Features:
- Multi-gate Shopify support (15000+ gates)
- Gate validation and rotation
- Connection pooling
- Parallel processing
- All original gateways (1-9)
"""

import os
import sys
import argparse
import time
import json
import random
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque

# Add gateway path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '100$/100$/'))

# --- Gateway Imports ---
GATEWAYS = {}

# Original Stripe Gateways (1-5)
try:
    from Charge1 import BlemartCheckout
    GATEWAYS[1] = {'func': BlemartCheckout, 'name': 'Blemart', 'amount': '$4.99', 'type': 'stripe'}
except ImportError as e:
    print(f"Warning: Gateway 1 not available: {e}")

try:
    from Charge2 import DistrictPeopleCheckout
    GATEWAYS[2] = {'func': DistrictPeopleCheckout, 'name': 'District People', 'amount': '€69.00', 'type': 'stripe'}
except ImportError as e:
    print(f"Warning: Gateway 2 not available: {e}")

try:
    from Charge3 import SaintVinsonDonateCheckout
    GATEWAYS[3] = {'func': SaintVinsonDonateCheckout, 'name': 'Saint Vinson', 'amount': '$0.01', 'type': 'stripe'}
except ImportError as e:
    print(f"Warning: Gateway 3 not available: {e}")

try:
    from Charge4 import BGDCheckoutLogic
    GATEWAYS[4] = {'func': BGDCheckoutLogic, 'name': 'BGD Fresh', 'amount': '$6.50', 'type': 'stripe'}
except ImportError as e:
    print(f"Warning: Gateway 4 not available: {e}")

try:
    from Charge5 import StaleksFloridaCheckoutVNew
    GATEWAYS[5] = {'func': StaleksFloridaCheckoutVNew, 'name': 'Staleks Florida', 'amount': '$0.01', 'type': 'stripe-dict'}
except ImportError as e:
    print(f"Warning: Gateway 5 not available: {e}")

# Extended Gateways (6-9)
try:
    from Charge6_Braintree import BraintreeCheckout
    GATEWAYS[6] = {'func': BraintreeCheckout, 'name': 'Braintree', 'amount': '$1.00', 'type': 'braintree'}
except ImportError as e:
    print(f"Warning: Gateway 6 not available: {e}")

try:
    from Charge7_Square import SquareCheckout
    GATEWAYS[7] = {'func': SquareCheckout, 'name': 'Square', 'amount': '$1.00', 'type': 'square'}
except ImportError as e:
    print(f"Warning: Gateway 7 not available: {e}")

try:
    from Charge8_Shopify import ShopifyCheckout
    GATEWAYS[8] = {'func': ShopifyCheckout, 'name': 'Shopify', 'amount': 'Variable', 'type': 'shopify'}
except ImportError as e:
    print(f"Warning: Gateway 8 not available: {e}")

try:
    from Charge9_StripeCheckout import StripeCheckoutGateway
    GATEWAYS[9] = {'func': StripeCheckoutGateway, 'name': 'Stripe Checkout', 'amount': 'Variable', 'type': 'stripe-checkout'}
except ImportError as e:
    print(f"Warning: Gateway 9 not available: {e}")

# Multi-Gate Shopify (Gateway 10)
try:
    from Charge8_Shopify_Multi import (
        ShopifyMultiGateCheckout, 
        init_gate_manager, 
        get_gate_manager,
        validate_gates_batch,
        check_cards_batch,
        GateManager
    )
    GATEWAYS[10] = {'func': ShopifyMultiGateCheckout, 'name': 'Shopify Multi-Gate', 'amount': 'Variable', 'type': 'shopify-multi'}
except ImportError as e:
    print(f"Warning: Gateway 10 (Multi-Gate Shopify) not available: {e}")

# --- Configuration ---
DEFAULT_THREADS = 10
MAX_THREADS = 50
RATE_LIMIT_DELAY = 0.5  # Seconds between requests per thread

# --- Colors ---
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def colorize(text, color):
    return f"{color}{text}{Colors.RESET}"

# --- Card Processing ---
def load_cards(filepath, limit=None):
    """Load cards from file"""
    cards = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '|' in line:
                    cards.append(line)
                    if limit and len(cards) >= limit:
                        break
    except Exception as e:
        print(f"Error loading cards: {e}")
    return cards

def load_gates(filepath):
    """Load gates from file"""
    gates = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if not line.startswith('http'):
                        line = 'https://' + line
                    gates.append(line)
    except Exception as e:
        print(f"Error loading gates: {e}")
    return gates

def check_card(card, gateway_id, extra_params=None):
    """Check a single card"""
    if gateway_id not in GATEWAYS:
        return f"Error: Gateway {gateway_id} not available"
    
    gateway = GATEWAYS[gateway_id]
    func = gateway['func']
    gtype = gateway['type']
    
    try:
        # Handle different gateway types
        if gtype == 'stripe-checkout':
            checkout_url = extra_params.get('checkout_url') if extra_params else None
            result = func(card, checkout_url)
        elif gtype == 'shopify':
            shop_url = extra_params.get('shop_url') if extra_params else None
            result = func(card, shop_url)
        elif gtype == 'shopify-multi':
            gate_manager = extra_params.get('gate_manager') if extra_params else None
            result = func(card, None, gate_manager)
        elif gtype == 'stripe-dict':
            result = func(card)
            if isinstance(result, dict):
                if result.get('result') == 'success' or 'success' in str(result).lower():
                    result = "Approved"
                elif 'error' in result:
                    result = f"Declined ({result.get('error', 'Unknown')})"
                else:
                    result = str(result)
        else:
            result = func(card)
        
        return result
        
    except Exception as e:
        return f"Error: {str(e)[:50]}"

def process_cards_parallel(cards, gateway_id, threads=DEFAULT_THREADS, extra_params=None, callback=None):
    """Process cards in parallel"""
    results = {
        'approved': [],
        'declined': [],
        'errors': [],
        'total': len(cards),
        'start_time': time.time()
    }
    
    processed = 0
    lock = threading.Lock()
    
    def process_single(card):
        nonlocal processed
        
        result = check_card(card, gateway_id, extra_params)
        
        with lock:
            processed += 1
            
            # Categorize result
            result_lower = result.lower() if isinstance(result, str) else str(result).lower()
            
            if any(x in result_lower for x in ['approved', 'charged', 'success', 'pm created']):
                results['approved'].append((card, result))
                status = 'approved'
            elif 'error' in result_lower:
                results['errors'].append((card, result))
                status = 'error'
            else:
                results['declined'].append((card, result))
                status = 'declined'
            
            if callback:
                callback(card, result, status, processed, len(cards))
        
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)
        
        return (card, result)
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(process_single, card) for card in cards]
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Thread error: {e}")
    
    results['end_time'] = time.time()
    results['duration'] = results['end_time'] - results['start_time']
    
    return results

# --- Gate Validation ---
def validate_gates_parallel(gates, threads=50, callback=None):
    """Validate gates in parallel"""
    if 10 not in GATEWAYS:
        print("Error: Multi-gate module not loaded")
        return []
    
    return validate_gates_batch(gates, max_workers=threads, callback=callback)

# --- Display Functions ---
def print_banner():
    banner = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║  {Colors.MAGENTA}███╗   ███╗ █████╗ ██████╗ ██╗   ██╗{Colors.CYAN}                        ║
║  {Colors.MAGENTA}████╗ ████║██╔══██╗██╔══██╗╚██╗ ██╔╝{Colors.CYAN}                        ║
║  {Colors.MAGENTA}██╔████╔██║███████║██║  ██║ ╚████╔╝ {Colors.CYAN}                        ║
║  {Colors.MAGENTA}██║╚██╔╝██║██╔══██║██║  ██║  ╚██╔╝  {Colors.CYAN}                        ║
║  {Colors.MAGENTA}██║ ╚═╝ ██║██║  ██║██████╔╝   ██║   {Colors.CYAN}                        ║
║  {Colors.MAGENTA}╚═╝     ╚═╝╚═╝  ╚═╝╚═════╝    ╚═╝   {Colors.CYAN}                        ║
║                                                              ║
║  {Colors.WHITE}VPS CHECKER v4.0 - Multi-Gate Shopify Support{Colors.CYAN}              ║
║  {Colors.YELLOW}15000+ Gates | Rotation | Caching | Fast{Colors.CYAN}                   ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
    print(banner)

def print_gateways():
    print(f"\n{Colors.CYAN}Available Gateways:{Colors.RESET}")
    print("-" * 60)
    for gid, info in sorted(GATEWAYS.items()):
        status = colorize("✓", Colors.GREEN)
        print(f"  {status} Gateway {gid}: {info['name']} ({info['amount']}) [{info['type']}]")
    print("-" * 60)

def print_result(card, result, status, current, total):
    """Print a single result"""
    card_masked = f"{card[:6]}****{card.split('|')[0][-4:]}"
    
    if status == 'approved':
        icon = colorize("✅", Colors.GREEN)
        result_color = Colors.GREEN
    elif status == 'error':
        icon = colorize("⚠️", Colors.YELLOW)
        result_color = Colors.YELLOW
    else:
        icon = colorize("❌", Colors.RED)
        result_color = Colors.RED
    
    progress = f"[{current}/{total}]"
    print(f"{progress} {icon} {card_masked} → {colorize(result[:60], result_color)}")

def print_summary(results):
    """Print results summary"""
    duration = results.get('duration', 0)
    total = results.get('total', 0)
    approved = len(results.get('approved', []))
    declined = len(results.get('declined', []))
    errors = len(results.get('errors', []))
    
    cps = total / duration if duration > 0 else 0
    
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}RESULTS SUMMARY{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"  Total Cards:    {total}")
    print(f"  {colorize(f'Approved: {approved}', Colors.GREEN)}")
    print(f"  {colorize(f'Declined: {declined}', Colors.RED)}")
    print(f"  {colorize(f'Errors:   {errors}', Colors.YELLOW)}")
    print(f"  Duration:       {duration:.2f}s")
    print(f"  Speed:          {cps:.2f} cards/sec")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    
    # Print approved cards
    if results.get('approved'):
        print(f"\n{Colors.GREEN}APPROVED CARDS:{Colors.RESET}")
        for card, result in results['approved']:
            print(f"  ✅ {card} → {result}")

# --- Main Functions ---
def interactive_mode():
    """Interactive mode for the checker"""
    print_banner()
    print_gateways()
    
    print(f"\n{Colors.CYAN}Interactive Mode{Colors.RESET}")
    print("-" * 40)
    
    # Get cards file
    cards_file = input("Enter cards file path: ").strip()
    if not os.path.exists(cards_file):
        print(f"{Colors.RED}Error: File not found{Colors.RESET}")
        return
    
    # Get gateway
    gateway_id = input("Enter gateway ID (1-10): ").strip()
    try:
        gateway_id = int(gateway_id)
    except:
        print(f"{Colors.RED}Error: Invalid gateway ID{Colors.RESET}")
        return
    
    if gateway_id not in GATEWAYS:
        print(f"{Colors.RED}Error: Gateway {gateway_id} not available{Colors.RESET}")
        return
    
    # Extra params
    extra_params = {}
    
    if gateway_id == 9:
        checkout_url = input("Enter Stripe checkout URL: ").strip()
        if checkout_url:
            extra_params['checkout_url'] = checkout_url
    
    elif gateway_id == 10:
        gates_file = input("Enter gates file path: ").strip()
        if gates_file and os.path.exists(gates_file):
            gates = load_gates(gates_file)
            print(f"Loaded {len(gates)} gates")
            
            validate = input("Validate gates first? (y/n): ").strip().lower()
            if validate == 'y':
                print("Validating gates...")
                gm = init_gate_manager(gates_list=gates)
                # Validate first 1000
                working = validate_gates_parallel(gates[:1000])
                print(f"Found {len(working)} working gates")
            else:
                gm = init_gate_manager(gates_list=gates)
            
            extra_params['gate_manager'] = gm
    
    # Get threads
    threads = input(f"Enter threads (default {DEFAULT_THREADS}): ").strip()
    threads = int(threads) if threads.isdigit() else DEFAULT_THREADS
    threads = min(threads, MAX_THREADS)
    
    # Get limit
    limit = input("Enter card limit (empty for all): ").strip()
    limit = int(limit) if limit.isdigit() else None
    
    # Load and process
    cards = load_cards(cards_file, limit)
    print(f"\nLoaded {len(cards)} cards")
    print(f"Using Gateway {gateway_id}: {GATEWAYS[gateway_id]['name']}")
    print(f"Threads: {threads}")
    print("-" * 40)
    
    results = process_cards_parallel(
        cards, 
        gateway_id, 
        threads=threads, 
        extra_params=extra_params,
        callback=print_result
    )
    
    print_summary(results)

def main():
    parser = argparse.ArgumentParser(
        description='MADY VPS Checker v4.0 - Multi-Gate Shopify Support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use original Stripe gateway
  python3 mady_vps_checker_v4.py cards.txt --gateway 1
  
  # Use Stripe Checkout URL
  python3 mady_vps_checker_v4.py cards.txt --gateway 9 --checkout-url "URL"
  
  # Use Multi-Gate Shopify (15000+ gates)
  python3 mady_vps_checker_v4.py cards.txt --gateway 10 --gates-file gates.txt
  
  # Validate gates first
  python3 mady_vps_checker_v4.py cards.txt --gateway 10 --gates-file gates.txt --validate-gates
  
  # Interactive mode
  python3 mady_vps_checker_v4.py --interactive
        """
    )
    
    parser.add_argument('cards_file', nargs='?', help='Path to cards file')
    parser.add_argument('--gateway', '-g', type=int, default=1, help='Gateway ID (1-10)')
    parser.add_argument('--threads', '-t', type=int, default=DEFAULT_THREADS, help=f'Number of threads (default: {DEFAULT_THREADS})')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of cards')
    parser.add_argument('--checkout-url', help='Stripe checkout URL (for gateway 9)')
    parser.add_argument('--shop-url', help='Shopify store URL (for gateway 8)')
    parser.add_argument('--gates-file', help='Gates file for multi-gate Shopify (gateway 10)')
    parser.add_argument('--validate-gates', action='store_true', help='Validate gates before checking')
    parser.add_argument('--validate-limit', type=int, default=1000, help='Limit gates to validate (default: 1000)')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--list-gateways', action='store_true', help='List available gateways')
    parser.add_argument('--output', '-o', help='Output file for results')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet mode (less output)')
    
    args = parser.parse_args()
    
    # Print banner
    if not args.quiet:
        print_banner()
    
    # List gateways
    if args.list_gateways:
        print_gateways()
        return
    
    # Interactive mode
    if args.interactive:
        interactive_mode()
        return
    
    # Check cards file
    if not args.cards_file:
        parser.print_help()
        return
    
    if not os.path.exists(args.cards_file):
        print(f"{Colors.RED}Error: Cards file not found: {args.cards_file}{Colors.RESET}")
        return
    
    # Check gateway
    if args.gateway not in GATEWAYS:
        print(f"{Colors.RED}Error: Gateway {args.gateway} not available{Colors.RESET}")
        print_gateways()
        return
    
    # Prepare extra params
    extra_params = {}
    
    if args.checkout_url:
        extra_params['checkout_url'] = args.checkout_url
    
    if args.shop_url:
        extra_params['shop_url'] = args.shop_url
    
    # Multi-gate Shopify setup
    if args.gateway == 10:
        if not args.gates_file:
            print(f"{Colors.RED}Error: Gateway 10 requires --gates-file{Colors.RESET}")
            return
        
        if not os.path.exists(args.gates_file):
            print(f"{Colors.RED}Error: Gates file not found: {args.gates_file}{Colors.RESET}")
            return
        
        gates = load_gates(args.gates_file)
        print(f"Loaded {len(gates)} gates from {args.gates_file}")
        
        if args.validate_gates:
            print(f"Validating first {args.validate_limit} gates...")
            gm = init_gate_manager(gates_list=gates)
            working = validate_gates_parallel(gates[:args.validate_limit])
            print(f"Found {len(working)} working gates")
            for w in working:
                gm.mark_working(w['url'])
        else:
            gm = init_gate_manager(gates_list=gates)
        
        extra_params['gate_manager'] = gm
    
    # Load cards
    cards = load_cards(args.cards_file, args.limit)
    
    if not cards:
        print(f"{Colors.RED}Error: No cards loaded{Colors.RESET}")
        return
    
    # Print info
    threads = min(args.threads, MAX_THREADS)
    gateway_info = GATEWAYS[args.gateway]
    
    print(f"\n{Colors.CYAN}Configuration:{Colors.RESET}")
    print(f"  Cards:    {len(cards)}")
    print(f"  Gateway:  {args.gateway} - {gateway_info['name']} ({gateway_info['amount']})")
    print(f"  Threads:  {threads}")
    if args.gateway == 10:
        print(f"  Gates:    {len(gates)}")
    print("-" * 60)
    print()
    
    # Process
    callback = None if args.quiet else print_result
    
    results = process_cards_parallel(
        cards,
        args.gateway,
        threads=threads,
        extra_params=extra_params,
        callback=callback
    )
    
    # Print summary
    print_summary(results)
    
    # Save results
    if args.output:
        try:
            with open(args.output, 'w') as f:
                f.write(f"# MADY VPS Checker v4.0 Results\n")
                f.write(f"# Date: {datetime.now().isoformat()}\n")
                f.write(f"# Gateway: {args.gateway} - {gateway_info['name']}\n")
                f.write(f"# Total: {results['total']}\n\n")
                
                f.write("# APPROVED\n")
                for card, result in results['approved']:
                    f.write(f"{card}|{result}\n")
                
                f.write("\n# DECLINED\n")
                for card, result in results['declined']:
                    f.write(f"{card}|{result}\n")
                
                f.write("\n# ERRORS\n")
                for card, result in results['errors']:
                    f.write(f"{card}|{result}\n")
            
            print(f"\nResults saved to: {args.output}")
        except Exception as e:
            print(f"Error saving results: {e}")

if __name__ == '__main__':
    main()
