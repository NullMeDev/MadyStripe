"""
Card Checker Core - Unified card checking logic
"""

import time
import threading
from typing import List, Dict, Optional, Callable, Tuple
from collections import deque
from datetime import datetime
from .gateways import get_gateway_manager


class CardResult:
    """Represents the result of a card check"""
    
    def __init__(self, card: str, status: str, message: str, card_type: str, gateway: str, timestamp: float = None):
        self.card = card
        self.status = status  # 'approved', 'declined', 'error'
        self.message = message
        self.card_type = card_type  # '2D', '3D', '3DS'
        self.gateway = gateway
        self.timestamp = timestamp or time.time()
    
    def is_approved(self) -> bool:
        """Check if card was approved"""
        return self.status == 'approved'
    
    def is_live(self) -> bool:
        """Check if card is live (approved or CVV/insufficient funds)"""
        msg_lower = self.message.lower()
        return (self.status == 'approved' or 
                'cvv' in msg_lower or 
                'cvc' in msg_lower or 
                'insufficient' in msg_lower)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'card': self.card,
            'status': self.status,
            'message': self.message,
            'card_type': self.card_type,
            'gateway': self.gateway,
            'timestamp': self.timestamp,
        }
    
    def __str__(self) -> str:
        return f"{self.card} | {self.status.upper()} | {self.message} | {self.card_type} | {self.gateway}"


class CheckerStats:
    """Statistics tracker for card checking"""
    
    def __init__(self):
        self.total = 0
        self.checked = 0
        self.approved = 0
        self.declined = 0
        self.errors = 0
        self.cvv_mismatch = 0
        self.insufficient_funds = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.results: deque = deque(maxlen=1000)  # Keep last 1000 results
    
    def add_result(self, result: CardResult):
        """Add a result and update stats"""
        with self.lock:
            self.checked += 1
            self.results.append(result)
            
            if result.status == 'approved':
                self.approved += 1
                
                # Check for special cases
                msg_lower = result.message.lower()
                if 'cvv' in msg_lower or 'cvc' in msg_lower:
                    self.cvv_mismatch += 1
                elif 'insufficient' in msg_lower:
                    self.insufficient_funds += 1
                    
            elif result.status == 'error':
                self.errors += 1
            else:
                self.declined += 1
    
    def get_success_rate(self) -> float:
        """Get success rate percentage"""
        with self.lock:
            if self.checked == 0:
                return 0.0
            return (self.approved / self.checked) * 100
    
    def get_live_rate(self) -> float:
        """Get live card rate (approved + CVV + insufficient)"""
        with self.lock:
            if self.checked == 0:
                return 0.0
            live = self.approved + self.cvv_mismatch + self.insufficient_funds
            return (live / self.checked) * 100
    
    def get_speed(self) -> float:
        """Get cards per second"""
        with self.lock:
            elapsed = time.time() - self.start_time
            if elapsed == 0:
                return 0.0
            return self.checked / elapsed
    
    def get_elapsed(self) -> float:
        """Get elapsed time in seconds"""
        return time.time() - self.start_time
    
    def get_eta(self) -> float:
        """Get estimated time remaining in seconds"""
        with self.lock:
            if self.checked == 0 or self.total == 0:
                return 0.0
            
            remaining = self.total - self.checked
            speed = self.get_speed()
            
            if speed == 0:
                return 0.0
            
            return remaining / speed
    
    def get_approved_cards(self, limit: int = None) -> List[CardResult]:
        """Get list of approved cards"""
        with self.lock:
            approved = [r for r in self.results if r.is_approved()]
            if limit:
                return approved[-limit:]
            return approved
    
    def get_live_cards(self, limit: int = None) -> List[CardResult]:
        """Get list of live cards (approved + CVV + insufficient)"""
        with self.lock:
            live = [r for r in self.results if r.is_live()]
            if limit:
                return live[-limit:]
            return live
    
    def to_dict(self) -> Dict:
        """Convert stats to dictionary"""
        with self.lock:
            return {
                'total': self.total,
                'checked': self.checked,
                'approved': self.approved,
                'declined': self.declined,
                'errors': self.errors,
                'cvv_mismatch': self.cvv_mismatch,
                'insufficient_funds': self.insufficient_funds,
                'success_rate': self.get_success_rate(),
                'live_rate': self.get_live_rate(),
                'speed': self.get_speed(),
                'elapsed': self.get_elapsed(),
                'eta': self.get_eta(),
            }


