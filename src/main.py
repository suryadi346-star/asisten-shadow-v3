"""
Asisten Shadow v3.0 - Main Terminal Application
Beautiful, Secure, User-Friendly
"""

import sys
from pathlib import Path
import base64

sys.path.append(str(Path(__file__).parent))

from core.database import Database
from core.user_manager import UserManager
from core.notes_manager import NotesManager
from terminal.ui import UI
import config


class AsistenShadow:
    """Main application class"""
    
    def __init__(self):
        self.db = Database()
        self.user_manager = UserManager(self.db)
        self.notes_manager = NotesManager(self.db)
        
        self.current_user = None
        self.master_password = None
        self.encryption_salt = None
    
    def run(self):
        """Main application loop"""
        UI.welcome()
        
        while True:
            if not self.current_user:
                # Not logged in - show main menu
                choice = self._main_menu()
                
                if choice == "1":
                    self._register()
                elif choice == "2":
                    self._login()
                elif choice == "3":
                    self._about()
                elif choice == "0":
                    break
            else:
                # Logged in - show dashboard
                choice = self._dashboard_menu()
                
                if choice == "1":
                    self._create_note()
                elif choice == "2":
                    self._list_notes()
                elif choice == "3":
                    self._view_note()
                elif choice == "4":
                    self._search_notes()
                elif choice == "5":
                    self._manage_note()
                elif choice == "6":
                    self._favorites()
                elif choice == "7":
                    self._statistics()
                elif choice == "8":
                    self._settings()
                elif choice == "0":
                    self._logout()
        
        UI.goodbye()
        self.db.close()
    
    # ==================== MENUS ====================
    
    def _main_menu(self):
        """Main menu (not logged in)"""
        return UI.menu(
            "MENU UTAMA",
            [
                "Register - Buat akun baru",
                "Login - Masuk ke akun",
                "Tentang Aplikasi"
            ]
        )
    
    def _dashboard_menu(self):
        """Dashboard menu (logged in)"""
        username = self.current_user['username']
        
        # Get quick stats
        stats = self.notes_manager.get_statistics(self.current_user['id'])
        
        UI.header(
            f"DASHBOARD - {username}",
            f"📝 {stats['total']} notes • ⭐ {stats['favorites']} favorites • 🔒 {stats['locked']} locked"
        )
        
        return UI.menu(
            "MENU",
            [
                f"{config.ICONS['add']} Buat Catatan Baru",
                f"{config.ICONS['note']} Lihat Semua Catatan",
                f"{config.ICONS['note']} Buka Catatan",
                f"{config.ICONS['search']} Cari Catatan",
                f"{config.ICONS['edit']} Kelola Catatan (Edit/Hapus)",
                f"{config.ICONS['star']} Favorites",
                f"{config.ICONS['info']} Statistik",
                f"{config.ICONS['settings']} Pengaturan"
            ]
        )
    
    # ==================== AUTH ====================
    
    def _register(self):
        """Register new user"""
        UI.section("REGISTRASI PENGGUNA BARU")
        
        username = UI.prompt("Username (min 3 karakter)")
        if not username:
            return
        
        email = UI.prompt("Email (opsional)", default="")
        
        password = UI.prompt("Password (min 8 karakter)", password=True)
        if not password:
            return
        
        confirm = UI.prompt("Konfirmasi Password", password=True)
        
        if password != confirm:
            UI.error("Password tidak cocok!")
            return
        
        # Register
        with UI.loading("Membuat akun...") as progress:
            task = progress.add_task("Registering...", total=None)
            success, message, user_id = self.user_manager.register(username, password, email)
        
        if success:
            UI.success(message)
            UI.info("Silakan login dengan akun baru Anda")
        else:
            UI.error(message)
    
    def _login(self):
        """Login user"""
        UI.section("LOGIN")
        
        username = UI.prompt("Username")
        if not username:
            return
        
        password = UI.prompt("Password", password=True)
        if not password:
            return
        
        # Login
        with UI.loading("Memverifikasi...") as progress:
            task = progress.add_task("Logging in...", total=None)
            success, message, user_data = self.user_manager.login(username, password)
        
        if success:
            self.current_user = user_data
            self.master_password = password  # Store for encryption
            
            # Get encryption salt
            self.encryption_salt = self.user_manager.get_encryption_salt(user_data['id'])
            
            UI.success(message)
            UI.info(f"Terakhir login: {user_data.get('last_login', 'Pertama kali')}")
        else:
            UI.error(message)
    
    def _logout(self):
        """Logout user"""
        if UI.confirm("Yakin ingin logout?"):
            self.current_user = None
            self.master_password = None
            self.encryption_salt = None
            
            UI.success("Logout berhasil!")
    
    # ==================== NOTES ====================
    
    def _create_note(self):
        """Create new note"""
        UI.section("BUAT CATATAN BARU")
        
        title = UI.prompt("Judul catatan")
        if not title:
            return
        
        UI.info("Tulis catatan (ketik '---END---' di baris baru untuk selesai)")
        
        content_lines = []
        while True:
            line = input()
            if line.strip() == "---END---":
                break
            content_lines.append(line)
        
        content = "\n".join(content_lines)
        
        if not content.strip():
            UI.warning("Catatan kosong, dibatalkan")
            return
        
        # Tags
        tags_input = UI.prompt("Tags (pisahkan dengan koma, opsional)", default="")
        tags = [t.strip() for t in tags_input.split(",")] if tags_input else []
        
        # Lock
        lock_note = UI.confirm("Kunci catatan dengan password?", default=False)
        lock_password = None
        if lock_note:
            lock_password = UI.prompt("Password untuk catatan ini", password=True)
        
        # Create
        with UI.loading("Membuat catatan...") as progress:
            task = progress.add_task("Creating...", total=None)
            success, message, note_id = self.notes_manager.create_note(
                self.current_user['id'],
                title,
                content,
                self.master_password,
                self.encryption_salt,
                tags=tags,
                is_locked=lock_note,
                lock_password=lock_password
            )
        
        if success:
            UI.success(f"{message} (ID: {note_id})")
        else:
            UI.error(message)
    
    def _list_notes(self):
        """List all notes"""
        UI.section("DAFTAR CATATAN")
        
        # Options
        include_archived = UI.confirm("Tampilkan arsip?", default=False)
        favorites_only = UI.confirm("Hanya favorites?", default=False)
        
        # Get notes
        notes = self.notes_manager.list_notes(
            self.current_user['id'],
            include_archived=include_archived,
            favorites_only=favorites_only,
            limit=50
        )
        
        if not notes:
            UI.info("Tidak ada catatan")
            return
        
        UI.notes_table(notes)
        UI.info(f"Total: {len(notes)} catatan")
    
    def _view_note(self):
        """View note content"""
        note_id = UI.prompt("ID Catatan")
        if not note_id.isdigit():
            return
        
        note_id = int(note_id)
        
        # Get note
        success, message, note = self.notes_manager.get_note(
            note_id,
            self.current_user['id'],
            master_password=self.master_password
        )
        
        if not success:
            if "terkunci" in message.lower():
                # Locked note
                lock_password = UI.prompt("Password catatan", password=True)
                success, message, note = self.notes_manager.get_note(
                    note_id,
                    self.current_user['id'],
                    master_password=self.master_password,
                    lock_password=lock_password
                )
                
                if not success:
                    UI.error(message)
                    return
            else:
                UI.error(message)
                return
        
        # Display note
        UI.clear()
        UI.note_card(note, show_content=False)
        UI.separator()
        
        # Render content as markdown
        if config.ENABLE_MARKDOWN:
            UI.markdown(note['content'])
        else:
            UI.print(note['content'])
        
        UI.separator()
        UI.info("Tekan Enter untuk kembali")
        input()
    
    def _search_notes(self):
        """Search notes"""
        UI.section("CARI CATATAN")
        
        query = UI.prompt("Kata kunci")
        if not query:
            return
        
        # Search
        with UI.loading("Mencari...") as progress:
            task = progress.add_task("Searching...", total=None)
            notes = self.notes_manager.search_notes(
                self.current_user['id'],
                query,
                master_password=self.master_password
            )
        
        if not notes:
            UI.info(f"Tidak ditemukan catatan dengan kata kunci: '{query}'")
            return
        
        UI.success(f"Ditemukan {len(notes)} catatan")
        UI.notes_table(notes)
    
    def _manage_note(self):
        """Edit or delete note"""
        UI.section("KELOLA CATATAN")
        
        note_id = UI.prompt("ID Catatan")
        if not note_id.isdigit():
            return
        
        note_id = int(note_id)
        
        # Get note info
        success, _, note = self.notes_manager.get_note(
            note_id,
            self.current_user['id']
        )
        
        if not success:
            UI.error("Catatan tidak ditemukan")
            return
        
        UI.note_card(note, show_content=False)
        
        action = UI.menu(
            "AKSI",
            [
                f"{config.ICONS['edit']} Edit",
                f"{config.ICONS['star']} Toggle Favorite",
                "📦 Toggle Archive",
                f"{config.ICONS['trash']} Hapus"
            ]
        )
        
        if action == "1":
            self._edit_note(note_id)
        elif action == "2":
            success, msg = self.notes_manager.toggle_favorite(note_id, self.current_user['id'])
            UI.success(msg) if success else UI.error(msg)
        elif action == "3":
            success, msg = self.notes_manager.toggle_archive(note_id, self.current_user['id'])
            UI.success(msg) if success else UI.error(msg)
        elif action == "4":
            self._delete_note(note_id, note.get('is_locked', False))
    
    def _edit_note(self, note_id: int):
        """Edit note"""
        # Get current content
        success, _, note = self.notes_manager.get_note(
            note_id,
            self.current_user['id'],
            master_password=self.master_password
        )
        
        if not success:
            UI.error("Gagal mengambil catatan")
            return
        
        UI.info("Edit judul (kosongkan untuk tidak mengubah)")
        new_title = UI.prompt("Judul baru", default=note['title'])
        
        UI.info("Edit content (ketik '---END---' untuk selesai, atau '---SKIP---' untuk tidak mengubah)")
        UI.print(f"Content saat ini:\n{note['content'][:200]}...\n")
        
        content_lines = []
        while True:
            line = input()
            if line.strip() == "---END---":
                break
            if line.strip() == "---SKIP---":
                content_lines = None
                break
            content_lines.append(line)
        
        new_content = "\n".join(content_lines) if content_lines else None
        
        # Update
        success, message = self.notes_manager.update_note(
            note_id,
            self.current_user['id'],
            title=new_title if new_title != note['title'] else None,
            content=new_content,
            master_password=self.master_password if new_content else None,
            encryption_salt=self.encryption_salt if new_content else None
        )
        
        UI.success(message) if success else UI.error(message)
    
    def _delete_note(self, note_id: int, is_locked: bool):
        """Delete note"""
        if not UI.confirm("⚠ Yakin ingin menghapus catatan ini?"):
            return
        
        lock_password = None
        if is_locked:
            lock_password = UI.prompt("Password catatan", password=True)
        
        success, message = self.notes_manager.delete_note(
            note_id,
            self.current_user['id'],
            lock_password=lock_password
        )
        
        UI.success(message) if success else UI.error(message)
    
    def _favorites(self):
        """Show favorite notes"""
        UI.section("CATATAN FAVORIT")
        
        notes = self.notes_manager.list_notes(
            self.current_user['id'],
            favorites_only=True
        )
        
        if not notes:
            UI.info("Belum ada catatan favorit")
            return
        
        UI.notes_table(notes)
    
    def _statistics(self):
        """Show statistics"""
        UI.clear()
        UI.section("STATISTIK")
        
        user_stats = self.user_manager.get_stats(self.current_user['id'])
        notes_stats = self.notes_manager.get_statistics(self.current_user['id'])
        
        combined_stats = {**user_stats, **notes_stats}
        UI.stats_panel(combined_stats)
        
        UI.info("Tekan Enter untuk kembali")
        input()
    
    def _settings(self):
        """Settings menu"""
        choice = UI.menu(
            "PENGATURAN",
            [
                "Ubah Password",
                "Edit Profil",
                "Hapus Akun"
            ]
        )
        
        if choice == "1":
            self._change_password()
        elif choice == "2":
            self._edit_profile()
        elif choice == "3":
            self._delete_account()
    
    def _change_password(self):
        """Change password"""
        UI.section("UBAH PASSWORD")
        
        old_password = UI.prompt("Password lama", password=True)
        new_password = UI.prompt("Password baru", password=True)
        confirm = UI.prompt("Konfirmasi password baru", password=True)
        
        if new_password != confirm:
            UI.error("Password baru tidak cocok!")
            return
        
        success, message = self.user_manager.change_password(
            self.current_user['id'],
            old_password,
            new_password
        )
        
        if success:
            UI.success(message)
            self.master_password = new_password  # Update stored password
        else:
            UI.error(message)
    
    def _edit_profile(self):
        """Edit user profile"""
        UI.section("EDIT PROFIL")
        
        user = self.user_manager.get_user(self.current_user['id'])
        
        email = UI.prompt("Email", default=user.get('email', ''))
        bio = UI.prompt("Bio", default=user.get('bio', ''))
        
        success, message = self.user_manager.update_profile(
            self.current_user['id'],
            email=email,
            bio=bio
        )
        
        UI.success(message) if success else UI.error(message)
    
    def _delete_account(self):
        """Delete account"""
        UI.warning("⚠ PERHATIAN: Aksi ini akan menghapus SEMUA data Anda!")
        
        if not UI.confirm("Yakin ingin menghapus akun?"):
            return
        
        password = UI.prompt("Konfirmasi dengan password Anda", password=True)
        
        success, message = self.user_manager.delete_user(
            self.current_user['id'],
            password
        )
        
        if success:
            UI.success(message)
            self.current_user = None
            self.master_password = None
        else:
            UI.error(message)
    
    def _about(self):
        """About application"""
        UI.clear()
        UI.header(
            f"ASISTEN SHADOW v{config.VERSION}",
            "Aplikasi Catatan Terenkripsi Multi-Platform"
        )
        
        about_text = f"""
## 🔒 Keamanan
- **AES-256-GCM** encryption untuk semua catatan
- **PBKDF2** key derivation dengan 100,000 iterasi
- **Zero-knowledge architecture** - password tidak pernah disimpan

## ⚡ Fitur
- Full-text search dengan FTS5
- Tags & favorites
- Version history
- Markdown support
- Lock individual notes

## 📊 Platform
- Terminal UI (Rich library)
- SQLite database
- Cross-platform (Windows, Linux, macOS)

## 🚀 GitHub
{config.GITHUB_URL}

## 👨‍💻 Developer
{config.AUTHOR}
"""
        
        UI.markdown(about_text)
        UI.info("Tekan Enter untuk kembali")
        input()


def main():
    """Entry point"""
    try:
        app = AsistenShadow()
        app.run()
    except KeyboardInterrupt:
        UI.goodbye()
    except Exception as e:
        UI.error(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
