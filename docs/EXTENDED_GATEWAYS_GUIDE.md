# 🚀 MADY VPS CHECKER v3.0 - EXTENDED GATEWAY GUIDE

## 📦 NEW GATEWAYS ADDED

This is a **branch version** of the original bot with additional payment gateways:

| Gateway | ID | Amount | Type | Status |
|---------|-----|--------|------|--------|
| **Braintree** | 6 | $1.00 | Braintree/PayPal | ✅ NEW |
| **Square** | 7 | $1.00 | Square Payments | ✅ NEW |
| **Shopify** | 8 | Variable | Shopify/Stripe | ✅ NEW |

---

## 📁 NEW FILES CREATED

### **Gateway Files:**
```
100$/100$/Charge6_Braintree.py  - Braintree gateway implementation
100$/100$/Charge7_Square.py     - Square gateway implementation
100$/100$/Charge8_Shopify.py    - Shopify gateway implementation
```

### **Bot Files:**
```
mady_vps_checker_v3.py          - Extended VPS checker with all 8 gateways
```

---

## 🎯 HOW TO USE

### **Basic Usage:**
```bash
cd /home/null/Desktop/MadyStripe

# Use original Stripe gateways (1-5)
python3 mady_vps_checker_v3.py /home/null/Desktop/TestCards.txt --gateway 1

# Use NEW Braintree gateway
python3 mady_vps_checker_v3.py /home/null/Desktop/TestCards.txt --gateway 6

# Use NEW Square gateway
python3 mady_vps_checker_v3.py /home/null/Desktop/TestCards.txt --gateway 7

# Use NEW Shopify gateway (requires shop URL)
python3 mady_vps_checker_v3.py cards.txt --gateway 8 --shop-url https://example.myshopify.com
```

### **Interactive Mode:**
```bash
python3 mady_vps_checker_v3.py --interactive
```
This will prompt you to:
1. Enter card file path
2. Select gateway from menu
3. Choose number of threads

### **With Options:**
```bash
# 10 threads, Braintree gateway, limit 50 cards
python3 mady_vps_checker_v3.py cards.txt -g 6 -t 10 -l 50

# Simulation mode (no real gateway calls)
python3 mady_vps_checker_v3.py cards.txt --simulate
```

---

## 📊 GATEWAY DETAILS

### **Gateway 6: Braintree**
- **Provider:** Braintree (PayPal)
- **Amount:** $1.00
- **Features:**
  - More lenient than Stripe
  - Good for card validation
  - PayPal integration
- **Usage:**
  ```bash
  python3 mady_vps_checker_v3.py cards.txt --gateway 6
  ```

### **Gateway 7: Square**
- **Provider:** Square Payments
- **Amount:** $1.00
- **Features:**
  - Good for small amounts
  - Web Payments SDK
  - Checkout Link support
- **Usage:**
  ```bash
  python3 mady_vps_checker_v3.py cards.txt --gateway 7
  ```

### **Gateway 8: Shopify**
- **Provider:** Shopify (uses Stripe)
- **Amount:** Variable (depends on product)
- **Features:**
  - Full checkout flow
  - Dynamic nonce scraping
  - Cart + Checkout automation
- **Usage:**
  ```bash
  python3 mady_vps_checker_v3.py cards.txt --gateway 8 --shop-url https://store.myshopify.com
  ```

---

## 🔧 GATEWAY IMPLEMENTATION DETAILS

### **Braintree (Charge6_Braintree.py)**
```python
# Key functions:
BraintreeCheckout(ccx)           # Main checkout function
BraintreeDropinCheckout(ccx, url) # Drop-in UI based checkout

# Flow:
1. Parse card details
2. Get Braintree client token
3. Tokenize card via Braintree API
4. Process payment with nonce
```

### **Square (Charge7_Square.py)**
```python
# Key functions:
SquareCheckout(ccx)              # Main checkout function
SquareWebPaymentCheckout(ccx, url) # Web Payment SDK checkout
SquareCheckoutLink(ccx, link)    # Checkout Link processing

# Flow:
1. Parse card details
2. Initialize Square payment form
3. Create card nonce
4. Submit payment
```

### **Shopify (Charge8_Shopify.py)**
```python
# Key functions:
ShopifyCheckout(ccx, shop_url)   # Main checkout function
ShopifyDirectCheckout(ccx, link) # Direct checkout link
ShopifyPaymentRequest(ccx, domain, token) # Payment submission

# Flow:
1. Visit shop and get cookies
2. Find product and add to cart
3. Get checkout token
4. Submit contact/shipping info
5. Create Stripe payment method
6. Process payment
```

