#!/usr/bin/env python3
"""
Final comprehensive test for all gateways
Shows which ones are working and which need fixes
"""

import sys
import time
import traceback
sys.path.insert(0, '100$/100$/')

# Test card
TEST_CARD = "5566258985615466|12|25|299"

print("="*70)
print("FINAL GATEWAY TEST - ALL GATEWAYS STATUS")
print("="*70)
print(f"\nTest Card: {TEST_CARD[:4]}****")
print("-"*70)

results = []

# Gateway 1 - Blemart
print("\n[1] Testing Blemart ($4.99)...")
try:
    from Charge1 import BlemartCheckout
    start = time.time()
    result = BlemartCheckout(TEST_CARD)
    elapsed = time.time() - start
    status = "✅ WORKING" if "Error" not in result and "Failed" not in result else "❌ ISSUES"
    results.append(f"Gateway 1 (Blemart): {status} - {result[:50]}... ({elapsed:.1f}s)")
    print(f"   {status}: {result[:60]}...")
except Exception as e:
    results.append(f"Gateway 1 (Blemart): ❌ ERROR - {str(e)[:50]}")
    print(f"   ❌ ERROR: {e}")

# Gateway 2 - District People
print("\n[2] Testing District People (€69)...")
try:
    from Charge2 import DistrictPeopleCheckout
    start = time.time()
    result = DistrictPeopleCheckout(TEST_CARD)
    elapsed = time.time() - start
    status = "✅ WORKING" if "Error" not in result and "Failed" not in result else "❌ ISSUES"
    results.append(f"Gateway 2 (District): {status} - {result[:50]}... ({elapsed:.1f}s)")
    print(f"   {status}: {result[:60]}...")
except Exception as e:
    results.append(f"Gateway 2 (District): ❌ ERROR - {str(e)[:50]}")
    print(f"   ❌ ERROR: {e}")

# Gateway 3 - Saint Vinson
print("\n[3] Testing Saint Vinson ($20)...")
try:
    from Charge3 import SaintVinsonDonateCheckout
    start = time.time()
    result = SaintVinsonDonateCheckout(TEST_CARD)
    elapsed = time.time() - start
    status = "✅ WORKING" if "Error" not in result and "Failed" not in result else "❌ ISSUES"
    results.append(f"Gateway 3 (Saint Vinson): {status} - {result[:50]}... ({elapsed:.1f}s)")
    print(f"   {status}: {result[:60]}...")
except Exception as e:
    results.append(f"Gateway 3 (Saint Vinson): ❌ ERROR - {str(e)[:50]}")
    print(f"   ❌ ERROR: {e}")

# Gateway 4 - BGD Fresh
print("\n[4] Testing BGD Fresh ($6.50)...")
try:
    from Charge4 import BGDCheckoutLogic
    start = time.time()
    result = BGDCheckoutLogic(TEST_CARD)
    elapsed = time.time() - start
    status = "✅ WORKING" if "Error" not in result and "Failed" not in result else "❌ ISSUES"
    results.append(f"Gateway 4 (BGD): {status} - {result[:50]}... ({elapsed:.1f}s)")
    print(f"   {status}: {result[:60]}...")
except Exception as e:
    results.append(f"Gateway 4 (BGD): ❌ ERROR - {str(e)[:50]}")
    print(f"   ❌ ERROR: {e}")

# Gateway 5 - Staleks (Priority)
print("\n[5] Testing Staleks ($1.00) - PRIORITY...")
try:
    from Charge5 import StaleksFloridaCheckoutVNew
    
    # Test without proxy first
    print("   Testing without proxy...")
    start = time.time()
    result = StaleksFloridaCheckoutVNew(TEST_CARD)
    elapsed = time.time() - start
    status = "✅ WORKING" if "Charged" in str(result) or "Declined" in str(result) else "❌ ISSUES"
    results.append(f"Gateway 5 (Staleks): {status} - {result[:50]}... ({elapsed:.1f}s)")
    print(f"   {status}: {result[:60]}...")
    
except Exception as e:
    results.append(f"Gateway 5 (Staleks): ❌ ERROR - {str(e)[:50]}")
    print(f"   ❌ ERROR: {e}")

# Summary
print("\n" + "="*70)
print("SUMMARY OF GATEWAY STATUS")
print("="*70)

working_count = 0
for r in results:
    print(r)
    if "✅ WORKING" in r:
        working_count += 1

print("\n" + "-"*70)
print(f"Total Working: {working_count}/5 gateways")
print("-"*70)

# Recommendations
print("\n📋 RECOMMENDATIONS:")
if working_count == 0:
    print("❌ No gateways are currently working properly")
    print("   - Check internet connectivity")
    print("   - Sites may be blocking or down")
    print("   - Consider using proxies")
elif working_count < 3:
    print("⚠️  Only some gateways are working")
    print("   - Focus on the working gateways")
    print("   - Debug the failing ones individually")
else:
    print("✅ Most gateways are operational")
    print("   - Ready for batch processing")
    print("   - Use working gateways for production")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
