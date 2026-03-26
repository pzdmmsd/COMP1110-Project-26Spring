from __future__ import annotations

import csv
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path

from campus_nav.models import CampusMap, EdgeType, Node
from campus_nav.utils import EDGES_CSV_PATH, NODES_CSV_PATH


@dataclass(frozen=True)
class ImportIssue:
    entity: str
    row_number: int
    reason: str


@dataclass
class LoadResult:
    campus_map: CampusMap
    issues: list[ImportIssue]
    nodes_loaded: int
    edges_loaded: int
    node_rows: int
    edge_rows: int


@dataclass(frozen=True)
class IntegrityReport:
    node_count: int
    edge_count: int
    isolated_nodes: int
    connected_components: int


@dataclass(frozen=True)
class ChangePreview:
    nodes_added: int
    nodes_removed: int
    nodes_modified: int
    edges_added: int
    edges_removed: int


def resolve_paths(nodes_path: str | None = None, edges_path: str | None = None) -> tuple[Path, Path]:
    base_dir = Path(__file__).resolve().parent.parent
    resolved_nodes = Path(nodes_path) if nodes_path else base_dir / NODES_CSV_PATH
    resolved_edges = Path(edges_path) if edges_path else base_dir / EDGES_CSV_PATH
    return resolved_nodes, resolved_edges


def _canonical_edge_key(node_1_id: str, node_2_id: str, edge_type: EdgeType, time_cost: int) -> tuple[str, str, str, int]:
    node_a, node_b = sorted((node_1_id, node_2_id))
    return node_a, node_b, str(edge_type), time_cost


