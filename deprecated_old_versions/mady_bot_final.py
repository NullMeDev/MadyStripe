#
# !/usr/bin/env python3
"""
MADY BOT - Complete Telegram Card Checker
Features:
- Stripe Checker (API-based, fast)
- Shopify Payments Checker (HTTP-based, CHARGED mode)
- File upload support for bulk checking
- Multiple gateway selection

Bot Token: 7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s
Group ID: -1003538559040
Credit: @MissNullMe
"""

import os
import sys
import json
import time
import tempfile
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add gateway path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '100$/100$/'))

import telebot
from telebot import types
import requests

# --- Configuration ---
# Load from config file
try:
    with open('mady_config.json', 'r') as f:
        config = json.load(f)
    BOT_TOKEN = config.get('bot_token', '7984658748:AAFLNS52swKHJkh4kWuu3LDgckslaZjyJTY')
    GROUP_ID = config.get('group_id', '-1003538559040')
    BOT_CREDIT = config.get('bot_credit', '@MissNullMe')
except FileNotFoundError:
    # Fallback to hardcoded values
    BOT_TOKEN = "7984658748:AAFLNS52swKHJkh4kWuu3LDgckslaZjyJTY"
    GROUP_ID = "-1003538559040"
    BOT_CREDIT = "@MissNullMe"

# --- Gateway Imports ---
STRIPE_GATEWAYS = {}

try:
    from Charge1 import BlemartCheckout
    STRIPE_GATEWAYS[1] = {'func': BlemartCheckout, 'name': 'Blemart', 'amount': '$4.99'}
except Exception as e:
    print(f"Charge1 import failed: {e}")

try:
    from Charge2 import DistrictPeopleCheckout
    STRIPE_GATEWAYS[2] = {'func': DistrictPeopleCheckout, 'name': 'District People', 'amount': '€69.00'}
except Exception as e:
    print(f"Charge2 import failed: {e}")

try:
    from Charge3 import SaintVinsonDonateCheckout
    STRIPE_GATEWAYS[3] = {'func': SaintVinsonDonateCheckout, 'name': 'Saint Vinson', 'amount': '$0.01'}
except Exception as e:
    print(f"Charge3 import failed: {e}")

try:
    from Charge4 import BGDCheckoutLogic
    STRIPE_GATEWAYS[4] = {'func': BGDCheckoutLogic, 'name': 'BGD Fresh', 'amount': '$6.50'}
except Exception as e:
    print(f"Charge4 import failed: {e}")

try:
    from Charge5 import StaleksFloridaCheckoutVNew
    STRIPE_GATEWAYS[5] = {'func': StaleksFloridaCheckoutVNew, 'name': 'Staleks Florida', 'amount': '$0.01'}
except Exception as e:
    print(f"Charge5 import failed: {e}")

try:
    from Charge10_ShopifyPayments import ShopifyPaymentsCheck, check_multiple_cards
    SHOPIFY_AVAILABLE = True
except Exception as e:
    print(f"Shopify Payments import failed: {e}")
    SHOPIFY_AVAILABLE = False

# --- Initialize Bot ---
bot = telebot.TeleBot(BOT_TOKEN)

# --- User Sessions ---
user_sessions = {}

# --- Default Shopify Store (can be changed per user) ---
DEFAULT_SHOPIFY_STORE = None  # User must provide store URL

# --- Helper Functions ---
def parse_card(card_str):
    """Parse card string into components"""
    card_str = card_str.strip()
    parts = card_str.split('|')
    if len(parts) != 4:
        return None
    return {
        'number': parts[0].replace(' ', ''),
        'month': parts[1].zfill(2),
        'year': parts[2][-2:] if len(parts[2]) == 4 else parts[2],
        'cvv': parts[3]
    }

def mask_card(card_str):
    """Mask card number for display"""
    parts = card_str.split('|')
    if len(parts) >= 1:
        num = parts[0].replace(' ', '')
        return f"{num[:6]}****{num[-4:]}"
    return card_str

