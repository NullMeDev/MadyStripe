# bot.py - v6.21: Display attempted charge amount in /start message

import requests
import telebot
import time
import os
import re
import json
import random
import string
from telebot import types
import traceback
import telebot.util
from datetime import datetime, timedelta

# --- Configuration ---
NEW_TOKEN = '7813629296:AAGFrbXtS9eNRYhmfhrg8DXbyObOQ41rt2c'
OWNER_ID = '7899718868'
DEVELOPER_TAG = "@pinta"

# --- Gateway Function Imports & Info ---
GATEWAY_INFO = {} # Store all gateway info here

try:
    from Charge1 import BlemartCheckout
    GATEWAY_INFO['charge1'] = {
        "func": BlemartCheckout, "name": "BlemartCheckout (Charge1.py)",
        "site": "Blemart (Bacola/Stripe PM)", "type": "string",
        "amount": "$4.99 USD" # Attempted amount
    }
except ImportError: print("Warning: Could not import BlemartCheckout from Charge1.py.")

try:
    from Charge2 import DistrictPeopleCheckout
    GATEWAY_INFO['charge2'] = {
        "func": DistrictPeopleCheckout, "name": "DistrictPeopleCheckout (Charge2.py)",
        "site": "District People (Konte/Stripe PM)", "type": "string",
        "amount": "€69.00 EUR" # Attempted amount
    }
except ImportError: print("Warning: Could not import DistrictPeopleCheckout from Charge2.py.")

try:
    from Charge3 import SaintVinsonDonateCheckout
    GATEWAY_INFO['charge3'] = {
        "func": SaintVinsonDonateCheckout, "name": "SaintVinsonDonateCheckout (Charge3.py)",
        "site": "Saint Vinson Donate (GiveWP/Stripe)", "type": "string",
        "amount": "$2.00 USD" # Attempted amount
    }
except ImportError: print("Warning: Could not import SaintVinsonDonateCheckout from Charge3.py.")

try:
    from Charge4 import BGDCheckoutLogic
    GATEWAY_INFO['charge4'] = {
        "func": BGDCheckoutLogic, "name": "BGDCheckoutLogic (Charge4.py)",
        "site": "BGD Fresh Milk (Reg + Stripe PM)", "type": "string",
        "amount": "$6.50 CAD" # Attempted amount
    }
except ImportError: print("Warning: Could not import BGDCheckoutLogic from Charge4.py.")

try:
    from Charge5 import StaleksFloridaCheckoutVNew
    GATEWAY_INFO['charge5'] = {
        "func": StaleksFloridaCheckoutVNew, "name": "StaleksFloridaCheckoutVNew (Charge5.py)",
        "site": "Staleks Florida (WooCommerce/Sources API)", "type": "dict",
        "amount": "$0.01 USD" # Attempted amount
    }
except ImportError: print("Warning: Could not import StaleksFloridaCheckoutVNew from Charge5.py.")

# --- Default Gateway Selection ---
try:
    DEFAULT_GATEWAY_KEY = "charge4" # Default key (e.g., 'charge4' for BGD Fresh Milk)

    if DEFAULT_GATEWAY_KEY not in GATEWAY_INFO or GATEWAY_INFO[DEFAULT_GATEWAY_KEY].get('func') is None:
        found_default = False
        for key, info in GATEWAY_INFO.items():
            if info.get('func') is not None:
                DEFAULT_GATEWAY_KEY = key; print(f"Warning: Default gateway '{DEFAULT_GATEWAY_KEY}' missing. Falling back to '{key}'."); found_default = True; break
        if not found_default: raise ValueError("No valid gateways could be loaded.")

    DEFAULT_GATEWAY_INFO = GATEWAY_INFO[DEFAULT_GATEWAY_KEY]
    ACTIVE_GATEWAY_FUNCTION = DEFAULT_GATEWAY_INFO['func']; GATEWAY_FUNCTION_NAME = DEFAULT_GATEWAY_INFO['name']
    TARGET_SITE_NAME = DEFAULT_GATEWAY_INFO['site']; EXPECTED_RESULT_TYPE = DEFAULT_GATEWAY_INFO['type']
    print(f"Default Gateway: {GATEWAY_FUNCTION_NAME}")

except (KeyError, ValueError) as e: print(f"FATAL ERROR setting default gateway: {e}"); exit()
except Exception as e: print(f"An unexpected error occurred during gateway initialization: {e}"); traceback.print_exc(); exit()

bot = telebot.TeleBot(NEW_TOKEN, parse_mode="HTML")

# --- User Management & State ---
allowed_users = [OWNER_ID]; valid_redeem_codes = {}; user_file_gateway_preference = {}
print("Bot starting..."); print(f"Owner ID: {OWNER_ID}"); print(f"DEFAULT GATEWAY: {GATEWAY_FUNCTION_NAME} ({TARGET_SITE_NAME})"); print(f"Initial Allowed Users: {allowed_users}")

# --- Bot Commands (Start, Status, Add, Delete, Code, Redeem - minor text changes) ---
@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.chat.id)
    print(f"Received /start from {user_id}")
    if user_id != OWNER_ID and user_id not in allowed_users:
        bot.reply_to(message, "🚫 <b>Access Denied!</b> 🚫\n\nContact @Jayaintactive.")
        return

    # Dynamically build the gateway command list with amounts
    gateway_command_lines = []
    # Ensure consistent order if needed, otherwise dict iteration order might vary
    sorted_gateway_keys = sorted(GATEWAY_INFO.keys())

    for key in sorted_gateway_keys:
        info = GATEWAY_INFO[key]
        if info.get('func'): # Only show if the gateway is loaded
            gw_num = key[-1] # Get the number (1, 2, 3, etc.)
            site_name_short = info['site'].split('(')[0].strip() # Shorter site name
            amount_str = info.get('amount', 'N/A') # Get the amount string
            gateway_command_lines.append(
                f"🔍 Use /cg{gw_num} <code>CC</code> for {site_name_short} ({amount_str})"
            )
        else:
             gw_num = key[-1]
             gateway_command_lines.append(
                f"❌ /cg{gw_num} ({info.get('site', 'Unknown')}) - Not Loaded"
             )

    gateway_commands_text = "\n".join(gateway_command_lines)
    default_gw_amount = GATEWAY_INFO.get(DEFAULT_GATEWAY_KEY, {}).get('amount', 'N/A') # Get default amount safely

    # Construct the final start message
    start_message = f"""
👋 Welcome {message.from_user.first_name}!

🤖 Bot: Payment Gateway Bot.
🎯 Default Target: <b>{telebot.util.escape(TARGET_SITE_NAME)}</b> ({default_gw_amount})

💳 Send a <code>.txt</code> file (<code>NUMBER|MM|YY|CVC</code>) for checking.
    ➡️ Use /chg1, /chg2, /chg3, /chg4 or /chg5 first to select the gateway.

{gateway_commands_text}

ℹ️ Use /info to check your user details.
⚙️ Use /gen <code>BIN</code> to generate cards (Luhn valid).

✨ **Other Commands:**
/status - Check bot status (owner only).
/add <code>[user_id]</code> - Add user (owner only).
/delete <code>[user_id]</code> - Remove user (owner only).
/code <code>[COUNT] [DAYS]</code> - Generate redeem code(s) (owner only).
/redeem <code>[code]</code> - Redeem access.

Ready when you are! 🔥
"""
    bot.reply_to(message, start_message)

