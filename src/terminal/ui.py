
"""
Rich Terminal UI - Beautiful Console Interface
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich import box
from rich.layout import Layout
from rich.align import Align
from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
import config

# Initialize console
console = Console()


class UI:
    """Rich Terminal UI utilities"""

    @staticmethod
    def clear():
        """Clear screen"""
        console.clear()

    @staticmethod
    def print(text: str, style: str = ""):
        """Print with style"""
        console.print(text, style=style)

    @staticmethod
    def success(message: str):
        """Print success message"""
        console.print(f"✓ {message}", style=f"bold {config.COLOR_SUCCESS}")

    @staticmethod
    def error(message: str):
        """Print error message"""
        console.print(f"✗ {message}", style=f"bold {config.COLOR_ERROR}")

    @staticmethod
    def warning(message: str):
        """Print warning message"""
        console.print(f"⚠ {message}", style=f"bold {config.COLOR_WARNING}")

    @staticmethod
    def info(message: str):
        """Print info message"""
        console.print(f"ℹ {message}", style=config.COLOR_INFO)

    @staticmethod
    def header(title: str, subtitle: str = ""):
        """Print header"""
        text = Text()
        text.append(f"\n{config.ICONS['note']} {title}\n", style=f"bold {config.COLOR_PRIMARY}")
        if subtitle:
            text.append(f"{subtitle}\n", style=config.COLOR_INFO)

        console.print(Panel(
            Align.center(text),
            border_style=config.COLOR_PRIMARY,
            box=box.DOUBLE
        ))

    @staticmethod
    def section(title: str):
        """Print section title"""
        console.print(f"\n[bold {config.COLOR_ACCENT}]═══ {title} ═══[/]\n")

    @staticmethod
    def table(title: str, columns: List[str], rows: List[List],
             show_header: bool = True) -> Table:
        """Create and display table"""
        table = Table(
            title=title,
            show_header=show_header,
            header_style=f"bold {config.COLOR_PRIMARY}",
            border_style=config.COLOR_PRIMARY,
            box=box.ROUNDED
        )

        # Add columns
        for col in columns:
            table.add_column(col)

        # Add rows
        for row in rows:
            table.add_row(*[str(cell) for cell in row])

        console.print(table)
        return table

    @staticmethod
    def menu(title: str, options: List[str], show_exit: bool = True) -> str:
        """Display menu and get choice"""
        UI.section(title)

        for i, option in enumerate(options, 1):
            console.print(f"  [{config.COLOR_PRIMARY}]{i}[/]. {option}")

        if show_exit:
            console.print(f"  [{config.COLOR_ERROR}]0[/]. Kembali")

        console.print()

        return Prompt.ask(
            "Pilih menu",
            choices=[str(i) for i in range(len(options) + (1 if show_exit else 0))],
            default="0"
        )

    @staticmethod
    def prompt(message: str, password: bool = False, default: str = "") -> str:
        """Get user input"""
        return Prompt.ask(
            f"[{config.COLOR_PRIMARY}]{message}[/]",
            password=password,
            default=default
        )

    @staticmethod
    def confirm(message: str, default: bool = False) -> bool:
        """Get yes/no confirmation"""
        return Confirm.ask(
            f"[{config.COLOR_WARNING}]{message}[/]",
            default=default
        )

    @staticmethod
    def note_card(note: Dict, show_content: bool = False):
        """Display note as card"""
        # Build title
        title_parts = []

        if note.get('is_locked'):
            title_parts.append(f"[{config.COLOR_ERROR}]{config.ICONS['lock']}[/]")

        if note.get('is_favorite'):
            title_parts.append(f"[{config.COLOR_WARNING}]{config.ICONS['star']}[/]")

        title_parts.append(f"[bold]{note.get('title', 'Untitled')}[/]")
        title = " ".join(title_parts)

        # Build content
        content_parts = []

        # Metadata
        meta = []
        if note.get('created_at'):
            meta.append(f"{config.ICONS['calendar']} {note['created_at'][:16]}")

        if note.get('tags'):
            tags_str = " ".join([f"[{config.COLOR_ACCENT}]#{tag}[/]" for tag in note['tags']])
            meta.append(f"{config.ICONS['tag']} {tags_str}")

        content_parts.append(" | ".join(meta))

        # Content preview
        if show_content and note.get('content'):
            content_parts.append("\n")
            preview = note['content'][:200] + "..." if len(note['content']) > 200 else note['content']
            content_parts.append(f"[dim]{preview}[/]")

        # Display
        console.print(Panel(
            "\n".join(content_parts),
            title=title,
            border_style=config.COLOR_SUCCESS if note.get('is_favorite') else config.COLOR_PRIMARY,
            box=box.ROUNDED
        ))

    @staticmethod
    def notes_table(notes: List[Dict]):
        """Display notes as table"""
        if not notes:
            UI.info("Tidak ada catatan")
            return

        table = Table(
            show_header=True,
            header_style=f"bold {config.COLOR_PRIMARY}",
            border_style=config.COLOR_PRIMARY,
            box=box.ROUNDED
        )

        table.add_column("ID", style="dim", width=4)
        table.add_column("Status", width=8)
        table.add_column("Title", style="bold")
        table.add_column("Tags", width=20)
        table.add_column("Updated", width=16)

        for note in notes:
            # Status icons
            status = []
            if note.get('is_locked'):
                status.append(f"[{config.COLOR_ERROR}]{config.ICONS['lock']}[/]")
            if note.get('is_favorite'):
                status.append(f"[{config.COLOR_WARNING}]{config.ICONS['star']}[/]")
            status_str = " ".join(status) if status else "-"

            # Tags
            tags = note.get('tags', [])
            if isinstance(tags, list):
                tags_str = " ".join([f"[{config.COLOR_ACCENT}]#{t}[/]" for t in tags[:3]])
                if len(tags) > 3:
                    tags_str += f" [dim]+{len(tags)-3}[/]"
            else:
                tags_str = "-"

            # Date
            updated = note.get('updated_at', '')[:16] if note.get('updated_at') else '-'

            table.add_row(
                str(note['id']),
                status_str,
                note.get('title', 'Untitled')[:40],
                tags_str,
                updated
            )

        console.print(table)

    @staticmethod
    def stats_panel(stats: Dict):
        """Display statistics"""
        content = []

        if 'user' in stats:
            user = stats['user']
            content.append(f"[bold]User:[/] {user.get('username')}")
            content.append(f"[dim]Member since: {user.get('created_at', '')[:10]}[/]")
            content.append("")

        content.append(f"{config.ICONS['note']} Total Notes: [bold]{stats.get('total_notes', 0)}[/]")
        content.append(f"{config.ICONS['star']} Favorites: [bold]{stats.get('favorite_notes', 0)}[/]")
        content.append(f"{config.ICONS['lock']} Locked: [bold]{stats.get('locked', 0)}[/]")
        content.append(f"{config.ICONS['tag']} Tags: [bold]{stats.get('total_tags', 0)}[/]")

        if stats.get('archived_notes'):
            content.append(f"📦 Archived: [bold]{stats.get('archived_notes', 0)}[/]")

        console.print(Panel(
            "\n".join(content),
            title=f"{config.ICONS['user']} Statistics",
            border_style=config.COLOR_INFO,
            box=box.ROUNDED
        ))

    @staticmethod
    def markdown(text: str):
        """Render markdown"""
        md = Markdown(text)
        console.print(md)

    @staticmethod
    def code(code: str, language: str = "python"):
        """Display code with syntax highlighting"""
        syntax = Syntax(code, language, theme=config.TERMINAL_THEME)
        console.print(syntax)

    @staticmethod
    def progress(description: str):
        """Create progress spinner"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        )

    @staticmethod
    def loading(message: str):
        """Show loading message"""
        return UI.progress(message)

    @staticmethod
    def separator():
        """Print separator line"""
        console.print(f"[dim]{'─' * console.width}[/]")

    @staticmethod
    def welcome():
        """Display welcome screen"""
        UI.clear()

        welcome_text = f"""
[bold {config.COLOR_PRIMARY}]
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     {config.ICONS['note']}  ASISTEN SHADOW v{config.VERSION}                                                      ║
║                                                           ║
║     Aplikasi Catatan Terenkripsi                          ║
║     Multi-platform • Secure • User-friendly               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
[/]

[{config.COLOR_INFO}]🔒 AES-256 Encryption • 🔍 Full-Text Search • ⚡ Lightning Fast[/]
"""
        console.print(welcome_text)

    @staticmethod
    def goodbye():
        """Display goodbye message"""
        console.print(f"\n[bold {config.COLOR_PRIMARY}]Terima kasih telah menggunakan Asisten Shadow![/]")
        console.print(f"[{config.COLOR_INFO}]Stay secure! {config.ICONS['lock']}[/]\n")


# Convenience shortcuts
clear = UI.clear
print = UI.print
success = UI.success
error = UI.error
warning = UI.warning
info = UI.info
header = UI.header
menu = UI.menu
prompt = UI.prompt
confirm = UI.confirm
