#!/usr/bin/env python3
"""
Comprehensive Gateway Testing Script
Tests all available gateways with provided test cards
"""

import sys
import os
import time
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.gateways import get_gateway_manager
from core.checker import CardChecker, load_cards_from_file


def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_subheader(text):
    """Print a formatted subheader"""
    print("\n" + "-"*70)
    print(f"  {text}")
    print("-"*70)


def test_gateway(gateway_id, cards, delay=1.0):
    """Test a specific gateway with cards"""
    manager = get_gateway_manager()
    gateway = manager.get_gateway(gateway_id)
    
    if not gateway:
        print(f"  ✗ Gateway '{gateway_id}' not found")
        return None
    
    print(f"\n  Gateway: {gateway.name}")
    print(f"  Charge: {gateway.charge_amount}")
    print(f"  Speed: {gateway.speed}")
    print(f"  Testing with {len(cards)} cards...")
    print()
    
    # Create checker
    checker = CardChecker(gateway_id=gateway_id, rate_limit=delay)
    checker.stats.total = len(cards)
    
    # Track results
    results = {
        'approved': [],
        'declined': [],
        'errors': [],
        'cvv': [],
        'insufficient': []
    }
    
    start_time = time.time()
    
    # Check each card
    for i, card in enumerate(cards, 1):
        print(f"  [{i}/{len(cards)}] Checking {card[:19]}...", end=" ")
        
        result = checker.check_single(card)
        
        # Categorize result
        msg_lower = result.message.lower()
        
        if result.status == 'approved':
            if 'cvv' in msg_lower or 'cvc' in msg_lower:
                results['cvv'].append(result)
                print(f"🔐 CVV - {result.message[:40]}")
            elif 'insufficient' in msg_lower:
                results['insufficient'].append(result)
                print(f"💰 INSUF - {result.message[:40]}")
            else:
                results['approved'].append(result)
                print(f"✅ APPROVED - {result.message[:40]}")
        elif result.status == 'error':
            results['errors'].append(result)
            print(f"⚠️  ERROR - {result.message[:40]}")
        else:
            results['declined'].append(result)
            print(f"❌ DECLINED - {result.message[:40]}")
        
        # Rate limiting
        if i < len(cards):
            time.sleep(delay)
    
    elapsed = time.time() - start_time
    
    # Print summary
    print()
    print(f"  Summary:")
    print(f"    ✅ Approved: {len(results['approved'])}")
    print(f"    🔐 CVV Mismatch: {len(results['cvv'])}")
    print(f"    💰 Insufficient: {len(results['insufficient'])}")
    print(f"    ❌ Declined: {len(results['declined'])}")
    print(f"    ⚠️  Errors: {len(results['errors'])}")
    print(f"    📊 Success Rate: {checker.stats.get_success_rate():.1f}%")
    print(f"    📈 Live Rate: {checker.stats.get_live_rate():.1f}%")
    print(f"    ⚡ Speed: {checker.stats.get_speed():.2f} c/s")
    print(f"    ⏱️  Time: {elapsed:.1f}s")
    
    return {
        'gateway': gateway.name,
        'gateway_id': gateway_id,
        'results': results,
        'stats': checker.stats.to_dict(),
        'elapsed': elapsed
    }