@bot.message_handler(commands=["status"])
def status_check(message):
     if str(message.chat.id) == OWNER_ID:
         code_count = len(valid_redeem_codes); pending_prefs = len(user_file_gateway_preference)
         available_gws = []
         # Use sorted keys for consistent order
         for key in sorted(GATEWAY_INFO.keys()):
             info = GATEWAY_INFO[key]
             available_gws.append(f"✅ /cg{key[-1]} ({info['site']})" if info.get('func') else f"❌ /cg{key[-1]} ({info.get('site', 'Unknown')}) - Not Loaded")
         gw_status = "\n".join(available_gws)
         bot.reply_to(message, f"⚙️ Bot Status: <b>Online</b>\n👑 Owner ID: <code>{OWNER_ID}</code>\n🎯 Default Gateway: {GATEWAY_FUNCTION_NAME}\n👥 Allowed Users: <code>{len(allowed_users)}</code>\n🔑 Valid Redeem Codes: <code>{code_count}</code>\n⏳ Pending File Prefs: {pending_prefs}\n\n<b>Available Gateways:</b>\n{gw_status}")
     else: bot.reply_to(message,"🚫 Unauthorized command.")

# --- Add/Delete/Code/Redeem (No functional change needed from v6.17) ---
@bot.message_handler(commands=["add"])
def add_user(message):
    if str(message.chat.id) == OWNER_ID:
        try: parts = message.text.split(maxsplit=1); new_user_id = parts[1].strip(); assert new_user_id.isdigit()
        except (IndexError, AssertionError): bot.reply_to(message, "📋 Usage: /add USER_ID (Must be numbers)"); return
        if new_user_id not in allowed_users: allowed_users.append(new_user_id); print(f"Added: {new_user_id}"); bot.reply_to(message, f"✅ User <code>{new_user_id}</code> added!")
        else: bot.reply_to(message, f"🤔 User <code>{new_user_id}</code> already allowed.")
    else: bot.reply_to(message, "🚫 Unauthorized command.")
@bot.message_handler(commands=["delete"])
def delete_user(message):
    if str(message.chat.id) == OWNER_ID:
        try: parts = message.text.split(maxsplit=1); user_id_to_delete = parts[1].strip()
        except IndexError: bot.reply_to(message, "📋 Usage: /delete USER_ID"); return
        if user_id_to_delete == OWNER_ID: bot.reply_to(message, "🛡️ Cannot remove owner."); return
        if user_id_to_delete in allowed_users: allowed_users.remove(user_id_to_delete); print(f"Removed: {user_id_to_delete}"); bot.reply_to(message, f"🗑️ User <code>{user_id_to_delete}</code> removed.")
        else: bot.reply_to(message, f"❓ User <code>{user_id_to_delete}</code> not found.")
    else: bot.reply_to(message, "🚫 Unauthorized command.")
def generate_redeem_code_string(): return '-'.join(''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(3))
@bot.message_handler(commands=["code"])
def generate_code_command(message):
    if str(message.chat.id) == OWNER_ID:
        try:
            parts = message.text.split(); count, days = int(parts[1]), int(parts[2])
            assert count > 0 and days > 0 and len(parts) == 3
            codes, expiry_ts = [], (datetime.utcnow() + timedelta(days=days)).timestamp(); reply = f"✅ Generated <b>{count}</b> code(s) valid for <b>{days}</b> day(s):\n\n"
            generated_count = 0; attempts = 0; max_attempts = count * 5
            while generated_count < count and attempts < max_attempts:
                attempts += 1; new_code = generate_redeem_code_string()
                if new_code not in valid_redeem_codes: valid_redeem_codes[new_code] = expiry_ts; codes.append(f"<code>{new_code}</code>"); generated_count += 1
            if generated_count < count: reply = f"⚠️ Generated only {generated_count}/{count} codes due to potential collisions.\n\n" + "\n".join(codes)
            else: reply += "\n".join(codes)
            expiry_dt_str = datetime.utcfromtimestamp(expiry_ts).strftime('%Y-%m-%d %H:%M UTC'); reply += f"\n\nExpires: {expiry_dt_str}"; bot.reply_to(message, reply); print(f"Generated {generated_count} codes, valid for {days} days.")
        except Exception as e: bot.reply_to(message, f"⚠️ Invalid Usage or Error: {e}\nUse: <code>/code COUNT DAYS</code>")
    else: bot.reply_to(message, "🚫 Unauthorized command.")
