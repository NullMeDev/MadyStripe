# 🤖 MADY BOT - Complete Setup Guide

## 📋 Overview

MADY is a Telegram bot with **TWO** card checking methods:
1. **Stripe Checker** - Fast API-based checking (1-3 sec/card)
2. **Shopify Payments Checker** - HTTP-based CHARGED mode (2-5 sec/card)

---

## 🚀 Quick Start

### 1. Update Bot Token (if needed)

Edit `mady_config.json`:
```json
{
    "bot_token": "7984658748:AAFLNS52swKHJkh4kWuu3LDgckslaZjyJTY",
    "group_id": "-1003538559040",
    "bot_credit": "@MissNullMe"
}
```

### 2. Start the Bot

```bash
cd /home/null/Desktop/MadyStripe
python3 mady_bot_final.py
```

**Note:** Only ONE bot instance can run at a time. If you get error 409, stop other instances first.

---

## 📱 Bot Commands

### 🔷 Stripe Checker Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Show help message | `/start` |
| `/stripe <card>` | Check single card | `/stripe 4242424242424242\|12\|25\|123` |
| `/gateway <1-5>` | Select gateway | `/gateway 3` |
| `/gates` | Show all gateways | `/gates` |
| `/stats` | Show bot status | `/stats` |

### 🟢 Shopify Payments Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/setstore <url>` | Set Shopify store | `/setstore https://example.myshopify.com` |
| `/shopify <card>` | Check single card | `/shopify 4242424242424242\|12\|25\|123` |

### 📁 File Checking

1. Upload a `.txt` file with cards (one per line)
2. Bot will ask: "Select checker:"
3. Choose **Stripe** or **Shopify**
4. Bot processes up to 200 cards

---

## 🔧 Available Gateways

### Stripe Gateways (API-based)

| ID | Gateway | Amount | Speed |
|----|---------|--------|-------|
| 1 | Blemart | $4.99 | ~2 sec |
| 2 | District People | €69.00 | ~2 sec |
| 3 | Saint Vinson | $20.00 | ~2 sec |
| 4 | BGD Fresh | $6.50 | ~3 sec |
| 5 | Staleks Florida | $0.01 | ~1 sec |

**Default:** Gateway 3 (Saint Vinson)

### Shopify Payments (HTTP-based)

- **Mode:** CHARGED (real charges attempted)
- **Speed:** ~2-5 seconds per card
- **Requirements:** Valid Shopify store URL with products
- **Method:** Direct HTTP requests (no browser needed)

---

## 📝 Card Format

All cards must be in this format:
```
CARD|MM|YY|CVV
```

**Examples:**
```
4242424242424242|12|25|123
5555555555554444|06|27|456
378282246310005|12|25|1234
```

---

## 🎯 Response Codes

### ✅ Approved Responses
- `CHARGED` - Card was charged successfully
- `CVV_MISMATCH` - Card valid, wrong CVV
- `INSUFFICIENT_FUNDS` - Card valid, no funds
- `3DS_REQUIRED` - Card valid, needs 3D Secure

### ❌ Declined Responses
- `DECLINED` - Card declined
- `EXPIRED_CARD` - Card expired
- `INVALID_CARD` - Invalid card number
- `FRAUD` - Fraud detected

### ⚠️ Error Responses
- `Error: ...` - Technical error occurred

---

## 📊 Usage Examples

### Example 1: Check Single Card with Stripe

```
User: /stripe 4242424242424242|12|25|123

Bot: ⏳ Checking card with Stripe...

Bot: ✅ CHARGED
━━━━━━━━━━━━━━━━
💳 Card: 4242424242424242|12|25|123
🔍 Checker: Stripe
🚪 Gateway: Saint Vinson
📝 Response: Charged
━━━━━━━━━━━━━━━━
🤖 Bot: @MissNullMe
```

### Example 2: Check Single Card with Shopify

```
User: /setstore https://example-store.myshopify.com

Bot: ✅ Shopify store set to:
https://example-store.myshopify.com

User: /shopify 4242424242424242|12|25|123

Bot: ⏳ Checking card with Shopify Payments (CHARGED MODE)...
🏪 Store: https://example-store.myshopify.com...

Bot: ✅ CHARGED
━━━━━━━━━━━━━━━━
💳 Card: 4242424242424242|12|25|123
🔍 Checker: Shopify Payments
🚪 Gateway: https://example-store.myshopify...
📝 Response: CHARGED
━━━━━━━━━━━━━━━━
🤖 Bot: @MissNullMe
```

