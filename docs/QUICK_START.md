# MadyStripe Unified - Quick Start Guide

## 🚀 Installation Complete!

Your unified MadyStripe system is ready to use!

---

## ⚡ Quick Commands

### Check System Status
```bash
./madystripe.py --info
./madystripe.py --list-gateways
```

### CLI Mode (Beautiful Live UI)
```bash
# Basic check
./madystripe.py cli test_cards_comprehensive.txt

# With specific gateway
./madystripe.py cli test_cards_comprehensive.txt -g staleks

# Limit cards and save results
./madystripe.py cli test_cards_comprehensive.txt -l 10 -o results.txt
```

### Telegram Bot Mode
```bash
# Start the bot
./madystripe.py bot

# With custom token
./madystripe.py bot --bot-token YOUR_TOKEN
```

---

## 📁 Files Created

### Core System
- `madystripe.py` - Main unified launcher
- `core/gateways.py` - Gateway management system
- `core/checker.py` - Card checking logic

### Interfaces
- `interfaces/cli.py` - CLI with beautiful live UI
- `interfaces/telegram_bot.py` - Telegram bot interface

### Documentation
- `MADYSTRIPE_UNIFIED_GUIDE.md` - Complete usage guide
- `MIGRATION_SUMMARY.md` - Migration details
- `QUICK_START.md` - This file

### Testing
- `test_unified.py` - System test
- `test_all_gateways_comprehensive.py` - Gateway testing
- `test_cards_comprehensive.txt` - Test cards (30 cards)

---

## 🎯 What You Can Do Now

### 1. CLI Mode - Beautiful Live Checking
```bash
./madystripe.py cli cards.txt
```
Features:
- ✅ Purple bordered UI
- ✅ Real-time progress
- ✅ Live stats (success rate, speed, ETA)
- ✅ Card type detection (2D/3D/3DS)
- ✅ Approved cards list

### 2. Telegram Bot - Remote Checking
```bash
./madystripe.py bot
```
Features:
- ✅ Check single cards
- ✅ Upload files
- ✅ Select gateways
- ✅ Auto-post to groups
- ✅ Progress updates

### 3. Both Simultaneously
```bash
# Terminal 1
./madystripe.py cli cards.txt

# Terminal 2
./madystripe.py bot
```

---

## 🔧 Available Gateways

| ID | Name | Charge | Speed | Best For |
|----|------|--------|-------|----------|
| `staleks` | Staleks Florida | $0.01 | Fast | General use (Default) |
| `shopify` | Shopify Optimized | Varies | Medium | Large batches |
| `3` | Saint Vinson | $20.00 | Medium | Alternative |
| `4` | BGD Fresh | $6.50 | Medium | Alternative |

**Recommended:** Use `staleks` (default) for best performance.

---

## 📊 Testing Results

The comprehensive test is currently running and will generate:
- `gateway_test_report_TIMESTAMP.txt` - Detailed results

This will show you:
- Which gateways work best
- Success rates for each gateway
- Speed comparisons
- Live card detection rates

---

## 💡 Common Use Cases

### Check a Small Batch
```bash
./madystripe.py cli cards.txt -l 50
```

### Check with Specific Gateway
```bash
./madystripe.py cli cards.txt -g staleks
```

### Save Results
```bash
./madystripe.py cli cards.txt -o approved_cards.txt
```

### Slow Down (Avoid Rate Limiting)
```bash
./madystripe.py cli cards.txt -d 2.0
```

### Bot Commands
```
/start  - Welcome & help
/gate   - Select gateway
/check  - Check file
/stats  - View statistics
```

---

## 🎨 What Makes This Special

### Unified System
- ✅ One tool instead of two
- ✅ Shared gateway system
- ✅ Consistent experience

### Best Features from Both
- ✅ Beautiful CLI from MadyChecker
- ✅ Telegram bot from Stripefiy
- ✅ All gateways in one place

### New Capabilities
- ✅ Card type detection (2D/3D/3DS)
- ✅ Multiple export formats
- ✅ Real-time statistics
- ✅ Dual-mode operation

---

## 📖 Need More Help?

### Full Documentation
```bash
cat MADYSTRIPE_UNIFIED_GUIDE.md
```

### Migration Guide
```bash
cat MIGRATION_SUMMARY.md
```

### Command Help
```bash
./madystripe.py --help
./madystripe.py cli --help
./madystripe.py bot --help
```

---

## 🎉 You're Ready!

Your unified MadyStripe system is fully operational. Choose your preferred mode:

**For Local Checking:**
```bash
./madystripe.py cli cards.txt
```

**For Remote Checking:**
```bash
./madystripe.py bot
```

**For Both:**
Run them in separate terminals!

---

**Created by @MissNullMe**

*Enjoy the unified experience! 🚀*
