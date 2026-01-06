# Shopify Payment Flow - Extracted from AutoshBot

## Complete Payment Process

### Step 1: Get Payment Token
**Endpoint:** `https://deposit.shopifycs.com/sessions`
**Method:** POST
**Payload:**
```python
{
    "credit_card": {
        "month": mes,
        "name": f"{firstName} {lastName}",
        "number": formattedCard,  # Spaces every 4 digits
        "verification_value": cvv,
        "year": ano,
        "start_month": "",
        "start_year": "",
        "issue_number": "",
    },
    "payment_session_scope": f"www.{store_domain}"
}
```
**Response:** `{"id": "token_here"}`

### Step 2: Submit Shipping (Proposal GraphQL)
**Endpoint:** `https://{store}/checkouts/unstable/graphql`
**Operation:** `Proposal`
**Key Variables:**
- sessionToken (sst)
- delivery (shipping address + delivery strategy)
- merchandise (product variant ID + quantity)
- buyerIdentity (email, phone)
- payment (empty at this stage)

**Response Path:** `data.session.negotiate.result.sellerProposal`
- Extract: `queueToken`, `stableId`, `delivery_strategy`, `tax_amount`, `shipping_amount`, `currency`

### Step 3: Submit Payment (SubmitForCompletion GraphQL)
**Endpoint:** `https://{store}/checkouts/unstable/graphql`
**Operation:** `SubmitForCompletion`
**Key Variables:**
- sessionToken (sst)
- queueToken (from step 2)
- attemptToken (payment token from step 1)
- payment.paymentLines[0].paymentMethod.sessionId = token
- delivery (same as step 2)
- merchandise (same as step 2)

**Success Response Path:** `data.submitForCompletion.receipt.id`
**Failure Response Path:** `data.submitForCompletion.errors[0].localizedMessage`

### Step 4: Verify Receipt
**Check receipt ID exists**
- If receipt ID present → APPROVED
- If error message contains "insufficient", "declined", "invalid" → DECLINED
- Otherwise → DECLINED (unknown error)

## Key Implementation Details

### 1. Card Formatting
```python
# Format: "4111 1111 1111 1111" (spaces every 4 digits)
formattedCard = " ".join([cc[i:i+4] for i in range(0, len(cc), 4)])
```

### 2. GraphQL Mutations
- **Proposal**: ~270 lines of GraphQL (shipping submission)
- **SubmitForCompletion**: ~704 lines of GraphQL (payment submission)
- Both use massive fragment definitions for receipt details

### 3. Error Detection
```python
# From receipt response
if 'receipt' in response and 'id' in response['receipt']:
    return True, receipt_id
elif 'errors' in response:
    error_msg = response['errors'][0]['localizedMessage']
    if any(word in error_msg.lower() for word in ['insufficient', 'declined', 'invalid']):
        return False, error_msg
```

### 4. Session Management
- Session token (sst) obtained from initial checkout URL
- Queue token obtained from Proposal response
- Payment token obtained from deposit.shopifycs.com
- All three required for SubmitForCompletion

## Critical Success Factors

1. **Exact GraphQL Structure**: Mutations must match Shopify's expected format exactly
2. **Token Flow**: sst → queueToken → paymentToken → receipt
3. **Error Handling**: Distinguish between declined cards and system errors
4. **Rate Limiting**: 5-8 second delays between requests
5. **Dynamic Data**: Extract stableId, delivery_strategy, amounts from Proposal response

## Implementation Strategy

### Phase 3A: Payment Token Generator
- POST to deposit.shopifycs.com
- Format card with spaces
- Return token ID

### Phase 3B: Shipping Submitter (Proposal)
- Build complete GraphQL mutation
- Submit with session token
- Extract queueToken, stableId, delivery_strategy

### Phase 3C: Payment Submitter (SubmitForCompletion)
- Build complete GraphQL mutation
- Include payment token
- Submit and extract receipt ID

### Phase 3D: Receipt Verifier
- Check for receipt.id
- Parse error messages
- Return approved/declined status

## Estimated Complexity
- **Lines of Code**: ~800-1000 (mostly GraphQL strings)
- **Time to Implement**: 3-4 hours
- **Testing Time**: 1-2 hours
- **Total**: 4-6 hours for Phase 3

## Next Steps
1. Create `core/shopify_payment_processor.py`
2. Implement token generation
3. Implement Proposal mutation
4. Implement SubmitForCompletion mutation
5. Implement receipt verification
6. Test with real cards
7. Integrate with smart gateway
