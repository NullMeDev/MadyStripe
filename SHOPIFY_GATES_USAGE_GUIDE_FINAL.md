# 🛍️ Shopify Dynamic Gates - Complete Usage Guide

## 📋 Overview

The Shopify Dynamic Gates system provides **real payment processing** with:
- ✅ **9,597 validated stores** with automatic selection
- ✅ **Real GraphQL API calls** (no stub functions)
- ✅ **Automatic fallback** when stores fail
- ✅ **4 price-specific gates** ($0.01, $5, $20, $100)
- ✅ **Multi-format proxy support**
- ✅ **Telegram bot integration**

---

## 🚀 Quick Start - Terminal Testing

### Test All Shopify Gates
```bash
cd /home/null/Desktop/MadyStripe
python3 test_shopify_gates_terminal.py
```

This will test all 4 Shopify gates with automatic store selection and fallback.

### Test Single Card
```python
from core.shopify_price_gateways_dynamic import DynamicShopifyPennyGateway

gateway = DynamicShopifyPennyGateway()
status, message, card_type = gateway.check("4111111111111111|12|25|123")

print(f"Status: {status}")
print(f"Message: {message}")
print(f"Card Type: {card_type}")
```

---

## 🎯 Available Gates

### 1. Penny Gate ($0.01 - $1.00)
```python
from core.shopify_price_gateways_dynamic import DynamicShopifyPennyGateway

gateway = DynamicShopifyPennyGateway()
status, message, card_type = gateway.check("card|mm|yy|cvv")
```

**Telegram Command:** `/penny card|mm|yy|cvv`

### 2. $5 Gate ($3.00 - $7.00)
```python
from core.shopify_price_gateways_dynamic import DynamicShopifyFiveDollarGateway

gateway = DynamicShopifyFiveDollarGateway()
status, message, card_type = gateway.check("card|mm|yy|cvv")
```

**Telegram Command:** `/low card|mm|yy|cvv`

### 3. $20 Gate ($15.00 - $25.00)
```python
from core.shopify_price_gateways_dynamic import DynamicShopifyTwentyDollarGateway

gateway = DynamicShopifyTwentyDollarGateway()
status, message, card_type = gateway.check("card|mm|yy|cvv")
```

**Telegram Command:** `/medium card|mm|yy|cvv`

### 4. $100 Gate ($80.00 - $120.00)
```python
from core.shopify_price_gateways_dynamic import DynamicShopifyHundredDollarGateway

gateway = DynamicShopifyHundredDollarGateway()
status, message, card_type = gateway.check("card|mm|yy|cvv")
```

**Telegram Command:** `/high card|mm|yy|cvv`

---

## 🤖 Telegram Bot Usage

### Start the Bot
```bash
cd /home/null/Desktop/MadyStripe
python3 interfaces/telegram_bot.py
```

### Available Commands

#### Stripe Gates
- `/str card|mm|yy|cvv` - Pipeline gateway ($1 charge)

#### Shopify Gates
- `/penny card|mm|yy|cvv` - Penny gate ($0.01-$1.00)
- `/low card|mm|yy|cvv` - $5 gate ($3.00-$7.00)
- `/medium card|mm|yy|cvv` - $20 gate ($15.00-$25.00)
- `/high card|mm|yy|cvv` - $100 gate ($80.00-$120.00)

#### Proxy Commands
- `/setproxy proxy_string` - Set proxy for requests
- `/checkproxy` - Check current proxy status
- `/clearproxy` - Remove proxy

#### File Processing
- Send `.txt` file with cards (one per line)
- Bot will check all cards and send results

---

## 🔧 Proxy Support

### Supported Formats

1. **Standard Format**
   ```
   username:password@host:port
   ```

2. **Alternative Format**
   ```
   host:port:username:password
   ```

3. **Complex Username Format**
   ```
   user_pinta:1acNvmOToR6d-country-US-state-Washington@residential.ip9.io:8000
   ```

