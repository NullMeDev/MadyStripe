#!/usr/bin/env python3
"""
Simple Terminal Test for Shopify Dynamic Gates
Usage: python3 test_shopify_gates_terminal.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.shopify_price_gateways_dynamic import (
    DynamicShopifyPennyGateway,
    DynamicShopifyFiveDollarGateway,
    DynamicShopifyTwentyDollarGateway,
    DynamicShopifyHundredDollarGateway
)


def test_single_card(gateway, card_data):
    """Test a single card with a gateway"""
    print(f"\n{'='*70}")
    print(f"Testing: {gateway.name}")
    print(f"Card: {card_data[:4]}...{card_data[-7:]}")
    print(f"{'='*70}")
    
    try:
        status, message, card_type = gateway.check(card_data)
        
        print(f"\n📊 RESULT:")
        print(f"  Status: {status}")
        print(f"  Message: {message}")
        print(f"  Card Type: {card_type}")
        
        if status == 'approved':
            print(f"\n✅ SUCCESS! Card was approved!")
        elif status == 'declined':
            print(f"\n❌ Card was declined")
        else:
            print(f"\n⚠️  Error occurred")
        
        return status
        
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return 'error'


def main():
    print("="*70)
    print("SHOPIFY DYNAMIC GATES - TERMINAL TEST")
    print("="*70)
    
    # Test card (will be declined - for testing only)
    test_card = "4111111111111111|12|25|123"
    
    print(f"\n📝 Test Card: {test_card}")
    print(f"⚠️  This is a test card and will likely be declined")
    print(f"🔄 Testing all 4 Shopify gates with automatic store fallback...")
    
    # Test all gates
    gates = [
        ("Penny Gate ($0.01-$1.00)", DynamicShopifyPennyGateway()),
        ("$5 Gate ($3.00-$7.00)", DynamicShopifyFiveDollarGateway()),
        ("$20 Gate ($15.00-$25.00)", DynamicShopifyTwentyDollarGateway()),
        ("$100 Gate ($80.00-$120.00)", DynamicShopifyHundredDollarGateway()),
    ]
    
    results = {}
    
    for gate_name, gateway in gates:
        print(f"\n\n{'#'*70}")
        print(f"# {gate_name}")
        print(f"{'#'*70}")
        
        status = test_single_card(gateway, test_card)
        results[gate_name] = status
        
        # Show gateway stats
        stats = gateway.get_stats()
        print(f"\n📈 Gateway Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    # Final summary
    print(f"\n\n{'='*70}")
    print(f"FINAL SUMMARY")
    print(f"{'='*70}")
    
    for gate_name, status in results.items():
        emoji = "✅" if status == "approved" else "❌" if status == "declined" else "⚠️"
        print(f"{emoji} {gate_name}: {status}")
    
    print(f"\n{'='*70}")
    print(f"Test complete!")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
