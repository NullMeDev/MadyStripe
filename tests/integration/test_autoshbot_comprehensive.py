#!/usr/bin/env python3
"""
Comprehensive Test Suite for AutoshBotSRC
Tests all components that can be validated without external services
"""

import sys
import os
import asyncio
import json

# Add AutoshBotSRC to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'AutoshBotSRC', 'AutoshBotSRC'))

print("=" * 60)
print("AUTOSHBOT COMPREHENSIVE TEST SUITE")
print("=" * 60)
print()

# Test Results Tracker
test_results = {
    'passed': 0,
    'failed': 0,
    'skipped': 0,
    'tests': []
}

def log_test(name, status, message=""):
    """Log test result"""
    test_results['tests'].append({
        'name': name,
        'status': status,
        'message': message
    })
    if status == 'PASS':
        test_results['passed'] += 1
        print(f"✅ {name}: PASSED")
    elif status == 'FAIL':
        test_results['failed'] += 1
        print(f"❌ {name}: FAILED - {message}")
    else:
        test_results['skipped'] += 1
        print(f"⏭️  {name}: SKIPPED - {message}")
    if message and status == 'PASS':
        print(f"   {message}")
    print()

# ============================================================
# TEST 1: Module Imports
# ============================================================
print("=" * 60)
print("TEST SUITE 1: MODULE IMPORTS")
print("=" * 60)
print()

try:
    from gateways import autoShopify
    log_test("Import autoShopify module", "PASS", "Module imported successfully")
except Exception as e:
    log_test("Import autoShopify module", "FAIL", str(e))

try:
    from utils import Utils
    log_test("Import Utils module", "PASS", "Utils module available")
except Exception as e:
    log_test("Import Utils module", "FAIL", str(e))

try:
    from database import init_db, get_user, add_user
    log_test("Import database functions", "PASS", "Database functions available")
except Exception as e:
    log_test("Import database functions", "FAIL", str(e))

# ============================================================
# TEST 2: Code Structure Validation
# ============================================================
print("=" * 60)
print("TEST SUITE 2: CODE STRUCTURE VALIDATION")
print("=" * 60)
print()

try:
    # Check if fetchProducts function exists
    if hasattr(autoShopify, 'fetchProducts'):
        log_test("fetchProducts function exists", "PASS", "Function defined in module")
    else:
        log_test("fetchProducts function exists", "FAIL", "Function not found")
except Exception as e:
    log_test("fetchProducts function exists", "FAIL", str(e))

try:
    # Check if process_card function exists
    if hasattr(autoShopify, 'process_card'):
        log_test("process_card function exists", "PASS", "Function defined in module")
    else:
        log_test("process_card function exists", "FAIL", "Function not found")
except Exception as e:
    log_test("process_card function exists", "FAIL", str(e))

try:
    # Check if verify_shopify_url function exists
    if hasattr(autoShopify, 'verify_shopify_url'):
        log_test("verify_shopify_url function exists", "PASS", "Function defined in module")
    else:
        log_test("verify_shopify_url function exists", "FAIL", "Function not found")
except Exception as e:
    log_test("verify_shopify_url function exists", "FAIL", str(e))

# ============================================================
# TEST 3: Function Signatures
# ============================================================
print("=" * 60)
print("TEST SUITE 3: FUNCTION SIGNATURES")
print("=" * 60)
print()

try:
    import inspect
    
    # Check fetchProducts signature
    sig = inspect.signature(autoShopify.fetchProducts)
    params = list(sig.parameters.keys())
    if 'domain' in params:
        log_test("fetchProducts signature", "PASS", f"Parameters: {params}")
    else:
        log_test("fetchProducts signature", "FAIL", "Missing 'domain' parameter")
except Exception as e:
    log_test("fetchProducts signature", "FAIL", str(e))

try:
    # Check process_card signature
    sig = inspect.signature(autoShopify.process_card)
    params = list(sig.parameters.keys())
    expected = ['ourl', 'variant_id']
    if all(p in params for p in expected):
        log_test("process_card signature", "PASS", f"Parameters: {params}")
    else:
        log_test("process_card signature", "FAIL", f"Missing parameters. Expected: {expected}, Got: {params}")
except Exception as e:
    log_test("process_card signature", "FAIL", str(e))

