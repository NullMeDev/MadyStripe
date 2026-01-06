# Shopify Integration - Comprehensive Testing Plan

## Overview
This document provides a complete testing plan for the Shopify integration. Follow these steps to thoroughly test all functionality.

## Prerequisites

### 1. Install Dependencies
```bash
pip install aiohttp asyncio requests
```

### 2. Verify Installation
```bash
python3 test_shopify_integration.py
```

Expected output: All 6 tests should pass

### 3. Prepare Test Data

**Create test card file:**
```bash
cat > shopify_test_cards.txt << EOF
4532015112830366|12|2025|123
5425233430109903|08|2026|456
4111111111111111|12|2025|789
4242424242424242|12|2027|100
EOF
```

**Find test Shopify stores:**
```bash
# Use stores from shopify_stores.txt or find new ones
cat shopify_stores.txt
```

## Test Suite

### Phase 1: Basic Functionality Tests (15 minutes)

#### Test 1.1: Gateway Import
```bash
python3 -c "from core.shopify_gateway import ShopifyGateway; print('✅ Import successful')"
```

**Expected:** ✅ Import successful

#### Test 1.2: Gateway Creation
```bash
python3 << EOF
from core.shopify_gateway import ShopifyGateway

gateway = ShopifyGateway("example.myshopify.com")
print(f"Gateway: {gateway.name}")
print(f"Store: {gateway.store_url}")
print(f"✅ Gateway created successfully")
EOF
```

**Expected:** Gateway details printed

#### Test 1.3: CLI Checker Help
```bash
python3 mady_shopify_checker.py --help
```

**Expected:** Help message with all options

#### Test 1.4: CLI Checker No Args
```bash
python3 mady_shopify_checker.py
```

**Expected:** Usage message

---

### Phase 2: Store Detection Tests (10 minutes)

#### Test 2.1: Valid Shopify Store
```bash
# Test with a known Shopify store
python3 << EOF
import requests

store = "shop.gymshark.com"  # Known Shopify store
try:
    resp = requests.get(f"https://{store}/products.json", timeout=5)
    if resp.status_code == 200 and "shopify" in resp.text.lower():
        print(f"✅ {store} is a Shopify store")
    else:
        print(f"❌ {store} is not a Shopify store")
except Exception as e:
    print(f"⚠️ Error: {e}")
EOF
```

**Expected:** ✅ Store is a Shopify store

#### Test 2.2: Invalid Store
```bash
python3 << EOF
import requests

store = "google.com"  # Not a Shopify store
try:
    resp = requests.get(f"https://{store}/products.json", timeout=5)
    if "shopify" in resp.text.lower():
        print(f"❌ False positive")
    else:
        print(f"✅ Correctly identified as non-Shopify")
except:
    print(f"✅ Correctly failed for non-Shopify store")
EOF
```

**Expected:** ✅ Correctly identified

#### Test 2.3: Multiple Stores
```bash
# Test multiple stores from shopify_stores.txt
for store in $(head -5 shopify_stores.txt); do
    echo "Testing: $store"
    curl -s "https://$store/products.json" | grep -q "shopify" && echo "✅ Shopify" || echo "❌ Not Shopify"
done
```

**Expected:** Most should return ✅ Shopify

---

### Phase 3: Single Card Tests (15 minutes)

#### Test 3.1: Single Card - Valid Store
```bash
# Create single card test file
echo "4532015112830366|12|2025|123" > single_test.txt

# Run with limit 1
python3 mady_shopify_checker.py single_test.txt \
  --store shop.gymshark.com \
  --limit 1 \
  --threads 1
```

**Expected Results:**
- Product discovery message
- Checkout attempt
- Result (approved/declined/error)
- Telegram notification (if approved)

**Check for:**
- ✅ No Python errors
- ✅ Clear status message
- ✅ Proper error handling
- ✅ Telegram posting (if approved)

#### Test 3.2: Single Card - Different Store
```bash
python3 mady_shopify_checker.py single_test.txt \
  --store allbirds.com \
  --limit 1 \
  --threads 1
```

