# Custom Amount Feature - Staleks Gateway

## Overview
The Staleks gateway (Gateway 5) now supports custom charge amounts! You can charge any amount from $0.01 to $999.99 USD.

## How It Works
The gateway adds multiple quantities of a $0.01 product to reach your desired amount:
- Want to charge $1.00? → Adds 100 items
- Want to charge $20.00? → Adds 2000 items
- Want to charge $0.50? → Adds 50 items

## Usage

### Interactive Mode (Recommended)
```bash
python3 mady_batch_checker.py /home/null/Desktop/TestCards.txt
```

**You'll be prompted:**
1. Select gateway (press Enter for Gateway 5)
2. Enter charge amount (press Enter for $0.01)

**Example:**
```
Enter gateway number (1-5) [default: 5]: 
✅ Using default: Staleks ($0.01)

============================================================
CHARGE AMOUNT CONFIGURATION
============================================================

Enter charge amount in USD [default: 0.01]: $20
✅ Charge amount set to: $20.00
```

### Command Line Mode
```bash
# Use Gateway 5 with default $0.01
python3 mady_batch_checker.py cards.txt -g 5

# The amount prompt will still appear for Gateway 5
```

## Examples

### Example 1: Charge $0.01 (Default)
```bash
python3 mady_batch_checker.py cards.txt
# Press Enter twice (gateway 5, amount 0.01)
```

### Example 2: Charge $1.00
```bash
python3 mady_batch_checker.py cards.txt
# Select gateway 5
# Enter: 1.00
```

### Example 3: Charge $20.00
```bash
python3 mady_batch_checker.py cards.txt
# Select gateway 5
# Enter: 20
```

### Example 4: Charge $5.50
```bash
python3 mady_batch_checker.py cards.txt
# Select gateway 5
# Enter: 5.50
```

## Telegram Message Format

Approved cards will show the custom amount:

```
✅ APPROVED CARD #1 ✅

Card: 5400670337565209|05|2031|384
Gateway: Staleks
Amount: $20.00
Response: Charged $20.00 [3D]
Card Type: 🔐 3D

Progress: 1/1000
Bot: @MissNullMe
```

## Important Notes

1. **Only Gateway 5 (Staleks) supports custom amounts**
   - Other gateways use fixed amounts
   - Gateway 1: $4.99
   - Gateway 2: €69
   - Gateway 3: $20
   - Gateway 4: $6.50

2. **Amount Validation**
   - Must be positive number
   - Automatically formatted to 2 decimal places
   - Invalid input defaults to $0.01

3. **Cart Quantity**
   - Product is $0.01 each
   - Quantity = Amount / 0.01
   - Example: $20.00 = 2000 items

4. **Reliability**
   - Gateway 5 is the most reliable
   - No expired signatures
   - Dynamic nonce scraping
   - Works consistently

## Quick Reference

| Amount | Command |
|--------|---------|
| $0.01  | Just press Enter (default) |
| $1.00  | Enter: 1 or 1.00 |
| $5.00  | Enter: 5 or 5.00 |
| $10.00 | Enter: 10 or 10.00 |
| $20.00 | Enter: 20 or 20.00 |
| $50.00 | Enter: 50 or 50.00 |

## Troubleshooting

**Q: Can I use custom amounts with other gateways?**
A: No, only Gateway 5 (Staleks) supports custom amounts.

**Q: What's the maximum amount?**
A: Technically unlimited, but recommended to stay under $100 for reliability.

**Q: What if I enter an invalid amount?**
A: The system will default to $0.01 and notify you.

**Q: Does the amount affect speed?**
A: No, processing speed is the same regardless of amount.

## Bot by @MissNullMe 🚀
