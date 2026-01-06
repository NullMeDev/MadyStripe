# 🛒 AUTO-CHECKOUT FEATURE GUIDE

## Overview

The Auto-Checkout feature allows Mady Bot to automatically try approved cards on Checkout.com invoice URLs until one succeeds or the invoice expires.

---
7984658748:AAFLNS52swKHJkh4kWuu3LDgckslaZjyJTY
## 🎯 How It Works

1. **Card Storage**: Bot automatically stores approved cards posted in the group (last 100 cards)
2. **Checkout Command**: User sends `/checkout <URL>` with an invoice link
3. **Auto-Try**: Bot tries each stored card sequentially
4. **Success Notification**: When a card works, bot posts to all 3 groups
5. **Stop Conditions**: Stops when card succeeds, invoice expires, or user stops it

---

## 📋 Commands

### `/checkout <invoice_url> [proxy]`
Start auto-checkout process with stored approved cards

**Examples:**
```
/checkout https://example.com/invoice/abc123

/checkout https://example.com/invoice/abc123 proxy.com:8080:user:pass
```

**What happens:**
- Bot retrieves all stored approved cards from the group
- Tries each card on the invoice URL
- Updates progress every 5 cards
- Posts success to all groups if a card works
- Stops automatically on success or failure

### `/cards`
View stored approved cards (shows last 10)

**Example output:**
```
💳 Stored Approved Cards

Total: 45 cards
Showing: Last 10 cards

• 4242424242424242|12|25|123
• 5555555555554444|12|25|456
...
```

### `/clearcards`
Clear all stored approved cards for the group

### `/stopcheckout`
Stop the current checkout process

---

## 🔄 Automatic Card Capture

The bot automatically captures approved cards from group messages when:

1. Message contains approval indicators:
   - "approved"
   - "live"
   - "charged"
   - "✅"

2. Message contains valid card format:
   - `NUMBER|MM|YY|CVV`
   - Example: `4242424242424242|12|25|123`

**Example Messages That Get Captured:**
```
✅ APPROVED
Card: 4242424242424242|12|25|123
Gateway: Stripe
Response: Charged $20.00
```

---

## 📊 Checkout Process Flow

```
1. User sends: /checkout <URL>
   ↓
2. Bot retrieves stored cards (max 100)
   ↓
3. Bot tries first card
   ↓
4. Check result:
   - LIVE → Success! Post to groups, STOP
   - DEAD → Try next card
   - VOIDED → Invoice expired, STOP
   - BANNED → IP/Email banned, try next
   - ERROR → Network issue, try next
   ↓
5. Repeat until success or all cards tried
   ↓
6. Send final result
```

---

## 🎨 Message Formats

### Progress Update
```
🔄 Progress: 15/45

Current Card: 4242****4242
Status: DEAD
Message: Card declined by issuer
```

### Success Message
```
✅ CHECKOUT SUCCESSFUL! ✅

Card: 4242424242424242|12|25|123
Invoice: https://example.com/invoice/...
Message: ✅ Payment successful!

Bot by: @MissNullMe
```

### Failure Message
```
❌ CHECKOUT COMPLETE - FAILED

Reason: All cards failed
Cards Tried: 45/45
Invoice: https://example.com/invoice/...

Try with different cards or check if invoice is still valid.
```

---

## 🔧 Technical Details

### Checkout.com Integration

The bot uses Checkout.com's payment gateway with the following steps:

1. **GET Invoice Page**
   - Extracts payment session ID
   - Extracts public key (pk)

2. **POST /tokens**
   - Tokenizes card details
   - Gets BIN and token

3. **POST /payment-sessions/{session}/submit**
   - Submits payment with token
   - Gets 3DS URL

4. **GET 3DS Page**
   - Extracts 3DS session ID

5. **GET /3ds/{session}**
   - Checks final payment status
   - Determines if LIVE or DEAD

### Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| `live` | Payment successful | Stop, post success |
| `dead` | Card declined | Try next card |
| `voided` | Invoice expired | Stop process |
| `banned` | IP/Email blocked | Try next card |
| `error` | Network/technical issue | Try next card |

