#!/usr/bin/env python3
"""
Test Bot - Debug version
"""

import requests
import time

# Bot Configuration
BOT_TOKEN = "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
GROUP_ID = "-1003538559040"

def test_bot_connection():
    """Test if bot token is valid"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print(f"✅ Bot connected successfully!")
                print(f"Bot username: @{bot_info.get('username', 'Unknown')}")
                print(f"Bot name: {bot_info.get('first_name', 'Unknown')}")
                return True
            else:
                print(f"❌ Bot error: {data.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def send_test_message():
    """Send a test message to the group"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': GROUP_ID,
        'text': '🤖 Mady Bot Test Message\n\nBot is working!',
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print(f"✅ Test message sent to group!")
                return True
            else:
                print(f"❌ Failed to send: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Send error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Testing Mady Bot Connection...")
    print("=" * 50)
    
    if test_bot_connection():
        print("\nSending test message to group...")
        send_test_message()
    else:
        print("\n❌ Bot connection failed. Check the token.")
    
    print("=" * 50)
