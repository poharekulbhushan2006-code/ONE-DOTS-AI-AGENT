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


ARCHETYPES = {
    "nova": {
        "name": "Blue Dot (NOVA)",
        "mission": "Product Launch Lead (Blue Face): learn audience and positioning, revise launch story as scope changes, and prepare email and social drafts.",
        "interval": 180,
        "color": "blue",
    },
    "sage": {
        "name": "Lime-Green Dot (SAGE)",
        "mission": "Research Scientist (Lime-Green Face with Round Glasses): learn research goals, evaluate incoming evidence, rerun data analyses, and flag unexpected results.",
        "interval": 180,
        "color": "green",
    },
    "axis": {
        "name": "Golden-Yellow Dot (AXIS)",
        "mission": "Enterprise Sales Lead (Golden-Yellow Face): review customer requirements against docs, test integrations, generate sandbox proof-of-concepts, and update proposals.",
        "interval: 300,
        "color": "yellow",
    },
    "muse": {
        "name": "Purple Dot (MUSE)",
        "mission": "Content Creator & Media Lead (Purple Face with Celestial Ring): learn creator voice, extract clip moments from interview transcripts, generate show notes, and draft social posts.",
        "interval": 180,
        "color": "purple",
    },
    "hex": {
        "name": "Dark Navy Dot (HEX)",
        "mission": "Software Developer (Dark Navy Face with Glowing Cyan Features): monitor customer feedback for bug reports, scope fixes, execute test suites in sandbox cloud computer, and prepare verified PRs.",
        "interval": 120,
        "color": "cyan",
    },
    "silver": {
        "name": "Red Dot (SILVER)",
        "mission": "Ineffable Discovery Scientist (Crimson/Red Face): autonomous trial-and-error pure RL discovery of algorithmic heuristics, optimizations, and mathematical invariants verified in isolated sandboxes.",
        "interval": 180,
        "color": "silver",
    },
}
# Backward compatibility aliases
ARCHETYPES["felipe"] = ARCHETYPES["nova"]
ARCHETYPES["todd"] = ARCHETYPES["sage"]
ARCHETYPES["alfred"] = ARCHETYPES["axis"]
ARCHETYPES["jojo"] = ARCHETYPES["muse"]
ARCHETYPES["dev"] = ARCHETYPES["hex"]
ARCHETYPES["sentry"] = ARCHETYPES["hex"]
ARCHETYPES["aura"] = ARCHETYPES["silver"]
ARCHETYPES["discovery"] = ARCHETYPES["silver"]


def cmd_deploy(name: str = None, mission: str = None, interval: int = 180, template: str = None):
    context = {}
    if template and template.lower() in ARCHETYPES:
        arch = ARCHETYPES[template.lower()]
        name = name or arch["name"]
        mission = mission or arch["mission"]
        interval = interval if interval != 180 else arch["interval"]
        context = {"color": arch["color"], "archetype": template.lower()}
    
    if not name or not mission:
        console.print("[bold red]Error: Name and mission are required (or specify --template).[/bold red]")
        sys.exit(1)

    agent = OneAgent(
        name=name,
        responsibility=mission,
        schedule_interval_seconds=interval,
        context=context,
        status=AgentStatus.IDLE,
    )
    saved = state_store.save_agent(agent)
    color_style = context.get("color", "cyan")
    console.print(f"[bold green][OK] Successfully deployed Dot unit:[/bold green] [bold {color_style}]{saved.name}[/bold {color_style}] (`{saved.id}`)")
    console.print(f"[dim]Responsibility: {saved.responsibility}[/dim]")
    console.print(f"[dim]Cadence: Every {saved.schedule_interval_seconds}s | Model: Google Gemini 3.5[/dim]")


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


def cmd_delete(agent_id: str):
    agent = state_store.get_agent(agent_id)
    if not agent:
        console.print(f"[red]Agent '{agent_id}' does not exist.[/red]")
        return
    state_store.delete_agent(agent_id)
    from memory.semantic_memory import semantic_memory
    semantic_memory.clear_agent(agent_id)
    console.print(f"[bold green]Agent '{agent.name}' ({agent.id}) successfully retired and deleted.[/bold green]")


def cmd_server(host: str, port: int):
    import uvicorn
    console.print(f"[bold green]Starting ONE Agent Control Plane & Web Dashboard...[/bold green]")
    console.print(f"Web Dashboard: [bold cyan]http://{host}:{port}[/bold cyan]")
    uvicorn.run("api.app:app", host=host, port=port, reload=True)


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
    deploy_p = subparsers.add_parser("deploy", help="Deploy an always-on Dot with a mission or archetype")
    deploy_p.add_argument("--template", choices=["nova", "sage", "axis", "muse", "hex", "felipe", "todd", "alfred", "jojo", "dev"], help="Specialist Dot template: nova (blue face launch lead), sage (lime-green glasses science), axis (golden sales), muse (purple media), hex (dark navy dev)")
    deploy_p.add_argument("--name", help="Custom Dot name")
    deploy_p.add_argument("--mission", help="Custom enduring responsibility / mission")
    deploy_p.add_argument("--interval", type=int, default=180, help="Cadence interval in seconds")

    # tick
    tick_p = subparsers.add_parser("tick", help="Trigger an autonomous tick on an agent")
    tick_p.add_argument("--id", required=True, help="Agent ID")

    # delete
    delete_p = subparsers.add_parser("delete", help="Retire and delete an agent")
    delete_p.add_argument("--id", required=True, help="Agent ID")

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
        cmd_deploy(name=args.name, mission=args.mission, interval=args.interval, template=args.template)
    elif args.command == "tick":
        cmd_tick(args.id)
    elif args.command == "delete":
        cmd_delete(args.id)
    elif args.command == "server":
        cmd_server(args.host, args.port)
    elif args.command == "test":
        cmd_test()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
