"""
Comprehensive End-to-End Shopify Gateway Test
Tests complete payment flow with real cards and proxy
"""

import sys
import time
from core.shopify_simple_gateway import SimpleShopifyGateway

def test_e2e():
    print("="*80)
    print("COMPREHENSIVE SHOPIFY GATEWAY END-TO-END TEST")
    print("="*80)
    
    # Load proxy
    proxy = None
    try:
        with open('proxies.txt', 'r') as f:
            proxy = f.read().strip().split('\n')[0]
        print(f"\n✅ Loaded proxy: {proxy.split(':')[0]}:{proxy.split(':')[1]}")
    except:
        print("\n⚠️  No proxy found, testing without proxy")
    
    # Initialize gateway
    print("\n[1/5] Initializing gateway...")
    gateway = SimpleShopifyGateway(proxy=proxy)
    
    if not gateway.stores:
        print("❌ No stores loaded!")
        return
    
    print(f"✅ Gateway initialized with {len(gateway.stores)} stores")
    
    # Test cards (mix of valid format and invalid)
    test_cards = [
        # Test card 1 - Will likely be declined (insufficient funds)
        "4111111111111111|12|25|123",
        # Test card 2 - Invalid card
        "4242424242424242|12|25|123",
        # Test card 3 - Another test card
        "5555555555554444|12|25|123",
    ]
    
    print(f"\n[2/5] Testing with {len(test_cards)} cards...")
    print("-" * 80)
    
    results = []
    
    for i, card in enumerate(test_cards, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(test_cards)}: {card[:4]}...{card[-7:]}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            status, message, card_type = gateway.check(card, max_attempts=2)
            elapsed = time.time() - start_time
            
            result = {
                'card': card,
                'status': status,
                'message': message,
                'card_type': card_type,
                'elapsed': elapsed
            }
            results.append(result)
            
            # Print result
            if status == 'approved':
                print(f"\n✅ APPROVED")
            elif status == 'declined':
                print(f"\n❌ DECLINED")
            else:
                print(f"\n⚠️  ERROR")
            
            print(f"   Message: {message}")
            print(f"   Card Type: {card_type}")
            print(f"   Time: {elapsed:.2f}s")
            
        except Exception as e:
            print(f"\n❌ EXCEPTION: {e}")
            results.append({
                'card': card,
                'status': 'error',
                'message': str(e),
                'card_type': 'Unknown',
                'elapsed': time.time() - start_time
            })
        
        # Wait between tests
        if i < len(test_cards):
            print(f"\n⏳ Waiting 5 seconds before next test...")
            time.sleep(5)
    
    # Print summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    
    approved = sum(1 for r in results if r['status'] == 'approved')
    declined = sum(1 for r in results if r['status'] == 'declined')
    errors = sum(1 for r in results if r['status'] == 'error')
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"✅ Approved: {approved}")
    print(f"❌ Declined: {declined}")
    print(f"⚠️  Errors: {errors}")
    
    print(f"\nDetailed Results:")
    print("-" * 80)
    for i, result in enumerate(results, 1):
        status_icon = "✅" if result['status'] == 'approved' else "❌" if result['status'] == 'declined' else "⚠️"
        print(f"{i}. {status_icon} {result['card'][:4]}...{result['card'][-7:]}")
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message']}")
        print(f"   Time: {result['elapsed']:.2f}s")
        print()
    
    # Gateway stats
    stats = gateway.get_stats()
    print(f"{'='*80}")
    print("GATEWAY STATISTICS")
    print(f"{'='*80}")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")
    
    # Return success if at least one card was processed (approved or declined)
    return approved > 0 or declined > 0


if __name__ == "__main__":
    try:
        success = test_e2e()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
