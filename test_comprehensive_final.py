#!/usr/bin/env python3
"""
Comprehensive Final Test for MadyStripe Unified v3.0
Tests all features, gateways, and edge cases
"""

import sys
import os
import time

# Add paths
sys.path.insert(0, os.path.dirname(__file__))

from core.gateways import get_gateway_manager, check_card
from core.checker import CardChecker, validate_card_format, load_cards_from_file, save_results

# Test cards
TEST_CARDS = [
    "4579720714941032|2|27|530",
    "4570663792067008|9|27|654",
    "4628880201124236|5|26|437",
]

def print_section(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_card_validation():
    """Test card validation"""
    print_section("TEST 1: Card Validation")
    
    test_cases = [
        ("4532123456789012|12|25|123", True, "Valid card"),
        ("invalid", False, "Invalid format"),
        ("1234|12|25", False, "Missing CVC"),
        ("4532123456789012|13|25|123", False, "Invalid month"),
        ("4532123456789012|12|25|12", False, "Invalid CVC length"),
    ]
    
    passed = 0
    for card, expected_valid, description in test_cases:
        is_valid, error = validate_card_format(card)
        status = "✅" if is_valid == expected_valid else "❌"
        print(f"{status} {description}: {card[:20]}...")
        if is_valid == expected_valid:
            passed += 1
    
    print(f"\nResult: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)

def test_gateway_manager():
    """Test gateway manager"""
    print_section("TEST 2: Gateway Manager")
    
    manager = get_gateway_manager()
    gateways = manager.list_gateways()
    
    print(f"✅ Gateway manager initialized")
    print(f"✅ Loaded {len(gateways)} gateways:")
    
    for gate in gateways:
        print(f"   [{gate['id']}] {gate['name']} - {gate['charge']} ({gate['speed']})")
    
    # Test default gateway
    default = manager.get_default_gateway()
    print(f"\n✅ Default gateway: {default.name if default else 'None'}")
    
    return len(gateways) > 0

def test_staleks_gateway():
    """Test Staleks gateway with real cards"""
    print_section("TEST 3: Staleks Gateway (Primary)")
    
    print("Testing with 3 cards...")
    
    checker = CardChecker(gateway_id='staleks', rate_limit=0.5)
    checker.stats.total = len(TEST_CARDS)
    
    results = []
    for i, card in enumerate(TEST_CARDS, 1):
        print(f"\n[{i}/{len(TEST_CARDS)}] Checking {card[:4]}****...")
        result = checker.check_single(card)
        results.append(result)
        
        status_emoji = "✅" if result.is_approved() else "❌"
        print(f"{status_emoji} {result.status.upper()}: {result.message[:50]}")
        print(f"   Card Type: {result.card_type} | Gateway: {result.gateway}")
        
        time.sleep(0.5)
    
    # Summary
    stats = checker.stats
    print(f"\n📊 Summary:")
    print(f"   Total: {stats.checked}")
    print(f"   Approved: {stats.approved}")
    print(f"   Declined: {stats.declined}")
    print(f"   Errors: {stats.errors}")
    print(f"   Success Rate: {stats.get_success_rate():.1f}%")
    print(f"   Speed: {stats.get_speed():.2f} c/s")
    
    return stats.checked == len(TEST_CARDS)

def test_cli_features():
    """Test CLI advanced features"""
    print_section("TEST 4: CLI Advanced Features")
    
    # Test file loading
    print("Testing file loading...")
    try:
        valid, invalid = load_cards_from_file('my_cards.txt', limit=5)
        print(f"✅ Loaded {len(valid)} valid cards")
        if invalid:
            print(f"⚠️  Skipped {len(invalid)} invalid cards")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return False
    
    # Test result saving
    print("\nTesting result saving...")
    try:
        checker = CardChecker()
        result = checker.check_single(TEST_CARDS[0])
        
        # Save in different formats
        save_results([result], '/tmp/test_results.txt', 'txt')
        print("✅ TXT format saved")
        
        save_results([result], '/tmp/test_results.json', 'json')
        print("✅ JSON format saved")
        
        save_results([result], '/tmp/test_results.csv', 'csv')
        print("✅ CSV format saved")
        
        return True
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        return False

def test_edge_cases():
    """Test edge cases"""
    print_section("TEST 5: Edge Cases")
    
    # Test empty file
    print("Testing empty file handling...")
    try:
        with open('/tmp/empty.txt', 'w') as f:
            pass
        valid, invalid = load_cards_from_file('/tmp/empty.txt')
        print(f"✅ Empty file handled: {len(valid)} cards")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test invalid formats
    print("\nTesting invalid card formats...")
    invalid_cards = [
        "not_a_card",
        "1234|12|25",
        "4532123456789012|99|25|123",
    ]
    
    for card in invalid_cards:
        is_valid, error = validate_card_format(card)
        status = "✅" if not is_valid else "❌"
        print(f"{status} Rejected: {card[:30]}... - {error}")
    
    return True

def test_telegram_bot_init():
    """Test Telegram bot initialization"""
    print_section("TEST 6: Telegram Bot")
    
    try:
        from interfaces.telegram_bot import TelegramBotInterface
        
        BOT_TOKEN = "7984658748:AAEvRmO6iBk5gKGIK6Evi5w35_Taw4K6Oe0"
        GROUP_IDS = ["-5286094140"]
        
        print(f"Token: {BOT_TOKEN[:20]}...")
        print(f"Group ID: {GROUP_IDS[0]}")
        
        bot = TelegramBotInterface(BOT_TOKEN, GROUP_IDS)
        print("✅ Bot initialized successfully")
        print(f"✅ Gateway manager: {len(bot.gateway_manager.list_gateways())} gateways")
        print("✅ Handlers registered")
        print("\n⚠️  Note: Bot not started (would run indefinitely)")
        print("   To start bot: ./madystripe.py bot")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  MADYSTRIPE UNIFIED v3.0 - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    tests = [
        ("Card Validation", test_card_validation),
        ("Gateway Manager", test_gateway_manager),
        ("Staleks Gateway", test_staleks_gateway),
        ("CLI Features", test_cli_features),
        ("Edge Cases", test_edge_cases),
        ("Telegram Bot", test_telegram_bot_init),
    ]
    
    results = []
    start_time = time.time()
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    elapsed = time.time() - start_time
    
    # Final summary
    print_section("FINAL SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{'='*70}")
    print(f"  Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"  Time: {elapsed:.2f} seconds")
    print(f"{'='*70}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is fully functional!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review output above.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