# ============================================================
# TEST 4: Error Handling (Async Tests)
# ============================================================
print("=" * 60)
print("TEST SUITE 4: ERROR HANDLING")
print("=" * 60)
print()

async def test_error_handling():
    """Test error handling in async functions"""
    
    # Test 1: Invalid domain
    try:
        result = await autoShopify.fetchProducts("invalid-domain-12345.com")
        if isinstance(result, tuple) and result[0] == False:
            log_test("Invalid domain handling", "PASS", f"Correctly returned error: {result[1]}")
        else:
            log_test("Invalid domain handling", "FAIL", "Did not return error tuple")
    except Exception as e:
        log_test("Invalid domain handling", "FAIL", str(e))
    
    # Test 2: Empty domain
    try:
        result = await autoShopify.fetchProducts("")
        if isinstance(result, tuple) and result[0] == False:
            log_test("Empty domain handling", "PASS", f"Correctly returned error: {result[1]}")
        else:
            log_test("Empty domain handling", "FAIL", "Did not return error tuple")
    except Exception as e:
        log_test("Empty domain handling", "FAIL", str(e))
    
    # Test 3: None domain
    try:
        result = await autoShopify.fetchProducts(None)
        if isinstance(result, tuple) and result[0] == False:
            log_test("None domain handling", "PASS", f"Correctly returned error: {result[1]}")
        else:
            log_test("None domain handling", "FAIL", "Did not return error tuple")
    except Exception as e:
        log_test("None domain handling", "FAIL", str(e))

# Run async tests
try:
    asyncio.run(test_error_handling())
except Exception as e:
    log_test("Async error handling tests", "FAIL", str(e))

# ============================================================
# TEST 5: Database Functions
# ============================================================
print("=" * 60)
print("TEST SUITE 5: DATABASE FUNCTIONS")
print("=" * 60)
print()

try:
    # Test database initialization
    init_db()
    log_test("Database initialization", "PASS", "Database initialized successfully")
except Exception as e:
    log_test("Database initialization", "FAIL", str(e))

try:
    # Test user creation
    test_user_id = 999999999
    add_user(test_user_id, "test_user")
    log_test("User creation", "PASS", f"Test user {test_user_id} created")
except Exception as e:
    log_test("User creation", "FAIL", str(e))

try:
    # Test user retrieval
    user = get_user(test_user_id)
    if user:
        log_test("User retrieval", "PASS", f"Retrieved user: {user.username}")
    else:
        log_test("User retrieval", "FAIL", "User not found")
except Exception as e:
    log_test("User retrieval", "FAIL", str(e))

# ============================================================
# TEST 6: Utils Functions
# ============================================================
print("=" * 60)
print("TEST SUITE 6: UTILITY FUNCTIONS")
print("=" * 60)
print()

try:
    # Test random name generation
    first, last = Utils.get_random_name()
    if first and last:
        log_test("Random name generation", "PASS", f"Generated: {first} {last}")
    else:
        log_test("Random name generation", "FAIL", "Empty names returned")
except Exception as e:
    log_test("Random name generation", "FAIL", str(e))

try:
    # Test email generation
    email = Utils.generate_email("John", "Doe")
    if email and '@' in email:
        log_test("Email generation", "PASS", f"Generated: {email}")
    else:
        log_test("Email generation", "FAIL", "Invalid email format")
except Exception as e:
    log_test("Email generation", "FAIL", str(e))

try:
    # Test address generation
    address = Utils.get_formatted_address()
    required_fields = ['street', 'city', 'state', 'zip', 'phone']
    if all(field in address for field in required_fields):
        log_test("Address generation", "PASS", f"Generated address with all fields")
    else:
        log_test("Address generation", "FAIL", f"Missing fields. Got: {address.keys()}")
except Exception as e:
    log_test("Address generation", "FAIL", str(e))

# ============================================================
# TEST 7: File Structure
# ============================================================
print("=" * 60)
print("TEST SUITE 7: FILE STRUCTURE")
print("=" * 60)
print()

required_files = [
    'AutoshBotSRC/AutoshBotSRC/bot.py',
    'AutoshBotSRC/AutoshBotSRC/database.py',
    'AutoshBotSRC/AutoshBotSRC/utils.py',
    'AutoshBotSRC/AutoshBotSRC/gateways/autoShopify.py',
    'AutoshBotSRC/AutoshBotSRC/commands/shopify.py',
    'AutoshBotSRC/AutoshBotSRC/requirements.txt',
]

