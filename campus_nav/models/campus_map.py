from __future__ import annotations

import csv
from pathlib import Path

from ..constants import InternalConstants as Const
from .edge import Edge
from .edge_type import EdgeType
from .node import Node


class CampusMap:
    """
    Represents the map of HKU as an undirected multigraph.
    """

    def __init__(self):
        """
        Constructor. Creates a new CampusMap instance.
        """

        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []

    def get_nodes(self) -> list[Node]:
        """
        Returns a copy of the list of nodes in the campus map.
        :return: A copy of the list of nodes in the campus map.
        """
        return list(self._nodes.values())

    def get_node_by_id(self, node_id: str) -> Node:
        """
        Returns the node with the given ID.
        :param node_id: The ID of the node to be returned.
        :return: The node with the given ID.
        :exception ValueError: If no node with the given ID exists in the campus map.
        """
        if node_id not in self._nodes:
            raise ValueError(f"No node with ID {node_id} exists in the campus map.")
        return self._nodes[node_id]

    def get_edges(self) -> list[Edge]:
        """
        Returns a copy of the list of edges in the campus map.
        :return: A copy of the list of edges in the campus map.
        """
        return self._edges.copy()

    def add_node(self, node: Node) -> None:
        """
        Adds a node to the campus map.
        :param node: The node to be added.
        :exception ValueError: If a node with the same ID already exists in the campus map.
        """
        if node.node_id in self._nodes:
            raise ValueError(f"A node with the same ID ({node.node_id}) already exists in the campus map.")
        self._nodes[node.node_id] = node

    def add_edge(self, node1_id: str, node2_id: str, edge_type: EdgeType, time_cost: int) -> None:
        """
        Adds an edge to the campus map.
        :param node1_id: The node that is incident to the edge.
        :param node2_id: The node that is incident to the edge.
        :param edge_type: The type of the edge.
        :param time_cost: The time it takes to traverse the edge, in seconds.
        """
        if node1_id not in self._nodes:
            raise ValueError(f"Node with ID {node1_id} does not exist in the campus map.")
        if node2_id not in self._nodes:
            raise ValueError(f"Node with ID {node2_id} does not exist in the campus map.")
        # normalise: node1_id should be the smaller one (lexicographically)
        if node1_id > node2_id:
            node1_id, node2_id = node2_id, node1_id
        edge = Edge(self._nodes[node1_id], self._nodes[node2_id], edge_type, time_cost)
        self._edges.append(edge)

    def remove_node(self, node_id: str, force_remove: bool = False) -> None:
        """
        Removes a node from the campus map.
        :param node_id: The ID of the node to be removed.
        :param force_remove: If true, the node will be removed even if it has incident edges.
        The incident edges will also be removed.
        If false, the node will only be removed if it has no incident edges and a ValueError will be raised otherwise.
        :exception ValueError: If the node has incident edges and force_remove is false.
        """
        if node_id not in self._nodes:
            raise ValueError(f"Node with ID {node_id} does not exist in the campus map.")
        node = self._nodes[node_id]
        if not force_remove and len(node.get_edges()) > 0:
            raise ValueError(f"Node with ID {node_id} has incident edges and cannot be removed.")
        for edge in node.get_edges():
            self.remove_edge(edge)
        del self._nodes[node_id]

    def remove_edge(self, edge: Edge) -> None:
        """
        Removes an edge from the campus map.
        :param edge: The edge to be removed.
        """
        edge.node1.remove_edge(edge) # the other incident node will automatically remove the edge as well
        self._edges.remove(edge)

    def write_to_csv(self, nodes_file: str | None = None, edges_file: str | None = None) -> None:
        """
        Writes the campus map to CSV files in deterministic order.
        For nodes, the order is sorted by node ID (lexicographically).
        For edges, the nodes pair will be rearranged such that node1_id is smaller than node2_id (lexicographically)
        and the order is sorted by (node1_id, node2_id, edge_type, time_cost).
        :param nodes_file: The path to the CSV file to write the nodes information to. If None, it defaults to the bundled file.
        :param edges_file: The path to the CSV file to write the edges information to. If None, it defaults to the bundled file.
        """
        if nodes_file is None: nodes_file = str(Path(__file__).resolve().parent.parent / Const.NODES_CSV_PATH)
        if edges_file is None: edges_file = str(Path(__file__).resolve().parent.parent / Const.EDGES_CSV_PATH)

        with open(str(nodes_file), mode='w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['node_id', 'node_description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for node in sorted(self.get_nodes(), key=lambda n: n.node_id):
                writer.writerow({'node_id': node.node_id, 'node_description': node.description})

        with open(str(edges_file), mode='w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['node_1_id', 'node_2_id', 'edge_type', 'time_cost']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for edge in sorted(self.get_edges(), key=lambda e: (e.node1.node_id, e.node2.node_id, e.edge_type.value, e.time_cost)):
                writer.writerow({
                    'node_1_id': edge.node1.node_id,
                    'node_2_id': edge.node2.node_id,
                    'edge_type': edge.edge_type.value,
                    'time_cost': edge.time_cost
                })
