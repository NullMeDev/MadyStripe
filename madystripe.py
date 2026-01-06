#!/usr/bin/env python3
"""
MadyStripe Unified v3.0
The ultimate card checking tool with CLI and Telegram bot interfaces

@MissNullMe
"""

import sys
import os
import argparse

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.gateways import get_gateway_manager


def print_banner():
    """Print MadyStripe banner"""
    # Simple banner without ASCII art
    pass


def run_cli_mode(args):
    """Run CLI interface"""
    from interfaces.cli import run_cli
    
    run_cli(
        cards_file=args.cards_file,
        gateway=args.gateway,
        limit=args.limit,
        delay=args.delay,
        output=args.output
    )


def run_bot_mode(args):
    """Run Telegram bot interface"""
    from interfaces.telegram_bot import run_telegram_bot
    
    # Get config from args or use defaults
    bot_token = args.bot_token or "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
    
    group_ids = args.group_ids or ["-1003538559040", "-4997223070", "-1003643720778"]
    if isinstance(group_ids, str):
        group_ids = [g.strip() for g in group_ids.split(',')]
    
    bot_credit = args.bot_credit or "@MissNullMe"
    
    run_telegram_bot(bot_token, group_ids, bot_credit)


def list_gateways():
    """List available gateways"""
    manager = get_gateway_manager()
    
    print("\n╔══════════════════════════════════════════════════════════════════╗")
    print("║                      AVAILABLE GATEWAYS                          ║")
    print("╚══════════════════════════════════════════════════════════════════╝\n")
    
    for gate in manager.list_gateways():
        print(f"  [{gate['id']}] {gate['name']}")
        print(f"      💰 Charge: {gate['charge']}")
        print(f"      ⚡ Speed: {gate['speed']}")
        print(f"      📊 Success Rate: {gate['success_rate']:.1f}%")
        print(f"      📝 {gate['description']}")
        print()


def show_info():
    """Show system information"""
    manager = get_gateway_manager()
    
    print("\n╔══════════════════════════════════════════════════════════════════╗")
    print("║                      SYSTEM INFORMATION                          ║")
    print("╚══════════════════════════════════════════════════════════════════╝\n")
    
    print(f"  Version: 3.0.0")
    print(f"  Author: @MissNullMe")
    print(f"  Available Gateways: {len(manager.list_gateways())}")
    print(f"  Default Gateway: {manager.default_gateway}")
    print()
    
    print("  Features:")
    print("    ✓ Multiple advanced gateways")
    print("    ✓ Beautiful CLI with live updates")
    print("    ✓ Telegram bot integration")
    print("    ✓ Card type detection (2D/3D/3DS)")
    print("    ✓ Real-time statistics")
    print("    ✓ Batch processing")
    print("    ✓ Result export (TXT/JSON/CSV)")
    print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='MadyStripe Unified v3.0 - Advanced Card Checker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # CLI Mode (with beautiful live UI)
  %(prog)s cli cards.txt
  %(prog)s cli cards.txt -g staleks -l 100
  %(prog)s cli cards.txt -o results.txt
  
  # Telegram Bot Mode
  %(prog)s bot
  %(prog)s bot --bot-token YOUR_TOKEN
  
  # List gateways
  %(prog)s --list-gateways
  
  # Show info
  %(prog)s --info

For more help on a specific mode:
  %(prog)s cli --help
  %(prog)s bot --help
        """
    )
    
    # Global options
    parser.add_argument('--list-gateways', action='store_true', help='List available gateways')
    parser.add_argument('--info', action='store_true', help='Show system information')
    parser.add_argument('--version', action='version', version='MadyStripe v3.0.0')
    
    # Subparsers for modes
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    
    # CLI mode
    cli_parser = subparsers.add_parser('cli', help='Run CLI interface')
    cli_parser.add_argument('cards_file', help='Path to cards file')
    cli_parser.add_argument('-g', '--gateway', help='Gateway ID (staleks, shopify, etc.)')
    cli_parser.add_argument('-l', '--limit', type=int, help='Limit number of cards')
    cli_parser.add_argument('-d', '--delay', type=float, default=0.5, help='Delay between checks (seconds)')
    cli_parser.add_argument('-o', '--output', help='Output file path')
    
    # Bot mode
    bot_parser = subparsers.add_parser('bot', help='Run Telegram bot')
    bot_parser.add_argument('--bot-token', help='Telegram bot token')
    bot_parser.add_argument('--group-ids', help='Comma-separated group IDs')
    bot_parser.add_argument('--bot-credit', help='Bot credit text')
    
    args = parser.parse_args()
    
    # No banner needed
    
    # Handle global options
    if args.list_gateways:
        list_gateways()
        return
    
    if args.info:
        show_info()
        return
    
    # Handle modes
    if args.mode == 'cli':
        run_cli_mode(args)
    elif args.mode == 'bot':
        run_bot_mode(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