---

## 📈 COMPARISON: ORIGINAL vs EXTENDED

| Feature | v2 (Original) | v3 (Extended) |
|---------|---------------|---------------|
| Stripe Gateways | ✅ 5 | ✅ 5 |
| Braintree | ❌ | ✅ |
| Square | ❌ | ✅ |
| Shopify | ❌ | ✅ |
| Total Gateways | 5 | 8 |
| Interactive Mode | ✅ | ✅ Enhanced |
| Proxy Support | ✅ | ✅ |
| Rate Limiting | ✅ | ✅ |

---

## 🛠️ CUSTOMIZATION

### **Adding Proxies:**
Edit `mady_vps_checker_v3.py`:
```python
PROXY_LIST = [
    "http://user:pass@proxy1.com:8080",
    "http://user:pass@proxy2.com:8080",
    # Add more proxies
]
```

### **Adjusting Rate Limits:**
```python
rate_limiter = RateLimiter(max_requests=30, time_window=60)
# Change to:
rate_limiter = RateLimiter(max_requests=20, time_window=60)  # More conservative
```

### **Adding New Gateways:**
1. Create `100$/100$/Charge9_NewGateway.py`
2. Add import in `mady_vps_checker_v3.py`:
```python
try:
    from Charge9_NewGateway import NewGatewayCheckout
    GATEWAYS[9] = {
        "name": "New Gateway",
        "func": NewGatewayCheckout,
        "amount": "$X.XX",
        "type": "Gateway Type",
        "category": "category"
    }
except ImportError as e:
    print(f"⚠️ Gateway 9 not available: {e}")
```

---

## 📋 FILE STRUCTURE

```
MadyStripe/
├── mady_complete.py           # Main Telegram bot (original)
├── mady_vps_checker.py        # Original VPS checker
├── mady_vps_checker_v2.py     # Improved VPS checker
├── mady_vps_checker_v3.py     # Extended VPS checker (NEW)
├── 100$/100$/
│   ├── Charge1.py             # Blemart (Stripe)
│   ├── Charge2.py             # District People (Stripe)
│   ├── Charge3.py             # Saint Vinson (Stripe)
│   ├── Charge4.py             # BGD Fresh (Stripe)
│   ├── Charge5.py             # Staleks (Stripe)
│   ├── Charge6_Braintree.py   # Braintree (NEW)
│   ├── Charge7_Square.py      # Square (NEW)
│   └── Charge8_Shopify.py     # Shopify (NEW)
├── GATEWAY_IMPROVEMENTS.md    # Improvement guide
└── EXTENDED_GATEWAYS_GUIDE.md # This file
```

---

## 🚀 QUICK START

```bash
# Navigate to directory
cd /home/null/Desktop/MadyStripe

# Test with simulation (no real charges)
python3 mady_vps_checker_v3.py /home/null/Desktop/TestCards.txt --simulate -l 10

# Use Braintree gateway
python3 mady_vps_checker_v3.py /home/null/Desktop/TestCards.txt --gateway 6 -t 5

# Interactive mode
python3 mady_vps_checker_v3.py --interactive
```

---

## ⚠️ IMPORTANT NOTES

1. **Shopify Gateway** requires a valid Shopify store URL with products
2. **Braintree** uses sandbox credentials by default - replace with live keys for production
3. **Square** requires application ID and location ID for production use
4. **Rate limiting** is enabled by default (30 requests/minute)
5. **Proxy support** is available but requires you to add your own proxies

---

## 📞 CONFIGURATION

**Bot Token:** `7984658748:AAFLNS52swKHJkh4kWuu3LDgckslaZjyJTY`
**Group ID:** `-1003546431412`
**Bot Credit:** `@MissNullMe`

---

## 🎉 SUMMARY

The v3 extended version adds:
- ✅ **Braintree Gateway** - PayPal's payment processor
- ✅ **Square Gateway** - Square's payment system
- ✅ **Shopify Gateway** - Full Shopify checkout automation
- ✅ **Enhanced Interactive Mode** - Gateway selection menu
- ✅ **Category Grouping** - Organized gateway display

**Total Gateways Available: 8**

Happy checking! 🚀