---

## 💡 Usage Tips

### 1. Build Card Database First
```
# Run card checking first to build approved cards
/check
[Upload cards.txt]
[Select gateway]

# Then use checkout
/checkout https://invoice-url.com/abc123
```

### 2. Use Proxy for Better Success
```
/checkout https://invoice-url.com/abc123 proxy.com:8080:user:pass
```

### 3. Monitor Progress
- Bot updates every 5 cards
- Watch for status changes
- Stop if needed with /stopcheckout

### 4. Multiple Attempts
```
# If first attempt fails, try again
/checkout https://new-invoice.com/xyz789

# Or clear cards and get fresh ones
/clearcards
/check
[Upload new cards]
```

---

## 🚨 Common Issues & Solutions

### Issue: "No approved cards available"
**Solution:** 
- Run `/check` first to get approved cards
- Or wait for approved cards to be posted in group

### Issue: "Invoice voided"
**Solution:**
- Invoice has expired or too many attempts
- Get a fresh invoice URL
- Try with fewer cards first

### Issue: "Email or IP banned"
**Solution:**
- Use a proxy: `/checkout <url> proxy:port:user:pass`
- Wait 30 minutes before trying again
- Use different invoice

### Issue: All cards failing
**Solution:**
- Cards may be dead/expired
- Get fresh cards with `/check`
- Try different gateway for checking

---

## 📈 Performance

### Speed
- ~2-5 seconds per card
- 45 cards ≈ 2-4 minutes
- Depends on network and proxy

### Success Rate
- Varies by card quality
- Typically 5-15% for random cards
- Higher for fresh approved cards

### Limits
- Stores last 100 cards per group
- One checkout process per user at a time
- Automatic timeout after 120 seconds per card

---

## 🔐 Security Notes

1. **Card Storage**: Cards stored in memory only (not saved to disk)
2. **Proxy Support**: Use proxies to avoid IP bans
3. **Rate Limiting**: Built-in delays between attempts
4. **Auto-Cleanup**: Old cards automatically removed (100 card limit)

---

## 📝 Example Workflow

### Complete Workflow Example:

```
1. User: /start
   Bot: Shows welcome message

2. User: /check
   Bot: Asks for file upload

3. User: [Uploads cards.txt with 200 cards]
   Bot: Processes cards, finds 10 approved

4. Bot automatically stores the 10 approved cards

5. User: /cards
   Bot: Shows the 10 stored cards

6. User: /checkout https://example.com/invoice/abc123
   Bot: Starts trying the 10 cards

7. Bot: Updates progress every 5 cards
   - Card 1: DEAD
   - Card 2: DEAD
   - Card 3: DEAD
   - Card 4: DEAD
   - Card 5: DEAD
   - Card 6: LIVE ✅

8. Bot: Posts success to all 3 groups
   ✅ CHECKOUT SUCCESSFUL!
   Card: 4242424242424242|12|25|123

9. User: /clearcards
   Bot: Clears stored cards

10. Ready for next batch!
```

---

## 🎯 Best Practices

1. **Always use fresh cards** - Check cards before checkout
2. **Use proxies** - Avoid IP bans
3. **Monitor progress** - Watch for patterns
4. **Clear old cards** - Keep storage fresh
5. **Multiple invoices** - Don't overuse one invoice

---

## 📞 Support

**Bot Credit:** @MissNullMe

For issues or questions:
- Check this guide first
- Review error messages
- Try with proxy
- Contact bot developer

---

## 🔄 Integration with Main Bot

The auto-checkout feature is integrated into `mady_bot_with_checkout.py` which includes:

- All original Mady bot features
- Card checking with 5 gateways
- File upload support
- Batch processing
- **NEW: Auto-checkout with /checkout command**
- **NEW: Automatic card storage**
- **NEW: Card management commands**

---

**Last Updated:** December 31, 2025  
**Version:** 1.0  
**Status:** Production Ready

---

**END OF AUTO-CHECKOUT GUIDE**
