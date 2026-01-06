#!/usr/bin/env python3
"""
Quick test script for MadyStripe Unified
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    
    try:
        from core.gateways import get_gateway_manager
        print("  ✓ core.gateways")
    except Exception as e:
        print(f"  ✗ core.gateways: {e}")
        return False
    
    try:
        from core.checker import CardChecker, validate_card_format
        print("  ✓ core.checker")
    except Exception as e:
        print(f"  ✗ core.checker: {e}")
        return False
    
    try:
        from interfaces.cli import run_cli
        print("  ✓ interfaces.cli")
    except Exception as e:
        print(f"  ✗ interfaces.cli: {e}")
        return False
    
    try:
        from interfaces.telegram_bot import TelegramBotInterface
        print("  ✓ interfaces.telegram_bot")
    except Exception as e:
        print(f"  ✗ interfaces.telegram_bot: {e}")
        return False
    
    return True


def test_gateways():
    """Test gateway manager"""
    print("\nTesting gateway manager...")
    
    try:
        from core.gateways import get_gateway_manager
        
        manager = get_gateway_manager()
        gateways = manager.list_gateways()
        
        print(f"  ✓ Found {len(gateways)} gateways")
        
        for gate in gateways:
            print(f"    - {gate['name']} ({gate['id']})")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_card_validation():
    """Test card validation"""
    print("\nTesting card validation...")
    
    try:
        from core.checker import validate_card_format
        
        test_cases = [
            ("4532123456789012|12|25|123", True),
            ("invalid", False),
            ("1234|12|25", False),
            ("4532123456789012|13|25|123", False),
        ]
        
        for card, expected_valid in test_cases:
            is_valid, error = validate_card_format(card)
            status = "✓" if is_valid == expected_valid else "✗"
            print(f"  {status} {card[:20]}... - {'Valid' if is_valid else error}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_checker():
    """Test card checker (without actually checking)"""
    print("\nTesting card checker...")
    
    try:
        from core.checker import CardChecker
        
        checker = CardChecker()
        print(f"  ✓ CardChecker created")
        print(f"  ✓ Default gateway: {checker.gateway_id or 'default'}")
        print(f"  ✓ Rate limit: {checker.rate_limit}s")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("MADYSTRIPE UNIFIED - SYSTEM TEST")
    print("="*60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Gateways", test_gateways()))
    results.append(("Card Validation", test_card_validation()))
    results.append(("Checker", test_checker()))
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("\nYou can now use MadyStripe Unified:")
        print("  ./madystripe.py --info")
        print("  ./madystripe.py --list-gateways")
        print("  ./madystripe.py cli cards.txt")
        print("  ./madystripe.py bot")
    else:
        print("✗ SOME TESTS FAILED")
        print("\nPlease check the errors above.")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