def load_validated_map(nodes_path: str | None = None, edges_path: str | None = None) -> LoadResult:
    nodes_file, edges_file = resolve_paths(nodes_path, edges_path)
    campus_map = CampusMap()
    issues: list[ImportIssue] = []

    node_rows = 0
    with open(nodes_file, mode="r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row_num, row in enumerate(reader, start=2):
            node_rows += 1
            node_id = (row.get("node_id") or "").strip()
            description = (row.get("node_description") or "").strip()

            if node_id == "":
                issues.append(ImportIssue(entity="node", row_number=row_num, reason="node_id cannot be empty"))
                continue
            if node_id in {node.node_id for node in campus_map.get_nodes()}:
                issues.append(ImportIssue(entity="node", row_number=row_num, reason=f"duplicate node_id: {node_id}"))
                continue

            campus_map.add_node(Node(node_id=node_id, description=description))

    edge_rows = 0
    seen_edges: set[tuple[str, str, str, int]] = set()
    with open(edges_file, mode="r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row_num, row in enumerate(reader, start=2):
            edge_rows += 1
            node_1_id = (row.get("node_1_id") or "").strip()
            node_2_id = (row.get("node_2_id") or "").strip()
            raw_edge_type = (row.get("edge_type") or "").strip()
            raw_time_cost = (row.get("time_cost") or "").strip()

            if node_1_id == "" or node_2_id == "":
                issues.append(ImportIssue(entity="edge", row_number=row_num, reason="node IDs cannot be empty"))
                continue
            if node_1_id == node_2_id:
                issues.append(ImportIssue(entity="edge", row_number=row_num, reason="self-loop edges are not allowed"))
                continue

            try:
                edge_type = EdgeType(raw_edge_type)
            except ValueError:
                issues.append(ImportIssue(entity="edge", row_number=row_num, reason=f"invalid edge_type: {raw_edge_type}"))
                continue

            try:
                time_cost = int(raw_time_cost)
            except ValueError:
                issues.append(ImportIssue(entity="edge", row_number=row_num, reason=f"time_cost is not an integer: {raw_time_cost}"))
                continue
            if time_cost < 0:
                issues.append(ImportIssue(entity="edge", row_number=row_num, reason="time_cost must be >= 0"))
                continue

            if not _node_exists(campus_map, node_1_id) or not _node_exists(campus_map, node_2_id):
                issues.append(
                    ImportIssue(
                        entity="edge",
                        row_number=row_num,
                        reason=(
                            f"edge references missing node(s): {node_1_id} / {node_2_id}"
                        ),
                    )
                )
                continue

            canonical_key = _canonical_edge_key(node_1_id, node_2_id, edge_type, time_cost)
            if canonical_key in seen_edges:
                issues.append(
                    ImportIssue(
                        entity="edge",
                        row_number=row_num,
                        reason=(
                            "duplicate edge found (including reversed order duplicate)"
                        ),
                    )
                )
                continue

            seen_edges.add(canonical_key)
            campus_map.add_edge(node1_id=node_1_id, node2_id=node_2_id, edge_type=edge_type, time_cost=time_cost)

    return LoadResult(
        campus_map=campus_map,
        issues=issues,
        nodes_loaded=len(campus_map.get_nodes()),
        edges_loaded=len(campus_map.get_edges()),
        node_rows=node_rows,
        edge_rows=edge_rows,
    )


def save_map(campus_map: CampusMap, nodes_path: str | None = None, edges_path: str | None = None) -> tuple[Path, Path]:
    nodes_file, edges_file = resolve_paths(nodes_path, edges_path)
    nodes_file.parent.mkdir(parents=True, exist_ok=True)
    edges_file.parent.mkdir(parents=True, exist_ok=True)

    with open(nodes_file, mode="w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["node_id", "node_description"])
        writer.writeheader()
        for node in sorted(campus_map.get_nodes(), key=lambda item: item.node_id):
            writer.writerow({"node_id": node.node_id, "node_description": node.description})

    sorted_edges = sorted(
        campus_map.get_edges(),
        key=lambda item: (item.node1.node_id, item.node2.node_id, str(item.edge_type), item.time_cost),
    )
    with open(edges_file, mode="w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["node_1_id", "node_2_id", "edge_type", "time_cost"])
        writer.writeheader()
        for edge in sorted_edges:
            writer.writerow(
                {
                    "node_1_id": edge.node1.node_id,
                    "node_2_id": edge.node2.node_id,
                    "edge_type": str(edge.edge_type),
                    "time_cost": edge.time_cost,
                }
            )

    return nodes_file, edges_file


def build_integrity_report(campus_map: CampusMap) -> IntegrityReport:
    nodes = campus_map.get_nodes()
    edges = campus_map.get_edges()
    isolated_nodes = sum(1 for node in nodes if len(node.get_edges()) == 0)

    visited: set[str] = set()
    connected_components = 0
    for node in nodes:
        if node.node_id in visited:
            continue
        connected_components += 1
        queue: deque[Node] = deque([node])
        visited.add(node.node_id)
        while queue:
            current = queue.popleft()
            for edge in current.get_edges():
                other = edge.get_other_node_of(current)
                if other.node_id not in visited:
                    visited.add(other.node_id)
                    queue.append(other)

    return IntegrityReport(
        node_count=len(nodes),
        edge_count=len(edges),
        isolated_nodes=isolated_nodes,
        connected_components=connected_components,
    )


def detect_duplicate_edges(campus_map: CampusMap) -> list[tuple[str, str, str, int, int]]:
    duplicates: list[tuple[str, str, str, int, int]] = []
    counter: Counter[tuple[str, str, str, int]] = Counter(
        _canonical_edge_key(edge.node1.node_id, edge.node2.node_id, edge.edge_type, edge.time_cost)
        for edge in campus_map.get_edges()
    )

    for key, count in sorted(counter.items()):
        if count > 1:
            duplicates.append((key[0], key[1], key[2], key[3], count))
    return duplicates


def snapshot(campus_map: CampusMap) -> tuple[dict[str, str], Counter[tuple[str, str, str, int]]]:
    nodes_snapshot = {node.node_id: node.description for node in campus_map.get_nodes()}
    edges_snapshot = Counter(
        _canonical_edge_key(edge.node1.node_id, edge.node2.node_id, edge.edge_type, edge.time_cost)
        for edge in campus_map.get_edges()
    )
    return nodes_snapshot, edges_snapshot


def build_change_preview(
    baseline: tuple[dict[str, str], Counter[tuple[str, str, str, int]]],
    current_map: CampusMap,
) -> ChangePreview:
    baseline_nodes, baseline_edges = baseline
    current_nodes, current_edges = snapshot(current_map)

    baseline_ids = set(baseline_nodes)
    current_ids = set(current_nodes)
    nodes_added = len(current_ids - baseline_ids)
    nodes_removed = len(baseline_ids - current_ids)
    nodes_modified = sum(
        1
        for node_id in (baseline_ids & current_ids)
        if baseline_nodes[node_id] != current_nodes[node_id]
    )

    edges_added = 0
    edges_removed = 0
    all_edge_keys = set(baseline_edges) | set(current_edges)
    for key in all_edge_keys:
        delta = current_edges[key] - baseline_edges[key]
        if delta > 0:
            edges_added += delta
        elif delta < 0:
            edges_removed += -delta

    return ChangePreview(
        nodes_added=nodes_added,
        nodes_removed=nodes_removed,
        nodes_modified=nodes_modified,
        edges_added=edges_added,
        edges_removed=edges_removed,
    )


def _node_exists(campus_map: CampusMap, node_id: str) -> bool:
    try:
        campus_map.get_node_by_id(node_id)
        return True
    except ValueError:
        return False