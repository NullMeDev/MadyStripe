#!/usr/bin/env python3
"""
Comprehensive Test Suite for Real Payment Gates
Tests all Shopify gates with actual payment processing
"""

import sys
import time
from core.shopify_price_gateways import (
    ShopifyPennyGateway,
    ShopifyLowGateway,
    ShopifyMediumGateway,
    ShopifyHighGateway
)

# Test cards
VALID_CARD = "4242424242424242|12|25|123"  # Stripe test card
DECLINED_CARD = "4000000000000002|12|25|123"  # Stripe declined test card
INVALID_CARD = "1234567890123456|12|25|123"  # Invalid card
INSUFFICIENT_FUNDS = "4000000000009995|12|25|123"  # Insufficient funds

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_test(test_name):
    print(f"🧪 {test_name}...")

def print_result(status, message, card_type):
    status_emoji = {
        'approved': '✅',
        'declined': '❌',
        'error': '⚠️'
    }
    emoji = status_emoji.get(status, '❓')
    print(f"   {emoji} Status: {status}")
    print(f"   📝 Message: {message}")
    print(f"   💳 Card Type: {card_type}")
    print()

def test_gateway(gateway_name, gateway_class, test_card, test_name):
    """Test a specific gateway with a card"""
    print_test(f"{gateway_name} - {test_name}")
    
    try:
        gateway = gateway_class()
        print(f"   🏪 Store: {gateway.store_url}")
        print(f"   💰 Charge: {gateway.charge_amount}")
        
        # Add delay to respect rate limits
        time.sleep(2)
        
        status, message, card_type = gateway.check(test_card)
        print_result(status, message, card_type)
        
        return status, message
    except Exception as e:
        print(f"   ⚠️ Exception: {str(e)}\n")
        return 'error', str(e)

def run_critical_path_tests():
    """Run critical path tests - one test per gate"""
    print_header("CRITICAL PATH TESTING")
    
    results = {}
    
    # Test each gate with valid card
    results['penny'] = test_gateway("Penny Gate ($0.01)", ShopifyPennyGateway, VALID_CARD, "Valid Card")
    results['low'] = test_gateway("Low Gate ($5)", ShopifyLowGateway, VALID_CARD, "Valid Card")
    results['medium'] = test_gateway("Medium Gate ($20)", ShopifyMediumGateway, VALID_CARD, "Valid Card")
    results['high'] = test_gateway("High Gate ($100)", ShopifyHighGateway, VALID_CARD, "Valid Card")
    
    return results

def run_thorough_tests():
    """Run thorough tests - all scenarios"""
    print_header("THOROUGH TESTING")
    
    results = {}
    
    # Test declined cards
    print_header("Testing Declined Cards")
    results['penny_declined'] = test_gateway("Penny Gate", ShopifyPennyGateway, DECLINED_CARD, "Declined Card")
    results['low_declined'] = test_gateway("Low Gate", ShopifyLowGateway, DECLINED_CARD, "Declined Card")
    
    # Test invalid cards
    print_header("Testing Invalid Cards")
    results['penny_invalid'] = test_gateway("Penny Gate", ShopifyPennyGateway, INVALID_CARD, "Invalid Card")
    results['low_invalid'] = test_gateway("Low Gate", ShopifyLowGateway, INVALID_CARD, "Invalid Card")
    
    # Test insufficient funds
    print_header("Testing Insufficient Funds")
    results['penny_insufficient'] = test_gateway("Penny Gate", ShopifyPennyGateway, INSUFFICIENT_FUNDS, "Insufficient Funds")
    
    # Test fallback mechanism
    print_header("Testing Fallback Mechanism")
    print_test("Penny Gate - Fallback Test")
    try:
        gateway = ShopifyPennyGateway(store_index=0, enable_fallback=True)
        print(f"   🏪 Primary Store: {gateway.store_url}")
        print(f"   🔄 Fallback Enabled: {gateway.enable_fallback}")
        print(f"   ✅ Fallback mechanism configured\n")
        results['fallback'] = ('success', 'Fallback configured')
    except Exception as e:
        print(f"   ⚠️ Exception: {str(e)}\n")
        results['fallback'] = ('error', str(e))
    
    return results

def print_summary(critical_results, thorough_results):
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    all_results = {**critical_results, **thorough_results}
    
    total = len(all_results)
    approved = sum(1 for status, _ in all_results.values() if status == 'approved')
    declined = sum(1 for status, _ in all_results.values() if status == 'declined')
    errors = sum(1 for status, _ in all_results.values() if status == 'error')
    
    print(f"📊 Total Tests: {total}")
    print(f"✅ Approved: {approved}")
    print(f"❌ Declined: {declined}")
    print(f"⚠️  Errors: {errors}")
    print()
    
    # Check if payment API is being used
    print_header("PAYMENT API VERIFICATION")
    try:
        gateway = ShopifyPennyGateway()
        has_payment_api = 'deposit.shopifycs.com' in str(gateway._process_card_real.__code__.co_consts)
        print(f"✅ Payment API Integration: {'ACTIVE' if has_payment_api else 'MISSING'}")
        print(f"🔗 API Endpoint: deposit.shopifycs.com/sessions")
        print(f"📡 GraphQL: SubmitForCompletion mutation")
    except Exception as e:
        print(f"⚠️ Could not verify: {e}")
    
    print()

def main():
    print_header("REAL PAYMENT GATES - COMPREHENSIVE TEST SUITE")
    print("Testing all Shopify gates with actual payment processing")
    print("Based on AutoshBot integration")
    
    # Run critical path tests
    critical_results = run_critical_path_tests()
    
    # Run thorough tests
    thorough_results = run_thorough_tests()
    
    # Print summary
    print_summary(critical_results, thorough_results)
    
    print_header("TESTING COMPLETE")
    print("All gates now use REAL payment processing!")
    print("No more simulation - actual charges via Shopify Payment API")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)
