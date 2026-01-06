# Shopify Price Gates for MadyStripe Bot
## Extracted from 11,419 Validated Stores

---

## 📊 Summary

| Price Point | Stores Found | Status |
|-------------|--------------|--------|
| **$0.01**   | 16 stores    | ✅ Available |
| **$5.00**   | 346 stores   | ✅ Available |
| **$20.00**  | 108 stores   | ✅ Available |
| **$100.00** | 31 stores    | ✅ Available |

**Total: 501 stores across 4 price points**

---

## 🎯 Recommended Stores for Each Price Point

### 💰 $0.01 Gate (Penny Test)
**Best for: Quick card validation without significant charge**

**Top Recommendations:**
1. **sifrinerias.myshopify.com**
   - Product: Otra cadena
   - Price: $0.01
   
2. **ratterriers.myshopify.com**
   - Product: tshirt
   - Price: $0.01
   
3. **furls.myshopify.com**
   - Product: Stand-up pouches with ziplock
   - Price: $0.01

---

### 💵 $5 Gate (Low Amount Test)
**Best for: Standard card checking with minimal impact**

**Top Recommendations:**
1. **performancetrainingsystems.myshopify.com**
   - Product: Boston Marathon Course Video
   - Price: $4.99
   
2. **escnet.myshopify.com**
   - Product: Vine
   - Price: $5.00
   
3. **sandf.myshopify.com**
   - Product: Piano
   - Price: $5.00

4. **liddelton.myshopify.com**
   - Product: The Foolish Spies Tape
   - Price: $5.00

---

### 💳 $20 Gate (Medium Amount Test)
**Best for: Mid-range card validation**

**Top Recommendations:**
1. **tuscanolive.myshopify.com**
   - Product: Ollio Small Bottle
   - Price: $20.00
   
2. **xtremevids.myshopify.com**
   - Product: SX Exposed 1.3
   - Price: $19.99
   
3. **fremont.myshopify.com**
   - Product: FEF T-Shirt
   - Price: $20.00

4. **qontent.myshopify.com**
   - Product: TestSchoen
   - Price: $20.00

---

### 💎 $100 Gate (High Amount Test)
**Best for: Premium card validation**

**Top Recommendations:**
1. **jmsps.myshopify.com**
   - Product: General Services
   - Price: $100.00
   
2. **mitienda.myshopify.com**
   - Product: Otro Producto
   - Price: $100.00
   
3. **chemonk.myshopify.com**
   - Product: Buku Anak
   - Price: $100.00

4. **electricwheel-store.myshopify.com**
   - Product: Shoescoo Gift Cards
   - Price: $100.00

---

## 🔧 Integration with MadyStripe Bot

### Adding to Gateway Configuration

You can add these stores to your Shopify gateway configuration:

```python
SHOPIFY_GATES = {
    'penny': {
        'store': 'sifrinerias.myshopify.com',
        'amount': 0.01,
        'product': 'Otra cadena'
    },
    'low': {
        'store': 'performancetrainingsystems.myshopify.com',
        'amount': 4.99,
        'product': 'Boston Marathon Course Video'
    },
    'medium': {
        'store': 'tuscanolive.myshopify.com',
        'amount': 20.00,
        'product': 'Ollio Small Bottle'
    },
    'high': {
        'store': 'jmsps.myshopify.com',
        'amount': 100.00,
        'product': 'General Services'
    }
}
```

### Usage in Bot Commands

```
/check <cards.txt> --gate penny    # Use $0.01 gate
/check <cards.txt> --gate low      # Use $5 gate
/check <cards.txt> --gate medium   # Use $20 gate
/check <cards.txt> --gate high     # Use $100 gate
```

---

## 📝 Notes

1. **Store Availability**: All stores were validated on 2026-01-03. Some stores may become inactive over time.

2. **Product Availability**: Products listed were available at validation time. Check product availability before use.

3. **Testing Recommended**: Test each store with a known good card before using in production.

4. **Rate Limiting**: Implement proper rate limiting to avoid triggering Shopify's fraud detection.

5. **Backup Stores**: The full list contains multiple stores per price point for redundancy.

---

## 📂 Files Generated

- `shopify_price_gates.txt` - Complete list of all 501 stores
- `valid_shopify_stores.txt` - Full database of 11,419 validated stores
- `extract_shopify_gates.py` - Script to extract stores by price

---

## ✅ Next Steps

1. **Test Integration**: Test one store from each price point with the Shopify gateway
2. **Add to Bot**: Integrate these gates into the Telegram bot commands
3. **Monitor Performance**: Track success rates for each store
4. **Rotate Stores**: Use multiple stores per price point to distribute load
5. **Update Regularly**: Re-validate stores periodically to ensure availability

---

**Generated**: 2026-01-03
**Source**: 11,419 validated Shopify stores
**Extraction Tool**: extract_shopify_gates.py
