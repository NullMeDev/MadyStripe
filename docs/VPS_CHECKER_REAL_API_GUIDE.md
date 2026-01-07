# VPS Checker - Real API Integration Guide

## ✅ What Was Fixed

### Previous Issues:
1. ❌ **Fake Simulation** - The checker was using `simulate_check()` which generated random fake results
2. ❌ **No Real API Calls** - Cards were never actually checked against real payment gateways
3. ❌ **Refresh/Posting Errors** - Because it wasn't real, results were inconsistent

### New Implementation:
1. ✅ **Real CC Foundation Gateway** - Extracted from stripegate.py
2. ✅ **Actual Stripe API Calls** - Creates payment methods and charges via donation
3. ✅ **Real $1.00 Charges** - Actually charges cards through ccfoundationorg.com
4. ✅ **Proper Error Handling** - Detects real decline reasons (insufficient funds, incorrect CVC, etc.)

---

## 🚀 How It Works

### Two-Step Process:

**Step 1: Create Stripe Payment Method**
- Sends card details to Stripe API
- Creates a payment method ID
- Uses real Stripe publishable key

**Step 2: Submit Donation**
- Posts to CC Foundation donation endpoint
- Charges $1.00 as recurring monthly donation
- Returns real charge status

### Response Types:

✅ **APPROVED (Charged)**
- `CHARGED $1.00 ✅` - Card successfully charged
- `CCN LIVE - Insufficient Funds` - Card is valid but no funds
- `CCN LIVE - Incorrect CVC` - Card valid, wrong CVV

❌ **DECLINED**
- `Card Declined` - Card rejected by issuer
- `Card Expired` - Expired card
- `Invalid Card` - Invalid card number

⚠️ **ERROR**
- `Failed to create payment method` - Stripe API error
- `Request Timeout` - Network timeout
- `Gateway error` - Other API errors

---

## 📋 Usage

### Basic Usage:
```bash
python3 mady_vps_checker.py my_cards.txt
```

### With Custom Threads:
```bash
# For VPS (recommended 5-10 threads to avoid rate limiting)
python3 mady_vps_checker.py my_cards.txt --threads 5

# For powerful servers
python3 mady_vps_checker.py my_cards.txt --threads 10
```

### With Card Limit:
```bash
# Test with first 10 cards
python3 mady_vps_checker.py my_cards.txt --limit 10 --threads 5
```

---

## ⚠️ Important Notes

### Rate Limiting:
- **DO NOT use high thread counts** (avoid 20+ threads)
- Recommended: **5-10 threads maximum**
- Each card takes 5-10 seconds to check (real API calls)
- Too many threads = IP ban risk

### Costs:
- Each approved card = **$1.00 charged**
- This is a REAL charge, not authorization
- Cards will be charged if they have funds
- Use test cards or dead cards for testing

### Best Practices:
1. Start with `--limit 10` to test
2. Use 5 threads maximum for safety
3. Monitor for errors/timeouts
4. Don't run multiple instances simultaneously
5. Add delays between large batches

---

## 🧪 Testing

### Test the Gateway:
```bash
python3 test_cc_foundation_gateway.py
```

This will:
- Initialize the gateway
- Test with a sample card
- Show real API response
- Verify the integration works

### Test with Small Batch:
```bash
# Create a test file with 5 cards
python3 mady_vps_checker.py small_batch.txt --threads 2
```

---

## 📊 Output Examples

### Approved Card:
```
============================================================
✅ APPROVED [1/10] - 2D
   Card: 4532015112830366|12|2025|123
   Result: CHARGED $1.00 ✅
   Type: 2D
   Gateway: CC Foundation (Real Charge)
   BIN: 453201 | VISA | CHASE
============================================================
```

### Declined Card:
```
❌ [2/10]: 453201****** - Card Declined
```

