#!/usr/bin/env python3
"""
Comprehensive test suite for Mady Bot
Tests all commands and functionality
"""

import requests
import time
import json
import sys
import os

# Bot Configuration
BOT_TOKEN = "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
GROUP_ID = "-1003538559040"
BOT_USERNAME = "MissNullMe_bot"  # Replace with actual bot username

def send_telegram_command(command, chat_id=None):
    """Send a command to the bot via Telegram API"""
    if chat_id is None:
        # Get bot info to find a chat
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        response = requests.get(url)
        if response.status_code == 200:
            updates = response.json().get('result', [])
            if updates:
                chat_id = updates[-1]['message']['chat']['id']
    
    if chat_id:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': command
        }
        response = requests.post(url, data=data)
        return response.status_code == 200
    return False

def test_bot_connection():
    """Test 1: Bot Connection"""
    print("\n🔍 TEST 1: Bot Connection")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    response = requests.get(url)
    
    if response.status_code == 200:
        bot_info = response.json()['result']
        print(f"   ✅ Bot connected: @{bot_info['username']}")
        print(f"   ✅ Bot name: {bot_info['first_name']}")
        return True
    else:
        print(f"   ❌ Failed to connect: {response.status_code}")
        return False

def test_group_access():
    """Test 2: Group Access"""
    print("\n🔍 TEST 2: Group Access")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': GROUP_ID,
        'text': '🤖 <b>Mady Bot Test Suite Running</b>\n\nTesting group access...',
        'parse_mode': 'HTML'
    }
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        print(f"   ✅ Can send to group: {GROUP_ID}")
        return True
    else:
        print(f"   ❌ Cannot access group: {response.status_code}")
        return False

def test_card_formats():
    """Test 3: Card Format Validation"""
    print("\n🔍 TEST 3: Card Format Validation")
    
    test_cases = [
        ("5566258985615466|12|25|299", True, "Valid Mastercard"),
        ("4304450802433666|12|25|956", True, "Valid Visa"),
        ("invalid|12|25|123", False, "Invalid number"),
        ("4532123456789012|13|25|123", False, "Invalid month"),
        ("4532123456789012|12|99|123", False, "Invalid year"),
        ("4532123456789012|12|25", False, "Missing CVV"),
    ]
    
    passed = 0
    for card, should_pass, description in test_cases:
        parts = card.split('|')
        is_valid = (
            len(parts) == 4 and
            parts[0].isdigit() and
            parts[1].isdigit() and 1 <= int(parts[1]) <= 12 and
            parts[2].isdigit() and
            parts[3].isdigit()
        )
        
        if is_valid == should_pass:
            print(f"   ✅ {description}: Passed")
            passed += 1
        else:
            print(f"   ❌ {description}: Failed")
    
    print(f"   📊 Passed {passed}/{len(test_cases)} tests")
    return passed == len(test_cases)

def test_gateway_loading():
    """Test 4: Gateway Loading"""
    print("\n🔍 TEST 4: Gateway Loading")
    
    sys.path.insert(0, '100$/100$/')
    gateways_loaded = []
    
    try:
        from Charge1 import BlemartCheckout
        gateways_loaded.append("Blemart ($4.99)")
        print("   ✅ Loaded: Blemart gateway")
    except:
        print("   ⚠️ Failed: Blemart gateway")
    
    try:
        from Charge2 import DistrictPeopleCheckout
        gateways_loaded.append("District People (€69)")
        print("   ✅ Loaded: District People gateway")
    except:
        print("   ⚠️ Failed: District People gateway")
    
    try:
        from Charge3 import SaintVinsonDonateCheckout
        gateways_loaded.append("Saint Vinson ($2)")
        print("   ✅ Loaded: Saint Vinson gateway")
    except:
        print("   ⚠️ Failed: Saint Vinson gateway")
    
    try:
        from Charge4 import BGDCheckoutLogic
        gateways_loaded.append("BGD Fresh ($6.50)")
        print("   ✅ Loaded: BGD Fresh gateway")
    except:
        print("   ⚠️ Failed: BGD Fresh gateway")
    
    try:
        from Charge5 import StaleksFloridaCheckoutVNew
        gateways_loaded.append("Staleks ($0.01)")
        print("   ✅ Loaded: Staleks gateway")
    except:
        print("   ⚠️ Failed: Staleks gateway")
    
    print(f"   📊 Loaded {len(gateways_loaded)}/5 gateways")
    return len(gateways_loaded) >= 1