@bot.message_handler(commands=["redeem"])
def redeem_code_command(message):
    user_id = str(message.chat.id)
    try: parts = message.text.split(maxsplit=1); code_to_redeem = parts[1].strip().upper()
    except IndexError: bot.reply_to(message, "📋 Usage: /redeem CODE"); return
    if user_id in allowed_users:
        bot.reply_to(message, "👍 You already have access.")
        if code_to_redeem in valid_redeem_codes: del valid_redeem_codes[code_to_redeem]; print(f"Code {code_to_redeem} removed (user already had access).")
        return
    if code_to_redeem in valid_redeem_codes:
        expiry_ts = valid_redeem_codes[code_to_redeem]
        if time.time() < expiry_ts:
            allowed_users.append(user_id); del valid_redeem_codes[code_to_redeem]
            expiry_dt = datetime.utcfromtimestamp(expiry_ts); expiry_dt_str = expiry_dt.strftime('%Y-%m-%d %H:%M UTC')
            bot.reply_to(message, f"✅ Code redeemed successfully!\nAccess granted until: {expiry_dt_str}")
            print(f"User {user_id} redeemed {code_to_redeem}.")
            try: bot.send_message(OWNER_ID, f"✅ Redeem Successful:\nUser: {message.from_user.first_name} (<code>{user_id}</code>)\nCode: <code>{code_to_redeem}</code>")
            except Exception as notify_err: print(f"Failed to notify owner about redeem: {notify_err}")
        else: del valid_redeem_codes[code_to_redeem]; bot.reply_to(message, f"❌ Code <code>{code_to_redeem}</code> has expired."); print(f"Expired code {code_to_redeem} attempted by {user_id}.")
    else: bot.reply_to(message, f"❌ Invalid or already used code: <code>{code_to_redeem}</code>.")

# --- BIN Lookup & Luhn Gen Functions (Copied from v6.12) ---
bin_session = requests.Session()
bin_session.headers.update({'User-Agent': 'Mozilla/5.0'})
def get_bin_info(bin_num):
    bin_data_dict = {'brand': 'N/A', 'type': 'N/A', 'country': 'N/A', 'country_flag': '🏳️', 'bank': 'N/A'}
    url = f'https://bins.antipublic.cc/bins/{bin_num}'
    try:
        response = bin_session.get(url, timeout=5); response.raise_for_status(); data = response.json()
        bin_data_dict['brand'] = str(data.get('brand') or 'N/A').upper(); bin_data_dict['type'] = str(data.get('type') or 'N/A').upper()
        bin_data_dict['country'] = str(data.get('country_name') or 'N/A'); bin_data_dict['country_flag'] = data.get('country_flag') or '🏳️'; bin_data_dict['bank'] = str(data.get('bank') or 'N/A')
    except requests.exceptions.Timeout: print(f"BIN lookup FAIL {bin_num}: Timeout"); bin_data_dict['bank'] = "Timeout"
    except requests.exceptions.HTTPError as e: print(f"BIN lookup FAIL {bin_num}: HTTP {e.response.status_code}"); bin_data_dict['bank'] = f"HTTP {e.response.status_code}"
    except requests.exceptions.RequestException as e: print(f"BIN lookup FAIL {bin_num}: Request Error {e}"); bin_data_dict['bank'] = "Request Error"
    except json.JSONDecodeError: print(f"BIN lookup FAIL {bin_num}: Invalid JSON"); bin_data_dict['bank'] = "JSON Error"
    except Exception as e: print(f"BIN lookup FAIL {bin_num}: {e}"); bin_data_dict['bank'] = "Lookup Error"
    for key, value in bin_data_dict.items():
        if value is None: bin_data_dict[key] = 'N/A' if key != 'country_flag' else '🏳️'
    return bin_data_dict
def calculate_luhn(card_number_partial):
    digits = [int(d) for d in card_number_partial];
    for i in range(len(digits) - 1, -1, -2): digits[i] = (digits[i] * 2) - 9 if digits[i] * 2 > 9 else digits[i] * 2
    checksum = sum(digits); luhn_digit = (checksum * 9) % 10; return luhn_digit
def generate_luhn_card(bin_num, length=16):
    if not bin_num.isdigit() or len(bin_num) < 6: return None
    partial_card = bin_num + ''.join(random.choice(string.digits) for _ in range(length - len(bin_num) - 1))
    luhn_check_digit = calculate_luhn(partial_card); return partial_card + str(luhn_check_digit)

# --- /info, /gen Commands (Copied from v6.12) ---
@bot.message_handler(commands=["info"])
def info_command(message):
    user_id = str(message.chat.id)
    if user_id != OWNER_ID and user_id not in allowed_users: bot.reply_to(message, "🚫 Access Denied."); return
    user_fname = telebot.util.escape(message.from_user.first_name or "N/A"); user_uname = f"@{message.from_user.username}" if message.from_user.username else "N/A"
    info_text = f"👤 **User Information**\n🆔 User ID: <code>{user_id}</code>\n🗣️ First Name: {user_fname}\n🌐 Username: {user_uname}\n🔑 Access Status: Allowed ✅"; bot.reply_to(message, info_text)
@bot.message_handler(commands=["gen"])
def gen_command(message):
    user_id = str(message.chat.id)
    if user_id != OWNER_ID and user_id not in allowed_users: bot.reply_to(message, "🚫 Access Denied."); return
    try: parts = message.text.split(maxsplit=1); bin_to_gen = parts[1].strip(); assert bin_to_gen.isdigit() and len(bin_to_gen) == 6
    except (IndexError, AssertionError): bot.reply_to(message, "📋 Usage: /gen 6_DIGIT_BIN"); return
    gen_msg = bot.send_message(message.chat.id, f"⚙️ Generating cards for BIN <code>{bin_to_gen}</code>..."); bin_data_dict = get_bin_info(bin_to_gen)
    gen_cards = []; current_year_short = int(time.strftime("%y")); max_tries = 20; generated_count = 0
    while generated_count < 10:
        tries = 0; card_number = None
        while card_number is None and tries < max_tries: card_number = generate_luhn_card(bin_to_gen); tries += 1
        if card_number is None: print(f"Failed to gen Luhn for {bin_to_gen} after {max_tries} tries"); break
        exp_year = current_year_short + random.randint(2, 6); exp_month = random.randint(1, 12); cvc = ''.join(random.choice(string.digits) for _ in range(3))
        exp_year_str = str(exp_year) if exp_year >= 10 else f"0{exp_year}"; gen_cards.append(f"{card_number}|{exp_month:02d}|{exp_year_str[-2:]}|{cvc}"); generated_count += 1
    bin_info_text = f"BIN Info: <code>{bin_to_gen}</code>\nBrand: {bin_data_dict['brand']} | Type: {bin_data_dict['type']}\nBank: {telebot.util.escape(bin_data_dict['bank'])}\nCountry: {telebot.util.escape(bin_data_dict['country'])} {bin_data_dict['country_flag']}\n--------------------"
    if gen_cards: cards_text = "\n".join([f"<code>{card}</code>" for card in gen_cards]); reply_message = f"{bin_info_text}\nGenerated Cards ({len(gen_cards)}):\n{cards_text}"
    else: reply_message = f"{bin_info_text}\n❌ Failed to generate cards for this BIN."
    bot.edit_message_text(reply_message, chat_id=message.chat.id, message_id=gen_msg.message_id)