4. **Porter Proxies Format**
   ```
   evo-pro.porterproxies.com:62345:PP_5J7SVIL0BJ-country-US:password
   ```

### Set Proxy via Telegram
```
/setproxy username:password@host:port
```

### Set Proxy in Code
```python
from core.proxy_parser import ProxyParser

proxy_string = "username:password@host:port"
proxy_dict = ProxyParser.parse(proxy_string)

# Use with requests
import requests
response = requests.get(url, proxies=proxy_dict)
```

---

## 📊 How It Works

### 1. Store Selection
- System loads 9,597 validated stores from cache
- Filters stores by price range (e.g., $0.01-$1.00 for penny gate)
- Selects store with best success rate
- Excludes recently failed stores (1-hour blacklist)

### 2. Product Finding
- Fetches products from selected store via Shopify API
- Finds product matching target price (±tolerance)
- Extracts variant ID for checkout

### 3. Payment Processing (Real GraphQL)
```
Step 1: Get Payment Token
  └─> POST https://deposit.shopifycs.com/sessions
      └─> Returns: payment_token

Step 2: Create Checkout
  └─> POST https://store.myshopify.com/cart/add.js
  └─> POST https://store.myshopify.com/checkout/
      └─> Returns: session_token, queue_token, stable_id

Step 3: Submit Shipping (Proposal GraphQL)
  └─> POST https://store.myshopify.com/checkouts/unstable/graphql
      └─> Mutation: Proposal
      └─> Returns: updated queue_token, delivery_strategy

Step 4: Submit Payment (SubmitForCompletion GraphQL)
  └─> POST https://store.myshopify.com/checkouts/unstable/graphql
      └─> Mutation: SubmitForCompletion
      └─> Returns: receipt_id (if approved)
```

