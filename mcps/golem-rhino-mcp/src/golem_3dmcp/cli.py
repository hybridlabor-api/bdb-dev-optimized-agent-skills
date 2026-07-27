"""
golem_3dmcp/cli.py
==================
CLI entry points for GOLEM-3DMCP.

Commands:
    golem start           — Start the MCP server (stdio mode)
    golem install-rhino   — Deploy the Rhino plugin
    golem uninstall-rhino — Remove the Rhino plugin
    golem doctor          — Diagnose environment and connection
    golem config          — Print agent JSON snippets
    golem version         — Print version info
"""

from __future__ import annotations

import platform
import shutil
import socket
import sys
from pathlib import Path

import click

# ---------------------------------------------------------------------------
# Rhino scripts directory detection
# ---------------------------------------------------------------------------

def _rhino_scripts_dir() -> Path | None:
    """Return the platform-specific Rhino 8 scripts directory, or None."""
    system = platform.system()
    if system == "Darwin":
        p = (
            Path.home() / "Library" / "Application Support"
            / "McNeel" / "Rhinoceros" / "8.0" / "scripts"
        )
        return p if p.parent.exists() else None
    elif system == "Windows":
        p = Path.home() / "AppData" / "Roaming" / "McNeel" / "Rhinoceros" / "8.0" / "scripts"
        return p if p.parent.exists() else None
    elif system == "Linux":
        p = Path.home() / ".config" / "McNeel" / "Rhinoceros" / "8.0" / "scripts"
        return p if p.parent.exists() else None
    return None


def _plugin_source_dir() -> Path:
    """Return the path to the bundled _rhino_plugin directory."""
    return Path(__file__).parent / "_rhino_plugin"


# ---------------------------------------------------------------------------
# CLI Group
# ---------------------------------------------------------------------------

@click.group()
def main() -> None:
    """GOLEM-3DMCP — MCP server for Rhinoceros 3D."""
    pass


# ---------------------------------------------------------------------------
# golem start
# ---------------------------------------------------------------------------

@main.command()
def start() -> None:
    """Start the GOLEM MCP server (stdio mode)."""
    from golem_3dmcp.server import main as server_main
    server_main()


# ---------------------------------------------------------------------------
# golem install-rhino
# ---------------------------------------------------------------------------

@main.command("install-rhino")
def install_rhino() -> None:
    """Deploy the Rhino plugin to the platform-specific scripts directory."""
    try:
        from rich.console import Console
        console = Console()
    except ImportError:
        console = None

    def _print(msg: str, style: str = "") -> None:
        if console:
            console.print(msg, style=style)
        else:
            click.echo(msg)

    source = _plugin_source_dir()
    if not source.exists():
        _print(
            "[red]Error:[/red] Bundled plugin not found. Reinstall golem-3dmcp.",
            style="bold red",
        )
        raise SystemExit(1)

    target = _rhino_scripts_dir()
    if target is None:
        _print("[yellow]Warning:[/yellow] Could not auto-detect Rhino 8 scripts directory.")
        _print("Please specify the path manually:")
        target_str = click.prompt("Rhino scripts directory path")
        target = Path(target_str)

    target.mkdir(parents=True, exist_ok=True)
    dest = target / "golem_3dmcp_plugin"

    if dest.exists():
        shutil.rmtree(dest)

    shutil.copytree(source, dest)

    # Copy startup.py to scripts root for easy auto-start registration
    startup_src = dest / "startup.py"
    startup_dst = target / "golem_startup.py"
    if startup_src.exists():
        shutil.copy2(startup_src, startup_dst)

    _print(f"\n[green]✓[/green] Plugin installed to: {dest}")
    _print(f"[green]✓[/green] Startup script: {startup_dst}")
    _print("\n[bold]Next steps:[/bold]")
    _print("  1. Open Rhino 8")
    _print("  2. Run golem_startup.py from the Script Editor, or")
    _print("  3. Add it to auto-start: Tools > Options > RhinoScript > Startup Scripts")


# ---------------------------------------------------------------------------
# golem uninstall-rhino
# ---------------------------------------------------------------------------

@main.command("uninstall-rhino")
def uninstall_rhino() -> None:
    """Remove the Rhino plugin from the scripts directory."""
    target = _rhino_scripts_dir()
    if target is None:
        click.echo("Could not auto-detect Rhino scripts directory.")
        return

    removed = False
    dest = target / "golem_3dmcp_plugin"
    if dest.exists():
        shutil.rmtree(dest)
        click.echo(f"Removed: {dest}")
        removed = True

    startup = target / "golem_startup.py"
    if startup.exists():
        startup.unlink()
        click.echo(f"Removed: {startup}")
        removed = True

    if removed:
        click.echo("Plugin uninstalled successfully.")
    else:
        click.echo("No GOLEM plugin found to remove.")


# ---------------------------------------------------------------------------
# golem doctor
# ---------------------------------------------------------------------------