# --- Result Parsing Function (Copied from v6.12 - Handles string/dict) ---
def parse_gateway_result(result_data, cc_combo, expected_type):
    status_icon = "❓"; status_title = "Unknown Result"; response_status = "UNKNOWN"
    response_icon = "❓"; response_detail = "N/A"; raw_snippet = "N/A"
    receipt_link = None; send_reply = False

    print(f"Parsing result for {cc_combo[:6]} - Type: {type(result_data)}, Expected: {expected_type}, Data: {str(result_data)[:200]}...")

    if expected_type == "string":
        if not isinstance(result_data, str):
             print(f"Warning: Expected string, got {type(result_data)}. Attempting dict parse...")
             if isinstance(result_data, dict) and "error" in result_data: result_string = result_data.get("error", "Unknown Error (Dict Fallback)"); raw_snippet = str(result_data)[:150]
             else: result_string = f"Unknown Type ({type(result_data)})"; raw_snippet = str(result_data)[:150]
        else: result_string = result_data; raw_snippet = result_string[:150]

        if result_string.startswith("Charged | "):
            parts = result_string.split(" | ", 1); status_icon, status_title, response_status, response_icon = "✅", "✅✅ Charged Successfully ✅✅", "CHARGED", "✅"; response_detail = "Payment Successful"; send_reply = True
            if len(parts) > 1 and parts[1].startswith("http"): receipt_link = parts[1]; response_detail += " (Receipt Link Found)"
            else: response_detail += " (No URL)"
        elif result_string == "Charged | Success Page (No URL in HTML)" or result_string == "Charged | Success Page (HTML Response)" or result_string == "Charged | Success (No Redirect URL)" or result_string == "Charged": status_icon, status_title, response_status, response_icon = "✅", "✅✅ Charged Successfully ✅✅", "CHARGED", "✅"; response_detail = "Payment Successful (No URL)"; send_reply = True
        elif "security code is incorrect" in result_string.lower() or "invalid_cvc" in result_string.lower() or "security code is invalid" in result_string.lower(): status_icon, status_title, response_status, response_icon = "✅", "✅✅ CCN Live ✅✅", "CCN LIVE", "✅"; response_detail = "Incorrect/Invalid Security Code"; send_reply = True
        elif "insufficient funds" in result_string.lower(): status_icon, status_title, response_status, response_icon = "💰", "💰💰 Insufficient Funds 💰💰", "INSUFFICIENT FUNDS", "💰"; response_detail = "Insufficient Funds"; send_reply = True
        elif "3DS/" in result_string or "Action Required" in result_string or "Verification Required" in result_string: status_icon, status_title, response_status, response_icon = "🔑", "🔑🔑 3DS/Action Required 🔑🔑", "3DS/ACTION", "🔑"; response_detail = result_string; send_reply = True
        elif result_string.startswith("Declined"):
            status_icon, status_title, response_status, response_icon = "❌", "❌❌ Card Declined ❌❌", "DECLINED", "❌"
            if "(Checkout Error:" in result_string: response_detail = result_string.split("(Checkout Error:", 1)[1].split(")", 1)[0]
            elif "(AVS -" in result_string: response_detail = result_string.split("(", 1)[1].split(")", 1)[0]
            elif ": " in result_string: response_detail = result_string.split(": ", 1)[1]
            elif "(" in result_string and ")" in result_string: response_detail = result_string[result_string.find("(")+1:result_string.rfind(")")]
            else: response_detail = result_string
        elif result_string.startswith("Error:"): status_icon, status_title, response_status, response_icon = "⚠️", "⚠️⚠️ Script Error ⚠️⚠️", "ERROR", "⚠️"; response_detail = result_string.split("Error:", 1)[1].strip()
        else: status_icon, status_title, response_status, response_icon = "❓", "❓❓ Unknown Response ❓❓", "UNKNOWN", "❓"; response_detail = result_string

    elif expected_type == "dict":
        if not isinstance(result_data, dict):
            print(f"Error: Expected dict, got {type(result_data)}."); status_icon, status_title, response_status, response_icon = "⚠️", "⚠️⚠️ Script Error ⚠️⚠️", "ERROR", "⚠️"; response_detail = f"Incorrect Result Type (Expected Dict, Got {type(result_data)})"; raw_snippet = str(result_data)[:150]; result_data = {}
        result_dict = result_data
        try:
            if "error" in result_dict:
                error_message = str(result_dict.get("error", "Unknown Gateway Error")).lower(); response_detail = str(result_dict.get("error", "Unknown Gateway Error")); raw_snippet = response_detail[:80]
                stripe_data = result_dict.get("stripe_response"); stripe_error_msg = ""
                if stripe_data and isinstance(stripe_data, dict) and "error" in stripe_data: stripe_error_msg = stripe_data["error"].get("message", "").lower(); response_detail = stripe_data["error"].get("message", "Stripe Error"); raw_snippet = response_detail[:80]
                if any(kw in error_message for kw in ['security code', 'cvc', 'check the card', 'incorrect_cvc']) or any(kw in stripe_error_msg for kw in ['security code', 'cvc', 'incorrect_cvc']): status_icon, status_title, response_status, response_icon = "✅", "✅✅ CCN Live ✅✅", "CCN LIVE", "✅"; response_detail = "Incorrect CVC / Check Card Details"; send_reply = True
                elif 'insufficient funds' in error_message or 'insufficient_funds' in stripe_error_msg: status_icon, status_title, response_status, response_icon = "💰", "💰💰 Insufficient Funds 💰💰", "INSUFFICIENT FUNDS", "💰"; response_detail = "Insufficient Funds"; send_reply = True
                elif 'expired card' in error_message or 'expired_card' in stripe_error_msg: status_icon, status_title, response_status, response_icon = "❌", "❌❌ Card Declined ❌❌", "DECLINED", "❌"; response_detail = "Expired Card"
                elif any(kw in error_message for kw in ['invalid api key', 'api_key', 'pk_live']) or any(kw in stripe_error_msg for kw in ['invalid_request_error', 'api_key']): status_icon, status_title, response_status, response_icon = "⚠️", "⚠️⚠️ Script Error ⚠️⚠️", "ERROR", "⚠️"; response_detail = "Config/API Key Error"; raw_snippet = error_message[:80]
                elif any(kw in error_message for kw in ['card was declined', 'generic_decline', 'do_not_honor', 'transaction_not_allowed', 'pickup_card', 'restricted_card']) or any(kw in stripe_error_msg for kw in ['generic_decline', 'do_not_honor', 'transaction_not_allowed', 'pickup_card', 'restricted_card']): status_icon, status_title, response_status, response_icon = "❌", "❌❌ Card Declined ❌❌", "DECLINED", "❌"; response_detail = "Card Declined (Generic/Risk)"
                elif "nonce scrape error" in error_message or "add to cart failed" in error_message or "failed fetch checkout" in error_message: status_icon, status_title, response_status, response_icon = "⚠️", "⚠️⚠️ Script Error ⚠️⚠️", "ERROR", "⚠️"; response_detail = f"Gateway Interaction Error ({result_dict.get('step','?')})"
                else: status_icon, status_title, response_status, response_icon = "⚠️", "⚠️⚠️ Script Error ⚠️⚠️", "ERROR", "⚠️"; raw_snippet = str(result_dict)[:80]
            elif result_dict.get("result") == "failure":
                messages_html = result_dict.get('messages', ''); messages_text = re.sub('<[^<]+?>', ' ', messages_html).strip().replace('\n', ' ').replace('  ', ' ').lower(); raw_snippet = messages_text[:80] if messages_text else "WooCommerce Failure (No Message)"
                status_icon, status_title, response_icon, response_status = "❌", "❌❌ Card Declined ❌❌", "❌", "DECLINED"; response_detail = "Declined (Generic - WC)"
                if any(kw in messages_text for kw in ['security code', 'cvc is incorrect', 'check the card details']): status_icon, status_title, response_status, response_icon = "✅", "✅✅ CCN Live ✅✅", "CCN LIVE", "✅"; response_detail = "Incorrect CVC / Check Card Details"; send_reply = True
                elif 'insufficient funds' in messages_text: status_icon, status_title, response_status, response_icon = "💰", "💰💰 Insufficient Funds 💰💰", "INSUFFICIENT FUNDS", "💰"; response_detail = "Insufficient Funds"; send_reply = True
                elif 'card was declined' in messages_text: response_detail = "Card Was Declined (WC)"
                elif 'expired card' in messages_text: response_detail = "Expired Card (WC)"
                elif any(kw in messages_text for kw in ['does not support', 'do not honor', 'transaction is not allowed', 'pickup_card']): response_detail = "Card Declined (WC - Check Type/Restrictions)"
            elif result_dict.get("result") == "success":
                redirect_url = result_dict.get("redirect", "").lower(); raw_snippet = f"Redirect: {result_dict.get('redirect', '')[:60]}..."; status_icon, status_title, response_status, response_icon = "✅", "✅✅ Charged Successfully ✅✅", "CHARGED", "✅"; response_detail = "Order Successful/Redirected"; send_reply = True
                if any(kw in redirect_url for kw in ["confirm", "_secret", "verify", "authenticate", "authentication_required", "challenge", "three_d_secure"]): status_icon, status_title, response_status, response_icon = "🔑", "🔑🔑 3DS Required / Action Needed 🔑🔑", "3DS/ACTION", "🔑"; response_detail = "Authentication/Redirect Required"
                elif any(kw in redirect_url for kw in ["order-received", "/key=", "thank_you", "order_id", "checkout/success"]): response_detail = "Order Received / Thank You Page"
            else: status_icon, status_title, response_status, response_icon = "❓", "❓❓ Unknown Response ❓❓", "UNKNOWN", "❓"; response_detail = "Unknown Gateway Response Structure"; raw_snippet = str(result_dict)[:80]
        except Exception as parse_e: status_icon, status_title, response_status, response_icon = "⚠️", "⚠️⚠️ Result Parse Error ⚠️⚠️", "ERROR", "⚠️"; response_detail = f"Error processing gateway dict result: {parse_e}"; raw_snippet = str(result_data)[:80]; print(f"Parse Error (Dict): {parse_e}\n{traceback.format_exc()}")

    else: status_icon, status_title, response_status, response_icon = "⚠️", "⚠️⚠️ Config Error ⚠️⚠️", "ERROR", "⚠️"; response_detail = f"Invalid expected_type: {expected_type}"; raw_snippet = str(result_data)[:150]

    return {"status_icon": status_icon, "status_title": status_title, "response_status": response_status, "response_icon": response_icon, "response_detail": response_detail, "raw_snippet": raw_snippet, "receipt_link": receipt_link, "send_reply": send_reply}