def check_stripe_card(card_str, gateway_id=3):
    """Check card using Stripe API gateway"""
    if gateway_id not in STRIPE_GATEWAYS:
        return "Error: Gateway not available"
    
    gateway = STRIPE_GATEWAYS[gateway_id]
    func = gateway['func']
    
    try:
        result = func(card_str)
        if isinstance(result, dict):
            if result.get('result') == 'success':
                return "CHARGED"
            elif 'error' in result:
                error = result.get('error', 'Unknown')
                if 'cvc' in error.lower() or 'cvv' in error.lower():
                    return "CVV_MISMATCH"
                elif 'insufficient' in error.lower():
                    return "INSUFFICIENT_FUNDS"
                elif 'expired' in error.lower():
                    return "EXPIRED_CARD"
                return f"DECLINED ({error[:30]})"
            else:
                return str(result)[:50]
        
        result_str = str(result).lower()
        if 'charged' in result_str or 'success' in result_str or 'approved' in result_str:
            return "CHARGED"
        elif 'cvv' in result_str or 'cvc' in result_str:
            return "CVV_MISMATCH"
        elif 'insufficient' in result_str:
            return "INSUFFICIENT_FUNDS"
        elif 'expired' in result_str:
            return "EXPIRED_CARD"
        elif '3ds' in result_str or 'action' in result_str:
            return "3DS_REQUIRED"
        else:
            return result[:50] if len(result) > 50 else result
            
    except Exception as e:
        return f"Error: {str(e)[:40]}"

def check_shopify_card(card_str, store_url):
    """Check card using Shopify Payments (CHARGED MODE)"""
    if not SHOPIFY_AVAILABLE:
        return "Error: Shopify checker not available"
    
    if not store_url:
        return "Error: No Shopify store URL set. Use /setstore <url>"
    
    try:
        result = ShopifyPaymentsCheck(card_str, store_url)
        return result
    except Exception as e:
        return f"Error: {str(e)[:40]}"

def format_result_message(card_str, result, checker_type="Stripe", gateway_info=""):
    """Format result for Telegram"""
    result_lower = result.lower() if isinstance(result, str) else str(result).lower()
    
    if any(x in result_lower for x in ['charged', 'success', 'approved']):
        status_emoji = "✅"
        status_text = "CHARGED"
    elif 'cvv' in result_lower or 'cvc' in result_lower:
        status_emoji = "🔐"
        status_text = "CVV MISMATCH"
    elif 'insufficient' in result_lower:
        status_emoji = "💰"
        status_text = "INSUFFICIENT FUNDS"
    elif '3ds' in result_lower or 'action' in result_lower:
        status_emoji = "🔒"
        status_text = "3DS REQUIRED"
    elif 'expired' in result_lower:
        status_emoji = "📅"
        status_text = "EXPIRED CARD"
    elif 'error' in result_lower:
        status_emoji = "⚠️"
        status_text = "ERROR"
    else:
        status_emoji = "❌"
        status_text = "DECLINED"
    
    msg = f"""
{status_emoji} <b>{status_text}</b>
━━━━━━━━━━━━━━━━
💳 <b>Card:</b> <code>{card_str}</code>
🔍 <b>Checker:</b> {checker_type}
{f'🚪 <b>Gateway:</b> {gateway_info}' if gateway_info else ''}
📝 <b>Response:</b> {result}
━━━━━━━━━━━━━━━━
🤖 <b>Bot:</b> {BOT_CREDIT}
"""
    return msg

# --- Bot Handlers ---
@bot.message_handler(commands=['start', 'help'])
def start_handler(message):
    """Show help message"""
    help_text = f"""
🤖 <b>MADY - Card Checker Bot</b>
━━━━━━━━━━━━━━━━━━━━━━

<b>🔷 STRIPE CHECKER</b>
/stripe &lt;card&gt; - Check single card
/gateway &lt;1-5&gt; - Select gateway
/gates - Show all gateways

<b>🟢 SHOPIFY CHECKER (CHARGED MODE)</b>
/shopify &lt;card&gt; - Check single card
/setstore &lt;url&gt; - Set Shopify store URL

<b>📁 FILE CHECKING</b>
Upload a .txt file with cards (one per line)
Then select Stripe or Shopify checker

<b>📝 CARD FORMAT</b>
<code>CARD|MM|YY|CVV</code>
Example: <code>4242424242424242|12|25|123</code>

<b>🔧 AVAILABLE STRIPE GATEWAYS</b>
"""
    
    for gid, info in sorted(STRIPE_GATEWAYS.items()):
        help_text += f"  {gid}. {info['name']} ({info['amount']})\n"
    
    help_text += f"""
━━━━━━━━━━━━━━━━━━━━━━
🤖 Bot by {BOT_CREDIT}
"""
    
    bot.reply_to(message, help_text, parse_mode='HTML')