### Example 3: Check File with Multiple Cards

```
User: [Uploads cards.txt with 50 cards]

Bot: 📁 Found 50 cards

Select checker:
[Stripe] [Shopify]

User: [Clicks "Stripe"]

Bot: ⏳ Checking 50 cards with Stripe...

Progress: 50/50
✅ 12 | ❌ 35 | ⚠️ 3

Bot: 📊 CHECK COMPLETE
━━━━━━━━━━━━━━━━━━━━━━
🔍 Checker: Stripe
📁 Total: 50
✅ Approved: 12
❌ Declined: 35
⚠️ Errors: 3
━━━━━━━━━━━━━━━━━━━━━━

✅ APPROVED CARDS:
4242424242424242|12|25|123
→ CHARGED

5555555555554444|06|27|456
→ CVV_MISMATCH

[... more cards ...]

🤖 Bot by @MissNullMe
```

---

## 🔄 Switching Between Checkers

### When to Use Stripe Checker
- ✅ Fast checking needed (1-3 sec/card)
- ✅ Testing against Stripe merchants
- ✅ Multiple gateways available
- ✅ No store URL needed

### When to Use Shopify Payments Checker
- ✅ Testing Shopify stores specifically
- ✅ Store uses Shopify Payments (not Stripe)
- ✅ Need CHARGED mode testing
- ✅ Have valid Shopify store URL

---

## 🛠️ Troubleshooting

### Error 401: Unauthorized
**Problem:** Bot token is invalid
**Solution:** Update token in `mady_config.json`

### Error 409: Conflict
**Problem:** Another bot instance is running
**Solution:** Stop other instances with `pkill -f mady_bot_final.py`

### No Shopify store set
**Problem:** Trying to use `/shopify` without setting store
**Solution:** Use `/setstore <url>` first

### Gateway not available
**Problem:** Selected gateway failed to import
**Solution:** Check gateway file exists in `100$/100$/` directory

---

## 📂 File Structure

```
MadyStripe/
├── mady_bot_final.py              # Main bot file
├── mady_config.json               # Bot configuration
├── 100$/100$/
│   ├── Charge1.py                 # Blemart gateway
│   ├── Charge2.py                 # District People gateway
│   ├── Charge3.py                 # Saint Vinson gateway
│   ├── Charge4.py                 # BGD Fresh gateway
│   ├── Charge5.py                 # Staleks Florida gateway
│   └── Charge10_ShopifyPayments.py # Shopify Payments checker
└── /home/null/Desktop/TestCards.txt # Test cards file
```

---

## 🔐 Security Notes

- Bot token is stored in `mady_config.json`
- Never share your bot token publicly
- Cards are processed in memory only
- No card data is stored permanently
- All checks are done via HTTPS

---

## 📈 Performance

### Stripe Checker
- **Speed:** 1-3 seconds per card
- **Parallel:** No (sequential checking)
- **Rate Limit:** Depends on gateway
- **Success Rate:** ~60-80% (depends on cards)

### Shopify Payments Checker
- **Speed:** 2-5 seconds per card
- **Parallel:** No (sequential checking)
- **Rate Limit:** Depends on store
- **Success Rate:** ~50-70% (depends on store & cards)

---

## 🆘 Support

For issues or questions:
- Check this guide first
- Review error messages carefully
- Ensure all files are in correct locations
- Verify bot token is valid
- Make sure only one bot instance is running

---

## 📝 Notes

1. **CHARGED MODE:** Shopify checker attempts real charges
2. **Test Cards:** Use `/home/null/Desktop/TestCards.txt` for testing
3. **File Limit:** Maximum 200 cards per file upload
4. **Store URL:** Must be a valid Shopify store with products
5. **Gateway Selection:** Persists per user session

---

## 🎉 Quick Reference

**Start Bot:**
```bash
python3 mady_bot_final.py
```

**Stop Bot:**
```bash
Ctrl+C or pkill -f mady_bot_final.py
```

**Check Single Card:**
```
/stripe 4242424242424242|12|25|123
```

**Set Shopify Store:**
```
/setstore https://example-store.myshopify.com
```

**Check with Shopify:**
```
/shopify 4242424242424242|12|25|123
```

---

**Bot Credit:** @MissNullMe
**Version:** 1.0 (CHARGED MODE)
**Last Updated:** 2026-01-02
