"""
Notes Manager - With Encryption & Full-Text Search
"""

from typing import Optional, Dict, List, Tuple
from datetime import datetime
import sys
from pathlib import Path
import base64

sys.path.append(str(Path(__file__).parent.parent))

from core.database import Database, dict_from_row
from core.crypto import CryptoManager
import config


class NotesManager:
    """
    Notes management dengan encryption & search
    
    Features:
    - AES-256 encryption untuk content
    - Full-text search (FTS5)
    - Tags support
    - Version history
    - Favorites & archive
    """
    
    def __init__(self, db: Database):
        self.db = db
    
    def create_note(self, user_id: int, title: str, content: str, 
                   master_password: str, encryption_salt: bytes,
                   tags: List[str] = None, is_locked: bool = False,
                   lock_password: str = None) -> Tuple[bool, str, Optional[int]]:
        """
        Create new note
        
        Args:
            user_id: User ID
            title: Note title
            content: Note content (will be encrypted)
            master_password: User's master password for encryption
            encryption_salt: User's encryption salt
            tags: List of tags
            is_locked: Whether note has additional lock
            lock_password: Password for locked note
            
        Returns:
            (success, message, note_id)
        """
        # Validate
        if not title.strip():
            return False, "Judul tidak boleh kosong", None
        
        if len(title) > config.MAX_NOTE_TITLE_LENGTH:
            return False, f"Judul maksimal {config.MAX_NOTE_TITLE_LENGTH} karakter", None
        
        if len(content) > config.MAX_NOTE_CONTENT_LENGTH:
            return False, f"Content maksimal {config.MAX_NOTE_CONTENT_LENGTH} karakter", None
        
        try:
            # Encrypt content
            encrypted_content = CryptoManager.encrypt_to_storage(
                content, master_password, encryption_salt
            )
            
            # Handle lock
            lock_hash = None
            lock_salt = None
            if is_locked and lock_password:
                lock_hash, lock_salt = CryptoManager.hash_password(lock_password)
            
            # Insert note
            cursor = self.db.execute(
                """
                INSERT INTO notes 
                (user_id, title, content, encrypted_content, is_encrypted, 
                 is_locked, lock_hash, lock_salt)
                VALUES (?, ?, ?, ?, 1, ?, ?, ?)
                """,
                (user_id, title, content, encrypted_content, is_locked, lock_hash, lock_salt)
            )
            
            note_id = cursor.lastrowid
            
            # Add tags
            if tags:
                self._add_tags_to_note(note_id, user_id, tags)
            
            # Create version
            self._create_version(note_id, user_id, title, content, encrypted_content, 1)
            
            self.db.commit()
            
            return True, config.MESSAGES['note_created'], note_id
            
        except Exception as e:
            self.db.rollback()
            return False, f"Error: {str(e)}", None
    
    def get_note(self, note_id: int, user_id: int, master_password: str = None,
                lock_password: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get note by ID
        
        Args:
            note_id: Note ID
            user_id: User ID
            master_password: For decryption
            lock_password: If note is locked
            
        Returns:
            (success, message, note_data)
        """
        # Get note
        note = self.db.fetchone(
            """
            SELECT n.*, 
                   GROUP_CONCAT(t.name) as tags
            FROM notes n
            LEFT JOIN note_tags nt ON n.id = nt.note_id
            LEFT JOIN tags t ON nt.tag_id = t.id
            WHERE n.id = ? AND n.user_id = ?
            GROUP BY n.id
            """,
            (note_id, user_id)
        )
        
        if not note:
            return False, config.MESSAGES['note_not_found'], None
        
        note_dict = dict_from_row(note)
        
        # Check if locked
        if note['is_locked']:
            if not lock_password:
                return False, "🔒 Catatan terkunci. Masukkan password.", note_dict
            
            # Verify lock password
            if not CryptoManager.verify_password(lock_password, note['lock_hash'], note['lock_salt']):
                return False, "Password salah", None
        
        # Decrypt content if master password provided
        if master_password and note['encrypted_content']:
            try:
                decrypted = CryptoManager.decrypt_from_storage(
                    note['encrypted_content'], master_password
                )
                note_dict['content'] = decrypted
            except:
                note_dict['content'] = "[Gagal mendekripsi - password salah?]"
        else:
            note_dict['content'] = note['content']  # Fallback to unencrypted
        
        # Parse tags
        if note_dict['tags']:
            note_dict['tags'] = note_dict['tags'].split(',')
        else:
            note_dict['tags'] = []
        
        # Update access stats
        self.db.execute(
            """
            UPDATE notes 
            SET last_accessed = CURRENT_TIMESTAMP,
                access_count = access_count + 1
            WHERE id = ?
            """,
            (note_id,)
        )
        self.db.commit()
        
        return True, "OK", note_dict
    
    def update_note(self, note_id: int, user_id: int, title: str = None,
                   content: str = None, master_password: str = None,
                   encryption_salt: bytes = None, tags: List[str] = None,
                   lock_password: str = None) -> Tuple[bool, str]:
        """Update note"""
        # Check if note exists and user owns it
        existing = self.db.fetchone(
            "SELECT id, is_locked, lock_hash, lock_salt, encrypted_content FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id)
        )
        
        if not existing:
            return False, config.MESSAGES['note_not_found']
        
        # Check lock
        if existing['is_locked'] and lock_password:
            if not CryptoManager.verify_password(lock_password, existing['lock_hash'], existing['lock_salt']):
                return False, "Password salah"
        
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if content is not None:
            # Update plaintext
            updates.append("content = ?")
            params.append(content)
            
            # Encrypt if password provided
            if master_password and encryption_salt:
                encrypted = CryptoManager.encrypt_to_storage(content, master_password, encryption_salt)
                updates.append("encrypted_content = ?")
                params.append(encrypted)
        
        if not updates:
            return False, "Tidak ada yang diupdate"
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(note_id)
        
        try:
            self.db.execute(
                f"UPDATE notes SET {', '.join(updates)} WHERE id = ?",
                tuple(params)
            )
            
            # Update tags if provided
            if tags is not None:
                self._update_note_tags(note_id, user_id, tags)
            
            # Create new version
            if content is not None:
                current_version = self._get_latest_version_number(note_id)
                encrypted = params[params.index(content) + 1] if master_password else ""
                self._create_version(note_id, user_id, title or "", content, encrypted, current_version + 1)
            
            self.db.commit()
            
            return True, config.MESSAGES['note_updated']
            
        except Exception as e:
            self.db.rollback()
            return False, f"Error: {str(e)}"
    
    def delete_note(self, note_id: int, user_id: int, lock_password: str = None) -> Tuple[bool, str]:
        """Delete note"""
        # Check if exists and locked
        note = self.db.fetchone(
            "SELECT is_locked, lock_hash, lock_salt FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id)
        )
        
        if not note:
            return False, config.MESSAGES['note_not_found']
        
        # Verify lock
        if note['is_locked']:
            if not lock_password:
                return False, "🔒 Masukkan password untuk menghapus"
            
            if not CryptoManager.verify_password(lock_password, note['lock_hash'], note['lock_salt']):
                return False, "Password salah"
        
        try:
            self.db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            self.db.commit()
            
            return True, config.MESSAGES['note_deleted']
            
        except Exception as e:
            self.db.rollback()
            return False, f"Error: {str(e)}"
    
    def search_notes(self, user_id: int, query: str, master_password: str = None,
                    limit: int = 50) -> List[Dict]:
        """
        Full-text search notes
        
        Args:
            user_id: User ID
            query: Search query
            master_password: For decryption
            limit: Max results
            
        Returns:
            List of matching notes
        """
        if len(query) < config.SEARCH_MIN_LENGTH:
            return []
        
        # Use FTS5 for search
        results = self.db.fetchall(
            """
            SELECT n.*, 
                   GROUP_CONCAT(t.name) as tags,
                   snippet(notes_fts, 0, '<mark>', '</mark>', '...', 32) as title_snippet,
                   snippet(notes_fts, 1, '<mark>', '</mark>', '...', 64) as content_snippet
            FROM notes n
            JOIN notes_fts ON n.id = notes_fts.rowid
            LEFT JOIN note_tags nt ON n.id = nt.note_id
            LEFT JOIN tags t ON nt.tag_id = t.id
            WHERE notes_fts MATCH ? AND n.user_id = ?
            GROUP BY n.id
            ORDER BY rank
            LIMIT ?
            """,
            (query, user_id, limit)
        )
        
        notes = []
        for row in results:
            note = dict_from_row(row)
            
            # Parse tags
            if note['tags']:
                note['tags'] = note['tags'].split(',')
            else:
                note['tags'] = []
            
            # Try decrypt if password provided
            if master_password and note['encrypted_content']:
                try:
                    note['content'] = CryptoManager.decrypt_from_storage(
                        note['encrypted_content'], master_password
                    )
                except:
                    note['content'] = "[Terenkripsi]"
            
            notes.append(note)
        
        return notes
    
    def list_notes(self, user_id: int, include_archived: bool = False,
                  favorites_only: bool = False, tag: str = None,
                  limit: int = 100, offset: int = 0) -> List[Dict]:
        """List notes with filters"""
        query = """
            SELECT n.*, 
                   GROUP_CONCAT(t.name) as tags
            FROM notes n
            LEFT JOIN note_tags nt ON n.id = nt.note_id
            LEFT JOIN tags t ON nt.tag_id = t.id
            WHERE n.user_id = ?
        """
        params = [user_id]
        
        if not include_archived:
            query += " AND n.is_archived = 0"
        
        if favorites_only:
            query += " AND n.is_favorite = 1"
        
        if tag:
            query += " AND t.name = ?"
            params.append(tag)
        
        query += " GROUP BY n.id ORDER BY n.updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        results = self.db.fetchall(query, tuple(params))
        
        notes = []
        for row in results:
            note = dict_from_row(row)
            if note['tags']:
                note['tags'] = note['tags'].split(',')
            else:
                note['tags'] = []
            notes.append(note)
        
        return notes
    
    def toggle_favorite(self, note_id: int, user_id: int) -> Tuple[bool, str]:
        """Toggle favorite status"""
        note = self.db.fetchone(
            "SELECT is_favorite FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id)
        )
        
        if not note:
            return False, config.MESSAGES['note_not_found']
        
        new_status = not note['is_favorite']
        
        self.db.execute(
            "UPDATE notes SET is_favorite = ? WHERE id = ?",
            (new_status, note_id)
        )
        self.db.commit()
        
        msg = "ditambahkan ke" if new_status else "dihapus dari"
        return True, f"✓ Catatan {msg} favorites"
    
    def toggle_archive(self, note_id: int, user_id: int) -> Tuple[bool, str]:
        """Toggle archive status"""
        note = self.db.fetchone(
            "SELECT is_archived FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id)
        )
        
        if not note:
            return False, config.MESSAGES['note_not_found']
        
        new_status = not note['is_archived']
        
        self.db.execute(
            "UPDATE notes SET is_archived = ? WHERE id = ?",
            (new_status, note_id)
        )
        self.db.commit()
        
        msg = "diarsipkan" if new_status else "dibatalkan arsipnya"
        return True, f"✓ Catatan {msg}"
    
    def get_statistics(self, user_id: int) -> Dict:
        """Get notes statistics"""
        stats = {}
        
        # Total notes
        total = self.db.fetchone(
            "SELECT COUNT(*) as count FROM notes WHERE user_id = ?",
            (user_id,)
        )
        stats['total'] = total['count']
        
        # Favorites
        fav = self.db.fetchone(
            "SELECT COUNT(*) as count FROM notes WHERE user_id = ? AND is_favorite = 1",
            (user_id,)
        )
        stats['favorites'] = fav['count']
        
        # Archived
        arch = self.db.fetchone(
            "SELECT COUNT(*) as count FROM notes WHERE user_id = ? AND is_archived = 1",
            (user_id,)
        )
        stats['archived'] = arch['count']
        
        # Locked
        locked = self.db.fetchone(
            "SELECT COUNT(*) as count FROM notes WHERE user_id = ? AND is_locked = 1",
            (user_id,)
        )
        stats['locked'] = locked['count']
        
        # Tags
        tags = self.db.fetchone(
            "SELECT COUNT(*) as count FROM tags WHERE user_id = ?",
            (user_id,)
        )
        stats['tags'] = tags['count']
        
        return stats
    
    # ==================== HELPER METHODS ====================
    
    def _add_tags_to_note(self, note_id: int, user_id: int, tag_names: List[str]):
        """Add tags to note"""
        for tag_name in tag_names[:config.MAX_TAGS_PER_NOTE]:
            if len(tag_name) > config.MAX_TAG_LENGTH:
                continue
            
            # Get or create tag
            tag = self.db.fetchone(
                "SELECT id FROM tags WHERE user_id = ? AND name = ?",
                (user_id, tag_name)
            )
            
            if tag:
                tag_id = tag['id']
            else:
                cursor = self.db.execute(
                    "INSERT INTO tags (user_id, name) VALUES (?, ?)",
                    (user_id, tag_name)
                )
                tag_id = cursor.lastrowid
            
            # Link tag to note
            try:
                self.db.execute(
                    "INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)",
                    (note_id, tag_id)
                )
            except:
                pass  # Already exists
    
    def _update_note_tags(self, note_id: int, user_id: int, tag_names: List[str]):
        """Update note tags"""
        # Remove existing tags
        self.db.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
        
        # Add new tags
        self._add_tags_to_note(note_id, user_id, tag_names)
    
    def _create_version(self, note_id: int, user_id: int, title: str, 
                       content: str, encrypted_content: str, version: int):
        """Create version history entry"""
        if not config.FEATURES['version_history']:
            return
        
        try:
            self.db.execute(
                """
                INSERT INTO note_versions 
                (note_id, title, content, encrypted_content, version_number, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (note_id, title, content, encrypted_content, version, user_id)
            )
        except:
            pass  # Don't fail if versioning fails
    
    def _get_latest_version_number(self, note_id: int) -> int:
        """Get latest version number"""
        result = self.db.fetchone(
            "SELECT MAX(version_number) as version FROM note_versions WHERE note_id = ?",
            (note_id,)
        )
        
        return result['version'] if result and result['version'] else 0
