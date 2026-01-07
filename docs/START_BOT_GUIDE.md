# HOW TO START THE TELEGRAM BOT - FIXED VERSION

## ✅ The CORRECT Bot File

**Use:** `interfaces/telegram_bot.py` (FALSE POSITIVES FIXED)

## 🚀 How to Start the Bot

### Method 1: Using Python3 (RECOMMENDED)

```bash
cd /home/null/Desktop/MadyStripe
python3 interfaces/telegram_bot.py
```

### Method 2: Direct Execution

```bash
cd /home/null/Desktop/MadyStripe
./interfaces/telegram_bot.py
```

**Note:** If you get "Permission denied", run:
```bash
chmod +x interfaces/telegram_bot.py
```

### Method 3: Using nohup (Background Process)

```bash
cd /home/null/Desktop/MadyStripe
nohup python3 interfaces/telegram_bot.py > bot.log 2>&1 &
```

To check if it's running:
```bash
ps aux | grep telegram_bot
```

To stop it:
```bash
pkill -f telegram_bot.py
```

## ⚠️ Common Issues

### Issue 1: "Permission denied"

**Problem:** File doesn't have execute permissions

**Solution:**
```bash
chmod +x interfaces/telegram_bot.py
```

### Issue 2: "Command not found" with sudo

**Problem:** `sudo` doesn't know where `python3` is, or you're trying to run the file directly

**Solution:** Don't use `sudo`. Use one of these instead:
```bash
# Option A: Use python3 directly (BEST)
python3 interfaces/telegram_bot.py

# Option B: Use full path to python3
/usr/bin/python3 interfaces/telegram_bot.py

# Option C: If you MUST use sudo (not recommended)
sudo /usr/bin/python3 interfaces/telegram_bot.py
```

### Issue 3: "ModuleNotFoundError"

**Problem:** Missing dependencies

**Solution:**
```bash
pip3 install telebot requests
```

### Issue 4: Bot starts but doesn't respond

**Problem:** Wrong bot token or network issues

**Solution:**
1. Check bot token in the file (line ~20)
2. Test internet connection
3. Check Telegram API is accessible

## 📋 Verification

After starting the bot, you should see:
```
Bot started successfully!
Listening for commands...
```

Then test in Telegram:
```
/start
```

You should get a welcome message with all available commands.

## 🎯 Available Commands

Once the bot is running, use these commands in Telegram:

```
/str 4111111111111111|12|25|123     - Stripe $1 gate
/penny 4111111111111111|12|25|123   - Shopify $0.01 gate
/low 4111111111111111|12|25|123     - Shopify $5 gate
/medium 4111111111111111|12|25|123  - Shopify $20 gate
/high 4111111111111111|12|25|123    - Shopify $100 gate
```

## ✅ What's Fixed

1. **False Positives:** ONLY `status == 'approved'` cards are posted to groups
2. **Commands:** Removed confusing aliases (/001, /5, /20, /100)
3. **Permissions:** File now has execute permissions
4. **All Denominations:** Fix applies to ALL gates (Stripe, Penny, Low, Medium, High)

## 🔍 Testing the Fix

To verify false positives are fixed:

```bash
# Run the test script
python3 test_bot_fixes.py
```

You should see:
```
🎉 ALL TESTS PASSED! False positives fix is working correctly!
```

## ❌ DON'T Use These Files

These files have the false positive bug and have been moved to `deprecated_old_versions/`:

- ❌ `mady_telegram_bot.py`
- ❌ `mady_bot.py`
- ❌ `mady_bot_final.py`
- ❌ `mady_complete_bot.py`
- ❌ All other `mady_*.py` bot files

## 📊 What Gets Posted to Groups

- ✅ **ONLY** cards with `status == 'approved'`
- ❌ Declined cards (shown only to you)
- ❌ Error cards (shown only to you)

## 🆘 Still Having Issues?

1. **Check Python version:**
   ```bash
   python3 --version
   ```
   Should be Python 3.7 or higher

2. **Check file exists:**
   ```bash
   ls -la interfaces/telegram_bot.py
   ```
   Should show: `-rwxrwxr-x` (with execute permission)

3. **Check dependencies:**
   ```bash
   python3 -c "import telebot; import requests; print('Dependencies OK')"
   ```

4. **View bot logs:**
   ```bash
   tail -f bot.log
   ```

## 🎉 Success!

If the bot starts successfully, you'll see:
- Bot responds to `/start` command
- Commands work correctly
- ONLY approved cards are posted to groups
- No false positives!

---

**Bot by:** @MissNullMe  
**Status:** ✅ FALSE POSITIVES FIXED  
**Date:** January 4, 2026
