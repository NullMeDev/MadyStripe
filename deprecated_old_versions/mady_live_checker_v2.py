#!/usr/bin/env python3
"""
MADY LIVE CHECKER v2.0
Live updating UI with purple borders, green approved, red declined
Uses Staleks Florida Gateway ($0.01)
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
    from Charge5 import StaleksFloridaCheckoutVNew
    GATEWAY_FUNC = StaleksFloridaCheckoutVNew
    GATEWAY_NAME = "Staleks Florida $0.01"
except ImportError:
    print("Error: Could not import Charge5")
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

def pad_line(text, width=60):
    """Pad line to exact width, accounting for ANSI codes"""
    # Remove ANSI codes to count actual characters
    import re
    clean_text = re.sub(r'\033\[[0-9;]+m', '', text)
    padding_needed = width - len(clean_text)
    return text + (' ' * max(0, padding_needed))

def draw_box(stats):
    """Draw the live stats box with perfect alignment"""
    elapsed = stats.get_elapsed()
    speed = stats.get_speed()
    success_rate = stats.get_success_rate()
    
    # Show full card (no masking - private tool)
    full_card = stats.current_card if stats.current_card else "Waiting..."
    
    # Result emoji
    result_lower = stats.current_result.lower()
    if 'charged' in result_lower or 'success' in result_lower or 'approved' in result_lower:
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
    current_batch = (stats.current // batch_size) + 1 if stats.current > 0 else 1
    total_batches = (stats.total // batch_size) + 1
    
    # Build UI with exact 60-char width
    lines = []
    lines.append(f"{C.PURPLE}╔═══════════════════════════╦══════════════════════════════╗{C.RESET}")
    lines.append(f"{C.PURPLE}║{C.RESET} {C.CYAN}LIVE STATS{C.RESET}                {C.PURPLE}║{C.RESET} {C.CYAN}Mady v2.0 @MissNullMe{C.RESET}     {C.PURPLE}║{C.RESET}")
    lines.append(f"{C.PURPLE}╠═══════════════════════════╩══════════════════════════════╣{C.RESET}")
    
    # Card line (full card number shown)
    card_line = f"{C.PURPLE}║{C.RESET} Card: {full_card}"
    lines.append(pad_line(card_line, 59) + f" {C.PURPLE}║{C.RESET}")
    
    # Result line
    result_line = f"{C.PURPLE}║{C.RESET} Result: {result_emoji}"
    lines.append(pad_line(result_line, 59) + f" {C.PURPLE}║{C.RESET}")
    
    lines.append(f"{C.PURPLE}╠══════════════════════════════════════════════════════════╣{C.RESET}")
    
    # Progress line
    progress_text = f"Progress: {stats.current}/{stats.total} cards (Batch {current_batch}/{total_batches})"
    progress_line = f"{C.PURPLE}║{C.RESET} {progress_text}"
    lines.append(pad_line(progress_line, 59) + f" {C.PURPLE}║{C.RESET}")
    
    lines.append(f"{C.PURPLE}╠══════════════════════════════════════════════════════════╣{C.RESET}")
    
    # Stats line
    stats_text = f"{C.GREEN}✓{C.RESET} {stats.approved}   {C.RED}✗{C.RESET} {stats.declined}   {C.YELLOW}CVV{C.RESET} {stats.cvv}   {C.YELLOW}Insuf{C.RESET} {stats.insufficient}   {C.YELLOW}Err{C.RESET} {stats.errors}"
    stats_line = f"{C.PURPLE}║{C.RESET} {stats_text}"
    lines.append(pad_line(stats_line, 59) + f" {C.PURPLE}║{C.RESET}")
    
    lines.append(f"{C.PURPLE}╠══════════════════════════════════════════════════════════╣{C.RESET}")
    
    # Metrics line
    metrics_text = f"Success: {success_rate:5.1f}%  Speed: {speed:5.2f} c/s  Time: {elapsed:8.1f}s"
    metrics_line = f"{C.PURPLE}║{C.RESET} {metrics_text}"
    lines.append(pad_line(metrics_line, 59) + f" {C.PURPLE}║{C.RESET}")
    
    lines.append(f"{C.PURPLE}╚══════════════════════════════════════════════════════════╝{C.RESET}")
    
    return '\n'.join(lines)

def draw_approved_list(stats):
    """Draw approved cards list with perfect alignment"""
    if not stats.approved_cards:
        return ""
    
    lines = []
    lines.append(f"\n{C.PURPLE}╔══════════════════════════════════════════════════════════╗{C.RESET}")
    
    header_text = f"{C.GREEN}✅ APPROVED CARDS ({len(stats.approved_cards)} total){C.RESET}"
    header_line = f"{C.PURPLE}║{C.RESET} {header_text}"
    lines.append(pad_line(header_line, 59) + f" {C.PURPLE}║{C.RESET}")
    
    lines.append(f"{C.PURPLE}╠══════════════════════════════════════════════════════════╣{C.RESET}")
    
    for i, (card, result) in enumerate(list(stats.approved_cards)[-20:], 1):
        # Show full card (no masking - private tool)
        full_card = card
        
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
        
        card_line = f"{C.PURPLE}║{C.RESET}   {i:2d}. {full_card} {status_text}"
        lines.append(pad_line(card_line, 59) + f" {C.PURPLE}║{C.RESET}")
    
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
        
        # Handle dict response from Staleks
        if isinstance(result, dict):
            if result.get('result') == 'success' or 'success' in str(result).lower():
                return "Approved"
            elif 'error' in result:
                return f"Declined ({result.get('error', 'Unknown')})"
            else:
                return str(result)
        
        return result
    except Exception as e:
        return f"Error: {str(e)[:50]}"

def categorize_result(result):
    """Categorize result"""
    result_lower = result.lower() if isinstance(result, str) else str(result).lower()
    
    if any(x in result_lower for x in ['charged', 'success', 'approved']):
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
    
    parser = argparse.ArgumentParser(description='MADY Live Checker v2.0 - Staleks Gateway')
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