@main.command()
def doctor() -> None:
    """Diagnose the GOLEM-3DMCP environment and connection."""
    try:
        from rich.console import Console
        from rich.table import Table  # noqa: F401
        console = Console()
        use_rich = True
    except ImportError:
        console = None
        use_rich = False

    from golem_3dmcp import __version__
    from golem_3dmcp.config import RHINO_GH_PORT, RHINO_HOST, RHINO_PORT

    checks = []

    # Python
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 10)
    checks.append(("Python", py_ver, py_ok))

    # Platform
    plat = f"{platform.system()} {platform.release()}"
    checks.append(("Platform", plat, True))

    # Package version
    checks.append(("Package", __version__, True))

    # Rhino detection
    rhino_dir = _rhino_scripts_dir()
    if rhino_dir and rhino_dir.parent.exists():
        checks.append(("Rhino 8", str(rhino_dir.parent), True))
    else:
        checks.append(("Rhino 8", "not detected", False))

    # Plugin installed
    if rhino_dir:
        plugin_dir = rhino_dir / "golem_3dmcp_plugin"
        if plugin_dir.exists():
            checks.append(("Plugin", "installed", True))
        else:
            checks.append(("Plugin", "not installed", False))
    else:
        checks.append(("Plugin", "unknown", False))

    # Port check
    def _check_port(host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except (TimeoutError, OSError):
            return False

    port_ok = _check_port(RHINO_HOST, RHINO_PORT)
    checks.append((f"Port {RHINO_PORT}", "listening" if port_ok else "closed", port_ok))

    # Grasshopper port
    gh_ok = _check_port(RHINO_HOST, RHINO_GH_PORT)
    checks.append((f"GH Port {RHINO_GH_PORT}", "listening" if gh_ok else "closed", gh_ok))

    # Connection test
    if port_ok:
        try:
            from golem_3dmcp.connection import RhinoConnection
            conn = RhinoConnection()
            conn.connect(host=RHINO_HOST, port=RHINO_PORT, timeout=5)
            conn.disconnect()
            checks.append(("Connection", "OK", True))
        except Exception as e:
            checks.append(("Connection", f"failed: {e}", False))
    else:
        checks.append(("Connection", "skipped (port closed)", False))

    # Output
    if use_rich:
        assert console is not None
        console.print("\n[bold]GOLEM-3DMCP Health Check[/bold]")
        console.print("━" * 45)
        for label, value, ok in checks:
            status = "[green]✓[/green]" if ok else "[red]✗[/red]"
            console.print(f"  {label:.<20s} {value:<20s} {status}")
        console.print("━" * 45)
        all_ok = all(ok for _, _, ok in checks)
        if all_ok:
            console.print("  [green bold]All checks passed![/green bold]")
        else:
            console.print("  [yellow]Some checks failed. See above.[/yellow]")
        console.print()
    else:
        click.echo("\nGOLEM-3DMCP Health Check")
        click.echo("=" * 45)
        for label, value, ok in checks:
            status = "OK" if ok else "FAIL"
            click.echo(f"  {label:.<20s} {value:<20s} [{status}]")
        click.echo("=" * 45)
        click.echo()


# ---------------------------------------------------------------------------
# golem config
# ---------------------------------------------------------------------------

@main.command()
def config() -> None:
    """Print MCP configuration JSON snippets for various agents."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.syntax import Syntax  # noqa: F401
        console = Console()
        use_rich = True
    except ImportError:
        console = None
        use_rich = False

    uvx_config = '''{
  "mcpServers": {
    "golem-3dmcp": {
      "command": "uvx",
      "args": ["--from", "golem-3dmcp", "golem", "start"]
    }
  }
}'''

    pip_config = '''{
  "mcpServers": {
    "golem-3dmcp": {
      "command": "golem",
      "args": ["start"]
    }
  }
}'''

    python_config = '''{
  "mcpServers": {
    "golem-3dmcp": {
      "command": "python",
      "args": ["-m", "golem_3dmcp"]
    }
  }
}'''

    if use_rich:
        assert console is not None
        console.print()
        console.print(Panel.fit(
            "[bold]GOLEM-3DMCP Configuration[/bold]\n\n"
            "Add one of these to your MCP agent configuration:\n\n"
            "[bold cyan]Option A — uvx (recommended, auto-installs):[/bold cyan]\n"
            f"[dim]{uvx_config}[/dim]\n\n"
            "[bold cyan]Option B — pip install (manual):[/bold cyan]\n"
            f"[dim]{pip_config}[/dim]\n\n"
            "[bold cyan]Option C — python -m (explicit):[/bold cyan]\n"
            f"[dim]{python_config}[/dim]\n\n"
            "Works with: Claude Code, Cursor, Windsurf, Cline, Continue,\n"
            "and any stdio MCP host.",
            title="GOLEM-3DMCP",
            border_style="green",
        ))
        console.print()
    else:
        click.echo("\nGOLEM-3DMCP Configuration")
        click.echo("=" * 50)
        click.echo("\nOption A — uvx (recommended):")
        click.echo(uvx_config)
        click.echo("\nOption B — pip install:")
        click.echo(pip_config)
        click.echo("\nOption C — python -m:")
        click.echo(python_config)
        click.echo()


# ---------------------------------------------------------------------------
# golem version
# ---------------------------------------------------------------------------

@main.command()
def version() -> None:
    """Print version and platform info."""
    from golem_3dmcp import __version__
    click.echo(f"golem-3dmcp {__version__}")
    click.echo(f"Python {sys.version}")
    click.echo(f"Platform: {platform.system()} {platform.release()} ({platform.machine()})")
