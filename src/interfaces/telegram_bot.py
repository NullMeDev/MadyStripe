#!/usr/bin/env python3
"""
MadyStripe Enhanced Telegram Bot
Full-featured Telegram bot with user management, rate limiting, and premium system
"""

import os
import sys
import json
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from functools import wraps

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import telebot
    from telebot import types
    from telebot.async_telebot import AsyncTeleBot
except ImportError:
    print("Installing pyTelegramBotAPI...")
    os.system("pip install pyTelegramBotAPI")
    import telebot
    from telebot import types
    from telebot.async_telebot import AsyncTeleBot

from core.database import get_database, Database
from core.rate_limiter import get_rate_limiter, RateLimiter, RateLimitExceeded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MadyStripeBot')

# Load configuration
def load_config() -> Dict:
    """Load bot configuration from secrets file"""
    config = {
        'bot_token': None,
        'group_id': None,
        'owner_ids': [],
        'admin_ids': [],
        'bot_credit': '@MissNullMe'
    }
    
    # Try loading from .secrets.local.json
    secrets_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.secrets.local.json'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'secrets.json'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mady_config.json'),
    ]
    
    for path in secrets_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    config['bot_token'] = data.get('telegram', {}).get('bot_token') or data.get('bot_token')
                    config['group_id'] = data.get('telegram', {}).get('group_id') or data.get('group_id')
                    config['owner_ids'] = data.get('owner_ids', [])
                    config['admin_ids'] = data.get('admin_ids', [])
                    config['bot_credit'] = data.get('bot_credit', '@MissNullMe')
                    break
            except:
                continue
    
    # Environment variable fallback
    if not config['bot_token']:
        config['bot_token'] = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not config['group_id']:
        config['group_id'] = os.environ.get('TELEGRAM_GROUP_ID')
    
    return config


