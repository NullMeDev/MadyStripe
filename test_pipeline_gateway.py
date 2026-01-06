#!/usr/bin/env python3
"""
Test script for Pipeline Foundation Gateway
Tests the real API integration with dynamic key extraction
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.pipeline_gateway import PipelineGateway

def test_gateway():
    """Test the Pipeline Foundation gateway"""
    
    print("="*70)
    print("PIPELINE FOUNDATION GATEWAY TEST")
    print("="*70)
    
    gateway = PipelineGateway()
    
    print(f"\n✅ Gateway initialized successfully!")
    print(f"   Name: {gateway.name}")
    print(f"   Charge Amount: {gateway.charge_amount}")
    print(f"   Description: {gateway.description}")
    print(f"   Donation Page: {gateway.donation_page}")
    
    print("\n" + "="*70)
    print("TESTING WITH SAMPLE CARD")
    print("="*70)
    
    # Test with a sample card (this will likely decline, but tests the API)
    test_card = "4532015112830366|12|2025|123"
    
    print(f"\nTesting card: {test_card}")
    print("Making real API call to Pipeline Foundation...")
    print("(This may take 10-15 seconds - fetching fresh keys)\n")
    
    try:
        status, message, card_type = gateway.check(test_card)
        
        print("="*70)
        print("RESULT:")
        print("="*70)
        print(f"Status: {status.upper()}")
        print(f"Message: {message}")
        print(f"Card Type: {card_type}")
        print(f"\nGateway Stats:")
        print(f"  Success: {gateway.success_count}")
        print(f"  Failed: {gateway.fail_count}")
        print(f"  Errors: {gateway.error_count}")
        print(f"  Success Rate: {gateway.get_success_rate():.1f}%")
        print("="*70)
        
        if status == "approved":
            print("\n✅ CARD APPROVED! Gateway is working correctly!")
            print("💰 $1.00 charged via weekly recurring donation")
        elif status == "declined":
            print("\n❌ Card declined (expected for test card)")
            print("✅ Gateway API is working correctly!")
        else:
            print("\n⚠️ Error occurred - check the message above")
            
    except Exception as e:
        print("="*70)
        print("ERROR:")
        print("="*70)
        print(f"Exception: {str(e)}")
        print("\n⚠️ Gateway test failed!")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nAdvantages of Pipeline Gateway:")
    print("  ✅ Dynamic Stripe key extraction (not hardcoded)")
    print("  ✅ Fresh nonce/form_id from page scraping")
    print("  ✅ More complete billing details")
    print("  ✅ Weekly recurring (vs monthly)")
    print("  ✅ Better error handling")
    print("  ✅ Different foundation (better rate limit distribution)")

if __name__ == "__main__":
    test_gateway()