# --- Generic Single Check Function ---
def single_check_handler(message, gateway_key):
    user_id = str(message.chat.id)
    if user_id != OWNER_ID and user_id not in allowed_users: bot.reply_to(message, "🚫 Access Denied."); return

    gw_info = GATEWAY_INFO.get(gateway_key)
    if not gw_info or not gw_info.get('func'): bot.reply_to(message, f"❌ Gateway '{gateway_key}' not loaded or configured correctly."); return

    gw_func = gw_info['func']; gw_name = gw_info['name']; gw_site = gw_info['site']
    gw_type = gw_info['type']; gw_amount = gw_info.get('amount', 'N/A')

    command_name = f"/cg{gateway_key[-1]}"
    try: parts = message.text.split(maxsplit=1); cc_combo = parts[1].strip(); assert re.match(r"^\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}$", cc_combo)
    except (IndexError, AssertionError): bot.reply_to(message, f"⚠️ Invalid Usage.\nUse: <code>{command_name} CC|MM|YY|CVC</code>"); return

    processing_msg = bot.reply_to(message, f"⏳ Checking <code>{cc_combo.split('|')[0][:6]}...</code> via {gw_name}")
    start_time = time.time(); bin_num = cc_combo.split('|')[0][:6]; bin_data_dict = get_bin_info(bin_num)

    gateway_result = None
    try: gateway_result = gw_func(cc_combo)
    except Exception as e: print(f"Gateway Function Error {command_name} {cc_combo}: {e}\n{traceback.format_exc()}"); gateway_result = f"Error: Gateway Func Exception: {e}" if gw_type == "string" else {"error": f"Gateway Func Exception: {e}"}
    end_time = time.time(); execution_time = end_time - start_time

    try: parsed_info = parse_gateway_result(gateway_result, cc_combo, gw_type)
    except Exception as parse_err: print(f"CRITICAL PARSE ERROR {command_name}: {parse_err}\n{traceback.format_exc()}"); parsed_info = { "status_icon": "⚠️", "status_title": "⚠️⚠️ Result Parse Error ⚠️⚠️", "response_status": "ERROR", "response_icon": "⚠️", "response_detail": f"Fatal Error processing result: {parse_err}", "raw_snippet": str(gateway_result)[:150], "receipt_link": None }

    user_display_name = telebot.util.escape(message.from_user.first_name or "User")
    reply_message = f"{parsed_info['status_icon']*2} {telebot.util.escape(parsed_info['status_title'])} {parsed_info['status_icon']*2}\n\nCard: <code>{cc_combo}</code>\nGateway: {telebot.util.escape(gw_site)}\nResponse: {parsed_info['response_status']} {parsed_info['response_icon']} ({telebot.util.escape(parsed_info['response_detail'])})"
    if parsed_info['response_status'] == "CHARGED": reply_message += f"\nAmount: {gw_amount}"
    reply_message += f"\n\nBin: {bin_num}\nInfo: {bin_data_dict['brand']} - {bin_data_dict['type']}\nBank: {telebot.util.escape(bin_data_dict['bank'])}\nCountry: {telebot.util.escape(bin_data_dict['country'])} {bin_data_dict['country_flag']}\n\nTime: {"{:.2f}".format(execution_time)} seconds\nChecked by: {user_display_name}"
    if parsed_info.get('receipt_link'): reply_message += f"\n<b>Receipt/Order</b>: <a href='{parsed_info['receipt_link']}'>View Order</a>"
    reply_message += f"\nRaw: <code>{telebot.util.escape(parsed_info['raw_snippet'])}</code>\nDev: {DEVELOPER_TAG}"

    # Send / Edit Reply (Fixed v6.19)
    try:
        bot.edit_message_text(reply_message, chat_id=message.chat.id, message_id=processing_msg.message_id, disable_web_page_preview=True)
    except telebot.apihelper.ApiTelegramException as api_ex:
        if "message is not modified" not in str(api_ex):
            print(f"Error editing {command_name} message: {api_ex}")
            try:
                bot.send_message(message.chat.id, reply_message, disable_web_page_preview=True)
            except Exception as send_ex:
                print(f"Error sending fallback {command_name} message: {send_ex}")
    except Exception as edit_e:
        print(f"Error editing {command_name} message (non-API): {edit_e}")
        try:
            bot.send_message(message.chat.id, reply_message, disable_web_page_preview=True)
        except Exception as send_ex:
            print(f"Error sending fallback {command_name} message: {send_ex}")

