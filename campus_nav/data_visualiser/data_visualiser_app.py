from __future__ import annotations

import csv
import os
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Rule, Static

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _count_csv_rows(path: Path) -> int:
    """Count data rows in a CSV file (excluding header)."""
    if not path.exists():
        return 0
    with open(path, encoding="utf-8", newline="") as f:
        return max(sum(1 for _ in csv.reader(f)) - 1, 0)


class DataVisualiserApp(App):
    """
    Textual launcher app for the GUI-based campus map visualiser.
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Exit"),
        ("r", "relaunch", "Relaunch GUI"),
    ]
    CSS_PATH = "data_visualiser_app.tcss"

    def __init__(self, theme: str | None = None):
        super().__init__()
        self.theme = theme or "textual-dark"
        self._gui_process: subprocess.Popen[str] | None = None
        self._stderr_output: str = ""

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="visualiser_root"):
            yield Static(
                "[b]Data Visualiser Launcher[/b]",
                id="title-label",
            )
            yield Rule(line_style="heavy")
            with Horizontal(id="stats-row"):
                yield Static("", id="stat-nodes")
                yield Static("", id="stat-edges")
                yield Static("", id="stat-status")
            yield Rule()
            yield Static("Preparing GUI visualiser window...", id="status")
            yield Rule()
            yield Static(
                "[dim]Ctrl+Q[/dim] Exit  ·  [dim]R[/dim] Relaunch GUI",
                id="hint",
            )
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Campus Navigator"
        self.sub_title = "Data Visualiser"

        # Show dataset stats
        n_nodes = _count_csv_rows(DATA_DIR / "nodes.csv")
        n_edges = _count_csv_rows(DATA_DIR / "edges.csv")
        self.query_one("#stat-nodes", Static).update(f"[b]Nodes:[/b] {n_nodes}")
        self.query_one("#stat-edges", Static).update(f"[b]Edges:[/b] {n_edges}")

        self._launch_gui()

    def _launch_gui(self) -> None:
        available, reason = _is_gui_available()
        if not available:
            self.query_one("#stat-status", Static).update("[red]Unavailable[/red]")
            self.query_one("#status", Static).update(
                "[red bold]GUI is not available in this environment.[/red bold]\n"
                f"Reason: {reason}\n"
                "Run this app in a desktop session with display access."
            )
            return

        nodes_path = DATA_DIR / "nodes.csv"
        edges_path = DATA_DIR / "edges.csv"
        command = [
            sys.executable,
            "-m",
            "campus_nav.data_visualiser.gui_window",
            "--nodes",
            str(nodes_path),
            "--edges",
            str(edges_path),
        ]

        try:
            self._gui_process = subprocess.Popen(  # pylint: disable=consider-using-with
                command, text=True, stderr=subprocess.PIPE,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.query_one("#stat-status", Static).update("[red]Error[/red]")
            self.query_one("#status", Static).update(
                f"[red bold]Failed to launch GUI window.[/red bold]\nError: {exc}"
            )
            return

        self.query_one("#stat-status", Static).update("[green]Running[/green]")
        self.query_one("#status", Static).update(
            "Campus map GUI window launched.\n"
            "Interact with the map in the opened window.\n"
            "This launcher will exit automatically when the GUI window closes."
        )
        self.set_interval(0.5, self._check_gui_process)

    def action_quit(self) -> None:
        if self._gui_process is not None and self._gui_process.poll() is None:
            self._gui_process.terminate()
        self.exit()

    def action_relaunch(self) -> None:
        if self._gui_process is not None and self._gui_process.poll() is None:
            return  # Already running
        self._stderr_output = ""
        self._launch_gui()

    def on_unmount(self) -> None:
        if self._gui_process is None:
            return
        if self._gui_process.poll() is None:
            self._gui_process.terminate()

    def _check_gui_process(self) -> None:
        if self._gui_process is None:
            return

        return_code = self._gui_process.poll()
        if return_code is None:
            return

        # Collect any stderr output
        if self._gui_process.stderr:
            try:
                chunk = self._gui_process.stderr.read()
                if chunk:
                    self._stderr_output += chunk
            except (ValueError, OSError):
                pass

        if return_code == 0:
            self.exit()
            return

        self.query_one("#stat-status", Static).update("[red]Exited[/red]")
        error_detail = self._stderr_output.strip()
        msg = (
            f"[red bold]GUI window exited with an error.[/red bold]\n"
            f"Exit code: {return_code}\n"
            "Check dependencies (PySide6 + QtWebEngine) and display availability.\n"
            "Press [b]R[/b] to relaunch."
        )
        if error_detail:
            msg += f"\n\n[dim]Stderr:[/dim]\n{error_detail[-800:]}"
        self.query_one("#status", Static).update(msg)
        self._gui_process = None


def _is_gui_available() -> tuple[bool, str]:
    if find_spec("PySide6") is None or find_spec("PySide6.QtWebEngineWidgets") is None:
        return False, "Missing GUI dependencies: PySide6 + QtWebEngine"

    assets_dir = Path(__file__).resolve().parent / "web_assets"
    bundle_file = assets_dir / "sigma-bundle.min.js"
    template_file = assets_dir / "visualiser_template.html"
    if not bundle_file.exists() or not template_file.exists():
        return False, f"Missing offline Sigma assets in {assets_dir}"

    if sys.platform.startswith("linux"):
        if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            return True, ""
        return False, "No DISPLAY/WAYLAND_DISPLAY found"

    if sys.platform == "darwin":
        if os.environ.get("SSH_CONNECTION") and not os.environ.get("DISPLAY"):
            return False, "Detected SSH session without display forwarding"
        return True, ""

    return True, ""
