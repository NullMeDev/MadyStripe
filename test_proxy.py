"""Test proxy connectivity"""
import requests

print("Testing proxy...")
print("="*70)

# Parse proxy
proxy_line = "user_pinta:1acNvmOToR6d-country-US-state-Washington-city-Benton@residential.ip9.io:8000"
parts = proxy_line.split('@')
auth = parts[0]
host_port = parts[1]

proxy_url = f"http://{auth}@{host_port}"

proxies = {
    'http': proxy_url,
    'https': proxy_url
}

print(f"Proxy: {host_port}")
print(f"Testing connection...\n")

try:
    # Test with httpbin
    response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Proxy works!")
        print(f"   Your IP through proxy: {data.get('origin')}")
        print(f"   Status: Connected")
    else:
        print(f"❌ Proxy returned status {response.status_code}")
        
except requests.exceptions.ProxyError as e:
    print(f"❌ Proxy error: {e}")
except requests.exceptions.Timeout:
    print(f"❌ Proxy timeout - connection too slow")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*70)
