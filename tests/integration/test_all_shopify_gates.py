#!/usr/bin/env python3
"""
Test all Shopify price gates ($5, $20, $100)
Generate comprehensive report
"""

import subprocess
import time
import sys

def run_gate_test(gate_name, gate_flag, num_cards=10):
    """Run VPS checker with specific gate"""
    print(f"\n{'='*70}")
    print(f"Testing {gate_name}")
    print(f"{'='*70}\n")
    
    cmd = [
        'python3', 'mady_vps_checker.py',
        'cards.txt',
        '--gate', gate_flag,
        '--limit', str(num_cards),
        '--threads', '5'
    ]
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        elapsed = time.time() - start_time
        
        # Parse results
        output = result.stdout
        
        # Extract key metrics
        approved = output.count('✅ APPROVED')
        declined = output.count('❌ DECLINED') + output.count('❌ [')
        errors = output.count('⚠️')
        
        # Extract final stats if available
        if 'FINAL RESULTS:' in output:
            lines = output.split('\n')
            for i, line in enumerate(lines):
                if 'FINAL RESULTS:' in line:
                    # Get next few lines
                    stats_section = '\n'.join(lines[i:i+10])
                    break
        
        print(f"\n📊 {gate_name} Results:")
        print(f"   ✅ Approved: {approved}")
        print(f"   ❌ Declined/Failed: {declined}")
        print(f"   ⚠️ Errors: {errors}")
        print(f"   ⏱️ Time: {elapsed:.1f}s")
        print(f"   🚀 Speed: {num_cards/elapsed:.2f} cards/sec")
        
        return {
            'gate': gate_name,
            'approved': approved,
            'declined': declined,
            'errors': errors,
            'time': elapsed,
            'success': approved > 0
        }
        
    except subprocess.TimeoutExpired:
        print(f"❌ {gate_name} test timed out after 120s")
        return {
            'gate': gate_name,
            'approved': 0,
            'declined': 0,
            'errors': 1,
            'time': 120,
            'success': False
        }
    except Exception as e:
        print(f"❌ {gate_name} test failed: {e}")
        return {
            'gate': gate_name,
            'approved': 0,
            'declined': 0,
            'errors': 1,
            'time': 0,
            'success': False
        }

def main():
    print("="*70)
    print("SHOPIFY GATES COMPREHENSIVE TEST")
    print("Testing $5, $20, and $100 gates")
    print("="*70)
    
    gates_to_test = [
        ('$5 Gate', 'low'),
        ('$20 Gate', 'medium'),
        ('$100 Gate', 'high')
    ]
    
    results = []
    
    for gate_name, gate_flag in gates_to_test:
        result = run_gate_test(gate_name, gate_flag, num_cards=10)
        results.append(result)
        time.sleep(2)  # Brief pause between tests
    
    # Generate summary report
    print(f"\n\n{'='*70}")
    print("COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*70}\n")
    
    total_approved = sum(r['approved'] for r in results)
    total_declined = sum(r['declined'] for r in results)
    total_errors = sum(r['errors'] for r in results)
    total_time = sum(r['time'] for r in results)
    
    print("Individual Gate Results:")
    print("-" * 70)
    for r in results:
        status = "✅ WORKING" if r['success'] else "❌ FAILED"
        print(f"{r['gate']:15} {status:15} | Approved: {r['approved']:2} | Time: {r['time']:.1f}s")
    
    print(f"\n{'-'*70}")
    print(f"Overall Statistics:")
    print(f"  Total Cards Tested: 30 (10 per gate)")
    print(f"  Total Approved: {total_approved}")
    print(f"  Total Declined: {total_declined}")
    print(f"  Total Errors: {total_errors}")
    print(f"  Total Time: {total_time:.1f}s")
    print(f"  Average Speed: {30/total_time:.2f} cards/sec")
    
    working_gates = sum(1 for r in results if r['success'])
    print(f"\n  Working Gates: {working_gates}/3")
    
    if working_gates == 3:
        print("\n🎉 ALL SHOPIFY GATES WORKING!")
    elif working_gates > 0:
        print(f"\n⚠️ {working_gates} out of 3 gates working")
    else:
        print("\n❌ No gates working - needs investigation")
    
    print(f"\n{'='*70}\n")

if __name__ == '__main__':
    main()
