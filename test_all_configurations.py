#!/usr/bin/env python3
"""
Comprehensive Testing Suite for MADY Bot
Tests all gateways, configurations, and features
"""

import sys
import time
import json
import traceback
from datetime import datetime

sys.path.insert(0, '100$/100$/')

# Test configuration
TEST_CARDS = [
    "5566258985615466|12|25|299",  # Card 1
    "4304450802433666|12|25|956",  # Card 2
    "5587170478868301|12|25|286",  # Card 3
    "4242424242424242|12|25|123",  # Test card
]

print("="*70)
print("MADY BOT - COMPREHENSIVE TESTING SUITE")
print("="*70)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("-"*70)

# Test results storage
test_results = {
    "gateways": {},
    "bot_features": {},
    "error_handling": {},
    "performance": {}
}

# ========== GATEWAY TESTING ==========
print("\n[PHASE 1] TESTING ALL GATEWAYS")
print("-"*70)

# Test Gateway 1 - Blemart
print("\n[1.1] Testing Gateway 1 (Blemart - $4.99)...")
try:
    from Charge1 import BlemartCheckout
    test_results["gateways"]["blemart"] = []
    
    for i, card in enumerate(TEST_CARDS[:2], 1):
        print(f"  Card {i}: {card[:4]}****", end=" ")
        start = time.time()
        try:
            result = BlemartCheckout(card)
            elapsed = time.time() - start
            
            if "Error" in result or "Failed" in result:
                status = "❌ ERROR"
            elif "Charged" in result or "Approved" in result:
                status = "✅ APPROVED"
            elif "declined" in result.lower():
                status = "⚠️ DECLINED"
            else:
                status = "❓ UNKNOWN"
            
            print(f"{status} ({elapsed:.1f}s)")
            test_results["gateways"]["blemart"].append({
                "card": card[:4] + "****",
                "status": status,
                "time": elapsed,
                "response": result[:50]
            })
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)[:30]}")
            test_results["gateways"]["blemart"].append({
                "card": card[:4] + "****",
                "status": "❌ EXCEPTION",
                "error": str(e)[:50]
            })
        time.sleep(1)
        
except ImportError as e:
    print(f"  ❌ Gateway 1 Import Failed: {e}")
    test_results["gateways"]["blemart"] = "Import Failed"

# Test Gateway 2 - District People
print("\n[1.2] Testing Gateway 2 (District People - €69)...")
try:
    from Charge2 import DistrictPeopleCheckout
    test_results["gateways"]["district"] = []
    
    for i, card in enumerate(TEST_CARDS[:2], 1):
        print(f"  Card {i}: {card[:4]}****", end=" ")
        start = time.time()
        try:
            result = DistrictPeopleCheckout(card)
            elapsed = time.time() - start
            
            if "Error" in result or "Failed" in result:
                status = "❌ ERROR"
            elif "Charged" in result or "Approved" in result:
                status = "✅ APPROVED"
            elif "declined" in result.lower():
                status = "⚠️ DECLINED"
            else:
                status = "❓ UNKNOWN"
            
            print(f"{status} ({elapsed:.1f}s)")
            test_results["gateways"]["district"].append({
                "card": card[:4] + "****",
                "status": status,
                "time": elapsed,
                "response": result[:50]
            })
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)[:30]}")
            test_results["gateways"]["district"].append({
                "card": card[:4] + "****",
                "status": "❌ EXCEPTION",
                "error": str(e)[:50]
            })
        time.sleep(1)
        
except ImportError as e:
    print(f"  ❌ Gateway 2 Import Failed: {e}")
    test_results["gateways"]["district"] = "Import Failed"

# Test Gateway 3 - Saint Vinson
print("\n[1.3] Testing Gateway 3 (Saint Vinson - $20)...")
try:
    from Charge3 import SaintVinsonDonateCheckout
    test_results["gateways"]["saintvinson"] = []
    
    for i, card in enumerate(TEST_CARDS[:2], 1):
        print(f"  Card {i}: {card[:4]}****", end=" ")
        start = time.time()
        try:
            result = SaintVinsonDonateCheckout(card)
            elapsed = time.time() - start
            
            if "Error" in result or "Failed" in result:
                status = "❌ ERROR"
            elif "Charged" in result or "Approved" in result:
                status = "✅ APPROVED"
            elif "declined" in result.lower():
                status = "⚠️ DECLINED"
            else:
                status = "❓ UNKNOWN"
            
            print(f"{status} ({elapsed:.1f}s)")
            test_results["gateways"]["saintvinson"].append({
                "card": card[:4] + "****",
                "status": status,
                "time": elapsed,
                "response": result[:50]
            })
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)[:30]}")
            test_results["gateways"]["saintvinson"].append({
                "card": card[:4] + "****",
                "status": "❌ EXCEPTION",
                "error": str(e)[:50]
            })
        time.sleep(1)
        
