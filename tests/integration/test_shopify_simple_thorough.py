"""
Thorough testing of SimpleShopifyGateway
Tests multiple stores, cards, and scenarios
"""

import sys
import time
import json
from datetime import datetime
from core.shopify_simple_gateway import SimpleShopifyGateway


def test_gateway_comprehensive():
    """Comprehensive gateway testing"""
    
    print("="*80)
    print("SHOPIFY SIMPLE GATEWAY - COMPREHENSIVE TEST")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize gateway
    print("[1/6] Initializing gateway...")
    gateway = SimpleShopifyGateway()
    print(f"✅ Gateway initialized")
    print(f"   Stores loaded: {len(gateway.stores)}")
    print()
    
    # Test cards (various scenarios)
    test_cards = [
        {
            'card': '4111111111111111|12|25|123',
            'name': 'Test Visa (will decline)',
            'expected': 'declined'
        },
        {
            'card': '5555555555554444|12|25|123',
            'name': 'Test Mastercard (will decline)',
            'expected': 'declined'
        },
        {
            'card': '378282246310005|12|25|1234',
            'name': 'Test Amex (will decline)',
            'expected': 'declined'
        },
    ]
    
    results = []
    
    # Test each card
    for i, test in enumerate(test_cards, 1):
        print(f"[{i+1}/6] Testing: {test['name']}")
        print(f"   Card: {test['card'][:4]}...{test['card'][-7:]}")
        print(f"   Max attempts: 10 stores")
        print()
        
        start_time = time.time()
        
        try:
            status, message, card_type = gateway.check(
                test['card'],
                max_attempts=10  # Try up to 10 stores
            )
            
            elapsed = time.time() - start_time
            
            result = {
                'card_name': test['name'],
                'card_masked': test['card'][:4] + '...' + test['card'][-7:],
                'status': status,
                'message': message,
                'card_type': card_type,
                'elapsed_seconds': round(elapsed, 2),
                'expected': test['expected'],
                'match': status == test['expected']
            }
            
            results.append(result)
            
            print(f"   Result: {status.upper()}")
            print(f"   Message: {message}")
            print(f"   Card Type: {card_type}")
            print(f"   Time: {elapsed:.2f}s")
            print(f"   Expected: {test['expected']} | Match: {'✅' if result['match'] else '❌'}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            result = {
                'card_name': test['name'],
                'card_masked': test['card'][:4] + '...' + test['card'][-7:],
                'status': 'error',
                'message': str(e),
                'card_type': 'Unknown',
                'elapsed_seconds': 0,
                'expected': test['expected'],
                'match': False
            }
            results.append(result)
        
        print()
        time.sleep(2)  # Rate limiting
    
    # Test store fallback
    print(f"[5/6] Testing store fallback mechanism...")
    print("   Testing with 5 attempts to verify fallback works")
    print()
    
    fallback_start = time.time()
    status, message, card_type = gateway.check(
        '4111111111111111|12|25|123',
        max_attempts=5
    )
    fallback_elapsed = time.time() - fallback_start
    
    print(f"   Fallback test completed in {fallback_elapsed:.2f}s")
    print(f"   Status: {status}")
    print()
    
    # Get statistics
    print(f"[6/6] Gateway Statistics")
    print("-" * 80)
    stats = gateway.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    print()
    
    # Summary
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total_tests = len(results)
    passed = sum(1 for r in results if r['match'])
    failed = total_tests - passed
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/total_tests*100):.1f}%")
    print()
    
    # Detailed results
    print("DETAILED RESULTS:")
    print("-" * 80)
    for i, result in enumerate(results, 1):
        status_icon = "✅" if result['match'] else "❌"
        print(f"{i}. {result['card_name']}")
        print(f"   Status: {result['status']} | Expected: {result['expected']} {status_icon}")
        print(f"   Message: {result['message'][:100]}")
        print(f"   Time: {result['elapsed_seconds']}s")
        print()
    
    # Save results
    report_file = f"shopify_simple_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'gateway_stats': stats,
            'test_results': results,
            'summary': {
                'total': total_tests,
                'passed': passed,
                'failed': failed,
                'success_rate': f"{(passed/total_tests*100):.1f}%"
            }
        }, f, indent=2)
    
    print(f"📄 Full report saved to: {report_file}")
    print()
    
    # Final verdict
    print("="*80)
    if passed == total_tests:
        print("🎉 ALL TESTS PASSED!")
    elif passed > 0:
        print("⚠️  SOME TESTS PASSED")
    else:
        print("❌ ALL TESTS FAILED")
    print("="*80)
    
    return passed == total_tests


if __name__ == "__main__":
    try:
        success = test_gateway_comprehensive()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