class MadyStripeBot:
    """Enhanced MadyStripe Telegram Bot"""
    
    VERSION = "2.0.0"
    
    def __init__(self, token: str = None):
        self.config = load_config()
        self.token = token or self.config['bot_token']
        
        if not self.token:
            raise ValueError("Bot token not provided. Set TELEGRAM_BOT_TOKEN or configure .secrets.local.json")
        
        self.bot = AsyncTeleBot(self.token)
        self.db = get_database()
        self.rate_limiter = get_rate_limiter()
        
        # Gateway manager (lazy loaded)
        self._gateway_manager = None
        
        # Maintenance mode
        self.maintenance_mode = self.db.get_setting('maintenance_mode', False)
        
        # Register handlers
        self._register_handlers()
        
        logger.info(f"MadyStripe Bot v{self.VERSION} initialized")
    
    @property
    def gateway_manager(self):
        """Lazy load gateway manager"""
        if self._gateway_manager is None:
            try:
                from core.gateways import get_gateway_manager
                self._gateway_manager = get_gateway_manager()
            except ImportError:
                logger.warning("Gateway manager not available")
        return self._gateway_manager
    
    def _get_user_tier(self, telegram_id: int) -> str:
        """Get user's tier for rate limiting"""
        user = self.db.get_user(telegram_id)
        if not user:
            return 'free'
        return user.get('role', 'free')
    
    def _is_owner(self, telegram_id: int) -> bool:
        """Check if user is owner"""
        return telegram_id in self.config.get('owner_ids', []) or self.db.is_owner(telegram_id)
    
    def _is_admin(self, telegram_id: int) -> bool:
        """Check if user is admin or owner"""
        return (telegram_id in self.config.get('admin_ids', []) or 
                telegram_id in self.config.get('owner_ids', []) or 
                self.db.is_admin(telegram_id))
    
    def _register_handlers(self):
        """Register all message handlers"""
        
        # ==================== Public Commands ====================
        
        @self.bot.message_handler(commands=['start'])
        async def cmd_start(message):
            """Welcome message"""
            user = self.db.get_or_create_user(
                message.from_user.id,
                message.from_user.username
            )
            
            welcome = f"""
🎴 <b>Welcome to MadyStripe Bot v{self.VERSION}</b> 🎴

<b>Your Profile:</b>
• ID: <code>{message.from_user.id}</code>
• Username: @{message.from_user.username or 'N/A'}
• Status: {'👑 Premium' if self.db.is_premium(message.from_user.id) else '🆓 Free'}

<b>Quick Commands:</b>
/help - Show all commands
/check - Check a card
/gates - List available gateways
/mystatus - Your account status

<b>Bot Credit:</b> {self.config['bot_credit']}
"""
            await self.bot.reply_to(message, welcome, parse_mode='HTML')
        
        @self.bot.message_handler(commands=['help', 'cmds'])
        async def cmd_help(message):
            """Show help message"""
            is_admin = self._is_admin(message.from_user.id)
            is_owner = self._is_owner(message.from_user.id)
            
            help_text = """
📚 <b>MadyStripe Bot Commands</b>

<b>🔍 Checking Commands:</b>
/check <code>cc|mm|yy|cvv</code> - Check single card
/mass - Check multiple cards (reply to file)
/gates - List available gateways
/gate <code>id</code> - Set default gateway

<b>👤 Account Commands:</b>
/mystatus - Your account status
/history - Check history
/redeem <code>code</code> - Redeem premium code

<b>📊 Info Commands:</b>
/bin <code>123456</code> - BIN lookup
/ping - Check bot status
/stats - Bot statistics
"""
            
            if is_admin:
                help_text += """
<b>🛡️ Admin Commands:</b>
/ban <code>user_id</code> <code>duration</code> - Ban user
/unban <code>user_id</code> - Unban user
/userinfo <code>user_id</code> - User information
/broadcast <code>message</code> - Broadcast to all users
"""
            
            if is_owner:
                help_text += """
<b>👑 Owner Commands:</b>
/gencode <code>days</code> <code>uses</code> - Generate premium code
/setadmin <code>user_id</code> - Set user as admin
/removeadmin <code>user_id</code> - Remove admin
/maintenance <code>on/off</code> - Toggle maintenance
/botstats - Detailed bot statistics
"""
            
            help_text += f"\n<b>Bot:</b> {self.config['bot_credit']}"
            
            await self.bot.reply_to(message, help_text, parse_mode='HTML')
        
        @self.bot.message_handler(commands=['mystatus', 'me', 'profile'])
        async def cmd_mystatus(message):
            """Show user status"""
            user = self.db.get_or_create_user(
                message.from_user.id,
                message.from_user.username
            )
            
            stats = self.db.get_user_stats(message.from_user.id)
            usage = self.rate_limiter.get_usage(message.from_user.id, user.get('role', 'free'))
            
            # Premium status
            premium_status = "🆓 Free"
            premium_until = ""
            if user.get('role') == 'owner':
                premium_status = "👑 Owner"
            elif user.get('role') == 'admin':
                premium_status = "🛡️ Admin"
            elif self.db.is_premium(message.from_user.id):
                premium_status = "⭐ Premium"
                if user.get('premium_until'):
                    premium_until = f"\n• Expires: {user['premium_until'][:10]}"
            
            status_text = f"""
👤 <b>Your Profile</b>

<b>Account:</b>
• ID: <code>{message.from_user.id}</code>
• Username: @{message.from_user.username or 'N/A'}
• Status: {premium_status}{premium_until}
• Member Since: {user.get('created_at', 'N/A')[:10]}

<b>📊 Statistics:</b>
• Total Checks: {stats.get('total_checks', 0):,}
• Approved: {stats.get('approved_checks', 0):,}
• Declined: {stats.get('declined_checks', 0):,}
• Success Rate: {stats.get('success_rate', 0):.1f}%

<b>⏱️ Rate Limits:</b>
• Hourly: {usage['hourly_used']}/{usage['hourly_limit']}
• Daily: {usage['daily_used']}/{usage['daily_limit']}
"""
            await self.bot.reply_to(message, status_text, parse_mode='HTML')
        
        @self.bot.message_handler(commands=['check', 'chk', 'cc'])
        async def cmd_check(message):
            """Check a single card"""
            # Check maintenance mode
            if self.maintenance_mode and not self._is_admin(message.from_user.id):
                await self.bot.reply_to(message, "🔧 Bot is under maintenance. Please try again later.")
                return
            
            # Check if banned
            if self.db.is_banned(message.from_user.id):
                await self.bot.reply_to(message, "🚫 You are banned from using this bot.")
                return
            
            # Get user tier
            user = self.db.get_or_create_user(message.from_user.id, message.from_user.username)
            tier = user.get('role', 'free')
            
            # Check rate limit
            allowed, limit_msg = self.rate_limiter.check_limit(message.from_user.id, tier)
            if not allowed:
                await self.bot.reply_to(message, limit_msg)
                return
            
            # Parse card from message
            text = message.text.split(maxsplit=1)
            if len(text) < 2:
                await self.bot.reply_to(message, "❌ Usage: /check cc|mm|yy|cvv")
                return
            
            card_str = text[1].strip()
            
            # Validate card format
            card_pattern = r'^\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}$'
            if not re.match(card_pattern, card_str):
                await self.bot.reply_to(message, "❌ Invalid card format. Use: cc|mm|yy|cvv")
                return
            
            # Send processing message
            processing_msg = await self.bot.reply_to(message, "⏳ Checking card...")
            
            try:
                # Record rate limit
                self.rate_limiter.start_request(message.from_user.id)
                
                # Check card using gateway
                if self.gateway_manager:
                    status, result_msg, card_type = self.gateway_manager.check(card_str)
                else:
                    status, result_msg, card_type = "error", "Gateway not available", "Unknown"
                
                self.rate_limiter.record_request(message.from_user.id)
                
                # Log check
                parts = card_str.split('|')
                self.db.log_check(
                    message.from_user.id,
                    parts[0][:6],  # BIN
                    parts[0][-4:],  # Last 4
                    "default",
                    status,
                    card_type,
                    result_msg
                )
                
                # Format response
                if status == "approved":
                    response = f"""
✅ <b>APPROVED</b>

<b>Card:</b> <code>{card_str}</code>
<b>Status:</b> {result_msg}
<b>Type:</b> {card_type}

<b>Bot:</b> {self.config['bot_credit']}
"""
                elif status == "declined":
                    response = f"""
❌ <b>DECLINED</b>

<b>Card:</b> <code>{card_str}</code>
<b>Response:</b> {result_msg}

<b>Bot:</b> {self.config['bot_credit']}
"""
                else:
                    response = f"""
⚠️ <b>ERROR</b>

<b>Card:</b> <code>{card_str}</code>
<b>Error:</b> {result_msg}

<b>Bot:</b> {self.config['bot_credit']}
"""
                
                await self.bot.edit_message_text(
                    response,
                    message.chat.id,
                    processing_msg.message_id,
                    parse_mode='HTML'
                )
                
            except Exception as e:
                logger.error(f"Check error: {e}")
                await self.bot.edit_message_text(
                    f"❌ Error: {str(e)[:100]}",
                    message.chat.id,
                    processing_msg.message_id
                )
            finally:
                self.rate_limiter.end_request(message.from_user.id)
        
        @self.bot.message_handler(commands=['gates', 'gateways'])
        async def cmd_gates(message):
            """List available gateways"""
            if not self.gateway_manager:
                await self.bot.reply_to(message, "❌ Gateway manager not available")
                return
            
            gateways = self.gateway_manager.list_gateways()
            
            gates_text = "🚪 <b>Available Gateways</b>\n\n"
            for gw in gateways:
                gates_text += f"[{gw['id']}] {gw['name']} - {gw.get('charge', 'N/A')}\n"
            
            gates_text += f"\n<i>Use /gate <id> to set default gateway</i>"
            
            await self.bot.reply_to(message, gates_text, parse_mode='HTML')
        
        @self.bot.message_handler(commands=['redeem'])
        async def cmd_redeem(message):
            """Redeem a premium code"""
            text = message.text.split(maxsplit=1)
            if len(text) < 2:
                await self.bot.reply_to(message, "❌ Usage: /redeem <code>")
                return
            
            code = text[1].strip().upper()
            success, msg, days = self.db.redeem_code(code, message.from_user.id)
            
            if success:
                await self.bot.reply_to(message, f"✅ {msg}\n\nEnjoy your premium access! 🎉")
            else:
                await self.bot.reply_to(message, f"❌ {msg}")
        
        @self.bot.message_handler(commands=['history'])
        async def cmd_history(message):
            """Show check history"""
            history = self.db.get_user_history(message.from_user.id, limit=10)
            
            if not history:
                await self.bot.reply_to(message, "📜 No check history found.")
                return
            
            history_text = "📜 <b>Recent Check History</b>\n\n"
            for i, check in enumerate(history, 1):
                status_emoji = "✅" if check['result'] == 'approved' else "❌"
                history_text += f"{i}. {status_emoji} {check['card_bin']}****{check['card_last4']} - {check['checked_at'][:16]}\n"
            
            await self.bot.reply_to(message, history_text, parse_mode='HTML')
        
        @self.bot.message_handler(commands=['stats'])
        async def cmd_stats(message):
            """Show bot statistics"""
            stats = self.db.get_total_stats()
            
            stats_text = f"""
📊 <b>Bot Statistics</b>

<b>Users:</b>
• Total: {stats['total_users']:,}
• Premium: {stats['premium_users']:,}

<b>Checks:</b>
• Total: {stats['total_checks']:,}
• Approved: {stats['approved_checks']:,}
• Today: {stats['today_checks']:,}
• Success Rate: {stats['success_rate']:.1f}%

<b>Bot:</b> {self.config['bot_credit']}
"""
            await self.bot.reply_to(message, stats_text, parse_mode='HTML')
        
        @self.bot.message_handler(commands=['ping'])
        async def cmd_ping(message):
            """Check bot status"""
            start = datetime.now()
            msg = await self.bot.reply_to(message, "🏓 Pong!")
            latency = (datetime.now() - start).total_seconds() * 1000
            await self.bot.edit_message_text(
                f"🏓 Pong! Latency: {latency:.0f}ms",
                message.chat.id,
                msg.message_id
            )
        
        # ==================== Admin Commands ====================
        
        @self.bot.message_handler(commands=['ban'])
        async def cmd_ban(message):
            """Ban a user (admin only)"""
            if not self._is_admin(message.from_user.id):
                await self.bot.reply_to(message, "🚫 Admin only command")
                return
            
            parts = message.text.split()
            if len(parts) < 2:
                await self.bot.reply_to(message, "❌ Usage: /ban <user_id> [duration]\nDurations: 1hour, 1day, 2days, 1week, 1month, 1year, permanent")
                return
            
            try:
                target_id = int(parts[1])
                duration = parts[2] if len(parts) > 2 else 'permanent'
                reason = ' '.join(parts[3:]) if len(parts) > 3 else None
                
                if self._is_owner(target_id):
                    await self.bot.reply_to(message, "🚫 Cannot ban owner")
                    return
                
                self.db.ban_user(target_id, duration, reason)
                self.db.log_admin_action(message.from_user.id, 'ban', target_id, f"Duration: {duration}")
                
                await self.bot.reply_to(message, f"✅ User {target_id} banned for {duration}")
            except ValueError:
                await self.bot.reply_to(message, "❌ Invalid user ID")
        
        @self.bot.message_handler(commands=['unban'])
        async def cmd_unban(message):
            """Unban a user (admin only)"""
            if not self._is_admin(message.from_user.id):
                await self.bot.reply_to(message, "🚫 Admin only command")
                return
            
            parts = message.text.split()
            if len(parts) < 2:
                await self.bot.reply_to(message, "❌ Usage: /unban <user_id>")
                return
            
            try:
                target_id = int(parts[1])
                self.db.unban_user(target_id)
                self.db.log_admin_action(message.from_user.id, 'unban', target_id)
                
                await self.bot.reply_to(message, f"✅ User {target_id} unbanned")
            except ValueError:
                await self.bot.reply_to(message, "❌ Invalid user ID")
        
        @self.bot.message_handler(commands=['userinfo'])
        async def cmd_userinfo(message):
            """Get user info (admin only)"""
            if not self._is_admin(message.from_user.id):
                await self.bot.reply_to(message, "🚫 Admin only command")
                return
            
            parts = message.text.split()
            if len(parts) < 2:
                await self.bot.reply_to(message, "❌ Usage: /userinfo <user_id>")
                return
            
            try:
                target_id = int(parts[1])
                user = self.db.get_user(target_id)
                
                if not user:
                    await self.bot.reply_to(message, "❌ User not found")
                    return
                
                stats = self.db.get_user_stats(target_id)
                
                info = f"""
👤 <b>User Info</b>

<b>ID:</b> <code>{user['telegram_id']}</code>
<b>Username:</b> @{user.get('username', 'N/A')}
<b>Role:</b> {user.get('role', 'free')}
<b>Premium Until:</b> {user.get('premium_until', 'N/A')}
<b>Banned:</b> {'Yes' if user.get('is_banned') else 'No'}
<b>Created:</b> {user.get('created_at', 'N/A')[:10]}

<b>Stats:</b>
• Total Checks: {stats.get('total_checks', 0)}
• Approved: {stats.get('approved_checks', 0)}
• Success Rate: {stats.get('success_rate', 0):.1f}%
"""
                await self.bot.reply_to(message, info, parse_mode='HTML')
            except ValueError:
                await self.bot.reply_to(message, "❌ Invalid user ID")
        
        # ==================== Owner Commands ====================
        
        @self.bot.message_handler(commands=['gencode'])
        async def cmd_gencode(message):
            """Generate premium code (owner only)"""
            if not self._is_owner(message.from_user.id):
                await self.bot.reply_to(message, "🚫 Owner only command")
                return
            
            parts = message.text.split()
            if len(parts) < 2:
                await self.bot.reply_to(message, "❌ Usage: /gencode <days> [max_uses]")
                return
            
            try:
                days = int(parts[1])
                max_uses = int(parts[2]) if len(parts) > 2 else 1
                
                code = self.db.generate_code(days, max_uses, message.from_user.id)
                
                await self.bot.reply_to(message, f"""
🎁 <b>Premium Code Generated</b>

<b>Code:</b> <code>{code}</code>
<b>Days:</b> {days}
<b>Max Uses:</b> {max_uses}

<i>Share this code with users to redeem premium access.</i>
""", parse_mode='HTML')
                
                self.db.log_admin_action(message.from_user.id, 'gencode', details=f"Days: {days}, Uses: {max_uses}")
            except ValueError:
                await self.bot.reply_to(message, "❌ Invalid parameters")
        
        @self.bot.message_handler(commands=['setadmin'])
        async def cmd_setadmin(message):
            """Set user as admin (owner only)"""
            if not self._is_owner(message.from_user.id):
                await self.bot.reply_to(message, "🚫 Owner only command")
                return
            
            parts = message.text.split()
            if len(parts) < 2:
                await self.bot.reply_to(message, "❌ Usage: /setadmin <user_id>")
                return
            
            try:
                target_id = int(parts[1])
                self.db.update_user(target_id, role='admin')
                self.db.log_admin_action(message.from_user.id, 'setadmin', target_id)
                
                await self.bot.reply_to(message, f"✅ User {target_id} is now an admin")
            except ValueError:
                await self.bot.reply_to(message, "❌ Invalid user ID")
        
        @self.bot.message_handler(commands=['removeadmin'])
        async def cmd_removeadmin(message):
            """Remove admin (owner only)"""
            if not self._is_owner(message.from_user.id):
                await self.bot.reply_to(message, "🚫 Owner only command")
                return
            
            parts = message.text.split()
            if len(parts) < 2:
                await self.bot.reply_to(message, "❌ Usage: /removeadmin <user_id>")
                return
            
            try:
                target_id = int(parts[1])
                self.db.update_user(target_id, role='free')
                self.db.log_admin_action(message.from_user.id, 'removeadmin', target_id)
                
                await self.bot.reply_to(message, f"✅ Admin removed from user {target_id}")
            except ValueError:
                await self.bot.reply_to(message, "❌ Invalid user ID")
        
        @self.bot.message_handler(commands=['maintenance'])
        async def cmd_maintenance(message):
            """Toggle maintenance mode (owner only)"""
            if not self._is_owner(message.from_user.id):
                await self.bot.reply_to(message, "🚫 Owner only command")
                return
            
            parts = message.text.split()
            if len(parts) < 2 or parts[1].lower() not in ['on', 'off']:
                await self.bot.reply_to(message, "❌ Usage: /maintenance <on/off>")
                return
            
            self.maintenance_mode = parts[1].lower() == 'on'
            self.db.set_setting('maintenance_mode', self.maintenance_mode)
            
            status = "enabled 🔧" if self.maintenance_mode else "disabled ✅"
            await self.bot.reply_to(message, f"Maintenance mode {status}")
        
        @self.bot.message_handler(commands=['botstats'])
        async def cmd_botstats(message):
            """Detailed bot statistics (owner only)"""
            if not self._is_owner(message.from_user.id):
                await self.bot.reply_to(message, "🚫 Owner only command")
                return
            
            stats = self.db.get_total_stats()
            daily_stats = self.db.get_daily_stats(7)
            gateway_stats = self.db.get_gateway_stats()
            
            stats_text = f"""
📊 <b>Detailed Bot Statistics</b>

<b>Users:</b>
• Total: {stats['total_users']:,}
• Premium: {stats['premium_users']:,}

<b>Checks:</b>
• Total: {stats['total_checks']:,}
• Approved: {stats['approved_checks']:,}
• Today: {stats['today_checks']:,}
• Success Rate: {stats['success_rate']:.1f}%

<b>Last 7 Days:</b>
"""
            for day in daily_stats[:7]:
                stats_text += f"• {day['date']}: {day['total']} checks ({day['approved']} approved)\n"
            
            if gateway_stats:
                stats_text += "\n<b>Gateway Performance:</b>\n"
                for gw in gateway_stats[:5]:
                    stats_text += f"• {gw['gateway']}: {gw['total']} ({gw['success_rate']}%)\n"
            
            await self.bot.reply_to(message, stats_text, parse_mode='HTML')
        
        @self.bot.message_handler(commands=['broadcast'])
        async def cmd_broadcast(message):
            """Broadcast message to all users (admin only)"""
            if not self._is_admin(message.from_user.id):
                await self.bot.reply_to(message, "🚫 Admin only command")
                return
            
            text = message.text.split(maxsplit=1)
            if len(text) < 2:
                await self.bot.reply_to(message, "❌ Usage: /broadcast <message>")
                return
            
            broadcast_msg = text[1]
            users = self.db.get_all_users(limit=10000)
            
            sent = 0
            failed = 0
            
            status_msg = await self.bot.reply_to(message, f"📢 Broadcasting to {len(users)} users...")
            
            for user in users:
                try:
                    await self.bot.send_message(
                        user['telegram_id'],
                        f"📢 <b>Broadcast Message</b>\n\n{broadcast_msg}",
                        parse_mode='HTML'
                    )
                    sent += 1
                except:
                    failed += 1
                
                # Update progress every 50 users
                if (sent + failed) % 50 == 0:
                    await self.bot.edit_message_text(
                        f"📢 Broadcasting... {sent + failed}/{len(users)}",
                        message.chat.id,
                        status_msg.message_id
                    )
            
            await self.bot.edit_message_text(
                f"✅ Broadcast complete!\n• Sent: {sent}\n• Failed: {failed}",
                message.chat.id,
                status_msg.message_id
            )
            
            self.db.log_admin_action(message.from_user.id, 'broadcast', details=f"Sent: {sent}, Failed: {failed}")
    
    async def run(self):
        """Start the bot"""
        logger.info(f"Starting MadyStripe Bot v{self.VERSION}...")
        logger.info(f"Bot credit: {self.config['bot_credit']}")
        
        try:
            await self.bot.polling(non_stop=True, skip_pending=True)
        except Exception as e:
            logger.error(f"Bot error: {e}")
            raise


def main():
    """Main entry point"""
    try:
        bot = MadyStripeBot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == '__main__':
    main()
