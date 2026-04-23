"""
Shadow VM Mode — Terminal Command Interface
Mengintegrasikan Shadow VM ke dalam Asisten Shadow v3

Fitur tambahan vs menu UI biasa:
- Command-line interface langsung (tanpa menu angka)
- Grep/search inline
- Export CLI
- Stats & info cepat
- Alias & history perintah
- Tag filter
- Batch operations
"""

import sys
import shlex
from pathlib import Path
from typing import Optional, List, Dict, Tuple, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from core.notes_manager import NotesManager
    from core.user_manager import UserManager

try:
    from rich.console import Console
    from rich.table import Table
    from rich.syntax import Syntax
    from rich import box
    RICH = True
    console = Console()
except ImportError:
    RICH = False

# ─── Color helpers ───────────────────────────────────────────────────────────

def _c(text: str, color: str = "green") -> str:
    """Wrap text in Rich color markup (no-op if Rich unavailable)."""
    if not RICH:
        return text
    return f"[{color}]{text}[/{color}]"

def _print(text: str, color: str = ""):
    if RICH:
        console.print(f"[{color}]{text}[/{color}]" if color else text)
    else:
        print(text)

def _ok(msg: str):   _print(f"✓ {msg}", "green")
def _err(msg: str):  _print(f"✗ {msg}", "red")
def _info(msg: str): _print(f"ℹ {msg}", "cyan")
def _warn(msg: str): _print(f"⚠ {msg}", "yellow")
def _sep():          _print("─" * 60, "dim")


# ─── VMShell ─────────────────────────────────────────────────────────────────

