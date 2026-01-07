#!/usr/bin/env python3
"""
Test Telegram posting functionality
"""

import requests

BOT_TOKEN = "7984658748:AAFPFDQH3hOjK0ZLMz0zxn0V-iNB4AZNhCc"
GROUP_ID = "-1003538559040"

def test_telegram():
    """Test sending a message to Telegram"""
    
    print("="*60)
    print("TELEGRAM POSTING TEST")
    print("="*60)
    print(f"\nBot Token: {BOT_TOKEN[:20]}...")
    print(f"Group ID: {GROUP_ID}")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    message = """
🧪 <b>TEST MESSAGE</b>

This is a test message from the VPS Checker.

If you see this, Telegram posting is working! ✅

<b>Bot:</b> @MissNullMe
"""
    
    data = {
        'chat_id': GROUP_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_notification': False
    }
    
    print("\nSending test message...")
    
    try:
        response = requests.post(url, data=data, timeout=10)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS! Message posted to Telegram!")
            print("Check your Telegram group to confirm.")
        else:
            print(f"\n❌ FAILED! Status code: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_telegram()
