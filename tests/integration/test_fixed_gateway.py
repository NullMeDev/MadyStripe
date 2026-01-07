#!/usr/bin/env python3
"""
Quick test of the fixed Shopify gateway
"""

from core.shopify_gateway_fixed import FixedShopifyGateway

def test_gateway():
    print("="*70)
    print("TESTING FIXED SHOPIFY GATEWAY")
    print("="*70)
    
    # Test store
    store = "ratterriers.myshopify.com"
    
    # Test cards (fake for testing)
    test_cards = [
        "4532015112830366|12|25|123",  # Visa
        "5425233430109903|12|25|456",  # Mastercard
    ]
    
    gateway = FixedShopifyGateway(store)
    
    print(f"\nGateway: {gateway.name}")
    print(f"Store: {gateway.store_url}")
    print(f"\nTesting {len(test_cards)} cards...\n")
    
    for i, card in enumerate(test_cards, 1):
        print(f"\n[{i}/{len(test_cards)}] Testing card...")
        status, message, card_type = gateway.check(card)
        
        if status == "approved":
            print(f"✅ {status.upper()}: {message} ({card_type})")
        elif status == "declined":
            print(f"❌ {status.upper()}: {message} ({card_type})")
        else:
            print(f"⚠️ {status.upper()}: {message} ({card_type})")
    
    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    print(f"Approved: {gateway.success_count}")
    print(f"Declined: {gateway.fail_count}")
    print(f"Errors: {gateway.error_count}")
    print(f"Success Rate: {gateway.get_success_rate():.1f}%")

if __name__ == '__main__':
    test_gateway()
