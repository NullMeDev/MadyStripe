# MadyStripe Unified v3.0 - Complete Guide

## 🎯 Overview

**MadyStripe Unified** is the ultimate card checking tool that combines the best features of both MadyChecker and Stripefiy into one powerful, unified system.

### ✨ Key Features

- 🚀 **Multiple Advanced Gateways** - Staleks, Shopify Optimized, and more
- 🎨 **Beautiful CLI Interface** - Live updating UI with purple borders and real-time stats
- 🤖 **Telegram Bot Integration** - Check cards remotely via Telegram
- 🔍 **Card Type Detection** - Automatically detects 2D/3D/3DS cards
- 📊 **Real-time Statistics** - Success rates, speed, ETA, and more
- 💾 **Result Export** - Save results in TXT, JSON, or CSV format
- ⚡ **Batch Processing** - Check hundreds of cards efficiently
- 🔄 **Dual Mode Operation** - Run CLI and bot simultaneously

---

## 📦 Installation

### Prerequisites

```bash
# Python 3.7 or higher required
python3 --version

# Install dependencies
pip install requests pyTelegramBotAPI
```

### Quick Start

```bash
cd /home/null/Desktop/MadyStripe
chmod +x madystripe.py
./madystripe.py --info
```

---

## 🎮 Usage

### 1. CLI Mode (Beautiful Live UI)

The CLI mode provides a beautiful, live-updating interface similar to the original MadyChecker.

#### Basic Usage

```bash
# Check cards with default gateway (Staleks - fastest)
./madystripe.py cli cards.txt

# Use specific gateway
./madystripe.py cli cards.txt -g staleks

# Limit to 100 cards
./madystripe.py cli cards.txt -l 100

# Custom delay (1 second between checks)
./madystripe.py cli cards.txt -d 1.0

# Save results to file
./madystripe.py cli cards.txt -o results.txt
```

#### CLI Features

- ✅ **Live Stats Box** - Real-time progress, success rate, speed
- 🎨 **Purple Borders** - Beautiful terminal UI
- 📊 **Progress Bar** - Visual progress indicator
- 🔴 **Live Cards List** - Shows approved cards as they're found
- ⚡ **Speed Metrics** - Cards per second, ETA
- 🎯 **Card Type Display** - Shows 2D/3D/3DS with emojis

#### Example Output

```
╔══════════════════════════════════════════════════════════════════╗
║  MADYSTRIPE UNIFIED v3.0                 @MissNullMe            ║
╚══════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════╗
║ LIVE STATS                                                       ║
╠══════════════════════════════════════════════════════════════════╣
║ Card: 4532123456789012|12|25|123                                ║
║ Result: ✅ Charged $0.01                                         ║
║ Type: 🔓 2D | Gateway: Staleks Florida                          ║
╠══════════════════════════════════════════════════════════════════╣
║ Progress: 45/100 (45.0%)                                         ║
║ ██████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░              ║
╠══════════════════════════════════════════════════════════════════╣
║ ✓ 12  ✗ 30  CVV 2  Insuf 1  Err 0                              ║
╠══════════════════════════════════════════════════════════════════╣
║ Success: 26.7%  Live: 33.3%  Speed:  2.00 c/s                  ║
║ Elapsed: 00:22  ETA: 00:27                                      ║
╚══════════════════════════════════════════════════════════════════╝
```

---

### 2. Telegram Bot Mode

Run the Telegram bot for remote card checking.

#### Basic Usage

```bash
# Run with default configuration
./madystripe.py bot

# Custom bot token
./madystripe.py bot --bot-token YOUR_TOKEN

# Custom group IDs
./madystripe.py bot --group-ids "-1001234567890,-1009876543210"
```

#### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show welcome message and instructions |
| `/gate` | Select which gateway to use |
| `/check /path/to/file.txt` | Check cards from file |
| `/stop` | Stop current checking process |
| `/stats` | View gateway statistics |
| `/help` | Show detailed help |

#### Bot Features

