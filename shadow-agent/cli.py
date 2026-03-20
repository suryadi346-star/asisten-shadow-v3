"""
Shadow Agent — CLI (Rich Terminal UI)
Bisa dipakai standalone di Termux tanpa Web UI.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich import print as rprint

from config import config
from core.database import init_db, list_sessions, get_session, list_tasks, get_stats
from core.orchestrator import Orchestrator
from core.provider import check_providers
from agents.agents import AGENT_REGISTRY

console = Console()


# ─── Header ───────────────────────────────────────────────────────────────────

def print_header():
    console.print(Panel.fit(
        f"[bold cyan]◆ Shadow Agent[/bold cyan] [dim]v{config.version}[/dim]\n"
        f"[dim]Lightweight AI Agent Orchestrator[/dim]",
        border_style="cyan"
    ))


# ─── Provider Status ──────────────────────────────────────────────────────────

def cmd_status():
    console.print("\n[bold]Checking providers...[/bold]")
    status = check_providers()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Provider")
    table.add_column("Status")
    table.add_column("Model")
    table.add_column("Info")

    for provider, info in status.items():
        ok = info.get("ok", False)
        table.add_row(
            provider.upper(),
            "[green]✓ OK[/green]" if ok else "[red]✗ FAIL[/red]",
            info.get("model", "-"),
            info.get("error", "") or "[dim]Connected[/dim]"
        )
    console.print(table)

    # Agent → Provider mapping
    console.print("\n[bold]Agent → Provider mapping:[/bold]")
    for agent, prov in config.agent_provider_map.items():
        console.print(f"  [cyan]{agent:12}[/cyan] → [yellow]{prov}[/yellow]")


# ─── Run Goal (Full Pipeline) ─────────────────────────────────────────────────

def cmd_run(goal: str = None, provider: str = None):
    if not goal:
        goal = Prompt.ask("\n[bold cyan]Goal[/bold cyan]")

    if not goal.strip():
        console.print("[red]Goal tidak boleh kosong.[/red]")
        return

    steps_done = []

    def on_progress(info):
        phase = info.get("phase", "")
        if phase == "init":
            console.print(f"\n[dim]Session: {info['session_id'][:8]}...[/dim]")
        elif phase == "planning":
            console.print(f"[yellow]⟳ Planner:[/yellow] {info.get('message', '')}")
        elif phase == "executing":
            agent = info.get("agent", "")
            task = info.get("task", "")[:60]
            console.print(f"[cyan]▶ Step {info['step']}[/cyan] [{agent}] {task}...")
        elif phase == "step_done":
            preview = info.get("preview", "")[:80]
            console.print(f"[green]✓ Step {info['step']} done[/green] — {preview}")
            steps_done.append(info)
        elif phase == "step_failed":
            console.print(f"[red]✗ Step {info['step']} failed:[/red] {info.get('error', '')}")
        elif phase == "complete":
            console.print(
                f"\n[bold green]Pipeline complete![/bold green] "
                f"{info['steps_done']}/{info['steps_total']} steps • "
                f"{info['total_tokens']} tokens used"
            )

    orc = Orchestrator(on_progress=on_progress)

    with console.status("[bold cyan]Running pipeline...[/bold cyan]", spinner="dots"):
        result = orc.run(goal=goal, provider_override=provider)

    # Print results
    if result.get("results"):
        console.print(f"\n[bold]═══ Results ({'session: ' + result['session_id'][:8]}) ═══[/bold]")
        for r in result["results"]:
            if r.get("success") and r.get("result"):
                console.print(Panel(
                    Markdown(r["result"]),
                    title=f"[cyan]Step {r['step']} — {r['agent'].upper()}[/cyan]",
                    border_style="dim"
                ))


# ─── Run Single Agent ─────────────────────────────────────────────────────────

def cmd_agent(agent_type: str = None, prompt: str = None, provider: str = None):
    if not agent_type:
        console.print("\n[bold]Available agents:[/bold]")
        for k, cls in AGENT_REGISTRY.items():
            console.print(f"  [cyan]{k}[/cyan]")
        agent_type = Prompt.ask("Agent type")

    if agent_type not in AGENT_REGISTRY:
        console.print(f"[red]Unknown agent: {agent_type}[/red]")
        return

    if not prompt:
        prompt = Prompt.ask(f"\n[bold cyan]{agent_type.capitalize()} prompt[/bold cyan]")

    orc = Orchestrator()
    with console.status(f"[cyan]{agent_type}[/cyan] running...", spinner="dots"):
        result = orc.run_single(
            agent_type=agent_type,
            prompt=prompt,
            provider=provider,
        )

    if result.get("success"):
        console.print(Panel(
            Markdown(result["result"]),
            title=f"[green]{agent_type.upper()} Result[/green] [{result['provider']} / {result['model']}]",
            border_style="green"
        ))
        console.print(f"[dim]Tokens: {result['tokens']['in']} in, {result['tokens']['out']} out[/dim]")
    else:
        console.print(f"[red]Failed:[/red] {result.get('error', 'Unknown error')}")


# ─── List Sessions ────────────────────────────────────────────────────────────

def cmd_sessions():
    sessions = list_sessions()
    if not sessions:
        console.print("[dim]No sessions yet.[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", width=10)
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Created")

    for s in sessions:
        sid = s["id"][:8] + "..."
        status_color = {"active": "yellow", "done": "green", "failed": "red"}.get(s["status"], "white")
        table.add_row(
            sid,
            s["name"][:40],
            f"[{status_color}]{s['status']}[/{status_color}]",
            s["created_at"][:16],
        )
    console.print(table)


# ─── Stats ────────────────────────────────────────────────────────────────────

def cmd_stats():
    stats = get_stats()
    if not stats:
        console.print("[dim]No stats yet.[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Date")
    table.add_column("Provider")
    table.add_column("Model")
    table.add_column("Calls")
    table.add_column("Tokens In")
    table.add_column("Tokens Out")
    table.add_column("Errors")

    for s in stats:
        table.add_row(
            s["date"],
            s["provider"].upper(),
            s["model"],
            str(s["calls"]),
            str(s["tokens_in"]),
            str(s["tokens_out"]),
            str(s["errors"]),
        )
    console.print(table)


# ─── Interactive Menu ─────────────────────────────────────────────────────────

def interactive_menu():
    print_header()
    while True:
        console.print("\n[bold]Commands:[/bold]")
        console.print("  [cyan]1[/cyan] Run full goal pipeline")
        console.print("  [cyan]2[/cyan] Run single agent")
        console.print("  [cyan]3[/cyan] List sessions")
        console.print("  [cyan]4[/cyan] Provider status")
        console.print("  [cyan]5[/cyan] Usage stats")
        console.print("  [cyan]q[/cyan] Quit")

        choice = Prompt.ask("\n[bold]→[/bold]", default="q")

        if choice == "1":
            cmd_run()
        elif choice == "2":
            cmd_agent()
        elif choice == "3":
            cmd_sessions()
        elif choice == "4":
            cmd_status()
        elif choice == "5":
            cmd_stats()
        elif choice in ("q", "quit", "exit"):
            console.print("[dim]Bye.[/dim]")
            break


# ─── CLI Entry ────────────────────────────────────────────────────────────────

def main():
    init_db()

    parser = argparse.ArgumentParser(description="Shadow Agent CLI")
    sub = parser.add_subparsers(dest="cmd")

    # run
    p_run = sub.add_parser("run", help="Run full goal pipeline")
    p_run.add_argument("goal", nargs="?", help="Goal to execute")
    p_run.add_argument("--provider", choices=["anthropic", "openai"], help="Force provider")

    # agent
    p_agent = sub.add_parser("agent", help="Run single agent")
    p_agent.add_argument("agent_type", nargs="?", choices=list(AGENT_REGISTRY))
    p_agent.add_argument("--prompt", help="Prompt for agent")
    p_agent.add_argument("--provider", choices=["anthropic", "openai"])

    # sessions
    sub.add_parser("sessions", help="List sessions")

    # status
    sub.add_parser("status", help="Check provider status")

    # stats
    sub.add_parser("stats", help="Usage statistics")

    # serve
    p_serve = sub.add_parser("serve", help="Start Web UI + API server")
    p_serve.add_argument("--port", type=int, default=config.port)
    p_serve.add_argument("--host", default=config.host)

    args = parser.parse_args()

    if args.cmd == "run":
        print_header()
        cmd_run(goal=args.goal, provider=getattr(args, "provider", None))
    elif args.cmd == "agent":
        print_header()
        cmd_agent(
            agent_type=args.agent_type,
            prompt=getattr(args, "prompt", None),
            provider=getattr(args, "provider", None),
        )
    elif args.cmd == "sessions":
        print_header()
        cmd_sessions()
    elif args.cmd == "status":
        print_header()
        cmd_status()
    elif args.cmd == "stats":
        print_header()
        cmd_stats()
    elif args.cmd == "serve":
        import uvicorn
        console.print(f"[bold cyan]Starting server on {args.host}:{args.port}[/bold cyan]")
        uvicorn.run(
            "api.server:app",
            host=args.host,
            port=args.port,
            reload=config.debug,
        )
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