# --- Individual Gateway Command Handlers ---
@bot.message_handler(commands=["cg1"])
def cg1_command(message): single_check_handler(message, 'charge1')
@bot.message_handler(commands=["cg2"])
def cg2_command(message): single_check_handler(message, 'charge2')
@bot.message_handler(commands=["cg3"])
def cg3_command(message): single_check_handler(message, 'charge3')
@bot.message_handler(commands=["cg4"])
def cg4_command(message): single_check_handler(message, 'charge4')
@bot.message_handler(commands=["cg5"])
def cg5_command(message): single_check_handler(message, 'charge5')


# --- Generic File Preference Command Handler ---
def file_pref_handler(message, gateway_key):
    user_id = str(message.chat.id)
    if user_id != OWNER_ID and user_id not in allowed_users: bot.reply_to(message, "🚫 Access Denied."); return
    gw_info = GATEWAY_INFO.get(gateway_key)
    if not gw_info or not gw_info.get('func'): bot.reply_to(message, f"❌ Gateway function for '{gateway_key}' not loaded. Cannot set preference."); return
    user_file_gateway_preference[user_id] = gateway_key # Store key only
    print(f"User {user_id} set file preference to {gw_info['name']}")
    bot.reply_to(message, f"✅ Gateway for next file upload set to: <b>{telebot.util.escape(gw_info['site'])}</b>.\nPlease send your <code>.txt</code> file now.")

# --- Individual File Preference Handlers ---
@bot.message_handler(commands=["chg1"])
def chg1_command(message): file_pref_handler(message, 'charge1')
@bot.message_handler(commands=["chg2"])
def chg2_command(message): file_pref_handler(message, 'charge2')
@bot.message_handler(commands=["chg3"])
def chg3_command(message): file_pref_handler(message, 'charge3')
@bot.message_handler(commands=["chg4"])
def chg4_command(message): file_pref_handler(message, 'charge4')
@bot.message_handler(commands=["chg5"])
def chg5_command(message): file_pref_handler(message, 'charge5')


