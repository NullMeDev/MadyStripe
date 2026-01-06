"""
CLI Interface - Beautiful live UI for card checking
Based on mady_live_checker_v2.py with enhancements
"""

import os
import sys
import time
import re
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.checker import CardChecker, CheckerStats, load_cards_from_file, save_results
from core.gateways import get_gateway_manager


# --- Colors ---
class Colors:
    PURPLE = '\033[95m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    CLEAR = '\033[2J'
    HOME = '\033[H'


# --- UI Functions ---
def clear_screen():
    """Clear the terminal screen"""
    print(Colors.CLEAR + Colors.HOME, end='')


def pad_line(text: str, width: int = 70) -> str:
    """Pad line to exact width, accounting for ANSI codes"""
    clean_text = re.sub(r'\033\[[0-9;]+m', '', text)
    padding_needed = width - len(clean_text)
    return text + (' ' * max(0, padding_needed))


def format_time(seconds: float) -> str:
    """Format seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def draw_header():
    """Draw the header - removed to avoid duplication"""
    return ""


def draw_stats_box(checker: CardChecker):
    """Draw the live stats box"""
    stats = checker.stats
    current_result = None
    
    # Get current card info
    if stats.results:
        current_result = stats.results[-1]
    
    # Calculate progress
    progress_pct = (stats.checked / stats.total * 100) if stats.total > 0 else 0
    
    # Build UI
    lines = []
    lines.append(f"{Colors.PURPLE}╔══════════════════════════════════════════════════════════════════╗{Colors.RESET}")
    lines.append(f"{Colors.PURPLE}║{Colors.RESET} {Colors.CYAN}{Colors.BOLD}LIVE STATS{Colors.RESET}                                                       {Colors.PURPLE}║{Colors.RESET}")
    lines.append(f"{Colors.PURPLE}╠══════════════════════════════════════════════════════════════════╣{Colors.RESET}")
    
    # Current card
    if current_result:
        card_display = current_result.card
        result_emoji = get_result_emoji(current_result)
        
        card_line = f"{Colors.PURPLE}║{Colors.RESET} Card: {card_display}"
        lines.append(pad_line(card_line, 69) + f" {Colors.PURPLE}║{Colors.RESET}")
        
        result_line = f"{Colors.PURPLE}║{Colors.RESET} Result: {result_emoji} {current_result.message[:40]}"
        lines.append(pad_line(result_line, 69) + f" {Colors.PURPLE}║{Colors.RESET}")
        
        type_line = f"{Colors.PURPLE}║{Colors.RESET} Type: {get_card_type_emoji(current_result.card_type)} {current_result.card_type} | Gateway: {current_result.gateway[:20]}"
        lines.append(pad_line(type_line, 69) + f" {Colors.PURPLE}║{Colors.RESET}")
    else:
        waiting_line = f"{Colors.PURPLE}║{Colors.RESET} {Colors.YELLOW}Waiting for first card...{Colors.RESET}"
        lines.append(pad_line(waiting_line, 69) + f" {Colors.PURPLE}║{Colors.RESET}")
    
    lines.append(f"{Colors.PURPLE}╠══════════════════════════════════════════════════════════════════╣{Colors.RESET}")
    
    # Progress bar
    progress_text = f"Progress: {stats.checked}/{stats.total} ({progress_pct:.1f}%)"
    progress_line = f"{Colors.PURPLE}║{Colors.RESET} {progress_text}"
    lines.append(pad_line(progress_line, 69) + f" {Colors.PURPLE}║{Colors.RESET}")
    
    # Progress bar visual
    bar_width = 50
    filled = int(bar_width * progress_pct / 100)
    bar = f"{Colors.GREEN}{'█' * filled}{Colors.WHITE}{'░' * (bar_width - filled)}{Colors.RESET}"
    bar_line = f"{Colors.PURPLE}║{Colors.RESET} {bar}"
    lines.append(pad_line(bar_line, 69) + f" {Colors.PURPLE}║{Colors.RESET}")
    
    lines.append(f"{Colors.PURPLE}╠══════════════════════════════════════════════════════════════════╣{Colors.RESET}")
    
    # Stats
    stats_text = f"{Colors.GREEN}✓{Colors.RESET} {stats.approved}  {Colors.RED}✗{Colors.RESET} {stats.declined}  {Colors.YELLOW}CVV{Colors.RESET} {stats.cvv_mismatch}  {Colors.YELLOW}Insuf{Colors.RESET} {stats.insufficient_funds}  {Colors.YELLOW}Err{Colors.RESET} {stats.errors}"
    stats_line = f"{Colors.PURPLE}║{Colors.RESET} {stats_text}"
    lines.append(pad_line(stats_line, 69) + f" {Colors.PURPLE}║{Colors.RESET}")
    
    lines.append(f"{Colors.PURPLE}╠══════════════════════════════════════════════════════════════════╣{Colors.RESET}")
    
    # Metrics
    success_rate = stats.get_success_rate()
    live_rate = stats.get_live_rate()
    speed = stats.get_speed()
    elapsed = stats.get_elapsed()
    eta = stats.get_eta()
    
    metrics1 = f"Success: {success_rate:5.1f}%  Live: {live_rate:5.1f}%  Speed: {speed:5.2f} c/s"
    metrics1_line = f"{Colors.PURPLE}║{Colors.RESET} {metrics1}"
    lines.append(pad_line(metrics1_line, 69) + f" {Colors.PURPLE}║{Colors.RESET}")
    
    metrics2 = f"Elapsed: {format_time(elapsed)}  ETA: {format_time(eta)}"
    metrics2_line = f"{Colors.PURPLE}║{Colors.RESET} {metrics2}"
    lines.append(pad_line(metrics2_line, 69) + f" {Colors.PURPLE}║{Colors.RESET}")
    
    lines.append(f"{Colors.PURPLE}╚══════════════════════════════════════════════════════════════════╝{Colors.RESET}")
    
    return '\n'.join(lines)


def draw_live_cards(checker: CardChecker, limit: int = 15):
    """Draw approved/live cards list"""
    live_cards = checker.stats.get_live_cards(limit)
    
    if not live_cards:
        return ""
    
    lines = []
    lines.append(f"\n{Colors.PURPLE}╔══════════════════════════════════════════════════════════════════╗{Colors.RESET}")
    
    header_text = f"{Colors.GREEN}✅ LIVE CARDS ({len(checker.stats.get_live_cards())} total){Colors.RESET}"
    header_line = f"{Colors.PURPLE}║{Colors.RESET} {header_text}"
    lines.append(pad_line(header_line, 69) + f" {Colors.PURPLE}║{Colors.RESET}")
    
    lines.append(f"{Colors.PURPLE}╠══════════════════════════════════════════════════════════════════╣{Colors.RESET}")
    
    for i, result in enumerate(live_cards[-limit:], 1):
        emoji = get_result_emoji(result)
        type_emoji = get_card_type_emoji(result.card_type)
        
        card_line = f"{Colors.PURPLE}║{Colors.RESET} {i:2d}. {result.card} {emoji} {type_emoji}"
        lines.append(pad_line(card_line, 69) + f" {Colors.PURPLE}║{Colors.RESET}")
    
    lines.append(f"{Colors.PURPLE}╚══════════════════════════════════════════════════════════════════╝{Colors.RESET}")
    
    return '\n'.join(lines)


def get_result_emoji(result) -> str:
    """Get emoji for result"""
    msg_lower = result.message.lower()
    
    if result.status == 'approved':
        if 'cvv' in msg_lower or 'cvc' in msg_lower:
            return f"{Colors.YELLOW}🔐{Colors.RESET}"
        elif 'insufficient' in msg_lower:
            return f"{Colors.YELLOW}💰{Colors.RESET}"
        else:
            return f"{Colors.GREEN}✅{Colors.RESET}"
    elif result.status == 'error':
        return f"{Colors.YELLOW}⚠️{Colors.RESET}"
    else:
        return f"{Colors.RED}❌{Colors.RESET}"


def get_card_type_emoji(card_type: str) -> str:
    """Get emoji for card type"""
    if card_type == "2D":
        return "🔓"
    elif card_type == "3D":
        return "🔐"
    elif card_type == "3DS":
        return "🛡️"
    else:
        return "❓"


def update_display(checker: CardChecker):
    """Update the full display"""
    clear_screen()
    print(draw_stats_box(checker))
    print(draw_live_cards(checker))
    sys.stdout.flush()


def run_cli(cards_file: str, gateway: str = None, limit: int = None, delay: float = 0.5, output: str = None):
    """
    Run the CLI interface
    
    Args:
        cards_file: Path to cards file
        gateway: Gateway ID to use
        limit: Limit number of cards
        delay: Delay between checks
        output: Output file path (optional)
    """
    # Load cards
    print(f"{Colors.CYAN}Loading cards from {cards_file}...{Colors.RESET}")
    
    try:
        valid_cards, invalid_cards = load_cards_from_file(cards_file, limit)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")
        return
    
    if invalid_cards:
        print(f"{Colors.YELLOW}Warning: {len(invalid_cards)} invalid cards skipped{Colors.RESET}")
    
    if not valid_cards:
        print(f"{Colors.RED}Error: No valid cards found{Colors.RESET}")
        return
    
    print(f"{Colors.GREEN}Loaded {len(valid_cards)} valid cards{Colors.RESET}")
    
    # Get gateway info
    gateway_manager = get_gateway_manager()
    gateway_obj = gateway_manager.get_gateway(gateway)
    
    if not gateway_obj:
        print(f"{Colors.RED}Error: Gateway not found{Colors.RESET}")
        return
    
    print(f"{Colors.CYAN}Using gateway: {gateway_obj.name} ({gateway_obj.charge_amount}){Colors.RESET}")
    print(f"{Colors.CYAN}Rate limit: {delay}s between checks{Colors.RESET}")
    print()
    print(f"{Colors.YELLOW}Starting in 3 seconds... (Press Ctrl+C to stop){Colors.RESET}")
    time.sleep(3)
    
    # Create checker
    checker = CardChecker(gateway_id=gateway, rate_limit=delay)
    checker.stats.total = len(valid_cards)
    
    # Start checking
    try:
        clear_screen()
        
        # Check cards with live updates
        results = []
        for i, card in enumerate(valid_cards, 1):
            result = checker.check_single(card)
            results.append(result)
            
            # Update display
            update_display(checker)
            
            # Rate limiting
            if i < len(valid_cards):
                time.sleep(delay)
        
        # Final display
        update_display(checker)
        
        # Summary
        print()
        print(f"{Colors.GREEN}{Colors.BOLD}✓ CHECKING COMPLETE!{Colors.RESET}")
        print()
        print(f"Total: {len(results)} cards")
        print(f"{Colors.GREEN}Approved: {checker.stats.approved}{Colors.RESET}")
        print(f"{Colors.YELLOW}CVV Mismatch: {checker.stats.cvv_mismatch}{Colors.RESET}")
        print(f"{Colors.YELLOW}Insufficient Funds: {checker.stats.insufficient_funds}{Colors.RESET}")
        print(f"{Colors.RED}Declined: {checker.stats.declined}{Colors.RESET}")
        print(f"{Colors.YELLOW}Errors: {checker.stats.errors}{Colors.RESET}")
        print()
        print(f"Success Rate: {checker.stats.get_success_rate():.1f}%")
        print(f"Live Rate: {checker.stats.get_live_rate():.1f}%")
        print(f"Average Speed: {checker.stats.get_speed():.2f} cards/sec")
        print(f"Total Time: {format_time(checker.stats.get_elapsed())}")
        
        # Save results
        if output:
            print()
            print(f"{Colors.CYAN}Saving results to {output}...{Colors.RESET}")
            save_results(results, output)
            print(f"{Colors.GREEN}Results saved!{Colors.RESET}")
        
    except KeyboardInterrupt:
        print()
        print(f"{Colors.YELLOW}Interrupted by user{Colors.RESET}")
        checker.stop()
        
        # Show partial results
        if checker.stats.checked > 0:
            print()
            print(f"Checked {checker.stats.checked}/{len(valid_cards)} cards")
            print(f"Approved: {checker.stats.approved}")
            print(f"Declined: {checker.stats.declined}")
            print(f"Errors: {checker.stats.errors}")


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='MadyStripe CLI - Beautiful live card checker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s cards.txt                    # Check with default gateway
  %(prog)s cards.txt -g staleks         # Use Staleks gateway
  %(prog)s cards.txt -l 100             # Limit to 100 cards
  %(prog)s cards.txt -d 1.0             # 1 second delay
  %(prog)s cards.txt -o results.txt     # Save results
        """
    )
    
    parser.add_argument('cards_file', help='Path to cards file')
    parser.add_argument('-g', '--gateway', help='Gateway ID (staleks, shopify, etc.)')
    parser.add_argument('-l', '--limit', type=int, help='Limit number of cards')
    parser.add_argument('-d', '--delay', type=float, default=0.5, help='Delay between checks (seconds)')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('--list-gateways', action='store_true', help='List available gateways')
    
    args = parser.parse_args()
    
    # List gateways
    if args.list_gateways:
        gateway_manager = get_gateway_manager()
        print(f"{Colors.CYAN}{Colors.BOLD}Available Gateways:{Colors.RESET}\n")
        for gate in gateway_manager.list_gateways():
            print(f"  {Colors.GREEN}[{gate['id']}]{Colors.RESET} {gate['name']}")
            print(f"      Charge: {gate['charge']} | Speed: {gate['speed']}")
            print(f"      {gate['description']}")
            print()
        return
    
    # Run checker
    run_cli(
        cards_file=args.cards_file,
        gateway=args.gateway,
        limit=args.limit,
        delay=args.delay,
        output=args.output
    )


if __name__ == '__main__':
    main()