@bot.message_handler(commands=['stripe', 'chk', 'check'])
def stripe_single_handler(message):
    """Check single card with Stripe"""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Usage: /stripe CARD|MM|YY|CVV")
            return
        
        card_str = parts[1].strip()
        
        if '|' not in card_str:
            bot.reply_to(message, "❌ Invalid format. Use: CARD|MM|YY|CVV")
            return
        
        # Get user's selected gateway
        user_id = message.from_user.id
        gateway_id = user_sessions.get(user_id, {}).get('gateway', 3)
        
        # Send processing message
        processing_msg = bot.reply_to(message, "⏳ Checking card with Stripe...")
        
        # Check card
        result = check_stripe_card(card_str, gateway_id)
        
        # Get gateway info
        gateway_info = STRIPE_GATEWAYS.get(gateway_id, {}).get('name', f'Gateway {gateway_id}')
        
        # Format and send result
        result_msg = format_result_message(card_str, result, "Stripe", gateway_info)
        bot.edit_message_text(result_msg, message.chat.id, processing_msg.message_id, parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

@bot.message_handler(commands=['shopify', 'shop'])
def shopify_single_handler(message):
    """Check single card with Shopify Payments (CHARGED MODE)"""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Usage: /shopify CARD|MM|YY|CVV")
            return
        
        card_str = parts[1].strip()
        
        if '|' not in card_str:
            bot.reply_to(message, "❌ Invalid format. Use: CARD|MM|YY|CVV")
            return
        
        # Get user's store URL
        user_id = message.from_user.id
        store_url = user_sessions.get(user_id, {}).get('shopify_store', DEFAULT_SHOPIFY_STORE)
        
        if not store_url:
            bot.reply_to(message, "❌ No Shopify store set. Use /setstore <url> first\n\nExample: /setstore https://example-store.myshopify.com")
            return
        
        # Send processing message
        processing_msg = bot.reply_to(message, f"⏳ Checking card with Shopify Payments (CHARGED MODE)...\n🏪 Store: {store_url[:40]}...")
        
        # Check card
        result = check_shopify_card(card_str, store_url)
        
        # Format and send result
        result_msg = format_result_message(card_str, result, "Shopify Payments", store_url[:30])
        bot.edit_message_text(result_msg, message.chat.id, processing_msg.message_id, parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

@bot.message_handler(commands=['setstore'])
def setstore_handler(message):
    """Set Shopify store URL for user"""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Usage: /setstore <shopify_store_url>\n\nExample: /setstore https://example-store.myshopify.com")
            return
        
        store_url = parts[1].strip()
        
        # Validate URL
        if not store_url.startswith('http'):
            store_url = 'https://' + store_url
        
        # Save to user session
        user_id = message.from_user.id
        if user_id not in user_sessions:
            user_sessions[user_id] = {}
        user_sessions[user_id]['shopify_store'] = store_url
        
        bot.reply_to(message, f"✅ Shopify store set to:\n<code>{store_url}</code>\n\nNow use /shopify CARD|MM|YY|CVV to check cards", parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

@bot.message_handler(commands=['gateway', 'gate'])
def gateway_handler(message):
    """Select Stripe gateway"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            # Show available gateways
            msg = "🔧 <b>Available Stripe Gateways:</b>\n\n"
            for gid, info in sorted(STRIPE_GATEWAYS.items()):
                msg += f"  /gateway {gid} - {info['name']} ({info['amount']})\n"
            bot.reply_to(message, msg, parse_mode='HTML')
            return
        
        gateway_id = int(parts[1])
        
        if gateway_id not in STRIPE_GATEWAYS:
            bot.reply_to(message, f"❌ Gateway {gateway_id} not available")
            return
        
        # Save user preference
        user_id = message.from_user.id
        if user_id not in user_sessions:
            user_sessions[user_id] = {}
        user_sessions[user_id]['gateway'] = gateway_id
        
        info = STRIPE_GATEWAYS[gateway_id]
        bot.reply_to(message, f"✅ Gateway set to: {gateway_id} - {info['name']} ({info['amount']})")
        
    except ValueError:
        bot.reply_to(message, "❌ Invalid gateway ID. Use a number 1-5")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

@bot.message_handler(commands=['gates', 'gateways'])
def gates_handler(message):
    """Show available gates"""
    msg = """
🚪 <b>AVAILABLE GATES</b>
━━━━━━━━━━━━━━━━━━━━━━

<b>🔷 STRIPE GATEWAYS</b>
"""
    
    for gid, info in sorted(STRIPE_GATEWAYS.items()):
        msg += f"  {gid}. {info['name']} - {info['amount']}\n"
    
    msg += f"""
<b>🟢 SHOPIFY PAYMENTS</b>
  Uses your Shopify store URL
  CHARGED MODE (real charges)
  Set store: /setstore &lt;url&gt;
  
━━━━━━━━━━━━━━━━━━━━━━
Use /gateway &lt;id&gt; to select Stripe gateway
Use /setstore &lt;url&gt; to set Shopify store
"""
    
    bot.reply_to(message, msg, parse_mode='HTML')

@bot.message_handler(commands=['stats', 'info'])
def stats_handler(message):
    """Show statistics"""
    user_id = message.from_user.id
    session = user_sessions.get(user_id, {})
    
    current_gateway = session.get('gateway', 3)
    gateway_info = STRIPE_GATEWAYS.get(current_gateway, {})
    shopify_store = session.get('shopify_store', 'Not set')
    
    msg = f"""
📊 <b>BOT STATUS</b>
━━━━━━━━━━━━━━━━━━━━━━

🔷 <b>Stripe Gateways:</b> {len(STRIPE_GATEWAYS)} available
🟢 <b>Shopify Checker:</b> {'Available' if SHOPIFY_AVAILABLE else 'Not available'}

<b>Your Settings:</b>
  Gateway: {current_gateway} - {gateway_info.get('name', 'Unknown')}
  Shopify Store: {shopify_store[:40] if shopify_store != 'Not set' else 'Not set'}

━━━━━━━━━━━━━━━━━━━━━━
🤖 Bot by {BOT_CREDIT}
"""
    
    bot.reply_to(message, msg, parse_mode='HTML')

@bot.message_handler(content_types=['document'])
def file_handler(message):
    """Handle file uploads"""
    try:
        # Check file extension
        file_name = message.document.file_name
        if not file_name.endswith('.txt'):
            bot.reply_to(message, "❌ Please upload a .txt file with cards")
            return
        
        # Download file
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            f.write(downloaded_file)
            temp_path = f.name
        
        # Read cards
        with open(temp_path, 'r') as f:
            lines = f.readlines()
        
        cards = []
        for line in lines:
            line = line.strip()
            if '|' in line and len(line.split('|')) == 4:
                cards.append(line)
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in file\n\nFormat: CARD|MM|YY|CVV")
            os.unlink(temp_path)
            return
        
        # Store temp path in session
        user_id = message.from_user.id
        if user_id not in user_sessions:
            user_sessions[user_id] = {}
        user_sessions[user_id]['temp_file'] = temp_path
        user_sessions[user_id]['cards'] = cards
        
        # Ask which checker to use
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔷 Stripe", callback_data="check_stripe"),
            types.InlineKeyboardButton("🟢 Shopify", callback_data="check_shopify")
        )
        
        bot.reply_to(
            message, 
            f"📁 Found <b>{len(cards)}</b> cards\n\nSelect checker:",
            reply_markup=markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('check_'))
def check_callback(call):
    """Handle checker selection callback"""
    try:
        checker_type = call.data.split('_')[1]  # stripe or shopify
        user_id = call.from_user.id
        
        session = user_sessions.get(user_id, {})
        cards = session.get('cards', [])
        temp_path = session.get('temp_file')
        
        if not cards:
            bot.answer_callback_query(call.id, "No cards found. Please upload file again.")
            return
        
        # Check Shopify store for shopify checker
        if checker_type == 'shopify':
            store_url = session.get('shopify_store')
            if not store_url:
                bot.answer_callback_query(call.id, "Set Shopify store first with /setstore")
                bot.edit_message_text(
                    "❌ No Shopify store set.\n\nUse /setstore <url> first",
                    call.message.chat.id,
                    call.message.message_id
                )
                return
        
        # Limit cards
        max_cards = 200
        cards_to_check = cards[:max_cards]
        
        # Update message
        bot.edit_message_text(
            f"⏳ Checking {len(cards_to_check)} cards with {checker_type.title()}...\n\n"
            f"Progress: 0/{len(cards_to_check)}",
            call.message.chat.id,
            call.message.message_id
        )
        
        # Get settings
        gateway_id = session.get('gateway', 3)
        store_url = session.get('shopify_store', '')
        
        # Process cards
        results = {'approved': [], 'declined': [], 'errors': []}
        
        for i, card in enumerate(cards_to_check):
            try:
                if checker_type == 'stripe':
                    result = check_stripe_card(card, gateway_id)
                else:
                    result = check_shopify_card(card, store_url)
                
                result_lower = result.lower() if isinstance(result, str) else str(result).lower()
                
                if any(x in result_lower for x in ['charged', 'cvv', 'insufficient', '3ds', 'success']):
                    results['approved'].append((card, result))
                elif 'error' in result_lower:
                    results['errors'].append((card, result))
                else:
                    results['declined'].append((card, result))
                    
            except Exception as e:
                results['errors'].append((card, str(e)[:30]))
            
            # Update progress every 10 cards
            if (i + 1) % 10 == 0 or i == len(cards_to_check) - 1:
                try:
                    bot.edit_message_text(
                        f"⏳ Checking {len(cards_to_check)} cards with {checker_type.title()}...\n\n"
                        f"Progress: {i+1}/{len(cards_to_check)}\n"
                        f"✅ {len(results['approved'])} | ❌ {len(results['declined'])} | ⚠️ {len(results['errors'])}",
                        call.message.chat.id,
                        call.message.message_id
                    )
                except:
                    pass
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
        
        # Send summary
        summary = f"""
📊 <b>CHECK COMPLETE</b>
━━━━━━━━━━━━━━━━━━━━━━
🔍 <b>Checker:</b> {checker_type.title()}
📁 <b>Total:</b> {len(cards_to_check)}
✅ <b>Approved:</b> {len(results['approved'])}
❌ <b>Declined:</b> {len(results['declined'])}
⚠️ <b>Errors:</b> {len(results['errors'])}
━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if results['approved']:
            summary += "\n<b>✅ APPROVED CARDS:</b>\n"
            for card, result in results['approved'][:30]:
                summary += f"<code>{card}</code>\n→ {result[:40]}\n\n"
        
        summary += f"\n🤖 Bot by {BOT_CREDIT}"
        
        # Split message if too long
        if len(summary) > 4000:
            summary = summary[:4000] + "...\n\n(Truncated)"
        
        bot.edit_message_text(summary, call.message.chat.id, call.message.message_id, parse_mode='HTML')
        
        # Cleanup
        try:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            if user_id in user_sessions:
                user_sessions[user_id].pop('temp_file', None)
                user_sessions[user_id].pop('cards', None)
        except:
            pass
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)[:50]}")

# --- Main ---
def main():
    print("="*60)
    print("MADY BOT - Stripe + Shopify Checker")
    print("="*60)
    print(f"Bot Token: {BOT_TOKEN[:20]}...")
    print(f"Group ID: {GROUP_ID}")
    print(f"Credit: {BOT_CREDIT}")
    print(f"Stripe Gateways: {len(STRIPE_GATEWAYS)}")
    print(f"Shopify Checker: {'Available' if SHOPIFY_AVAILABLE else 'Not available'}")
    print("="*60)
    print("Starting bot...")
    
    # Start polling
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
