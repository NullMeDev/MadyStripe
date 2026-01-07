#!/usr/bin/env python3
"""
Comprehensive Test for Integrated Shopify Price Gateways
Tests all 4 Shopify gates through the unified gateway manager
"""

import sys
import time
from datetime import datetime

# Import from core
from core import get_gateway_manager, list_gateways

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_section(title):
    """Print a section header"""
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}")

def test_gateway_availability():
    """Test that all Shopify gateways are available"""
    print_header("SHOPIFY GATEWAYS AVAILABILITY TEST")
    
    manager = get_gateway_manager()
    all_gates = list_gateways()
    
    print("\n📋 All Available Gateways:")
    for gate in all_gates:
        print(f"  [{gate['id']}] {gate['name']}")
        print(f"      Charge: {gate['charge']}")
        print(f"      Speed: {gate['speed']}")
        print(f"      Description: {gate['description']}")
        print()
    
    # Check for Shopify price gates
    shopify_gates = {
        '5': 'Shopify $1 Gate',
        '6': 'Shopify $5 Gate',
        '7': 'Shopify $15 Gate',
        '8': 'Shopify $45+ Gate',
    }
    
    print("\n✅ Shopify Price Gates Status:")
    all_available = True
    for gate_id, gate_name in shopify_gates.items():
        gateway = manager.get_gateway(gate_id)
        if gateway:
            print(f"  ✓ [{gate_id}] {gate_name} - Available")
        else:
            print(f"  ✗ [{gate_id}] {gate_name} - NOT AVAILABLE")
            all_available = False
    
    return all_available

def test_single_gateway(gateway_id, gateway_name, test_card):
    """Test a single gateway with a test card"""
    print_section(f"Testing {gateway_name}")
    
    manager = get_gateway_manager()
    
    print(f"\n🔍 Testing with card: {test_card[:19]}...")
    print(f"⏱️  Starting test at: {datetime.now().strftime('%H:%M:%S')}")
    
    start_time = time.time()
    
    try:
        status, message, card_type, gateway = manager.check_card(test_card, gateway_id)
        
        elapsed = time.time() - start_time
        
        print(f"\n📊 Results:")
        print(f"  Gateway: {gateway}")
        print(f"  Status: {status.upper()}")
        print(f"  Message: {message}")
        print(f"  Card Type: {card_type}")
        print(f"  Time: {elapsed:.2f}s")
        
        # Determine result emoji
        if status == 'approved':
            emoji = "✅"
        elif status == 'declined':
            emoji = "❌"
        else:
            emoji = "⚠️"
        
        print(f"\n{emoji} Test Result: {status.upper()}")
        
        return {
            'gateway_id': gateway_id,
            'gateway_name': gateway_name,
            'status': status,
            'message': message,
            'card_type': card_type,
            'time': elapsed,
            'success': status in ['approved', 'declined']  # Not error
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n⚠️ Exception occurred: {str(e)}")
        print(f"  Time: {elapsed:.2f}s")
        
        return {
            'gateway_id': gateway_id,
            'gateway_name': gateway_name,
            'status': 'error',
            'message': str(e),
            'card_type': 'Unknown',
            'time': elapsed,
            'success': False
        }

def test_all_shopify_gates():
    """Test all 4 Shopify price gateways"""
    print_header("TESTING ALL SHOPIFY PRICE GATEWAYS")
    
    # Test card (you should replace with a real test card)
    test_card = "4532123456789012|12|25|123"
    
    print(f"\n⚠️  NOTE: Using test card format")
    print(f"   For real testing, replace with actual card data")
    
    # Define gateways to test
    gateways_to_test = [
        ('5', 'Shopify $1 Gate (Penny)'),
        ('6', 'Shopify $5 Gate (Low)'),
        ('7', 'Shopify $15 Gate (Medium)'),
        ('8', 'Shopify $45+ Gate (High)'),
    ]
    
    results = []
    
    for gateway_id, gateway_name in gateways_to_test:
        result = test_single_gateway(gateway_id, gateway_name, test_card)
        results.append(result)
        
        # Small delay between tests
        time.sleep(1)
    
    return results

def print_summary(results):
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total - successful
    
    print(f"\n📊 Overall Statistics:")
    print(f"  Total Tests: {total}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Success Rate: {(successful/total*100):.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for result in results:
        status_emoji = "✅" if result['success'] else "❌"
        print(f"\n  {status_emoji} {result['gateway_name']}")
        print(f"     Status: {result['status'].upper()}")
        print(f"     Message: {result['message'][:60]}...")
        print(f"     Time: {result['time']:.2f}s")
    
    # Calculate average time
    avg_time = sum(r['time'] for r in results) / len(results)
    print(f"\n⏱️  Average Response Time: {avg_time:.2f}s")
    
    return successful == total

def main():
    """Main test function"""
    print_header("SHOPIFY PRICE GATEWAYS - INTEGRATION TEST")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Check availability
    print_section("Step 1: Checking Gateway Availability")
    all_available = test_gateway_availability()
    
    if not all_available:
        print("\n❌ ERROR: Not all Shopify gateways are available!")
        print("   Please check the integration.")
        return False
    
    print("\n✅ All Shopify gateways are available!")
    
    # Step 2: Test all gateways
    print_section("Step 2: Testing All Gateways")
    results = test_all_shopify_gates()
    
    # Step 3: Print summary
    all_passed = print_summary(results)
    
    # Final result
    print_header("FINAL RESULT")
    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
        print("   Shopify Price Gateways are fully integrated and working!")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("   Please review the results above.")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
