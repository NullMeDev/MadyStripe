#!/usr/bin/env python3
"""
MadyStripe Rate Limiter Module
Per-user rate limiting for API abuse prevention
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict
import threading

class RateLimiter:
    """
    Rate limiter with configurable limits per user tier
    
    Limits:
    - Free users: 10 checks/hour, 50 checks/day
    - Premium users: 100 checks/hour, 500 checks/day
    - Admin/Owner: Unlimited
    """
    
    # Default limits per tier
    LIMITS = {
        'free': {
            'hourly': 10,
            'daily': 50,
            'burst': 3,  # Max concurrent requests
            'cooldown': 5  # Seconds between requests
        },
        'premium': {
            'hourly': 100,
            'daily': 500,
            'burst': 10,
            'cooldown': 1
        },
        'admin': {
            'hourly': float('inf'),
            'daily': float('inf'),
            'burst': float('inf'),
            'cooldown': 0
        },
        'owner': {
            'hourly': float('inf'),
            'daily': float('inf'),
            'burst': float('inf'),
            'cooldown': 0
        }
    }
    
    def __init__(self):
        self._hourly_counts: Dict[int, list] = defaultdict(list)
        self._daily_counts: Dict[int, list] = defaultdict(list)
        self._last_request: Dict[int, float] = {}
        self._active_requests: Dict[int, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def _clean_old_entries(self, user_id: int):
        """Remove expired entries from tracking"""
        now = time.time()
        hour_ago = now - 3600
        day_ago = now - 86400
        
        # Clean hourly
        self._hourly_counts[user_id] = [
            t for t in self._hourly_counts[user_id] if t > hour_ago
        ]
        
        # Clean daily
        self._daily_counts[user_id] = [
            t for t in self._daily_counts[user_id] if t > day_ago
        ]
    
    def check_limit(self, user_id: int, tier: str = 'free') -> Tuple[bool, str]:
        """
        Check if user can make a request
        
        Returns:
            (allowed: bool, message: str)
        """
        with self._lock:
            self._clean_old_entries(user_id)
            
            limits = self.LIMITS.get(tier, self.LIMITS['free'])
            
            # Check cooldown
            if user_id in self._last_request:
                elapsed = time.time() - self._last_request[user_id]
                if elapsed < limits['cooldown']:
                    wait_time = limits['cooldown'] - elapsed
                    return False, f"⏳ Please wait {wait_time:.1f}s before next check"
            
            # Check burst limit
            if self._active_requests[user_id] >= limits['burst']:
                return False, "⚠️ Too many concurrent requests. Please wait."
            
            # Check hourly limit
            hourly_count = len(self._hourly_counts[user_id])
            if hourly_count >= limits['hourly']:
                return False, f"⏰ Hourly limit reached ({limits['hourly']} checks/hour)"
            
            # Check daily limit
            daily_count = len(self._daily_counts[user_id])
            if daily_count >= limits['daily']:
                return False, f"📅 Daily limit reached ({limits['daily']} checks/day)"
            
            return True, "OK"
    
    def record_request(self, user_id: int):
        """Record a request for rate limiting"""
        with self._lock:
            now = time.time()
            self._hourly_counts[user_id].append(now)
            self._daily_counts[user_id].append(now)
            self._last_request[user_id] = now
    
    def start_request(self, user_id: int):
        """Mark start of a request (for burst limiting)"""
        with self._lock:
            self._active_requests[user_id] += 1
    
    def end_request(self, user_id: int):
        """Mark end of a request"""
        with self._lock:
            if self._active_requests[user_id] > 0:
                self._active_requests[user_id] -= 1
    
    def get_usage(self, user_id: int, tier: str = 'free') -> Dict:
        """Get current usage statistics for user"""
        with self._lock:
            self._clean_old_entries(user_id)
            
            limits = self.LIMITS.get(tier, self.LIMITS['free'])
            hourly_count = len(self._hourly_counts[user_id])
            daily_count = len(self._daily_counts[user_id])
            
            return {
                'hourly_used': hourly_count,
                'hourly_limit': limits['hourly'],
                'hourly_remaining': max(0, limits['hourly'] - hourly_count),
                'daily_used': daily_count,
                'daily_limit': limits['daily'],
                'daily_remaining': max(0, limits['daily'] - daily_count),
                'tier': tier
            }
    
    def reset_user(self, user_id: int):
        """Reset all limits for a user (admin function)"""
        with self._lock:
            self._hourly_counts[user_id] = []
            self._daily_counts[user_id] = []
            self._last_request.pop(user_id, None)
            self._active_requests[user_id] = 0
    
    def get_wait_time(self, user_id: int, tier: str = 'free') -> Optional[float]:
        """Get time until user can make next request"""
        with self._lock:
            self._clean_old_entries(user_id)
            
            limits = self.LIMITS.get(tier, self.LIMITS['free'])
            
            # Check cooldown
            if user_id in self._last_request:
                elapsed = time.time() - self._last_request[user_id]
                if elapsed < limits['cooldown']:
                    return limits['cooldown'] - elapsed
            
            # Check hourly limit
            hourly_count = len(self._hourly_counts[user_id])
            if hourly_count >= limits['hourly']:
                # Find oldest entry and calculate when it expires
                oldest = min(self._hourly_counts[user_id])
                return (oldest + 3600) - time.time()
            
            # Check daily limit
            daily_count = len(self._daily_counts[user_id])
            if daily_count >= limits['daily']:
                oldest = min(self._daily_counts[user_id])
                return (oldest + 86400) - time.time()
            
            return None


class TokenBucket:
    """
    Token bucket rate limiter for more granular control
    Allows burst traffic while maintaining average rate
    """
    
    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: Tokens added per second
            capacity: Maximum tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self._tokens: Dict[int, float] = {}
        self._last_update: Dict[int, float] = {}
        self._lock = threading.Lock()
    
    def _refill(self, user_id: int):
        """Refill tokens based on elapsed time"""
        now = time.time()
        
        if user_id not in self._tokens:
            self._tokens[user_id] = self.capacity
            self._last_update[user_id] = now
            return
        
        elapsed = now - self._last_update[user_id]
        self._tokens[user_id] = min(
            self.capacity,
            self._tokens[user_id] + elapsed * self.rate
        )
        self._last_update[user_id] = now
    
    def consume(self, user_id: int, tokens: int = 1) -> bool:
        """
        Try to consume tokens
        Returns True if successful, False if not enough tokens
        """
        with self._lock:
            self._refill(user_id)
            
            if self._tokens[user_id] >= tokens:
                self._tokens[user_id] -= tokens
                return True
            return False
    
    def get_tokens(self, user_id: int) -> float:
        """Get current token count for user"""
        with self._lock:
            self._refill(user_id)
            return self._tokens[user_id]
    
    def wait_time(self, user_id: int, tokens: int = 1) -> float:
        """Calculate wait time until tokens are available"""
        with self._lock:
            self._refill(user_id)
            
            if self._tokens[user_id] >= tokens:
                return 0
            
            needed = tokens - self._tokens[user_id]
            return needed / self.rate


# Singleton instance
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """Get rate limiter singleton instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


# Decorator for rate limiting
def rate_limited(tier_func=None):
    """
    Decorator to apply rate limiting to functions
    
    Usage:
        @rate_limited(lambda user_id: get_user_tier(user_id))
        async def check_card(user_id, card):
            ...
    """
    def decorator(func):
        async def wrapper(user_id, *args, **kwargs):
            limiter = get_rate_limiter()
            
            # Get tier
            tier = 'free'
            if tier_func:
                tier = tier_func(user_id)
            
            # Check limit
            allowed, message = limiter.check_limit(user_id, tier)
            if not allowed:
                raise RateLimitExceeded(message)
            
            # Record and execute
            limiter.start_request(user_id)
            try:
                result = await func(user_id, *args, **kwargs)
                limiter.record_request(user_id)
                return result
            finally:
                limiter.end_request(user_id)
        
        return wrapper
    return decorator


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass
