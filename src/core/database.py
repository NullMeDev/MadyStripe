#!/usr/bin/env python3
"""
MadyStripe Database Module
SQLite database for user management, analytics, and check history
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import threading
import hashlib
import secrets

class Database:
    """SQLite database handler for MadyStripe"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, 'data', 'madystripe.db')
        
        self.db_path = db_path
        self._local = threading.local()
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    def _init_db(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                role TEXT DEFAULT 'free',
                premium_until DATETIME,
                total_checks INTEGER DEFAULT 0,
                approved_checks INTEGER DEFAULT 0,
                declined_checks INTEGER DEFAULT 0,
                daily_checks INTEGER DEFAULT 0,
                last_check_date DATE,
                is_banned INTEGER DEFAULT 0,
                ban_until DATETIME,
                ban_reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Premium codes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS premium_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                days INTEGER NOT NULL,
                max_uses INTEGER DEFAULT 1,
                current_uses INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Code redemptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_redemptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code_id INTEGER,
                user_id INTEGER,
                redeemed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (code_id) REFERENCES premium_codes(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Check history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS check_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                card_bin TEXT,
                card_last4 TEXT,
                gateway TEXT,
                result TEXT,
                card_type TEXT,
                response_message TEXT,
                checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Rate limits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                count INTEGER DEFAULT 0,
                window_start DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, action)
            )
        ''')
        
        # Admin actions log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                target_user_id INTEGER,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bot settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
    
    # ==================== User Management ====================
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def create_user(self, telegram_id: int, username: str = None) -> Dict:
        """Create new user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (telegram_id, username, role, created_at, updated_at)
                VALUES (?, ?, 'free', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (telegram_id, username))
            conn.commit()
            return self.get_user(telegram_id)
        except sqlite3.IntegrityError:
            # User already exists
            return self.get_user(telegram_id)
    
    def get_or_create_user(self, telegram_id: int, username: str = None) -> Dict:
        """Get existing user or create new one"""
        user = self.get_user(telegram_id)
        if user is None:
            user = self.create_user(telegram_id, username)
        elif username and user.get('username') != username:
            # Update username if changed
            self.update_user(telegram_id, username=username)
            user = self.get_user(telegram_id)
        return user
    
    def update_user(self, telegram_id: int, **kwargs) -> bool:
        """Update user fields"""
        if not kwargs:
            return False
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Build update query
        fields = ', '.join([f'{k} = ?' for k in kwargs.keys()])
        values = list(kwargs.values()) + [telegram_id]
        
        cursor.execute(f'''
            UPDATE users SET {fields}, updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
        ''', values)
        conn.commit()
        return cursor.rowcount > 0
    
    def is_premium(self, telegram_id: int) -> bool:
        """Check if user has active premium"""
        user = self.get_user(telegram_id)
        if not user:
            return False
        
        if user['role'] in ('owner', 'admin'):
            return True
        
        if user['premium_until']:
            premium_until = datetime.fromisoformat(user['premium_until'])
            return premium_until > datetime.now()
        
        return False
    
    def is_admin(self, telegram_id: int) -> bool:
        """Check if user is admin or owner"""
        user = self.get_user(telegram_id)
        return user and user['role'] in ('owner', 'admin')
    
    def is_owner(self, telegram_id: int) -> bool:
        """Check if user is owner"""
        user = self.get_user(telegram_id)
        return user and user['role'] == 'owner'
    
    def is_banned(self, telegram_id: int) -> bool:
        """Check if user is banned"""
        user = self.get_user(telegram_id)
        if not user or not user['is_banned']:
            return False
        
        if user['ban_until']:
            ban_until = datetime.fromisoformat(user['ban_until'])
            if ban_until <= datetime.now():
                # Ban expired, unban user
                self.unban_user(telegram_id)
                return False
        
        return True
    
    def ban_user(self, telegram_id: int, duration: str = None, reason: str = None) -> bool:
        """Ban a user"""
        ban_until = None
        if duration:
            duration_map = {
                '1hour': timedelta(hours=1),
                '1day': timedelta(days=1),
                '2days': timedelta(days=2),
                '1week': timedelta(weeks=1),
                '1month': timedelta(days=30),
                '1year': timedelta(days=365),
                'permanent': None
            }
            delta = duration_map.get(duration)
            if delta:
                ban_until = (datetime.now() + delta).isoformat()
        
        return self.update_user(
            telegram_id,
            is_banned=1,
            ban_until=ban_until,
            ban_reason=reason
        )
    
    def unban_user(self, telegram_id: int) -> bool:
        """Unban a user"""
        return self.update_user(
            telegram_id,
            is_banned=0,
            ban_until=None,
            ban_reason=None
        )
    
    def set_premium(self, telegram_id: int, days: int) -> bool:
        """Set premium status for user"""
        user = self.get_user(telegram_id)
        if not user:
            return False
        
        # Calculate new premium end date
        current_premium = None
        if user['premium_until']:
            current_premium = datetime.fromisoformat(user['premium_until'])
        
        if current_premium and current_premium > datetime.now():
            # Extend existing premium
            new_premium = current_premium + timedelta(days=days)
        else:
            # New premium
            new_premium = datetime.now() + timedelta(days=days)
        
        return self.update_user(
            telegram_id,
            premium_until=new_premium.isoformat(),
            role='premium' if user['role'] == 'free' else user['role']
        )
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all users with pagination"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?
        ''', (limit, offset))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_user_count(self) -> int:
        """Get total user count"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        return cursor.fetchone()[0]
    
    def get_premium_user_count(self) -> int:
        """Get premium user count"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE premium_until > CURRENT_TIMESTAMP OR role IN ('owner', 'admin')
        ''')
        return cursor.fetchone()[0]
    
    # ==================== Premium Codes ====================
    
    def generate_code(self, days: int, max_uses: int = 1, created_by: int = None, 
                      expires_days: int = 30) -> str:
        """Generate a premium code"""
        code = secrets.token_urlsafe(12).upper()[:16]
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO premium_codes (code, days, max_uses, created_by, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (code, days, max_uses, created_by, expires_at))
        conn.commit()
        
        return code
    
    def redeem_code(self, code: str, telegram_id: int) -> tuple:
        """
        Redeem a premium code
        Returns: (success: bool, message: str, days: int)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get code
        cursor.execute('SELECT * FROM premium_codes WHERE code = ?', (code,))
        code_row = cursor.fetchone()
        
        if not code_row:
            return False, "Invalid code", 0
        
        code_data = dict(code_row)
        
        if not code_data['is_active']:
            return False, "Code is no longer active", 0
        
        if code_data['current_uses'] >= code_data['max_uses']:
            return False, "Code has reached maximum uses", 0
        
        if code_data['expires_at']:
            expires_at = datetime.fromisoformat(code_data['expires_at'])
            if expires_at <= datetime.now():
                return False, "Code has expired", 0
        
        # Check if user already redeemed this code
        user = self.get_or_create_user(telegram_id)
        cursor.execute('''
            SELECT * FROM code_redemptions 
            WHERE code_id = ? AND user_id = ?
        ''', (code_data['id'], user['id']))
        
        if cursor.fetchone():
            return False, "You have already redeemed this code", 0
        
        # Redeem the code
        cursor.execute('''
            UPDATE premium_codes SET current_uses = current_uses + 1 WHERE id = ?
        ''', (code_data['id'],))
        
        cursor.execute('''
            INSERT INTO code_redemptions (code_id, user_id) VALUES (?, ?)
        ''', (code_data['id'], user['id']))
        
        conn.commit()
        
        # Apply premium
        self.set_premium(telegram_id, code_data['days'])
        
        return True, f"Successfully redeemed {code_data['days']} days of premium!", code_data['days']
    
    def get_code_info(self, code: str) -> Optional[Dict]:
        """Get code information"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM premium_codes WHERE code = ?', (code,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # ==================== Check History ====================
    
    def log_check(self, telegram_id: int, card_bin: str, card_last4: str,
                  gateway: str, result: str, card_type: str = None,
                  response_message: str = None) -> int:
        """Log a card check"""
        user = self.get_or_create_user(telegram_id)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO check_history 
            (user_id, card_bin, card_last4, gateway, result, card_type, response_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user['id'], card_bin, card_last4, gateway, result, card_type, response_message))
        conn.commit()
        
        # Update user stats
        today = datetime.now().date().isoformat()
        
        if user['last_check_date'] != today:
            # Reset daily counter
            self.update_user(telegram_id, daily_checks=1, last_check_date=today)
        else:
            cursor.execute('''
                UPDATE users SET daily_checks = daily_checks + 1 WHERE telegram_id = ?
            ''', (telegram_id,))
        
        # Update total stats
        if result == 'approved':
            cursor.execute('''
                UPDATE users SET total_checks = total_checks + 1, 
                approved_checks = approved_checks + 1 WHERE telegram_id = ?
            ''', (telegram_id,))
        elif result == 'declined':
            cursor.execute('''
                UPDATE users SET total_checks = total_checks + 1,
                declined_checks = declined_checks + 1 WHERE telegram_id = ?
            ''', (telegram_id,))
        else:
            cursor.execute('''
                UPDATE users SET total_checks = total_checks + 1 WHERE telegram_id = ?
            ''', (telegram_id,))
        
        conn.commit()
        return cursor.lastrowid
    
    def get_user_history(self, telegram_id: int, limit: int = 50) -> List[Dict]:
        """Get user's check history"""
        user = self.get_user(telegram_id)
        if not user:
            return []
        
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM check_history WHERE user_id = ?
            ORDER BY checked_at DESC LIMIT ?
        ''', (user['id'], limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_user_stats(self, telegram_id: int) -> Dict:
        """Get user statistics"""
        user = self.get_user(telegram_id)
        if not user:
            return {}
        
        return {
            'total_checks': user['total_checks'],
            'approved_checks': user['approved_checks'],
            'declined_checks': user['declined_checks'],
            'daily_checks': user['daily_checks'],
            'success_rate': (user['approved_checks'] / user['total_checks'] * 100) 
                           if user['total_checks'] > 0 else 0
        }
    
    # ==================== Analytics ====================
    
    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Get daily check statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                DATE(checked_at) as date,
                COUNT(*) as total,
                SUM(CASE WHEN result = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN result = 'declined' THEN 1 ELSE 0 END) as declined
            FROM check_history
            WHERE checked_at >= DATE('now', ?)
            GROUP BY DATE(checked_at)
            ORDER BY date DESC
        ''', (f'-{days} days',))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_gateway_stats(self) -> List[Dict]:
        """Get statistics per gateway"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                gateway,
                COUNT(*) as total,
                SUM(CASE WHEN result = 'approved' THEN 1 ELSE 0 END) as approved,
                ROUND(SUM(CASE WHEN result = 'approved' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) as success_rate
            FROM check_history
            GROUP BY gateway
            ORDER BY total DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_total_stats(self) -> Dict:
        """Get total bot statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE premium_until > CURRENT_TIMESTAMP OR role IN ('owner', 'admin')
        ''')
        premium_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM check_history')
        total_checks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM check_history WHERE result = 'approved'")
        approved_checks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM check_history WHERE DATE(checked_at) = DATE('now')")
        today_checks = cursor.fetchone()[0]
        
        return {
            'total_users': total_users,
            'premium_users': premium_users,
            'total_checks': total_checks,
            'approved_checks': approved_checks,
            'today_checks': today_checks,
            'success_rate': (approved_checks / total_checks * 100) if total_checks > 0 else 0
        }
    
    # ==================== Settings ====================
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row[0])
            except:
                return row[0]
        return default
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a setting value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        value_str = json.dumps(value) if not isinstance(value, str) else value
        
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value_str))
        conn.commit()
        return True
    
    # ==================== Admin Logging ====================
    
    def log_admin_action(self, admin_id: int, action: str, 
                         target_user_id: int = None, details: str = None):
        """Log an admin action"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO admin_logs (admin_id, action, target_user_id, details)
            VALUES (?, ?, ?, ?)
        ''', (admin_id, action, target_user_id, details))
        conn.commit()
    
    def get_admin_logs(self, limit: int = 100) -> List[Dict]:
        """Get admin action logs"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]


# Singleton instance
_db_instance = None

def get_database() -> Database:
    """Get database singleton instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