class VMShell:
    """
    Interactive Shadow VM shell.
    Dipanggil dari main.py saat user pilih 'VM Mode'.
    """

    PROMPT = "[bold red]root@shadow:[/bold red][dim]~[/dim][bold red]#[/bold red] " if RICH else "root@shadow:~# "

    def __init__(self, notes_manager, user_manager, current_user: dict, master_password: str, encryption_salt: bytes):
        self.nm    = notes_manager
        self.um    = user_manager
        self.user  = current_user
        self.mpwd  = master_password
        self.salt  = encryption_salt
        self.alias: Dict[str, str] = {}
        self.hist:  List[str]      = []
        self._running              = True

        # Map command name -> method
        self._cmds = {
            # notes
            "note":     self._cmd_note,
            "notes":    self._cmd_notes,
            "grep":     self._cmd_grep,
            "tags":     self._cmd_tags,
            "stats":    self._cmd_stats,
            "pinned":   self._cmd_pinned,
            "recent":   self._cmd_recent,
            # export
            "export":   self._cmd_export,
            "backup":   self._cmd_backup,
            # util
            "calc":     self._cmd_calc,
            "date":     self._cmd_date,
            "rand":     self._cmd_rand,
            "uuid":     self._cmd_uuid,
            "flip":     self._cmd_flip,
            "dice":     self._cmd_dice,
            "base64":   self._cmd_base64,
            "b64d":     self._cmd_b64d,
            "hash":     self._cmd_hash,
            "echo":     self._cmd_echo,
            # session
            "whoami":   self._cmd_whoami,
            "history":  self._cmd_history,
            "alias":    self._cmd_alias,
            "unalias":  self._cmd_unalias,
            "help":     self._cmd_help,
            "clear":    self._cmd_clear,
            "exit":     self._cmd_exit,
            "quit":     self._cmd_exit,
            "logout":   self._cmd_exit,
        }

    # ─── Run loop ──────────────────────────────────────────────────────────

    def run(self):
        _print("\n[bold green]Shadow VM Shell v4.0[/bold green]" if RICH else "\nShadow VM Shell v4.0")
        _info(f"Logged in as: {self.user['username']}")
        _info("Type 'help' for commands. 'exit' to return to main menu.")
        _sep()

        while self._running:
            try:
                if RICH:
                    raw = console.input(self.PROMPT).strip()
                else:
                    raw = input("root@shadow:~# ").strip()
            except (KeyboardInterrupt, EOFError):
                _print("\n^C", "dim")
                break

            if not raw:
                continue

            # Expand alias
            parts = raw.split()
            if parts[0] in self.alias:
                expanded = self.alias[parts[0]] + (" " + " ".join(parts[1:]) if parts[1:] else "")
                parts = expanded.split()
                raw = expanded

            self.hist.append(raw)

            cmd = parts[0]
            args = parts[1:]

            # tag: shorthand  e.g. tag:python
            if cmd.startswith("tag:"):
                self._filter_by_tag(cmd[4:])
                continue

            if cmd in self._cmds:
                try:
                    self._cmds[cmd](args)
                except Exception as e:
                    _err(f"Error: {e}")
            else:
                _err(f"Command not found: {cmd}  (try 'help')")

    # ─── NOTES ─────────────────────────────────────────────────────────────

    def _cmd_note(self, args: List[str]):
        if not args:
            return _err("Usage: note [new|view|del|edit|tag|pin|dup|mv|info] ...")

        sub = args[0]

        # ── new ──
        if sub == "new":
            title = " ".join(args[1:])
            if not title:
                return _err("Usage: note new TITLE")
            _info(f"Creating: \"{title}\"")
            _info("Type content. End with a line containing only: END")
            _sep()
            lines = []
            while True:
                try:
                    line = input()
                    if line.strip().upper() in ("END", "---END---", "--END--"):
                        break
                    lines.append(line)
                except EOFError:
                    break
            content = "\n".join(lines)
            if not content.strip():
                return _warn("Empty — cancelled")

            tags_input = input("Tags (comma-separated, or Enter to skip): ").strip()
            tags = [t.strip() for t in tags_input.split(",") if t.strip()]

            success, msg, nid = self.nm.create_note(
                self.user["id"], title, content,
                self.mpwd, self.salt, tags=tags
            )
            _ok(msg + f" (ID: {nid})") if success else _err(msg)
            return

        # ── view ──
        if sub == "view":
            note = self._get_note(args)
            if not note:
                return
            _sep()
            _print(f"[bold yellow][{note['id']}] {note['title']}[/bold yellow]" if RICH else f"[{note['id']}] {note['title']}")
            tags = note.get("tags", [])
            if tags:
                _print(f"Tags: {' '.join('#' + t for t in tags)}", "magenta")
            _sep()
            _print(note.get("content", ""), "white")
            _sep()
            return

        # ── del ──
        if sub in ("del", "delete", "rm"):
            note = self._get_note(args)
            if not note:
                return
            confirm = input(f"Delete #{note['id']} '{note['title']}'? [y/N] ").strip().lower()
            if confirm != "y":
                return _info("Cancelled")
            success, msg = self.nm.delete_note(note["id"], self.user["id"])
            _ok(msg) if success else _err(msg)
            return

        # ── edit ──
        if sub == "edit":
            note = self._get_note(args)
            if not note:
                return
            _info(f"Editing #{note['id']}: \"{note['title']}\"")
            _info("Type new content. END to finish. SKIP to keep current.")
            _sep()
            lines = []
            skip = False
            while True:
                try:
                    line = input()
                    if line.strip().upper() in ("END", "---END---"):
                        break
                    if line.strip().upper() in ("SKIP", "---SKIP---"):
                        skip = True
                        break
                    lines.append(line)
                except EOFError:
                    break
            new_content = None if skip else "\n".join(lines)
            new_title_input = input(f"New title (Enter to keep '{note['title']}'): ").strip()
            new_title = new_title_input or None

            success, msg = self.nm.update_note(
                note["id"], self.user["id"],
                title=new_title,
                content=new_content,
                master_password=self.mpwd if new_content else None,
                encryption_salt=self.salt if new_content else None,
            )
            _ok(msg) if success else _err(msg)
            return

        # ── tag ──
        if sub == "tag":
            note = self._get_note(args)
            if not note or len(args) < 3:
                return _err("Usage: note tag ID tag1,tag2")
            # tags are args[2:] joined
            raw_tags = " ".join(args[2:])
            tags = [t.strip() for t in raw_tags.replace(",", " ").split() if t.strip()]
            success, msg = self.nm.update_note(
                note["id"], self.user["id"],
                tags=tags
            )
            _ok(f"Tags updated: {tags}") if success else _err(msg)
            return

        # ── pin ──
        if sub == "pin":
            note = self._get_note(args)
            if not note:
                return
            success, msg = self.nm.toggle_favorite(note["id"], self.user["id"])
            _ok(msg) if success else _err(msg)
            return

        # ── dup ──
        if sub == "dup":
            note = self._get_note(args)
            if not note:
                return
            new_title = "Copy of " + note["title"]
            content = note.get("content", "")
            success, msg, nid = self.nm.create_note(
                self.user["id"], new_title, content,
                self.mpwd, self.salt
            )
            _ok(f"Duplicated as #{nid}: \"{new_title}\"") if success else _err(msg)
            return

        # ── mv ──
        if sub == "mv":
            note = self._get_note(args)
            if not note or len(args) < 3:
                return _err("Usage: note mv ID NEW_TITLE")
            new_title = " ".join(args[2:])
            success, msg = self.nm.update_note(note["id"], self.user["id"], title=new_title)
            _ok(f"Renamed → \"{new_title}\"") if success else _err(msg)
            return

        # ── info ──
        if sub == "info":
            note = self._get_note(args)
            if not note:
                return
            _sep()
            rows = [
                ("ID",      str(note["id"])),
                ("Title",   note["title"]),
                ("Tags",    ", ".join(note.get("tags", [])) or "(none)"),
                ("Pinned",  "YES ★" if note.get("is_favorite") else "no"),
                ("Locked",  "YES 🔒" if note.get("is_locked") else "no"),
                ("Created", str(note.get("created_at", ""))[:16]),
                ("Updated", str(note.get("updated_at", ""))[:16]),
                ("Chars",   str(len(note.get("content", "")))),
                ("Words",   str(len(note.get("content", "").split()))),
                ("Lines",   str(note.get("content", "").count("\n") + 1)),
            ]
            for k, v in rows:
                _print(f"  [cyan]{k:<12}[/cyan][white]{v}[/white]" if RICH else f"  {k:<12}{v}")
            _sep()
            return

        _err(f"Unknown sub-command: {sub}")

    def _cmd_notes(self, args: List[str]):
        sub = args[0] if args else "list"
        notes = self.nm.list_notes(
            self.user["id"],
            include_archived=False,
            favorites_only=(sub == "pinned"),
            limit=200,
        )
        if not notes:
            return _info("No notes found. Create with: note new TITLE")

        if sub in ("list", ""):
            if RICH:
                t = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
                t.add_column("ID", style="dim", width=5)
                t.add_column("★", width=3)
                t.add_column("🔒", width=3)
                t.add_column("Title", style="bold")
                t.add_column("Tags", width=24)
                t.add_column("Updated", width=16)
                for n in notes:
                    pin  = "★" if n.get("is_favorite") else ""
                    lock = "🔒" if n.get("is_locked")  else ""
                    tags = " ".join(f"#{t}" for t in n.get("tags", [])[:3])
                    upd  = str(n.get("updated_at", ""))[:16]
                    t.add_row(str(n["id"]), pin, lock, n.get("title", "")[:45], tags, upd)
                console.print(t)
            else:
                print(f"{'ID':<5} {'Title':<40} {'Tags'}")
                for n in notes:
                    tags = ",".join(n.get("tags", []))
                    print(f"{n['id']:<5} {n.get('title','')[:40]:<40} {tags}")
            _info(f"Total: {len(notes)}")

        elif sub == "all":
            for n in notes:
                _print(f"\n[yellow bold][{n['id']}] {n['title']}[/yellow bold]" if RICH else f"\n[{n['id']}] {n['title']}")
                content = n.get("content", "")
                preview = content[:150].replace("\n", " ")
                _print(f"  {preview}{'...' if len(content) > 150 else ''}", "white")

    def _cmd_grep(self, args: List[str]):
        query = " ".join(args).lower()
        if not query:
            return _err("Usage: grep QUERY")
        notes = self.nm.search_notes(self.user["id"], query, master_password=self.mpwd)
        if not notes:
            return _info(f'No results for: "{query}"')
        _ok(f'{len(notes)} result(s) for "{query}":')
        for n in notes:
            _print(f"\n  [cyan][{n['id']}][/cyan] [yellow]{n['title']}[/yellow]" if RICH else f"  [{n['id']}] {n['title']}")
            content = n.get("content", "")
            idx = content.lower().find(query)
            if idx >= 0:
                snip = content[max(0, idx-30): idx+80].replace("\n", " ")
                _print(f"  ...{snip}...", "dim")

    def _cmd_tags(self, _):
        notes = self.nm.list_notes(self.user["id"], limit=999)
        counts: Dict[str, int] = {}
        for n in notes:
            for t in n.get("tags", []):
                counts[t] = counts.get(t, 0) + 1
        if not counts:
            return _info("No tags found")
        _print(f"{'TAG':<20} COUNT", "green")
        for tag, cnt in sorted(counts.items(), key=lambda x: -x[1]):
            _print(f"  {'#' + tag:<20} {cnt}", "magenta")

    def _filter_by_tag(self, tag: str):
        notes = self.nm.list_notes(self.user["id"], limit=999)
        found = [n for n in notes if tag in n.get("tags", [])]
        if not found:
            return _info(f"No notes with tag #{tag}")
        _ok(f"Notes tagged #{tag}: {len(found)}")
        for n in found:
            _print(f"  [{n['id']}] {n['title']}", "white")

    def _cmd_stats(self, _):
        notes = self.nm.list_notes(self.user["id"], include_archived=True, limit=9999)
        total    = len(notes)
        pinned   = sum(1 for n in notes if n.get("is_favorite"))
        locked   = sum(1 for n in notes if n.get("is_locked"))
        all_tags = set(t for n in notes for t in n.get("tags", []))
        words    = sum(len(n.get("content", "").split()) for n in notes)
        chars    = sum(len(n.get("content", "")) for n in notes)
        _sep()
        rows = [
            ("Notes",       total),
            ("Pinned",      pinned),
            ("Locked",      locked),
            ("Tags",        len(all_tags)),
            ("Total Words", words),
            ("Total Chars", chars),
            ("User",        self.user["username"]),
        ]
        for k, v in rows:
            _print(f"  [cyan]{k:<16}[/cyan][bold green]{v}[/bold green]" if RICH else f"  {k:<16}{v}")
        _sep()

    def _cmd_pinned(self, _):
        notes = self.nm.list_notes(self.user["id"], favorites_only=True, limit=999)
        if not notes:
            return _info("No pinned notes")
        for n in notes:
            _print(f"  ★ [{n['id']}] {n['title']}", "yellow")

    def _cmd_recent(self, args: List[str]):
        n = int(args[0]) if args and args[0].isdigit() else 5
        notes = self.nm.list_notes(self.user["id"], limit=n)
        for note in notes:
            upd = str(note.get("updated_at", ""))[:16]
            _print(f"  [dim]{upd}[/dim]  [cyan][{note['id']}][/cyan] {note['title']}" if RICH else f"  {upd}  [{note['id']}] {note['title']}")

    # ─── EXPORT ─────────────────────────────────────────────────────────────

    def _cmd_export(self, args: List[str]):
        import json
        sub = args[0] if args else "json"
        notes = self.nm.list_notes(self.user["id"], limit=9999)

        if sub == "json":
            import config
            path = config.EXPORTS_DIR / f"shadow-export-{datetime.now():%Y%m%d-%H%M%S}.json"
            data = [{"id": n["id"], "title": n["title"], "content": n.get("content", ""),
                     "tags": n.get("tags", []), "pinned": n.get("is_favorite", False),
                     "created": str(n.get("created_at", "")), "updated": str(n.get("updated_at", ""))}
                    for n in notes]
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            _ok(f"Exported {len(notes)} notes → {path}")

        elif sub == "md":
            import config
            path = config.EXPORTS_DIR / f"shadow-notes-{datetime.now():%Y%m%d}.md"
            lines = [f"# Shadow Notes Export\n_{datetime.now().strftime('%d %b %Y %H:%M')}_\n\n---\n"]
            for n in notes:
                lines.append(f"## [{n['id']}] {n['title']}")
                lines.append(f"**Tags:** {', '.join(n.get('tags', [])) or 'none'}  |  **Pinned:** {'Yes' if n.get('is_favorite') else 'No'}\n")
                lines.append(n.get("content", "") + "\n\n---\n")
            path.write_text("\n".join(lines))
            _ok(f"Exported → {path}")

        elif sub == "note":
            note = self._get_note(args[1:])
            if not note:
                return
            import config
            path = config.EXPORTS_DIR / f"note-{note['id']}.txt"
            path.write_text(note.get("content", ""))
            _ok(f"Note #{note['id']} → {path}")

        else:
            _err("Usage: export [json|md|note ID]")

    def _cmd_backup(self, _):
        import json, config
        notes = self.nm.list_notes(self.user["id"], limit=9999)
        data = {
            "version": "4.0",
            "timestamp": datetime.now().isoformat(),
            "user": self.user["username"],
            "notes": [{"id": n["id"], "title": n["title"], "content": n.get("content", ""),
                       "tags": n.get("tags", []), "pinned": n.get("is_favorite", False)}
                      for n in notes],
        }
        path = config.BACKUPS_DIR / f"backup-{datetime.now():%Y%m%d-%H%M%S}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        _ok(f"Backup saved → {path}")

    # ─── UTIL ───────────────────────────────────────────────────────────────

    def _cmd_calc(self, args: List[str]):
        expr = " ".join(args)
        if not expr:
            return _err("Usage: calc EXPRESSION")
        try:
            import ast
            result = eval(compile(ast.parse(expr, mode="eval"), "<calc>", "eval"),
                          {"__builtins__": {}}, {})
            _print(f"[white]{expr}[/white] = [bold green]{result}[/bold green]" if RICH else f"{expr} = {result}")
        except Exception:
            _err("Invalid expression")

    def _cmd_date(self, _):
        now = datetime.now()
        _print(now.strftime("%A, %d %B %Y — %H:%M:%S"), "white")
        _print(f"Unix: {int(now.timestamp())}", "dim")

    def _cmd_rand(self, args: List[str]):
        import random
        n = int(args[0]) if args and args[0].isdigit() else 100
        _print(str(random.randint(0, n)), "green")

    def _cmd_uuid(self, _):
        import uuid
        _print(str(uuid.uuid4()), "cyan")

    def _cmd_flip(self, _):
        import random
        _print("HEADS ★" if random.random() > 0.5 else "TAILS", "yellow")

    def _cmd_dice(self, args: List[str]):
        import random
        n = int(args[0]) if args and args[0].isdigit() else 6
        r = random.randint(1, n)
        _print(f"d{n}: [bold green]{r}[/bold green]" if RICH else f"d{n}: {r}")

    def _cmd_base64(self, args: List[str]):
        import base64
        text = " ".join(args)
        if not text:
            return _err("Usage: base64 TEXT")
        _print(base64.b64encode(text.encode()).decode(), "cyan")

    def _cmd_b64d(self, args: List[str]):
        import base64
        try:
            _print(base64.b64decode(args[0]).decode(), "white")
        except Exception:
            _err("Invalid base64")

    def _cmd_hash(self, args: List[str]):
        import hashlib
        text = " ".join(args)
        if not text:
            return _err("Usage: hash TEXT")
        h = hashlib.sha256(text.encode()).hexdigest()
        _print(f"SHA-256({text}):", "dim")
        _print(h, "cyan")

    def _cmd_echo(self, args: List[str]):
        _print(" ".join(args), "white")

    # ─── SESSION ────────────────────────────────────────────────────────────

    def _cmd_whoami(self, _):
        _print(f"uid=0(root) user={self.user['username']} email={self.user.get('email','')}", "white")

    def _cmd_history(self, _):
        if not self.hist:
            return _info("No history")
        for i, cmd in enumerate(self.hist, 1):
            _print(f"  [dim]{i:>3}[/dim]  {cmd}" if RICH else f"  {i:>3}  {cmd}")

    def _cmd_alias(self, args: List[str]):
        if not args:
            if not self.alias:
                return _info("No aliases")
            for k, v in self.alias.items():
                _print(f"  alias [cyan]{k}[/cyan]='{v}'" if RICH else f"  alias {k}='{v}'")
            return
        raw = " ".join(args)
        if "=" not in raw:
            return _err("Usage: alias NAME=COMMAND")
        k, v = raw.split("=", 1)
        self.alias[k.strip()] = v.strip()
        _ok(f"Alias: {k.strip()} = {v.strip()}")

    def _cmd_unalias(self, args: List[str]):
        if not args:
            return _err("Usage: unalias NAME")
        if args[0] in self.alias:
            del self.alias[args[0]]
            _ok(f"Removed: {args[0]}")
        else:
            _err(f"No alias: {args[0]}")

    def _cmd_help(self, args: List[str]):
        categories = {
            "Notes": [
                ("note new TITLE",       "Buat catatan baru"),
                ("notes list",           "Daftar semua catatan"),
                ("notes all",            "List + preview content"),
                ("note view ID",         "Tampilkan catatan"),
                ("note del ID",          "Hapus catatan"),
                ("note edit ID",         "Edit catatan"),
                ("note tag ID tags",     "Tambah tag"),
                ("note pin ID",          "Toggle favorite"),
                ("note dup ID",          "Duplikat catatan"),
                ("note mv ID TITLE",     "Rename catatan"),
                ("note info ID",         "Meta detail catatan"),
                ("grep QUERY",           "Cari teks dalam catatan"),
                ("tags",                 "Daftar semua tag"),
                ("tag:TAGNAME",          "Filter by tag"),
                ("stats",                "Statistik catatan"),
                ("pinned",               "Catatan ter-pin"),
                ("recent [N]",           "N catatan terbaru"),
            ],
            "Export": [
                ("export json",          "Export semua ke JSON"),
                ("export md",            "Export ke Markdown"),
                ("export note ID",       "Export satu catatan"),
                ("backup",               "Backup snapshot"),
            ],
            "Util": [
                ("calc EXPR",            "Kalkulator"),
                ("base64 TEXT",          "Encode Base64"),
                ("b64d TEXT",            "Decode Base64"),
                ("hash TEXT",            "SHA-256 hash"),
                ("date",                 "Waktu sekarang"),
                ("rand [N]",             "Angka random"),
                ("uuid",                 "Generate UUID"),
                ("flip",                 "Coin flip"),
                ("dice [N]",             "Roll dadu"),
                ("echo TEXT",            "Print teks"),
            ],
            "Session": [
                ("alias NAME=CMD",       "Buat alias"),
                ("unalias NAME",         "Hapus alias"),
                ("history",              "Riwayat perintah"),
                ("whoami",               "Info user"),
                ("clear",                "Bersihkan layar"),
                ("exit / quit",          "Kembali ke main menu"),
            ],
        }
        filt = args[0].lower() if args else None
        cats = {k: v for k, v in categories.items() if not filt or k.lower().startswith(filt)}
        for cat, cmds in cats.items():
            _print(f"\n[bold yellow]── {cat} ──[/bold yellow]" if RICH else f"\n── {cat} ──")
            for c, d in cmds:
                if RICH:
                    console.print(f"  [green]{c:<26}[/green][white]{d}[/white]")
                else:
                    print(f"  {c:<26}{d}")

    def _cmd_clear(self, _):
        import os
        os.system("cls" if sys.platform == "win32" else "clear")

    def _cmd_exit(self, _):
        _ok("Exiting VM shell → main menu")
        self._running = False

    # ─── HELPERS ─────────────────────────────────────────────────────────────

    def _get_note(self, args: List[str]) -> Optional[dict]:
        """Resolve note ID from args[0] (or args[1] for sub-commands)."""
        id_str = args[0] if args else None
        if not id_str or not id_str.isdigit():
            _err("Provide note ID")
            return None
        note_id = int(id_str)
        success, msg, note = self.nm.get_note(
            note_id, self.user["id"],
            master_password=self.mpwd
        )
        if not success:
            _err(msg)
            return None
        return note
