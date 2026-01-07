# Shopify Store Database Guide

## Overview

The MadyStripe Shopify API Gateway now includes a pre-validated store database with 200+ stores that have been scanned and verified to work with the payment flow. This significantly improves reliability and speed.

## Features

### Pre-Validated Stores
- **204 stores** with pre-fetched product information
- Each store has a verified `variant_id` ready for checkout
- Stores are sorted by price (cheapest first)
- No need to fetch products at runtime - faster card checking

### Store Cycling
- Gateway automatically cycles through stores in sequence
- Failed stores are tracked and temporarily skipped
- Successful stores are prioritized
- Wrap-around cycling ensures all stores are used

### Price Distribution
| Price Range | Count |
|-------------|-------|
| Under $1    | 5     |
| $1-$5       | 38    |
| $5-$10      | 37    |
| $10-$50     | 88    |
| Over $50    | 36    |

## Files

### `validated_stores_db.json`
The main database file containing all validated stores:
```json
{
  "generated_at": "2026-01-XX...",
  "total_stores": 204,
  "stores": [
    {
      "domain": "store.example.com",
      "variant_id": "12345678901234",
      "price": "1.00",
      "product_title": "Product Name",
      "total_products": 10,
      "validated_at": "2026-01-XX..."
    }
  ]
}
```

### `scripts/build_store_database.py`
Script to rebuild the store database:
```bash
python3 scripts/build_store_database.py
```

Options (edit in script):
- `MAX_STORES = 500` - Maximum stores to scan
- `TARGET_WORKING = 200` - Target number of working stores
- `CONCURRENT_REQUESTS = 20` - Concurrent requests

## Usage

### Using Gateway #9 (Shopify API)
```python
from src.core.gateways import GatewayManager

gm = GatewayManager()
status, message, card_type = gm.check_card("4242424242424242|12|25|123", gateway=9)
```

### Direct Gateway Usage
```python
from src.core.shopify_api_gateway import ShopifyAPIGateway

gateway = ShopifyAPIGateway()
print(f"Loaded {len(gateway.stores)} stores")

# Check a card
status, message, card_type = gateway.check("4242424242424242|12|25|123")
```

### Store Cycling
```python
# Get next store in rotation
store = gateway.get_next_store()
print(f"Using: {store['url']} - variant: {store['variant_id']}")

# Mark store as failed (will be skipped temporarily)
gateway.mark_store_failed(store['url'])

# Mark store as successful
gateway.mark_store_success(store['url'])
```

## Rebuilding the Database

To refresh the store database with new stores:

```bash
cd /home/null/Desktop/MadyStripe
python3 scripts/build_store_database.py
```

The script will:
1. Load stores from `shopify_stores.txt` and `valid_shopify_stores.txt`
2. Prioritize `.myshopify.com` stores (less protected)
3. Validate each store:
   - Fetch products from `/products.json`
   - Test cart add functionality
   - Test checkout accessibility
4. Save working stores to `validated_stores_db.json`

## Top 10 Cheapest Stores

| Store | Price | Product |
|-------|-------|---------|
| onweb.myshopify.com | $0.40 | test |
| holidayshopcloseouts.com | $0.50 | XTREME SUPER SPORT BALL |
| store.perrinbrewing.com | $0.50 | Perrin Sticker |
| chazdean.com | $0.98 | ShipInsure Package Protection |
| brightland.co | $0.98 | Shipping Protection + Carbon Offset |
| wobangwo.myshopify.com | $1.00 | buy dream |
| www.glamifybeauty.com | $1.00 | Silk Eyelash Extensions |
| hardware.shopify.com | $1.00 | Payment Marketing Kit - US |
| mydocumentedlife.net | $1.00 | forme. Label Stickers |
| timewarpboulder.com | $1.00 | Action Comics 1938 #354 |

## Troubleshooting

### No stores loaded
If the gateway shows 0 stores:
1. Check if `validated_stores_db.json` exists
2. Run `python3 scripts/build_store_database.py` to rebuild

### All stores failing
If all stores are failing:
1. Check your internet connection
2. Try using proxies
3. Rebuild the database with fresh stores

### Store marked as failed
Failed stores are automatically skipped. The failed list is cleared when:
- More than 50% of stores have failed
- Gateway is reinitialized

## Integration with Telegram Bot

The enhanced Telegram bot automatically uses Gateway #9:
```
/chk 4242424242424242|12|25|123
```

Or specify the gateway:
```
/chk 4242424242424242|12|25|123 9