class CardChecker:
    """Main card checker class"""
    
    def __init__(self, gateway_id: str = None, proxy: str = None, rate_limit: float = 0.5):
        """
        Initialize card checker
        
        Args:
            gateway_id: Gateway to use (None for default)
            proxy: Proxy string (optional)
            rate_limit: Delay between checks in seconds
        """
        self.gateway_id = gateway_id
        self.proxy = proxy
        self.rate_limit = rate_limit
        self.gateway_manager = get_gateway_manager()
        self.stats = CheckerStats()
        self.stop_flag = False
        self.current_card = None
        self.callbacks = []
    
    def add_callback(self, callback: Callable[[CardResult], None]):
        """Add a callback function to be called after each check"""
        self.callbacks.append(callback)
    
    def check_single(self, card: str) -> CardResult:
        """Check a single card"""
        self.current_card = card
        
        # Check card through gateway
        status, message, card_type, gateway_name = self.gateway_manager.check_card(
            card, self.gateway_id, self.proxy
        )
        
        # Create result
        result = CardResult(card, status, message, card_type, gateway_name)
        
        # Update stats
        self.stats.add_result(result)
        
        # Call callbacks
        for callback in self.callbacks:
            try:
                callback(result)
            except:
                pass
        
        return result
    
    def check_batch(self, cards: List[str], progress_callback: Callable[[int, int], None] = None) -> List[CardResult]:
        """
        Check a batch of cards sequentially
        
        Args:
            cards: List of card strings
            progress_callback: Optional callback(current, total)
        
        Returns:
            List of CardResult objects
        """
        self.stats.total = len(cards)
        self.stats.checked = 0
        self.stop_flag = False
        results = []
        
        for i, card in enumerate(cards, 1):
            if self.stop_flag:
                break
            
            result = self.check_single(card)
            results.append(result)
            
            if progress_callback:
                progress_callback(i, len(cards))
            
            # Rate limiting
            if i < len(cards):  # Don't sleep after last card
                time.sleep(self.rate_limit)
        
        return results
    
    def stop(self):
        """Stop the current checking process"""
        self.stop_flag = True
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = CheckerStats()


def validate_card_format(card: str) -> Tuple[bool, str]:
    """
    Validate card format
    
    Args:
        card: Card string
    
    Returns:
        (is_valid, error_message)
    """
    card = card.strip()
    
    if not card:
        return False, "Empty card"
    
    if '|' not in card:
        return False, "Invalid format (use NUMBER|MM|YY|CVC)"
    
    parts = card.split('|')
    
    if len(parts) != 4:
        return False, f"Invalid format (expected 4 parts, got {len(parts)})"
    
    number, mm, yy, cvc = parts
    
    # Validate number
    number = number.replace(' ', '')
    if not number.isdigit():
        return False, "Card number must be numeric"
    
    if len(number) < 13 or len(number) > 19:
        return False, f"Invalid card number length ({len(number)})"
    
    # Validate month
    if not mm.isdigit():
        return False, "Month must be numeric"
    
    mm_int = int(mm)
    if mm_int < 1 or mm_int > 12:
        return False, f"Invalid month ({mm_int})"
    
    # Validate year
    if not yy.isdigit():
        return False, "Year must be numeric"
    
    if len(yy) not in [2, 4]:
        return False, f"Invalid year length ({len(yy)})"
    
    # Validate CVC
    if not cvc.isdigit():
        return False, "CVC must be numeric"
    
    if len(cvc) < 3 or len(cvc) > 4:
        return False, f"Invalid CVC length ({len(cvc)})"
    
    return True, ""


def load_cards_from_file(filepath: str, limit: int = None) -> Tuple[List[str], List[str]]:
    """
    Load cards from a file
    
    Args:
        filepath: Path to file
        limit: Maximum number of cards to load
    
    Returns:
        (valid_cards, invalid_cards)
    """
    valid_cards = []
    invalid_cards = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                is_valid, error = validate_card_format(line)
                
                if is_valid:
                    valid_cards.append(line)
                    if limit and len(valid_cards) >= limit:
                        break
                else:
                    invalid_cards.append(line)
    
    except Exception as e:
        raise Exception(f"Error loading file: {e}")
    
    return valid_cards, invalid_cards


def save_results(results: List[CardResult], filepath: str, format: str = 'txt'):
    """
    Save results to file
    
    Args:
        results: List of CardResult objects
        filepath: Output file path
        format: Output format ('txt', 'json', 'csv')
    """
    if format == 'json':
        import json
        with open(filepath, 'w') as f:
            json.dump([r.to_dict() for r in results], f, indent=2)
    
    elif format == 'csv':
        with open(filepath, 'w') as f:
            f.write("Card,Status,Message,CardType,Gateway,Timestamp\n")
            for r in results:
                f.write(f'"{r.card}","{r.status}","{r.message}","{r.card_type}","{r.gateway}",{r.timestamp}\n')
    
    else:  # txt
        with open(filepath, 'w') as f:
            for r in results:
                f.write(f"{r}\n")


if __name__ == "__main__":
    # Test
    print("="*60)
    print("CARD CHECKER TEST")
    print("="*60)
    
    # Test card validation
    test_cards = [
        "4532123456789012|12|25|123",
        "invalid",
        "1234|12|25",
        "4532123456789012|13|25|123",
    ]
    
    print("\nCard Validation:")
    for card in test_cards:
        valid, error = validate_card_format(card)
        status = "✓" if valid else "✗"
        print(f"  {status} {card[:20]}... - {error if error else 'Valid'}")