for file_path in required_files:
    if os.path.exists(file_path):
        log_test(f"File exists: {os.path.basename(file_path)}", "PASS", f"Found at {file_path}")
    else:
        log_test(f"File exists: {os.path.basename(file_path)}", "FAIL", f"Not found at {file_path}")

# ============================================================
# TEST 8: Configuration Validation
# ============================================================
print("=" * 60)
print("TEST SUITE 8: CONFIGURATION VALIDATION")
print("=" * 60)
print()

try:
    # Check if bot.py has token placeholder
    with open('AutoshBotSRC/AutoshBotSRC/bot.py', 'r') as f:
        content = f.read()
        if 'TOKEN' in content:
            log_test("Bot token configuration", "PASS", "TOKEN variable found in bot.py")
        else:
            log_test("Bot token configuration", "FAIL", "TOKEN variable not found")
except Exception as e:
    log_test("Bot token configuration", "FAIL", str(e))

try:
    # Check requirements.txt
    with open('AutoshBotSRC/AutoshBotSRC/requirements.txt', 'r') as f:
        requirements = f.read()
        required_packages = ['aiohttp', 'aiogram', 'SQLAlchemy']
        missing = [pkg for pkg in required_packages if pkg.lower() not in requirements.lower()]
        if not missing:
            log_test("Requirements validation", "PASS", f"All required packages present")
        else:
            log_test("Requirements validation", "FAIL", f"Missing packages: {missing}")
except Exception as e:
    log_test("Requirements validation", "FAIL", str(e))

# ============================================================
# TEST 9: Code Quality Checks
# ============================================================
print("=" * 60)
print("TEST SUITE 9: CODE QUALITY")
print("=" * 60)
print()

try:
    # Check for syntax errors in autoShopify.py
    with open('AutoshBotSRC/AutoshBotSRC/gateways/autoShopify.py', 'r') as f:
        code = f.read()
        compile(code, 'autoShopify.py', 'exec')
        log_test("Syntax validation", "PASS", "No syntax errors in autoShopify.py")
except SyntaxError as e:
    log_test("Syntax validation", "FAIL", f"Syntax error: {e}")
except Exception as e:
    log_test("Syntax validation", "FAIL", str(e))

try:
    # Check for the bug fix (no premature variant reference)
    with open('AutoshBotSRC/AutoshBotSRC/gateways/autoShopify.py', 'r') as f:
        lines = f.readlines()
        # Check that variant is not used before the loop
        bug_found = False
        for i, line in enumerate(lines[20:40], start=20):  # Check lines 20-40
            if 'variant.get' in line or 'variant[' in line:
                # Check if this is before the 'for variant in' loop
                for j in range(i+1, min(i+10, len(lines))):
                    if 'for variant in' in lines[j]:
                        bug_found = True
                        break
                if bug_found:
                    break
        
        if not bug_found:
            log_test("Bug fix verification", "PASS", "No premature variant reference found")
        else:
            log_test("Bug fix verification", "FAIL", "Premature variant reference still exists")
except Exception as e:
    log_test("Bug fix verification", "FAIL", str(e))

# ============================================================
# FINAL SUMMARY
# ============================================================
print("=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print()
print(f"✅ Passed:  {test_results['passed']}")
print(f"❌ Failed:  {test_results['failed']}")
print(f"⏭️  Skipped: {test_results['skipped']}")
print(f"📊 Total:   {test_results['passed'] + test_results['failed'] + test_results['skipped']}")
print()

# Calculate success rate
total_tests = test_results['passed'] + test_results['failed']
if total_tests > 0:
    success_rate = (test_results['passed'] / total_tests) * 100
    print(f"Success Rate: {success_rate:.1f}%")
    print()

# Save results to file
try:
    with open('test_results_comprehensive.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    print("📝 Detailed results saved to: test_results_comprehensive.json")
except Exception as e:
    print(f"⚠️  Could not save results: {e}")

print()
print("=" * 60)
print("TESTING COMPLETE!")
print("=" * 60)

# Exit with appropriate code
sys.exit(0 if test_results['failed'] == 0 else 1)
