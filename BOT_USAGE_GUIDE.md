# 🤖 MADY TELEGRAM BOT - COMPLETE USAGE GUIDE

## ✅ Bot Features
- **Batch Processing**: Check 200+ cards at once
- **Multiple Gateways**: 5 different payment gateways
- **Slash Commands**: Easy-to-use interface
- **Auto-posting**: Approved cards sent to 3 groups
- **Real-time Progress**: Live updates during checking
- **File Upload**: Direct text file support

## 🚀 Quick Start

### 1. Start the Bot
```bash
cd /home/null/Desktop/MadyStripe
python3 mady_telegram_bot.py
```

### 2. Open Telegram
Search for your bot using the token:
- Bot Token: `7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s`
- Or search: `@MadyCheckerBot` (if username is set)

### 3. Send Commands

## 📝 Commands

### `/start`
- Shows welcome message
- Lists all available commands
- Displays bot features

### `/check`
- Starts card checking process
- Bot will ask for text file
- Upload file with cards (format: NUMBER|MM|YY|CVC)
- Select gateway when prompted

### `/gateway`
- Shows list of available gateways
- Displays charge amounts
- Select gateway for information

### `/stop`
- Stops current checking process
- Use if you need to cancel batch

### `/status`
- Shows bot status
- Lists available gateways
- Shows if check is running

### `/help`
- Shows detailed help
- Card format examples
- Tips and tricks

## 📁 File Format

Create a text file with cards in this format:
```
5566258985615466|12|25|299
4304450802433666|12|25|956
5587170478868301|12|25|286
```

- One card per line
- Format: `NUMBER|MM|YY|CVC`
- No spaces or extra characters
- Save as `.txt` file

## 🎯 Gateway Selection

When prompted, choose gateway by number:

1. **Blemart** - $4.99 USD
2. **District People** - €69.00 EUR  
3. **Saint Vinson** - $20.00 USD
4. **BGD Fresh** - $6.50 CAD
5. **CC Foundation** - $1.00 USD (Fastest)

## 💬 Usage Examples

### Example 1: Check 5 Cards
1. Send `/check`
2. Upload `test_cards.txt` with 5 cards
3. Select gateway `5` (fastest)
4. Wait for results

### Example 2: Check Full List
1. Send `/check`
2. Upload `/home/null/Desktop/TestCards.txt`
3. Select gateway based on success rate
4. Bot processes all cards
5. Approved cards posted to groups

### Example 3: Quick Single Card
Just send the card directly:
```
5566258985615466|12|25|299
```
Bot will check using default gateway (5)

## 📊 Understanding Results

### Success Messages:
- ✅ **APPROVED** - Card charged successfully
- 💰 **Insufficient Funds** - Valid card, no money
- 📅 **Expired** - Card expired

### Failure Messages:
- ❌ **Declined** - Card rejected
- ❌ **Invalid Card** - Wrong number/CVC
- ⚠️ **Error** - Gateway or network issue

## 🔧 Troubleshooting

### Bot Not Responding:
```bash
# Restart bot
pkill -f mady_telegram_bot.py
python3 mady_telegram_bot.py
```

### Gateway Errors:
- Try different gateway
- Check internet connection
- Wait 5 minutes (rate limit)

### No Approvals:
- Normal approval rate: 3-5%
- Try Gateway 5 (most reliable)
- Check card format

## ⚙️ Advanced Settings

### Modify Bot Settings:
Edit `mady_telegram_bot.py`:
```python
BOT_TOKEN = "your_token"
GROUP_IDS = ["group1", "group2"]
```

### Add Custom Gateway:
```python
from CustomCharge import CustomCheckout
gateways[6] = {
    "func": CustomCheckout,
    "name": "Custom Gateway",
    "amount": "$X.XX"
}
```

## 📈 Performance Tips

1. **Best Gateway**: Use Gateway 5 for speed
2. **Batch Size**: 50-100 cards optimal
3. **Timing**: 2-3 second delays prevent blocks
4. **Groups**: Approved cards auto-post to all groups

## 🛡️ Security Notes

- Bot only processes card format
- No card data stored
- Results sent only to configured groups
- Use VPN/proxy if blocked

## 📞 Support

**Bot by:** @MissNullMe

### Common Issues:

**Q: Bot says "No gateways available"**
A: Check that Charge files are in `100$/100$/` folder

**Q: All cards declining?**
A: Gateway may be down, try another

**Q: How to check specific amount of cards?**
A: Create new text file with desired cards only

**Q: Can I use proxies?**
A: Not in this version, use `mady_batch_checker.py` for proxy support

## 🎮 Quick Test

Test with single card:
```
4242424242424242|12|25|123
```

Test with file:
```bash
echo "5566258985615466|12|25|299" > test.txt
# Upload test.txt to bot
```

## ✅ Ready to Use!

The bot is now running and ready to:
- Check your card files
- Process batches up to 200+ cards
- Post approvals to Telegram groups
- Provide real-time progress updates

**Start with:** `/start` in Telegram

---

**Enjoy using MADY Bot!** 🚀
