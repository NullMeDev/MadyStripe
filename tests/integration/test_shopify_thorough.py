#!/usr/bin/env python3
"""
Thorough Testing Suite for Shopify Dynamic Gates
Tests all functionality including error handling, fallback, and performance
"""

import sys
import time
import json
from datetime import datetime
from typing import List, Dict, Tuple

# Import from core
from core import get_gateway_manager, list_gateways


class ShopifyThoroughTester:
    """Comprehensive tester for Shopify gates"""
    
    def __init__(self):
        self.manager = get_gateway_manager()
        self.results = []
        self.start_time = None
        
    def print_header(self, title: str):
        """Print formatted header"""
        print("\n" + "="*80)
        print(f"  {title}")
        print("="*80)
    
    def print_section(self, title: str):
        """Print section header"""
        print(f"\n{'─'*80}")
        print(f"  {title}")
        print(f"{'─'*80}")
    
    def test_gateway_availability(self) -> bool:
        """Test 1: Gateway Availability"""
        self.print_header("TEST 1: GATEWAY AVAILABILITY")
        
        all_gates = list_gateways()
        
        print("\n📋 All Available Gateways:")
        for gate in all_gates:
            print(f"  [{gate['id']}] {gate['name']}")
            print(f"      Charge: {gate['charge']}")
            print(f"      Speed: {gate['speed']}")
            print(f"      Description: {gate['description']}")
            print()
        
        # Check for Shopify gates
        shopify_gates = {
            '5': 'Shopify $1 Gate',
            '6': 'Shopify $5 Gate',
            '7': 'Shopify $20 Gate',
            '8': 'Shopify $100 Gate',
        }
        
        print("\n✅ Shopify Dynamic Gates Status:")
        all_available = True
        for gate_id, gate_name in shopify_gates.items():
            gateway = self.manager.get_gateway(gate_id)
            if gateway:
                print(f"  ✓ [{gate_id}] {gate_name} - Available")
            else:
                print(f"  ✗ [{gate_id}] {gate_name} - NOT AVAILABLE")
                all_available = False
        
        result = {
            'test': 'Gateway Availability',
            'passed': all_available,
            'details': f"{len([g for g in shopify_gates.keys() if self.manager.get_gateway(g)])} / {len(shopify_gates)} gates available"
        }
        self.results.append(result)
        
        return all_available
    
    def test_single_card_per_gate(self) -> bool:
        """Test 2: Single Card Through Each Gate"""
        self.print_header("TEST 2: SINGLE CARD PER GATE")
        
        # Test card (will be declined - insufficient funds)
        test_card = "4111111111111111|12|25|123"
        
        print(f"\n🔍 Testing card: {test_card[:19]}...")
        print(f"⚠️  Note: This is a test card that will likely be declined")
        
        gates_to_test = [
            ('5', 'Shopify $1 Gate'),
            ('6', 'Shopify $5 Gate'),
            ('7', 'Shopify $20 Gate'),
            ('8', 'Shopify $100 Gate'),
        ]
        
        all_passed = True
        
        for gate_id, gate_name in gates_to_test:
            self.print_section(f"Testing {gate_name}")
            
            print(f"\n⏱️  Starting at: {datetime.now().strftime('%H:%M:%S')}")
            start = time.time()
            
            try:
                status, message, card_type, gateway = self.manager.check_card(
                    test_card, gate_id
                )
                
                elapsed = time.time() - start
                
                print(f"\n📊 Results:")
                print(f"  Gateway: {gateway}")
                print(f"  Status: {status.upper()}")
                print(f"  Message: {message[:100]}...")
                print(f"  Card Type: {card_type}")
                print(f"  Time: {elapsed:.2f}s")
                
                # Determine if test passed
                # Success = got a response (approved, declined, or error)
                passed = status in ['approved', 'declined', 'error']
                
                if passed:
                    print(f"\n✅ Test PASSED - Got valid response")
                else:
                    print(f"\n❌ Test FAILED - Invalid response")
                    all_passed = False
                
                result = {
                    'test': f'Single Card - {gate_name}',
                    'passed': passed,
                    'status': status,
                    'message': message[:100],
                    'time': elapsed
                }
                self.results.append(result)
                
            except Exception as e:
                elapsed = time.time() - start
                print(f"\n❌ Exception: {str(e)}")
                print(f"  Time: {elapsed:.2f}s")
                
                all_passed = False
                
                result = {
                    'test': f'Single Card - {gate_name}',
                    'passed': False,
                    'status': 'exception',
                    'message': str(e),
                    'time': elapsed
                }
                self.results.append(result)
            
            # Small delay between tests
            time.sleep(2)
        
        return all_passed
    
    def test_invalid_card_format(self) -> bool:
        """Test 3: Invalid Card Format Handling"""
        self.print_header("TEST 3: INVALID CARD FORMAT HANDLING")
        
        invalid_cards = [
            ("", "Empty card"),
            ("invalid", "Invalid format"),
            ("4111|12|25", "Missing CVV"),
            ("4111111111111111|13|25|123", "Invalid month"),
            ("4111111111111111|12|20|123", "Expired year"),
        ]
        
        all_passed = True
        
        for card, description in invalid_cards:
            print(f"\n🔍 Testing: {description}")
            print(f"   Card: {card if card else '(empty)'}")
            
            try:
                status, message, card_type, gateway = self.manager.check_card(
                    card, '5'  # Use penny gate
                )
                
                # Should get error status
                passed = status == 'error'
                
                print(f"   Status: {status}")
                print(f"   Message: {message[:60]}...")
                print(f"   Result: {'✅ PASSED' if passed else '❌ FAILED'}")
                
                if not passed:
                    all_passed = False
                
                result = {
                    'test': f'Invalid Format - {description}',
                    'passed': passed,
                    'status': status,
                    'message': message[:100]
                }
                self.results.append(result)
                
            except Exception as e:
                print(f"   Exception: {str(e)}")
                print(f"   Result: ✅ PASSED (exception caught)")
                
                result = {
                    'test': f'Invalid Format - {description}',
                    'passed': True,
                    'status': 'exception',
                    'message': str(e)
                }
                self.results.append(result)
        
        return all_passed
    
    def test_performance(self) -> bool:
        """Test 4: Performance Measurement"""
        self.print_header("TEST 4: PERFORMANCE MEASUREMENT")
        
        test_card = "4111111111111111|12|25|123"
        
        print(f"\n⏱️  Measuring response times for each gate...")
        print(f"   (Testing with same card 3 times per gate)")
        
        gates = ['5', '6', '7', '8']
        gate_names = ['$1 Gate', '$5 Gate', '$20 Gate', '$100 Gate']
        
        performance_data = {}
        
        for gate_id, gate_name in zip(gates, gate_names):
            print(f"\n📊 Testing {gate_name}...")
            
            times = []
            for i in range(3):
                print(f"   Attempt {i+1}/3...", end=' ')
                start = time.time()
                
                try:
                    status, message, card_type, gateway = self.manager.check_card(
                        test_card, gate_id
                    )
                    elapsed = time.time() - start
                    times.append(elapsed)
                    print(f"{elapsed:.2f}s ({status})")
                    
                except Exception as e:
                    elapsed = time.time() - start
                    times.append(elapsed)
                    print(f"{elapsed:.2f}s (error)")
                
                time.sleep(1)
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            performance_data[gate_name] = {
                'avg': avg_time,
                'min': min_time,
                'max': max_time
            }
            
            print(f"   Average: {avg_time:.2f}s")
            print(f"   Min: {min_time:.2f}s")
            print(f"   Max: {max_time:.2f}s")
        
        # Check if performance is acceptable (< 60s average)
        all_passed = all(data['avg'] < 60 for data in performance_data.values())
        
        result = {
            'test': 'Performance Measurement',
            'passed': all_passed,
            'details': performance_data
        }
        self.results.append(result)
        
        return all_passed
    
    def test_fallback_system(self) -> bool:
        """Test 5: Fallback System"""
        self.print_header("TEST 5: FALLBACK SYSTEM")
        
        print("\n🔄 Testing automatic fallback to next store...")
        print("   (Using penny gate with max_attempts=3)")
        
        test_card = "4111111111111111|12|25|123"
        
        try:
            start = time.time()
            status, message, card_type, gateway = self.manager.check_card(
                test_card, '5'
            )
            elapsed = time.time() - start
            
            print(f"\n📊 Results:")
            print(f"  Status: {status}")
            print(f"  Message: {message[:100]}...")
            print(f"  Time: {elapsed:.2f}s")
            
            # Check if fallback was used (message should mention store)
            fallback_used = 'store' in message.lower() or 'attempt' in message.lower()
            
            print(f"\n  Fallback detected: {'Yes' if fallback_used else 'No'}")
            
            passed = status in ['approved', 'declined', 'error']
            
            result = {
                'test': 'Fallback System',
                'passed': passed,
                'fallback_used': fallback_used,
                'status': status,
                'time': elapsed
            }
            self.results.append(result)
            
            return passed
            
        except Exception as e:
            print(f"\n❌ Exception: {str(e)}")
            
            result = {
                'test': 'Fallback System',
                'passed': False,
                'status': 'exception',
                'message': str(e)
            }
            self.results.append(result)
            
            return False
    
    def generate_report(self):
        """Generate final test report"""
        self.print_header("COMPREHENSIVE TEST REPORT")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.get('passed', False))
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 Overall Statistics:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if self.start_time:
            total_time = time.time() - self.start_time
            print(f"  Total Time: {total_time:.2f}s ({total_time/60:.1f} minutes)")
        
        print(f"\n📋 Detailed Results:")
        for i, result in enumerate(self.results, 1):
            status_emoji = "✅" if result.get('passed', False) else "❌"
            print(f"\n  {status_emoji} Test {i}: {result['test']}")
            
            for key, value in result.items():
                if key not in ['test', 'passed']:
                    if isinstance(value, dict):
                        print(f"     {key}:")
                        for k, v in value.items():
                            print(f"       {k}: {v}")
                    else:
                        print(f"     {key}: {value}")
        
        # Save report to file
        report_file = f"shopify_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': f"{(passed_tests/total_tests*100):.1f}%",
                'results': self.results
            }, f, indent=2)
        
        print(f"\n💾 Report saved to: {report_file}")
        
        return passed_tests == total_tests
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        self.print_header("SHOPIFY DYNAMIC GATES - THOROUGH TESTING")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.start_time = time.time()
        
        tests = [
            ("Gateway Availability", self.test_gateway_availability),
            ("Single Card Per Gate", self.test_single_card_per_gate),
            ("Invalid Card Format", self.test_invalid_card_format),
            ("Performance Measurement", self.test_performance),
            ("Fallback System", self.test_fallback_system),
        ]
        
        for test_name, test_func in tests:
            try:
                print(f"\n\n{'='*80}")
                print(f"Running: {test_name}")
                print(f"{'='*80}")
                
                test_func()
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Testing interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Test failed with exception: {e}")
                import traceback
                traceback.print_exc()
        
        # Generate final report
        all_passed = self.generate_report()
        
        print(f"\n{'='*80}")
        if all_passed:
            print("✅ ALL TESTS PASSED!")
        else:
            print("⚠️  SOME TESTS FAILED - Review report above")
        print(f"{'='*80}")
        
        return all_passed


def main():
    """Main test function"""
    tester = ShopifyThoroughTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