- 📱 **Single Card Checking** - Send card directly: `4532123456789012|12|25|123`
- 📁 **File Upload** - Drag and drop .txt files
- 📊 **Progress Updates** - Real-time updates every 10 cards
- 🎯 **Card Type Detection** - Shows 2D/3D/3DS with emojis
- 📢 **Auto Group Posting** - Approved cards posted to groups
- 🔐 **Private Results** - Declined cards shown only to you

#### Example Bot Interaction

```
User: /start
Bot: 🤖 Welcome to MadyStripe Unified v3.0!
     Available Gateways:
     1. Staleks Florida - $0.01
     2. Shopify Optimized - Varies
     ...

User: 4532123456789012|12|25|123
Bot: ⏳ Checking with Staleks Florida...
     ✅ APPROVED!
     Card: 4532123456789012|12|25|123
     Gateway: Staleks Florida
     Response: Charged $0.01
     Card Type: 🔓 2D
```

---

## 🔧 Available Gateways

### List Gateways

```bash
./madystripe.py --list-gateways
```

### Gateway Details

| ID | Name | Charge | Speed | Description |
|----|------|--------|-------|-------------|
| `staleks` | Staleks Florida | $0.01 | Fast | CC Foundation - Fastest, lowest charge |
| `shopify` | Shopify Optimized | Varies | Medium | 15000+ Shopify stores with Stripe |
| `3` | Saint Vinson | $20.00 | Medium | Legacy gateway |
| `4` | BGD Fresh | $6.50 | Medium | Legacy gateway |

### Recommended Gateway

**Staleks Florida** (`staleks` or `1`) is recommended for:
- ✅ Fastest checking speed
- ✅ Lowest charge amount ($0.01)
- ✅ High success rate
- ✅ Reliable performance

---

## 📊 Understanding Results

### Card Statuses

| Status | Emoji | Meaning |
|--------|-------|---------|
| **Approved** | ✅ | Card successfully charged |
| **CVV Mismatch** | 🔐 | Card is live but CVV incorrect |
| **Insufficient Funds** | 💰 | Card is live but no funds |
| **Declined** | ❌ | Card declined by bank |
| **Error** | ⚠️ | Technical error occurred |

### Card Types

| Type | Emoji | Description |
|------|-------|-------------|
| **2D** | 🔓 | No authentication required |
| **3D** | 🔐 | 3D Secure v1 authentication |
| **3DS** | 🛡️ | 3D Secure v2 authentication |

### Success Metrics

- **Success Rate** - Percentage of approved cards
- **Live Rate** - Percentage of live cards (approved + CVV + insufficient)
- **Speed** - Cards checked per second
- **ETA** - Estimated time remaining

---

## 📁 File Formats

### Input File Format

Cards should be in the format: `NUMBER|MM|YY|CVC`

```
4532123456789012|12|25|123
5566258985615466|01|26|456
4304450802433666|03|27|789
```

### Output Formats

#### TXT Format (Default)
```
4532123456789012|12|25|123 | APPROVED | Charged $0.01 | 2D | Staleks Florida
5566258985615466|01|26|456 | DECLINED | Card declined | 2D | Staleks Florida
```

#### JSON Format
```json
[
  {
    "card": "4532123456789012|12|25|123",
    "status": "approved",
    "message": "Charged $0.01",
    "card_type": "2D",
    "gateway": "Staleks Florida",
    "timestamp": 1704123456.789
  }
]
```

#### CSV Format
```csv
Card,Status,Message,CardType,Gateway,Timestamp
"4532123456789012|12|25|123","approved","Charged $0.01","2D","Staleks Florida",1704123456.789
```

---

## 🚀 Advanced Usage

### Running Both Modes Simultaneously

You can run CLI and bot at the same time in different terminals:

```bash
# Terminal 1 - CLI Mode
./madystripe.py cli cards.txt

# Terminal 2 - Bot Mode
./madystripe.py bot
```

### Custom Rate Limiting

Adjust the delay between checks to avoid rate limiting:

```bash
# Fast (0.5s delay)
./madystripe.py cli cards.txt -d 0.5

# Medium (1.0s delay)
./madystripe.py cli cards.txt -d 1.0

# Slow (2.5s delay)
./madystripe.py cli cards.txt -d 2.5
```