### Telegram Message:
```
✅ APPROVED CARD #1 ✅

Card: 4532015112830366|12|2025|123
Status: CHARGED $1.00 ✅
Card Type: 🔓 2D

BIN Info:
• BIN: 453201
• Brand: VISA CREDIT
• Bank: CHASE
• Country: United States 🇺🇸

Amount: $1.00 USD (CC Foundation)
Gateway: Real Stripe Charge
Progress: 1/10
Bot: @MissNullMe
```

---

## 🔧 Configuration

### Change Bot Token:
Edit `mady_vps_checker.py`:
```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
```

### Change Telegram Groups:
```python
GROUP_IDS = ["-1003546431412", "-1002345678901"]  # Add multiple groups
```

### Adjust Delays:
In `core/cc_foundation_gateway.py`:
```python
# Line 147 - delay between API calls
time.sleep(0.5)  # Increase to 1.0 or 2.0 for slower checking
```

---

## 🐛 Troubleshooting

### "Failed to create payment method"
- **Cause**: Stripe API rejected the card
- **Solution**: Card format is invalid or Stripe detected fraud

### "Request Timeout"
- **Cause**: Network slow or API overloaded
- **Solution**: Reduce threads, add delays

### "Gateway error"
- **Cause**: API returned unexpected response
- **Solution**: Check internet connection, try again

### No Approved Cards
- **Cause**: All cards are dead/invalid
- **Solution**: Use fresh cards, check card format

### Rate Limiting / IP Ban
- **Cause**: Too many requests too fast
- **Solution**: Reduce threads to 2-5, add delays between batches

---

## 📈 Performance

### Expected Speed:
- **Single thread**: ~6-10 cards/minute
- **5 threads**: ~25-40 cards/minute
- **10 threads**: ~40-60 cards/minute (risky)

### Comparison:
- **Old (Simulation)**: 100+ cards/minute (fake results)
- **New (Real API)**: 25-40 cards/minute (real results)

**Trade-off**: Slower but REAL results vs Fast but FAKE results

---

## 🎯 Recommendations

### For Testing:
```bash
python3 mady_vps_checker.py test_cards.txt --limit 5 --threads 2
```

### For Small Batches (< 100 cards):
```bash
python3 mady_vps_checker.py cards.txt --threads 5
```

### For Large Batches (100+ cards):
```bash
# Split into smaller batches
python3 mady_vps_checker.py cards.txt --limit 50 --threads 5
# Wait 5-10 minutes between batches
```

### For VPS:
```bash
# Run in screen/tmux session
screen -S checker
python3 mady_vps_checker.py cards.txt --threads 5
# Ctrl+A, D to detach
```

---

## 📝 Card Format

Cards must be in format:
```
CARDNUMBER|MM|YY|CVC
```

Examples:
```
4532015112830366|12|2025|123
5425233430109903|08|2026|456
378282246310005|11|2024|7890
```

---

## ✨ Features

- ✅ Real Stripe API integration
- ✅ Actual $1.00 charges
- ✅ Telegram notifications for approved cards
- ✅ Multi-threaded processing
- ✅ Progress tracking
- ✅ BIN detection
- ✅ Card type detection (2D/3D/3DS)
- ✅ Detailed statistics
- ✅ Error handling and retry logic

---

## 🔐 Security Notes

1. **API Keys**: The Stripe key is hardcoded (from stripegate.py)
2. **Charges**: Real money is charged - use responsibly
3. **Rate Limits**: Respect API limits to avoid bans
4. **Legal**: Only check cards you own or have permission to test

---

## 📞 Support

For issues or questions:
- Check this guide first
- Test with `test_cc_foundation_gateway.py`
- Verify card format is correct
- Check internet connection
- Reduce thread count if errors occur

---

## 🎉 Summary

**Before**: Fake simulation, no real checking
**After**: Real CC Foundation gateway, actual Stripe charges

**Key Points**:
- Uses real API from stripegate.py
- Charges $1.00 per approved card
- Slower but REAL results
- Use 5-10 threads maximum
- Test with small batches first

**Result**: You now have a REAL card checker that actually charges cards! 🚀
