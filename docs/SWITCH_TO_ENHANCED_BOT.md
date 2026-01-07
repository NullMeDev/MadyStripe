# Switch from Mady2.0 (AutoshBot) to Enhanced Bot

## 🔄 Quick Switch Guide

### Step 1: Stop Old Bot (Mady2.0)

```bash
# Find the running bot process
ps aux | grep "bot.py\|telegram_bot.py" | grep -v grep

# Kill the old bot (replace <PID> with actual process ID)
kill <PID>

# Or kill all Python bots
pkill -f "bot.py"
pkill -f "telegram_bot.py"
```

### Step 2: Start Enhanced Bot

```bash
# Make sure you're in the MadyStripe directory
cd /home/null/Desktop/MadyStripe

# Start the Enhanced Bot
./start_enhanced_bot.sh

# Or manually:
python3 interfaces/telegram_bot_enhanced.py
```

### Step 3: Test on Telegram

```
/start
```

You should see:
```
🤖 MadyStripe Enhanced v4.0

🎯 STRIPE GATES (Fast & Reliable):
/auth - 🔐 AUTH Gate (CC Foundation $1)
/charge - 💰 CHARGE Gate (Pipeline $1)

🛍️ SHOPIFY GATE (HTTP/GraphQL):
/shopify - Dynamic store finder

Bot by: @MissNullMe
```

### Step 4: Load Shopify Stores

```
/addsh
```

You should see:
```
✅ Shopify Stores Loaded!

Loaded: 45 stores
Source: working_shopify_stores.txt

Sample stores:
1. santamonica.myshopify.com
2. pepper-spray-store.myshopify.com
...
```

### Step 5: Check Cards

```
/shopify 4748443210075173|2|28|983
```

---

## 📊 Command Comparison

### Old Bot (Mady2.0 / AutoshBot)
```
/sh - Check cards
/addsh - Add store
/listsh - List stores
/addproxy - Add proxy
/listproxy - List proxies
```

### New Bot (Enhanced)
```
/auth - AUTH gate (CC Foundation)
/charge - CHARGE gate (Pipeline)
/shopify - Shopify gate
/addsh - Load 45 stores
/stats - View statistics
```

---

## ✅ Benefits of Enhanced Bot

1. **Multiple Gateways**
   - AUTH (CC Foundation) - Fast
   - CHARGE (Pipeline) - Accurate
   - SHOPIFY (HTTP) - Stealth

2. **Auto-Load Stores**
   - `/addsh` loads all 45 stores instantly
   - No manual addition needed

3. **File Reply Feature**
   - Upload file → Get results as reply
   - Better organization

4. **Better Detection**
   - Strict error detection
   - No false positives
   - Live card type detection (2D/3D/3DS)

---

## 🔧 Troubleshooting

### Bot Not Responding?

```bash
# Check if bot is running
ps aux | grep telegram_bot_enhanced

# Check logs
tail -f bot_output.log

# Restart bot
./start_enhanced_bot.sh
```

### Wrong Bot Running?

```bash
# Kill all bots
pkill -f "bot.py"
pkill -f "telegram_bot"

# Start Enhanced Bot
./start_enhanced_bot.sh
```

### Can't Find start_enhanced_bot.sh?

```bash
# Make it executable
chmod +x start_enhanced_bot.sh

# Or run directly
python3 interfaces/telegram_bot_enhanced.py
```

---

## 📝 Quick Test Workflow

```bash
# 1. Stop old bot
pkill -f "bot.py"

# 2. Start Enhanced Bot
./start_enhanced_bot.sh

# 3. On Telegram:
/start
/addsh
/shopify 4748443210075173|2|28|983
```

---

**Ready to switch!** 🚀
