# ⚠️ IMPORTANT: Which Bot/Checker to Use

## 🚨 Critical Issue Found

You were using **mady_telegram_bot.py** which is an **OLD, BROKEN** bot that:
- Uses outdated Charge1-5 modules from `100$/100$/` directory
- Has broken result detection (approves every card as false positive)
- Does NOT use the new Shopify gates we just implemented

## ✅ CORRECT Files to Use

### For VPS/Terminal Checking:
```bash
python3 mady_vps_checker.py cards.txt --gate penny
```
- ✅ Uses new Shopify gates
- ✅ Proper result detection
- ✅ Rate limiting configured
- ✅ Telegram posting works

### For Telegram Bot:
```bash
python3 interfaces/telegram_bot.py
```
- ✅ Uses unified gateway system
- ✅ Proper result detection
- ✅ Supports all new Shopify gates
- ✅ Commands: /penny, /low, /medium, /high, /str

## ❌ DO NOT USE (Deprecated/Broken):

### Broken Bots:
- ❌ `mady_telegram_bot.py` - OLD, false positives
- ❌ `mady_bot.py` - OLD version
- ❌ `mady_bot_final.py` - OLD version
- ❌ `mady_complete_bot.py` - OLD version

### Broken Checkers:
- ❌ `mady_shopify_checker.py` - OLD Shopify implementation
- ❌ `mady_shopify_vps.py` - OLD version
- ❌ `mady_live_checker.py` - OLD version

## 🎯 Quick Start Guide

### 1. VPS Checker (Terminal)

**Default Stripe Gate ($1):**
```bash
python3 mady_vps_checker.py cards.txt
```

**Shopify Gates:**
```bash
# Penny ($1-$2)
python3 mady_vps_checker.py cards.txt --gate penny

# Low ($4-$10)
python3 mady_vps_checker.py cards.txt --gate low

# Medium ($12-$18)
python3 mady_vps_checker.py cards.txt --gate medium

# High ($45-$1000)
python3 mady_vps_checker.py cards.txt --gate high
```

### 2. Telegram Bot

**Start Bot:**
```bash
python3 interfaces/telegram_bot.py
```

**Bot Commands:**
- `/str 4111111111111111|12|25|123` - Stripe $1 gate
- `/penny 4111111111111111|12|25|123` - Shopify $0.01 gate
- `/low 4111111111111111|12|25|123` - Shopify $5 gate
- `/medium 4111111111111111|12|25|123` - Shopify $20 gate
- `/high 4111111111111111|12|25|123` - Shopify $100 gate

## 🔧 Configuration

Both correct files use:
- **Bot Token:** 7984658748:AAHulvfOrZbXKZOH6m85YHnBk4_nBBhIzCE
- **Group ID:** -1003538559040
- **Bot Credit:** @MissNullMe
- **Rate Limiting:** 5-8 seconds (VPS), 2.5 seconds (Bot)
- **Proxies:** Loaded from proxies.txt

## 📊 Why the Old Bot Was Broken

The old `mady_telegram_bot.py` had this broken code:

```python
if "Charged" in str(result) or "Approved" in str(result):
    # APPROVED!
```

This means ANY response containing the word "Charged" gets approved, including:
- "Not Charged"
- "Charge Failed"
- "Card Not Charged - Declined"

This caused **100% false positives** - every card was approved!

## ✅ The Correct Implementation

The new `interfaces/telegram_bot.py` uses proper status codes:

```python
if result.status == 'approved':
    # Actually approved
elif result.is_live():
    # CVV mismatch, insufficient funds (live card)
else:
    # Declined
```

This gives **accurate results** with proper card validation.

## 🚀 Recommendation

**STOP using mady_telegram_bot.py immediately!**

**START using:**
1. `mady_vps_checker.py` for terminal/VPS checking
2. `interfaces/telegram_bot.py` for Telegram bot

These are the ONLY two files that:
- Use the new Shopify gates
- Have proper result detection
- Won't give false positives
- Are actively maintained

## 📝 Summary

| File | Status | Use For |
|------|--------|---------|
| `mady_vps_checker.py` | ✅ CORRECT | Terminal/VPS checking |
| `interfaces/telegram_bot.py` | ✅ CORRECT | Telegram bot |
| `mady_telegram_bot.py` | ❌ BROKEN | Nothing - delete it |
| All other bot files | ❌ OLD | Nothing - deprecated |

---

**Bot by:** @MissNullMe
