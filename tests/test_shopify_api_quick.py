#!/usr/bin/env python3
"""
Quick test for Shopify API Gateway using known working store
"""

import sys
import os
import time

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

# Test cards
TEST_CARDS = [
    "4579720714941032|2|27|530",
    "4570663792067008|9|27|654",
    "4628880201124236|5|26|437",
]

# Known working Shopify stores
WORKING_STORES = [
    "allbirds.com",
    "gymshark.com",
    "fashionnova.com",
]


def test_with_working_store():
    """Test the gateway with a known working store"""
    print("=" * 60)
    print("SHOPIFY API GATEWAY - QUICK TEST WITH WORKING STORE")
    print("=" * 60)
    
    from src.core.shopify_api_gateway import ShopifyAPIGateway
    
    # Create gateway with custom store list
    gateway = ShopifyAPIGateway()
    
    # Override stores with known working ones
    gateway.stores = [{'url': store, 'variant_id': None, 'price': None} for store in WORKING_STORES]
    print(f"Using {len(gateway.stores)} known working stores")
    
    results = []
    
    for i, card in enumerate(TEST_CARDS):
        print(f"\n--- Test {i+1}/{len(TEST_CARDS)} ---")
        print(f"Card: {card[:6]}...{card[-4:]}")
        
        start_time = time.time()
        status, message, card_type = gateway.check(card)
        elapsed = time.time() - start_time
        
        print(f"Status: {status}")
        print(f"Message: {message}")
        print(f"Card Type: {card_type}")
        print(f"Time: {elapsed:.2f}s")
        
        results.append({
            'card': card,
            'status': status,
            'message': message,
            'card_type': card_type,
            'time': elapsed
        })
        
        # Wait between tests
        if i < len(TEST_CARDS) - 1:
            print("Waiting 3s...")
            time.sleep(3)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for i, result in enumerate(results):
        card_short = result['card'][:6] + "..." + result['card'][-4:]
        status_icon = "✓" if result['status'] in ['approved', 'declined'] else "⚠"
        print(f"  {status_icon} Card {i+1}: {result['status']} - {result['message'][:50]}")
    
    # Count successes (approved or declined means the flow worked)
    successful = sum(1 for r in results if r['status'] in ['approved', 'declined'])
    print(f"\n  Flow completed: {successful}/{len(results)}")
    
    return results


if __name__ == "__main__":
    test_with_working_store()
