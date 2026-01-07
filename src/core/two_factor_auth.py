"""
Two-Factor Authentication (2FA) Module for MadyStripe

Provides TOTP-based 2FA for enhanced security.
Uses pyotp for OTP generation and verification.
"""

import pyotp
import base64
import hashlib
import secrets
import json
import os
from typing import Optional, Tuple, Dict, Any
from datetime import datetime


class TwoFactorAuth:
    """
    Two-Factor Authentication manager using TOTP.
    
    Features:
    - TOTP secret generation
    - QR code URL generation for authenticator apps
    - OTP verification
    - Backup codes generation
    - Recovery options
    """
    
    def __init__(self, issuer: str = "MadyStripe"):
        """
        Initialize 2FA manager.
        
        Args:
            issuer: The issuer name shown in authenticator apps
        """
        self.issuer = issuer
        self.backup_codes_count = 10
        self.backup_code_length = 8
        
    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret.
        
        Returns:
            Base32-encoded secret string
        """
        return pyotp.random_base32()
    
    def get_totp(self, secret: str) -> pyotp.TOTP:
        """
        Get TOTP object for a secret.
        
        Args:
            secret: Base32-encoded secret
            
        Returns:
            pyotp.TOTP object
        """
        return pyotp.TOTP(secret)
    
    def get_provisioning_uri(self, secret: str, user_id: str, username: str = None) -> str:
        """
        Get provisioning URI for QR code generation.
        
        Args:
            secret: Base32-encoded secret
            user_id: User's Telegram ID or unique identifier
            username: Optional username for display
            
        Returns:
            otpauth:// URI for QR code
        """
        totp = self.get_totp(secret)
        name = username or f"User_{user_id}"
        return totp.provisioning_uri(name=name, issuer_name=self.issuer)
    
    def verify_otp(self, secret: str, otp: str, valid_window: int = 1) -> bool:
        """
        Verify an OTP code.
        
        Args:
            secret: Base32-encoded secret
            otp: The OTP code to verify
            valid_window: Number of time windows to check (default 1 = ±30 seconds)
            
        Returns:
            True if OTP is valid, False otherwise
        """
        try:
            totp = self.get_totp(secret)
            return totp.verify(otp, valid_window=valid_window)
        except Exception:
            return False
    
    def get_current_otp(self, secret: str) -> str:
        """
        Get the current OTP for a secret (for testing).
        
        Args:
            secret: Base32-encoded secret
            
        Returns:
            Current 6-digit OTP
        """
        totp = self.get_totp(secret)
        return totp.now()
    
    def generate_backup_codes(self) -> list:
        """
        Generate backup codes for account recovery.
        
        Returns:
            List of backup codes
        """
        codes = []
        for _ in range(self.backup_codes_count):
            code = secrets.token_hex(self.backup_code_length // 2).upper()
            # Format as XXXX-XXXX
            formatted = f"{code[:4]}-{code[4:]}"
            codes.append(formatted)
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for secure storage.
        
        Args:
            code: The backup code to hash
            
        Returns:
            SHA-256 hash of the code
        """
        # Normalize code (remove dashes, uppercase)
        normalized = code.replace('-', '').upper()
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def verify_backup_code(self, code: str, hashed_codes: list) -> Tuple[bool, Optional[str]]:
        """
        Verify a backup code against stored hashes.
        
        Args:
            code: The backup code to verify
            hashed_codes: List of hashed backup codes
            
        Returns:
            Tuple of (is_valid, matched_hash)
        """
        code_hash = self.hash_backup_code(code)
        if code_hash in hashed_codes:
            return True, code_hash
        return False, None