except ImportError as e:
    print(f"  ❌ Gateway 3 Import Failed: {e}")
    test_results["gateways"]["saintvinson"] = "Import Failed"

# Test Gateway 4 - BGD Fresh
print("\n[1.4] Testing Gateway 4 (BGD Fresh - $6.50)...")
try:
    from Charge4 import BGDCheckoutLogic
    test_results["gateways"]["bgd"] = []
    
    for i, card in enumerate(TEST_CARDS[:2], 1):
        print(f"  Card {i}: {card[:4]}****", end=" ")
        start = time.time()
        try:
            result = BGDCheckoutLogic(card)
            elapsed = time.time() - start
            
            if "Error" in result or "Failed" in result:
                status = "❌ ERROR"
            elif "Charged" in result or "Approved" in result:
                status = "✅ APPROVED"
            elif "declined" in result.lower():
                status = "⚠️ DECLINED"
            else:
                status = "❓ UNKNOWN"
            
            print(f"{status} ({elapsed:.1f}s)")
            test_results["gateways"]["bgd"].append({
                "card": card[:4] + "****",
                "status": status,
                "time": elapsed,
                "response": result[:50]
            })
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)[:30]}")
            test_results["gateways"]["bgd"].append({
                "card": card[:4] + "****",
                "status": "❌ EXCEPTION",
                "error": str(e)[:50]
            })
        time.sleep(1)
        
except ImportError as e:
    print(f"  ❌ Gateway 4 Import Failed: {e}")
    test_results["gateways"]["bgd"] = "Import Failed"

# Test Gateway 5 - CC Foundation
print("\n[1.5] Testing Gateway 5 (CC Foundation - $1.00)...")
try:
    from Charge5 import StaleksFloridaCheckoutVNew
    test_results["gateways"]["ccfoundation"] = []
    
    for i, card in enumerate(TEST_CARDS[:2], 1):
        print(f"  Card {i}: {card[:4]}****", end=" ")
        start = time.time()
        try:
            result = StaleksFloridaCheckoutVNew(card)
            elapsed = time.time() - start
            
            if isinstance(result, dict):
                if "error" in result:
                    status = "❌ ERROR"
                else:
                    status = "❓ DICT_RESPONSE"
                result_str = str(result)[:50]
            else:
                result_str = str(result)
                if "Error" in result_str or "Failed" in result_str:
                    status = "❌ ERROR"
                elif "Charged" in result_str or "Approved" in result_str:
                    status = "✅ APPROVED"
                elif "declined" in result_str.lower():
                    status = "⚠️ DECLINED"
                else:
                    status = "❓ UNKNOWN"
            
            print(f"{status} ({elapsed:.1f}s)")
            test_results["gateways"]["ccfoundation"].append({
                "card": card[:4] + "****",
                "status": status,
                "time": elapsed,
                "response": result_str[:50]
            })
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)[:30]}")
            test_results["gateways"]["ccfoundation"].append({
                "card": card[:4] + "****",
                "status": "❌ EXCEPTION",
                "error": str(e)[:50]
            })
        time.sleep(1)
        
except ImportError as e:
    print(f"  ❌ Gateway 5 Import Failed: {e}")
    test_results["gateways"]["ccfoundation"] = "Import Failed"

# ========== BOT FEATURE TESTING ==========
print("\n[PHASE 2] TESTING BOT FEATURES")
print("-"*70)

# Test bot imports
print("\n[2.1] Testing Bot Module Imports...")
try:
    import telebot
    print("  ✅ telebot imported successfully")
    test_results["bot_features"]["telebot"] = "Success"
except ImportError:
    print("  ❌ telebot not installed")
    test_results["bot_features"]["telebot"] = "Failed"

# Test bot initialization
print("\n[2.2] Testing Bot Initialization...")
try:
    BOT_TOKEN = "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
    test_bot = telebot.TeleBot(BOT_TOKEN, skip_pending=True)
    bot_info = test_bot.get_me()
    print(f"  ✅ Bot connected: @{bot_info.username}")
    test_results["bot_features"]["initialization"] = f"Success - @{bot_info.username}"