**Expected:** Similar to Test 3.1

#### Test 3.3: Invalid Card Format
```bash
echo "invalid|card|format" > invalid_test.txt

python3 mady_shopify_checker.py invalid_test.txt \
  --store shop.gymshark.com \
  --limit 1
```

**Expected:** ⚠️ Error: Invalid card format

---

### Phase 4: Multi-Card Tests (10 minutes)

#### Test 4.1: Small Batch (5 cards)
```bash
head -5 shopify_test_cards.txt > small_batch.txt

python3 mady_shopify_checker.py small_batch.txt \
  --store shop.gymshark.com \
  --threads 3
```

**Expected:**
- All 5 cards processed
- Statistics displayed
- Summary sent to Telegram

**Monitor:**
- Processing speed
- Error rate
- Telegram notifications

#### Test 4.2: Medium Batch (20 cards)
```bash
head -20 my_cards.txt > medium_batch.txt

python3 mady_shopify_checker.py medium_batch.txt \
  --store allbirds.com \
  --threads 5
```

**Expected:**
- All 20 cards processed
- ~4 cards/minute rate
- Final statistics

---

### Phase 5: Thread Count Tests (10 minutes)

#### Test 5.1: Single Thread
```bash
python3 mady_shopify_checker.py small_batch.txt \
  --store shop.gymshark.com \
  --threads 1
```

**Measure:** Time taken, success rate

#### Test 5.2: 5 Threads
```bash
python3 mady_shopify_checker.py small_batch.txt \
  --store shop.gymshark.com \
  --threads 5
```

**Measure:** Time taken, success rate

#### Test 5.3: 10 Threads (Max)
```bash
python3 mady_shopify_checker.py small_batch.txt \
  --store shop.gymshark.com \
  --threads 10
```

**Measure:** Time taken, rate limiting issues

**Compare:**
- 1 thread: Slowest, most reliable
- 5 threads: Balanced
- 10 threads: Fastest, may hit rate limits

---

### Phase 6: Error Handling Tests (10 minutes)

#### Test 6.1: Non-existent Store
```bash
python3 mady_shopify_checker.py single_test.txt \
  --store nonexistent-store-12345.myshopify.com \
  --limit 1
```

**Expected:** ⚠️ Error: Site Error or Network Error

#### Test 6.2: Store with No Products
```bash
# Find a store with no products (rare)
python3 mady_shopify_checker.py single_test.txt \
  --store empty-store.myshopify.com \
  --limit 1
```

**Expected:** ⚠️ Error: No products found

#### Test 6.3: Invalid Proxy
```bash
python3 mady_shopify_checker.py single_test.txt \
  --store shop.gymshark.com \
  --proxy 192.168.1.1:9999:user:pass \
  --limit 1
```

**Expected:** ⚠️ Error: Proxy/Network Error

#### Test 6.4: Keyboard Interrupt
```bash
# Start a batch and press Ctrl+C after 5 seconds
python3 mady_shopify_checker.py medium_batch.txt \
  --store shop.gymshark.com \
  --threads 5

# Press Ctrl+C after a few cards
```

**Expected:**
- Graceful shutdown
- Partial statistics displayed
- No data corruption

---

### Phase 7: Proxy Tests (10 minutes)

#### Test 7.1: Valid Proxy
```bash
# If you have a working proxy
python3 mady_shopify_checker.py single_test.txt \
  --store shop.gymshark.com \
  --proxy YOUR_PROXY:PORT:USER:PASS \
  --limit 1
```

**Expected:** ✅ Works with proxy

#### Test 7.2: Proxy Format Validation
```bash
# Test various proxy formats
python3 mady_shopify_checker.py single_test.txt \
  --store shop.gymshark.com \
  --proxy ip:port \
  --limit 1
```

**Expected:** Should handle gracefully

---

### Phase 8: Telegram Integration Tests (10 minutes)

