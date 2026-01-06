#!/usr/bin/env python3
"""
MADY COMPLETE BOT - Telegram Bot with Stripe + Shopify Checking
Integrates:
1. Stripe API Checker (Python - fast, API-based)
2. Shopify Payments Checker (Rust/Stripeify - browser-based)

Bot Commands:
/start - Show help
/stripe <card> - Check single card via Stripe
/shopify <card> - Check single card via Shopify Payments
/check <file> - Check file with Stripe (default)
/checkshopify <file> - Check file with Shopify Payments
/gates - Show available gates
/stats - Show statistics
"""

import os
import sys
import json
import time
import subprocess
import threading
import tempfile
from datetime import datetime

# Add gateway path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '100$/100$/'))

import telebot
from telebot import types

# --- Configuration ---
BOT_TOKEN = "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
GROUP_ID = "-1003538559040"
BOT_CREDIT = "@MissNullMe"

# Stripeify path
STRIPEIFY_DIR = "/home/null/Desktop/Stripeify"
STRIPEIFY_BIN = os.path.join(STRIPEIFY_DIR, "target/release/stripeify")

# --- Gateway Imports ---
STRIPE_GATEWAYS = {}

try:
    from Charge1 import BlemartCheckout
    STRIPE_GATEWAYS[1] = {'func': BlemartCheckout, 'name': 'Blemart', 'amount': '$4.99'}
except: pass

try:
    from Charge2 import DistrictPeopleCheckout
    STRIPE_GATEWAYS[2] = {'func': DistrictPeopleCheckout, 'name': 'District People', 'amount': '€69.00'}
except: pass

try:
    from Charge3 import SaintVinsonDonateCheckout
    STRIPE_GATEWAYS[3] = {'func': SaintVinsonDonateCheckout, 'name': 'Saint Vinson', 'amount': '$20.00'}
except: pass

try:
    from Charge4 import BGDCheckoutLogic
    STRIPE_GATEWAYS[4] = {'func': BGDCheckoutLogic, 'name': 'BGD Fresh', 'amount': '$6.50'}
except: pass

try:
    from Charge5 import StaleksFloridaCheckoutVNew
    STRIPE_GATEWAYS[5] = {'func': StaleksFloridaCheckoutVNew, 'name': 'Staleks Florida', 'amount': '$0.01'}
except: pass

try:
    from Charge9_StripeCheckout import StripeCheckoutGateway
    STRIPE_GATEWAYS[9] = {'func': StripeCheckoutGateway, 'name': 'Stripe Checkout', 'amount': 'Variable'}
except: pass

# --- Initialize Bot ---
bot = telebot.TeleBot(BOT_TOKEN)

# --- User Sessions ---
user_sessions = {}

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

def check_stripe_card(card_str, gateway_id=1):
    """Check card using Stripe API gateway"""
    if gateway_id not in STRIPE_GATEWAYS:
        return "Error: Gateway not available"
    
    gateway = STRIPE_GATEWAYS[gateway_id]
    func = gateway['func']
    
    try:
        result = func(card_str)
        if isinstance(result, dict):
            if result.get('result') == 'success':
                return "Approved"
            elif 'error' in result:
                return f"Declined ({result.get('error', 'Unknown')})"
            else:
                return str(result)
        return result
    except Exception as e:
        return f"Error: {str(e)[:50]}"