except Exception as e:
    print(f"  ❌ Bot initialization failed: {str(e)[:50]}")
    test_results["bot_features"]["initialization"] = f"Failed - {str(e)[:50]}"

# Test file reading
print("\n[2.3] Testing File Operations...")
try:
    with open("/home/null/Desktop/TestCards.txt", "r") as f:
        lines = f.readlines()
        valid_cards = [l.strip() for l in lines if '|' in l and len(l.strip().split('|')) == 4]
        print(f"  ✅ Read {len(valid_cards)} valid cards from TestCards.txt")
        test_results["bot_features"]["file_reading"] = f"Success - {len(valid_cards)} cards"
except Exception as e:
    print(f"  ❌ File reading failed: {str(e)[:50]}")
    test_results["bot_features"]["file_reading"] = f"Failed - {str(e)[:50]}"

# ========== ERROR HANDLING TESTING ==========
print("\n[PHASE 3] TESTING ERROR HANDLING")
print("-"*70)

# Test invalid card formats
print("\n[3.1] Testing Invalid Card Formats...")
invalid_cards = [
    "invalid",
    "1234|56|78",
    "||||",
    "4242424242424242|13|25|123",  # Invalid month
    "4242424242424242|12|99|123",  # Invalid year
]

for i, card in enumerate(invalid_cards, 1):
    print(f"  Test {i}: '{card[:20]}...'", end=" ")
    try:
        # Try with Gateway 5 as it's most robust
        from Charge5 import StaleksFloridaCheckoutVNew
        result = StaleksFloridaCheckoutVNew(card)
        if "Error" in str(result) or "Invalid" in str(result):
            print("✅ Properly handled")
            test_results["error_handling"][f"invalid_{i}"] = "Handled"
        else:
            print("⚠️ Not properly handled")
            test_results["error_handling"][f"invalid_{i}"] = "Not handled"
    except Exception as e:
        print(f"❌ Exception: {str(e)[:20]}")
        test_results["error_handling"][f"invalid_{i}"] = "Exception"

# ========== PERFORMANCE TESTING ==========
print("\n[PHASE 4] TESTING PERFORMANCE")
print("-"*70)

print("\n[4.1] Gateway Response Times...")
for gateway, results in test_results["gateways"].items():
    if isinstance(results, list) and results:
        times = [r.get("time", 0) for r in results if "time" in r]
        if times:
            avg_time = sum(times) / len(times)
            print(f"  {gateway}: {avg_time:.2f}s average")
            test_results["performance"][gateway] = f"{avg_time:.2f}s"

# ========== SUMMARY ==========
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)

# Gateway Summary
print("\n[GATEWAYS]")
working_gateways = 0
for gateway, results in test_results["gateways"].items():
    if isinstance(results, list) and results:
        errors = sum(1 for r in results if "ERROR" in r.get("status", ""))
        total = len(results)
        if errors < total:
            working_gateways += 1
            print(f"  ✅ {gateway}: {total - errors}/{total} successful")
        else:
            print(f"  ❌ {gateway}: All failed")
    else:
        print(f"  ❌ {gateway}: {results}")

# Bot Features Summary
print("\n[BOT FEATURES]")
for feature, result in test_results["bot_features"].items():
    if "Success" in str(result):
        print(f"  ✅ {feature}: {result}")
    else:
        print(f"  ❌ {feature}: {result}")

# Error Handling Summary
print("\n[ERROR HANDLING]")
handled = sum(1 for r in test_results["error_handling"].values() if r == "Handled")
total_errors = len(test_results["error_handling"])
print(f"  Properly handled: {handled}/{total_errors}")

# Performance Summary
print("\n[PERFORMANCE]")
for gateway, time in test_results["performance"].items():
    print(f"  {gateway}: {time}")

# Final Status
print("\n" + "="*70)
print("FINAL STATUS")
print("="*70)
print(f"✅ Working Gateways: {working_gateways}/5")
print(f"✅ Bot Features: {sum(1 for r in test_results['bot_features'].values() if 'Success' in str(r))}/{len(test_results['bot_features'])}")
print(f"✅ Error Handling: {handled}/{total_errors}")

# Save results
print("\n[Saving test results to test_results.json...]")
try:
    with open("test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    print("✅ Results saved to test_results.json")
except Exception as e:
    print(f"❌ Failed to save results: {e}")

print("\n" + "="*70)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
