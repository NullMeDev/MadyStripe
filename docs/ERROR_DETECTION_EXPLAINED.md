# Error Detection - Explained

## Question: Does "Unable to process donation" mean declined or error?

**Answer: It means the card was DECLINED (dead card), not a technical error.**

---

## Understanding the Response Types

### ✅ APPROVED (Live Cards)
These indicate the card is **valid and working**:

1. **"CHARGED $1.00 ✅"** - Card successfully charged
2. **"CCN LIVE - Insufficient Funds"** - Card is valid but no money
3. **"CCN LIVE - Incorrect CVC"** - Card valid, wrong CVV
4. **"CCN LIVE - AVS Mismatch"** - Card valid, wrong address
5. **"CCN LIVE - 3DS Required"** - Card valid, needs 3D Secure

### ❌ DECLINED (Dead Cards)
These indicate the card is **invalid or blocked**:

1. **"Card Declined"** - Generic decline by issuer
2. **"Card Declined (Generic)"** - Gateway's generic error (like "Unable to process donation")
3. **"Card Expired"** - Card past expiration date
4. **"Invalid Card Number"** - Wrong card number format
5. **"Card Lost/Stolen"** - Card reported as lost/stolen
6. **"Do Not Honor"** - Bank refuses transaction

### ⚠️ ERROR (Technical Issues)
These indicate **system/network problems**:

1. **"Failed to create payment method"** - Stripe API rejected
2. **"Request Timeout"** - Network timeout
3. **"Exception: ..."** - Code error

---

## The "Unable to process donation" Case

### What the Gateway Returns:
```json
{
  "errors": ["An error occurred while processing your donation.", "Unable to process donation."]
}
```

### What It Means:
- The gateway **received the card details**
- The gateway **tried to charge the card**
- The card was **declined by the payment processor**
- The gateway returns a **generic error message**

### Why It's Confusing:
The message says "error occurred" but it's actually a **card decline**, not a technical error. The gateway just uses generic wording.

### How We Handle It:
```python
elif 'unable to process' in error_lower or 'error occurred' in error_lower:
    # This is the "Unable to process donation" case
    # It's a generic decline, not a technical error
    return False, "Card Declined (Generic)"
```

We detect this pattern and classify it as **DECLINED** with a clearer message.

---

## Improved Error Detection

### Before:
```
❌ [1/3]: 4579720714941032|2|27|530 - An error occurred while processing your donation., Unable to process donation.
```
**Problem**: Looks like a technical error, unclear if card is dead

### After:
```
❌ [1/3]: 4579720714941032|2|27|530 - Card Declined (Generic)
```
**Better**: Clear that it's a card decline, not a system error

---

## Complete Error Detection Logic

### 1. Live Card Indicators (Approved)
```python
if 'insufficient' in error or 'funds' in error:
    return True, "CCN LIVE - Insufficient Funds"
elif 'cvc' in error or 'cvv' in error:
    return True, "CCN LIVE - Incorrect CVC"
elif 'zip' in error or 'postal' in error or 'address' in error:
    return True, "CCN LIVE - AVS Mismatch"
```

### 2. Dead Card Indicators (Declined)
```python
elif 'declined' in error or 'card was declined' in error:
    return False, "Card Declined"
elif 'expired' in error:
    return False, "Card Expired"
elif 'invalid' in error or 'incorrect' in error:
    return False, "Invalid Card Number"
elif 'lost' in error or 'stolen' in error:
    return False, "Card Lost/Stolen"
elif 'do not honor' in error:
    return False, "Do Not Honor"
```

### 3. Generic Errors (Declined)
```python
elif 'unable to process' in error or 'error occurred' in error:
    return False, "Card Declined (Generic)"
```

### 4. Unknown (Declined)
```python
else:
    return False, f"Declined: {error[:80]}"
```

---

## Real-World Examples

### Test Results:
```
❌ [1/3]: 4579720714941032|2|27|530 - Card Declined (Generic)
❌ [2/3]: 4570663792067008|9|27|654 - Card Declined (Generic)
❌ [3/3]: 4628880201124236|5|26|437 - Card Declined (Generic)
```

**Interpretation**: All 3 cards are **dead/invalid**. The gateway tried to charge them but they were declined.

### If We Had Live Cards:
```
✅ [1/10]: 4532015112830366|12|2025|123 - CCN LIVE - Insufficient Funds
✅ [2/10]: 5425233430109903|08|2026|456 - CCN LIVE - Incorrect CVC
✅ [3/10]: 378282246310005|11|2024|789 - CHARGED $1.00 ✅
❌ [4/10]: 4111111111111111|12|2025|123 - Card Declined
❌ [5/10]: 4000000000000002|01|2026|456 - Card Declined (Generic)
```

---

## Summary

| Message | Type | Meaning |
|---------|------|---------|
| CHARGED $1.00 ✅ | ✅ Approved | Card charged successfully |
| CCN LIVE - Insufficient Funds | ✅ Approved | Card valid, no money |
| CCN LIVE - Incorrect CVC | ✅ Approved | Card valid, wrong CVV |
| CCN LIVE - AVS Mismatch | ✅ Approved | Card valid, wrong address |
| Card Declined | ❌ Declined | Dead card |
| Card Declined (Generic) | ❌ Declined | Dead card (generic error) |
| Card Expired | ❌ Declined | Expired card |
| Invalid Card Number | ❌ Declined | Wrong format |
| Failed to create payment method | ⚠️ Error | Stripe API issue |
| Request Timeout | ⚠️ Error | Network issue |

---

## Key Takeaway

**"Unable to process donation" = Card Declined (Generic)**

It's **NOT** a technical error. It's the gateway's way of saying "this card doesn't work" without giving specific details.

The improved error detection now makes this clear by showing:
```
❌ Card Declined (Generic)
```

Instead of the confusing:
```
❌ An error occurred while processing your donation., Unable to process donation.
```

---

## For Users

When you see:
- ✅ **"CCN LIVE"** = Good! Card is valid, save it
- ❌ **"Card Declined"** = Bad! Card is dead, discard it
- ⚠️ **"Error"** or **"Timeout"** = Technical issue, try again

The gateway is now much clearer about what each response means!
