# Shopify API Gateway - Implementation Complete

## Overview

The Shopify API Gateway has been successfully implemented and integrated into the MadyStripe card checking system. This gateway uses Shopify's `/products.json` API endpoint to dynamically discover products and process payments through the GraphQL checkout API.

## Key Features

### 1. Dynamic Product Discovery
- Fetches products from any Shopify store via `/products.json`
- Automatically finds the cheapest available product variant
- No manual configuration required for new stores

### 2. Full Payment Flow
The gateway implements the complete Shopify checkout process:
1. **Fetch Products** - GET `{store}/products.json`
2. **Add to Cart** - POST `{store}/cart/add.js`
3. **Initiate Checkout** - GET `{store}/checkout`
4. **Extract Session Tokens** - Parse checkout page for session tokens
5. **GraphQL Proposal** - Send delivery/payment proposal
6. **Get Payment Token** - POST to `deposit.shopifycs.com/sessions`
7. **Submit Payment** - GraphQL `SubmitForCompletion` mutation
8. **Poll for Result** - GraphQL `PollForReceipt` query

### 3. Store Prioritization
- **Known Working Stores**: Pre-verified stores that work reliably
- **MyShopify Stores**: `.myshopify.com` stores (less protected)
- **Other Stores**: Custom domain stores (may have bot protection)

### 4. Error Handling
- Comprehensive error detection for all checkout stages
- Proper handling of 3D Secure requirements
- Detection of soft declines (card is live but declined)

## Files

### Core Gateway
- `src/core/shopify_api_gateway.py` - Main gateway implementation

### Integration
- `src/core/gateways.py` - Gateway #9 registration

### Tests
- `tests/test_shopify_api_gateway.py` - Unit tests
- `tests/test_shopify_api_full.py` - Full flow test
- `tests/test_myshopify_checkout.py` - Checkout flow test

## Usage

### Via Gateway Manager
```python
from src.core.gateways import GatewayManager

gm = GatewayManager()
status, message, card_type = gm.check_card("4242424242424242|12|25|123", gateway=9)
```

### Direct Usage
```python
from src.core.shopify_api_gateway import ShopifyAPIGateway

gateway = ShopifyAPIGateway()
status, message, card_type = gateway.check("4242424242424242|12|25|123")
```

### Gateway Aliases
- `9` - Gateway number
- `shopify_api` - Name alias
- `shopify_full` - Alternative alias

## Verified Working Stores

The following stores have been tested and verified to work:
- `puppylove.myshopify.com` - Pet products
- `theaterchurch.myshopify.com` - Church merchandise
- `fdbf.myshopify.com` - Various products

## Response Codes

| Status | Message | Meaning |
|--------|---------|---------|
| `approved` | Charged $X.XX USD | Card charged successfully |
| `approved` | Insufficient Funds (Card Live) | Card is live but has no funds |
| `approved` | Incorrect CVV (Card Live) | Card is live but CVV wrong |
| `declined` | 3D Secure Required | Card requires 3DS verification |
| `declined` | Declined | Generic decline |
| `declined` | Card Expired | Card has expired |
| `error` | Cart add failed | Could not add product to cart |
| `error` | Store requires login | Store needs account |
| `error` | Captcha required | Bot protection triggered |

## Technical Details

### GraphQL Endpoints
- Checkout: `{store}/checkouts/unstable/graphql`
- Payment Token: `https://deposit.shopifycs.com/sessions`

### Required Headers
```python
{
    'User-Agent': 'Mozilla/5.0 ...',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Content-Type': 'application/json',
}
```

### Session Tokens
- `sessionToken` - Main checkout session
- `queueToken` - Queue management token
- `stableId` - Line item identifier

## Limitations

1. **Bot Protection**: Major stores (allbirds, fashionnova, gymshark) have aggressive bot protection that blocks requests without proxies
2. **Proxies Required**: For protected stores, residential proxies are recommended
3. **Rate Limiting**: Some stores may rate limit after multiple requests
4. **3D Secure**: Cards requiring 3DS will be flagged but not completed

## Future Improvements

1. Add proxy rotation support
2. Implement retry logic with store fallback
3. Add more verified working stores
4. Implement captcha solving integration
