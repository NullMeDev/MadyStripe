# MadyStripe - Shopify API Gateway Implementation TODO

## Completed Tasks

- [x] **Create `src/core/shopify_api_gateway.py`**
  - [x] Implement `ShopifyAPIGateway` class with full payment flow
  - [x] Implement `fetch_products()` - Fetches products from `/products.json`
  - [x] Implement `process_card()` - Complete checkout flow using GraphQL API
  - [x] Implement `_generate_buyer_info()` - Random buyer data generation
  - [x] Implement GraphQL queries (Proposal, SubmitForCompletion, PollForReceipt)
  - [x] Add proxy support for all requests
  - [x] Add store rotation from `shopify_stores.txt` (14,919 stores loaded)
  - [x] Create `ShopifyAPIGatewayWrapper` for GatewayManager integration

- [x] **Update `src/core/gateways.py`**
  - [x] Import `ShopifyAPIGatewayWrapper`
  - [x] Register as Gateway #9 with aliases: `shopify_api`, `shopify_full`, `9`

- [x] **Create test file `tests/test_shopify_api_gateway.py`**
  - [x] Test gateway import
  - [x] Test gateway initialization
  - [x] Test wrapper class
  - [x] Test GatewayManager integration
  - [x] Test card format validation
  - [x] Test buyer info generation
  - [x] Test fetch products (async)

## Test Results

All 7 tests passed:
- ✓ Import Gateway
- ✓ Gateway Initialization (14,919 stores loaded)
- ✓ Wrapper Class
- ✓ GatewayManager Integration (Gateway #9 registered)
- ✓ Card Format Validation
- ✓ Buyer Info Generation
- ✓ Fetch Products

## Available Gateways

| ID | Name | Charge Amount | Description |
|----|------|---------------|-------------|
| 5 | Shopify $1 Gate | $0.01-$1.00 | Dynamic Shopify gate |
| 6 | Shopify $5 Gate | $3.00-$7.00 | Dynamic Shopify gate |
| 7 | Shopify $20 Gate | $15.00-$25.00 | Dynamic Shopify gate |
| 8 | Shopify $100 Gate | $80.00-$120.00 | Dynamic Shopify gate |
| **9** | **Shopify API** | **Varies** | **Full /products.json flow (15K+ stores)** |

## Usage

```python
from src.core.gateways import get_gateway_manager, check_card

# Using gateway manager
manager = get_gateway_manager()
status, message, card_type, gateway_name = manager.check_card(card, gateway_id='9')

# Or using convenience function
status, message, card_type, gateway_name = check_card(card, gateway='shopify_api')

# Direct usage
from src.core.shopify_api_gateway import ShopifyAPIGateway
gateway = ShopifyAPIGateway()
status, message, card_type = gateway.check("4242424242424242|12|25|123")
```

## Recent Updates (January 2026)

- [x] **Fixed cart add issues with major stores**
  - Identified that major stores (allbirds, fashionnova, gymshark) have bot protection
  - Updated gateway to prioritize `.myshopify.com` stores (less protected)
  - Added known working stores list for reliable checkout

- [x] **Verified working checkout flow**
  - Tested with `puppylove.myshopify.com` - WORKING
  - Cart add: SUCCESS (status 200)
  - Checkout page: ACCESSIBLE
  - Session token: EXTRACTED
  - GraphQL endpoint: AVAILABLE

- [x] **Store prioritization implemented**
  - Known working stores loaded first
  - `.myshopify.com` stores prioritized over custom domains
  - Store list shuffled for load distribution

## Verified Working Stores

| Store | Products | Status |
|-------|----------|--------|
| puppylove.myshopify.com | 2 | ✓ Working |
| theaterchurch.myshopify.com | 5 | ✓ Working |
| fdbf.myshopify.com | 3 | ✓ Working |

## Store Database Implementation (COMPLETED)

- [x] **Built pre-validated store database**
  - [x] Created `scripts/build_store_database.py` - Async store scanner
  - [x] Scanned 500+ stores, validated 204 working stores
  - [x] Generated `validated_stores_db.json` with pre-fetched variant IDs
  - [x] Stores include: domain, variant_id, price, product_title

- [x] **Implemented store cycling**
  - [x] Gateway loads from JSON database first (204 pre-validated stores)
  - [x] Sequential cycling through stores (not random)
  - [x] Failed store tracking - skips failed stores temporarily
  - [x] Success clears failed status

- [x] **Created comprehensive tests**
  - [x] `tests/test_store_cycling.py` - Store cycling tests
  - [x] `tests/test_e2e_shopify_gateway.py` - End-to-end tests

## Test Results Summary

| Test | Status |
|------|--------|
| Store Database Loading | ✓ PASS (204 stores) |
| Store Cycling | ✓ PASS |
| Failed Store Tracking | ✓ PASS |
| Gateway Initialization | ✓ PASS |
| GatewayManager Integration | ✓ PASS |

## Next Steps (Optional)

- [ ] Add more comprehensive error handling
- [ ] Expand store database to 500+ stores
- [ ] Add proxy rotation for protected stores
- [ ] Performance optimization for high-volume checking
- [ ] Add store health monitoring dashboard