#### Test 8.1: Approved Card Notification
```bash
# Use a card that will be approved
python3 mady_shopify_checker.py single_test.txt \
  --store shop.gymshark.com \
  --limit 1
```

**Check Telegram:**
- ✅ Message received
- ✅ Proper formatting
- ✅ All details included
- ✅ Bot credit shown

#### Test 8.2: Batch Summary
```bash
python3 mady_shopify_checker.py small_batch.txt \
  --store shop.gymshark.com \
  --threads 3
```

**Check Telegram:**
- ✅ Summary message received
- ✅ Statistics correct
- ✅ Proper formatting

#### Test 8.3: Multiple Approved Cards
```bash
# Run a batch that should have multiple approvals
python3 mady_shopify_checker.py medium_batch.txt \
  --store shop.gymshark.com \
  --threads 5
```

**Check Telegram:**
- ✅ Each approved card posted separately
- ✅ Summary at end
- ✅ No duplicate messages

---

### Phase 9: Performance Tests (10 minutes)

#### Test 9.1: Speed Test
```bash
time python3 mady_shopify_checker.py small_batch.txt \
  --store shop.gymshark.com \
  --threads 5
```

**Measure:**
- Total time
- Cards per second
- Success rate

#### Test 9.2: Large Batch
```bash
head -50 my_cards.txt > large_batch.txt

python3 mady_shopify_checker.py large_batch.txt \
  --store shop.gymshark.com \
  --threads 10
```

**Monitor:**
- Memory usage
- CPU usage
- Network traffic
- Rate limiting

#### Test 9.3: Sustained Load
```bash
# Run multiple batches back-to-back
for i in {1..3}; do
    echo "Batch $i"
    python3 mady_shopify_checker.py small_batch.txt \
      --store shop.gymshark.com \
      --threads 5
    sleep 30
done
```

**Check:**
- Consistent performance
- No memory leaks
- No degradation

---

### Phase 10: Edge Cases (10 minutes)

#### Test 10.1: Empty File
```bash
touch empty.txt
python3 mady_shopify_checker.py empty.txt --store shop.gymshark.com
```

**Expected:** ❌ Error: No valid cards found

#### Test 10.2: Mixed Valid/Invalid Cards
```bash
cat > mixed.txt << EOF
4532015112830366|12|2025|123
invalid|card|here
5425233430109903|08|2026|456
another|bad|one
EOF

python3 mady_shopify_checker.py mixed.txt \
  --store shop.gymshark.com
```

**Expected:**
- Valid cards processed
- Invalid cards show errors
- No crashes

#### Test 10.3: Very Long Card File
```bash
# Create 1000 card file
for i in {1..1000}; do
    echo "4532015112830366|12|2025|123"
done > huge.txt

python3 mady_shopify_checker.py huge.txt \
  --store shop.gymshark.com \
  --limit 10
```

**Expected:**
- Loads quickly
- Limit works correctly
- No memory issues

---

## Test Results Template

### Test Execution Log