### Batch Processing

Process large batches efficiently:

```bash
# Process first 1000 cards
./madystripe.py cli large_file.txt -l 1000 -o batch1.txt

# Process next 1000 cards (manually skip first 1000 in file)
./madystripe.py cli large_file.txt -l 1000 -o batch2.txt
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Gateway Not Available

```bash
# List available gateways
./madystripe.py --list-gateways

# Check if gateway files exist
ls -la 100$/100$/Charge*.py
```

#### 2. Import Errors

```bash
# Ensure you're in the correct directory
cd /home/null/Desktop/MadyStripe

# Check Python path
python3 -c "import sys; print(sys.path)"
```

#### 3. Telegram Bot Not Responding

```bash
# Check bot token
./madystripe.py bot --bot-token YOUR_TOKEN

# Verify bot is running
ps aux | grep madystripe
```

#### 4. Rate Limiting / HTTP 400 Errors

```bash
# Increase delay between checks
./madystripe.py cli cards.txt -d 2.5

# Try different gateway
./madystripe.py cli cards.txt -g shopify
```

---

## 📈 Performance Tips

### For Best Results

1. **Use Staleks Gateway** - Fastest and most reliable
2. **Optimal Delay** - 0.5-1.0 seconds between checks
3. **Batch Size** - Process 100-200 cards at a time
4. **File Quality** - Ensure cards are properly formatted
5. **Network** - Stable internet connection required

### Speed Benchmarks

| Gateway | Average Speed | Success Rate |
|---------|---------------|--------------|
| Staleks Florida | 2.0 c/s | ~30% |
| Shopify Optimized | 1.5 c/s | ~25% |
| Legacy Gateways | 1.0 c/s | ~20% |

---

## 🔒 Security Notes

- ⚠️ This tool is for educational purposes only
- 🔐 Keep your bot token secure
- 🚫 Don't share your configuration files
- 📝 Be aware of rate limiting
- ⚖️ Use responsibly and legally

---

## 📞 Support

### Getting Help

```bash
# Show general help
./madystripe.py --help

# Show CLI help
./madystripe.py cli --help

# Show bot help
./madystripe.py bot --help

# Show system info
./madystripe.py --info
```

### Bot Credit

Created by **@MissNullMe**

---

## 🎉 What's New in v3.0

### Major Changes

✅ **Unified Architecture** - Combined MadyChecker and Stripefiy
✅ **Core Module System** - Modular, maintainable code
✅ **Enhanced Gateways** - Best gateways from both tools
✅ **Improved UI** - Better CLI with more information
✅ **Better Bot** - Enhanced Telegram bot with more features
✅ **Card Type Detection** - Automatic 2D/3D/3DS detection
✅ **Multiple Export Formats** - TXT, JSON, CSV support
✅ **Real-time Stats** - Live success rates and metrics

### Migration from Old Versions

If you were using the old tools:

- **mady_live_checker_v2.py** → Use `./madystripe.py cli`
- **mady_final.py** → Use `./madystripe.py bot`

All your old gateway files are still used, but now managed through the unified system!

---

## 📝 Quick Reference

### Essential Commands

```bash
# CLI Mode
./madystripe.py cli cards.txt                    # Basic check
./madystripe.py cli cards.txt -g staleks         # Specific gateway
./madystripe.py cli cards.txt -l 100 -o out.txt  # Limit & save

# Bot Mode
./madystripe.py bot                              # Start bot

# Info
./madystripe.py --list-gateways                  # List gateways
./madystripe.py --info                           # System info
./madystripe.py --version                        # Version
```

### Card Format

```
NUMBER|MM|YY|CVC
4532123456789012|12|25|123
```

### Bot Commands

```
/start  - Welcome message
/gate   - Select gateway
/check  - Check file
/stop   - Stop checking
/stats  - View statistics
/help   - Show help
```

---

**Enjoy MadyStripe Unified v3.0! 🎉**

*For questions or issues, contact @MissNullMe*