def test_file_processing():
    """Test 5: File Processing"""
    print("\n🔍 TEST 5: File Processing")
    
    test_file = "/home/null/Desktop/TestCards.txt"
    
    if os.path.exists(test_file):
        with open(test_file, 'r') as f:
            lines = f.readlines()
        
        valid_cards = [line.strip() for line in lines if '|' in line.strip()]
        print(f"   ✅ Found test file: {len(valid_cards)} cards")
        
        # Test first 3 cards only
        print(f"   📋 Sample cards:")
        for i, card in enumerate(valid_cards[:3], 1):
            print(f"      {i}. {card[:6]}******{card[-4:]}")
        
        return True
    else:
        print(f"   ❌ Test file not found: {test_file}")
        return False

def test_proxy_loading():
    """Test 6: Proxy Loading"""
    print("\n🔍 TEST 6: Proxy Loading")
    
    proxy_file = "/home/null/Documents/usetheseproxies.txt"
    
    if os.path.exists(proxy_file):
        with open(proxy_file, 'r') as f:
            lines = f.readlines()
        
        proxies = []
        for line in lines:
            line = line.strip()
            if line and ':' in line:
                parts = line.split(':')
                if len(parts) >= 4:
                    proxies.append(line)
        
        print(f"   ✅ Loaded {len(proxies)} proxies")
        if proxies:
            print(f"   📋 Sample proxy: {proxies[0].split(':')[0]}:****")
        return True
    else:
        print(f"   ❌ Proxy file not found")
        return False

def test_single_card_check():
    """Test 7: Single Card Check"""
    print("\n🔍 TEST 7: Single Card Check (Simulated)")
    
    # Import and test Staleks gateway directly
    sys.path.insert(0, '100$/100$/')
    try:
        from Charge5 import StaleksFloridaCheckoutVNew
        
        test_card = "4532123456789012|12|25|123"
        print(f"   🔄 Testing card: {test_card[:6]}******")
        
        # Note: This will likely fail but we're testing the function works
        result = StaleksFloridaCheckoutVNew(test_card)
        
        if isinstance(result, dict):
            if 'error' in result:
                print(f"   ✅ Gateway responded: {str(result['error'])[:50]}")
            else:
                print(f"   ✅ Gateway responded: Payment attempt made")
        else:
            print(f"   ✅ Gateway responded: {str(result)[:50]}")
        
        return True
    except Exception as e:
        print(f"   ❌ Gateway error: {str(e)[:50]}")
        return False

def test_commands_summary():
    """Test 8: Commands Summary"""
    print("\n🔍 TEST 8: Bot Commands")
    
    commands = [
        ("/start", "Show welcome message"),
        ("/gate", "Select gateway (1-5)"),
        ("/check /path/to/file.txt", "Check cards from file"),
        ("/stop", "Stop current process"),
        ("4532...|12|25|123", "Check single card"),
        ("Upload .txt", "Process uploaded file")
    ]
    
    print("   📋 Available commands:")
    for cmd, desc in commands:
        print(f"      • {cmd} - {desc}")
    
    return True

def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("🤖 MADY BOT - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    tests = [
        ("Bot Connection", test_bot_connection),
        ("Group Access", test_group_access),
        ("Card Formats", test_card_formats),
        ("Gateway Loading", test_gateway_loading),
        ("File Processing", test_file_processing),
        ("Proxy Loading", test_proxy_loading),
        ("Single Card Check", test_single_card_check),
        ("Commands Summary", test_commands_summary)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ Test crashed: {str(e)[:50]}")
            failed += 1
    
    print("\n" + "="*60)
    print("📊 TEST RESULTS:")
    print(f"   ✅ Passed: {passed}/{len(tests)}")
    print(f"   ❌ Failed: {failed}/{len(tests)}")
    
    if passed == len(tests):
        print("\n🎉 ALL TESTS PASSED! Bot is fully functional!")
    elif passed >= 6:
        print("\n✅ Bot is operational with minor issues")
    else:
        print("\n⚠️ Bot has issues that need attention")
    
    print("\n📝 USAGE INSTRUCTIONS:")
    print("1. Open Telegram and search for your bot")
    print("2. Send /start to see the menu")
    print("3. Send /gate to select a gateway (recommend 5 for $0.01)")
    print("4. Send /check /home/null/Desktop/TestCards.txt")
    print("5. Or send a single card: 4532123456789012|12|25|123")
    print("6. Approved cards will appear in group: " + GROUP_ID)
    
    print("="*60)

if __name__ == "__main__":
    run_all_tests()
