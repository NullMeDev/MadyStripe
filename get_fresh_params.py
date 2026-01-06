#!/usr/bin/env python3
"""
Get fresh parameters from ccfoundationorg.com
"""

import requests
from bs4 import BeautifulSoup
import re
import json

print("="*60)
print("FETCHING FRESH PARAMETERS FROM CCFOUNDATIONORG.COM")
print("="*60)

try:
    # Step 1: Get the donation page
    print("\n1. Fetching donation page...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    response = requests.get('https://ccfoundationorg.com/donate/', headers=headers, timeout=15)
    
    if response.status_code == 200:
        print(f"   ✓ Page fetched (Status: {response.status_code})")
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the donation form
        print("\n2. Searching for donation form parameters...")
        
        # Find nonce
        nonce_input = soup.find('input', {'name': '_charitable_donation_nonce'})
        if nonce_input:
            nonce = nonce_input.get('value', '')
            print(f"   ✓ Nonce found: {nonce}")
        else:
            print("   ✗ Nonce not found")
            nonce = None
            
        # Find form ID
        form_id_input = soup.find('input', {'name': 'charitable_form_id'})
        if form_id_input:
            form_id = form_id_input.get('value', '')
            print(f"   ✓ Form ID found: {form_id}")
        else:
            print("   ✗ Form ID not found")
            form_id = None
            
        # Find campaign ID
        campaign_input = soup.find('input', {'name': 'campaign_id'})
        if campaign_input:
            campaign_id = campaign_input.get('value', '')
            print(f"   ✓ Campaign ID found: {campaign_id}")
        else:
            print("   ✗ Campaign ID not found")
            campaign_id = None
            
        # Find Stripe publishable key
        stripe_key = None
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for Stripe key patterns
                pk_match = re.search(r'pk_live_[a-zA-Z0-9]+', script.string)
                if pk_match:
                    stripe_key = pk_match.group(0)
                    print(f"   ✓ Stripe key found: {stripe_key[:20]}...")
                    break
                    
        if not stripe_key:
            # Try in inline scripts
            for script in soup.find_all('script', string=True):
                text = script.string
                if 'pk_live_' in text:
                    pk_match = re.search(r'pk_live_[a-zA-Z0-9]+', text)
                    if pk_match:
                        stripe_key = pk_match.group(0)
                        print(f"   ✓ Stripe key found: {stripe_key[:20]}...")
                        break
        
        # Get cookies
        print("\n3. Cookies from response:")
        for cookie_name, cookie_value in response.cookies.items():
            print(f"   - {cookie_name}: {cookie_value[:30]}...")
            
        # Generate updated code
        print("\n" + "="*60)
        print("UPDATED PARAMETERS FOR CHARGE5.PY:")
        print("="*60)
        
        if nonce:
            print(f"\n# Update these in Charge5.py:")
            print(f"'_charitable_donation_nonce': '{nonce}',")
        if form_id:
            print(f"'charitable_form_id': '{form_id}',")
            print(f"'{form_id}': '',")
        if campaign_id:
            print(f"'campaign_id': '{campaign_id}',")
        if stripe_key:
            print(f"\n# Stripe key:")
            print(f"key = '{stripe_key}'")
            
        # Check if the form uses any JavaScript to generate additional parameters
        print("\n4. Checking for JavaScript-generated parameters...")
        
        # Look for AJAX endpoints
        ajax_endpoints = []
        for script in scripts:
            if script.string:
                if 'admin-ajax.php' in script.string:
                    print("   ✓ AJAX endpoint confirmed: wp-admin/admin-ajax.php")
                if 'make_donation' in script.string:
                    print("   ✓ Action confirmed: make_donation")
                    
    else:
        print(f"   ✗ Failed to fetch page (Status: {response.status_code})")
        
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("PARAMETER FETCH COMPLETE")
print("="*60)
