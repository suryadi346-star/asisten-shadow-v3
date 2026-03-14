"""
Asisten Shadow v3.0 - Enhanced Configuration
Multi-platform, secure, user-friendly note-taking app
"""

import os
from pathlib import Path

# ==================== APP INFO ====================
APP_NAME = "Asisten Shadow"
VERSION = "3.0.0"
AUTHOR = "Asisten Shadow Team"
DESCRIPTION = "Multi-platform encrypted note-taking app"
GITHUB_URL = "https://github.com/suryadi346-star/asisten-shadow-v3"

# ==================== PATHS ====================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
EXPORTS_DIR = BASE_DIR / "exports"
BACKUPS_DIR = BASE_DIR / "backups"

# Ensure directories exist
for directory in [DATA_DIR, LOGS_DIR, EXPORTS_DIR, BACKUPS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# File paths
DB_FILE = DATA_DIR / "asisten_shadow.db"
CONFIG_FILE = DATA_DIR / "config.json"
LOG_FILE = LOGS_DIR / "app.log"

# ==================== SECURITY ====================
# Encryption
ENCRYPTION_ALGORITHM = "AES-256-GCM"
KEY_DERIVATION = "PBKDF2"
PBKDF2_ITERATIONS = 100000
SALT_SIZE = 32
IV_SIZE = 12
TAG_SIZE = 16

# Password requirements
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 50
MIN_PASSWORD_LENGTH = 8  # Increased from 6
MAX_PASSWORD_LENGTH = 128

# Session
SESSION_TIMEOUT = 3600  # 1 hour in seconds
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes

# ==================== DATABASE ====================
# SQLite settings
DB_TIMEOUT = 30
DB_CHECK_SAME_THREAD = False
DB_ISOLATION_LEVEL = None

# Performance
CACHE_SIZE = 2000  # Number of pages
PAGE_SIZE = 4096
JOURNAL_MODE = "WAL"  # Write-Ahead Logging
SYNCHRONOUS = "NORMAL"

# ==================== UI SETTINGS ====================
# Terminal UI
TERMINAL_WIDTH = 100
TERMINAL_THEME = "monokai"
ENABLE_MOUSE = True
ENABLE_COLOR = True

# Colors (Rich library)
COLOR_PRIMARY = "cyan"
COLOR_SUCCESS = "green"
COLOR_WARNING = "yellow"
COLOR_ERROR = "red"
COLOR_INFO = "blue"
COLOR_ACCENT = "magenta"

# ==================== WEB INTERFACE ====================
# Server
WEB_HOST = "127.0.0.1"
WEB_PORT = 8000
WEB_DEBUG = False
WEB_RELOAD = False

# CORS
CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
CORS_ALLOW_CREDENTIALS = True

# API
API_PREFIX = "/api/v1"
API_DOCS_URL = "/docs"
API_REDOC_URL = "/redoc"

# JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-key-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 3600  # 1 hour

# ==================== NOTES ====================
# Limits
MAX_NOTE_TITLE_LENGTH = 200
MAX_NOTE_CONTENT_LENGTH = 1_000_000  # 1MB
MAX_TAGS_PER_NOTE = 20
MAX_TAG_LENGTH = 50

# Features
ENABLE_MARKDOWN = True
ENABLE_ATTACHMENTS = True
ENABLE_VERSION_HISTORY = True
ENABLE_AUTO_BACKUP = True

# Attachments
MAX_ATTACHMENT_SIZE = 10_485_760  # 10MB
ALLOWED_EXTENSIONS = {
    'images': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'],
    'documents': ['.pdf', '.doc', '.docx', '.txt', '.md', '.html'],
    'archives': ['.zip', '.tar', '.gz', '.7z'],
    'code': ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs'],
}

# ==================== SEARCH ====================
# Full-text search
SEARCH_MIN_LENGTH = 2
SEARCH_MAX_RESULTS = 100
ENABLE_FUZZY_SEARCH = True
FUZZY_THRESHOLD = 0.6

# ==================== BACKUP ====================
# Auto-backup
AUTO_BACKUP_ENABLED = True
AUTO_BACKUP_INTERVAL = 86400  # 24 hours
MAX_BACKUPS_KEEP = 7  # Keep last 7 backups

# Export formats
EXPORT_FORMATS = ['json', 'markdown', 'html', 'pdf', 'txt']

# ==================== LOGGING ====================
# Log levels
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 10_485_760  # 10MB
LOG_BACKUP_COUNT = 5

# ==================== FEATURES FLAGS ====================
FEATURES = {
    'encryption': True,
    'markdown': True,
    'attachments': True,
    'tags': True,
    'favorites': True,
    'search': True,
    'export': True,
    'import': True,
    'backup': True,
    'version_history': True,
    'sharing': False,  # Future feature
    'collaboration': False,  # Future feature
    'cloud_sync': False,  # Future feature
    'ai_features': False,  # Future feature
}

# ==================== PERFORMANCE ====================
# Caching
ENABLE_CACHE = True
CACHE_TTL = 300  # 5 minutes
MAX_CACHE_SIZE = 100  # Number of items

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ==================== VALIDATION ====================
# Input validation
SANITIZE_INPUT = True
STRIP_HTML_TAGS = False  # Allow HTML in markdown
MAX_REQUEST_SIZE = 52_428_800  # 50MB

# ==================== MESSAGES ====================
MESSAGES = {
    # Success
    "login_success": "✓ Login berhasil! Selamat datang {username}",
    "register_success": "✓ Registrasi berhasil! Silakan login",
    "note_created": "✓ Catatan berhasil dibuat",
    "note_updated": "✓ Catatan berhasil diperbarui",
    "note_deleted": "✓ Catatan berhasil dihapus",
    "export_success": "✓ Export berhasil ke {filename}",
    "backup_success": "✓ Backup berhasil dibuat",

    # Errors
    "login_failed": "✗ Username atau password salah",
    "username_exists": "✗ Username sudah digunakan",
    "invalid_username": "✗ Username minimal {min} karakter",
    "invalid_password": "✗ Password minimal {min} karakter",
    "note_not_found": "✗ Catatan tidak ditemukan",
    "permission_denied": "✗ Anda tidak memiliki akses",
    "encryption_failed": "✗ Gagal mengenkripsi data",
    "decryption_failed": "✗ Gagal mendekripsi data",

    # Warnings
    "session_expired": "⚠ Sesi Anda telah berakhir, silakan login kembali",
    "weak_password": "⚠ Password Anda lemah, gunakan kombinasi huruf, angka, dan simbol",
    "backup_recommended": "⚠ Backup terakhir {days} hari yang lalu, backup sekarang?",

    # Info
    "no_notes": "ℹ Belum ada catatan, buat catatan pertama Anda!",
    "searching": "ℹ Mencari catatan...",
    "loading": "ℹ Memuat data...",
}

# ==================== EMOJI/ICONS ====================
ICONS = {
    'note': '📝',
    'lock': '🔒',
    'unlock': '🔓',
    'search': '🔍',
    'tag': '🏷️',
    'star': '⭐',
    'calendar': '📅',
    'attachment': '📎',
    'export': '💾',
    'backup': '🔄',
    'user': '👤',
    'settings': '⚙️',
    'trash': '🗑️',
    'edit': '✏️',
    'add': '➕',
    'remove': '➖',
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️',
}

# ==================== DEVELOPMENT ====================
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"
DEBUG = DEV_MODE
TESTING = False

# ==================== PLATFORM DETECTION ====================
import platform
PLATFORM = platform.system()  # Windows, Linux, Darwin (macOS)
IS_WINDOWS = PLATFORM == "Windows"
IS_LINUX = PLATFORM == "Linux"
IS_MACOS = PLATFORM == "Darwin"
