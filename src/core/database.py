"""
Database Module - SQLite dengan Full-Text Search
High-performance database layer
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
import config


class Database:
    """
    SQLite database manager dengan advanced features
    
    Features:
    - WAL mode untuk concurrent access
    - Full-text search (FTS5)
    - Proper indexing
    - Transaction management
    - Connection pooling
    """
    
    def __init__(self, db_path: Path = config.DB_FILE):
        """Initialize database connection"""
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._initialize_schema()
    
    def _connect(self):
        """Create database connection"""
        self.conn = sqlite3.connect(
            self.db_path,
            timeout=config.DB_TIMEOUT,
            check_same_thread=config.DB_CHECK_SAME_THREAD,
            isolation_level=config.DB_ISOLATION_LEVEL
        )
        self.conn.row_factory = sqlite3.Row
        
        # Performance optimizations
        self._optimize_database()
    
    def _optimize_database(self):
        """Apply performance optimizations"""
        cursor = self.conn.cursor()
        
        # Enable WAL mode
        cursor.execute(f"PRAGMA journal_mode={config.JOURNAL_MODE}")
        
        # Set cache size
        cursor.execute(f"PRAGMA cache_size={config.CACHE_SIZE}")
        
        # Set page size
        cursor.execute(f"PRAGMA page_size={config.PAGE_SIZE}")
        
        # Set synchronous mode
        cursor.execute(f"PRAGMA synchronous={config.SYNCHRONOUS}")
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys=ON")
        
        self.conn.commit()
    
    def _initialize_schema(self):
        """Create database schema"""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                encryption_salt TEXT NOT NULL,
                email TEXT,
                bio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                login_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                settings TEXT DEFAULT '{}'
            )
        """)
        
        # Notes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                encrypted_content TEXT NOT NULL,
                is_encrypted BOOLEAN DEFAULT 1,
                is_locked BOOLEAN DEFAULT 0,
                lock_hash TEXT,
                lock_salt TEXT,
                is_favorite BOOLEAN DEFAULT 0,
                is_archived BOOLEAN DEFAULT 0,
                color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, name),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Note-Tag relationship
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS note_tags (
                note_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (note_id, tag_id),
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
        
        # Attachments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
            )
        """)
        
        # Version history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS note_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                encrypted_content TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER NOT NULL,
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        # Activity log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id INTEGER,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Full-text search virtual table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                title,
                content,
                content=notes,
                content_rowid=id
            )
        """)
        
        # Triggers for FTS sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
                INSERT INTO notes_fts(rowid, title, content) 
                VALUES (new.id, new.title, new.content);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
                DELETE FROM notes_fts WHERE rowid = old.id;
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
                UPDATE notes_fts SET title = new.title, content = new.content 
                WHERE rowid = new.id;
            END
        """)
        
        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_user_id ON notes(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON notes(updated_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_favorite ON notes(is_favorite)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_archived ON notes(is_archived)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tags_user_id ON tags(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_user_id ON activity_log(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_created_at ON activity_log(created_at)")
        
        self.conn.commit()
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor
    
    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Fetch one result"""
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def fetchall(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Fetch all results"""
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def commit(self):
        """Commit transaction"""
        self.conn.commit()
    
    def rollback(self):
        """Rollback transaction"""
        self.conn.rollback()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def vacuum(self):
        """Optimize database"""
        self.execute("VACUUM")
        self.commit()
    
    def backup(self, backup_path: Path):
        """Backup database"""
        backup_conn = sqlite3.connect(backup_path)
        self.conn.backup(backup_conn)
        backup_conn.close()
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        stats = {}
        
        # Count tables
        stats['total_users'] = self.fetchone("SELECT COUNT(*) as count FROM users")['count']
        stats['total_notes'] = self.fetchone("SELECT COUNT(*) as count FROM notes")['count']
        stats['total_tags'] = self.fetchone("SELECT COUNT(*) as count FROM tags")['count']
        stats['total_attachments'] = self.fetchone("SELECT COUNT(*) as count FROM attachments")['count']
        
        # Database size
        stats['db_size_bytes'] = self.db_path.stat().st_size
        stats['db_size_mb'] = round(stats['db_size_bytes'] / (1024 * 1024), 2)
        
        # Page info
        page_info = self.fetchone("PRAGMA page_count")
        stats['page_count'] = page_info[0] if page_info else 0
        
        return stats


# ==================== CONTEXT MANAGER ====================

class DatabaseConnection:
    """Context manager for database connections"""
    
    def __init__(self, db_path: Path = config.DB_FILE):
        self.db_path = db_path
        self.db = None
    
    def __enter__(self) -> Database:
        self.db = Database(self.db_path)
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
        else:
            self.db.commit()
        self.db.close()


# ==================== HELPER FUNCTIONS ====================

def dict_from_row(row: sqlite3.Row) -> Dict:
    """Convert SQLite Row to dictionary"""
    return {key: row[key] for key in row.keys()}


def get_db() -> Database:
    """Get database instance (singleton pattern)"""
    if not hasattr(get_db, '_instance'):
        get_db._instance = Database()
    return get_db._instance


def init_database():
    """Initialize database (for first run)"""
    db = Database()
    print(f"✓ Database initialized at: {config.DB_FILE}")
    stats = db.get_stats()
    print(f"  Database size: {stats['db_size_mb']} MB")
    db.close()


if __name__ == "__main__":
    init_database()
