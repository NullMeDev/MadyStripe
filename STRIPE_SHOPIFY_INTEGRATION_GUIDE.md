# Stripe & Shopify Integration Guide for AutoshBotSRC

## Overview

This guide documents the comprehensive fixes and improvements made to integrate Stripe and Shopify gateways with AutoshBotSRC.

## Files Created/Modified

### New Gateway Files

1. **`AutoshBotSRC/AutoshBotSRC/gateways/autoShopify_fixed.py`**
   - Fixed version of the Shopify gateway
   - Improved product fetching with retry logic
   - Better error handling
   - Fallback stores support

2. **`AutoshBotSRC/AutoshBotSRC/gateways/autoStripe.py`**
   - New Stripe gateway using CC Foundation
   - $1.00 charge for card validation
   - Proper error code parsing

3. **`AutoshBotSRC/AutoshBotSRC/gateways/autoUnified.py`**
   - Unified gateway manager
   - Auto-selects best gateway
   - Fallback support between gateways

## Issues Fixed

### 1. "No Products Found" Issue
**Problem:** The original `autoShopify.py` was failing to fetch products even with thousands of stores.

**Root Causes:**
- URL normalization issues (missing `https://`)
- No retry logic for transient failures
- No fallback stores when primary fails
- Poor error handling

**Solution:**
```python
# Fixed URL normalization
if not domain.startswith("http"):
    domain = "https://" + domain
domain = domain.rstrip("/")

# Added retry logic
for attempt in range(retries):
    try:
        # ... fetch products
    except Exception:
        if attempt < retries - 1:
            await asyncio.sleep(1)
            continue
```

### 2. Truncated Code Bug
**Problem:** Line ~832 in original file had `return Fa` (truncated)

**Solution:** Complete implementation with proper return statements.

### 3. Missing Stripe Gateway
**Problem:** No Stripe integration existed.

**Solution:** Created `autoStripe.py` using the working CC Foundation gateway:
- Uses Stripe API for payment method creation
- Submits $1.00 donation for validation
- Proper error code parsing

## Bot Commands

After integration, the following commands are available:

| Command | Gateway | Description |
|---------|---------|-------------|
| `/st` | Stripe | Check via CC Foundation ($1.00) |
| `/cc` | Stripe | Alias for Stripe gateway |
| `/sh` | Shopify | Check via Shopify stores |
| `/shop` | Shopify | Shopify-only mode |
| `/stripe` | Stripe | Stripe-only mode |
| `/auto` | Unified | Auto-select best gateway |

## Usage Examples

### Single Card Check
```
/st 4242424242424242|12|2028|123
```

### Mass Check (File Upload)
```
/sh
[Upload file with cards]
```

### Auto Mode
```
/auto 4242424242424242|12|2028|123
```

## Gateway Selection Logic

The unified gateway (`/auto`) uses this logic:

1. **If site + proxies configured:** Try Shopify first, then Stripe
2. **If no site/proxies:** Use Stripe directly
3. **On gateway error:** Automatically try next gateway
4. **On definitive decline:** Return immediately (no fallback needed)

## Configuration

### Adding Shopify Sites
Users can add their own Shopify sites via the bot:
```
/addsh shopnicekicks.com
```

### Adding Proxies
```
/addproxy user:pass@host:port
```

## Fallback Stores

The fixed Shopify gateway includes fallback stores:
```python
FALLBACK_STORES = [
    {"url": "wiredministries.com", "variant_id": ""},
    {"url": "shopnicekicks.com", "variant_id": ""},
    {"url": "culturekings.com.au", "variant_id": ""},
    {"url": "kith.com", "variant_id": ""},
    {"url": "deadstock.ca", "variant_id": ""},
]
```

## Response Codes

### Live Card Indicators
- `Charged!` - Card successfully charged
- `Insufficient Funds` - Card is live but no balance
- `CVV Error` - Card is live, CVV mismatch
- `Incorrect Zip` - Card is live, address mismatch

### Dead Card Indicators
- `Card Declined` - Generic decline
- `Expired Card` - Card has expired
- `Lost/Stolen Card` - Card reported lost/stolen
- `Do Not Honor` - Bank refused transaction
- `Invalid Account` - Account doesn't exist

### Gateway Errors (Will Retry)
- `Proxy Error` - Proxy connection failed
- `Timeout` - Request timed out
- `Captcha Required` - Need better proxies
- `Rate Limited` - Too many requests

## Testing

Run the test script:
```bash
cd /home/null/Desktop/MadyStripe
python test_autoshbot_gateways.py
```

## Architecture

```
AutoshBotSRC/
├── gateways/
│   ├── __init__.py          # Auto-registers all gateways
│   ├── autoShopify.py       # Original (buggy)
│   ├── autoShopify_fixed.py # Fixed version
│   ├── autoStripe.py        # New Stripe gateway
│   └── autoUnified.py       # Unified manager
├── commands/
│   └── base_command.py      # Command registration
├── database.py              # ShopifySite, Proxy models
├── utils.py                 # Helper functions
└── bot.py                   # Main bot
```

## Recommendations

### For Best Results:

1. **Use Stripe for Quick Checks**
   - No proxy required
   - Consistent $1.00 charge
   - Fast response

2. **Use Shopify for Stealth**
   - Requires good proxies
   - Variable charge amounts
   - Better for mass checking

3. **Use Auto Mode for Reliability**
   - Automatic fallback
   - Best of both worlds

### Proxy Requirements

For Shopify:
- Residential proxies recommended
- Rotate proxies frequently
- Avoid datacenter IPs

For Stripe:
- Works without proxies
- Optional proxy support for rate limiting

## Troubleshooting

### "No Products Found"
1. Check if store URL is correct
2. Try different fallback stores
3. Use better proxies
4. Check if store has products.json enabled

### "Captcha Required"
1. Use residential proxies
2. Rotate proxies more frequently
3. Add delays between requests

### "Rate Limited"
1. Wait before retrying
2. Use more proxies
3. Reduce request frequency

## Version History

- **v1.0** - Initial integration
  - Fixed Shopify gateway
  - Added Stripe gateway
  - Created unified manager
  - Added fallback stores
  - Improved error handling
