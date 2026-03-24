from __future__ import annotations

from typing import TYPE_CHECKING

from .edge_type import EdgeType

if TYPE_CHECKING:
    from .node import Node

class Edge:
    """
    Represents a path connecting two nodes on the campus map.
    """

    def __init__(self, node1: Node, node2: Node, edge_type: EdgeType, time_cost: int):
        """
        Constructor. Creates a new edge. Automatically adds the edge to the incident nodes.
        :param node1: The node that is incident to this edge.
        :param node2: The node that is incident to this edge.
        :param edge_type: The type of this edge.
        :param time_cost: The time it takes to traverse this edge, in seconds.
        :exception ValueError: If node1 and node2 are the same.
        """

        if node1.node_id == node2.node_id:
            raise ValueError("A multigraph does not allow loops.")

        self.node1: Node = node1
        """
        The node that is incident to this edge.
        """
        node1.add_edge(self)

        self.node2: Node = node2
        """
        The node that is incident to this edge.
        """
        node2.add_edge(self)

        self.edge_type: EdgeType = edge_type
        """
        The type of this edge.
        """

        self.time_cost: int = time_cost
        """
        The time it takes to traverse this edge, in seconds.
        """

    def get_other_node_of(self, node: Node) -> Node:
        """
        Returns the other node that is incident to this edge.
        :param node: The node that is incident to this edge.
        :return: The other node that is incident to this edge.
        :exception ValueError: If the given node is not incident to this edge.
        """
        if node.node_id == self.node1.node_id:
            return self.node2
        elif node.node_id == self.node2.node_id:
            return self.node1
        else:
            raise ValueError("The given node is not incident to this edge.")
