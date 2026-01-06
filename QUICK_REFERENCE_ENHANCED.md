# MadyStripe Enhanced Bot - Quick Reference Card

## 🚀 Start Bot

```bash
./start_enhanced_bot.sh
```

Or manually:
```bash
python3 interfaces/telegram_bot_enhanced.py
```

---

## 📱 Commands

### Gateway Commands
```
/auth CARD     - AUTH gate (CC Foundation $1)
/charge CARD   - CHARGE gate (Pipeline $1)
/shopify CARD  - SHOPIFY gate (HTTP)
```

### Utility
```
/start  - Welcome message
/help   - Detailed help
/stop   - Stop checking
/stats  - View statistics
```

---

## 💳 Card Format

```
4532123456789012|12|25|123
```

---

## 📁 Mass Checking

### Method 1: Upload File
1. Upload .txt file
2. Click gateway button
3. Get results

### Method 2: Reply to Message
1. Send cards
2. Reply with `/auth` or `/charge` or `/shopify`
3. Get results

---

## 🎯 Gateway Selection

| Gateway | Speed | Accuracy | Use For |
|---------|-------|----------|---------|
| AUTH | ⚡⚡⚡ | ⭐⭐⭐ | Quick screening |
| CHARGE | ⚡⚡ | ⭐⭐⭐⭐⭐ | Final validation |
| SHOPIFY | ⚡ | ⭐⭐⭐ | HTTP-based |

---

## 📊 Result Types

```
✅ APPROVED  - Live card
❌ DECLINED  - Dead card
⚠️ ERROR     - Check failed
```

---

## 🎨 Card Types

```
🔓 2D   - No authentication
🔐 3D   - 3D Secure v1
🛡️ 3DS  - 3D Secure v2
```

---

## 🔧 Troubleshooting

### Bot Not Responding
```bash
ps aux | grep telegram_bot_enhanced
python3 interfaces/telegram_bot_enhanced.py
```

### Check Old Bot
```bash
ps aux | grep telegram_bot.py
kill <PID>
```

---

## 📚 Documentation

- `ENHANCED_BOT_GUIDE.md` - Full guide
- `ENHANCED_BOT_IMPLEMENTATION_COMPLETE.md` - Implementation details
- `start_enhanced_bot.sh` - Startup script

---

## ✅ Quick Tips

1. **For Speed:** Use `/auth`
2. **For Accuracy:** Use `/charge`
3. **For Stealth:** Use `/shopify`
4. **For Mass:** Upload file
5. **For Small:** Reply to message

---

**Bot Version:** 4.0 Enhanced  
**Bot Credit:** @MissNullMe  
**Status:** Production Ready 🚀
