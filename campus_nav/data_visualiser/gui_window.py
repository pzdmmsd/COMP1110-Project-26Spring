from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow

from campus_nav.models import CampusMap
from campus_nav.utils import construct_map_from_csv

ASSETS_DIR = Path(__file__).resolve().parent / "web_assets"
HTML_TEMPLATE_PATH = ASSETS_DIR / "visualiser_template.html"
SIGMA_BUNDLE_PATH = ASSETS_DIR / "sigma-bundle.min.js"

EDGE_TYPE_COLORS: dict[str, str] = {
    "FLAT": "#4c7ef3",
    "STAIRS": "#e8590c",
    "MINOR_STAIRS": "#f08c00",
    "ESCALATOR": "#12b886",
    "LIFT": "#7048e8",
}


def _build_graph_payload(campus_map: CampusMap) -> dict[str, list[dict[str, object]]]:
    nodes = sorted(campus_map.get_nodes(), key=lambda item: item.node_id)

    node_payload: list[dict[str, object]] = []
    for index, node in enumerate(nodes):
        # Golden-angle spiral yields a deterministic scattered layout.
        angle = index * 2.399963229728653
        radius = 1.8 * math.sqrt(index + 1)
        node_payload.append(
            {
                "id": node.node_id,
                "label": node.node_id,
                "x": radius * math.cos(angle),
                "y": radius * math.sin(angle),
                "size": 8,
                "color": "#2a6fdb",
                "description": node.description,
            }
        )

    model_edges = campus_map.get_edges()
    edge_payload: list[dict[str, object]] = []
    for index, edge in enumerate(model_edges):
        edge_type = str(edge.edge_type)
        edge_payload.append(
            {
                "id": f"e{index}",
                "source": edge.node1.node_id,
                "target": edge.node2.node_id,
                "label": f"{edge_type} ({edge.time_cost}s)",
                "size": 1.8,
                "color": EDGE_TYPE_COLORS.get(edge_type, "#8a98b0"),
                "edge_type": edge_type,
                "time_cost": edge.time_cost,
            }
        )

    return {"nodes": node_payload, "edges": edge_payload}


def _build_html(graph_payload: dict[str, list[dict[str, object]]]) -> str:
    config = {"edge_type_colors": EDGE_TYPE_COLORS}
    payload_json = json.dumps(graph_payload, ensure_ascii=True).replace("</", "<\\/")
    config_json = json.dumps(config, ensure_ascii=True).replace("</", "<\\/")
    template = HTML_TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.replace("__GRAPH_PAYLOAD_JSON__", payload_json).replace(
        "__CONFIG_JSON__", config_json
    )


def run_gui(nodes_path: str | None = None, edges_path: str | None = None) -> int:
    if not SIGMA_BUNDLE_PATH.exists() or not HTML_TEMPLATE_PATH.exists():
        raise FileNotFoundError(
            f"Missing offline assets in {ASSETS_DIR}. "
            "Expected sigma-bundle.min.js and visualiser_template.html"
        )

    if nodes_path is None or edges_path is None:
        campus_map = construct_map_from_csv()
    else:
        campus_map = construct_map_from_csv(nodes_file=nodes_path, edges_file=edges_path)

    graph_payload = _build_graph_payload(campus_map)
    html_content = _build_html(graph_payload)

    app = QApplication(sys.argv)
    n_nodes = len(graph_payload["nodes"])
    n_edges = len(graph_payload["edges"])
    window = QMainWindow()
    window.setWindowTitle(f"Campus Navigator — {n_nodes} nodes, {n_edges} edges")
    window.resize(1200, 800)

    view = QWebEngineView()
    base_url = QUrl.fromLocalFile(f"{ASSETS_DIR.resolve().as_posix()}/")
    view.setHtml(html_content, baseUrl=base_url)
    window.setCentralWidget(view)

    window.show()
    return app.exec()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the campus map visualiser GUI.")
    parser.add_argument("--nodes", default=None, help="Path to nodes CSV")
    parser.add_argument("--edges", default=None, help="Path to edges CSV")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    return run_gui(nodes_path=args.nodes, edges_path=args.edges)


if __name__ == "__main__":
    raise SystemExit(main())
