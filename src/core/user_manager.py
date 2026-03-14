"""
User Manager - With AES-256 Encryption Support
"""

from typing import Optional, Dict, Tuple
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from core.database import Database, dict_from_row
from core.crypto import CryptoManager
import config


class UserManager:
    """
    User management dengan encryption support
    
    Features:
    - Secure password hashing
    - Per-user encryption salt
    - Session management
    - Activity tracking
    """
    
    def __init__(self, db: Database):
        self.db = db
    
    def register(self, username: str, password: str, email: str = None) -> Tuple[bool, str, Optional[int]]:
        """
        Register new user
        
        Args:
            username: Username
            password: Password
            email: Email (optional)
            
        Returns:
            (success, message, user_id)
        """
        # Validate username
        if len(username) < config.MIN_USERNAME_LENGTH:
            return False, config.MESSAGES['invalid_username'].format(min=config.MIN_USERNAME_LENGTH), None
        
        if len(username) > config.MAX_USERNAME_LENGTH:
            return False, f"Username maksimal {config.MAX_USERNAME_LENGTH} karakter", None
        
        # Validate password
        if len(password) < config.MIN_PASSWORD_LENGTH:
            return False, config.MESSAGES['invalid_password'].format(min=config.MIN_PASSWORD_LENGTH), None
        
        # Check if username exists
        existing = self.db.fetchone(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        )
        
        if existing:
            return False, config.MESSAGES['username_exists'], None
        
        # Hash password
        password_hash, salt = CryptoManager.hash_password(password)
        
        # Generate encryption salt (for encrypting notes)
        encryption_salt = CryptoManager.generate_salt()
        encryption_salt_b64 = CryptoManager.encrypt_to_storage("", "", encryption_salt).split(':')[0]
        
        # Insert user
        try:
            cursor = self.db.execute(
                """
                INSERT INTO users (username, password_hash, salt, encryption_salt, email)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username, password_hash, salt, encryption_salt_b64, email)
            )
            
            user_id = cursor.lastrowid
            self.db.commit()
            
            # Log activity
            self._log_activity(user_id, "user_registered", "user", user_id)
            
            return True, config.MESSAGES['register_success'], user_id
            
        except Exception as e:
            self.db.rollback()
            return False, f"Error: {str(e)}", None
    
    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Login user
        
        Args:
            username: Username
            password: Password
            
        Returns:
            (success, message, user_data)
        """
        # Get user
        user = self.db.fetchone(
            """
            SELECT id, username, password_hash, salt, encryption_salt, 
                   is_active, login_count, email, bio, created_at
            FROM users 
            WHERE username = ?
            """,
            (username,)
        )
        
        if not user:
            return False, config.MESSAGES['login_failed'], None
        
        # Check if active
        if not user['is_active']:
            return False, "Akun Anda telah dinonaktifkan", None
        
        # Verify password
        if not CryptoManager.verify_password(password, user['password_hash'], user['salt']):
            return False, config.MESSAGES['login_failed'], None
        
        # Update login info
        self.db.execute(
            """
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP,
                login_count = login_count + 1
            WHERE id = ?
            """,
            (user['id'],)
        )
        self.db.commit()
        
        # Log activity
        self._log_activity(user['id'], "user_login", "user", user['id'])
        
        # Return user data
        user_data = dict_from_row(user)
        user_data['password_hash'] = None  # Don't return sensitive data
        user_data['salt'] = None
        
        return True, config.MESSAGES['login_success'].format(username=username), user_data
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        user = self.db.fetchone(
            """
            SELECT id, username, email, bio, created_at, last_login, 
                   login_count, is_active, settings
            FROM users 
            WHERE id = ?
            """,
            (user_id,)
        )
        
        return dict_from_row(user) if user else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        user = self.db.fetchone(
            """
            SELECT id, username, email, bio, created_at, last_login, 
                   login_count, is_active, settings
            FROM users 
            WHERE username = ?
            """,
            (username,)
        )
        
        return dict_from_row(user) if user else None
    
    def update_profile(self, user_id: int, email: str = None, bio: str = None) -> Tuple[bool, str]:
        """Update user profile"""
        updates = []
        params = []
        
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        
        if bio is not None:
            updates.append("bio = ?")
            params.append(bio)
        
        if not updates:
            return False, "Tidak ada yang diupdate"
        
        params.append(user_id)
        
        try:
            self.db.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                tuple(params)
            )
            self.db.commit()
            
            self._log_activity(user_id, "profile_updated", "user", user_id)
            
            return True, "✓ Profil berhasil diupdate"
            
        except Exception as e:
            self.db.rollback()
            return False, f"Error: {str(e)}"
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        # Get current password
        user = self.db.fetchone(
            "SELECT password_hash, salt FROM users WHERE id = ?",
            (user_id,)
        )
        
        if not user:
            return False, "User tidak ditemukan"
        
        # Verify old password
        if not CryptoManager.verify_password(old_password, user['password_hash'], user['salt']):
            return False, "Password lama salah"
        
        # Validate new password
        if len(new_password) < config.MIN_PASSWORD_LENGTH:
            return False, config.MESSAGES['invalid_password'].format(min=config.MIN_PASSWORD_LENGTH)
        
        # Hash new password
        new_hash, new_salt = CryptoManager.hash_password(new_password)
        
        try:
            self.db.execute(
                "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                (new_hash, new_salt, user_id)
            )
            self.db.commit()
            
            self._log_activity(user_id, "password_changed", "user", user_id)
            
            return True, "✓ Password berhasil diubah"
            
        except Exception as e:
            self.db.rollback()
            return False, f"Error: {str(e)}"
    
    def get_encryption_salt(self, user_id: int) -> Optional[bytes]:
        """Get user's encryption salt for encrypting notes"""
        import base64
        
        user = self.db.fetchone(
            "SELECT encryption_salt FROM users WHERE id = ?",
            (user_id,)
        )
        
        if user and user['encryption_salt']:
            return base64.b64decode(user['encryption_salt'].encode('utf-8'))
        
        return None
    
    def get_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        stats = {}
        
        # User info
        user = self.get_user(user_id)
        if user:
            stats['user'] = user
        
        # Notes count
        notes = self.db.fetchone(
            "SELECT COUNT(*) as count FROM notes WHERE user_id = ?",
            (user_id,)
        )
        stats['total_notes'] = notes['count']
        
        # Favorite notes
        favorites = self.db.fetchone(
            "SELECT COUNT(*) as count FROM notes WHERE user_id = ? AND is_favorite = 1",
            (user_id,)
        )
        stats['favorite_notes'] = favorites['count']
        
        # Archived notes
        archived = self.db.fetchone(
            "SELECT COUNT(*) as count FROM notes WHERE user_id = ? AND is_archived = 1",
            (user_id,)
        )
        stats['archived_notes'] = archived['count']
        
        # Tags count
        tags = self.db.fetchone(
            "SELECT COUNT(*) as count FROM tags WHERE user_id = ?",
            (user_id,)
        )
        stats['total_tags'] = tags['count']
        
        # Recent activity
        activities = self.db.fetchall(
            """
            SELECT action, created_at 
            FROM activity_log 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 5
            """,
            (user_id,)
        )
        stats['recent_activities'] = [dict_from_row(a) for a in activities]
        
        return stats
    
    def delete_user(self, user_id: int, password: str) -> Tuple[bool, str]:
        """Delete user account"""
        # Verify password
        user = self.db.fetchone(
            "SELECT password_hash, salt FROM users WHERE id = ?",
            (user_id,)
        )
        
        if not user:
            return False, "User tidak ditemukan"
        
        if not CryptoManager.verify_password(password, user['password_hash'], user['salt']):
            return False, "Password salah"
        
        try:
            # Delete user (cascade will delete notes, tags, etc.)
            self.db.execute("DELETE FROM users WHERE id = ?", (user_id,))
            self.db.commit()
            
            return True, "✓ Akun berhasil dihapus"
            
        except Exception as e:
            self.db.rollback()
            return False, f"Error: {str(e)}"
    
    def _log_activity(self, user_id: int, action: str, resource_type: str = None, 
                     resource_id: int = None, details: str = None):
        """Log user activity"""
        try:
            self.db.execute(
                """
                INSERT INTO activity_log (user_id, action, resource_type, resource_id, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, action, resource_type, resource_id, details)
            )
            self.db.commit()
        except:
            pass  # Don't fail if logging fails
