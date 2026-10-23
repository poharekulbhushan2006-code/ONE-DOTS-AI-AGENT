"""
ONE: Always-On Autonomous AI Agent System
CLI Management Tool & Runtime Controller
"""

import argparse
import asyncio
import sys

# Configure UTF-8 encoding for Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config.settings import settings
from core.models import OneAgent, AgentStatus
from memory.state_store import state_store
from core.orchestrator import AgentOrchestrator
from tools.registry import ToolRegistry

console = Console(highlight=False)


def print_banner():
    console.print(Panel.fit(
        "[bold cyan]>> ONE[/bold cyan] : [bold white]Always-On Autonomous AI Agent System[/bold white]\n"
        "[italic dim]Give an AI a responsibility -- not just a prompt. Research | Analyze | Build | Monitor | Report | Adapt[/italic dim]",
        border_style="cyan"
    ))


def cmd_list():
    agents = state_store.list_agents()
    if not agents:
        console.print("[yellow]No ONE agents currently deployed.[/yellow]")
        console.print("Deploy one using: [bold]python cli.py deploy --name <Name> --mission <Mission>[/bold]")
        return

    table = Table(title="Autonomous Fleet", border_style="dim")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold white")
    table.add_column("Status", style="magenta")
    table.add_column("Stage", style="blue")
    table.add_column("Ticks", style="green")
    table.add_column("Cadence", style="dim")
    table.add_column("Responsibility", style="white")

    for a in agents:
        table.add_row(
            a.id,
            a.name,
            a.status.value.upper(),
            a.current_stage.value,
            str(a.total_ticks),
            f"{a.schedule_interval_seconds}s",
            a.responsibility[:50] + ("..." if len(a.responsibility) > 50 else ""),
        )
    console.print(table)


def cmd_deploy(name: str, mission: str, interval: int):
    agent = OneAgent(
        name=name,
        responsibility=mission,
        schedule_interval_seconds=interval,
        status=AgentStatus.IDLE,
    )
    saved = state_store.save_agent(agent)
    console.print(f"[bold green][OK] Successfully deployed ONE unit:[/bold green] [bold cyan]{saved.name}[/bold cyan] (`{saved.id}`)")
    console.print(f"[dim]Responsibility: {saved.responsibility}[/dim]")
    console.print(f"[dim]Cadence: Every {saved.schedule_interval_seconds}s[/dim]")


def cmd_tick(agent_id: str):
    agent = state_store.get_agent(agent_id)
    if not agent:
        console.print(f"[bold red]Error: Agent '{agent_id}' not found.[/bold red]")
        sys.exit(1)

    console.print(f"[bold cyan]Triggering autonomous tick for {agent.name} (`{agent.id}`)...[/bold cyan]")
    orchestrator = AgentOrchestrator(agent_id)
    result = asyncio.run(orchestrator.execute_tick())

    console.print(Panel(
        f"[bold green]Tick Finished[/bold green]\n"
        f"Status: {result.get('status')}\n"
        f"Stages: {' -> '.join(result.get('stages_executed', []))}\n"
        f"Next Scheduled Run: {result.get('next_tick_at', 'None')}",
        title="Cycle Result",
        border_style="green"
    ))


def cmd_server(host: str, port: int):
    import uvicorn
    console.print(f"[bold green]Starting ONE Agent Control Plane & Web Dashboard...[/bold green]")
    console.print(f"Web Dashboard: [bold cyan]http://{host}:{port}[/bold cyan]")
    uvicorn.run("api.app:app", host=host, port=port, reload=False)


def cmd_test():
    console.print("[bold yellow]Running ONE Subsystem Self-Test...[/bold yellow]")
    
    # 1. State Store
    console.print("1. Testing SQLite State Store... ", end="")
    test_agent = OneAgent(name="TestUnit", responsibility="Test autonomous operations")
    state_store.save_agent(test_agent)
    fetched = state_store.get_agent(test_agent.id)
    assert fetched is not None and fetched.name == "TestUnit"
    console.print("[bold green]PASS[/bold green]")

    # 2. Sandbox Computer
    console.print("2. Testing Sandbox Python & Shell Environment... ", end="")
    tools = ToolRegistry(test_agent.id)
    py_res = tools.sandbox_run_python("print('Sandbox Python is online!')")
    assert py_res.get("success") is True and "online" in py_res.get("stdout", "")
    console.print("[bold green]PASS[/bold green]")

    # 3. Episodic Semantic Memory
    console.print("3. Testing Episodic Memory Storage & Recall... ", end="")
    tools.memory_remember("Key insight: Competitor launched autonomous browser agent", category="finding")
    recall = tools.memory_recall("autonomous browser")
    assert recall.get("success") is True and len(recall.get("memories", [])) > 0
    console.print("[bold green]PASS[/bold green]")

    # 4. Autonomous Browser
    console.print("4. Testing Autonomous Playwright Browser... ", end="")
    nav_res = asyncio.run(tools.browser_inspect("https://example.com", take_screenshot=True))
    assert nav_res.get("success") is True and "Example" in nav_res.get("title", "")
    console.print(f"[bold green]PASS[/bold green] (Title: '{nav_res.get('title')}', Screenshot: {nav_res.get('screenshot_filename')})")

    # 5. Full Autonomous Lifecycle
    console.print("5. Testing Full 6-Stage Autonomous Loop... ", end="")
    orch = AgentOrchestrator(test_agent.id)
    loop_res = asyncio.run(orch.execute_tick())
    assert loop_res.get("status") in ["sleeping", "waiting_approval"]
    console.print(f"[bold green]PASS[/bold green] (Stages: {' -> '.join(loop_res.get('stages_executed', []))})")

    console.print("\n[bold green][SUCCESS] All 5 ONE Core Subsystems Verified and Functional![/bold green]")


def main():
    print_banner()
    parser = argparse.ArgumentParser(description="ONE: Always-On Autonomous AI Agent System")
    subparsers = parser.add_subparsers(dest="command")

    # list
    subparsers.add_parser("list", help="List all deployed ONE agents")

    # deploy
    deploy_p = subparsers.add_parser("deploy", help="Deploy a new ONE agent with a mission")
    deploy_p.add_argument("--name", required=True, help="Agent name")
    deploy_p.add_argument("--mission", required=True, help="Enduring responsibility / mission")
    deploy_p.add_argument("--interval", type=int, default=180, help="Cadence interval in seconds")

    # tick
    tick_p = subparsers.add_parser("tick", help="Trigger an autonomous tick on an agent")
    tick_p.add_argument("--id", required=True, help="Agent ID")

    # server
    server_p = subparsers.add_parser("server", help="Launch the API server and Web Dashboard")
    server_p.add_argument("--host", default="127.0.0.1", help="Host address")
    server_p.add_argument("--port", type=int, default=8000, help="Port")

    # test
    subparsers.add_parser("test", help="Run comprehensive subsystem diagnostic tests")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list()
    elif args.command == "deploy":
        cmd_deploy(args.name, args.mission, args.interval)
    elif args.command == "tick":
        cmd_tick(args.id)
    elif args.command == "server":
        cmd_server(args.host, args.port)
    elif args.command == "test":
        cmd_test()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