def main():
    """Main test function"""
    print_header("MADYSTRIPE UNIFIED - COMPREHENSIVE GATEWAY TEST")
    
    # Load test cards
    cards_file = 'test_cards_comprehensive.txt'
    
    print(f"\n📁 Loading test cards from: {cards_file}")
    
    try:
        valid_cards, invalid_cards = load_cards_from_file(cards_file)
    except Exception as e:
        print(f"❌ Error loading cards: {e}")
        return 1
    
    if invalid_cards:
        print(f"⚠️  Warning: {len(invalid_cards)} invalid cards skipped")
    
    if not valid_cards:
        print(f"❌ No valid cards found")
        return 1
    
    print(f"✅ Loaded {len(valid_cards)} valid cards")
    
    # Get available gateways
    manager = get_gateway_manager()
    gateways = manager.list_gateways()
    
    print(f"\n🔧 Found {len(gateways)} available gateways")
    
    # Test each gateway
    all_results = []
    
    for i, gate_info in enumerate(gateways, 1):
        print_subheader(f"Testing Gateway {i}/{len(gateways)}: {gate_info['name']}")
        
        try:
            result = test_gateway(gate_info['id'], valid_cards, delay=0.5)
            if result:
                all_results.append(result)
        except KeyboardInterrupt:
            print("\n\n⚠️  Testing interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error testing gateway: {e}")
            import traceback
            traceback.print_exc()
    
    # Final summary
    print_header("FINAL TEST SUMMARY")
    
    if not all_results:
        print("\n❌ No gateways were successfully tested")
        return 1
    
    print(f"\n✅ Tested {len(all_results)} gateways with {len(valid_cards)} cards each")
    print()
    
    # Summary table
    print("  Gateway Performance:")
    print("  " + "-"*66)
    print(f"  {'Gateway':<25} {'Success':<10} {'Live':<10} {'Speed':<10}")
    print("  " + "-"*66)
    
    for result in all_results:
        gateway_name = result['gateway'][:24]
        success_rate = result['stats']['success_rate']
        live_rate = result['stats']['live_rate']
        speed = result['stats']['speed']
        
        print(f"  {gateway_name:<25} {success_rate:>6.1f}%    {live_rate:>6.1f}%    {speed:>6.2f} c/s")
    
    print("  " + "-"*66)
    
    # Best gateway
    best_gateway = max(all_results, key=lambda x: x['stats']['live_rate'])
    print(f"\n🏆 Best Gateway (by live rate): {best_gateway['gateway']}")
    print(f"   Live Rate: {best_gateway['stats']['live_rate']:.1f}%")
    print(f"   Success Rate: {best_gateway['stats']['success_rate']:.1f}%")
    print(f"   Speed: {best_gateway['stats']['speed']:.2f} c/s")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"gateway_test_report_{timestamp}.txt"
    
    print(f"\n💾 Saving detailed report to: {report_file}")
    
    with open(report_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("MADYSTRIPE UNIFIED - COMPREHENSIVE GATEWAY TEST REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Test Cards: {len(valid_cards)}\n")
        f.write(f"Gateways Tested: {len(all_results)}\n\n")
        
        for result in all_results:
            f.write("-"*70 + "\n")
            f.write(f"Gateway: {result['gateway']} ({result['gateway_id']})\n")
            f.write("-"*70 + "\n")
            
            stats = result['stats']
            f.write(f"Total Checked: {stats['checked']}\n")
            f.write(f"Approved: {stats['approved']}\n")
            f.write(f"CVV Mismatch: {stats['cvv_mismatch']}\n")
            f.write(f"Insufficient Funds: {stats['insufficient_funds']}\n")
            f.write(f"Declined: {stats['declined']}\n")
            f.write(f"Errors: {stats['errors']}\n")
            f.write(f"Success Rate: {stats['success_rate']:.1f}%\n")
            f.write(f"Live Rate: {stats['live_rate']:.1f}%\n")
            f.write(f"Speed: {stats['speed']:.2f} cards/sec\n")
            f.write(f"Time: {result['elapsed']:.1f}s\n\n")
            
            # List approved cards
            results_data = result['results']
            if results_data['approved'] or results_data['cvv'] or results_data['insufficient']:
                f.write("Live Cards:\n")
                for r in results_data['approved']:
                    f.write(f"  ✅ {r.card} - {r.message}\n")
                for r in results_data['cvv']:
                    f.write(f"  🔐 {r.card} - {r.message}\n")
                for r in results_data['insufficient']:
                    f.write(f"  💰 {r.card} - {r.message}\n")
                f.write("\n")
    
    print(f"✅ Report saved!")
    
    print("\n" + "="*70)
    print("✅ COMPREHENSIVE TESTING COMPLETE!")
    print("="*70)
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
