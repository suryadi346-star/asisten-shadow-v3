# 🔥 Asisten Shadow v3.0

<div align="center">

![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**Multi-Platform Encrypted Note-Taking App**

[Features](#-features) • [Security](#-security) • [Installation](#-installation) • [Usage](#-usage) • [Screenshots](#-screenshots)

</div>

---

## 🎯 What's New in v3.0

### 🔒 **Real Security**
- ✅ **AES-256-GCM** encryption (not Base64!)
- ✅ **PBKDF2** key derivation (100,000 iterations)
- ✅ **Zero-knowledge architecture**
- ✅ Unique salt + IV per note

### ⚡ **Performance**
- ✅ **SQLite** database (not JSON files!)
- ✅ **Full-text search** with FTS5
- ✅ Proper indexing & query optimization
- ✅ WAL mode for concurrent access

### 🎨 **Beautiful UI**
- ✅ **Rich Terminal** with colors & formatting
- ✅ Interactive menus
- ✅ Real-time updates
- ✅ Markdown rendering

### ✨ **Advanced Features**
- ✅ Tags & favorites
- ✅ Version history
- ✅ Lock individual notes
- ✅ Full-text search
- ✅ Activity logging

---

## 🚀 Features

### Core Features
- 📝 **Create, Read, Update, Delete** notes
- 🔒 **End-to-end encryption** (AES-256)
- 🔍 **Full-text search** (instant results)
- 🏷️ **Tags & organization**
- ⭐ **Favorites & archive**
- 📦 **Version history**

### Security
- 🔐 **AES-256-GCM** encryption
- 🔑 **PBKDF2** key derivation
- 🛡️ **Per-user encryption salt**
- 🔒 **Additional note-level locks**
- ⚠️ **Zero-knowledge** (we can't read your notes)

### User Experience
- 🎨 **Beautiful terminal UI** (Rich library)
- ⌨️ **Keyboard shortcuts**
- 🌈 **Syntax highlighting**
- 📊 **Statistics & analytics**
- 💾 **Auto-backup** (optional)

---

## 🔒 Security

### Encryption Flow

```
Your Password
    ↓
PBKDF2 (100,000 iterations)
    ↓
256-bit Encryption Key
    ↓
AES-256-GCM Encryption
    ↓
Encrypted Note (with unique IV)
    ↓
SQLite Database
```

### What We Store
- ❌ **NOT** your password (only hash)
- ❌ **NOT** your encryption key (derived each time)
- ✅ **ONLY** encrypted content
- ✅ **ONLY** password hash (PBKDF2)

### Zero-Knowledge
- Your notes are encrypted with **your password**
- We (developers) **cannot read** your notes
- Even if database is stolen, notes are **still encrypted**
- Forgot password = **lost access** (by design)

---

## ⚡ Installation

### Quick Start

```bash
# Clone repository
git clone https://github.com/suryadi346-star/asisten-shadow-v3.git
cd asisten-shadow-v3

# Run launcher (auto-setup)
./run.sh  # Linux/Mac
# or
run.bat   # Windows
```

### Manual Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run
cd src
python main.py
```

### Requirements
- Python 3.7+
- cryptography library
- rich library

---

## 💻 Usage

### First Time

1. **Run application**
   ```bash
   ./run.sh
   ```

2. **Register account**
   - Choose "Register"
   - Enter username (min 3 chars)
   - Enter password (min 8 chars)
   - Confirm password

3. **Login**
   - Choose "Login"
   - Enter credentials

4. **Create note**
   - Choose "Buat Catatan Baru"
   - Enter title
   - Write content
   - Type `---END---` to finish
   - Add tags (optional)
   - Lock note (optional)

### Daily Use

```bash
# Launch app
./run.sh

# Login with your credentials

# Quick actions:
1 → Create new note
2 → List all notes
3 → View note
4 → Search notes
5 → Edit/Delete note
6 → View favorites
```

---

## 🎨 Screenshots

### Main Menu
```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     📝  ASISTEN SHADOW v3.0.2                             ║
║                                                           ║
║     Aplikasi Catatan Terenkripsi                          ║
║     Multi-platform • Secure • User-friendly               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

🔒 AES-256 Encryption • 🔍 Full-Text Search • ⚡ Lightning Fast
```

### Dashboard
```
════════════════════════════════════════════════════════════
       DASHBOARD - username
       📝 10 notes • ⭐ 3 favorites • 🔒 2 locked
════════════════════════════════════════════════════════════

═══ MENU ═══

  1. ➕ Buat Catatan Baru
  2. 📝 Lihat Semua Catatan
  3. 📝 Buka Catatan
  4. 🔍 Cari Catatan
  5. ✏️ Kelola Catatan
```

---

## 🔥 What Makes v3.0 Different?

### vs v2.0

| Feature | v2.0 | v3.0 |
|---------|------|------|
| **Encryption** | Base64 (not real) | AES-256-GCM ✓ |
| **Database** | JSON files | SQLite ✓ |
| **Search** | Basic keyword | Full-text (FTS5) ✓ |
| **UI** | Plain text | Rich colors ✓ |
| **Performance** | Slow with 100+ notes | Fast with 10,000+ ✓ |
| **Security** | Weak | Military-grade ✓ |

### vs Competitors

**Simplenote:**
- ❌ Cloud-only (privacy concern)
- ❌ No encryption by default
- ✅ But simpler UI

**Standard Notes:**
- ✅ Good encryption
- ❌ Paid for many features
- ❌ Complex setup

**Asisten Shadow:**
- ✅ **Free & open source**
- ✅ **Military-grade encryption**
- ✅ **Works offline**
- ✅ **No cloud dependency**
- ✅ **Beautiful UI**

---

## 📊 Performance

Tested on:
- Hardware: i5 processor, 8GB RAM
- OS: Ubuntu 22.04
- Dataset: 1,000 notes

| Operation | Time |
|-----------|------|
| Create note | ~50ms |
| Search (FTS5) | ~5ms |
| List 100 notes | ~20ms |
| Encrypt note | ~10ms |
| Decrypt note | ~8ms |

**Memory Usage:** ~30MB (with 1,000 notes loaded)

---

## 🛠️ Architecture

```
asisten-shadow-v3/
├── src/
│   ├── core/
│   │   ├── crypto.py         # AES-256 encryption
│   │   ├── database.py       # SQLite manager
│   │   ├── user_manager.py   # User auth
│   │   └── notes_manager.py  # Notes CRUD
│   ├── terminal/
│   │   ├── ui.py             # Rich terminal UI
│   │   └── vm_mode.py
│   ├── config.py             # Configuration
│   └── main.py               # Entry point
├── data/                     # SQLite database
├── tests/                    # Unit tests
└── requirements.txt
```

---

## 🔜 Roadmap

### v3.1 (Next)
- [ ] Web interface (FastAPI + React)
- [ ] REST API
- [ ] File attachments
- [ ] Export to PDF/Markdown

### v3.5 (Future)
- [ ] Desktop app (Electron)
- [ ] Mobile app (React Native)
- [ ] Cloud sync (optional, encrypted)
- [ ] Collaboration features

### v4.0 (Long-term)
- [ ] AI integration (auto-tagging, summarization)
- [ ] End-to-end encrypted sharing
- [ ] Plugin system
- [ ] Multi-vault support

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📜 License

MIT License - See [LICENSE](LICENSE)

---

## 🙏 Credits

- **Encryption:** [Cryptography](https://cryptography.io/)
- **Terminal UI:** [Rich](https://rich.readthedocs.io/)
- **Database:** SQLite

---

## 📞 Support

- GitHub Issues: [Report bugs](https://github.com/suryadi346-star/asisten-shadow-v3/issues)
- Discussions: [Ask questions](https://github.com/suryadi346-star/asisten-shadow-v3/discussions)

---

<div align="center">

**⭐ Star this repo if you find it useful! ⭐**

Made with ❤️ by Asisten Shadow Team

</div>
