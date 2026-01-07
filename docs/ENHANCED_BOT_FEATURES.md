# MadyStripe Enhanced Bot Features

## Overview

MadyStripe v2.0.0 introduces a comprehensive set of professional features for the Telegram bot, including user management, rate limiting, premium codes, and admin controls.

## New Features

### 1. SQLite Database (`src/core/database.py`)

Full-featured database with:
- **User Management**: Registration, profiles, statistics
- **Premium System**: Code generation, redemption, expiry tracking
- **Check History**: Logging all card checks with BIN masking
- **Admin Logging**: Audit trail for all admin actions
- **Settings Storage**: Persistent bot configuration

### 2. Rate Limiter (`src/core/rate_limiter.py`)

Per-user rate limiting with tier support:

| Tier | Hourly Limit | Daily Limit | Cooldown |
|------|-------------|-------------|----------|
| Free | 10 | 50 | 5s |
| Premium | 100 | 500 | 1s |
| Admin/Owner | Unlimited | Unlimited | 0s |

### 3. Enhanced Telegram Bot (`src/interfaces/telegram_bot.py`)

#### Public Commands
- `/start` - Welcome message with profile info
- `/help` - Show all available commands
- `/check <cc|mm|yy|cvv>` - Check a single card
- `/gates` - List available gateways
- `/mystatus` - View account status and statistics
- `/history` - View recent check history
- `/redeem <code>` - Redeem premium code
- `/stats` - Bot statistics
- `/ping` - Check bot latency

#### Admin Commands
- `/ban <user_id> <duration>` - Ban user (1hour, 1day, 2days, 1week, 1month, 1year, permanent)
- `/unban <user_id>` - Unban user
- `/userinfo <user_id>` - View user details
- `/broadcast <message>` - Send message to all users

#### Owner Commands
- `/gencode <days> [uses]` - Generate premium code
- `/setadmin <user_id>` - Promote user to admin
- `/removeadmin <user_id>` - Demote admin
- `/maintenance <on/off>` - Toggle maintenance mode
- `/botstats` - Detailed bot statistics

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE,
    username TEXT,
    role TEXT DEFAULT 'free',
    premium_until DATETIME,
    total_checks INTEGER DEFAULT 0,
    approved_checks INTEGER DEFAULT 0,
    declined_checks INTEGER DEFAULT 0,
    daily_checks INTEGER DEFAULT 0,
    is_banned INTEGER DEFAULT 0,
    ban_until DATETIME,
    created_at DATETIME
);
```

### Premium Codes Table
```sql
CREATE TABLE premium_codes (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE,
    days INTEGER,
    max_uses INTEGER DEFAULT 1,
    current_uses INTEGER DEFAULT 0,
    created_by INTEGER,
    expires_at DATETIME,
    is_active INTEGER DEFAULT 1
);
```

### Check History Table
```sql
CREATE TABLE check_history (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    card_bin TEXT,
    card_last4 TEXT,
    gateway TEXT,
    result TEXT,
    card_type TEXT,
    response_message TEXT,
    checked_at DATETIME
);
```

## Configuration

### Secrets File (`.secrets.local.json`)
```json
{
    "telegram": {
        "bot_token": "YOUR_BOT_TOKEN",
        "group_id": "-1001234567890"
    },
    "owner_ids": [123456789],
    "admin_ids": [987654321],
    "bot_credit": "@YourUsername"
}
```

## Usage

### Starting the Bot
```bash
cd /home/null/Desktop/MadyStripe
python3 -m src.interfaces.telegram_bot
```

### Or directly:
```bash
python3 src/interfaces/telegram_bot.py
```

## Security Features

1. **BIN Masking**: Only first 6 and last 4 digits logged
2. **Rate Limiting**: Prevents abuse
3. **Ban System**: Time-based user bans
4. **Admin Logging**: All admin actions tracked
5. **Maintenance Mode**: Disable bot for non-admins

## File Structure

```
src/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── database.py      # SQLite database
│   ├── rate_limiter.py  # Rate limiting
│   └── gateways.py      # Gateway manager
└── interfaces/
    ├── __init__.py
    └── telegram_bot.py  # Enhanced bot
```

## Dependencies

Add to `requirements.txt`:
```
pyTelegramBotAPI>=4.14.0
```

## Migration from Old Bot

1. The new bot uses SQLite instead of JSON files
2. User data will be created fresh on first interaction
3. Premium codes need to be regenerated
4. Admin/owner IDs configured in `.secrets.local.json`

## Future Enhancements

- [ ] MongoDB support for scalability
- [ ] 2FA authentication
- [ ] Web dashboard
- [ ] API endpoints
- [ ] Multi-bot support
