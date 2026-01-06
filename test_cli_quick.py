#!/usr/bin/env python3
"""
Quick CLI Interface Test
Tests the CLI with a small sample
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

def test_cli_import():
    """Test CLI import"""
    print("Testing CLI import...")
    try:
        from interfaces.cli import run_cli
        print("  ✓ CLI module imported successfully")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_cli_help():
    """Test CLI help"""
    print("\nTesting CLI help system...")
    try:
        import subprocess
        result = subprocess.run(
            ['python3', 'madystripe.py', 'cli', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("  ✓ CLI help works")
            return True
        else:
            print(f"  ✗ CLI help failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_gateway_list():
    """Test gateway listing"""
    print("\nTesting gateway listing...")
    try:
        import subprocess
        result = subprocess.run(
            ['python3', 'madystripe.py', '--list-gateways'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and 'Staleks' in result.stdout:
            print("  ✓ Gateway listing works")
            print(f"  Found gateways in output")
            return True
        else:
            print(f"  ✗ Gateway listing failed")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_system_info():
    """Test system info"""
    print("\nTesting system info...")
    try:
        import subprocess
        result = subprocess.run(
            ['python3', 'madystripe.py', '--info'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and 'MadyStripe' in result.stdout:
            print("  ✓ System info works")
            return True
        else:
            print(f"  ✗ System info failed")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    print("="*60)
    print("QUICK CLI INTERFACE TEST")
    print("="*60)
    
    tests = [
        ("CLI Import", test_cli_import),
        ("CLI Help", test_cli_help),
        ("Gateway List", test_gateway_list),
        ("System Info", test_system_info),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ Test crashed: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL CLI TESTS PASSED!")
    else:
        print("✗ SOME CLI TESTS FAILED")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
