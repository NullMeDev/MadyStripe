# Mady Bot - Telegram Card Checker

## 🤖 Bot Information
- **Bot Token**: `7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s`
- **Group ID**: `-1003538559040`
- **Bot Credit**: `@MissNullMe`

## ✅ Features
- Check single cards or files with up to 200 cards
- 5 different payment gateways with varying charge amounts
- Automatic posting of approved cards to Telegram group
- Rate limiting (2.5 seconds between cards)
- Gateway selection per user

## 🎯 Available Gateways
1. **Blemart** - $4.99 USD
2. **District People** - €69.00 EUR
3. **Saint Vinson** - $2.00 USD
4. **BGD Fresh** - $6.50 CAD
5. **Staleks** - $0.01 USD (Default/Recommended)

## 📝 Commands

### In Telegram Bot:
- `/start` - Show welcome message and instructions
- `/gate` - Select which gateway to use (1-5)
- `/check /path/to/file.txt` - Check cards from a file
- `/stop` - Stop current checking process

### Usage Examples:
1. **Check single card:**
   ```
   4532123456789012|12|25|123
   ```

2. **Check file:**
   ```
   /check /home/null/Desktop/TestCards.txt
   ```

3. **Upload file:**
   - Simply drag and drop a .txt file to the bot

## 🚀 Running the Bot

### Main Bot (Final Version):
```bash
cd /home/null/Desktop/MadyStripe
python3 mady_final.py
```

### Test Script:
```bash
python3 test_with_proxy.py
```

## 📁 File Structure
```
MadyStripe/
├── mady_final.py          # Main bot (RECOMMENDED)
├── mady_bot_with_proxies.py  # Bot with proxy support
├── test_with_proxy.py     # Test script
├── 100$/100$/
│   ├── Charge1.py         # Blemart gateway
│   ├── Charge2.py         # District People gateway
│   ├── Charge3.py         # Saint Vinson gateway
│   ├── Charge4.py         # BGD Fresh gateway
│   └── Charge5.py         # Staleks gateway
└── README.md              # This file
```

## 🔧 Proxy Configuration
Proxies are loaded from: `/home/null/Documents/usetheseproxies.txt`

Format: `host:port:username:password`

## ⚠️ Important Notes
- The bot processes up to 200 cards per file
- Rate limiting: 2.5 seconds between each card check
- Only approved cards are posted to the group
- Declined cards are shown only in private chat
- HTTP 400 errors usually mean the gateway is blocking - proxies help with this

## 🎮 How to Use

1. **Start the bot:**
   ```bash
   python3 mady_final.py
   ```

2. **In Telegram:**
   - Send `/start` to see instructions
   - Send `/gate` to choose a gateway (recommend 5 for lowest charge)
   - Send `/check /home/null/Desktop/TestCards.txt` to check your cards
   - Or upload a .txt file directly

3. **Results:**
   - ✅ Approved cards → Posted to group `-1003538559040`
   - ❌ Declined cards → Shown only to you
   - Progress updates every 10 cards

## 🛑 Troubleshooting

### Bot not responding:
```bash
# Kill all Python processes
pkill -9 -f "python3"

# Restart the bot
python3 mady_final.py
```

### HTTP 400 errors:
- The gateways are detecting bot traffic
- Proxies are already configured in the bot
- Try using gateway 5 (Staleks) which tends to work best

### Multiple bot instances error:
- Only run one instance at a time
- Use `pkill -9 -f "python3"` to kill all instances first

## 📊 Success Rate
- Gateway 5 (Staleks) - Highest success rate, $0.01 charge
- Gateway 3 (Saint Vinson) - Good success rate, $2.00 charge
- Other gateways may have anti-bot protection

---
**Bot by @MissNullMe**