class TwoFactorManager:
    """
    Manager for 2FA operations with database integration.
    """
    
    def __init__(self, db=None):
        """
        Initialize 2FA manager.
        
        Args:
            db: Database instance (optional, will use get_database if not provided)
        """
        self.auth = TwoFactorAuth()
        self._db = db
        
    @property
    def db(self):
        """Lazy load database."""
        if self._db is None:
            from .database import get_database
            self._db = get_database()
        return self._db
    
    def setup_2fa(self, user_id: int, username: str = None) -> Dict[str, Any]:
        """
        Set up 2FA for a user.
        
        Args:
            user_id: Telegram user ID
            username: Optional username
            
        Returns:
            Dict with secret, provisioning_uri, and backup_codes
        """
        # Generate secret
        secret = self.auth.generate_secret()
        
        # Generate provisioning URI
        uri = self.auth.get_provisioning_uri(secret, str(user_id), username)
        
        # Generate backup codes
        backup_codes = self.auth.generate_backup_codes()
        hashed_codes = [self.auth.hash_backup_code(code) for code in backup_codes]
        
        # Store in database (pending verification)
        self._store_pending_2fa(user_id, secret, hashed_codes)
        
        return {
            'secret': secret,
            'provisioning_uri': uri,
            'backup_codes': backup_codes,
            'qr_data': uri  # Can be used to generate QR code
        }
    
    def _store_pending_2fa(self, user_id: int, secret: str, hashed_codes: list):
        """Store pending 2FA setup in database."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if table exists, create if not
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS two_factor_auth (
                    user_id INTEGER PRIMARY KEY,
                    secret TEXT,
                    backup_codes TEXT,
                    is_enabled INTEGER DEFAULT 0,
                    setup_at DATETIME,
                    verified_at DATETIME
                )
            ''')
            
            # Insert or update
            cursor.execute('''
                INSERT OR REPLACE INTO two_factor_auth 
                (user_id, secret, backup_codes, is_enabled, setup_at)
                VALUES (?, ?, ?, 0, ?)
            ''', (user_id, secret, json.dumps(hashed_codes), datetime.now().isoformat()))
            
            conn.commit()
        except Exception as e:
            print(f"Error storing 2FA: {e}")
    
    def verify_and_enable(self, user_id: int, otp: str) -> Tuple[bool, str]:
        """
        Verify OTP and enable 2FA for user.
        
        Args:
            user_id: Telegram user ID
            otp: OTP code from authenticator app
            
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get pending 2FA setup
            cursor.execute(
                'SELECT secret, is_enabled FROM two_factor_auth WHERE user_id = ?',
                (user_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return False, "2FA not set up. Use /setup2fa first."
            
            secret, is_enabled = row
            
            if is_enabled:
                return False, "2FA is already enabled."
            
            # Verify OTP
            if not self.auth.verify_otp(secret, otp):
                return False, "Invalid OTP code. Please try again."
            
            # Enable 2FA
            cursor.execute('''
                UPDATE two_factor_auth 
                SET is_enabled = 1, verified_at = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
            
            conn.commit()
            return True, "2FA enabled successfully!"
            
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def verify_login(self, user_id: int, otp: str) -> Tuple[bool, str]:
        """
        Verify OTP for login.
        
        Args:
            user_id: Telegram user ID
            otp: OTP code
            
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT secret, backup_codes, is_enabled FROM two_factor_auth WHERE user_id = ?',
                (user_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return True, "2FA not enabled"  # No 2FA = pass through
            
            secret, backup_codes_json, is_enabled = row
            
            if not is_enabled:
                return True, "2FA not enabled"
            
            # Try OTP first
            if self.auth.verify_otp(secret, otp):
                return True, "OTP verified"
            
            # Try backup code
            backup_codes = json.loads(backup_codes_json) if backup_codes_json else []
            is_valid, matched_hash = self.auth.verify_backup_code(otp, backup_codes)
            
            if is_valid:
                # Remove used backup code
                backup_codes.remove(matched_hash)
                cursor.execute(
                    'UPDATE two_factor_auth SET backup_codes = ? WHERE user_id = ?',
                    (json.dumps(backup_codes), user_id)
                )
                conn.commit()
                return True, f"Backup code used. {len(backup_codes)} remaining."
            
            return False, "Invalid OTP or backup code"
            
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def is_2fa_enabled(self, user_id: int) -> bool:
        """Check if 2FA is enabled for a user."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT is_enabled FROM two_factor_auth WHERE user_id = ?',
                (user_id,)
            )
            row = cursor.fetchone()
            
            return row and row[0] == 1
        except Exception:
            return False
    
    def disable_2fa(self, user_id: int, otp: str) -> Tuple[bool, str]:
        """
        Disable 2FA for a user.
        
        Args:
            user_id: Telegram user ID
            otp: OTP code for verification
            
        Returns:
            Tuple of (success, message)
        """
        # Verify OTP first
        success, message = self.verify_login(user_id, otp)
        if not success:
            return False, "Invalid OTP. Cannot disable 2FA."
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM two_factor_auth WHERE user_id = ?', (user_id,))
            conn.commit()
            
            return True, "2FA disabled successfully."
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def regenerate_backup_codes(self, user_id: int, otp: str) -> Tuple[bool, str, list]:
        """
        Regenerate backup codes for a user.
        
        Args:
            user_id: Telegram user ID
            otp: OTP code for verification
            
        Returns:
            Tuple of (success, message, new_codes)
        """
        # Verify OTP first
        success, message = self.verify_login(user_id, otp)
        if not success:
            return False, "Invalid OTP. Cannot regenerate codes.", []
        
        try:
            # Generate new codes
            new_codes = self.auth.generate_backup_codes()
            hashed_codes = [self.auth.hash_backup_code(code) for code in new_codes]
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'UPDATE two_factor_auth SET backup_codes = ? WHERE user_id = ?',
                (json.dumps(hashed_codes), user_id)
            )
            conn.commit()
            
            return True, "Backup codes regenerated.", new_codes
        except Exception as e:
            return False, f"Error: {str(e)}", []


# Singleton instance
_two_factor_manager = None

def get_2fa_manager() -> TwoFactorManager:
    """Get singleton 2FA manager instance."""
    global _two_factor_manager
    if _two_factor_manager is None:
        _two_factor_manager = TwoFactorManager()
    return _two_factor_manager


if __name__ == '__main__':
    # Test the 2FA module
    print("Testing 2FA Module")
    print("=" * 50)
    
    auth = TwoFactorAuth()
    
    # Generate secret
    secret = auth.generate_secret()
    print(f"Secret: {secret}")
    
    # Get provisioning URI
    uri = auth.get_provisioning_uri(secret, "123456789", "TestUser")
    print(f"Provisioning URI: {uri}")
    
    # Get current OTP
    current_otp = auth.get_current_otp(secret)
    print(f"Current OTP: {current_otp}")
    
    # Verify OTP
    is_valid = auth.verify_otp(secret, current_otp)
    print(f"OTP Valid: {is_valid}")
    
    # Generate backup codes
    backup_codes = auth.generate_backup_codes()
    print(f"Backup Codes: {backup_codes}")
    
    # Test backup code verification
    hashed = [auth.hash_backup_code(code) for code in backup_codes]
    is_valid, matched = auth.verify_backup_code(backup_codes[0], hashed)
    print(f"Backup Code Valid: {is_valid}")
    
    print()
    print("=" * 50)
    print("All tests passed!")
