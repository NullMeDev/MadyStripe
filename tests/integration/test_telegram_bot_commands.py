#!/usr/bin/env python3
"""
Test Telegram Bot Commands and Functionality
"""

import telebot
import time
import os
from datetime import datetime

# Bot configuration
BOT_TOKEN = "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
TEST_GROUP = "-1003538559040"

print("="*70)
print("TELEGRAM BOT COMMAND TESTING")
print("="*70)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("-"*70)

# Initialize bot
try:
    bot = telebot.TeleBot(BOT_TOKEN, skip_pending=True)
    bot_info = bot.get_me()
    print(f"\n✅ Bot Connected: @{bot_info.username}")
    print(f"   Bot ID: {bot_info.id}")
    print(f"   Bot Name: {bot_info.first_name}")
except Exception as e:
    print(f"\n❌ Failed to connect to bot: {e}")
    exit(1)

# Test sending messages to groups
print("\n[1] Testing Group Messaging...")
print("-"*40)

test_groups = [
    "-1003538559040",
    "-4997223070", 
    "-1003643720778"
]

for group_id in test_groups:
    print(f"Testing group {group_id}...", end=" ")
    try:
        test_msg = f"""🧪 <b>Test Message</b>
━━━━━━━━━━━━━━━━
<b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
<b>Status:</b> Bot Testing
<b>Bot:</b> @MissNullMe
━━━━━━━━━━━━━━━━"""
        
        msg = bot.send_message(group_id, test_msg, parse_mode='HTML')
        print(f"✅ Success (msg_id: {msg.message_id})")
        
        # Delete test message after 2 seconds
        time.sleep(2)
        try:
            bot.delete_message(group_id, msg.message_id)
            print(f"   Cleanup: Message deleted")
        except:
            print(f"   Cleanup: Could not delete")
            
    except telebot.apihelper.ApiTelegramException as e:
        if "chat not found" in str(e).lower():
            print("❌ Chat not found")
        elif "bot was kicked" in str(e).lower():
            print("❌ Bot not in group")
        elif "not enough rights" in str(e).lower():
            print("❌ No permissions")
        else:
            print(f"❌ API Error: {str(e)[:30]}")
    except Exception as e:
        print(f"❌ Error: {str(e)[:30]}")
    
    time.sleep(1)

# Test bot commands
print("\n[2] Testing Bot Commands...")
print("-"*40)

# Get bot commands
try:
    commands = bot.get_my_commands()
    if commands:
        print("Registered commands:")
        for cmd in commands:
            print(f"  /{cmd.command} - {cmd.description}")
    else:
        print("No commands registered. Setting default commands...")
        
        # Set default commands
        bot.set_my_commands([
            telebot.types.BotCommand("start", "Start the bot"),
            telebot.types.BotCommand("check", "Check cards from file"),
            telebot.types.BotCommand("gateway", "Select gateway"),
            telebot.types.BotCommand("stop", "Stop current check"),
            telebot.types.BotCommand("status", "View bot status"),
            telebot.types.BotCommand("help", "Show help")
        ])
        print("✅ Commands set successfully")
except Exception as e:
    print(f"❌ Error with commands: {e}")

# Test webhook status
print("\n[3] Testing Webhook Status...")
print("-"*40)

try:
    webhook_info = bot.get_webhook_info()
    if webhook_info.url:
        print(f"⚠️ Webhook is set: {webhook_info.url}")
        print("   Removing webhook for polling mode...")
        bot.remove_webhook()
        print("   ✅ Webhook removed")
    else:
        print("✅ No webhook set (polling mode)")
except Exception as e:
    print(f"❌ Error checking webhook: {e}")

# Test file handling
print("\n[4] Testing File Operations...")
print("-"*40)

# Check if test cards file exists
test_file = "/home/null/Desktop/TestCards.txt"
if os.path.exists(test_file):
    with open(test_file, 'r') as f:
        lines = f.readlines()
        valid_cards = [l.strip() for l in lines if '|' in l and len(l.strip().split('|')) == 4]
        print(f"✅ Test file found: {len(valid_cards)} valid cards")
        
        # Show sample cards
        print("   Sample cards:")
        for card in valid_cards[:3]:
            parts = card.split('|')
            print(f"   - {parts[0][:4]}****|{parts[1]}|{parts[2]}|***")
else:
    print(f"❌ Test file not found: {test_file}")

# Test bot process
print("\n[5] Checking Bot Process...")
print("-"*40)

import subprocess
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
bot_processes = [line for line in result.stdout.split('\n') if 'mady_telegram_bot' in line and 'grep' not in line]

if bot_processes:
    print("✅ Bot process is running:")
    for proc in bot_processes:
        parts = proc.split()
        if len(parts) > 10:
            pid = parts[1]
            cpu = parts[2]
            mem = parts[3]
            cmd = ' '.join(parts[10:])
            print(f"   PID: {pid}, CPU: {cpu}%, MEM: {mem}%")
            print(f"   CMD: {cmd[:50]}...")
else:
    print("⚠️ Bot process not found. Starting bot...")
    # Could start the bot here if needed

# Test gateway availability
print("\n[6] Testing Gateway Availability...")
print("-"*40)

import sys
sys.path.insert(0, '100$/100$/')

gateways_available = []
gateway_tests = [
    (1, "Charge1", "BlemartCheckout"),
    (2, "Charge2", "DistrictPeopleCheckout"),
    (3, "Charge3", "SaintVinsonDonateCheckout"),
    (4, "Charge4", "BGDCheckoutLogic"),
    (5, "Charge5", "StaleksFloridaCheckoutVNew")
]

for num, module, func in gateway_tests:
    try:
        exec(f"from {module} import {func}")
        print(f"✅ Gateway {num} ({module}): Available")
        gateways_available.append(num)
    except ImportError as e:
        print(f"❌ Gateway {num} ({module}): Not available - {str(e)[:30]}")

# Summary
print("\n" + "="*70)
print("TELEGRAM BOT TEST SUMMARY")
print("="*70)

print(f"""
Bot Status:
  - Connection: ✅ Connected as @{bot_info.username if 'bot_info' in locals() else 'Unknown'}
  - Process: {'✅ Running' if bot_processes else '⚠️ Not detected'}
  - Gateways: {len(gateways_available)}/5 available
  - Test Cards: {'✅ Available' if os.path.exists(test_file) else '❌ Not found'}
  
Groups Accessible:
  - Group 1: {test_groups[0]} - Check logs above
  - Group 2: {test_groups[1]} - Check logs above  
  - Group 3: {test_groups[2]} - Check logs above

Ready for Testing:
  1. Open Telegram
  2. Search for @{bot_info.username if 'bot_info' in locals() else 'YourBot'}
  3. Send /start to begin
  4. Use /check to test card checking
  5. Upload TestCards.txt when prompted
""")

print("-"*70)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# Create a test card file for easy testing
print("\n[Creating small test file for quick testing...]")
test_content = """5566258985615466|12|25|299
4304450802433666|12|25|956
5587170478868301|12|25|286
4242424242424242|12|25|123
5534375250914413|12|25|471"""

with open("quick_test_cards.txt", "w") as f:
    f.write(test_content)
print("✅ Created quick_test_cards.txt with 5 cards for testing")