```
Date: _______________
Tester: _______________

Phase 1: Basic Functionality
[ ] Test 1.1: Gateway Import - PASS/FAIL
[ ] Test 1.2: Gateway Creation - PASS/FAIL
[ ] Test 1.3: CLI Help - PASS/FAIL
[ ] Test 1.4: CLI No Args - PASS/FAIL

Phase 2: Store Detection
[ ] Test 2.1: Valid Store - PASS/FAIL
[ ] Test 2.2: Invalid Store - PASS/FAIL
[ ] Test 2.3: Multiple Stores - PASS/FAIL

Phase 3: Single Card
[ ] Test 3.1: Valid Store - PASS/FAIL
[ ] Test 3.2: Different Store - PASS/FAIL
[ ] Test 3.3: Invalid Format - PASS/FAIL

Phase 4: Multi-Card
[ ] Test 4.1: Small Batch - PASS/FAIL
[ ] Test 4.2: Medium Batch - PASS/FAIL

Phase 5: Thread Count
[ ] Test 5.1: Single Thread - PASS/FAIL
[ ] Test 5.2: 5 Threads - PASS/FAIL
[ ] Test 5.3: 10 Threads - PASS/FAIL

Phase 6: Error Handling
[ ] Test 6.1: Non-existent Store - PASS/FAIL
[ ] Test 6.2: No Products - PASS/FAIL
[ ] Test 6.3: Invalid Proxy - PASS/FAIL
[ ] Test 6.4: Keyboard Interrupt - PASS/FAIL

Phase 7: Proxy
[ ] Test 7.1: Valid Proxy - PASS/FAIL
[ ] Test 7.2: Format Validation - PASS/FAIL

Phase 8: Telegram
[ ] Test 8.1: Approved Notification - PASS/FAIL
[ ] Test 8.2: Batch Summary - PASS/FAIL
[ ] Test 8.3: Multiple Approved - PASS/FAIL

Phase 9: Performance
[ ] Test 9.1: Speed Test - PASS/FAIL
[ ] Test 9.2: Large Batch - PASS/FAIL
[ ] Test 9.3: Sustained Load - PASS/FAIL

Phase 10: Edge Cases
[ ] Test 10.1: Empty File - PASS/FAIL
[ ] Test 10.2: Mixed Cards - PASS/FAIL
[ ] Test 10.3: Long File - PASS/FAIL

Overall Result: ___/30 tests passed
```

### Performance Metrics

```
Single Card Processing Time: _____ seconds
5-Card Batch Time: _____ seconds
20-Card Batch Time: _____ seconds

Average Speed: _____ cards/minute

Success Rate: _____%
Error Rate: _____%

Memory Usage: _____ MB
CPU Usage: _____%
```

### Issues Found

```
Issue 1: _____________________
Severity: High/Medium/Low
Status: Open/Fixed

Issue 2: _____________________
Severity: High/Medium/Low
Status: Open/Fixed

...
```

## Automated Testing Script

Save this as `run_all_tests.sh`:

```bash
#!/bin/bash

echo "========================================="
echo "Shopify Integration - Automated Tests"
echo "========================================="

# Phase 1
echo -e "\n[Phase 1] Basic Functionality"
python3 test_shopify_integration.py

# Phase 2
echo -e "\n[Phase 2] Store Detection"
curl -s "https://shop.gymshark.com/products.json" | grep -q "shopify" && echo "✅ Store detection works"

# Phase 3
echo -e "\n[Phase 3] Single Card Test"
echo "4532015112830366|12|2025|123" > test_single.txt
python3 mady_shopify_checker.py test_single.txt --store shop.gymshark.com --limit 1

# Phase 4
echo -e "\n[Phase 4] Small Batch Test"
head -5 my_cards.txt > test_batch.txt
python3 mady_shopify_checker.py test_batch.txt --store shop.gymshark.com --threads 3

echo -e "\n========================================="
echo "Testing Complete"
echo "========================================="
```

Run with:
```bash
chmod +x run_all_tests.sh
./run_all_tests.sh
```

## Success Criteria

### Must Pass:
- ✅ All Phase 1 tests (basic functionality)
- ✅ At least 2/3 Phase 2 tests (store detection)
- ✅ At least 2/3 Phase 3 tests (single card)
- ✅ At least 1/2 Phase 4 tests (multi-card)
- ✅ All Phase 6 tests (error handling)
- ✅ At least 2/3 Phase 8 tests (Telegram)

### Should Pass:
- Phase 5 tests (threading)
- Phase 7 tests (proxy)
- Phase 9 tests (performance)
- Phase 10 tests (edge cases)

### Minimum Acceptable:
- 20/30 tests passing (67%)
- No critical errors
- Telegram integration working
- Basic functionality operational

## Conclusion

After completing all tests, you should have:
1. Verified all core functionality
2. Identified any issues
3. Confirmed Telegram integration
4. Validated error handling
5. Measured performance

The Shopify integration is production-ready if 80%+ of tests pass.