### 4. Automatic Fallback
- If store fails → Try next store (up to 3 attempts)
- If product not found → Try next store
- If checkout fails → Try next store
- If payment declined → Return declined (don't try other stores)

---

## 🎯 Response Codes

### Status Values
- `approved` - Card was charged successfully
- `declined` - Card was declined by bank
- `error` - Technical error (store issue, network, etc.)

### Example Responses

**Approved:**
```python
status = 'approved'
message = 'Receipt ID: gid://shopify/Receipt/12345 | Store: example.myshopify.com | Product: Test Product ($0.99)'
card_type = 'Visa'
```

**Declined:**
```python
status = 'declined'
message = 'Insufficient funds'
card_type = 'Mastercard'
```

**Error:**
```python
status = 'error'
message = 'All stores failed. Last error: Failed to create checkout'
card_type = 'Unknown'
```

---

## 📈 Gateway Statistics

### Get Stats
```python
gateway = DynamicShopifyPennyGateway()

# Check some cards...
gateway.check("card1|mm|yy|cvv")
gateway.check("card2|mm|yy|cvv")

# Get statistics
stats = gateway.get_stats()
print(stats)
```

### Stats Output
```python
{
    'total_attempts': 10,
    'successful_charges': 3,
    'success_rate': '30.0%',
    'failed_stores': 5,
    'available_stores': 9592
}
```

---

## 🔍 Troubleshooting

### Issue: "No available stores"
**Solution:** All stores in price range are temporarily blacklisted. Wait 1 hour or adjust price tolerance.

### Issue: "Failed to create checkout"
**Solution:** Store requires login or has checkout disabled. System will automatically try next store.

### Issue: "No products found"
**Solution:** Store has no products in price range. System will automatically try next store.

### Issue: "Payment token generation failed"
**Solution:** Invalid card details or deposit.shopifycs.com is down. Check card format.

### Issue: Slow performance
**Solution:** 
- Each Shopify payment takes 15-30 seconds (4 API calls)
- Use multiple gates concurrently for better throughput
- Consider using Stripe gates for faster checking

---

## ⚡ Performance

### Speed Comparison
- **Stripe Gates:** ~2-3 seconds per card
- **Shopify Gates:** ~15-30 seconds per card (real checkout process)

### Optimization Tips
1. **Use appropriate gate for your needs:**
   - Fast checking → Use Stripe gates
   - Real Shopify testing → Use Shopify gates

2. **Concurrent processing:**
   - Run multiple bot instances
   - Use different price gates simultaneously

3. **Proxy rotation:**
   - Set proxies to avoid rate limiting
   - Rotate proxies between requests

---

## 🛠️ Advanced Usage

### Custom Price Range
```python
from core.shopify_smart_gateway import ShopifySmartGateway

# Create custom gateway for $10-$15 range
gateway = ShopifySmartGateway(target_price=12.50, price_tolerance=2.50)
status, message, card_type = gateway.check("card|mm|yy|cvv", max_attempts=5)
```

### Direct Store Testing
```python
from core.shopify_payment_processor import ShopifyPaymentProcessor

processor = ShopifyPaymentProcessor()

status, message, card_type = processor.process_card(
    store_url="https://example.myshopify.com",
    variant_id=12345,
    card_number="4111111111111111",
    exp_month="12",
    exp_year="25",
    cvv="123"
)
```

### Store Database Queries
```python
from core.shopify_store_database import ShopifyStoreDatabase

db = ShopifyStoreDatabase()

# Find stores in price range
stores = db.find_stores_by_price(0.01, 1.00, limit=10)

# Get random store
store = db.get_random_store("penny")

# Get store at specific price
store = db.get_store_at_price(5.00, tolerance=0.50)

# Get database stats
stats = db.get_stats()
```

---

## 📝 Integration with VPS Checker

### Update mady_vps_checker.py
```python
from core.shopify_price_gateways_dynamic import (
    DynamicShopifyPennyGateway,
    DynamicShopifyFiveDollarGateway,
    DynamicShopifyTwentyDollarGateway,
    DynamicShopifyHundredDollarGateway
)

# Add to gateway list
gateways = {
    'stripe': PipelineGateway(),
    'shopify_penny': DynamicShopifyPennyGateway(),
    'shopify_5': DynamicShopifyFiveDollarGateway(),
    'shopify_20': DynamicShopifyTwentyDollarGateway(),
    'shopify_100': DynamicShopifyHundredDollarGateway(),
}

# Use in checker
gateway = gateways['shopify_penny']
status, message, card_type = gateway.check(card_data)
```

---

## 🎓 Best Practices

### 1. Rate Limiting
- Add 5-8 second delays between Shopify requests
- Use proxies to distribute load
- Don't hammer same store repeatedly

### 2. Error Handling
- Always check status code ('approved', 'declined', 'error')
- Log failed stores for analysis
- Implement retry logic for network errors

### 3. Store Management
- Let system handle store selection automatically
- Don't manually blacklist stores (system does this)
- Review store success rates periodically

### 4. Card Format
- Always use format: `number|month|year|cvv`
- Month: 2 digits (01-12)
- Year: 2 or 4 digits (25 or 2025)
- CVV: 3-4 digits

---

## 📞 Support

### Common Questions

**Q: Why are Shopify gates slower than Stripe?**
A: Shopify gates perform real checkout process (4 API calls), while Stripe gates use direct API. This is necessary for accurate testing.

**Q: Can I use my own stores?**
A: Yes! Add stores to `valid_shopify_stores.txt` and reload the database.

**Q: How often are stores validated?**
A: Stores are validated once and cached. Failed stores are blacklisted for 1 hour.

**Q: Can I adjust price tolerance?**
A: Yes! Create custom gateway with desired tolerance (see Advanced Usage).

---

## 🎉 Summary

You now have a complete Shopify payment testing system with:
- ✅ 9,597 validated stores
- ✅ Real GraphQL payment processing
- ✅ Automatic fallback system
- ✅ 4 price-specific gates
- ✅ Multi-format proxy support
- ✅ Telegram bot integration
- ✅ Comprehensive error handling

**Ready to use!** Start with `python3 test_shopify_gates_terminal.py` to verify everything works.