def check_shopify_card(card_str, gates_file=None, auth_only=True):
    """Check card using Shopify Payments (Stripeify)"""
    # Check if Stripeify binary exists
    if not os.path.exists(STRIPEIFY_BIN):
        return "Error: Stripeify not built. Run 'cargo build --release' in Stripeify directory."
    
    # Create temp files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(card_str + '\n')
        cards_file = f.name
    
    output_file = tempfile.mktemp(suffix='.json')
    
    # Use default gates if not specified
    if not gates_file:
        gates_file = os.path.join(STRIPEIFY_DIR, "valid_gates.json")
        if not os.path.exists(gates_file):
            gates_file = os.path.join(STRIPEIFY_DIR, "production_gates.json")
    
    try:
        # Build command
        cmd = [
            STRIPEIFY_BIN,
            "--cards", cards_file,
            "--gates", gates_file,
            "--output", output_file,
            "--max-gates", "5",
        ]
        
        if auth_only:
            cmd.append("--auth-only")
        
        # Run Stripeify
        result = subprocess.run(
            cmd,
            cwd=STRIPEIFY_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Parse output
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                results = json.load(f)
            
            if results:
                r = results[0]
                return f"{r.get('status', 'Unknown')} | Gate: {r.get('gate', 'Unknown')[:30]}"
            else:
                return "No result (gate may be down)"
        else:
            # Check stdout for result
            if "CVV_MISMATCH" in result.stdout:
                return "CVV_MISMATCH (Card Valid)"
            elif "CHARGED" in result.stdout:
                return "CHARGED"
            elif "DECLINED" in result.stdout:
                return "DECLINED"
            elif "INSUFFICIENT_FUNDS" in result.stdout:
                return "INSUFFICIENT_FUNDS"
            else:
                return f"Unknown result: {result.stdout[:100]}"
                
    except subprocess.TimeoutExpired:
        return "Error: Timeout (>120s)"
    except Exception as e:
        return f"Error: {str(e)[:50]}"
    finally:
        # Cleanup
        try:
            os.unlink(cards_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
        except:
            pass

def format_result_message(card_str, result, checker_type="Stripe"):
    """Format result for Telegram"""
    masked = mask_card(card_str)
    
    result_lower = result.lower() if isinstance(result, str) else str(result).lower()
    
    if any(x in result_lower for x in ['approved', 'charged', 'cvv_mismatch', 'success', 'pm created']):
        status_emoji = "✅"
        status_text = "APPROVED"
    elif 'insufficient' in result_lower:
        status_emoji = "💰"
        status_text = "INSUFFICIENT FUNDS"
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

<b>🔷 STRIPE CHECKER (API-based, Fast)</b>
/stripe &lt;card&gt; - Check single card
/stripecheck - Check file with Stripe
/gateway &lt;1-9&gt; - Select Stripe gateway

<b>🟢 SHOPIFY CHECKER (Browser-based)</b>
/shopify &lt;card&gt; - Check single card
/shopifycheck - Check file with Shopify

<b>📋 OTHER COMMANDS</b>
/gates - Show available gates
/stats - Show statistics
/help - Show this message

<b>📝 CARD FORMAT</b>
<code>CARD|MM|YY|CVV</code>
Example: <code>4242424242424242|12|25|123</code>

<b>🔧 STRIPE GATEWAYS</b>
"""
    
    for gid, info in sorted(STRIPE_GATEWAYS.items()):
        help_text += f"  {gid}. {info['name']} ({info['amount']})\n"
    
    help_text += f"""
━━━━━━━━━━━━━━━━━━━━━━
🤖 Bot by {BOT_CREDIT}
"""
    
    bot.reply_to(message, help_text, parse_mode='HTML')

@bot.message_handler(commands=['stripe'])
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
        gateway_id = user_sessions.get(user_id, {}).get('gateway', 1)
        
        # Send processing message
        processing_msg = bot.reply_to(message, "⏳ Checking card with Stripe...")
        
        # Check card
        result = check_stripe_card(card_str, gateway_id)
        
        # Format and send result
        result_msg = format_result_message(card_str, result, f"Stripe Gateway {gateway_id}")
        bot.edit_message_text(result_msg, message.chat.id, processing_msg.message_id, parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

@bot.message_handler(commands=['shopify'])
def shopify_single_handler(message):
    """Check single card with Shopify Payments"""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Usage: /shopify CARD|MM|YY|CVV")
            return
        
        card_str = parts[1].strip()
        
        if '|' not in card_str:
            bot.reply_to(message, "❌ Invalid format. Use: CARD|MM|YY|CVV")
            return
        
        # Send processing message
        processing_msg = bot.reply_to(message, "⏳ Checking card with Shopify Payments...\n(This may take 30-60 seconds)")
        
        # Check card
        result = check_shopify_card(card_str, auth_only=True)
        
        # Format and send result
        result_msg = format_result_message(card_str, result, "Shopify Payments")
        bot.edit_message_text(result_msg, message.chat.id, processing_msg.message_id, parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

@bot.message_handler(commands=['gateway'])
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
        bot.reply_to(message, "❌ Invalid gateway ID. Use a number 1-9")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

@bot.message_handler(commands=['gates'])
def gates_handler(message):
    """Show available gates"""
    msg = """
🚪 <b>AVAILABLE GATES</b>
━━━━━━━━━━━━━━━━━━━━━━

<b>🔷 STRIPE GATEWAYS (API-based)</b>
"""
    
    for gid, info in sorted(STRIPE_GATEWAYS.items()):
        msg += f"  {gid}. {info['name']} - {info['amount']}\n"
    
    msg += """
<b>🟢 SHOPIFY PAYMENTS (Browser-based)</b>
  Uses donation pages from Shopify stores
  Auth-only mode (no charges)
  
━━━━━━━━━━━━━━━━━━━━━━
Use /gateway <id> to select Stripe gateway
"""
    
    bot.reply_to(message, msg, parse_mode='HTML')

@bot.message_handler(commands=['stats'])
def stats_handler(message):
    """Show statistics"""
    msg = f"""
📊 <b>BOT STATISTICS</b>
━━━━━━━━━━━━━━━━━━━━━━

🔷 <b>Stripe Gateways:</b> {len(STRIPE_GATEWAYS)} available
🟢 <b>Shopify:</b> {'Available' if os.path.exists(STRIPEIFY_BIN) else 'Not built'}

━━━━━━━━━━━━━━━━━━━━━━
🤖 Bot by {BOT_CREDIT}
"""
    
    bot.reply_to(message, msg, parse_mode='HTML')

@bot.message_handler(content_types=['document'])
def file_handler(message):
    """Handle file uploads"""
    try:
        # Download file
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            f.write(downloaded_file)
            temp_path = f.name
        
        # Read cards
        with open(temp_path, 'r') as f:
            cards = [line.strip() for line in f if '|' in line.strip()]
        
        if not cards:
            bot.reply_to(message, "❌ No valid cards found in file")
            os.unlink(temp_path)
            return
        
        # Ask which checker to use
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔷 Stripe", callback_data=f"check_stripe_{temp_path}"),
            types.InlineKeyboardButton("🟢 Shopify", callback_data=f"check_shopify_{temp_path}")
        )
        
        bot.reply_to(
            message, 
            f"📁 Found {len(cards)} cards\n\nSelect checker:",
            reply_markup=markup
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('check_'))
def check_callback(call):
    """Handle checker selection callback"""
    try:
        parts = call.data.split('_', 2)
        checker_type = parts[1]  # stripe or shopify
        temp_path = parts[2]
        
        # Read cards
        with open(temp_path, 'r') as f:
            cards = [line.strip() for line in f if '|' in line.strip()]
        
        # Update message
        bot.edit_message_text(
            f"⏳ Checking {len(cards)} cards with {checker_type.title()}...",
            call.message.chat.id,
            call.message.message_id
        )
        
        # Get user's gateway for Stripe
        user_id = call.from_user.id
        gateway_id = user_sessions.get(user_id, {}).get('gateway', 1)
        
        # Process cards
        results = {'approved': [], 'declined': [], 'errors': []}
        
        for i, card in enumerate(cards[:100]):  # Limit to 100 cards
            if checker_type == 'stripe':
                result = check_stripe_card(card, gateway_id)
            else:
                result = check_shopify_card(card, auth_only=True)
            
            result_lower = result.lower() if isinstance(result, str) else str(result).lower()
            
            if any(x in result_lower for x in ['approved', 'charged', 'cvv_mismatch', 'success']):
                results['approved'].append((card, result))
            elif 'error' in result_lower:
                results['errors'].append((card, result))
            else:
                results['declined'].append((card, result))
            
            # Update progress every 10 cards
            if (i + 1) % 10 == 0:
                try:
                    bot.edit_message_text(
                        f"⏳ Progress: {i+1}/{len(cards[:100])}\n"
                        f"✅ {len(results['approved'])} | ❌ {len(results['declined'])} | ⚠️ {len(results['errors'])}",
                        call.message.chat.id,
                        call.message.message_id
                    )
                except:
                    pass
        
        # Send summary
        summary = f"""
📊 <b>CHECK COMPLETE</b>
━━━━━━━━━━━━━━━━━━━━━━
🔍 <b>Checker:</b> {checker_type.title()}
📁 <b>Total:</b> {len(cards[:100])}
✅ <b>Approved:</b> {len(results['approved'])}
❌ <b>Declined:</b> {len(results['declined'])}
⚠️ <b>Errors:</b> {len(results['errors'])}
━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if results['approved']:
            summary += "\n<b>✅ APPROVED CARDS:</b>\n"
            for card, result in results['approved'][:20]:
                summary += f"<code>{card}</code> → {result[:30]}\n"
        
        bot.edit_message_text(summary, call.message.chat.id, call.message.message_id, parse_mode='HTML')
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except:
            pass
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {str(e)[:50]}")

# --- Main ---
def main():
    print("="*60)
    print("MADY COMPLETE BOT - Stripe + Shopify Checker")
    print("="*60)
    print(f"Bot Token: {BOT_TOKEN[:20]}...")
    print(f"Group ID: {GROUP_ID}")
    print(f"Stripe Gateways: {len(STRIPE_GATEWAYS)}")
    print(f"Stripeify: {'Available' if os.path.exists(STRIPEIFY_BIN) else 'Not built'}")
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
