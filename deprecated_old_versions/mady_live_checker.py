#!/usr/bin/env python3
"""
MADY LIVE CHECKER v2.0
Live updating UI with purple borders, green approved, red declined
@MissNullMe
"""

import os
import sys
import time
import threading
from datetime import datetime
from collections import deque

# Add gateway path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '100$/100$/'))

# --- Colors ---
class C:
    PURPLE = '\033[95m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    CLEAR = '\033[2J'
    HOME = '\033[H'

# --- Gateway Import ---
try:
    from Charge3 import SaintVinsonDonateCheckout
    GATEWAY_FUNC = SaintVinsonDonateCheckout
    GATEWAY_NAME = "Saint Vinson $0.01"
except ImportError:
    print("Error: Could not import Charge3")
    sys.exit(1)

# --- Stats Class ---
class LiveStats:
    def __init__(self):
        self.total = 0
        self.current = 0
        self.approved = 0
        self.declined = 0
        self.cvv = 0
        self.insufficient = 0
        self.errors = 0
        self.current_card = ""
        self.current_result = ""
        self.approved_cards = deque(maxlen=100)
        self.start_time = time.time()
        self.lock = threading.Lock()
    
    def update(self, card, result, status):
        with self.lock:
            self.current += 1
            self.current_card = card
            self.current_result = result
            
            if status == 'approved':
                self.approved += 1
                self.approved_cards.append((card, result))
            elif status == 'cvv':
                self.cvv += 1
                self.approved_cards.append((card, result))
            elif status == 'insufficient':
                self.insufficient += 1
                self.approved_cards.append((card, result))
            elif status == 'error':
                self.errors += 1
            else:
                self.declined += 1
    
    def get_success_rate(self):
        if self.current == 0:
            return 0.0
        return ((self.approved + self.cvv + self.insufficient) / self.current) * 100
    
    def get_speed(self):
        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return 0.0
        return self.current / elapsed
    
    def get_elapsed(self):
        return time.time() - self.start_time

# --- UI Functions ---
def clear_screen():
    print(C.CLEAR + C.HOME, end='')

def draw_box(stats):
    """Draw the live stats box"""
    elapsed = stats.get_elapsed()
    speed = stats.get_speed()
    success_rate = stats.get_success_rate()
    
    # Mask card
    card_parts = stats.current_card.split('|')
    if len(card_parts) >= 4:
        card_num = card_parts[0]
        masked = f"{card_num[:6]}...{card_num[-4:]}|{card_parts[1]}|{card_parts[2]}|{card_parts[3]}"
    else:
        masked = stats.current_card
    
    # Result emoji
    result_lower = stats.current_result.lower()
    if 'charged' in result_lower or 'success' in result_lower:
        result_emoji = f"{C.GREEN}✅{C.RESET}"
    elif 'cvv' in result_lower or 'cvc' in result_lower:
        result_emoji = f"{C.YELLOW}🔐{C.RESET}"
    elif 'insufficient' in result_lower:
        result_emoji = f"{C.YELLOW}💰{C.RESET}"
    elif 'error' in result_lower:
        result_emoji = f"{C.YELLOW}⚠️{C.RESET}"
    else:
        result_emoji = f"{C.RED}❌{C.RESET}"
    
    # Calculate batch
    batch_size = 100
    current_batch = (stats.current // batch_size) + 1
    total_batches = (stats.total // batch_size) + 1
    
    # Build UI
    lines = []
    lines.append(f"{C.PURPLE}╔═══════════════════════════╦══════════════════════════════╗{C.RESET}")
    lines.append(f"{C.PURPLE}║{C.RESET} {C.CYAN}LIVE STATS{C.RESET}                {C.PURPLE}║{C.RESET} {C.CYAN}Mady v2.0 @MissNullMe{C.RESET}     {C.PURPLE}║{C.RESET}")
    lines.append(f"{C.PURPLE}╠═══════════════════════════╩══════════════════════════════╣{C.RESET}")
    lines.append(f"{C.PURPLE}║{C.RESET} Card: {masked:<45} {C.PURPLE}║{C.RESET}")
    lines.append(f"{C.PURPLE}║{C.RESET} Result: {result_emoji:<52} {C.PURPLE}║{C.RESET}")
    lines.append(f"{C.PURPLE}╠══════════════════════════════════════════════════════════╣{C.RESET}")
    lines.append(f"{C.PURPLE}║{C.RESET} Progress: {stats.current}/{stats.total} cards (Batch {current_batch}/{total_batches}){' '*(58-len(f'Progress: {stats.current}/{stats.total} cards (Batch {current_batch}/{total_batches})'))} {C.PURPLE}║{C.RESET}")
    lines.append(f"{C.PURPLE}╠══════════════════════════════════════════════════════════╣{C.RESET}")
    lines.append(f"{C.PURPLE}║{C.RESET} {C.GREEN}✓{C.RESET} {stats.approved:<3} {C.RED}✗{C.RESET} {stats.declined:<3} {C.YELLOW}CVV{C.RESET} {stats.cvv:<3} {C.YELLOW}Insuf{C.RESET} {stats.insufficient:<3} {C.YELLOW}Err{C.RESET} {stats.errors:<3}{' '*(58-len(f'✓ {stats.approved}   ✗ {stats.declined}   CVV {stats.cvv}   Insuf {stats.insufficient}   Err {stats.errors}'))} {C.PURPLE}║{C.RESET}")
    lines.append(f"{C.PURPLE}╠══════════════════════════════════════════════════════════╣{C.RESET}")
    lines.append(f"{C.PURPLE}║{C.RESET} Success: {success_rate:5.1f}%  Speed: {speed:5.2f} c/s  Time: {elapsed:8.1f}s  {C.PURPLE}║{C.RESET}")
    lines.append(f"{C.PURPLE}╚══════════════════════════════════════════════════════════╝{C.RESET}")
    
    return '\n'.join(lines)

def draw_approved_list(stats):
    """Draw approved cards list"""
    if not stats.approved_cards:
        return ""
    
    lines = []
    lines.append(f"\n{C.PURPLE}╔══════════════════════════════════════════════════════════╗{C.RESET}")
    lines.append(f"{C.PURPLE}║{C.RESET} {C.GREEN}✅ APPROVED CARDS ({len(stats.approved_cards)} total){C.RESET}{' '*(58-len(f'✅ APPROVED CARDS ({len(stats.approved_cards)} total)'))} {C.PURPLE}║{C.RESET}")
    lines.append(f"{C.PURPLE}╠══════════════════════════════════════════════════════════╣{C.RESET}")
    
    for i, (card, result) in enumerate(list(stats.approved_cards)[-20:], 1):  # Show last 20
        card_parts = card.split('|')
        if len(card_parts) >= 4:
            card_num = card_parts[0]
            masked = f"{card_num[:6]}...{card_num[-4:]}|{card_parts[1]}|{card_parts[2]}|{card_parts[3]}"
        else:
            masked = card
        
        # Determine status
        result_lower = result.lower()
        if 'charged' in result_lower or 'success' in result_lower:
            status_text = f"{C.GREEN}[CHARGED]{C.RESET}"
        elif 'cvv' in result_lower or 'cvc' in result_lower:
            status_text = f"{C.YELLOW}[CVV_MISMATCH]{C.RESET}"
        elif 'insufficient' in result_lower:
            status_text = f"{C.YELLOW}[INSUFFICIENT_FUNDS]{C.RESET}"
        else:
            status_text = f"{C.GREEN}[APPROVED]{C.RESET}"
        
        line = f"{C.PURPLE}║{C.RESET}   {i:2d}. {masked} {status_text}"
        # Pad to 58 chars (accounting for ANSI codes)
        padding = 58 - len(f"   {i:2d}. {masked} [STATUS]")
        line += ' ' * padding + f" {C.PURPLE}║{C.RESET}"
        lines.append(line)
    
    lines.append(f"{C.PURPLE}╚══════════════════════════════════════════════════════════╝{C.RESET}")
    
    return '\n'.join(lines)

def update_display(stats):
    """Update the display"""
    clear_screen()
    print(draw_box(stats))
    print(draw_approved_list(stats))
    sys.stdout.flush()

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

def check_card(card):
    """Check a single card"""
    try:
        result = GATEWAY_FUNC(card)
        return result
    except Exception as e:
        return f"Error: {str(e)[:50]}"

def categorize_result(result):
    """Categorize result"""
    result_lower = result.lower() if isinstance(result, str) else str(result).lower()
    
    if 'charged' in result_lower or 'success' in result_lower:
        return 'approved'
    elif 'cvv' in result_lower or 'cvc' in result_lower:
        return 'cvv'
    elif 'insufficient' in result_lower:
        return 'insufficient'
    elif 'error' in result_lower:
        return 'error'
    else:
        return 'declined'

def process_cards(cards, stats):
    """Process cards sequentially with live updates"""
    for card in cards:
        result = check_card(card)
        status = categorize_result(result)
        stats.update(card, result, status)
        update_display(stats)
        time.sleep(0.5)  # Rate limiting

# --- Main ---
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='MADY Live Checker v2.0')
    parser.add_argument('cards_file', help='Path to cards file')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of cards')
    parser.add_argument('--delay', '-d', type=float, default=0.5, help='Delay between checks (seconds)')
    
    args = parser.parse_args()
    
    # Load cards
    cards = load_cards(args.cards_file, args.limit)
    
    if not cards:
        print(f"{C.RED}Error: No cards loaded{C.RESET}")
        return
    
    # Initialize stats
    stats = LiveStats()
    stats.total = len(cards)
    
    # Clear screen and start
    clear_screen()
    print(f"{C.CYAN}MADY Live Checker v2.0{C.RESET}")
    print(f"Gateway: {GATEWAY_NAME}")
    print(f"Cards: {len(cards)}")
    print(f"Starting in 3 seconds...")
    time.sleep(3)
    
    # Process cards
    try:
        process_cards(cards, stats)
    except KeyboardInterrupt:
        print(f"\n\n{C.YELLOW}Interrupted by user{C.RESET}")
    
    # Final display
    update_display(stats)
    print(f"\n{C.GREEN}Checking complete!{C.RESET}")
    print(f"Total: {stats.total} | Approved: {stats.approved + stats.cvv + stats.insufficient} | Declined: {stats.declined}")

if __name__ == '__main__':
    main()
