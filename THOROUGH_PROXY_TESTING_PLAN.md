# Thorough Proxy Testing Plan

## Overview
Comprehensive testing plan for Webshare residential proxy integration with Shopify Hybrid Gateway V3.

## Test Suite

### ✅ Test 1: Basic Proxy Integration (COMPLETED)
**Status**: PASSED ✅
**Details**:
- Loaded 100 proxies successfully
- Authentication working (3/3 proxies tested)
- Rotation working correctly
- Performance: 53.60s (faster than baseline 54.55s)

---

### 🔄 Test 2: Extended Proxy Pool (1,000 proxies)
**Status**: IN PROGRESS
**Objective**: Verify gateway can handle larger proxy pools
**Steps**:
1. Create file with 1,000 authenticated proxies
2. Load proxies into gateway
3. Verify memory usage
4. Test rotation across multiple attempts
5. Measure performance impact

**Expected Results**:
- All 1,000 proxies load successfully
- Memory usage remains reasonable (<500MB)
- Rotation works across all proxies
- Performance similar to 100-proxy test

---

### ⏳ Test 3: Proxy Failover Testing
**Objective**: Verify gateway handles invalid/dead proxies gracefully
**Steps**:
1. Create proxy file with mix of valid and invalid proxies
2. Add intentionally bad proxies (wrong port, wrong auth)
3. Run gateway and observe failover behavior
4. Verify gateway skips bad proxies and continues

**Test Cases**:
- Invalid port number
- Wrong authentication credentials
- Non-existent proxy host
- Timeout scenarios

**Expected Results**:
- Gateway detects failed proxies
- Automatically moves to next proxy
- Logs failure reasons
- Completes task with working proxies

---

### ⏳ Test 4: Multiple Store Attempts (10+ attempts)
**Objective**: Test proxy rotation over extended attempts
**Steps**:
1. Configure gateway for 10 store attempts
2. Run test with single card
3. Verify different proxy used for each attempt
4. Monitor for proxy reuse patterns

**Expected Results**:
- 10 different proxies used (or round-robin if <10 proxies)
- No proxy conflicts
- Consistent performance across attempts
- Proper rotation logging

---

### ⏳ Test 5: Headless Mode Testing
**Objective**: Verify proxy works in headless Chrome (VPS deployment)
**Steps**:
1. Set `headless=True` in gateway configuration
2. Run test with proxies
3. Verify authentication works in headless mode
4. Check for any headless-specific issues

**Expected Results**:
- Proxies work in headless mode
- Authentication successful
- No visual/display errors
- Performance similar to non-headless

---

### ⏳ Test 6: Integration with mady_vps_checker.py
**Objective**: Integrate V3 gateway into production checker
**Steps**:
1. Import ShopifyHybridGatewayV3 into mady_vps_checker.py
2. Add to gateway rotation list
3. Configure with proxy file
4. Test with real card data
5. Verify Telegram posting works

**Expected Results**:
- Gateway integrates smoothly
- Works alongside other gateways
- Telegram notifications sent correctly
- Rate limiting improved with proxies

---

### ⏳ Test 7: Long-Running Stability Test
**Objective**: Test proxy stability over extended period
**Steps**:
1. Prepare 100 test cards
2. Run checker with proxy-enabled gateway
3. Monitor for:
   - Memory leaks
   - Connection issues
   - Proxy exhaustion
   - Performance degradation
4. Collect metrics over 1+ hour run

**Expected Results**:
- No memory leaks
- Stable performance throughout
- Proxy rotation continues smoothly
- No connection pool exhaustion

---

## Test Metrics to Collect

### Performance Metrics
- **Load Time**: Time to load proxy file
- **Auth Time**: Time to authenticate each proxy
- **Request Time**: Time per checkout attempt
- **Total Time**: End-to-end time per card
- **Memory Usage**: RAM consumption with different proxy pool sizes

### Reliability Metrics
- **Success Rate**: % of successful proxy connections
- **Failover Rate**: % of proxies that failed and triggered failover
- **Rotation Accuracy**: Verify proxies rotate as expected
- **Stability**: No crashes or hangs over extended runs

### Scalability Metrics
- **100 Proxies**: Baseline performance
- **1,000 Proxies**: 10x scale test
- **10,000 Proxies**: 100x scale test (optional)
- **All 215K Proxies**: Maximum scale test (optional)

---

## Test Environment

### Hardware
- **CPU**: Monitor CPU usage during tests
- **RAM**: Track memory consumption
- **Network**: Monitor bandwidth usage

### Software
- **Python**: 3.x
- **Chrome**: Latest version
- **Selenium**: 4.0+
- **undetected-chromedriver**: 3.5.5+

### Configuration
- **Proxy File**: webshare_proxies_auth.txt (variable size)
- **Headless**: Test both True and False
- **Store Database**: 9,597 stores
- **Max Attempts**: Variable (3, 10, 100)

---

## Success Criteria

### Must Pass
- ✅ All proxies load without errors
- ✅ Authentication works for all proxies
- ✅ Rotation functions correctly
- ✅ No performance degradation vs baseline
- ✅ Headless mode works
- ✅ Integration with VPS checker successful

### Should Pass
- ✅ Failover handles bad proxies gracefully
- ✅ Long-running stability (no crashes)
- ✅ Memory usage remains reasonable
- ✅ Scales to 1,000+ proxies

### Nice to Have
- ✅ Scales to 10,000+ proxies
- ✅ Concurrent card checking works
- ✅ Advanced monitoring/metrics

---

## Test Schedule

### Phase 1: Core Testing (Current)
1. ✅ Basic integration (100 proxies) - COMPLETED
2. 🔄 Extended pool (1,000 proxies) - IN PROGRESS
3. ⏳ Failover testing
4. ⏳ Multiple attempts (10+)

### Phase 2: Production Readiness
5. ⏳ Headless mode testing
6. ⏳ VPS checker integration
7. ⏳ Long-running stability

### Phase 3: Optional Advanced Testing
- Concurrent testing
- Maximum scale (215K proxies)
- Performance optimization
- Advanced monitoring

---

## Risk Assessment

### Low Risk ✅
- Basic proxy loading (proven to work)
- Authentication (working correctly)
- Rotation (functioning as designed)

### Medium Risk ⚠️
- Large proxy pools (1,000+) - may impact memory
- Headless mode - potential display issues
- Long-running stability - unknown over extended periods

### High Risk ❌
- Maximum scale (215K proxies) - may exhaust resources
- Concurrent testing - potential race conditions
- Production integration - may affect existing functionality

---

## Rollback Plan

If any test fails critically:
1. Revert to baseline (no proxy) configuration
2. Use smaller proxy pool (100 proxies)
3. Disable proxy feature temporarily
4. Debug and fix issues
5. Re-test before re-enabling

---

## Documentation

All test results will be documented in:
- `THOROUGH_PROXY_TEST_RESULTS.md` - Comprehensive results
- `test_*.log` files - Detailed logs
- Screenshots (if applicable)
- Performance graphs (if generated)

---

**Test Plan Created**: 2025-01-05
**Status**: Phase 1 In Progress
**Next Test**: Extended Proxy Pool (1,000 proxies)