# --- Document Handler (Uses selected or default gateway) ---
@bot.message_handler(content_types=["document"])
def main(message):
    user_id = str(message.chat.id)
    print(f"Received document from {user_id}")
    if user_id != OWNER_ID and user_id not in allowed_users: bot.reply_to(message, "🚫 Access Denied."); return
    if not message.document.file_name.lower().endswith(".txt"): bot.reply_to(message, "⚠️ Send <code>.txt</code> file."); return

    preferred_gw_key = user_file_gateway_preference.get(user_id)
    selected_gw_key = None; selected_gw_info = None
    if preferred_gw_key and preferred_gw_key in GATEWAY_INFO and GATEWAY_INFO[preferred_gw_key].get('func'):
        selected_gw_key = preferred_gw_key; selected_gw_info = GATEWAY_INFO[selected_gw_key]
        print(f"Using user {user_id}'s preference: {selected_gw_info['name']}")
        try: del user_file_gateway_preference[user_id]; print(f"Cleared file preference for user {user_id}")
        except KeyError: print(f"Warning: Could not clear preference for user {user_id}, might have been cleared already.")
    else:
        selected_gw_key = DEFAULT_GATEWAY_KEY; selected_gw_info = DEFAULT_GATEWAY_INFO
        print(f"No valid preference found for user {user_id}. Using default: {selected_gw_info['name']}")

    selected_gateway_func = selected_gw_info['func']; selected_gateway_name = selected_gw_info['name']
    selected_site_name = selected_gw_info['site']; selected_expected_type = selected_gw_info['type']
    selected_amount = selected_gw_info.get('amount', 'N/A')

    if selected_gateway_func is None: bot.reply_to(message, f"❌ Cannot process file. The selected gateway '{selected_gateway_name}' is not available (check bot logs and files)."); return

    counters = {'charged': 0, 'ccn_live': 0, '3ds_action': 0, 'insufficient_funds': 0, 'declined': 0, 'error': 0}
    total_count = 0; processed_count = 0; status_message_id = None
    temp_file_path = f"temp_{user_id}_combo_{message.message_id}.txt"; stop_file_path = f"{user_id}.stop"

    # Cleanup old stop file (Syntax Fixed v6.20)
    if os.path.exists(stop_file_path):
        try:
            os.remove(stop_file_path)
            print(f"Removed old stop file: {stop_file_path}")
        except OSError as e:
            print(f"Error removing old stop file {stop_file_path}: {e}")

    try:
        file_info = bot.get_file(message.document.file_id); assert file_info.file_size <= 1024 * 1024
        print(f"Downloading: {message.document.file_name}"); downloaded_file = bot.download_file(file_info.file_path)
        with open(temp_file_path, "wb") as w: w.write(downloaded_file)
        status_message = bot.reply_to(message, f"⏳ Processing <code>{telebot.util.escape(message.document.file_name)}</code> via {selected_gateway_name}..."); status_message_id = status_message.message_id
        start_process_time = time.time()

        with open(temp_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines(); total_count = len(lines)
            if total_count == 0: bot.edit_message_text("⚠️ File is empty.", chat_id=message.chat.id, message_id=status_message_id); return

            print(f"Total lines: {total_count}")
            for line_num, line in enumerate(lines):
                processed_count += 1; cc_combo = line.strip()
                # Stop Check (Syntax Fixed v6.16)
                if os.path.exists(stop_file_path):
                    print(f"Stop file found for user {user_id}. Halting.")
                    try: bot.edit_message_text(f'🛑 Process stopped by user.\nProcessed: {processed_count-1}/{total_count}', chat_id=message.chat.id, message_id=status_message_id, reply_markup=None)
                    except Exception: pass
                    return
                if not re.match(r"^\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}$", cc_combo): print(f"Skip invalid line {line_num+1}: {cc_combo[:20]}..."); counters['error'] += 1; continue

                if processed_count % 5 == 0 or processed_count == 1 or processed_count == total_count:
                    try:
                        elapsed_time = time.time() - start_process_time; time_per_card = elapsed_time / processed_count if processed_count > 0 else 0; est_remaining = (total_count - processed_count) * time_per_card
                        current_progress_text = (f"**⏳ Processing: {telebot.util.escape(message.document.file_name)}**\nTarget: {telebot.util.escape(selected_site_name)}\nCard: <code>{cc_combo[:6]}******{cc_combo[-4:]}</code>\nProgress: {processed_count}/{total_count} ({elapsed_time:.1f}s / Est: {est_remaining:.0f}s)\n\n✅ C:{counters['charged']} | 🔑 3DS:{counters['3ds_action']} | ✅ CCN:{counters['ccn_live']} | 💰 LowF:{counters['insufficient_funds']} | ❌ Dec:{counters['declined']} | ⚠️ Err:{counters['error']}")
                        mes = types.InlineKeyboardMarkup(row_width=1); mes.add(types.InlineKeyboardButton("🛑 STOP 🛑", callback_data=f'stop_{user_id}'))
                        if not (processed_count > 1 and elapsed_time < 1.5 and processed_count % 15 != 0 and processed_count != total_count): bot.edit_message_text(chat_id=message.chat.id, message_id=status_message_id, text=current_progress_text, reply_markup=mes)
                    except telebot.apihelper.ApiTelegramException as api_ex:
                        if "message is not modified" not in str(api_ex): print(f"Status update error (API): {api_ex}")
                    except Exception as e: print(f"Status update error: {e}")

                bin_num = cc_combo.split('|')[0][:6]; bin_data_dict = get_bin_info(bin_num)
                card_process_start_time = time.time(); gateway_result = None
                try: gateway_result = selected_gateway_func(cc_combo)
                except Exception as e: print(f"Gateway Function Error {cc_combo}: {e}\n{traceback.format_exc()}"); gateway_result = f"Error: Gateway Func Exception: {e}" if selected_expected_type == "string" else {"error": f"Gateway Func Exception: {e}"}
                card_process_end_time = time.time(); execution_time = card_process_end_time - card_process_start_time

                try: parsed_info = parse_gateway_result(gateway_result, cc_combo, selected_expected_type)
                except Exception as parse_err: print(f"CRITICAL PARSE ERROR main: {parse_err}\n{traceback.format_exc()}"); parsed_info = { "status_icon": "⚠️", "status_title": "⚠️⚠️ Result Parse Error ⚠️⚠️", "response_status": "ERROR", "response_icon": "⚠️", "response_detail": f"Fatal Error processing result: {parse_err}", "raw_snippet": str(gateway_result)[:150], "receipt_link": None, "send_reply": False }; counters['error'] += 1

                status = parsed_info['response_status']
                if status == "CHARGED": counters['charged'] += 1
                elif status == "CCN LIVE": counters['ccn_live'] += 1
                elif status == "3DS/ACTION": counters['3ds_action'] += 1
                elif status == "INSUFFICIENT FUNDS": counters['insufficient_funds'] += 1
                elif status == "ERROR": counters['error'] += 1
                elif status == "DECLINED": counters['declined'] += 1
                else: counters['error'] += 1

                if parsed_info['send_reply']:
                    user_display_name = telebot.util.escape(message.from_user.first_name or "User")
                    reply_message = f"{parsed_info['status_icon']*2} {telebot.util.escape(parsed_info['status_title'])} {parsed_info['status_icon']*2}\n\nCard: <code>{cc_combo}</code>\nGateway: {telebot.util.escape(selected_site_name)}\nResponse: {parsed_info['response_status']} {parsed_info['response_icon']} ({telebot.util.escape(parsed_info['response_detail'])})"
                    if parsed_info['response_status'] == "CHARGED": reply_message += f"\nAmount: {selected_amount}" # Show amount on charged
                    reply_message += f"\n\nBin: {bin_num}\nInfo: {bin_data_dict['brand']} - {bin_data_dict['type']}\nBank: {telebot.util.escape(bin_data_dict['bank'])}\nCountry: {telebot.util.escape(bin_data_dict['country'])} {bin_data_dict['country_flag']}\n\nTime: {"{:.2f}".format(execution_time)} seconds\nChecked by: {user_display_name}"
                    if parsed_info.get('receipt_link'): reply_message += f"\n<b>Receipt/Order</b>: <a href='{parsed_info['receipt_link']}'>View Order</a>"
                    reply_message += f"\nRaw: <code>{telebot.util.escape(parsed_info['raw_snippet'])}</code>\nDev: {DEVELOPER_TAG}"
                    try: bot.send_message(message.chat.id, reply_message, disable_web_page_preview=True)
                    except Exception as send_err: print(f"Send Error during file processing: {send_err}")
                # time.sleep(0.1)

            end_process_time = time.time(); total_execution_time = end_process_time - start_process_time
            summary_text = f"""🎉 **Processing Complete!** 🎉\n\n📁 File: <code>{telebot.util.escape(message.document.file_name)}</code>\n🎯 Gateway Used: {telebot.util.escape(selected_site_name)}\n🧮 Processed: {processed_count}/{total_count}\n⏱️ Time: {"{:.2f}".format(total_execution_time)}s\n--- Results ---\n✅ Charged: {counters['charged']} | 🔑 3DS/Action: {counters['3ds_action']}\n✅ CCN Live: {counters['ccn_live']} | 💰 Low Funds: {counters['insufficient_funds']}\n❌ Declined: {counters['declined']} | ⚠️ Errors: {counters['error']}\n---\nChecked By: {telebot.util.escape(message.from_user.first_name or 'User')}\nBot: @{bot.get_me().username} ({DEVELOPER_TAG})"""
            if status_message_id:
                try: bot.edit_message_text(chat_id=message.chat.id, message_id=status_message_id, text=summary_text, reply_markup=None, disable_web_page_preview=True)
                except Exception as final_edit_err: print(f"Error editing final summary: {final_edit_err}"); bot.send_message(message.chat.id, summary_text, disable_web_page_preview=True)
            else: bot.send_message(message.chat.id, summary_text, disable_web_page_preview=True)
            print("Processing finished.")

    except AssertionError: bot.reply_to(message, "⚠️ File size exceeds 1MB limit.")
    except FileNotFoundError: print(f"Error: Temp file not found ({temp_file_path})."); bot.reply_to(message, "❌ Error reading processed file.")
    except telebot.apihelper.ApiTelegramException as api_main_ex: print(f"Main Handler API Error: {api_main_ex}"); bot.reply_to(message, f"❌ Telegram API Error: {api_main_ex}")
    except Exception as e: print(f"Main Handler Error: {e}"); traceback.print_exc(); bot.reply_to(message, f"❌ Unexpected Error during processing: {e}")
    finally:
        # Cleanup Temp File (Fixed v6.17)
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            try: os.remove(temp_file_path); print(f"Cleaned temp file: {temp_file_path}")
            except OSError as e: print(f"Cleanup Error (temp file {temp_file_path}): {e}")
        # Cleanup Stop File (Fixed v6.17)
        if 'stop_file_path' in locals() and os.path.exists(stop_file_path):
             try: os.remove(stop_file_path); print(f"Cleaned stop file: {stop_file_path}")
             except OSError as e: print(f"Cleanup Error (stop file {stop_file_path}): {e}")
        # Clear user preference just in case it wasn't cleared earlier (Fixed v6.17)
        if user_id in user_file_gateway_preference:
            try: del user_file_gateway_preference[user_id]; print(f"Cleared preference for {user_id} in finally block.")
            except KeyError: pass

# --- Callback Query Handlers (Stop Button - Copied from v6.12) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('stop_'))
def stop_callback(call):
    try: target_user_id = call.data.split('_')[1]
    except IndexError: bot.answer_callback_query(call.id, text="Invalid stop request data."); return
    if call.message.reply_to_message: original_user_id = str(call.message.reply_to_message.from_user.id)
    else: original_user_id = str(call.message.chat.id)
    if target_user_id == original_user_id and str(call.from_user.id) == original_user_id:
        stop_file_path = f"{target_user_id}.stop"
        try:
            with open(stop_file_path, "w") as f: f.write("stop"); print(f"Stop file created by {target_user_id}: {stop_file_path}")
            bot.answer_callback_query(call.id, text="🛑 Stopping process...")
            bot.edit_message_text("🛑 Stopping requested...", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
        except Exception as e: print(f"Stop Callback Error: {e}"); bot.answer_callback_query(call.id, text="Error stopping process.")
    else: bot.answer_callback_query(call.id, text="🚫 You cannot stop this process.")

# --- Start Polling ---
print("+-----------------------------------------------------------------+")
print(f"Bot @{bot.get_me().username} running (DEFAULT Gateway: {GATEWAY_FUNCTION_NAME})...")
print("+-----------------------------------------------------------------+")
while True:
    try: bot.infinity_polling(timeout=20, long_polling_timeout=10, none_stop=True)
    except requests.exceptions.ReadTimeout: print("Polling ReadTimeout. Reconnecting..."); time.sleep(5)
    except requests.exceptions.ConnectionError: print("Polling ConnectionError. Reconnecting..."); time.sleep(10)
    except telebot.apihelper.ApiTelegramException as api_ex: print(f"Polling API Error: {api_ex}. Retrying..."); time.sleep(15)
    except Exception as e: print(f"CRITICAL POLLING ERROR: {e}"); traceback.print_exc(); print("Attempting restart poll in 30s..."); time.sleep(30)